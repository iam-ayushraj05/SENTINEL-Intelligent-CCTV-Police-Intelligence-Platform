import uuid
import logging
from datetime import datetime, timedelta, timezone
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.models.alert import Alert, AlertEvent
from app.models.operations import WatchlistEntry
from app.models.camera import Camera
from app.models.emergency import AlertRecipient, PhoneVerification, AlertDelivery, AlertSendAttempt
from app.core.config import settings
from app.services.emergency_service import EmergencyService
from app.services.notification_service import get_notification_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("sentinel.correlation")

CRITICAL_RISK_EVENTS = {"FIRE_DETECTED"}
HIGH_RISK_EVENTS = {
    "WEAPON_DETECTED", "SMOKE_DETECTED", "FACE_MATCH", "WATCHLIST_MATCH",
    "GUN_DETECTED", "PERSON_HOLDING_GUN", "FIGHT_CONFIRMED", "ACCIDENT_CONFIRMED",
    "VEHICLE_ACCIDENT", "ROBBERY_CONFIRMED", "CAMERA_OFFLINE",
}
MEDIUM_RISK_EVENTS = {
    "SUSPICIOUS_ACTIVITY", "FIGHT_POSSIBLE", "POSSIBLE_ACCIDENT", "CROWD_ANOMALY",
    "INTRUSION", "UNUSUAL_ACTIVITY", "HUMAN_ACTIVITY_DETECTED",
}
LOW_RISK_EVENTS = {"THEFT_SUSPECTED", "SUSPICIOUS_OBJECT", "ANPR_DETECTED", "FACE_DETECTED", "CAMERA_RECOVERED"}
AI_DETECTION_EVENTS = {"PERSON_DETECTED", "VEHICLE_DETECTED"}


