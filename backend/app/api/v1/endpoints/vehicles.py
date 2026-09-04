from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
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
async def get_vehicle_sightings(plate: str, db: AsyncSession = Depends(get_db)):
    normalized = plate.replace("-", "").replace(" ", "").upper()
    
    # Query Sightings
    stmt = (
        select(VehicleSighting, Camera.name.label("camera_name"))
        .join(Camera, VehicleSighting.camera_id == Camera.id)
        .where(getattr(VehicleSighting, "normalized_plate", VehicleSighting.plate_text) == normalized)
        .order_by(VehicleSighting.timestamp.desc())
    )
    result = await db.execute(stmt)
    rows = result.all() if hasattr(result, "all") else []

    sightings = []
    for row in rows:
        sighting = row[0] if isinstance(row, (tuple, list)) else row
        cam_name = row[1] if isinstance(row, (tuple, list)) and len(row) > 1 else "Camera Node"
        s_read = SightingRead(
            id=getattr(sighting, "id", None),
            camera_id=getattr(sighting, "camera_id", None),
            camera_name=cam_name,
            timestamp=getattr(sighting, "timestamp", datetime.utcnow()),
            confidence=getattr(sighting, "confidence", 0.95),
            latitude=getattr(sighting, "latitude", 23.0225),
            longitude=getattr(sighting, "longitude", 72.5714),
            vehicle_type=getattr(sighting, "vehicle_type", "Automobile"),
            color=getattr(sighting, "color", "Silver"),
            evidence_url=getattr(sighting, "crop_image_url", None),
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
    )


@router.get("/{plate}/timeline")
async def get_vehicle_timeline(plate: str, db: AsyncSession = Depends(get_db)):
    res = await get_vehicle_sightings(plate, db)
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
    res = await get_vehicle_sightings(plate, db)
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
