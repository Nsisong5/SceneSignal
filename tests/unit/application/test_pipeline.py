"""Integration and unit tests for ExtractionPipeline and SceneIntelligenceService."""

from pathlib import Path
import pytest
from scene_signal.adapters.fakes.fake_frames import FakeFrameExtractionAdapter
from scene_signal.adapters.fakes.fake_media_probe import FakeMediaProbe
from scene_signal.adapters.fakes.fake_shots import FakeShotDetectionAdapter
from scene_signal.adapters.fakes.fake_vision import FakeVisionAdapter
from scene_signal.adapters.storage.local_fs import LocalFilesystemStorageAdapter
from scene_signal.application.pipeline import PipelinePorts, ExtractionPipeline
from scene_signal.application.service import SceneIntelligenceService
from scene_signal.schemas.job import parse_extraction_job


def test_service_extract_with_fakes(tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"fake video bytes")

    ports = PipelinePorts(
        storage=LocalFilesystemStorageAdapter(),
        media_probe=FakeMediaProbe(),
        frame_extraction=FakeFrameExtractionAdapter(),
        shot_detection=FakeShotDetectionAdapter(),
        vision=FakeVisionAdapter(),
    )

    service = SceneIntelligenceService(ports=ports, allowed_roots=[tmp_path])

    job_dict = {
        "contract_version": "1.0",
        "job_id": "job-test-01",
        "asset_id": "asset-01",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip.mp4"},
        "extraction_profile": "standard",
    }

    result = service.extract(job_dict)
    assert result.status == "succeeded"
    assert result.document is not None
    assert result.document.outcome == "complete"
    assert len(result.document.shots) > 0
    assert len(result.document.frames) > 0
