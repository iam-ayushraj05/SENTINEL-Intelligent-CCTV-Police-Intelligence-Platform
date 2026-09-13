import base64
import hashlib
import io
import os
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "text/csv",
    "application/csv",
}
MAX_FILE_BYTES = 25 * 1024 * 1024


def _encryption_key() -> bytes:
    raw_key = settings.dms_encryption_key
    if not raw_key:
        raise RuntimeError("DMS_ENCRYPTION_KEY is not configured")
    try:
        key = base64.urlsafe_b64decode(raw_key.encode())
    except ValueError as exc:
        raise RuntimeError("DMS_ENCRYPTION_KEY must be urlsafe-base64") from exc
    if len(key) != 32:
        raise RuntimeError("DMS_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt_and_store(data: bytes, owner_id: uuid.UUID) -> tuple[str, str]:
    key = _encryption_key()
    nonce = os.urandom(12)
    encrypted = nonce + AESGCM(key).encrypt(nonce, data, None)
    relative_key = f"{owner_id}/{uuid.uuid4().hex}.bin"
    target = Path(settings.dms_storage_path) / relative_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encrypted)
    return relative_key, hashlib.sha256(data).hexdigest()


def read_and_decrypt(storage_key: str) -> bytes:
    encrypted = (Path(settings.dms_storage_path) / storage_key).read_bytes()
    nonce, ciphertext = encrypted[:12], encrypted[12:]
    return AESGCM(_encryption_key()).decrypt(nonce, ciphertext, None)


def remove_stored_file(storage_key: str) -> None:
    target = Path(settings.dms_storage_path) / storage_key
    target.unlink(missing_ok=True)


def extract_text(data: bytes, mime_type: str) -> str:
    try:
        if mime_type == "application/pdf":
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages).strip()
        if mime_type in {"text/csv", "application/csv"}:
            return data.decode("utf-8-sig", errors="replace")[:100_000]
        if mime_type.startswith("image/"):
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(io.BytesIO(data))).strip()
    except Exception:
        # OCR is best-effort; a failed OCR pass must not lose the encrypted original.
        return ""
    return ""