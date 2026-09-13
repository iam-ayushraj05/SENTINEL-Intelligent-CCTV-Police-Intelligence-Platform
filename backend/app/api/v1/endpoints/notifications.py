from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.emergency import NotificationLog
from app.schemas.auth import UserRead
from app.schemas.emergency import SmsTestRequest
from app.services.notification_service import get_notification_service

router = APIRouter()


def require_admin(user: UserRead = Depends(get_current_user)) -> UserRead:
    if user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required")
    return user


@router.get("/health", dependencies=[Depends(require_admin)])
async def notification_health():
    return get_notification_service().health()


@router.post("/test-sms")
async def test_sms(
    payload: SmsTestRequest,
    db: AsyncSession = Depends(get_db),
    _: UserRead = Depends(require_admin),
):
    service = get_notification_service()
    result = await service.send_sms(payload.phone_number, payload.message)
    accepted = result.get("status") == "SMS_ACCEPTED"
    log = NotificationLog(
        message=payload.message,
        status=result.get("status", "FAILED"),
        provider_message_id=result.get("message_sid"),
        error_code=result.get("error_code"),
        error_message=result.get("error"),
        sent_at=datetime.utcnow() if accepted else None,
    )
    db.add(log)
    await db.commit()
    if not accepted:
        error_code = result.get("error_code") or "SMS_PROVIDER_REJECTED"
        code = 400 if error_code == "INVALID_PHONE_NUMBER" else 503 if error_code == "SMS_PROVIDER_NOT_CONFIGURED" else 502
        raise HTTPException(
            status_code=code,
            detail={
                "success": False,
                "error_code": error_code,
                "message": result.get("error") or "SMS provider rejected the request.",
            },
        )
    return {
        "success": True,
        "status": result["status"],
        "provider": result.get("provider", "twilio"),
        "simulated": result.get("simulated", False),
        "provider_message_id": result["message_sid"],
        "phone_number": result["phone_number"],
    }
