"""Unit tests for sampling planner."""

import pytest
from scene_signal.application.sampling import plan_sampling
from scene_signal.domain.policies import SamplingProfile
from scene_signal.domain.timeline import Interval, TimeUs


def test_plan_sampling_default_shot():
    profile = SamplingProfile("standard", target_frames_per_minute=36, min_frames_total=5, max_frames_total=32, max_frames_per_shot=8)
    duration_us = 5_000_000  # 5s
    plan = plan_sampling(duration_us, [], profile)
    assert plan.strategy_version == "1.0"
    assert len(plan.samples) >= profile.min_frames_total


def test_plan_sampling_multiple_shots():
    profile = SamplingProfile("quick", target_frames_per_minute=12, min_frames_total=3, max_frames_total=12, max_frames_per_shot=4)
    duration_us = 10_000_000  # 10s
    shots = [
        Interval(TimeUs(0), TimeUs(5_000_000)),
        Interval(TimeUs(5_000_000), TimeUs(10_000_000)),
    ]
    plan = plan_sampling(duration_us, shots, profile)
    assert len(plan.samples) >= 3
    # Check that samples fall within shots
    for sample in plan.samples:
        t = TimeUs(sample.planned_time_us)
        in_any = any(s.contains(t) or s.end.microseconds == t.microseconds for s in shots)
        assert in_any
