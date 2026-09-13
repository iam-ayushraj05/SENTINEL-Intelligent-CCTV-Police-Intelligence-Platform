"""
Tests for CameraStreamManager reconnect logic and resource management.
"""
import os
import sys
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestReconnectPolicy:
    """Test exponential backoff behavior."""

    def test_initial_delay(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=2.0, maximum=30.0, jitter_factor=0.0)
        delay = policy.next_delay()
        assert delay == pytest.approx(2.0, abs=0.1)

    def test_exponential_growth(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=2.0, maximum=30.0, jitter_factor=0.0)
        delays = [policy.next_delay() for _ in range(5)]
        # Without jitter: 2, 4, 8, 16, 30 (capped)
        assert delays[0] == pytest.approx(2.0, abs=0.1)
        assert delays[1] == pytest.approx(4.0, abs=0.1)
        assert delays[2] == pytest.approx(8.0, abs=0.1)
        assert delays[3] == pytest.approx(16.0, abs=0.1)
        assert delays[4] == pytest.approx(30.0, abs=0.1)  # Capped at 30

    def test_cap_at_maximum(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=2.0, maximum=30.0, jitter_factor=0.0)
        for _ in range(20):
            delay = policy.next_delay()
        assert delay <= 30.0

    def test_reset(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=2.0, maximum=30.0, jitter_factor=0.0)
        policy.next_delay()
        policy.next_delay()
        policy.reset()
        delay = policy.next_delay()
        assert delay == pytest.approx(2.0, abs=0.1)

    def test_max_retries_exceeded(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=1.0, maximum=30.0, jitter_factor=0.0, max_retries=3)
        assert policy.next_delay() is not None
        assert policy.next_delay() is not None
        assert policy.next_delay() is not None
        assert policy.next_delay() is None  # Exceeded

    def test_jitter_within_bounds(self):
        from app.services.camera_stream_manager import ReconnectPolicy
        policy = ReconnectPolicy(initial=10.0, maximum=100.0, jitter_factor=0.25)
        delays = [policy.next_delay() for _ in range(1)]
        # With 25% jitter, first delay should be between 7.5 and 12.5
        assert 7.5 <= delays[0] <= 12.5


class TestStreamMetrics:
    """Test stream metrics tracking."""

    def test_initial_state(self):
        from app.services.camera_stream_manager import StreamMetrics
        metrics = StreamMetrics(camera_id="cam11")
        assert metrics.state == "IDLE"
        assert metrics.reconnect_count == 0
        assert metrics.total_frames == 0

    def test_uptime_when_not_connected(self):
        from app.services.camera_stream_manager import StreamMetrics
        metrics = StreamMetrics(camera_id="cam11")
        assert metrics.uptime_seconds is None

    def test_to_dict_no_secrets(self):
        from app.services.camera_stream_manager import StreamMetrics
        metrics = StreamMetrics(camera_id="cam11")
        d = metrics.to_dict()
        assert "camera_id" in d
        assert "state" in d
        # Must never contain credentials
        assert "password" not in str(d).lower()
        assert "rtsp://" not in str(d)


class TestCameraStreamManager:
    """Test CameraStreamManager lifecycle."""

    def test_creation(self):
        from app.services.camera_stream_manager import CameraStreamManager
        mgr = CameraStreamManager("cam11")
        assert mgr.camera_id == "cam11"
        assert mgr.is_live is False
        assert mgr.is_stopped is False

    @pytest.mark.asyncio
    async def test_stop(self):
        from app.services.camera_stream_manager import CameraStreamManager
        mgr = CameraStreamManager("cam11")
        await mgr.stop()
        assert mgr.is_stopped is True
        assert mgr.metrics.state == "STOPPED"

    @pytest.mark.asyncio
    async def test_connect_without_credentials(self):
        from app.services.camera_stream_manager import CameraStreamManager
        from app.core.config import settings
        original = settings.sentinel_cctv_email
        try:
            settings.sentinel_cctv_email = ""
            mgr = CameraStreamManager("cam11")
            result = await mgr.connect()
            assert result is False
            assert mgr.metrics.state == "ERROR"
            assert "credentials" in mgr.metrics.last_error.lower()
        finally:
            settings.sentinel_cctv_email = original
