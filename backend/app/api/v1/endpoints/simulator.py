import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.camera import Camera
from app.services.correlation_engine import evaluate_detection_event
from app.services.websocket_manager import ws_manager

router = APIRouter()


class ManualTriggerRequest(BaseModel):
    event_type: str = "WATCHLIST_MATCH"
    plate_number: str | None = "GJ05CD5678"
    camera_id: uuid.UUID | None = None
    confidence: float = 0.96


@router.post("/trigger-event")
async def trigger_simulated_event(req: ManualTriggerRequest, db: AsyncSession = Depends(get_db)):
    cam = None
    if hasattr(db, "get"):
        if req.camera_id:
            cam = await db.get(Camera, req.camera_id)
        else:
            res = await db.execute(select(Camera))
            cam = res.scalars().first() if hasattr(res, "scalars") else None

    if not cam:
        cam = Camera(id=uuid.uuid4(), camera_code="CAM-GJ-AMD-001", name="SG Highway Junction")

    alert = await evaluate_detection_event(
        db=db,
        camera_id=cam.id,
        event_type=req.event_type,
        subject_reference=req.plate_number,
        confidence=req.confidence,
        evidence_url="https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
        metadata_json={"manually_triggered": True, "demo_mode": True},
    )

    return {
        "status": "TRIGGERED",
        "event_type": req.event_type,
        "camera_code": getattr(cam, "camera_code", "CAM-GJ-AMD-001"),
        "alert_created": getattr(alert, "alert_code", "ALT-DEMO-001") if alert else None,
    }
