"""Unit tests for SceneSignal extraction job and result schemas."""

import json
from pathlib import Path

import jsonschema
import pytest

from scene_signal.domain.errors import InvalidJobContractError, UnsupportedContractVersionError
from scene_signal.schemas.export import export_schemas
from scene_signal.schemas.job import parse_extraction_job
from scene_signal.schemas.result import SceneIntelligenceDocument


def test_minimal_and_full_requests():
    min_path = Path("docs/examples/request.minimal.json")
    full_path = Path("docs/examples/request.full.json")

    job_min = parse_extraction_job(min_path.read_text(encoding="utf-8"))
    assert job_min.job_id == "extract-001"
    assert job_min.source_kind == "generated"

    job_full = parse_extraction_job(full_path.read_text(encoding="utf-8"))
    assert job_full.job_id == "extract-002"
    assert job_full.source_kind == "user_upload"


def test_source_kinds_equivalence():
    for name in ["request.generated.json", "request.user_upload.json", "request.imported.json"]:
        path = Path(f"docs/examples/{name}")
        job = parse_extraction_job(path.read_text(encoding="utf-8"))
        assert job.contract_version == "1.0"


def test_invalid_source_kind():
    path = Path("docs/examples/request.invalid_source_kind.json")
    with pytest.raises(InvalidJobContractError) as exc_info:
        parse_extraction_job(path.read_text(encoding="utf-8"))
    assert "source_kind" in exc_info.value.details["fields"]


def test_extra_fields_rejected():
    data = {
        "contract_version": "1.0",
        "job_id": "extract-001",
        "asset_id": "asset-001",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip.mp4"},
        "extraction_profile": "standard",
        "api_key": "secret123",
    }
    with pytest.raises(InvalidJobContractError):
        parse_extraction_job(data)


def test_unsupported_contract_version():
    data = {
        "contract_version": "2.0",
        "job_id": "extract-001",
        "asset_id": "asset-001",
        "source_kind": "generated",
        "asset_ref": {"scheme": "file", "uri": "clip.mp4"},
        "extraction_profile": "standard",
    }
    with pytest.raises(UnsupportedContractVersionError):
        parse_extraction_job(data)


def test_valid_result_schema():
    res_path = Path("docs/examples/result.valid.json")
    data = json.loads(res_path.read_text(encoding="utf-8"))
    doc = SceneIntelligenceDocument.model_validate(data)
    assert doc.schema_version == "1.0"
    assert doc.job["job_id"] == "extract-001"


def test_invalid_event_precision_result():
    res_path = Path("docs/examples/result.invalid_event_precision.json")
    data = json.loads(res_path.read_text(encoding="utf-8"))
    with pytest.raises(ValueError):
        SceneIntelligenceDocument.model_validate(data)


def test_export_schemas_deterministic(tmp_path):
    out_dir = tmp_path / "schemas1"
    export_schemas(out_dir)

    out_dir2 = tmp_path / "schemas2"
    export_schemas(out_dir2)

    f1 = (out_dir / "extraction_job.schema.json").read_text(encoding="utf-8")
    f2 = (out_dir2 / "extraction_job.schema.json").read_text(encoding="utf-8")
    assert f1 == f2

    # Validate example against exported schema
    job_schema = json.loads(f1)
    min_data = json.loads(Path("docs/examples/request.minimal.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=min_data, schema=job_schema)
