from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict
from scene_signal.render.domain.execution_plan import RenderExecutionPlan
from scene_signal.render.ports.progress import ProgressReporterPort
from scene_signal.render.ports.cancellation import CancellationToken

class EngineResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_path: Path
    engine_notes: dict[str, Any] = {}

class RenderEnginePort(ABC):
    @abstractmethod
    def render(
        self,
        execution_plan: RenderExecutionPlan,
        workspace_dir: Path,
        progress: ProgressReporterPort,
        cancel_token: CancellationToken,
    ) -> EngineResult:
        pass
