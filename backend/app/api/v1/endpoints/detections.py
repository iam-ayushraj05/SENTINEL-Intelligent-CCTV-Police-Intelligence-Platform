import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.detection import Detection
from app.schemas.detection import DetectionRead

router = APIRouter()


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
