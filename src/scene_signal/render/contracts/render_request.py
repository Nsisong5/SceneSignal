from typing import Literal

from pydantic import BaseModel, ConfigDict

from scene_signal.render.contracts.common import CorrelationId, RenderJobId
from scene_signal.render.contracts.edit_plan import EditPlan


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["1.0"] = "1.0"
    render_job_id: RenderJobId
    plan: EditPlan
    correlation_id: CorrelationId | None = None
