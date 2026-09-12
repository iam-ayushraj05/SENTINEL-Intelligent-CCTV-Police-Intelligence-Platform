import uuid
from datetime import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
from pathlib import Path

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.person import Person
from app.models.alert import Alert
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.models.operations import Investigation, InvestigationNote
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_person_records(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = select(Person).order_by(Person.created_at.desc())
    if search:
        stmt = stmt.where(Person.full_name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    records = result.scalars().all() if hasattr(result, "scalars") else []
    return [{
        "id": str(item.id),
        "person_code": item.person_code,
        "full_name": item.full_name,
        "alias": item.alias,
        "case_id": item.case_id,
        "case_title": item.case_title,
        "case_status": item.case_status,
        "assigned_officer": item.assigned_officer,
        "phone_number": item.phone_number,
        "address": item.address,
        "notes": item.notes,
        "date_of_birth": item.date_of_birth.isoformat() if item.date_of_birth else None,
        "gender": item.gender,
        "agency_unit": item.agency_unit,
        "metadata_json": item.metadata_json or {},
        "created_at": item.created_at.isoformat() if item.created_at else None,
    } for item in records if (item.metadata_json or {}).get("owner_user_id") in {None, str(current_user.id)}]


def _validate_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    compact = re.sub(r"[\s().-]", "", phone)
    if compact.startswith("0") and len(compact) == 11:
        compact = "+91" + compact[1:]
    elif compact.startswith("91") and len(compact) == 12:
        compact = "+" + compact
    if not re.fullmatch(r"\+91[6-9]\d{9}", compact):
        raise HTTPException(status_code=422, detail="Phone number must be a valid Indian mobile number")
    return compact


@router.post("/intake", status_code=201, response_model=dict)
async def create_person_intake(
    full_name: str = Form(...),
    case_title: str = Form(...),
    alias: str | None = Form(None),
    date_of_birth: str | None = Form(None),
    gender: str | None = Form(None),
    agency_unit: str | None = Form(None),
    phone_number: str | None = Form(None),
    address: str | None = Form(None),
    case_notes: str | None = Form(None),
    photo: UploadFile | None = File(None),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not full_name.strip() or not case_title.strip():
        raise HTTPException(status_code=422, detail="Full name and case title are required")
    parsed_dob = None
    if date_of_birth:
        try:
            parsed_dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Date of birth must use YYYY-MM-DD") from exc
    normalized_phone = _validate_phone(phone_number)
    photo_bytes = None
    photo_extension = None
    if photo:
        if photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Photo must be JPEG, PNG, or WebP")
        photo_bytes = await photo.read()
        if len(photo_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Photo must be smaller than 10 MB")
        photo_extension = Path(photo.filename or "photo.jpg").suffix.lower() or ".jpg"

    now = datetime.utcnow()
    case_id = uuid.uuid4()
    person_id = uuid.uuid4()
    case_number = f"CASE-{now.year}-GJ-{uuid.uuid4().hex[:6].upper()}"
    person_code = f"PERSON-{uuid.uuid4().hex[:8].upper()}"
    target = Path(settings.evidence_storage_path) / "persons" / str(person_id) / f"identity{photo_extension}" if photo_bytes else None
    try:
        case = Investigation(id=case_id, case_number=case_number, title=case_title.strip(), description=case_notes, status="OPEN", assigned_officer_name=current_user.full_name, created_by=current_user.username, created_at=now, updated_at=now)
        person = Person(id=person_id, person_code=person_code, full_name=full_name.strip(), alias=alias, case_id=str(case_id), case_title=case.title, case_status="OPEN", assigned_officer=current_user.full_name, agency_unit=agency_unit, phone_number=normalized_phone, address=address, notes=case_notes, date_of_birth=parsed_dob, gender=gender, metadata_json={"manual_entry": True, "owner_user_id": str(current_user.id), "agency_unit": agency_unit, "idempotency_key": idempotency_key})
        db.add(case)
        db.add(person)
        if case_notes:
            db.add(InvestigationNote(id=uuid.uuid4(), investigation_id=case_id, author=current_user.full_name, note=case_notes, created_at=now))
        db.add(AuditLog(id=uuid.uuid4(), username=current_user.username, action="PERSON_RECORD_CREATE", resource=f"Person:{person_code}", result="SUCCESS", timestamp=now))
        if photo_bytes and target:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(photo_bytes)
            photo_url = f"/api/v1/persons/{person_id}/photo"
            person.metadata_json = {**person.metadata_json, "photo_url": photo_url, "photo_filename": photo.filename}
            db.add(Evidence(id=uuid.uuid4(), file_name=photo.filename or "identity-photo", file_path=photo_url, mime_type=photo.content_type or "image/jpeg", investigation_id=case_id, evidence_code=f"EVD-{uuid.uuid4().hex[:8].upper()}", evidence_type="IDENTITY_PHOTO", description=f"Manual identity photo for {person_code}", current_custodian=current_user.full_name, metadata_json={"person_id": str(person_id), "storage_path": str(target)}))
        await db.commit()
    except Exception as exc:
        await db.rollback()
        if target and target.exists():
            target.unlink()
        raise HTTPException(status_code=500, detail="Person record and case could not be saved") from exc
    return {"id": str(person_id), "person_code": person_code, "case_id": str(case_id), "status": "created"}


@router.post("", status_code=201, response_model=dict)
async def create_person_record(payload: dict, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    person_code = f"PERSON-{uuid.uuid4().hex[:8].upper()}"
    person = Person(
        id=uuid.uuid4(),
        person_code=person_code,
        full_name=payload.get("full_name"),
        alias=payload.get("alias"),
        case_id=payload.get("case_id"),
        case_title=payload.get("case_title"),
        case_status=payload.get("case_status") or "OPEN",
        assigned_officer=payload.get("assigned_officer") or "Officer",
        agency_unit=payload.get("agency_unit"),
        phone_number=payload.get("phone_number"),
        address=payload.get("address"),
        notes=payload.get("notes"),
        date_of_birth=datetime.fromisoformat(payload["date_of_birth"]) if payload.get("date_of_birth") else None,
        gender=payload.get("gender"),
        metadata_json={"manual_entry": True, "owner_user_id": str(current_user.id), **(payload.get("metadata_json") or {})},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(person)
    db.add(AuditLog(
        id=uuid.uuid4(),
        username=current_user.username,
        action="PERSON_RECORD_CREATE",
        resource=f"Person:{person_code}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    ))
    await db.commit()
    await db.refresh(person)
    return {"id": str(person.id), "person_code": person_code, "status": "created"}


@router.post("/{person_id}/photo")
async def upload_person_photo(person_id: uuid.UUID, photo: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person record not found")
    if photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Photo must be JPEG, PNG, or WebP")
    content = await photo.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo must be smaller than 10 MB")
    folder = Path(settings.evidence_storage_path) / "persons" / str(person.id)
    folder.mkdir(parents=True, exist_ok=True)
    extension = Path(photo.filename or "photo.jpg").suffix.lower() or ".jpg"
    target = folder / f"identity{extension}"
    target.write_bytes(content)
    photo_url = f"/api/v1/persons/{person.id}/photo"
    person.metadata_json = {**(person.metadata_json or {}), "photo_url": photo_url, "photo_filename": photo.filename}
    if person.case_id:
        try:
            case_id = uuid.UUID(str(person.case_id))
            db.add(Evidence(
                id=uuid.uuid4(),
                file_name=photo.filename or "identity-photo",
                file_path=photo_url,
                mime_type=photo.content_type or "image/jpeg",
                investigation_id=case_id,
                evidence_code=f"EVD-{uuid.uuid4().hex[:8].upper()}",
                evidence_type="IDENTITY_PHOTO",
                description=f"Manual identity photo for {person.person_code}",
                current_custodian="Operator",
                metadata_json={"person_id": str(person.id), "storage_path": str(target)},
            ))
        except ValueError:
            pass
    await db.commit()
    return {"person_id": str(person.id), "photo_url": person.metadata_json["photo_url"]}


@router.get("/{person_id}/photo")
async def get_person_photo(person_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person record not found")
    if (person.metadata_json or {}).get("owner_user_id") not in {None, str(current_user.id)}:
        raise HTTPException(status_code=403, detail="You do not have access to this person record")
    folder = (Path(settings.evidence_storage_path) / "persons" / str(person.id)).resolve()
    matches = [path for path in folder.glob("identity.*") if path.is_file()] if folder.exists() else []
    if not matches:
        raise HTTPException(status_code=404, detail="Person photo not found")
    return FileResponse(matches[0])


@router.post("/{person_id}/associate-alert")
async def associate_alert_with_person(person_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person record not found")
    alert_id = payload.get("alert_id")
    if alert_id:
        alert = await db.get(Alert, uuid.UUID(str(alert_id)))
        if alert:
            alert.metadata_json = {**(alert.metadata_json or {}), "associated_person_id": str(person.id), "associated_person_code": person.person_code, "case_association_notice": f"This alert has been associated with Person Record {person.person_code}."}
            alert.verification_status = "VERIFIED"
            alert.investigation_status = "ASSOCIATED"
    await db.commit()
    return {"status": "associated", "person_id": str(person.id), "person_code": person.person_code, "message": f"This alert has been associated with Person Record {person.person_code}."}
