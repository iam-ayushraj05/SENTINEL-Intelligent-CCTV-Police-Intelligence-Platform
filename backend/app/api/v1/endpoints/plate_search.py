"""
Plate Search API — search actual ANPR observations from the database.

GET /api/v1/search/plates?plate=GJ01AB1234&camera_id=cam11&start_time=...&end_time=...&min_confidence=0.7

Returns ONLY actual recorded observations. Never fabricates plate data.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException

try:
    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

    def and_(*args):
        return None

from app.core.database import get_db
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.camera import Camera

router = APIRouter()


@router.get("/plates")
async def search_plates(
    plate: str = Query(..., min_length=2, description="Plate number to search (partial match supported)"),
    camera_id: str | None = Query(None, description="Filter by camera ID or code"),
    start_time: datetime | None = Query(None, description="Start of time range (ISO 8601)"),
    end_time: datetime | None = Query(None, description="End of time range (ISO 8601)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum OCR confidence"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Search actual ANPR plate observations from the database.
    Returns real recorded sightings only — never fabricated data.
    """
    normalized_query = plate.replace("-", "").replace(" ", "").upper()

    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            conditions = [
                VehicleSighting.is_deleted == False,
                VehicleSighting.confidence >= min_confidence,
            ]

            # Plate filter — search both raw and normalized
            conditions.append(
                VehicleSighting.normalized_plate.ilike(f"%{normalized_query}%")
                if hasattr(VehicleSighting, "normalized_plate")
                else VehicleSighting.plate_text.ilike(f"%{normalized_query}%")
            )

            # Camera filter
            if camera_id:
                try:
                    cam_uuid = uuid.UUID(camera_id)
                    conditions.append(VehicleSighting.camera_id == cam_uuid)
                except ValueError:
                    # Look up by camera_code
                    cam_stmt = select(Camera.id).where(Camera.camera_code.ilike(camera_id))
                    cam_result = await db.execute(cam_stmt)
                    cam_row = cam_result.scalars().first()
                    if cam_row:
                        conditions.append(VehicleSighting.camera_id == cam_row)
                    else:
                        return {"query": plate, "results": [], "total": 0}

            # Time range filters
            if start_time:
                conditions.append(VehicleSighting.timestamp >= start_time)
            if end_time:
                conditions.append(VehicleSighting.timestamp <= end_time)

            stmt = (
                select(VehicleSighting)
                .where(and_(*conditions))
                .order_by(VehicleSighting.timestamp.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            sightings = result.scalars().all()

            # Resolve camera names
            camera_ids = list({s.camera_id for s in sightings})
            cam_map = {}
            if camera_ids:
                cam_stmt = select(Camera).where(Camera.id.in_(camera_ids))
                cam_result = await db.execute(cam_stmt)
                for cam in cam_result.scalars().all():
                    cam_map[cam.id] = {"code": cam.camera_code, "name": cam.name, "zone": cam.zone}

            results = []
            for s in sightings:
                cam_info = cam_map.get(s.camera_id, {})
                results.append({
                    "id": str(s.id),
                    "plate_text": s.plate_text,
                    "normalized_plate": getattr(s, "normalized_plate", s.plate_text),
                    "confidence": round(s.confidence, 4),
                    "camera_id": str(s.camera_id),
                    "camera_code": cam_info.get("code"),
                    "camera_name": cam_info.get("name"),
                    "camera_zone": cam_info.get("zone"),
                    "timestamp": s.timestamp.isoformat(),
                    "vehicle_class": (s.metadata_json or {}).get("vehicle_class"),
                    "direction": (s.metadata_json or {}).get("direction"),
                    "snapshot_url": s.crop_image_url,
                })

            # Record Audit Log for ANPR Search
            try:
                from app.models.audit import AuditLog
                audit = AuditLog(
                    id=uuid.uuid4(),
                    username="police_operator",
                    action="ANPR_SEARCH",
                    resource=f"PlateQuery:{normalized_query}",
                    details=f"Conf >= {min_confidence}, Cam: {camera_id or 'ALL'}",
                    result="SUCCESS",
                    timestamp=datetime.utcnow(),
                )
                db.add(audit)
                await db.commit()
            except Exception:
                pass

            return {
                "query": plate,
                "normalized_query": normalized_query,
                "results": results,
                "total": len(results),
                "filters": {
                    "camera_id": camera_id,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "min_confidence": min_confidence,
                },
            }


        except Exception as exc:
            # Database may not be fully initialized
            return {"query": plate, "results": [], "total": 0, "error": "Database query failed"}

    # Fallback when database is unavailable
    return {"query": plate, "results": [], "total": 0}
