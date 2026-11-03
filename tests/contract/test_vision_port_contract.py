"""Contract tests for VisualAnalysisPort adapters."""

from pathlib import Path
import pytest
from scene_signal.adapters.fakes.fake_vision import FakeVisionAdapter
from scene_signal.ports.visual_analysis import VisionAnalysisRequest, VisionMode, ProviderTimeout


def test_fake_vision_contract():
    adapter = FakeVisionAdapter(mode=VisionMode.STILL_FRAMES)
    caps = adapter.capabilities()
    assert caps.provider == "fake"
    assert caps.analysis_mode == VisionMode.STILL_FRAMES

    req = VisionAnalysisRequest(
        job_id="job-1",
        shot_id="shot-001",
        shot_start_seconds=0.0,
        shot_end_seconds=5.0,
        frame_paths=[Path("frame-001.jpg")],
        frame_timestamps_seconds=[0.833333],
        requested_capabilities=["visual_observations", "camera_analysis"],
    )
    resp = adapter.analyze(req)
    assert len(resp.observations) > 0
    assert resp.shot_summary is not None


def test_fake_vision_error_injection():
    adapter = FakeVisionAdapter(fail_with=ProviderTimeout("Timeout"))
    with pytest.raises(ProviderTimeout):
        adapter.analyze(
            VisionAnalysisRequest(
                job_id="job-1",
                shot_id="shot-001",
                shot_start_seconds=0.0,
                shot_end_seconds=5.0,
                frame_paths=[],
                frame_timestamps_seconds=[],
                requested_capabilities=[],
            )
        )
