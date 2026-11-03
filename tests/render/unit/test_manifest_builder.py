from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef
from scene_signal.render.domain.execution_plan import RenderExecutionPlan, SegmentExecutionSpec
from scene_signal.render.domain.timing import derive_timeline
from scene_signal.render.application.manifest_builder import ManifestBuilder

def test_manifest_builder():
    plan = EditPlan(
        plan_id="p-manifest",
        assets=[PlanAsset(asset_id="a1", asset_ref=AssetRef(uri="clip1.mp4"))],
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
            segments=[Segment(segment_id="s1", asset_id="a1", source_start_seconds=0, source_end_seconds=4, audio_mode="mute")]
        ),
        expected_duration_seconds=4.0,
    )
    req = RenderRequest(render_job_id="job-man-001", plan=plan)
    derived = derive_timeline(plan)
    exec_plan = RenderExecutionPlan(
        plan_id=plan.plan_id,
        profile=plan.output_profile,
        derived_timeline=derived,
        segments=[
            SegmentExecutionSpec(
                segment_id="s1",
                asset_id="a1",
                source_path="clip1.mp4",
                source_start_seconds=0,
                source_end_seconds=4,
                frame_count=120,
                fps="30",
                width=1280,
                height=720,
                fit="letterbox",
                audio_mode="mute",
                intermediate_path="intermediate_s1.mp4",
            )
        ],
        output_path="output.mp4",
    )

    manifest = ManifestBuilder.build(
        request=req,
        execution_plan=exec_plan,
        outcome="succeeded",
        phase_reached="complete",
        renderer_meta={"name": "test"},
        sources=[],
        postconditions=[],
        warnings=[],
    )

    assert manifest.render_job_id == "job-man-001"
    assert manifest.plan_id == "p-manifest"
    assert manifest.outcome == "succeeded"
    assert manifest.plan_fingerprint.startswith("sha256:")
    assert manifest.request_hash.startswith("sha256:")
