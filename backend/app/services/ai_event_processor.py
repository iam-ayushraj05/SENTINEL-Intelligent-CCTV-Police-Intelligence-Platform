import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.models.detection import Detection, DetectionEvent
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.audit import AuditLog
from app.models.camera import Camera

from app.services.correlation_engine import evaluate_detection_event
from app.services.kafka_producer import (
    publish_event,
    publish_person_detection,
    publish_vehicle_detection,
    publish_anpr_observation,
    publish_face_event,
    publish_weapon_event,
    publish_fire_event,
    publish_smoke_event,
    publish_activity_event,
    publish_watchlist_match,
    TOPIC_DETECTION_PERSON,
    TOPIC_DETECTION_VEHICLE,
    TOPIC_ANPR_OBSERVATION,
    TOPIC_FACE_EVENTS,
    TOPIC_WEAPON_EVENTS,
    TOPIC_FIRE_EVENTS,
    TOPIC_SMOKE_EVENTS,
    TOPIC_ACTIVITY_EVENTS,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("sentinel.ai_event_processor")


async def process_sentinel_ai_event(
    db: AsyncSession,
    event_dict: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Processes a standardized Sentinel AI event:
    1. Resolves target camera
    2. Persists event to PostgreSQL database
    3. Evaluates event with Alert Engine (deduplication & severity mapping)
    4. Publishes to corresponding Kafka topic
    5. Broadcasts event over WebSocket (/ws/events)
    6. Creates AuditLog entry
    """
    event_type = event_dict.get("event_type", "UNKNOWN")
    camera_id_str = event_dict.get("camera_id")
    track_id = event_dict.get("track_id")
    confidence = float(event_dict.get("confidence", 0.80))
    bbox = event_dict.get("bounding_box") or {}
    class_name = event_dict.get("class_name", "")
    metadata = event_dict.get("metadata", {})

    # 1. Resolve camera UUID
    camera_uuid = None
    if camera_id_str:
        try:
            camera_uuid = uuid.UUID(camera_id_str)
        except ValueError:
            # Look up camera by camera_code
            if hasattr(db, "execute") and type(db).__name__ != "DummySession":
                try:
                    stmt = select(Camera.id).where(Camera.camera_code.ilike(camera_id_str))
                    res = await db.execute(stmt)
                    cam_id = res.scalars().first()
                    if cam_id:
                        camera_uuid = cam_id
                except Exception:
                    pass

    if not camera_uuid:
        # Fallback dummy UUID for unmapped camera
        camera_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    # 2. Database Persistence
    subject_ref = None

    if event_type == "PERSON_DETECTED":
        detection = Detection(
            id=uuid.uuid4(),
            camera_id=camera_uuid,
            object_type="person",
            confidence=confidence,
            bbox=bbox if isinstance(bbox, dict) else {"coordinates": bbox},
            track_id=track_id,
            metadata_json=metadata,
            timestamp=datetime.now(timezone.utc),
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            db.add(detection)
            await db.commit()

        await publish_person_detection(str(camera_uuid), track_id or "", confidence, bbox)

    elif event_type == "VEHICLE_DETECTED":
        detection = Detection(
            id=uuid.uuid4(),
            camera_id=camera_uuid,
            object_type=class_name.lower() or "vehicle",
            confidence=confidence,
            bbox=bbox if isinstance(bbox, dict) else {"coordinates": bbox},
            track_id=track_id,
            metadata_json=metadata,
            timestamp=datetime.now(timezone.utc),
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            db.add(detection)
            await db.commit()

        await publish_vehicle_detection(str(camera_uuid), track_id or "", class_name, confidence, bbox)

    elif event_type == "ANPR_DETECTED":
        norm_plate = metadata.get("normalized_plate") or class_name
        raw_ocr = metadata.get("raw_ocr") or norm_plate
        subject_ref = norm_plate

        sighting = VehicleSighting(
            id=uuid.uuid4(),
            camera_id=camera_uuid,
            plate_text=raw_ocr,
            normalized_plate=norm_plate,
            confidence=confidence,
            metadata_json={"track_id": track_id, **metadata},
            timestamp=datetime.now(timezone.utc),
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            db.add(sighting)
            await db.commit()

        await publish_anpr_observation(str(camera_uuid), raw_ocr, norm_plate, confidence)

    elif event_type in ("FACE_DETECTED", "FACE_MATCH"):
        matched_name = metadata.get("matched_name")
        if matched_name:
            subject_ref = matched_name

        await publish_face_event(
            str(camera_uuid),
            event_type,
            confidence,
            requires_human_review=(event_type == "FACE_MATCH"),
            metadata=metadata,
        )

    elif event_type == "WEAPON_DETECTED":
        await publish_weapon_event(str(camera_uuid), event_type, confidence, metadata=metadata)

    elif event_type == "FIRE_DETECTED":
        await publish_fire_event(str(camera_uuid), event_type, confidence, metadata=metadata)

    elif event_type == "SMOKE_DETECTED":
        await publish_smoke_event(str(camera_uuid), event_type, confidence, metadata=metadata)

    elif event_type == "HUMAN_ACTIVITY_DETECTED":
        activity_label = metadata.get("activity") or class_name
        await publish_activity_event(str(camera_uuid), activity_label, confidence, metadata=metadata)

    # 3. Evaluate Alert Engine & Deduplication
    alert = await evaluate_detection_event(
        db=db,
        camera_id=camera_uuid,
        event_type=event_type,
        subject_reference=subject_ref,
        confidence=confidence,
        metadata_json=event_dict,
    )

    # 4. WebSocket Event Broadcast
    ws_event_payload = {
        "event_id": event_dict.get("event_id", str(uuid.uuid4())),
        "event_type": event_type,
        "camera_id": str(camera_uuid),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": confidence,
        "class_name": class_name,
        "track_id": track_id,
        "bounding_box": bbox,
        "requires_human_review": event_dict.get("requires_human_review", False),
    }
    await ws_manager.broadcast_event(ws_event_payload)

    # 5. Audit Log (Never logs passwords or credentials)
    if hasattr(db, "add") and type(db).__name__ != "DummySession":
        try:
            audit = AuditLog(
                id=uuid.uuid4(),
                username="sentinel_ai_engine",
                action=f"AI_EVENT_{event_type}",
                resource=f"Camera:{camera_uuid}",
                details=f"Class: {class_name}, Conf: {confidence:.2f}",
                result="SUCCESS",
                timestamp=datetime.now(timezone.utc),
            )
            db.add(audit)
            await db.commit()
        except Exception as e:
            logger.debug("AuditLog record note: %s", e)

    return ws_event_payload
