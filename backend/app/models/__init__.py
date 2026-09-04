from app.models.base import Base
from app.models.user import User, Role, Permission, user_roles, role_permissions
from app.models.camera import Camera, CameraSource, CameraHealthEvent
from app.models.detection import Detection, DetectionTrack, DetectionEvent
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.person import Person, PersonObservation, PersonMatch
from app.models.operations import (
    Department,
    Watchlist,
    WatchlistEntry,
    Investigation,
    InvestigationEvent,
    InvestigationNote,
)
from app.models.alert import Alert, AlertEvent, AlertAssignment
from app.models.evidence import Evidence
from app.models.government import GovernmentSource, ExternalRecord
from app.models.audit import AuditLog
from app.models.settings import SystemSetting

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "Camera",
    "CameraSource",
    "CameraHealthEvent",
    "Detection",
    "DetectionTrack",
    "DetectionEvent",
    "Vehicle",
    "VehicleSighting",
    "Person",
    "PersonObservation",
    "PersonMatch",
    "Department",
    "Watchlist",
    "WatchlistEntry",
    "Investigation",
    "InvestigationEvent",
    "InvestigationNote",
    "Alert",
    "AlertEvent",
    "AlertAssignment",
    "Evidence",
    "GovernmentSource",
    "ExternalRecord",
    "AuditLog",
    "SystemSetting",
]
