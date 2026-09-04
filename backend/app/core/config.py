import os

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
    demo_mode: bool = True
    
    # Database & Storage
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # Auth & Security
    secret_key: str = "sentinel-police-command-super-secret-key-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: list[str] = ["*"]
    
    # Integrations & Streaming
    mediamtx_api_url: str = "http://localhost:9997"
    mediamtx_rtsp_url: str = "rtsp://localhost:8554"
    
    # AI Pipeline
    ai_model: str = "yolov8n"
    ai_confidence_threshold: float = 0.50
    ai_anpr_confidence_threshold: float = 0.65

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
