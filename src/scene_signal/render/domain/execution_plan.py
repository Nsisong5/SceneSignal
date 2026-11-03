from fractions import Fraction
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile
from scene_signal.render.domain.timing import DerivedTimeline

class SegmentExecutionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segment_id: str
    asset_id: str
    source_path: str
    source_start_seconds: Decimal
    source_end_seconds: Decimal
    frame_count: int
    fps: str
    width: int
    height: int
    fit: str
    audio_mode: str
    intermediate_path: str

class RenderExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    plan_id: str
    profile: OutputProfile
    derived_timeline: DerivedTimeline
    segments: list[SegmentExecutionSpec]
    output_path: str
