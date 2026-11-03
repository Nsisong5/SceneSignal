from pathlib import Path

import pytest

from scene_signal.render.domain.errors import RenderError
from scene_signal.render.domain.plan_validation import validate_edit_plan


def test_validate_valid_plan():
    plan_path = Path("docs/render/examples/plans/three_clips.video_only.json")
    if plan_path.exists():
        plan = validate_edit_plan(plan_path.read_bytes())
        assert plan.plan_id == "plan-example-001"

def test_validate_end_before_start():
    plan_path = Path("docs/render/examples/plans/invalid_end_before_start.json")
    if plan_path.exists():
        with pytest.raises(RenderError) as exc_info:
            validate_edit_plan(plan_path.read_bytes())
        assert exc_info.value.code == "INVALID_EDIT_PLAN"
