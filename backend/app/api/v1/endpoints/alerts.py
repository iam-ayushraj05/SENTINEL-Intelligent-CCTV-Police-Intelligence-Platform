import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from fastapi.responses import FileResponse

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.alert import Alert, AlertEvent, AlertAssignment
from app.models.emergency import AlertDelivery
from app.services.notification_service import get_notification_service
from app.core.config import settings
from app.models.camera import Camera
from app.models.audit import AuditLog
from app.schemas.alert import (
    AlertRead,
    AlertCreate,
    AlertUpdate,
    AlertAcknowledgeRequest,
    AlertAssignRequest,
)
from app.services.websocket_manager import ws_manager

router = APIRouter()


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Create an operator-entered alert and publish it to the live alert feed."""
    severity = payload.severity.upper()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise HTTPException(status_code=422, detail="Severity must be LOW, MEDIUM, HIGH, or CRITICAL")

    camera = await db.get(Camera, payload.camera_id) if payload.camera_id else None
    if payload.camera_id and not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    now = datetime.utcnow()
    alert = Alert(
        id=uuid.uuid4(),
        alert_code=f"MAN-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
        alert_type=payload.alert_type.strip() or "MANUAL",
        severity=severity,
        camera_id=payload.camera_id,
        title=payload.title.strip(),
        description=payload.description,
        confidence=payload.confidence,
        status="OPEN",
        verification_status="OPERATOR_VERIFIED",
        metadata_json={**(payload.metadata_json or {}), "source": "MANUAL"},
        created_at=now,
        updated_at=now,
    )
    db.add(alert)
    db.add(AlertEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        action="CREATED",
        actor="Operator",
        comment="Created manually from the alert command center",
        timestamp=now,
    ))
    db.add(AuditLog(
        id=uuid.uuid4(),
        username="Operator",
        action="ALERT_CREATE_MANUAL",
        resource=f"Alert:{alert.alert_code}",
        result="SUCCESS",
        timestamp=now,
    ))
    await db.commit()
    await db.refresh(alert)
    await ws_manager.broadcast_alert({
        "id": str(alert.id),
        "alert_code": alert.alert_code,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "camera_id": str(alert.camera_id) if alert.camera_id else None,
        "camera_name": camera.name if camera else None,
        "camera_code": camera.camera_code if camera else None,
        "title": alert.title,
        "description": alert.description,
        "confidence": alert.confidence,
        "status": alert.status,
        "metadata_json": alert.metadata_json,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    })
    return await get_alert(alert.id, db)


@router.post("/{alert_id}/evidence")
async def upload_alert_evidence(alert_id: uuid.UUID, evidence: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Store an operator/AI evidence file locally and attach its reference to the alert."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    allowed_types = {"video/mp4", "video/webm", "image/jpeg", "image/png"}
    if evidence.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Evidence must be MP4, WebM, JPEG, or PNG")
    content = await evidence.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Evidence file is larger than 100 MB")
    digest = hashlib.sha256(content).hexdigest()
    extension = Path(evidence.filename or "evidence.bin").suffix.lower() or ".bin"
    folder = Path(settings.evidence_storage_path) / str(alert.camera_id or "unknown") / datetime.utcnow().strftime("%Y/%m/%d") / alert.severity
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{alert.alert_code}_{digest[:16]}{extension}"
    target.write_bytes(content)
    alert.evidence_url = f"/api/v1/alerts/{alert.id}/evidence/{target.name}"
    alert.metadata_json = {**(alert.metadata_json or {}), "evidence_sha256": digest, "evidence_upload_status": "STORED_LOCAL"}
    await db.commit()
    return {"alert_id": alert.id, "evidence_url": alert.evidence_url, "sha256": digest, "status": "STORED_LOCAL"}


@router.get("/{alert_id}/evidence/{filename}")
async def get_alert_evidence(alert_id: uuid.UUID, filename: str, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    root = Path(settings.evidence_storage_path).resolve()
    matches = list(root.rglob(filename))
    if not matches or root not in matches[0].resolve().parents:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return FileResponse(matches[0])


@router.post("/{alert_id}/stop-escalation")
async def stop_alert_escalation(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Stop SMS retry and explicitly terminate an active outbound call."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    result = await db.execute(select(AlertDelivery).where(AlertDelivery.status == "ACTIVE"))
    deliveries = [item for item in result.scalars().all() if (item.metadata_json or {}).get("alert_id") == str(alert_id)]
    service = get_notification_service()
    stopped_calls = []
    for delivery in deliveries:
        call_sid = (delivery.metadata_json or {}).get("provider_call_id")
        if call_sid:
            stopped_calls.append(await service.stop_voice_call(call_sid))
        delivery.status = "STOPPED"
        delivery.is_recurring = False
        delivery.next_send_at = None
        delivery.stopped_at = datetime.utcnow()
    await db.commit()
    return {"alert_id": alert_id, "status": "STOPPED", "deliveries_stopped": len(deliveries), "calls": stopped_calls}


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    severity: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    alert_type: str | None = None,
    camera_id: uuid.UUID | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Alert, Camera.name.label("camera_name"), Camera.camera_code.label("camera_code"))
        .outerjoin(Camera, Alert.camera_id == Camera.id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    if severity:
        stmt = stmt.where(Alert.severity == severity.upper())
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter.upper())
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if camera_id:
        stmt = stmt.where(Alert.camera_id == camera_id)

    result = await db.execute(stmt)
    rows = result.all()

    output = []
    for alert, cam_name, cam_code in rows:
        a_read = AlertRead.model_validate(alert)
        a_read.camera_name = cam_name
        a_read.camera_code = cam_code
        output.append(a_read)
    return output


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Alert, Camera.name.label("camera_name"), Camera.camera_code.label("camera_code"))
        .outerjoin(Camera, Alert.camera_id == Camera.id)
        .where(Alert.id == alert_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert, cam_name, cam_code = row
    a_read = AlertRead.model_validate(alert)
    a_read.camera_name = cam_name
    a_read.camera_code = cam_code
    return a_read


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    payload: AlertAcknowledgeRequest = AlertAcknowledgeRequest(),
    db: AsyncSession = Depends(get_db),
):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ACKNOWLEDGED"
    alert.assigned_officer = payload.officer_name or "Operator"
    alert.updated_at = datetime.utcnow()

    event = AlertEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        action="ACKNOWLEDGED",
        actor=payload.officer_name or "Operator",
        comment=payload.note,
        timestamp=datetime.utcnow(),
    )
    db.add(event)

    audit = AuditLog(
        id=uuid.uuid4(),
        username=payload.officer_name or "Operator",
        action="ALERT_ACKNOWLEDGE",
        resource=f"Alert:{alert.alert_code}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    return await get_alert(alert_id, db)


@router.post("/{alert_id}/assign", response_model=AlertRead)
async def assign_alert(
    alert_id: uuid.UUID,
    payload: AlertAssignRequest,
    db: AsyncSession = Depends(get_db),
):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.assigned_officer = payload.officer_name
    alert.status = "INVESTIGATING"
    alert.updated_at = datetime.utcnow()

    event = AlertEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        action="ASSIGNED",
        actor=payload.officer_name,
        comment=f"Assigned to officer {payload.officer_name}",
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    return await get_alert(alert_id, db)


@router.post("/{alert_id}/resolve", response_model=AlertRead)
async def resolve_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.updated_at = datetime.utcnow()

    event = AlertEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        action="RESOLVED",
        actor="Operator",
        comment="Alert resolved after operational verification",
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    return await get_alert(alert_id, db)


@router.post("/{alert_id}/dismiss", response_model=AlertRead)
async def dismiss_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "DISMISSED"
    alert.updated_at = datetime.utcnow()

    event = AlertEvent(
        id=uuid.uuid4(),
        alert_id=alert.id,
        action="DISMISSED",
        actor="Operator",
        comment="Alert dismissed as false alarm",
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    return await get_alert(alert_id, db)
