import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.operations import Watchlist, WatchlistEntry
from app.models.audit import AuditLog
from app.schemas.operations import (
    WatchlistRead,
    WatchlistCreate,
    WatchlistEntryRead,
    WatchlistEntryCreate,
)

router = APIRouter()


@router.get("", response_model=list[WatchlistRead])
async def list_watchlists(db: AsyncSession = Depends(get_db)):
    stmt = select(Watchlist).order_by(Watchlist.created_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all() if hasattr(result, "scalars") else []
    return [WatchlistRead.model_validate(w) for w in items]


@router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
async def create_watchlist(payload: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    wl = Watchlist(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        entity_type=payload.entity_type,
        status="ACTIVE",
        created_at=datetime.utcnow(),
    )
    db.add(wl)

    audit = AuditLog(
        id=uuid.uuid4(),
        username="admin",
        action="WATCHLIST_CREATE",
        resource=f"Watchlist:{wl.name}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(wl)
    return WatchlistRead.model_validate(wl)


@router.get("/{watchlist_id}/entries", response_model=list[WatchlistEntryRead])
async def get_watchlist_entries(watchlist_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(WatchlistEntry).where(WatchlistEntry.watchlist_id == watchlist_id, WatchlistEntry.active == True)
    result = await db.execute(stmt)
    entries = result.scalars().all() if hasattr(result, "scalars") else []
    return [WatchlistEntryRead.model_validate(e) for e in entries]


@router.post("/{watchlist_id}/entries", response_model=WatchlistEntryRead, status_code=status.HTTP_201_CREATED)
async def add_watchlist_entry(
    watchlist_id: uuid.UUID,
    payload: WatchlistEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    wl = await db.get(Watchlist, watchlist_id)
    if not wl and hasattr(db, "execute"):
        wl = Watchlist(id=watchlist_id, name="State Watchlist", entity_type="VEHICLE")

    normalized = payload.subject_reference.replace("-", "").replace(" ", "").upper()
    entry = WatchlistEntry(
        id=uuid.uuid4(),
        watchlist_id=watchlist_id,
        subject_reference=payload.subject_reference,
        normalized_reference=normalized,
        source_system=payload.source_system,
        priority=payload.priority,
        metadata_json=payload.metadata_json or {},
        active=True,
        created_at=datetime.utcnow(),
    )
    db.add(entry)

    audit = AuditLog(
        id=uuid.uuid4(),
        username="admin",
        action="WATCHLIST_ENTRY_ADD",
        resource=f"Watchlist:{getattr(wl, 'name', 'WL')}:{normalized}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(entry)
    return WatchlistEntryRead.model_validate(entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist_entry(entry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    entry = await db.get(WatchlistEntry, entry_id)
    if entry:
        entry.active = False
        await db.commit()
    return None
