import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.detection import Detection, DetectionEvent
from app.schemas.detection import DetectionRead, DetectionEventIngest, DetectionBatchIngest
from app.services.correlation_engine import evaluate_detection_event
from datetime import datetime

router = APIRouter()


from app.models.camera import Camera
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.operations import WatchlistEntry


async def _resolve_camera_id(raw_cam_id: Any, db: AsyncSession) -> uuid.UUID | None:
    if isinstance(raw_cam_id, uuid.UUID):
        return raw_cam_id
    cam_str = str(raw_cam_id).strip()
    try:
        return uuid.UUID(cam_str)
    except ValueError:
        pass
    stmt = select(Camera).where(Camera.camera_code.ilike(cam_str))
    res = await db.execute(stmt)
    cam = res.scalars().first()
    return cam.id if cam else None


@router.post("/ingest")
async def ingest_detection_batch(payload: DetectionBatchIngest, db: AsyncSession = Depends(get_db)):
    """Persist AI detections, ANPR vehicle sightings, and route events to alert correlation."""
    target_camera_uuid = await _resolve_camera_id(payload.camera_id, db) or uuid.uuid4()

    for item in payload.detections:
        db.add(Detection(
            id=uuid.uuid4(),
            camera_id=target_camera_uuid,
            object_type=str(item.get("object_type", "unknown")),
            confidence=float(item.get("confidence", 0)),
            bbox=item.get("bbox", {}),
            track_id=item.get("track_id"),
            frame_reference=item.get("frame_reference"),
            metadata_json=item,
            timestamp=datetime.utcnow(),
        ))

        # ANPR Vehicle Sighting Ingestion
        norm_plate = item.get("normalized_plate") or item.get("plate_number")
        if norm_plate:
            clean_norm = str(norm_plate).replace("-", "").replace(" ", "").upper()
            v_res = await db.execute(select(Vehicle).where(Vehicle.normalized_plate == clean_norm))
            vehicle = v_res.scalars().first()
            now = datetime.utcnow()
            if not vehicle:
                vehicle = Vehicle(
                    id=uuid.uuid4(),
                    plate_number=str(item.get("plate_number") or clean_norm),
                    normalized_plate=clean_norm,
                    vehicle_type=str(item.get("object_type") or "Automobile"),
                    first_seen=now,
                    last_seen=now,
                )
                db.add(vehicle)
                await db.flush()
            else:
                vehicle.last_seen = now

            sighting = VehicleSighting(
                id=uuid.uuid4(),
                vehicle_id=vehicle.id,
                camera_id=target_camera_uuid,
                plate_text=str(item.get("plate_number") or clean_norm),
                normalized_plate=clean_norm,
                confidence=float(item.get("ocr_confidence") or item.get("confidence") or 0.90),
                crop_image_url=item.get("frame_reference"),
                timestamp=now,
                metadata_json=item,
            )
            db.add(sighting)

            # Watchlist check
            wl_res = await db.execute(select(WatchlistEntry).where(WatchlistEntry.normalized_reference == clean_norm))
            wl_entry = wl_res.scalars().first()
            if wl_entry:
                payload.events.append(DetectionEventIngest(
                    camera_id=str(target_camera_uuid),
                    event_type="ANPR_WATCHLIST_HIT",
                    subject_reference=clean_norm,
                    confidence=sighting.confidence,
                    metadata_json={"watchlist_id": str(wl_entry.id), "priority": wl_entry.priority},
                ))

    await db.commit()
    alerts = []
    for event in payload.events:
        result = await ingest_detection_event(event, db)
        if result.get("alert_id"):
            alerts.append(result["alert_id"])
    return {"camera_id": str(target_camera_uuid), "detections_saved": len(payload.detections), "alert_ids": alerts}


@router.post("/events/ingest")
async def ingest_detection_event(payload: DetectionEventIngest, db: AsyncSession = Depends(get_db)):
    """Accept normalized AI events and route them through the existing correlation engine."""
    event = DetectionEvent(
        id=uuid.uuid4(),
        event_type=payload.event_type,
        camera_id=payload.camera_id,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    alert = await evaluate_detection_event(
        db,
        payload.camera_id,
        payload.event_type,
        payload.subject_reference,
        payload.confidence,
        payload.evidence_url,
        payload.metadata_json,
    )
    return {"event_id": event.id, "alert_id": getattr(alert, "id", None), "severity": getattr(alert, "severity", None)}


@router.get("", response_model=list[DetectionRead])
async def list_detections(
    camera_id: uuid.UUID | None = None,
    object_type: str | None = None,
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Detection).order_by(Detection.timestamp.desc()).limit(limit)
    if camera_id:
        stmt = stmt.where(Detection.camera_id == camera_id)
    if object_type:
        stmt = stmt.where(getattr(Detection, "object_type", getattr(Detection, "object_class", None)) == object_type)
    if min_confidence is not None:
        stmt = stmt.where(Detection.confidence >= min_confidence)
    result = await db.execute(stmt)
    detections = result.scalars().all() if hasattr(result, "scalars") else []
    return [DetectionRead.model_validate(d) for d in detections]


@router.get("/{detection_id}", response_model=DetectionRead)
async def get_detection(detection_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    det = await db.get(Detection, detection_id)
    if not det:
        raise HTTPException(status_code=404, detail="Detection not found")
    return DetectionRead.model_validate(det)
