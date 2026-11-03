from pathlib import Path
from scene_signal.render.ports.render_engine import RenderEnginePort, EngineResult
from scene_signal.render.domain.execution_plan import RenderExecutionPlan
from scene_signal.render.ports.progress import ProgressReporterPort
from scene_signal.render.ports.cancellation import CancellationToken

class FakeRenderEngine(RenderEnginePort):
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.render_call_count = 0

    def render(
        self,
        execution_plan: RenderExecutionPlan,
        workspace_dir: Path,
        progress: ProgressReporterPort,
        cancel_token: CancellationToken,
    ) -> EngineResult:
        self.render_call_count += 1
        cancel_token.raise_if_cancelled()
        progress.report("normalize", 0.5, "Normalizing segments (fake)")
        cancel_token.raise_if_cancelled()
        progress.report("assemble", 1.0, "Assembling output (fake)")

        if self.should_fail:
            raise RuntimeError("Fake render engine failure")

        out_path = workspace_dir / "output.mp4"
        out_path.write_bytes(b"fake rendered mp4 content")
        return EngineResult(output_path=out_path, engine_notes={"engine": "fake"})
