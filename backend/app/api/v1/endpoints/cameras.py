import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.camera import Camera, CameraHealthEvent
from app.models.detection import Detection
from app.models.audit import AuditLog
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraRead,
    CameraStreamDescriptor,
    CameraHealthCheckResponse,
)
from app.integrations.vms_adapter import MockVMSAdapter

router = APIRouter()
vms_adapter = MockVMSAdapter()


@router.get("", response_model=list[CameraRead])
async def list_cameras(
    status_filter: str | None = Query(None, alias="status"),
    zone: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Camera).where(Camera.is_active == True)
    if status_filter:
        stmt = stmt.where(Camera.status == status_filter.upper())
    if zone:
        stmt = stmt.where(Camera.zone == zone)
    result = await db.execute(stmt)
    cameras = result.scalars().all()
    return [CameraRead.model_validate(c) for c in cameras]


@router.post("", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
async def create_camera(payload: CameraCreate, db: AsyncSession = Depends(get_db)):
    camera = Camera(
        id=uuid.uuid4(),
        camera_code=payload.camera_code,
        name=payload.name,
        description=payload.description,
        department_id=payload.department_id,
        zone=payload.zone,
        camera_type=payload.camera_type,
        manufacturer=payload.manufacturer,
        model=payload.model,
        protocol=payload.protocol,
        rtsp_url=payload.rtsp_url,
        stream_url=payload.stream_url or f"http://localhost:8889/live/{payload.camera_code.lower()}",
        vms_reference=payload.vms_reference,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status="ONLINE",
        is_active=True,
        last_heartbeat=datetime.utcnow(),
    )
    db.add(camera)

    # Audit Log
    audit = AuditLog(
        id=uuid.uuid4(),
        username="admin",
        action="CAMERA_CREATE",
        resource=f"Camera:{camera.camera_code}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(camera)
    return CameraRead.model_validate(camera)


@router.get("/{camera_id}", response_model=CameraRead)
async def get_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraRead.model_validate(camera)


@router.put("/{camera_id}", response_model=CameraRead)
async def update_camera(camera_id: uuid.UUID, payload: CameraUpdate, db: AsyncSession = Depends(get_db)):
    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(camera, field, val)

    camera.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(camera)
    return CameraRead.model_validate(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera.is_active = False
    await db.commit()
    return None


@router.get("/{camera_id}/stream", response_model=CameraStreamDescriptor)
async def get_camera_stream(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    stream_data = await vms_adapter.get_stream(camera.camera_code)
    return CameraStreamDescriptor(
        camera_id=camera.id,
        camera_code=camera.camera_code,
        protocol=camera.protocol,
        session_url=stream_data["session_url"],
        hls_url=stream_data["hls_url"],
        webrtc_url=stream_data["webrtc_url"],
        status=camera.status,
    )


@router.post("/{camera_id}/health-check", response_model=CameraHealthCheckResponse)
async def camera_health_check(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    health = await vms_adapter.get_camera_health(camera.camera_code)
    camera.last_heartbeat = datetime.utcnow()
    
    health_evt = CameraHealthEvent(
        id=uuid.uuid4(),
        camera_id=camera.id,
        status=camera.status,
        latency_ms=health["latency_ms"],
        timestamp=datetime.utcnow(),
    )
    db.add(health_evt)
    await db.commit()

    return CameraHealthCheckResponse(
        camera_id=camera.id,
        status=camera.status,
        latency_ms=health["latency_ms"],
        checked_at=datetime.utcnow(),
    )


@router.get("/{camera_id}/events")
async def get_camera_events(camera_id: uuid.UUID, limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Detection)
        .where(Detection.camera_id == camera_id)
        .order_by(Detection.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    detections = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "object_type": getattr(d, "object_type", getattr(d, "object_class", "vehicle")),
            "confidence": d.confidence,
            "bbox": d.bbox,
            "track_id": d.track_id,
            "timestamp": d.timestamp.isoformat(),
        }
        for d in detections
    ]


@router.post("/bulk-import")
async def bulk_import_cameras(db: AsyncSession = Depends(get_db)):
    """Simulates bulk authorized CSV import of cameras."""
    return {"message": "Bulk camera import completed successfully", "imported_count": 0}
