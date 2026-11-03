from pathlib import Path
import pytest
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.domain.plan_validation import validate_edit_plan
from scene_signal.render.application.render_service import RenderService
from scene_signal.render.adapters.fakes.fake_resolver import FakeAssetResolver
from scene_signal.render.adapters.fakes.fake_progress import FakeProgressReporter
from scene_signal.render.adapters.fakes.fake_clock import FakeClock
from scene_signal.render.adapters.fakes.fake_cancellation import FakeCancellationToken
from scene_signal.render.adapters.ffmpeg.inspector import FfprobeInspector
from scene_signal.render.adapters.ffmpeg.ffmpeg_engine import FFmpegRenderEngine
from scene_signal.render.adapters.storage.local_repository import LocalRenderRepository
from scene_signal.render.adapters.fakes.fake_workspace import FakeWorkspace

@pytest.mark.requires_ffmpeg
def test_render_integration_three_clips(tmp_path: Path):
    plan_path = Path("docs/render/examples/plans/three_clips.video_only.json")
    if not plan_path.exists():
        pytest.skip("Example plan not found")

    plan_data = validate_edit_plan(plan_path.read_bytes())
    req = RenderRequest(render_job_id="demo-1", plan=plan_data)

    assets_root = Path("tests/fixtures/media")
    data_root = tmp_path / "data"

    resolver = FakeAssetResolver(assets_root=assets_root)
    inspector = FfprobeInspector()
    engine = FFmpegRenderEngine()
    repository = LocalRenderRepository(data_root)
    workspace_factory = FakeWorkspace(data_root / "work" / "demo-1")
    clock = FakeClock()

    service = RenderService(
        resolver=resolver,
        inspector=inspector,
        engine=engine,
        repository=repository,
        workspace_factory=workspace_factory,
        clock=clock,
    )

    progress = FakeProgressReporter()
    cancel_token = FakeCancellationToken(cancelled=False)

    res = service.render(req, progress, cancel_token)
    assert res.status == "succeeded"
    assert res.output.frame_count == 360
    assert res.output.has_audio is False

    # Test idempotency via repository
    res2 = service.render(req, progress, cancel_token)
    assert res2.status == "succeeded"
    assert res2.render_job_id == "demo-1"
