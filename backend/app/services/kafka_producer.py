"""
Kafka Event Producer — publishes structured events to Sentinel Kafka topics.

Topics:
  sentinel.camera.status
  sentinel.detection.person
  sentinel.detection.vehicle
  sentinel.anpr.observation
  sentinel.watchlist.match
  sentinel.alerts
  sentinel.system.events

Gracefully degrades if Kafka is unavailable (logs warning, never crashes).
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

logger = logging.getLogger("sentinel.kafka")

# Sentinel Kafka topics
TOPIC_CAMERA_STATUS = "sentinel.camera.status"
TOPIC_DETECTION_PERSON = "sentinel.detection.person"
TOPIC_DETECTION_VEHICLE = "sentinel.detection.vehicle"
TOPIC_ANPR_OBSERVATION = "sentinel.anpr.observation"
TOPIC_FACE_EVENTS = "sentinel.face.events"
TOPIC_WEAPON_EVENTS = "sentinel.weapon.events"
TOPIC_FIRE_EVENTS = "sentinel.fire.events"
TOPIC_SMOKE_EVENTS = "sentinel.smoke.events"
TOPIC_ACTIVITY_EVENTS = "sentinel.activity.events"
TOPIC_WATCHLIST_MATCH = "sentinel.watchlist.match"
TOPIC_ALERTS = "sentinel.alerts"
TOPIC_SYSTEM_EVENTS = "sentinel.system.events"

SCHEMA_VERSION = "1.0.0"


_producer = None
_kafka_available = None


def _build_event(event_type: str, camera_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    """Builds a structured Kafka event envelope. Never includes credentials."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "camera_id": camera_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "payload": payload,
    }


async def _get_producer():
    """Lazy-initializes the Kafka producer. Returns None if unavailable."""
    global _producer, _kafka_available

    if _kafka_available is False:
        return None

    if _producer is not None:
        return _producer

    try:
        from aiokafka import AIOKafkaProducer
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await _producer.start()
        _kafka_available = True
        logger.info("Kafka producer connected to %s", settings.kafka_bootstrap_servers)
        return _producer
    except ImportError:
        logger.info("aiokafka not installed; Kafka events will be logged only")
        _kafka_available = False
        return None
    except Exception as exc:
        logger.warning("Kafka connection failed (%s); events will be logged only", exc)
        _kafka_available = False
        return None


async def publish_event(topic: str, event_type: str, camera_id: str | None = None, payload: dict[str, Any] | None = None) -> None:
    """
    Publish a structured event to a Kafka topic.
    Falls back to logging if Kafka is unavailable.
    """
    event = _build_event(event_type, camera_id, payload or {})

    producer = await _get_producer()
    if producer is not None:
        try:
            await producer.send_and_wait(topic, event)
            return
        except Exception as exc:
            logger.warning("Failed to publish to Kafka topic %s: %s", topic, exc)

    # Fallback: log the event
    logger.info("Event [%s] %s: camera=%s", topic, event_type, camera_id)


# ---- Convenience publishers ----

async def publish_camera_status(camera_id: str, status: str, **extra: Any) -> None:
    await publish_event(TOPIC_CAMERA_STATUS, "CAMERA_STATUS_CHANGE", camera_id, {"status": status, **extra})


async def publish_person_detection(camera_id: str, track_id: str, confidence: float, bbox: dict, **extra: Any) -> None:
    await publish_event(TOPIC_DETECTION_PERSON, "PERSON_DETECTED", camera_id, {
        "track_id": track_id, "confidence": confidence, "bbox": bbox, **extra,
    })


async def publish_vehicle_detection(camera_id: str, track_id: str, vehicle_class: str, confidence: float, bbox: dict, **extra: Any) -> None:
    await publish_event(TOPIC_DETECTION_VEHICLE, "VEHICLE_DETECTED", camera_id, {
        "track_id": track_id, "vehicle_class": vehicle_class, "confidence": confidence, "bbox": bbox, **extra,
    })


async def publish_anpr_observation(camera_id: str, plate_text: str, normalized_plate: str, confidence: float, **extra: Any) -> None:
    await publish_event(TOPIC_ANPR_OBSERVATION, "ANPR_PLATE_DETECTED", camera_id, {
        "plate_text": plate_text, "normalized_plate": normalized_plate, "confidence": confidence, **extra,
    })


async def publish_face_event(camera_id: str, event_type: str, confidence: float, requires_human_review: bool = False, **extra: Any) -> None:
    await publish_event(TOPIC_FACE_EVENTS, event_type, camera_id, {
        "confidence": confidence, "requires_human_review": requires_human_review, **extra,
    })


async def publish_weapon_event(camera_id: str, event_type: str, confidence: float, **extra: Any) -> None:
    await publish_event(TOPIC_WEAPON_EVENTS, event_type, camera_id, {
        "confidence": confidence, "requires_human_review": True, **extra,
    })


async def publish_fire_event(camera_id: str, event_type: str, confidence: float, **extra: Any) -> None:
    await publish_event(TOPIC_FIRE_EVENTS, event_type, camera_id, {
        "confidence": confidence, "requires_human_review": True, **extra,
    })


async def publish_smoke_event(camera_id: str, event_type: str, confidence: float, **extra: Any) -> None:
    await publish_event(TOPIC_SMOKE_EVENTS, event_type, camera_id, {
        "confidence": confidence, "requires_human_review": True, **extra,
    })


async def publish_activity_event(camera_id: str, activity_type: str, confidence: float, **extra: Any) -> None:
    await publish_event(TOPIC_ACTIVITY_EVENTS, "HUMAN_ACTIVITY_DETECTED", camera_id, {
        "activity_type": activity_type, "confidence": confidence, **extra,
    })


async def publish_watchlist_match(camera_id: str, plate: str, watchlist_id: str, priority: str, **extra: Any) -> None:
    await publish_event(TOPIC_WATCHLIST_MATCH, "WATCHLIST_MATCH", camera_id, {
        "plate": plate, "watchlist_id": watchlist_id, "priority": priority,
        "message": "Watchlist match — human verification required.", **extra,
    })



async def publish_alert(alert_type: str, camera_id: str | None, severity: str, alert_id: str, **extra: Any) -> None:
    await publish_event(TOPIC_ALERTS, alert_type, camera_id, {
        "alert_id": alert_id, "severity": severity, **extra,
    })


async def publish_system_event(event_type: str, **extra: Any) -> None:
    await publish_event(TOPIC_SYSTEM_EVENTS, event_type, None, extra)


async def close_producer() -> None:
    """Shut down the Kafka producer cleanly."""
    global _producer, _kafka_available
    if _producer is not None:
        try:
            await _producer.stop()
        except Exception:
            pass
        _producer = None
    _kafka_available = None
