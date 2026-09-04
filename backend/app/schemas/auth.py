import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800
    user: "UserRead"


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: str
    badge_number: str | None = None
    department_id: uuid.UUID | None = None
    is_active: bool = True
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "OPERATOR"
    badge_number: str | None = None
    department_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    badge_number: str | None = None