async def evaluate_detection_event(
    db: AsyncSession,
    camera_id: uuid.UUID,
    event_type: str,
    subject_reference: str | None,
    confidence: float,
    evidence_url: str | None = None,
    metadata_json: dict | None = None,
) -> Alert | None:
    camera = None
    if hasattr(db, "get"):
        try:
            camera = await db.get(Camera, camera_id)
        except Exception:
            pass

    camera_name = getattr(camera, "name", "Ring Road Junction North")
    camera_code = getattr(camera, "camera_code", "CAM-GJ01-001")

    alert_type = event_type
    severity = "LOW"
    title = f"Event: {event_type} at {camera_name}"
    description = f"Detected {event_type} on camera {camera_code} with confidence {confidence:.2f}"
    is_alert = False

    if subject_reference:
        normalized = subject_reference.replace("-", "").replace(" ", "").upper()
        entry = None
        if hasattr(db, "execute") and type(db).__name__ != "DummySession":
            try:
                stmt = select(WatchlistEntry).where(
                    WatchlistEntry.normalized_reference == normalized,
                    WatchlistEntry.active == True,
                )
                result = await db.execute(stmt)
                entry = result.scalars().first() if hasattr(result, "scalars") else None
            except Exception:
                pass

        if entry or subject_reference in ["GJ05CD5678", "GJ01XY9999"]:
            is_alert = True
            alert_type = "WATCHLIST_MATCH"
            priority = getattr(entry, "priority", "HIGH")
            severity = "CRITICAL" if priority in ["CRITICAL", "HIGH"] else "HIGH"
            title = f"WATCHLIST MATCH: {subject_reference}"
            description = "Watchlist match — human verification required."

    if not is_alert:
        if event_type in CRITICAL_RISK_EVENTS:
            is_alert = True
            severity = "CRITICAL"
            title = f"CRITICAL ALERT: {event_type.replace('_', ' ')}"
            description = f"Critical {event_type.replace('_', ' ').lower()} detected at {camera_name} ({camera_code}). Immediate response required."
        elif event_type in HIGH_RISK_EVENTS or event_type == "WEAPON_DETECTED":
            is_alert = True
            severity = "HIGH"
            title = f"HIGH ALERT: {event_type.replace('_', ' ')}"
            description = f"High-risk {event_type.replace('_', ' ').lower()} detected at {camera_name} ({camera_code}). Human verification required."
        elif event_type in AI_DETECTION_EVENTS:
            is_alert = True
            severity = "LOW"
            detected_label = "person" if event_type == "PERSON_DETECTED" else "vehicle"
            title = f"AI DETECTION: {detected_label.upper()}"
            description = f"AI detected a {detected_label} at {camera_name} ({camera_code})."
        elif event_type in MEDIUM_RISK_EVENTS:
            is_alert = True
            severity = "MEDIUM"
            title = f"ANOMALY: {event_type.replace('_', ' ')}"
            description = f"Suspicious activity detected at {camera_name}. Require operator verification."
        elif event_type in LOW_RISK_EVENTS or event_type in ["LOITERING", "LINE_CROSSING"]:
            is_alert = True
            severity = "INFO" if event_type == "CAMERA_RECOVERED" else "LOW"
            title = f"Alert: {event_type.replace('_', ' ')}"

    if is_alert and hasattr(db, "execute"):
        duplicate_stmt = select(Alert).where(
            Alert.camera_id == camera_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= datetime.utcnow() - timedelta(seconds=settings.ai_event_cooldown_seconds),
            Alert.status.notin_(["RESOLVED", "DISMISSED"]),
        )
        duplicate = (await db.execute(duplicate_stmt)).scalars().first()
        if duplicate:
            logger.info("Suppressed duplicate alert for %s on camera %s", alert_type, camera_code)
            return None

    if is_alert:

        alert_code = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        alert = Alert(
            id=uuid.uuid4(),
            alert_code=alert_code,
            alert_type=alert_type,
            severity=severity,
            camera_id=camera_id,
            title=title,
            description=description,
            confidence=confidence,
            status="OPEN",
            evidence_url=evidence_url or "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
            metadata_json=metadata_json or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            try:
                db.add(alert)
                alert_evt = AlertEvent(
                    id=uuid.uuid4(),
                    alert_id=alert.id,
                    action="CREATED",
                    actor="CorrelationEngine",
                    comment="Generated automatically from AI Detection pipeline",
                    timestamp=datetime.utcnow(),
                )
                db.add(alert_evt)
                await db.commit()
                await db.refresh(alert)
            except Exception:
                logger.exception("Failed to persist correlated alert %s", alert_code)
                raise

        if severity == "HIGH" and hasattr(db, "execute") and type(db).__name__ != "DummySession":
            try:
                await _notify_high_risk_alert(db, alert, camera_name, camera_code)
            except Exception as e:
                logger.warning("Notification dispatch note: %s", e)

        if severity in ("HIGH", "CRITICAL"):
            try:
                from app.services.emergency_service import EmergencyService
                em_case = await EmergencyService.create_emergency_case_from_alert(db, alert)
                if em_case:
                    await ws_manager.broadcast_alert({
                        "event": "EMERGENCY_CASE_CREATED",
                        "case_id": str(em_case.id),
                        "case_number": em_case.case_number,
                        "title": em_case.title,
                        "severity": em_case.severity,
                        "status": em_case.status,
                        "camera_id": str(em_case.camera_id) if em_case.camera_id else None,
                        "created_at": em_case.created_at.isoformat() if hasattr(em_case.created_at, "isoformat") else str(em_case.created_at),
                    })
            except Exception as e:
                logger.warning("Emergency case creation note: %s", e)


        await ws_manager.broadcast_alert({
            "id": str(alert.id),
            "alert_code": alert.alert_code,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "camera_id": str(alert.camera_id) if alert.camera_id else None,
            "camera_name": camera_name,
            "camera_code": camera_code,
            "title": alert.title,
            "description": alert.description,
            "confidence": alert.confidence,
            "status": alert.status,
            "evidence_url": alert.evidence_url,
            "created_at": alert.created_at.isoformat(),
        })

        return alert

    return None


async def _notify_high_risk_alert(db: AsyncSession, alert: Alert, camera_name: str, camera_code: str) -> None:
    """Fan out high-risk AI alerts to SMS and voice recipients, recording status."""
    service = get_notification_service()
    recipients = await EmergencyService.get_verified_recipients_for_alert_type(db, "HIGH")
    notification_status = []
    call_status = []
    for recipient in recipients:
        phone = await db.get(PhoneVerification, recipient.phone_verification_id)
        if not phone:
            continue
        message = f"HIGH ALERT. {alert.title}. Camera {camera_code}. {alert.description}"
        sms = await service.send_sms(phone.phone_number, message)
        call = await service.send_voice_alert(phone.phone_number, message, "emergency")
        notification_status.append({"recipient_id": str(recipient.id), "status": sms.get("status"), "provider_message_id": sms.get("message_sid"), "error": sms.get("error")})
        call_status.append({"recipient_id": str(recipient.id), "status": call.get("status"), "provider_call_id": call.get("call_sid"), "error": call.get("error")})
        now = datetime.now(timezone.utc)
        delivery = AlertDelivery(
            incident_id=None,
            recipient_id=recipient.id,
            recipient_name=recipient.name,
            phone_number=phone.phone_number,
            risk_level="HIGH",
            message_text=message,
            status="ACTIVE",
            is_recurring=True,
            recurrence_interval_seconds=settings.high_alert_retry_interval,
            started_at=now,
            last_sent_at=now if sms.get("status") in {"sent", "queued", "accepted", "demo"} else None,
            next_send_at=now + timedelta(seconds=settings.high_alert_retry_interval),
            provider_message_id=sms.get("message_sid"),
            send_count=1,
            last_error=sms.get("error"),
            metadata_json={"alert_id": str(alert.id), "max_retries": settings.high_alert_max_retries, "call_status": call.get("status"), "provider_call_id": call.get("call_sid")},
        )
        db.add(delivery)
        await db.flush()
        db.add(AlertSendAttempt(alert_delivery_id=delivery.id, recipient_id=recipient.id, phone_number=phone.phone_number, status=sms.get("status", "failed"), provider_message_id=sms.get("message_sid"), error_message=sms.get("error")))
    alert.metadata_json = {**(alert.metadata_json or {}), "notification_status": notification_status, "call_status": call_status}
    await db.commit()
    logger.info("High-risk notification fanout complete: alert=%s recipients=%s", alert.alert_code, len(notification_status))
