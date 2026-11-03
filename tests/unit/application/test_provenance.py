"""Unit tests for provenance builder and redaction guard."""

import pytest
from scene_signal.application.provenance import build_provenance


def test_build_provenance_success():
    prov = build_provenance(
        job_id="job-1",
        asset_id="asset-1",
        asset_fingerprint="sha256:" + "0" * 64,
        contract_version="1.0",
        schema_version="1.0",
        extraction_profile="standard",
        request_hash="sha256:" + "1" * 64,
        sampling_strategy_version="1.0",
        sampling_parameters={},
        media_probe={"name": "ffprobe", "version": "6.0"},
        frame_extractor={"name": "ffmpeg", "version": "6.0"},
        shot_detector={"name": "ffmpeg_scene", "version": "1.0"},
        vision={"provider": "fake", "model": "fake-1"},
        started_at="2026-10-12T00:00:00Z",
        completed_at="2026-10-12T00:00:01Z",
        stage_attempts={"inspection": 1},
        warning_count=0,
    )
    assert prov.job_id == "job-1"


def test_build_provenance_redaction_guard():
    with pytest.raises(ValueError):
        build_provenance(
            job_id="job-1",
            asset_id="asset-1",
            asset_fingerprint="sha256:" + "0" * 64,
            contract_version="1.0",
            schema_version="1.0",
            extraction_profile="standard",
            request_hash="sha256:" + "1" * 64,
            sampling_strategy_version="1.0",
            sampling_parameters={"api_key": "sk-secret-123"},
            media_probe={"name": "ffprobe", "version": "6.0"},
            frame_extractor={"name": "ffmpeg", "version": "6.0"},
            shot_detector={"name": "ffmpeg_scene", "version": "1.0"},
            vision=None,
            started_at="2026-10-12T00:00:00Z",
            completed_at="2026-10-12T00:00:01Z",
            stage_attempts={},
            warning_count=0,
        )
