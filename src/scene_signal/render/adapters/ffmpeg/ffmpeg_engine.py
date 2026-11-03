from pathlib import Path
import subprocess
from scene_signal.render.ports.render_engine import RenderEnginePort, EngineResult
from scene_signal.render.domain.execution_plan import RenderExecutionPlan
from scene_signal.render.ports.progress import ProgressReporterPort
from scene_signal.render.ports.cancellation import CancellationToken
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.adapters.ffmpeg.command_builder import CommandBuilder
from scene_signal.render.adapters.ffmpeg.inspector import FfprobeInspector

class FFmpegRenderEngine(RenderEnginePort):
    def render(
        self,
        execution_plan: RenderExecutionPlan,
        workspace_dir: Path,
        progress: ProgressReporterPort,
        cancel_token: CancellationToken,
    ) -> EngineResult:
        workspace_dir.mkdir(parents=True, exist_ok=True)
        intermediates = []
        inspector = FfprobeInspector()

        target_w = execution_plan.profile.width
        target_h = execution_plan.profile.height

        total_segs = len(execution_plan.segments)
        for idx, seg in enumerate(execution_plan.segments):
            cancel_token.raise_if_cancelled()
            progress.report("normalize", idx / max(1, total_segs), f"Normalizing segment {seg.segment_id}")

            inter_path = workspace_dir / seg.intermediate_path
            intermediates.append(inter_path)

            seg_copy = seg.model_copy(update={"intermediate_path": str(inter_path)})
            cmd = CommandBuilder.build_normalize_command(seg_copy, target_w, target_h)

            try:
                proc = subprocess.run(
                    cmd,
                    shell=False,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            except subprocess.CalledProcessError as e:
                stderr_tail = e.stderr[-500:] if e.stderr else ""
                raise RenderError(
                    code="FFMPEG_FAILED",
                    message=f"FFmpeg normalization failed for segment {seg.segment_id}: {stderr_tail}",
                    retryable=False,
                    phase="render",
                    details={"stderr": stderr_tail, "segment_id": seg.segment_id},
                ) from e
            except Exception as e:
                raise RenderError(
                    code="FFMPEG_FAILED",
                    message=f"FFmpeg execution error: {e}",
                    retryable=False,
                    phase="render",
                ) from e

            # Verify intermediate output
            try:
                info = inspector.inspect(inter_path)
                if info.width != target_w or info.height != target_h:
                    raise RenderError(
                        code="FFMPEG_FAILED",
                        message=f"Intermediate dimensions mismatch for {seg.segment_id}: expected {target_w}x{target_h}, got {info.width}x{info.height}",
                        retryable=False,
                        phase="render",
                    )
            except RenderError:
                raise
            except Exception as e:
                raise RenderError(
                    code="FFMPEG_FAILED",
                    message=f"Failed to verify intermediate file for {seg.segment_id}: {e}",
                    retryable=False,
                    phase="render",
                ) from e

        cancel_token.raise_if_cancelled()
        progress.report("assemble", 0.8, "Assembling timeline")

        concat_txt = workspace_dir / "concat.txt"
        concat_lines = []
        for inter in intermediates:
            concat_lines.append(f"file '{inter.name}'")
        concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")

        out_path = workspace_dir / execution_plan.output_path
        assemble_cmd = CommandBuilder.build_assemble_command(concat_txt, out_path)

        try:
            subprocess.run(
                assemble_cmd,
                shell=False,
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            stderr_tail = e.stderr[-500:] if e.stderr else ""
            raise RenderError(
                code="FFMPEG_FAILED",
                message=f"FFmpeg assembly failed: {stderr_tail}",
                retryable=False,
                phase="render",
                details={"stderr": stderr_tail},
            ) from e
        except Exception as e:
            raise RenderError(
                code="FFMPEG_FAILED",
                message=f"FFmpeg assembly execution error: {e}",
                retryable=False,
                phase="render",
            ) from e

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise RenderError(
                code="OUTPUT_ARTIFACT_INVALID",
                message="Output artifact was not created or is empty",
                retryable=False,
                phase="render",
            )

        progress.report("complete", 1.0, "Render completed successfully")
        return EngineResult(output_path=out_path, engine_notes={"engine": "ffmpeg"})
