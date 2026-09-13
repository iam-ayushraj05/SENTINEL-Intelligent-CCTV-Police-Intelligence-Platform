import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.evidence import CustodyEvent, Evidence
from app.models.operations import Investigation
from app.schemas.auth import UserRead
from app.services.document_storage import ALLOWED_TYPES, MAX_FILE_BYTES, encrypt_and_store

router = APIRouter()
EVIDENCE_TYPES = {"PHYSICAL", "DIGITAL", "FORENSIC", "CCTV", "PHOTO", "VIDEO", "AUDIO"}


def _read_evidence(item: Evidence) -> dict:
    return {
        "id": str(item.id),
        "evidence_id": item.evidence_code,
        "investigation_id": str(item.investigation_id) if item.investigation_id else None,
        "filename": item.file_name,
        "mime_type": item.mime_type,
        "sha256": item.file_hash,
        "evidence_type": item.evidence_type,
        "description": item.description,
        "status": item.status,
        "current_location": item.current_location,
        "current_custodian": item.current_custodian,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
async def list_evidence(
    investigation_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None, max_length=120),
    user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Evidence).order_by(Evidence.created_at.desc())
    if investigation_id:
        stmt = stmt.where(Evidence.investigation_id == investigation_id)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Evidence.evidence_code.ilike(pattern) | Evidence.file_name.ilike(pattern) | Evidence.description.ilike(pattern))
    result = await db.execute(stmt)
    return [_read_evidence(item) for item in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    investigation_id: uuid.UUID | None = Form(None),
    evidence_type: str = Form("DIGITAL"),
    description: str | None = Form(None),
    location: str | None = Form(None),
    user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if evidence_type.upper() not in EVIDENCE_TYPES:
        raise HTTPException(422, "Unsupported evidence type")
    if file.content_type not in ALLOWED_TYPES and not (file.content_type or "").startswith(("video/", "audio/")):
        raise HTTPException(415, "Unsupported evidence file type")
    data = await file.read()
    if not data:
        raise HTTPException(422, "Evidence file is empty")
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "Evidence file exceeds the 25 MB upload limit")
    if investigation_id and not await db.get(Investigation, investigation_id):
        raise HTTPException(404, "Investigation case not found")
    if not getattr(user, "id", None):
        raise HTTPException(401, "Authenticated user is required for evidence storage")
    try:
        storage_key, digest = encrypt_and_store(data, user.id)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    now = datetime.utcnow()
    item = Evidence(
        id=uuid.uuid4(),
        evidence_code=f"EVD-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        file_name=Path(file.filename or "evidence.bin").name,
        file_path=storage_key,
        mime_type=file.content_type or "application/octet-stream",
        file_hash=digest,
        investigation_id=investigation_id,
        evidence_type=evidence_type.upper(),
        description=description,
        status="IN_CUSTODY",
        current_location=location or "Evidence intake",
        current_custodian=getattr(user, "username", "authenticated-user"),
        metadata_json={"original_filename": Path(file.filename or "evidence.bin").name, "acquired_at": now.isoformat(), "integrity": "SHA-256"},
    )
    custody = CustodyEvent(id=uuid.uuid4(), evidence_id=item.id, to_person=item.current_custodian, to_location=item.current_location, reason="Initial evidence intake", created_by=item.current_custodian, created_at=now)
    db.add_all([item, custody, AuditLog(id=uuid.uuid4(), username=item.current_custodian, action="EVIDENCE_CREATE", resource=f"Evidence:{item.evidence_code}", details=digest, result="SUCCESS", timestamp=now)])
    await db.commit()
    await db.refresh(item)
    return _read_evidence(item)


@router.get("/{evidence_id}/chain-of-custody")
async def get_chain_of_custody(evidence_id: uuid.UUID, user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await db.get(Evidence, evidence_id):
        raise HTTPException(404, "Evidence not found")
    result = await db.execute(select(CustodyEvent).where(CustodyEvent.evidence_id == evidence_id).order_by(CustodyEvent.created_at))
    return [{"id": str(item.id), "from_person": item.from_person, "from_location": item.from_location, "to_person": item.to_person, "to_location": item.to_location, "reason": item.reason, "condition_before": item.condition_before, "condition_after": item.condition_after, "seal_condition": item.seal_condition, "created_by": item.created_by, "created_at": item.created_at.isoformat()} for item in result.scalars().all()]


@router.post("/{evidence_id}/custody-transfer", status_code=status.HTTP_201_CREATED)
async def transfer_custody(evidence_id: uuid.UUID, payload: dict, user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.get(Evidence, evidence_id)
    if not item:
        raise HTTPException(404, "Evidence not found")
    reason = str(payload.get("reason", "")).strip()
    to_location = str(payload.get("to_location", "")).strip()
    if not reason or not to_location:
        raise HTTPException(422, "reason and to_location are required")
    actor = getattr(user, "username", "authenticated-user")
    event = CustodyEvent(id=uuid.uuid4(), evidence_id=item.id, from_person=item.current_custodian, from_location=item.current_location, to_person=payload.get("to_person"), to_location=to_location, reason=reason, condition_before=payload.get("condition_before"), condition_after=payload.get("condition_after"), seal_condition=payload.get("seal_condition"), created_by=actor, created_at=datetime.utcnow())
    item.current_custodian = payload.get("to_person")
    item.current_location = to_location
    item.status = "IN_TRANSIT" if payload.get("in_transit") else "IN_CUSTODY"
    db.add_all([event, AuditLog(id=uuid.uuid4(), username=actor, action="EVIDENCE_CUSTODY_TRANSFER", resource=f"Evidence:{item.evidence_code}", details=reason, result="SUCCESS", timestamp=datetime.utcnow())])
    await db.commit()
    return {"status": "recorded", "evidence_id": str(item.id), "custody_event_id": str(event.id)}