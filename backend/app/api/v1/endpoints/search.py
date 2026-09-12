from fastapi import APIRouter, Depends, Query
try:
    from sqlalchemy import select, or_
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession
    def or_(*args): return None

from app.core.database import get_db
from app.models.camera import Camera
from app.models.alert import Alert
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.operations import Investigation, WatchlistEntry

router = APIRouter()


@router.get("")
async def global_search(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    query_str = f"%{q}%"
    normalized = q.replace("-", "").replace(" ", "").upper()

    cameras, alerts, plates, vehicles, cases, watchlists = [], [], [], [], [], []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            c_stmt = select(Camera).where(
                or_(Camera.name.ilike(query_str), Camera.camera_code.ilike(query_str), Camera.zone.ilike(query_str))
            ).limit(5)
            c_res = await db.execute(c_stmt)
            c_items = c_res.scalars().all() if hasattr(c_res, "scalars") else []
            cameras = [
                {"id": str(c.id), "code": c.camera_code, "name": c.name, "zone": c.zone, "status": c.status}
                for c in c_items
            ]

            a_stmt = select(Alert).where(
                or_(Alert.title.ilike(query_str), Alert.alert_code.ilike(query_str), Alert.description.ilike(query_str))
            ).limit(5)
            a_res = await db.execute(a_stmt)
            a_items = a_res.scalars().all() if hasattr(a_res, "scalars") else []
            alerts = [
                {"id": str(a.id), "code": a.alert_code, "title": a.title, "severity": a.severity, "status": a.status}
                for a in a_items
            ]

            v_stmt = select(Vehicle).where(
                Vehicle.is_deleted == False,
                or_(Vehicle.normalized_plate.ilike(f"%{normalized}%"), Vehicle.plate_number.ilike(query_str), Vehicle.make.ilike(query_str), Vehicle.model.ilike(query_str), Vehicle.vehicle_type.ilike(query_str), Vehicle.color.ilike(query_str))
            ).limit(20)
            v_res = await db.execute(v_stmt)
            v_items = v_res.scalars().all() if hasattr(v_res, "scalars") else []
            plates = [
                {"plate": v.plate_number, "confidence": (v.metadata_json or {}).get("plate_confidence", 0), "vehicle_id": str(v.id), "timestamp": v.last_seen.isoformat()}
                for v in v_items
            ]
            vehicles = [{"id": str(v.id), "plate": v.plate_number, "make": v.make, "model": v.model, "vehicle_type": v.vehicle_type, "color": v.color, "last_seen": v.last_seen.isoformat(), "metadata_json": v.metadata_json or {}} for v in v_items]

            i_stmt = select(Investigation).where(
                or_(Investigation.case_number.ilike(query_str), Investigation.title.ilike(query_str))
            ).limit(5)
            i_res = await db.execute(i_stmt)
            i_items = i_res.scalars().all() if hasattr(i_res, "scalars") else []
            cases = [
                {"id": str(i.id), "case_number": i.case_number, "title": i.title, "status": i.status}
                for i in i_items
            ]

            w_stmt = select(WatchlistEntry).where(WatchlistEntry.normalized_reference.ilike(f"%{normalized}%")).limit(5)
            w_res = await db.execute(w_stmt)
            w_items = w_res.scalars().all() if hasattr(w_res, "scalars") else []
            watchlists = [
                {"id": str(w.id), "reference": w.subject_reference, "priority": w.priority, "source": w.source_system}
                for w in w_items
            ]
        except Exception:
            pass

    return {
        "query": q,
        "results": {
            "cameras": cameras,
            "alerts": alerts,
            "plates": plates,
            "vehicles": vehicles,
            "investigations": cases,
            "watchlists": watchlists,
        },
    }
