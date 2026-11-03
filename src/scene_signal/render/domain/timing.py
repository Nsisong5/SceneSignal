from decimal import Decimal
from fractions import Fraction
import math
from typing import Any
from pydantic import BaseModel, ConfigDict
from scene_signal.render.contracts.edit_plan import EditPlan
from scene_signal.render.contracts.common import Fps

def to_fraction(val: Decimal | float | int | str | Fraction) -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, Decimal):
        return Fraction(val.normalize())
    if isinstance(val, float):
        return Fraction(str(val))
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        if "/" in val:
            parts = val.split("/")
            return Fraction(int(parts[0]), int(parts[1]))
        return Fraction(val)
    raise TypeError(f"Cannot convert {type(val)} to Fraction")

def frame_index(t: Decimal | float | int | str | Fraction, fps: Fraction) -> int:
    t_f = to_fraction(t)
    fps_f = to_fraction(fps)
    val = t_f * fps_f + Fraction(1, 2)
    return math.floor(val)

class DerivedSegment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int
    segment_id: str
    asset_id: str
    source_start_seconds: Decimal
    source_end_seconds: Decimal
    duration_seconds: Decimal
    timeline_start_seconds: Decimal
    timeline_end_seconds: Decimal
    frame_start: int
    frame_count: int
    audio_mode: str

class DerivedTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segments: list[DerivedSegment]
    total_frames: int
    expected_duration_seconds: Decimal
    derived_duration_seconds: Decimal
    fps: Fps

def derive_timeline(plan: EditPlan) -> DerivedTimeline:
    fps = to_fraction(plan.output_profile.fps)
    segments = plan.timeline.segments
    
    derived_segments = []
    current_frame = 0
    current_time = Fraction(0, 1)

    for idx, seg in enumerate(segments):
        start_t = to_fraction(seg.source_start_seconds)
        end_t = to_fraction(seg.source_end_seconds)
        duration = end_t - start_t
        
        f_start = frame_index(start_t, fps)
        f_end = frame_index(end_t, fps)
        frame_cnt = f_end - f_start
        if frame_cnt < 1:
            frame_cnt = max(1, frame_index(duration, fps))
        
        timeline_start = current_time
        timeline_end = timeline_start + Fraction(frame_cnt, 1) / fps
        
        ds = DerivedSegment(
            index=idx,
            segment_id=seg.segment_id,
            asset_id=seg.asset_id,
            source_start_seconds=Decimal(str(start_t)),
            source_end_seconds=Decimal(str(end_t)),
            duration_seconds=Decimal(str(duration)),
            timeline_start_seconds=Decimal(str(timeline_start)),
            timeline_end_seconds=Decimal(str(timeline_end)),
            frame_start=current_frame,
            frame_count=frame_cnt,
            audio_mode=seg.audio_mode,
        )
        derived_segments.append(ds)
        current_frame += frame_cnt
        current_time = timeline_end

    total_frames = current_frame
    derived_duration = Fraction(total_frames, 1) / fps
    expected_dur = to_fraction(plan.expected_duration_seconds) if plan.expected_duration_seconds is not None else derived_duration

    return DerivedTimeline(
        segments=derived_segments,
        total_frames=total_frames,
        expected_duration_seconds=Decimal(str(expected_dur)),
        derived_duration_seconds=Decimal(str(derived_duration)),
        fps=plan.output_profile.fps,
    )
