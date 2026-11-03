from pathlib import Path
from decimal import Decimal
from scene_signal.render.contracts.render_result import OutputMetadata, ArtifactRef
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef
from scene_signal.render.domain.postconditions import verify_output_postconditions

def test_postconditions_passing(tmp_path: Path):
    dummy_file = tmp_path / "out.mp4"
    dummy_file.write_bytes(b"some mp4 bytes")

    plan = EditPlan(
        plan_id="p-post-1",
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

    meta = OutputMetadata(
        ref=ArtifactRef(scheme="file", uri=str(dummy_file)),
        container="mp4",
        video_codec="h264",
        audio_codec=None,
        duration_seconds=Decimal("4.0"),
        width=1280,
        height=720,
        frame_rate="30",
        frame_count=120,
        has_video=True,
        has_audio=False,
        file_size_bytes=100,
    )

    checks = verify_output_postconditions(dummy_file, meta, plan)
    for c in checks:
        assert c.status == "passed"
