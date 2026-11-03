from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from scene_signal.render.contracts.common import PlanId, ProductionId, RenderJobId
from scene_signal.render.contracts.error_info import ErrorInfo
from scene_signal.render.contracts.render_result import PostconditionCheck, WarningItem


class RenderManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    render_job_id: RenderJobId
    plan_id: PlanId
    plan_fingerprint: str
    request_hash: str
    production_id: ProductionId | None = None
    outcome: Literal["succeeded", "failed", "cancelled"]
    phase_reached: str
    profile: dict[str, Any]
    renderer: dict[str, Any]
    strategy: str = "normalize_then_assemble"
    limits_applied: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    postconditions: list[PostconditionCheck] = []
    warnings: list[WarningItem] = []
    error: ErrorInfo | None = None
    commands: list[dict[str, Any]] = []
