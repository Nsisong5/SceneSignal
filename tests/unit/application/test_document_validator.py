"""Unit tests for document cross-reference and consistency validator."""

from pathlib import Path
import pytest
from scene_signal.application.document_validator import validate_document
from scene_signal.schemas.result import (
    SceneIntelligenceDocument,
    MediaMetadata,
    TimelineMetadata,
    Shot,
    FrameRecord,
    Provenance,
)


def test_validate_document_valid():
    media = MediaMetadata(
        duration_seconds=5.0,
        width=1280,
        height=720,
        display_width=1280,
        display_height=720,
        rotation_degrees=0,
        has_video=True,
        has_audio=False,
        frame_rate_mode="constant",
        video_codec="h264",
        container_format="mp4",
        file_size_bytes=1000,
    )
    timeline = TimelineMetadata()
    shots = [
        Shot(
            id="shot-001",
            start_seconds=0.0,
            end_seconds=5.0,
            segment_kind="content",
            boundary_method="initial_segment",
            boundary_kind="asset_start",
            analysis_status="analyzed",
        )
    ]
    frames = [
        FrameRecord(
            id="frame-001",
            timestamp_seconds=1.0,
            requested_timestamp_seconds=1.0,
            timestamp_source="decoded_pts",
            shot_id="shot-001",
            sampling_reason="shot_bin",
            width=1280,
            height=720,
        )
    ]
    prov = Provenance(
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
        started_at="2026-10-12T00:00:00Z",
        completed_at="2026-10-12T00:00:01Z",
        stage_attempts={},
        warning_count=0,
    )

    doc = SceneIntelligenceDocument(
        schema_version="1.0",
        outcome="complete",
        job={"job_id": "job-1", "asset_id": "asset-1", "source_kind": "generated", "extraction_profile": "standard"},
        checksum_status="not_supplied",
        media=media,
        timeline=timeline,
        shots=shots,
        frames=frames,
        provenance=prov,
    )

    violations = validate_document(doc)
    assert len(violations) == 0
