"""Deterministic JSON schema export for ExtractionJob and SceneIntelligenceDocument."""

import json
from pathlib import Path

from scene_signal.schemas.job import ExtractionJob
from scene_signal.schemas.result import SceneIntelligenceDocument


def export_schemas(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    job_schema = ExtractionJob.model_json_schema()
    doc_schema = SceneIntelligenceDocument.model_json_schema()

    job_path = out_dir / "extraction_job.schema.json"
    doc_path = out_dir / "scene_intelligence_document.schema.json"

    job_path.write_text(json.dumps(job_schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doc_path.write_text(json.dumps(doc_schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
