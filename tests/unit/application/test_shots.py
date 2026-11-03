"""Unit tests for shot builder."""

import pytest
from scene_signal.application.shots import build_shots
from scene_signal.domain.policies import ShotPolicy
from scene_signal.ports.shot_detection import BoundaryCandidate, ShotDetectionResult


def test_build_shots_not_requested():
    shots, warnings = build_shots(None, 5_000_000, ShotPolicy(), requested=False)
    assert len(shots) == 1
    assert shots[0].analysis_status == "not_requested"
    assert shots[0].start_us == 0
    assert shots[0].end_us == 5_000_000


def test_build_shots_degraded():
    shots, warnings = build_shots(None, 5_000_000, ShotPolicy(), requested=True)
    assert len(shots) == 1
    assert shots[0].analysis_status == "analyzed"
    assert "SHOT_DETECTION_DEGRADED" in warnings


def test_build_shots_with_boundaries():
    det = ShotDetectionResult(
        boundaries=[BoundaryCandidate(time_us=2_500_000, kind="hard_cut")]
    )
    shots, warnings = build_shots(det, 5_000_000, ShotPolicy(), requested=True)
    assert len(shots) == 2
    assert shots[0].start_us == 0
    assert shots[0].end_us == 2_500_000
    assert shots[1].start_us == 2_500_000
    assert shots[1].end_us == 5_000_000
    assert "GRADUAL_TRANSITIONS_NOT_DETECTED" in warnings
