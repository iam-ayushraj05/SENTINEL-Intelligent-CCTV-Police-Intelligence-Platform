import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.alert import Alert, AlertEvent, AlertAssignment
from app.models.camera import Camera
from app.models.audit import AuditLog
from app.schemas.alert import (
    AlertRead,
    AlertCreate,
    AlertUpdate,
    AlertAcknowledgeRequest,
    AlertAssignRequest,
)

router = APIRouter()


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
