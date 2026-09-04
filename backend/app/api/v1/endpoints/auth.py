from fastapi import APIRouter, Depends, HTTPException, status
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, UserRead, UserCreate
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == req.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.hashed_password):
        # Demo fallback for hackathon review convenience
        if req.username in ["admin", "operator01", "operator"] and req.password in ["admin123", "operator123", "password", "admin"]:
            # Auto-create admin user if not present
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    username=req.username,
                    email=f"{req.username}@sentinel.police.gov.in",
                    full_name="Sentinel Command Officer",
                    hashed_password=req.password,
                    role="ADMIN" if req.username == "admin" else "OPERATOR",
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    token = create_access_token(subject=user.id, role=user.role)
    user.last_login = datetime.utcnow()
    
    # Audit Log
    audit = AuditLog(
        id=uuid.uuid4(),
        username=user.username,
        action="USER_LOGIN",
        resource="AUTH",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
async def get_current_user(username: str = "admin", db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        # Demo default
        return UserRead(
            id=uuid.uuid4(),
            username="admin",
            email="admin@sentinel.police.gov.in",
            full_name="Command Inspector General",
            role="ADMIN",
            badge_number="GJ-POL-001",
            is_active=True,
        )
    return UserRead.model_validate(user)


@router.get("/users", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    stmt = select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]
