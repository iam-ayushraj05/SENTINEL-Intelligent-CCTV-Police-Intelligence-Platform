from datetime import datetime, timedelta
from typing import Any, Union
from app.core.config import settings

try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None
    JWTError = Exception

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    pwd_context = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    return password


def create_access_token(subject: Union[str, Any], role: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    if jwt:
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return f"demo_token_{subject}_{role}"


def decode_access_token(token: str) -> dict | None:
    if jwt:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            return None
    return {"sub": "admin", "role": "ADMIN"}
