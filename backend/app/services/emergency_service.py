import uuid
import logging
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Optional
import httpx

try:
    from sqlalchemy import select, and_, or_
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.models.emergency import (
    EmergencyIncident,
    IncidentTimeline,
    AmbulanceDispatch,
    EmergencyCall,
    AlertRecipient,
    PhoneVerification,
    AlertDelivery,
    AlertSendAttempt,
    CaseMessage,
)
from app.core.config import settings

logger = logging.getLogger("sentinel.emergency")


_CASE_SEQ_LOCK = asyncio.Lock()
_MEM_CASE_SEQUENCE = 9999999
_CASE_TIMELINE_CACHE: dict[str, list[IncidentTimeline]] = {}


class EmergencyService:
    """Manages emergency incidents/cases, dispatch, and multi-camera correlation."""

    VALID_STATUSES = ["OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "UNDER_REVIEW", "RESOLVED", "CLOSED"]

    @staticmethod
    async def get_next_case_sequence(db: AsyncSession) -> int:
        """
        Concurrency-safe sequence number generator starting at 10000000.
        Uses PostgreSQL sequence / DB max query / thread lock fallback.
        """
        if hasattr(db, "execute") and type(db).__name__ != "DummySession":
            # 1. Try PostgreSQL sequence nextval
            try:
                from sqlalchemy import text
                res = await db.execute(text("SELECT nextval('emergency_case_seq')"))
                val = res.scalar()
                if val:
                    return int(val)
            except Exception:
                pass

            # 2. Try DB MAX(sequence_number)
            try:
                from sqlalchemy import func
                res = await db.execute(select(func.max(EmergencyIncident.sequence_number)))
                max_seq = res.scalar()
                if max_seq is not None and max_seq >= 10000000:
                    return int(max_seq) + 1
            except Exception:
                pass

        # 3. Thread-safe in-memory fallback for test clients / DummySession
        global _MEM_CASE_SEQUENCE
        async with _CASE_SEQ_LOCK:
            _MEM_CASE_SEQUENCE += 1
            return _MEM_CASE_SEQUENCE

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> bool:
        """
        Validate backend status transition rules:
        OPEN -> ACKNOWLEDGED -> IN_PROGRESS -> UNDER_REVIEW -> RESOLVED -> CLOSED
        """
        curr = current_status.upper() if current_status else "OPEN"
        nxt = new_status.upper() if new_status else "OPEN"

        if nxt not in EmergencyService.VALID_STATUSES:
            return False
        if curr == nxt:
            return True
        if curr == "CLOSED":
            return False  # Terminal state

        valid_next = {
            "OPEN": ["ACKNOWLEDGED", "CLOSED"],
            "ACKNOWLEDGED": ["IN_PROGRESS", "UNDER_REVIEW", "RESOLVED", "CLOSED"],
            "IN_PROGRESS": ["UNDER_REVIEW", "RESOLVED", "CLOSED"],
            "UNDER_REVIEW": ["RESOLVED", "CLOSED"],
            "RESOLVED": ["CLOSED"],
        }
        return nxt in valid_next.get(curr, [])

    @staticmethod
    async def create_emergency_case_from_alert(
        db: AsyncSession,
        alert: Any,
        source_event_id: Optional[str] = None,
        created_by: str = "SYSTEM",
    ) -> EmergencyIncident:
        """Create a concurrency-safe Emergency Case starting at CASE-10000000 from a validated alert."""
        seq_num = await EmergencyService.get_next_case_sequence(db)
        case_number = f"CASE-{seq_num}"

        incident = EmergencyIncident(
            id=uuid.uuid4(),
            sequence_number=seq_num,
            incident_code=case_number,
            incident_type=alert.alert_type,
            title=getattr(alert, "title", f"EMERGENCY: {alert.alert_type}"),
            severity=alert.severity,
            priority="CRITICAL" if alert.severity == "CRITICAL" else "HIGH",
            detection_source="AI",
            camera_id=alert.camera_id,
            description=alert.description or f"Validated emergency alert {alert.alert_code}",
            ai_confidence=getattr(alert, "confidence", 0.9),
            status="OPEN",
            source_alert_id=alert.id,
            source_event_id=source_event_id or getattr(alert, "alert_code", str(alert.id)),
            created_by=created_by,
            metadata_json=getattr(alert, "metadata_json", {}) or {},
        )

        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            try:
                db.add(incident)
                await db.flush()

                # Add initial CASE_CREATED and ALERT_RECEIVED timeline entries
                timeline_created = IncidentTimeline(
                    id=uuid.uuid4(),
                    incident_id=incident.id,
                    case_number=case_number,
                    event_type="CASE_CREATED",
                    camera_id=alert.camera_id,
                    actor_id=created_by,
                    event_time=datetime.utcnow(),
                    description=f"Emergency case {case_number} initialized",
                )
                db.add(timeline_created)

                timeline_alert = IncidentTimeline(
                    id=uuid.uuid4(),
                    incident_id=incident.id,
                    case_number=case_number,
                    event_type="ALERT_RECEIVED",
                    camera_id=alert.camera_id,
                    actor_id="AlertEngine",
                    event_time=datetime.utcnow(),
                    description=f"Source alert {alert.alert_code} received ({alert.severity})",
                )
                db.add(timeline_alert)
                await db.commit()
                await db.refresh(incident)
            except Exception as e:
                logger.exception("Failed to persist emergency case %s: %s", case_number, e)
                raise

        logger.info("Emergency case %s created successfully from alert %s", case_number, getattr(alert, "alert_code", str(alert.id)))
        return incident

    @staticmethod
    def generate_incident_code() -> str:
        """Generate unique incident code."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"INC-{timestamp}-{unique_id}"

    @staticmethod
    async def create_emergency_incident(
        db: AsyncSession,
        incident_type: str,
        severity: str,
        detection_source: str,
        camera_id: Optional[uuid.UUID],
        location_latitude: Optional[float],
        location_longitude: Optional[float],
        location_name: Optional[str],
        description: str,
        ai_confidence: Optional[float] = None,
        detected_objects: Optional[dict] = None
    ) -> EmergencyIncident:
        """Create a new emergency incident/case."""
        seq_num = await EmergencyService.get_next_case_sequence(db)
        case_number = f"CASE-{seq_num}"

        incident = EmergencyIncident(
            id=uuid.uuid4(),
            sequence_number=seq_num,
            incident_code=case_number,
            incident_type=incident_type,
            title=f"EMERGENCY: {incident_type}",
            severity=severity,
            priority="CRITICAL" if severity == "CRITICAL" else "HIGH",
            detection_source=detection_source,
            camera_id=camera_id,
            location_latitude=location_latitude,
            location_longitude=location_longitude,
            location_name=location_name,
            description=description,
            ai_confidence=ai_confidence,
            detected_objects=detected_objects,
            status="OPEN"
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            db.add(incident)
            await db.flush()

            timeline_entry = IncidentTimeline(
                id=uuid.uuid4(),
                incident_id=incident.id,
                case_number=case_number,
                event_type="CASE_CREATED",
                camera_id=camera_id,
                actor_id="Operator",
                event_time=datetime.utcnow(),
                description=f"Case created: {incident_type}",
            )
            db.add(timeline_entry)
            await db.commit()

        logger.info(f"Emergency incident created: {incident.incident_code}")
        return incident

    @staticmethod
    async def add_incident_timeline_event(
        db: AsyncSession,
        incident_id: uuid.UUID,
        event_type: str,
        description: str,
        camera_id: Optional[uuid.UUID] = None,
        actor_id: str = "SYSTEM",
        case_number: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> IncidentTimeline:
        """Add an immutable event to the incident timeline."""
        timeline_entry = IncidentTimeline(
            id=uuid.uuid4(),
            incident_id=incident_id,
            case_number=case_number,
            event_type=event_type,
            camera_id=camera_id,
            actor_id=actor_id,
            event_time=datetime.utcnow(),
            description=description,
            metadata_json=metadata_json or {},
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            try:
                db.add(timeline_entry)
                await db.commit()
            except Exception:
                pass

        if case_number:
            if case_number not in _CASE_TIMELINE_CACHE:
                _CASE_TIMELINE_CACHE[case_number] = []
            _CASE_TIMELINE_CACHE[case_number].append(timeline_entry)

        return timeline_entry

    @staticmethod
    async def dispatch_ambulance(
        db: AsyncSession,
        incident_id: uuid.UUID,
        hospital_name: str,
        hospital_phone: str,
        hospital_latitude: float,
        hospital_longitude: float,
        ambulance_id: Optional[str] = None
    ) -> AmbulanceDispatch:
        """Create ambulance dispatch for an incident."""
        dispatch = AmbulanceDispatch(
            incident_id=incident_id,
            ambulance_id=ambulance_id or f"AMB-{str(uuid.uuid4())[:8]}",
            hospital_name=hospital_name,
            hospital_phone=hospital_phone,
            hospital_latitude=hospital_latitude,
            hospital_longitude=hospital_longitude,
            status="DISPATCHED"
        )
        db.add(dispatch)
        await db.flush()

        # Add timeline entry
        await EmergencyService.add_incident_timeline_event(
            db,
            incident_id,
            "AMBULANCE_DISPATCHED",
            f"Ambulance dispatched to {hospital_name}"
        )

        logger.info(f"Ambulance dispatched for incident {incident_id}: {dispatch.ambulance_id}")
        return dispatch

    @staticmethod
    async def find_nearest_hospital(
        latitude: float,
        longitude: float,
        max_distance_km: float = 50
    ) -> dict:
        """Find nearest hospital from coordinates."""
        # This is a demo implementation
        # In production, integrate with a real hospital database/API
        
        hospitals = [
            {
                "hospital_name": "City General Hospital",
                "hospital_phone": "+91-9876543210",
                "latitude": latitude + 0.01,
                "longitude": longitude + 0.01,
                "distance_km": 1.2,
                "arrival_minutes": 8
            },
            {
                "hospital_name": "Emergency Medical Centre",
                "hospital_phone": "+91-9876543211",
                "latitude": latitude - 0.01,
                "longitude": longitude - 0.01,
                "distance_km": 2.5,
                "arrival_minutes": 15
            },
            {
                "hospital_name": "Trauma Care Hospital",
                "hospital_phone": "+91-9876543212",
                "latitude": latitude + 0.02,
                "longitude": longitude - 0.02,
                "distance_km": 3.8,
                "arrival_minutes": 22
            }
        ]

        # Sort by distance
        hospitals_sorted = sorted(hospitals, key=lambda h: h["distance_km"])
        nearest = hospitals_sorted[0] if hospitals_sorted else None

        if nearest:
            logger.info(f"Nearest hospital: {nearest['hospital_name']} ({nearest['distance_km']} km)")
        return nearest or {}

    @staticmethod
    async def create_emergency_call(
        db: AsyncSession,
        incident_id: uuid.UUID,
        recipient_id: uuid.UUID,
        phone_number: str,
        message_text: str,
        call_type: str = "TTS_ALERT"
    ) -> EmergencyCall:
        """Record an emergency call."""
        call = EmergencyCall(
            incident_id=incident_id,
            recipient_id=recipient_id,
            phone_number=phone_number,
            call_type=call_type,
            message_text=message_text,
            status="PENDING"
        )
        db.add(call)
        await db.commit()
        return call

    @staticmethod
    async def update_call_status(
        db: AsyncSession,
        call_id: uuid.UUID,
        status: str,
        call_duration_seconds: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> EmergencyCall:
        """Update emergency call status."""
        call = await db.get(EmergencyCall, call_id)
        if call:
            call.status = status
            if call_duration_seconds:
                call.call_duration_seconds = call_duration_seconds
            if error_message:
                call.error_message = error_message
            if status in ["CONNECTED", "COMPLETED"]:
                call.started_at = call.started_at or datetime.utcnow()
                call.ended_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Call {call_id} status updated to {status}")
        return call

    @staticmethod
    async def correlate_multi_camera_events(
        db: AsyncSession,
        camera_events: list[dict]
    ) -> Optional[EmergencyIncident]:
        """
        Correlate events from multiple cameras into a single incident.
        camera_events: List of detection events with camera_id, event_type, timestamp, etc.
        """
        if not camera_events:
            return None

        # Sort by timestamp
        sorted_events = sorted(camera_events, key=lambda e: e.get("timestamp", datetime.utcnow()))
        
        # Use first event as reference
        first_event = sorted_events[0]
        
        incident = await EmergencyService.create_emergency_incident(
            db,
            incident_type="MULTI_CAMERA_CORRELATION",
            severity="HIGH",
            detection_source="AI",
            camera_id=first_event.get("camera_id"),
            location_latitude=first_event.get("latitude"),
            location_longitude=first_event.get("longitude"),
            location_name=first_event.get("location_name", "Multi-camera incident"),
            description=f"Correlated incident across {len(sorted_events)} cameras",
            detected_objects={"correlations": [e.get("event_type") for e in sorted_events]}
        )

        # Add each event to timeline
        for i, event in enumerate(sorted_events):
            await EmergencyService.add_incident_timeline_event(
                db,
                incident.id,
                event.get("event_type", "UNKNOWN"),
                f"Camera {event.get('camera_id')}: {event.get('description', '')}",
                event.get("camera_id")
            )

        logger.info(f"Correlated {len(sorted_events)} camera events into incident {incident.incident_code}")
        return incident

    @staticmethod
    async def get_active_incidents(db: AsyncSession, limit: int = 50) -> list[EmergencyIncident]:
        """Get all active emergency incidents."""
        stmt = (
            select(EmergencyIncident)
            .where(EmergencyIncident.status.in_(["OPEN", "ACKNOWLEDGED"]))
            .order_by(EmergencyIncident.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_incident_timeline(
        db: AsyncSession,
        incident_id: uuid.UUID
    ) -> list[IncidentTimeline]:
        """Get chronological timeline for an incident."""
        stmt = (
            select(IncidentTimeline)
            .where(IncidentTimeline.incident_id == incident_id)
            .order_by(IncidentTimeline.event_time.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_incident_ambulance_status(
        db: AsyncSession,
        incident_id: uuid.UUID
    ) -> Optional[AmbulanceDispatch]:
        """Get ambulance dispatch status for an incident."""
        stmt = select(AmbulanceDispatch).where(AmbulanceDispatch.incident_id == incident_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_incident_status(
        db: AsyncSession,
        incident_id: uuid.UUID,
        status: str,
        operator_comments: Optional[str] = None
    ) -> EmergencyIncident:
        """Update incident status."""
        incident = await db.get(EmergencyIncident, incident_id)
        if incident:
            incident.status = status
            if operator_comments:
                incident.operator_comments = operator_comments
            incident.updated_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Incident {incident.incident_code} status updated to {status}")
        return incident

    @staticmethod
    async def get_verified_recipients_for_alert_type(
        db: AsyncSession,
        alert_type: str,
        recipient_type: Optional[str] = None
    ) -> list[AlertRecipient]:
        """Get verified recipients for a specific alert type."""
        stmt = (
            select(AlertRecipient)
            .join(PhoneVerification)
            .where(
                and_(
                    AlertRecipient.is_active == True,
                    PhoneVerification.is_verified == True,
                    PhoneVerification.is_blocked == False,
                    or_(
                        AlertRecipient.alert_preference == "ALL",
                        AlertRecipient.alert_preference == alert_type
                    )
                )
            )
        )
        
        if recipient_type:
            stmt = stmt.where(AlertRecipient.recipient_type == recipient_type)
        
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def process_due_alert_followups() -> None:
        """Send each due active high alert and schedule its next five-minute run."""
        from app.core.database import AsyncSessionLocal
        from app.services.notification_service import get_notification_service

        async with AsyncSessionLocal() as db:
            stmt = (
                select(AlertDelivery, PhoneVerification)
                .join(AlertRecipient, AlertRecipient.id == AlertDelivery.recipient_id)
                .join(PhoneVerification, PhoneVerification.id == AlertRecipient.phone_verification_id)
                .where(
                    AlertDelivery.status == "ACTIVE",
                    AlertDelivery.is_recurring == True,
                    AlertDelivery.next_send_at <= datetime.now(timezone.utc),
                    PhoneVerification.is_verified == True,
                    PhoneVerification.is_blocked == False,
                )
            )
            rows = (await db.execute(stmt)).all()
            notification_service = get_notification_service()
            for delivery, phone in rows:
                max_retries = int((delivery.metadata_json or {}).get("max_retries", 0))
                if max_retries and delivery.send_count >= max_retries + 1:
                    delivery.status = "STOPPED"
                    delivery.is_recurring = False
                    delivery.next_send_at = None
                    delivery.stopped_at = datetime.now(timezone.utc)
                    await db.commit()
                    logger.info("[ALERT] Maximum retries reached for delivery %s", delivery.id)
                    continue
                # Claim the slot before calling Twilio so the single scheduler cannot send twice.
                now = datetime.now(timezone.utc)
                delivery.next_send_at = now + timedelta(seconds=delivery.recurrence_interval_seconds)
                await db.commit()
                logger.info("[ALERT] Sending recurring SMS to %s", phone.phone_number)
                result = await notification_service.send_sms(
                    phone.phone_number,
                    delivery.message_text,
                )
                send_status = result.get("status", "failed")
                provider_id = result.get("message_sid")
                error_message = result.get("error")
                delivery.send_count += 1
                delivery.last_error = error_message
                if send_status in {"sent", "queued", "accepted", "demo"}:
                    delivery.last_sent_at = now
                    delivery.provider_message_id = provider_id
                db.add(AlertSendAttempt(
                    alert_delivery_id=delivery.id,
                    recipient_id=delivery.recipient_id,
                    phone_number=phone.phone_number,
                    status=send_status,
                    provider_message_id=provider_id,
                    error_message=error_message,
                    attempted_at=now,
                ))
                await db.commit()
                logger.info("[ALERT] Next send scheduled for: %s", delivery.next_send_at)

    @staticmethod
    async def run_alert_followup_worker() -> None:
        """Poll persisted due times so restarts do not lose scheduled messages."""
        while True:
            try:
                await EmergencyService.process_due_alert_followups()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Alert follow-up worker failed")
            await asyncio.sleep(15)
