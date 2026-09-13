from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.camera import Camera
from app.models.operations import WatchlistEntry
from app.schemas.vehicle import VehicleIntelligenceResponse, SightingRead, VehicleRouteResponse, RouteSegment
from app.integrations.gov_adapter import MockGovernmentDataAdapter

router = APIRouter()
gov_adapter = MockGovernmentDataAdapter()


@router.get("/{plate}/sightings", response_model=VehicleIntelligenceResponse)
async def get_vehicle_sightings(plate: str, from_time: str | None = Query(None), to_time: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    normalized = plate.replace("-", "").replace(" ", "").upper()
    
    # Query Sightings
    stmt = (
        select(
            VehicleSighting,
            Camera.name.label("camera_name"),
            Camera.latitude.label("camera_lat"),
            Camera.longitude.label("camera_lng"),
        )
        .join(Camera, VehicleSighting.camera_id == Camera.id)
        .where(VehicleSighting.normalized_plate == normalized, VehicleSighting.is_deleted == False)
        .order_by(VehicleSighting.timestamp.desc())
    )
    if from_time:
        stmt = stmt.where(VehicleSighting.timestamp >= datetime.fromisoformat(from_time))
    if to_time:
        stmt = stmt.where(VehicleSighting.timestamp <= datetime.fromisoformat(to_time))
    result = await db.execute(stmt)
    rows = result.all() if hasattr(result, "all") else []

    sightings = []
    for row in rows:
        sighting = row[0] if isinstance(row, (tuple, list)) else row
        cam_name = row[1] if isinstance(row, (tuple, list)) and len(row) > 1 else "Camera Node"
        cam_lat = row[2] if isinstance(row, (tuple, list)) and len(row) > 2 and row[2] is not None else 22.2587
        cam_lng = row[3] if isinstance(row, (tuple, list)) and len(row) > 3 and row[3] is not None else 71.1924
        s_read = SightingRead(
            id=getattr(sighting, "id", None),
            camera_id=getattr(sighting, "camera_id", None),
            camera_name=cam_name,
            timestamp=getattr(sighting, "timestamp", datetime.utcnow()),
            confidence=getattr(sighting, "confidence", 0.95),
            latitude=cam_lat,
            longitude=cam_lng,
            vehicle_type=getattr(sighting, "vehicle_type", "Automobile"),
            color=getattr(sighting, "color", "Silver"),
            evidence_url=getattr(sighting, "crop_image_url", None),
            metadata_json=getattr(sighting, "metadata_json", None) or {},
        )
        sightings.append(s_read)

    # Check Watchlist Match
    stmt_wl = select(WatchlistEntry).where(WatchlistEntry.normalized_reference == normalized)
    wl_result = await db.execute(stmt_wl)
    entries = wl_result.scalars().all() if hasattr(wl_result, "scalars") else []
    wl_matches = [
        {
            "id": str(getattr(e, "id", "")),
            "watchlist_id": str(getattr(e, "watchlist_id", "")),
            "priority": getattr(e, "priority", "HIGH"),
            "source_system": getattr(e, "source_system", "VAHAN_POLICE_FIR"),
        }
        for e in entries
    ]

    # Authorized Government DB Lookup
    gov_record = await gov_adapter.search_vehicle_record(normalized)

    # Vehicle entity
    stmt_v = select(Vehicle).where(Vehicle.normalized_plate == normalized)
    v_res = await db.execute(stmt_v)
    v_entity = v_res.scalars().first() if hasattr(v_res, "scalars") else None

    first_seen = sightings[-1].timestamp if sightings else datetime.utcnow()
    last_seen = sightings[0].timestamp if sightings else datetime.utcnow()

    return VehicleIntelligenceResponse(
        plate=plate,
        normalized_plate=normalized,
        vehicle_type=getattr(v_entity, "vehicle_type", (gov_record.get("maker_model", "Automobile") if gov_record else "Vehicle")),
        color=getattr(v_entity, "color", "Silver"),
        make=getattr(v_entity, "make", (gov_record.get("owner_name", None) if gov_record else None)),
        model=getattr(v_entity, "model", None),
        first_seen=first_seen,
        last_seen=last_seen,
        total_sightings=len(sightings),
        sightings=sightings,
        watchlist_matches=wl_matches,
        registered_owner=gov_record,
        metadata_json=getattr(v_entity, "metadata_json", None) or {},
        match_scores=(getattr(v_entity, "metadata_json", None) or {}).get("match_scores"),
        deleted=bool(getattr(v_entity, "is_deleted", False)),
    )


@router.get("/deleted", response_model=list[dict])
async def list_deleted_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.is_deleted == True).order_by(Vehicle.deleted_at.desc()))
    return [{"id": str(item.id), "plate": item.plate_number, "normalized_plate": item.normalized_plate, "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None, "metadata_json": item.metadata_json or {}} for item in result.scalars().all()]


@router.delete("/{plate}")
async def soft_delete_vehicle(plate: str, db: AsyncSession = Depends(get_db)):
    normalized = plate.replace("-", "").replace(" ", "").upper()
    result = await db.execute(select(Vehicle).where(Vehicle.normalized_plate == normalized))
    vehicle = result.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle record not found")
    now = datetime.utcnow()
    vehicle.is_deleted = True
    vehicle.deleted_at = now
    sightings = (await db.execute(select(VehicleSighting).where(VehicleSighting.vehicle_id == vehicle.id))).scalars().all()
    for sighting in sightings:
        sighting.is_deleted = True
        sighting.deleted_at = now
    await db.commit()
    return {"status": "deleted", "plate": vehicle.plate_number, "deleted_at": now.isoformat()}


@router.get("/{plate}/timeline")
async def get_vehicle_timeline(plate: str, db: AsyncSession = Depends(get_db)):
    res = await get_vehicle_sightings(plate, db=db)
    return {
        "plate": res.plate,
        "timeline": [
            {
                "timestamp": s.timestamp.isoformat(),
                "camera_name": s.camera_name,
                "confidence": s.confidence,
                "lat": s.latitude,
                "lng": s.longitude,
                "evidence_url": s.evidence_url,
            }
            for s in res.sightings
        ],
    }


@router.get("/{plate}/route", response_model=VehicleRouteResponse)
async def get_vehicle_route(plate: str, db: AsyncSession = Depends(get_db)):
    res = await get_vehicle_sightings(plate, db=db)
    sightings = list(reversed(res.sightings))

    segments = []
    for i in range(len(sightings) - 1):
        s1 = sightings[i]
        s2 = sightings[i + 1]
        seg = RouteSegment(
            from_camera=s1.camera_name or "Camera A",
            to_camera=s2.camera_name or "Camera B",
            start_time=s1.timestamp,
            end_time=s2.timestamp,
            confidence=round((s1.confidence + s2.confidence) / 2, 2),
            geometry={
                "type": "LineString",
                "coordinates": [
                    [s1.longitude or 72.57, s1.latitude or 23.02],
                    [s2.longitude or 72.57, s2.latitude or 23.02],
                ],
            },
        )
        segments.append(seg)

    return VehicleRouteResponse(plate=plate, segments=segments)
