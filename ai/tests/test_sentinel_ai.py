import pytest
import numpy as np
import torch
import os

from ai.sentinel_ai.config.settings import ai_settings
from ai.sentinel_ai.events.schema import SentinelAIEvent, EventType
from ai.sentinel_ai.scheduler.resource_manager import resource_manager, ModelResourceManager
from ai.sentinel_ai.detectors.person_detector import PersonDetector
from ai.sentinel_ai.detectors.vehicle_detector import VehicleDetector
from ai.sentinel_ai.tracking.tracker import MultiObjectTracker
from ai.sentinel_ai.anpr.normalizer import ANPRNormalizer
from ai.sentinel_ai.anpr.detector import ANPRDetector
from ai.sentinel_ai.face.face_engine import FaceEngine
from ai.sentinel_ai.weapon.weapon_detector import WeaponDetector
from ai.sentinel_ai.activity.har_engine import HAREngine
from ai.sentinel_ai.validation.fire_smoke_validator import FireSmokeValidator
from ai.sentinel_ai.validation.temporal_validator import TemporalValidator
from ai.sentinel_ai.adapters.sentinel_adapter import sentinel_ai_adapter


def create_dummy_frame(width=640, height=480):
    return np.zeros((height, width, 3), dtype=np.uint8)


def test_gpu_and_environment():
    """Verify GPU detection and PyTorch availability"""
    cuda_avail = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_avail else 0
    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU Fallback"
    print(f"CUDA Available: {cuda_avail}, Devices: {device_count}, Name: {device_name}")
    assert isinstance(cuda_avail, bool)


def test_model_resource_manager():
    """Verify loading, unloading, and status reporting of resource_manager"""
    mgr = ModelResourceManager(max_concurrent_models=2)
    device = mgr.get_device()
    assert device.type in ("cuda", "cpu")

    dummy_model = {"model": "test"}
    mgr.register_model("test_model", dummy_model, version="1.0.0")
    status = mgr.get_system_status()
    assert "test_model" in status["loaded_models"]

    unloaded = mgr.unload_model("test_model")
    assert unloaded is True
    assert "test_model" not in mgr.loaded_models


def test_person_detector_labeling():
    """Verify PersonDetector returns 'Person detected' (not criminal)"""
    detector = PersonDetector()
    frame = create_dummy_frame()
    events = detector.detect(frame, camera_id="cam_01")
    assert isinstance(events, list)
    for evt in events:
        assert evt.event_type == EventType.PERSON_DETECTED
        assert evt.class_name == "Person detected"


def test_vehicle_detector():
    """Verify VehicleDetector produces VEHICLE_DETECTED events"""
    detector = VehicleDetector()
    frame = create_dummy_frame()
    events = detector.detect(frame, camera_id="cam_01")
    assert isinstance(events, list)
    for evt in events:
        assert evt.event_type == EventType.VEHICLE_DETECTED


def test_multiobject_tracker():
    """Verify MultiObjectTracker updates track IDs within camera session"""
    tracker = MultiObjectTracker(camera_id="cam_01", iou_threshold=0.3)
    bboxes = [[10.0, 10.0, 50.0, 50.0], [100.0, 100.0, 200.0, 200.0]]
    track_map1 = tracker.update(bboxes)
    assert len(track_map1) == 2

    # Frame 2 with slightly shifted box
    shifted_bboxes = [[12.0, 12.0, 52.0, 52.0], [102.0, 102.0, 202.0, 202.0]]
    track_map2 = tracker.update(shifted_bboxes)
    assert track_map2[0] == track_map1[0]
    assert track_map2[1] == track_map1[1]


def test_anpr_normalizer():
    """Verify ANPRNormalizer strips noise and EU country band without inventing digits"""
    raw_ocr = "  RO-B123ABC  "
    normalized = ANPRNormalizer.normalize_plate(raw_ocr)
    assert normalized == "B123ABC"

    assert ANPRNormalizer.is_valid_plate("GJ01AB1234") is True
    assert ANPRNormalizer.is_valid_plate("12") is False


def test_face_engine_review_requirement():
    """Verify FaceEngine enforces human review requirement on FACE_MATCH"""
    engine = FaceEngine()
    frame = create_dummy_frame()
    events = engine.process_frame(frame, camera_id="cam_01")
    assert isinstance(events, list)
    for evt in events:
        if evt.event_type == EventType.FACE_MATCH:
            assert evt.requires_human_review is True


def test_weapon_detector_temporal_validation():
    """Verify WeaponDetector temporal state transition"""
    detector = WeaponDetector(min_consecutive_frames=3)
    frame = create_dummy_frame()

    # Stub candidate detection
    detector.weapon_system = type("StubSystem", (), {
        "process_frame": lambda self, f: [{"class": "handgun", "confidence": 0.85, "bbox": [10, 10, 50, 50]}]
    })()

    # Frame 1 -> POSSIBLE_WEAPON
    evts1 = detector.process_frame(frame, camera_id="cam_01")
    assert len(evts1) == 1
    assert evts1[0].status == "POSSIBLE_WEAPON"

    # Frame 2 -> POSSIBLE_WEAPON
    detector.process_frame(frame, camera_id="cam_01")

    # Frame 3 -> CONFIRMED
    evts3 = detector.process_frame(frame, camera_id="cam_01")
    assert len(evts3) == 1
    assert evts3[0].status == "CONFIRMED"
    assert evts3[0].requires_human_review is True


def test_fire_smoke_validator():
    """Verify FireSmokeValidator HSV and size filtering"""
    validator = FireSmokeValidator()
    frame = create_dummy_frame()

    # Black frame will fail warm color HSV check for fire
    assert validator.verify_hsv_color(frame[0:50, 0:50], "fire") is False


def test_har_engine():
    """Verify HAREngine processing"""
    engine = HAREngine()
    frame = create_dummy_frame()
    events = engine.process_frame_or_clip(frame, camera_id="cam_01")
    assert isinstance(events, list)


def test_temporal_validator():
    """Verify TemporalValidator cooldown duplicate suppression"""
    validator = TemporalValidator(cooldown_seconds=3.0)
    event1 = SentinelAIEvent(
        event_type=EventType.PERSON_DETECTED,
        camera_id="cam_01",
        class_name="Person detected",
        confidence=0.9,
        model_name="yolo",
    )
    event2 = SentinelAIEvent(
        event_type=EventType.PERSON_DETECTED,
        camera_id="cam_01",
        class_name="Person detected",
        confidence=0.9,
        model_name="yolo",
    )

    filtered1 = validator.filter_events([event1])
    assert len(filtered1) == 1

    # Immediate second call is suppressed by cooldown
    filtered2 = validator.filter_events([event2])
    assert len(filtered2) == 0


def test_sentinel_ai_adapter_e2e():
    """Verify SentinelAIAdapter end-to-end frame processing"""
    frame = create_dummy_frame()
    events = sentinel_ai_adapter.process_frame(frame, camera_id="cam_test_e2e")
    assert isinstance(events, list)
