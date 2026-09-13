import os
from pathlib import Path
from typing import Any

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    try:
        from pydantic.v1 import BaseSettings
        SettingsConfigDict = None
    except ImportError:
        try:
            from pydantic import BaseSettings
            SettingsConfigDict = None
        except ImportError:
            class BaseSettings:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            SettingsConfigDict = None


class Settings(BaseSettings):
    app_name: str = "SENTINEL — Unified CCTV Intelligence Platform"
    environment: str = "development"
    demo_mode: bool = False
    
    # Database & Storage
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # Auth & Security
    secret_key: str = "sentinel-police-command-super-secret-key-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: list[str] = ["*"]
    
    try:
        from pydantic import field_validator

        @field_validator("cors_origins", mode="before")
        @classmethod
        def assemble_cors_origins(cls, v: Any) -> list[str]:
            if isinstance(v, str):
                if v.startswith("[") and v.endswith("]"):
                    try:
                        import json
                        return json.loads(v)
                    except Exception:
                        pass
                return [i.strip() for i in v.split(",") if i.strip()]
            if isinstance(v, list):
                return v
            return ["*"]
    except Exception:
        pass
    
    # CCTV Resource Platform
    sentinel_cctv_email: str = ""
    sentinel_cctv_password: str = ""
    sentinel_cctv_host: str = "103.250.160.189"
    sentinel_cctv_rtsp_port: int = 8554
    sentinel_cctv_whep_port: int = 8889
    sentinel_cctv_hls_base: str = "https://cctv.corp8.cloud"
    sentinel_cctv_catalogue_url: str = "https://cctv.corp8.cloud/cameras.json"
    sentinel_cctv_mode: str = "live"

    # Resource & Stream Concurrency Limits
    max_concurrent_viewers: int = 10
    max_ai_cameras: int = 4
    ai_frame_interval_ms: int = 500

    # AI Pipeline
    ai_model: str = "yolov8n"
    ai_confidence_threshold: float = 0.50
    ai_anpr_confidence_threshold: float = 0.65
    ai_model_path: str = "yolo11n.pt"
    ai_event_confirmation_frames: int = 3
    ai_event_cooldown_seconds: int = 30
    ai_face_detection_enabled: bool = True
    ai_face_min_size: int = 40
    high_alert_retry_interval: int = 300
    high_alert_max_retries: int = 5
    evidence_pre_event_seconds: int = 10
    evidence_post_event_seconds: int = 20
    evidence_storage_path: str = "./evidence"
    dms_storage_path: str = "./private-document-storage"
    dms_encryption_key: str = ""
    dms_max_file_bytes: int = 25 * 1024 * 1024
    
    # Emergency & Alert Services
    enable_sms_alerts: bool = True
    enable_voice_calls: bool = True
    enable_tts: bool = True
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Google Maps API
    google_maps_api_key: str = "your_google_maps_api_key"
    
    # OTP Configuration
    otp_expiry_minutes: int = 10
    otp_max_attempts: int = 3
    
    # Hospital & Emergency Services
    default_hospital_api_url: str = "https://api.hospital-service.local/hospitals"
    police_emergency_phone: str = "+91-emergency-phone"
    
    # Multi-camera correlation
    event_correlation_timeout_seconds: int = 30
    camera_proximity_distance_meters: int = 500

    if SettingsConfigDict is not None:
        _backend_dir = Path(__file__).resolve().parents[2]
        _project_root = _backend_dir.parent
        model_config = SettingsConfigDict(
            env_file=(str(_project_root / ".env"), str(_backend_dir / ".env")),
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )


settings = Settings()


def validate_cctv_credentials() -> dict:
    """
    Validates that CCTV credentials are configured.
    Returns a status dict. NEVER includes the actual password value.
    """
    has_email = bool(settings.sentinel_cctv_email)
    has_password = bool(settings.sentinel_cctv_password)

    if not has_email or not has_password:
        return {
            "status": "CCTV_CONFIG_MISSING",
            "email_configured": has_email,
            "password_configured": has_password,
            "message": "CCTV credentials not set in environment. Set SENTINEL_CCTV_EMAIL and SENTINEL_CCTV_PASSWORD.",
        }

    return {
        "status": "CCTV_CONFIG_OK",
        "email_configured": True,
        "password_configured": True,
        "hls_base": settings.sentinel_cctv_hls_base,
        "host": settings.sentinel_cctv_host,
        "mode": settings.sentinel_cctv_mode,
    }
