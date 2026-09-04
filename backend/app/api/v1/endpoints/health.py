from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "sentinel-api", "demo_mode": True}


@router.get("/health/services")
async def health_services():
    return {
        "status": "healthy",
        "services": {
            "postgresql": {"status": "UP", "latency_ms": 1.2},
            "redis": {"status": "UP", "latency_ms": 0.8},
            "kafka": {"status": "UP", "latency_ms": 2.1},
            "mediamtx": {"status": "UP", "latency_ms": 3.5},
            "ai_workers": {"status": "UP", "active_workers": 4, "fps": 28.5},
        },
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    metrics = """# HELP sentinel_active_cameras Total active registered cameras
# TYPE sentinel_active_cameras gauge
sentinel_active_cameras 6

# HELP sentinel_active_alerts Current active open/investigating alerts
# TYPE sentinel_active_alerts gauge
sentinel_active_alerts 2

# HELP sentinel_ai_inferences_total Total AI inferences completed
# TYPE sentinel_ai_inferences_total counter
sentinel_ai_inferences_total 14520

# HELP sentinel_ai_fps Current average AI inference FPS
# TYPE sentinel_ai_fps gauge
sentinel_ai_fps 28.5

# HELP sentinel_http_requests_total Total HTTP requests processed
# TYPE sentinel_http_requests_total counter
sentinel_http_requests_total 312
"""
    return metrics
