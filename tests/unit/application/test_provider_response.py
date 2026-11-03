"""Unit tests for capability negotiation and response validation."""

from pathlib import Path
import pytest
from scene_signal.application.provider_response import negotiate, validate_response
from scene_signal.ports.visual_analysis import (
    ProviderResponseInvalid,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisionCapabilities,
    VisionMode,
    RawObservation,
)


def test_negotiate():
    caps = VisionCapabilities(
        provider="fake",
        model="fake-1",
        adapter_version="1.0",
        analysis_mode=VisionMode.STILL_FRAMES,
        supported_capabilities=["visual_observations", "shot_detection"],
    )
    result = negotiate(["visual_observations", "temporal_events"], caps, "still_frames")
    reports = {r.capability: r for r in result.reports}
    assert reports["visual_observations"].status == "completed"
    assert reports["temporal_events"].status == "unsupported"
    assert reports["shot_detection"].status == "not_requested"


def test_validate_response_drops_empty_and_bad_category():
    req = VisionAnalysisRequest(
        job_id="job-1",
        shot_id="shot-001",
        shot_start_seconds=0.0,
        shot_end_seconds=5.0,
        frame_paths=[Path("frame-001.jpg")],
        frame_timestamps_seconds=[1.0],
        requested_capabilities=["visual_observations"],
    )
    resp = VisionAnalysisResponse(
        observations=[
            RawObservation(id="o1", category="object_presence", scope="frame", description="   "),  # empty description dropped
            RawObservation(id="o2", category="invalid_category", scope="frame", description="test"),  # bad category dropped with warning
            RawObservation(id="o3", category="object_presence", scope="frame", description="valid", confidence=1.5),  # confidence out of range dropped to null
        ]
    )
    caps = VisionCapabilities("fake", "fake", "1.0", VisionMode.STILL_FRAMES, [])
    validated = validate_response(req, resp, caps)
    assert len(validated.observations) == 1
    assert validated.observations[0].confidence is None
    assert "PROVIDER_ITEM_DROPPED" in validated.warnings


def test_validate_response_bad_frame_ref():
    req = VisionAnalysisRequest(
        job_id="job-1",
        shot_id="shot-001",
        shot_start_seconds=0.0,
        shot_end_seconds=5.0,
        frame_paths=[Path("frame-001.jpg")],
        frame_timestamps_seconds=[1.0],
        requested_capabilities=["visual_observations"],
    )
    resp = VisionAnalysisResponse(
        observations=[
            RawObservation(id="o1", category="object_presence", scope="frame", description="desc", evidence_frame_refs=["frame-999"])
        ]
    )
    caps = VisionCapabilities("fake", "fake", "1.0", VisionMode.STILL_FRAMES, [])
    with pytest.raises(ProviderResponseInvalid):
        validate_response(req, resp, caps)
