from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import (
    RenderResult,
    OutputMetadata,
    ExpectedMetadata,
    TimingMetadata,
    RendererMetadata,
    ArtifactRef,
    PostconditionCheck,
)
from scene_signal.render.contracts.canonical import request_hash
from scene_signal.render.domain.plan_validation import validate_render_request
from scene_signal.render.domain.timing import derive_timeline, to_fraction
from scene_signal.render.domain.execution_plan import RenderExecutionPlan, SegmentExecutionSpec
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.domain.postconditions import verify_output_postconditions
from scene_signal.render.ports.asset_storage import AssetResolverPort, WorkspacePort
from scene_signal.render.ports.media_probe import MediaInspectorPort
from scene_signal.render.ports.render_engine import RenderEnginePort
from scene_signal.render.ports.repository import RenderRepositoryPort
from scene_signal.render.ports.progress import ProgressReporterPort
from scene_signal.render.ports.cancellation import CancellationToken
from scene_signal.render.ports.clock import Clock
from scene_signal.render.application.manifest_builder import ManifestBuilder

class RenderService:
    def __init__(
        self,
        resolver: AssetResolverPort,
        inspector: MediaInspectorPort,
        engine: RenderEnginePort,
        repository: RenderRepositoryPort,
        workspace_factory: WorkspacePort,
        clock: Clock,
        capabilities: Any | None = None,
    ) -> None:
        self.resolver = resolver
        self.inspector = inspector
        self.engine = engine
        self.repository = repository
        self.workspace_factory = workspace_factory
        self.clock = clock
        self.capabilities = capabilities

    def render(
        self,
        request: RenderRequest | str | bytes | dict[str, Any],
        progress: ProgressReporterPort,
        cancel_token: CancellationToken,
    ) -> RenderResult:
        start_time = self.clock.now()

        try:
            if isinstance(request, RenderRequest):
                req = request
            else:
                req = validate_render_request(request, self.capabilities)
        except RenderError as e:
            raise e

        rh = request_hash(req)
        job_id = req.render_job_id

        claim_status = self.repository.claim_job(job_id, rh)
        if claim_status == "idempotent_succeeded":
            stored = self.repository.load_result(job_id)
            if stored:
                return stored
        elif claim_status == "in_progress":
            raise RenderError("RENDER_JOB_IN_PROGRESS", f"Job {job_id} is already in progress", retryable=True, phase="validate")
        elif claim_status == "conflict":
            raise RenderError("RENDER_JOB_CONFLICT", f"Job {job_id} exists with a different request hash", retryable=False, phase="validate")

        self.repository.save_request(job_id, req)
        progress.report("validate", 0.02, "Validation passed")

        try:
            cancel_token.raise_if_cancelled()

            sources_meta = []
            resolved_assets = {}
            source_audio_map = {}
            for asset in req.plan.assets:
                resolved = self.resolver.resolve(asset)
                resolved_assets[asset.asset_id] = resolved
                info = self.inspector.inspect(resolved.local_path)
                source_audio_map[asset.asset_id] = info.has_audio
                sources_meta.append({
                    "asset_id": asset.asset_id,
                    "path": str(resolved.local_path),
                    "duration_seconds": float(info.duration_seconds),
                    "width": info.width,
                    "height": info.height,
                    "frame_rate": str(info.frame_rate),
                })

            progress.report("inspect", 0.10, "Assets resolved and inspected")
            cancel_token.raise_if_cancelled()

            derived = derive_timeline(req.plan)
            seg_specs = []
            for ds in derived.segments:
                if ds.audio_mode == "source" and not source_audio_map.get(ds.asset_id, False):
                    raise RenderError(
                        code="SOURCE_AUDIO_MISSING",
                        message=f"Segment {ds.segment_id} requested source audio from asset {ds.asset_id} which has no audio stream",
                        retryable=False,
                        phase="validate",
                    )

                res_asset = resolved_assets[ds.asset_id]
                seg_specs.append(SegmentExecutionSpec(
                    segment_id=ds.segment_id,
                    asset_id=ds.asset_id,
                    source_path=str(res_asset.local_path),
                    source_start_seconds=ds.source_start_seconds,
                    source_end_seconds=ds.source_end_seconds,
                    frame_count=ds.frame_count,
                    fps=str(derived.fps),
                    width=req.plan.output_profile.width,
                    height=req.plan.output_profile.height,
                    fit=req.plan.output_profile.fit,
                    audio_mode=ds.audio_mode,
                    intermediate_path=f"intermediate_{ds.segment_id}.mp4",
                ))

            exec_plan = RenderExecutionPlan(
                plan_id=req.plan.plan_id,
                profile=req.plan.output_profile,
                derived_timeline=derived,
                segments=seg_specs,
                output_path="output.mp4",
            )

            with self.workspace_factory as ws:
                engine_res = self.engine.render(exec_plan, ws.work_dir, progress, cancel_token)
                out_file = engine_res.output_path
                file_size = out_file.stat().st_size if out_file.exists() else 0

                # Inspect output file
                out_info = self.inspector.inspect(out_file)

            calc_frames = int(to_fraction(out_info.duration_seconds) * to_fraction(out_info.frame_rate))

            output_meta = OutputMetadata(
                ref=ArtifactRef(scheme="file", uri=f"renders/{job_id}/output.mp4"),
                container=req.plan.output_profile.container,
                video_codec=req.plan.output_profile.video_codec,
                audio_codec=out_info.audio.codec if out_info.audio else None,
                duration_seconds=out_info.duration_seconds,
                width=out_info.width,
                height=out_info.height,
                frame_rate=str(out_info.frame_rate),
                frame_count=calc_frames,
                has_video=out_info.has_video,
                has_audio=out_info.has_audio,
                file_size_bytes=file_size,
            )

            postconditions = verify_output_postconditions(out_file, output_meta, req.plan)
            failed_checks = [p for p in postconditions if p.status == "failed"]
            if failed_checks:
                raise RenderError(
                    code="OUTPUT_ARTIFACT_INVALID",
                    message=f"Postconditions failed: {[p.check for p in failed_checks]}",
                    retryable=False,
                    phase="verify",
                    details={"postconditions": [p.model_dump() for p in postconditions]},
                )

            end_time = self.clock.now()
            elapsed = Decimal(str((end_time - start_time).total_seconds()))

            renderer_meta = RendererMetadata(
                name="scene_signal.render",
                version="1.0",
                ffmpeg_version="ffmpeg",
                ffprobe_version="ffprobe",
                encoder_settings={"preset": "medium"},
            )

            expected_meta = ExpectedMetadata(
                duration_seconds=derived.derived_duration_seconds,
                duration_fraction=str(derived.derived_duration_seconds),
                frame_count=derived.total_frames,
            )

            timing_meta = TimingMetadata(
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat(),
                elapsed_seconds=elapsed,
            )

            manifest = ManifestBuilder.build(
                request=req,
                execution_plan=exec_plan,
                outcome="succeeded",
                phase_reached="complete",
                renderer_meta=renderer_meta.model_dump(),
                sources=sources_meta,
                postconditions=[p.model_dump() for p in postconditions],
                warnings=[],
            )

            self.repository.save_manifest(job_id, manifest)

            result = RenderResult(
                render_job_id=job_id,
                plan_id=req.plan.plan_id,
                status="succeeded",
                output=output_meta,
                expected=expected_meta,
                timing=timing_meta,
                renderer=renderer_meta,
                postconditions=postconditions,
                warnings=[],
                manifest_ref=ArtifactRef(scheme="file", uri=f"renders/{job_id}/manifest.json"),
                error=None,
            )

            self.repository.save_result(job_id, result)
            return result

        except Exception as err:
            end_time = self.clock.now()
            elapsed = Decimal(str((end_time - start_time).total_seconds()))
            
            if isinstance(err, RenderError):
                err_info = err.to_error_info()
                status = "cancelled" if err.code == "RENDER_CANCELLED" else "failed"
                postconditions = err.details.get("postconditions", [])
            else:
                from scene_signal.render.contracts.error_info import ErrorInfo
                err_info = ErrorInfo(
                    code="INTERNAL_ERROR",
                    message=str(err),
                    retryable=False,
                    phase="render",
                    details={"exception": type(err).__name__},
                )
                status = "failed"
                postconditions = []

            renderer_meta = RendererMetadata(
                name="scene_signal.render",
                version="1.0",
                ffmpeg_version="ffmpeg",
                ffprobe_version="ffprobe",
                encoder_settings={},
            )

            expected_meta = ExpectedMetadata(
                duration_seconds=Decimal("0"),
                duration_fraction="0",
                frame_count=0,
            )

            timing_meta = TimingMetadata(
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat(),
                elapsed_seconds=elapsed,
            )

            result = RenderResult(
                render_job_id=job_id,
                plan_id=req.plan.plan_id if 'req' in locals() else "unknown",
                status=status,
                output=None,
                expected=expected_meta,
                timing=timing_meta,
                renderer=renderer_meta,
                postconditions=postconditions,
                warnings=[],
                manifest_ref=ArtifactRef(scheme="file", uri=f"renders/{job_id}/manifest.json"),
                error=err_info,
            )

            self.repository.save_result(job_id, result)
            if isinstance(err, RenderError):
                raise err
            raise RenderError("INTERNAL_ERROR", str(err), retryable=False, phase="render") from err
