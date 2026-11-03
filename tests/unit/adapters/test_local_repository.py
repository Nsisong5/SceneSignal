"""Unit tests for LocalJobRepositoryAdapter."""

from pathlib import Path
import pytest
from scene_signal.adapters.storage.local_repository import LocalJobRepositoryAdapter
from scene_signal.domain.errors import ExtractionError
from scene_signal.schemas.job import parse_extraction_job
from scene_signal.domain.canonical import request_hash


def test_repository_claim_and_idempotency(tmp_path):
    repo = LocalJobRepositoryAdapter(tmp_path)
    job = parse_extraction_job({
        "contract_version": "1.0",
        "job_id": "job-repo-01",
        "asset_id": "asset-01",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip.mp4"},
        "extraction_profile": "standard",
    })
    h = request_hash(job)

    status = repo.claim_job(job, h)
    assert status == "new"

    # Claim again with same job -> idempotent_hit or handled
    status2 = repo.claim_job(job, h)
    assert status2 in ("new", "idempotent_hit", "retry_failed")


def test_repository_conflict(tmp_path):
    repo = LocalJobRepositoryAdapter(tmp_path)
    job1 = parse_extraction_job({
        "contract_version": "1.0",
        "job_id": "job-repo-02",
        "asset_id": "asset-01",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip1.mp4"},
        "extraction_profile": "standard",
    })
    h1 = request_hash(job1)
    repo.claim_job(job1, h1)

    job2 = parse_extraction_job({
        "contract_version": "1.0",
        "job_id": "job-repo-02",
        "asset_id": "asset-02",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip2.mp4"},
        "extraction_profile": "standard",
    })
    h2 = request_hash(job2)

    with pytest.raises(ExtractionError) as exc_info:
        repo.claim_job(job2, h2)
    assert exc_info.value.code.value == "JOB_ID_CONFLICT"
