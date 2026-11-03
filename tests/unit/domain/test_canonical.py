"""Unit tests for canonical JSON and request hashing."""

from scene_signal.domain.canonical import canonical_json, request_hash
from scene_signal.schemas.job import parse_extraction_job


def test_canonical_json_and_request_hash():
    data1 = {
        "contract_version": "1.0",
        "job_id": "extract-001",
        "asset_id": "asset-001",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip.mp4"},
        "extraction_profile": "standard",
        "correlation_id": "corr-1",
    }
    data2 = {
        "correlation_id": "corr-2",
        "extraction_profile": "standard",
        "asset_ref": {"uri": "clip.mp4", "scheme": "file"},
        "source_kind": "generated",
        "asset_id": "asset-001",
        "job_id": "extract-001",
        "contract_version": "1.0",
    }

    job1 = parse_extraction_job(data1)
    job2 = parse_extraction_job(data2)

    assert request_hash(job1) == request_hash(job2)
    assert canonical_json(job1) == canonical_json(job2)
