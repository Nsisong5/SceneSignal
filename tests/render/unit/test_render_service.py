from pathlib import Path
import pytest
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef
from scene_signal.render.application.render_service import RenderService
from scene_signal.render.adapters.fakes.fake_resolver import FakeAssetResolver
from scene_signal.render.adapters.fakes.fake_inspector import FakeMediaInspector
from scene_signal.render.adapters.fakes.fake_engine import FakeRenderEngine
from scene_signal.render.adapters.fakes.fake_repository import FakeRenderRepository
from scene_signal.render.adapters.fakes.fake_workspace import FakeWorkspace
from scene_signal.render.adapters.fakes.fake_progress import FakeProgressReporter
from scene_signal.render.adapters.fakes.fake_clock import FakeClock
from scene_signal.render.adapters.fakes.fake_cancellation import FakeCancellationToken
from scene_signal.render.domain.errors import RenderError

def test_render_service_success(tmp_path: Path):
    plan = EditPlan(
        plan_id="p-service-1",
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
        expected_duration_seconds=4.0,
    )
    req = RenderRequest(render_job_id="job-svc-001", plan=plan)

    resolver = FakeAssetResolver(assets_root=tmp_path)
    inspector = FakeMediaInspector()
    engine = FakeRenderEngine()
    repository = FakeRenderRepository()
    workspace_factory = FakeWorkspace(tmp_path / "work")
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
    assert res.render_job_id == "job-svc-001"
    assert res.output.frame_count == 120
    assert engine.render_call_count == 1

    # Test Idempotency (second call with same job_id and request)
    res2 = service.render(req, progress, cancel_token)
    assert res2.status == "succeeded"
    assert engine.render_call_count == 1  # Engine not called again due to idempotency

def test_render_service_cancellation(tmp_path: Path):
    plan = EditPlan(
        plan_id="p-service-2",
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
        expected_duration_seconds=4.0,
    )
    req = RenderRequest(render_job_id="job-svc-cancel", plan=plan)

    resolver = FakeAssetResolver(assets_root=tmp_path)
    inspector = FakeMediaInspector()
    engine = FakeRenderEngine()
    repository = FakeRenderRepository()
    workspace_factory = FakeWorkspace(tmp_path / "work")
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
    cancel_token = FakeCancellationToken(cancelled=True)

    with pytest.raises(RenderError):
        service.render(req, progress, cancel_token)
