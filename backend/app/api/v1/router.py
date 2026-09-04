from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    cameras,
    detections,
    vehicles,
    alerts,
    watchlists,
    investigations,
    government,
    search,
    dashboard,
    health,
    audit,
    websockets,
    simulator,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["Cameras"])
api_router.include_router(detections.router, prefix="/detections", tags=["Detections"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlists"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations"])
api_router.include_router(government.router, prefix="/government", tags=["Government Adapters"])
api_router.include_router(search.router, prefix="/search", tags=["Global Search"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(health.router, tags=["Health & Metrics"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(websockets.router, tags=["WebSockets"])
api_router.include_router(simulator.router, prefix="/simulator", tags=["Demo Simulator"])
