import pytest
from scene_signal.render.domain.plan_validation import validate_edit_plan
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef

def test_timeline_duration_mismatch():
    plan = EditPlan(
        plan_id="p-1",
        assets=[
            PlanAsset(asset_id="a1", asset_ref=AssetRef(uri="clip1.mp4")),
        ],
        output_profile=OutputProfile(
            container="mp4",
            video_codec="h264",
            width=1280,
            height=720,
            fps=30,
            fit="letterbox",
            audio=None,
        ),
        timeline=Timeline(
            segments=[
                Segment(segment_id="s1", asset_id="a1", source_start_seconds=0, source_end_seconds=4, audio_mode="mute"),
            ]
        ),
        expected_duration_seconds=10.0,  # derived is 4.0s -> T-05 mismatch
    )
    with pytest.raises(RenderError) as exc_info:
        validate_edit_plan(plan.model_dump())
    assert exc_info.value.code == "INVALID_EDIT_PLAN"
    assert exc_info.value.details["code"] == "PLAN_DURATION_MISMATCH"
