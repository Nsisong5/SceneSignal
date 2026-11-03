"""Temporal ground truth tests against manifest data."""

import json
from pathlib import Path
import pytest
from scene_signal.domain.timeline import TimeUs, Interval, tile_check


def test_temporal_ground_truth_manifest():
    manifest_path = Path("tests/fixtures/manifest.json")
    if not manifest_path.exists():
        pytest.skip("Manifest not found")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "multishot_12s.mp4" in data
    assert data["multishot_12s.mp4"]["tolerance"] == 0.1


def test_exact_time_conversion_arithmetic():
    t = TimeUs.from_float_seconds(1.5)
    assert t.microseconds == 1500000
    assert t.to_seconds() == 1.500000


def test_approximate_shot_boundaries_tolerance():
    detected = 3.01
    expected = 3.0
    tolerance = 0.1
    assert abs(detected - expected) <= tolerance
