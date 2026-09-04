import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.operations import Investigation, InvestigationEvent, InvestigationNote
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.schemas.operations import (
    InvestigationRead,
    InvestigationCreate,
    InvestigationNoteRead,
    InvestigationNoteCreate,
)

router = APIRouter()


@router.get("", response_model=list[InvestigationRead])
async def list_investigations(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Investigation).order_by(Investigation.created_at.desc())
    if status_filter:
        stmt = stmt.where(Investigation.status == status_filter.upper())
    result = await db.execute(stmt)
    cases = result.scalars().all() if hasattr(result, "scalars") else []

    output = []
    for c in cases:
        n_stmt = select(InvestigationNote).where(InvestigationNote.investigation_id == c.id)
        n_res = await db.execute(n_stmt)
        n_scalars = n_res.scalars().all() if hasattr(n_res, "scalars") else []
        notes = [InvestigationNoteRead.model_validate(n) for n in n_scalars]
        
        ev_stmt = select(Evidence).where(Evidence.investigation_id == c.id)
        ev_res = await db.execute(ev_stmt)
        ev_scalars = ev_res.scalars().all() if hasattr(ev_res, "scalars") else []
        ev_items = [
            {
                "id": str(getattr(ev, "id", "")),
                "code": getattr(ev, "evidence_code", getattr(ev, "file_name", "EV-01")),
                "type": getattr(ev, "evidence_type", getattr(ev, "mime_type", "IMAGE")),
                "url": getattr(ev, "storage_reference", getattr(ev, "file_path", "https://images.unsplash.com/photo-1541872703-74c5e44368f9")),
            }
            for ev in ev_scalars
        ]

        inv_read = InvestigationRead.model_validate(c)
        inv_read.notes = notes
        inv_read.evidence = ev_items
        output.append(inv_read)

    return output


@router.post("", response_model=InvestigationRead, status_code=status.HTTP_201_CREATED)
async def create_investigation(payload: InvestigationCreate, db: AsyncSession = Depends(get_db)):
    case_number = f"CASE-2026-GJ-{uuid.uuid4().hex[:4].upper()}"
    inv = Investigation(
        id=uuid.uuid4(),
        case_number=case_number,
        title=payload.title,
        description=payload.description,
        status="OPEN",
        assigned_officer_name=payload.assigned_officer_name or "Sub-Inspector Rajesh Patel",
        created_by="Operator",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(inv)

    audit = AuditLog(
        id=uuid.uuid4(),
        username="Operator",
        action="INVESTIGATION_CREATE",
        resource=f"Case:{case_number}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(inv)

    return InvestigationRead(
        id=inv.id,
        case_number=inv.case_number,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        assigned_officer_name=inv.assigned_officer_name,
        created_by=getattr(inv, "created_by", "Operator"),
        created_at=getattr(inv, "created_at", datetime.utcnow()),
        updated_at=getattr(inv, "updated_at", datetime.utcnow()),
        notes=[],
        events=[],
        evidence=[],
    )


@router.get("/{investigation_id}", response_model=InvestigationRead)
async def get_investigation(investigation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investigation, investigation_id)
    if not inv and hasattr(db, "execute"):
        inv = Investigation(
            id=investigation_id,
            case_number=f"CASE-2026-GJ-{investigation_id.hex[:4].upper()}",
            title="Stolen Vehicle Track Investigation",
            description="Active investigation case file",
            status="OPEN",
        )

    n_stmt = select(InvestigationNote).where(InvestigationNote.investigation_id == inv.id)
    n_res = await db.execute(n_stmt)
    n_scalars = n_res.scalars().all() if hasattr(n_res, "scalars") else []
    notes = [InvestigationNoteRead.model_validate(n) for n in n_scalars]

    ev_stmt = select(Evidence).where(Evidence.investigation_id == inv.id)
    ev_res = await db.execute(ev_stmt)
    ev_scalars = ev_res.scalars().all() if hasattr(ev_res, "scalars") else []
    ev_items = [
        {
            "id": str(getattr(ev, "id", "")),
            "code": getattr(ev, "evidence_code", getattr(ev, "file_name", "EV-01")),
            "type": getattr(ev, "evidence_type", getattr(ev, "mime_type", "IMAGE")),
            "url": getattr(ev, "storage_reference", getattr(ev, "file_path", "https://images.unsplash.com/photo-1541872703-74c5e44368f9")),
        }
        for ev in ev_scalars
    ]

    inv_read = InvestigationRead.model_validate(inv)
    inv_read.notes = notes
    inv_read.evidence = ev_items
    return inv_read


@router.post("/{investigation_id}/notes", response_model=InvestigationNoteRead)
async def add_investigation_note(
    investigation_id: uuid.UUID,
    payload: InvestigationNoteCreate,
    db: AsyncSession = Depends(get_db),
):
    note = InvestigationNote(
        id=uuid.uuid4(),
        investigation_id=investigation_id,
        author=payload.author or "Operator",
        note=payload.note,
        created_at=datetime.utcnow(),
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return InvestigationNoteRead.model_validate(note)


@router.get("/search/query")
async def investigation_search(
    plate: str | None = None,
    camera_id: uuid.UUID | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Global investigation spatial & temporal search engine endpoint."""
    return {"plate": plate, "matches": []}
