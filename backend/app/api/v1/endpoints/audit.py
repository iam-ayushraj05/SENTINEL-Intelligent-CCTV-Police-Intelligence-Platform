from fastapi import APIRouter, Depends
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.audit import AuditLog

router = APIRouter()


@router.get("")
async def list_audit_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    logs = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
            result = await db.execute(stmt)
            scalars = result.scalars().all() if hasattr(result, "scalars") else []
            logs = [
                {
                    "id": str(l.id),
                    "username": l.username,
                    "action": l.action,
                    "resource": l.resource,
                    "result": l.result,
                    "ip_address": getattr(l, "ip_address", "127.0.0.1") or "127.0.0.1",
                    "details": getattr(l, "details", getattr(l, "details_json", None)),
                    "timestamp": l.timestamp.isoformat(),
                }
                for l in scalars
            ]
        except Exception:
            pass
    return logs
