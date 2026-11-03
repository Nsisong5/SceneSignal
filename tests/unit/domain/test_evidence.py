"""Unit tests for evidence rules."""

from scene_signal.domain.evidence import (
    allowed_event_precision,
    camera_movement_allowed,
    observation_scope_allowed,
)


def test_camera_movement_allowed():
    assert camera_movement_allowed("pan_left", "still_frames", 1, True) is False
    assert camera_movement_allowed("pan_left", "still_frames", 2, True) is True
    assert camera_movement_allowed("unknown", "still_frames", 1, True) is True
    assert camera_movement_allowed("pan_left", "frame_sequence", 2, False) is False
    assert camera_movement_allowed("pan_left", "frame_sequence", 2, True) is True


def test_allowed_event_precision():
    assert allowed_event_precision("adapter_reported_interval", False) is False
    assert allowed_event_precision("adapter_reported_interval", True) is True
    assert allowed_event_precision("single_sample_only", False) is True


def test_observation_scope_allowed():
    assert observation_scope_allowed("frame", True, False) is True
    assert observation_scope_allowed("frame", True, True) is False
    assert observation_scope_allowed("shot", False, True) is True
    assert observation_scope_allowed("shot", True, True) is False
