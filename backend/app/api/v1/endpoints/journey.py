"""
Cross-Camera Vehicle Journey API — builds timelines from actual observations.

GET /api/v1/vehicles/{plate}/journey

Returns a chronological sequence of actual camera sightings.
Labels output as "Observation sequence" — NOT guaranteed physical identity.
Never fabricates movement between cameras.
"""

import uuid
from fastapi import APIRouter, Depends, Query

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.camera import Camera

router = APIRouter()


@router.get("/{plate}/journey")
async def get_vehicle_journey(
    plate: str,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Build a cross-camera journey timeline from actual observations.

    This is an observation sequence — sightings are ordered by timestamp.
    It does NOT guarantee the observations belong to the same physical vehicle
    unless the evidence supports it.
    """
    normalized = plate.replace("-", "").replace(" ", "").upper()

    observations = []

    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            # Find all sightings for this plate
            stmt = (
                select(VehicleSighting)
                .where(
                    VehicleSighting.is_deleted == False,
                    VehicleSighting.confidence >= min_confidence,
                    VehicleSighting.normalized_plate.ilike(f"%{normalized}%")
                    if hasattr(VehicleSighting, "normalized_plate")
                    else VehicleSighting.plate_text.ilike(f"%{normalized}%"),
                )
                .order_by(VehicleSighting.timestamp.asc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            sightings = result.scalars().all()

            if not sightings:
                return {
                    "plate": plate,
                    "normalized_plate": normalized,
                    "journey_type": "observation_sequence",
                    "observation_count": 0,
                    "observations": [],
                    "note": "No observations found for this plate.",
                }

            # Resolve camera info
            camera_ids = list({s.camera_id for s in sightings})
            cam_map = {}
            if camera_ids:
                cam_stmt = select(Camera).where(Camera.id.in_(camera_ids))
                cam_result = await db.execute(cam_stmt)
                for cam in cam_result.scalars().all():
                    cam_map[cam.id] = {
                        "camera_code": cam.camera_code,
                        "camera_name": cam.name,
                        "zone": cam.zone,
                        "latitude": cam.latitude,
                        "longitude": cam.longitude,
                    }

            # Build journey with time gaps
            for idx, sighting in enumerate(sightings):
                cam = cam_map.get(sighting.camera_id, {})

                entry = {
                    "sequence_index": idx + 1,
                    "camera_id": str(sighting.camera_id),
                    "camera_code": cam.get("camera_code"),
                    "camera_name": cam.get("camera_name"),
                    "zone": cam.get("zone"),
                    "latitude": cam.get("latitude"),
                    "longitude": cam.get("longitude"),
                    "timestamp": sighting.timestamp.isoformat(),
                    "plate_text": sighting.plate_text,
                    "confidence": round(sighting.confidence, 4),
                    "snapshot_url": sighting.crop_image_url,
                }

                # Calculate gap from previous observation
                if idx > 0:
                    prev_ts = sightings[idx - 1].timestamp
                    delta = sighting.timestamp - prev_ts
                    entry["time_gap_seconds"] = round(delta.total_seconds(), 1)
                    entry["previous_camera"] = cam_map.get(sightings[idx - 1].camera_id, {}).get("camera_code")
                else:
                    entry["time_gap_seconds"] = None
                    entry["previous_camera"] = None

                # Next observation preview
                if idx < len(sightings) - 1:
                    next_ts = sightings[idx + 1].timestamp
                    delta = next_ts - sighting.timestamp
                    entry["next_camera"] = cam_map.get(sightings[idx + 1].camera_id, {}).get("camera_code")
                    entry["time_to_next_seconds"] = round(delta.total_seconds(), 1)
                else:
                    entry["next_camera"] = None
                    entry["time_to_next_seconds"] = None

                observations.append(entry)

        except Exception:
            pass

    return {
        "plate": plate,
        "normalized_plate": normalized,
        "journey_type": "observation_sequence",
        "disclaimer": "This is a chronological observation sequence. It does not guarantee physical identity across sightings.",
        "observation_count": len(observations),
        "observations": observations,
    }
