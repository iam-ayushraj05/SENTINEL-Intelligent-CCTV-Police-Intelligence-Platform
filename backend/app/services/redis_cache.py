"""
Redis Cache Service — transient state for camera heartbeats, stream state, and metrics.

NOT a permanent evidence store. All data here is ephemeral.
Gracefully degrades if Redis is unavailable.
"""

import json
import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger("sentinel.redis_cache")

_redis = None
_redis_available = None

# Key prefixes
PREFIX_HEARTBEAT = "sentinel:camera:heartbeat:"
PREFIX_STREAM_STATE = "sentinel:camera:state:"
PREFIX_AI_WORKERS = "sentinel:ai:workers"
PREFIX_RECENT_DETECTIONS = "sentinel:camera:detections:"
PREFIX_ALERT_STATE = "sentinel:alert:temp:"

# TTLs in seconds
TTL_HEARTBEAT = 120
TTL_STREAM_STATE = 300
TTL_DETECTION_COUNT = 60


async def _get_redis():
    """Lazy-initialize Redis connection. Returns None if unavailable."""
    global _redis, _redis_available

    if _redis_available is False:
        return None

    if _redis is not None:
        return _redis

    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await _redis.ping()
        _redis_available = True
        logger.info("Redis connected at %s", settings.redis_url)
        return _redis
    except ImportError:
        logger.info("redis[asyncio] not installed; cache operations will be skipped")
        _redis_available = False
        return None
    except Exception as exc:
        logger.warning("Redis connection failed (%s); cache operations will be skipped", exc)
        _redis_available = False
        return None


# ---- Camera Heartbeat ----

async def set_camera_heartbeat(camera_id: str) -> None:
    """Record camera heartbeat timestamp."""
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.set(f"{PREFIX_HEARTBEAT}{camera_id}", str(time.time()), ex=TTL_HEARTBEAT)
    except Exception as exc:
        logger.debug("Redis heartbeat set failed: %s", exc)


async def get_camera_heartbeat(camera_id: str) -> float | None:
    """Get last heartbeat timestamp for camera."""
    r = await _get_redis()
    if r is None:
        return None
    try:
        val = await r.get(f"{PREFIX_HEARTBEAT}{camera_id}")
        return float(val) if val else None
    except Exception:
        return None


# ---- Camera Stream State ----

async def set_camera_state(camera_id: str, state: dict[str, Any]) -> None:
    """Store current stream state (LIVE, OFFLINE, CONNECTING, etc.)."""
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.set(f"{PREFIX_STREAM_STATE}{camera_id}", json.dumps(state, default=str), ex=TTL_STREAM_STATE)
    except Exception as exc:
        logger.debug("Redis state set failed: %s", exc)


async def get_camera_state(camera_id: str) -> dict[str, Any] | None:
    """Get current stream state for camera."""
    r = await _get_redis()
    if r is None:
        return None
    try:
        val = await r.get(f"{PREFIX_STREAM_STATE}{camera_id}")
        return json.loads(val) if val else None
    except Exception:
        return None


async def get_all_camera_states() -> dict[str, dict[str, Any]]:
    """Get all camera states. Returns empty dict if Redis unavailable."""
    r = await _get_redis()
    if r is None:
        return {}
    try:
        keys = []
        async for key in r.scan_iter(f"{PREFIX_STREAM_STATE}*"):
            keys.append(key)
        if not keys:
            return {}
        values = await r.mget(keys)
        result = {}
        for key, val in zip(keys, values):
            camera_id = key.replace(PREFIX_STREAM_STATE, "")
            if val:
                result[camera_id] = json.loads(val)
        return result
    except Exception:
        return {}


# ---- AI Workers ----

async def set_active_ai_workers(count: int) -> None:
    """Track active AI worker count."""
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.set(PREFIX_AI_WORKERS, str(count), ex=TTL_STREAM_STATE)
    except Exception:
        pass


async def get_active_ai_workers() -> int:
    r = await _get_redis()
    if r is None:
        return 0
    try:
        val = await r.get(PREFIX_AI_WORKERS)
        return int(val) if val else 0
    except Exception:
        return 0


# ---- Detection Counts ----

async def increment_detection_count(camera_id: str, object_type: str) -> None:
    """Increment recent detection counter for a camera."""
    r = await _get_redis()
    if r is None:
        return
    try:
        key = f"{PREFIX_RECENT_DETECTIONS}{camera_id}"
        await r.hincrby(key, object_type, 1)
        await r.expire(key, TTL_DETECTION_COUNT)
    except Exception:
        pass


async def get_detection_counts(camera_id: str) -> dict[str, int]:
    """Get recent detection counts by type for a camera."""
    r = await _get_redis()
    if r is None:
        return {}
    try:
        key = f"{PREFIX_RECENT_DETECTIONS}{camera_id}"
        counts = await r.hgetall(key)
        return {k: int(v) for k, v in counts.items()}
    except Exception:
        return {}


# ---- Cleanup ----

async def close_redis() -> None:
    """Close Redis connection."""
    global _redis, _redis_available
    if _redis is not None:
        try:
            await _redis.close()
        except Exception:
            pass
        _redis = None
    _redis_available = None
