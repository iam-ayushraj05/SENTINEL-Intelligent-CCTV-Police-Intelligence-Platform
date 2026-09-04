import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
try:
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import AsyncSession

from app.core.database import get_db
from app.integrations.gov_adapter import MockGovernmentDataAdapter
from app.models.audit import AuditLog

router = APIRouter()
gov_adapter = MockGovernmentDataAdapter()


class VehicleLookupRequest(BaseModel):
    plate_number: str


class PersonLookupRequest(BaseModel):
    reference_id: str


@router.post("/vehicle-lookup")
async def lookup_vehicle(req: VehicleLookupRequest, db: AsyncSession = Depends(get_db)):
    audit = AuditLog(
        id=uuid.uuid4(),
        username="Operator",
        action="GOV_DB_QUERY_VEHICLE",
        resource=f"VAHAN:{req.plate_number}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()

    record = await gov_adapter.search_vehicle_record(req.plate_number)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle record not found in authorized government registry")
    return record


@router.post("/person-lookup")
async def lookup_person(req: PersonLookupRequest, db: AsyncSession = Depends(get_db)):
    audit = AuditLog(
        id=uuid.uuid4(),
        username="Operator",
        action="GOV_DB_QUERY_PERSON",
        resource=f"POLICE_DB:{req.reference_id}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()

    record = await gov_adapter.search_person_reference(req.reference_id)
    return record
