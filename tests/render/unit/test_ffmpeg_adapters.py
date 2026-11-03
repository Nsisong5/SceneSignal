from pathlib import Path
from decimal import Decimal
import pytest
from scene_signal.render.adapters.media.ffmpeg_inspector import FFmpegMediaInspector
from scene_signal.render.adapters.media.ffmpeg_engine import FFmpegRenderEngine
from scene_signal.render.domain.execution_plan import RenderExecutionPlan, SegmentExecutionSpec
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef
from scene_signal.render.domain.timing import derive_timeline
from scene_signal.render.adapters.fakes.fake_progress import FakeProgressReporter
from scene_signal.render.adapters.fakes.fake_cancellation import FakeCancellationToken

@pytest.mark.requires_ffmpeg
def test_ffmpeg_media_inspector():
    clip_path = Path("tests/fixtures/media/clip_30s_continuous.mp4")
    if not clip_path.exists():
        pytest.skip("Fixture clip not found")
    
    inspector = FFmpegMediaInspector()
    info = inspector.inspect(clip_path)
    assert info.has_video is True
    assert info.width == 640
    assert info.height == 360

@pytest.mark.requires_ffmpeg
def test_ffmpeg_render_engine(tmp_path: Path):
    clip_path = Path("tests/fixtures/media/clip_30s_continuous.mp4")
    if not clip_path.exists():
        pytest.skip("Fixture clip not found")

    plan = EditPlan(
        plan_id="p-ffmpeg-1",
        assets=[PlanAsset(asset_id="a1", asset_ref=AssetRef(uri=str(clip_path)))],
        output_profile=OutputProfile(
            container="mp4",
            video_codec="h264",
            width=640,
            height=360,
            fps=24,
            fit="letterbox",
            audio=None,
        ),
        timeline=Timeline(
            segments=[Segment(segment_id="s1", asset_id="a1", source_start_seconds=Decimal("0"), source_end_seconds=Decimal("2"), audio_mode="mute")]
        ),
        expected_duration_seconds=Decimal("2.0"),
    )

    derived = derive_timeline(plan)
    exec_plan = RenderExecutionPlan(
        plan_id=plan.plan_id,
        profile=plan.output_profile,
        derived_timeline=derived,
        segments=[
            SegmentExecutionSpec(
                segment_id="s1",
                asset_id="a1",
                source_path=str(clip_path),
                source_start_seconds=Decimal("0"),
                source_end_seconds=Decimal("2"),
                frame_count=48,
                fps="24",
                width=640,
                height=360,
                fit="letterbox",
                audio_mode="mute",
                intermediate_path="inter_s1.mp4",
            )
        ],
        output_path="output.mp4",
    )

    engine = FFmpegRenderEngine()
    progress = FakeProgressReporter()
    cancel_token = FakeCancellationToken(cancelled=False)

    res = engine.render(exec_plan, tmp_path, progress, cancel_token)
    assert res.output_path.exists()
    assert res.output_path.stat().st_size > 0
