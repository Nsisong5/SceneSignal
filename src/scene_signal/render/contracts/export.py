import json
from pathlib import Path

from scene_signal.render.contracts.edit_plan import EditPlan
from scene_signal.render.contracts.manifest import RenderManifest
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import RenderResult


def export_schemas_to_dir(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    schemas = {
        "edit_plan.schema.json": EditPlan.model_json_schema(),
        "render_request.schema.json": RenderRequest.model_json_schema(),
        "render_result.schema.json": RenderResult.model_json_schema(),
        "render_manifest.schema.json": RenderManifest.model_json_schema(),
    }
    paths = {}
    for filename, schema in schemas.items():
        p = out_dir / filename
        p.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
        paths[filename] = p
    return paths
