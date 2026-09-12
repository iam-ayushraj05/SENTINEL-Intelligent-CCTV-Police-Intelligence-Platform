import random
import string
from datetime import datetime, timedelta
from fastapi import HTTPException

try:
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.models.emergency import PhoneVerification
from app.core.config import settings


class OTPService:
    """Manages OTP generation, sending, and verification."""

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random OTP."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    async def create_otp_for_phone(db: AsyncSession, phone_number: str) -> str:
        """Create and store OTP for a phone number."""
        # Check if phone verification record exists
        stmt = select(PhoneVerification).where(PhoneVerification.phone_number == phone_number)
        result = await db.execute(stmt)
        phone_record = result.scalar_one_or_none()

        if phone_record is None:
            # Create new phone verification record
            phone_record = PhoneVerification(
                phone_number=phone_number,
                is_verified=False
            )
            db.add(phone_record)

        # Generate OTP
        otp = OTPService.generate_otp()
        phone_record.otp = otp
        phone_record.otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.otp_expiry_minutes)
        phone_record.failed_attempts = 0
        await db.commit()

        return otp

    @staticmethod
    async def verify_otp(db: AsyncSession, phone_number: str, otp: str) -> dict:
        """Verify OTP for a phone number."""
        stmt = select(PhoneVerification).where(PhoneVerification.phone_number == phone_number)
        result = await db.execute(stmt)
        phone_record = result.scalar_one_or_none()

        if not phone_record:
            raise HTTPException(status_code=404, detail="Phone number not found")

        if phone_record.is_blocked:
            raise HTTPException(status_code=403, detail="Phone number is blocked due to multiple failed attempts")

        if phone_record.otp_expires_at and datetime.utcnow() > phone_record.otp_expires_at:
            raise HTTPException(status_code=400, detail="OTP has expired")

        if phone_record.otp != otp:
            phone_record.failed_attempts += 1
            if phone_record.failed_attempts >= settings.otp_max_attempts:
                phone_record.is_blocked = True
                phone_record.block_reason = "Too many failed OTP attempts"
            await db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Mark as verified
        phone_record.is_verified = True
        phone_record.verification_timestamp = datetime.utcnow()
        phone_record.otp = None  # Clear OTP after verification
        phone_record.otp_expires_at = None
        phone_record.failed_attempts = 0
        await db.commit()

        return {
            "status": "verified",
            "phone_number": phone_number,
            "verification_timestamp": phone_record.verification_timestamp
        }

    @staticmethod
    async def get_verification_status(db: AsyncSession, phone_number: str) -> dict:
        """Get verification status for a phone number."""
        stmt = select(PhoneVerification).where(PhoneVerification.phone_number == phone_number)
        result = await db.execute(stmt)
        phone_record = result.scalar_one_or_none()

        if not phone_record:
            return {
                "status": "not_registered",
                "phone_number": phone_number
            }

        return {
            "status": "verified" if phone_record.is_verified else ("blocked" if phone_record.is_blocked else "pending"),
            "phone_number": phone_number,
            "is_verified": phone_record.is_verified,
            "is_blocked": phone_record.is_blocked,
            "verification_timestamp": phone_record.verification_timestamp
        }

    @staticmethod
    async def unblock_phone(db: AsyncSession, phone_number: str) -> dict:
        """Unblock a phone number (admin only)."""
        stmt = select(PhoneVerification).where(PhoneVerification.phone_number == phone_number)
        result = await db.execute(stmt)
        phone_record = result.scalar_one_or_none()

        if not phone_record:
            raise HTTPException(status_code=404, detail="Phone number not found")

        phone_record.is_blocked = False
        phone_record.block_reason = None
        phone_record.failed_attempts = 0
        await db.commit()

        return {
            "status": "unblocked",
            "phone_number": phone_number
        }
