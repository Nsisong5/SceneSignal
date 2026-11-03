"""Shot builder application logic."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from scene_signal.domain.policies import ShotPolicy
from scene_signal.domain.timeline import Interval, TimeUs
from scene_signal.ports.shot_detection import ShotDetectionResult


@dataclass(frozen=True)
class ShotDraft:
    id: str
    start_us: int
    end_us: int
    segment_kind: str  # "content" | "black"
    boundary_method: str
    boundary_kind: str
    boundary_score: Optional[float] = None
    boundary_score_meaning: Optional[str] = None
    boundary_uncertainty_us: Optional[int] = None
    analysis_status: str = "analyzed"


def build_shots(
    detection_result: Optional[ShotDetectionResult],
    media_duration_us: int,
    policy: ShotPolicy,
    requested: bool,
) -> Tuple[List[ShotDraft], List[str]]:
    """Build tiled shots from detection result and media duration."""
    warnings: List[str] = []
    duration_us = media_duration_us

    if duration_us <= 0:
        return [
            ShotDraft(
                id="shot-001",
                start_us=0,
                end_us=1000000,
                segment_kind="content",
                boundary_method="initial_segment",
                boundary_kind="asset_start",
                analysis_status="analyzed",
            )
        ], []

    if not requested:
        return [
            ShotDraft(
                id="shot-001",
                start_us=0,
                end_us=duration_us,
                segment_kind="content",
                boundary_method="initial_segment",
                boundary_kind="asset_start",
                analysis_status="not_requested",
            )
        ], []

    if detection_result is None:
        warnings.append("SHOT_DETECTION_DEGRADED")
        return [
            ShotDraft(
                id="shot-001",
                start_us=0,
                end_us=duration_us,
                segment_kind="content",
                boundary_method="initial_segment",
                boundary_kind="asset_start",
                analysis_status="analyzed",
            )
        ], warnings

    warnings.append("GRADUAL_TRANSITIONS_NOT_DETECTED")

    # Collect cut times and black intervals
    cut_times = set()
    cut_times.add(0)
    cut_times.add(duration_us)

    black_ivs = []
    for bi in detection_result.black_intervals:
        if 0 < bi.start_us < duration_us:
            cut_times.add(bi.start_us)
        if 0 < bi.end_us < duration_us:
            cut_times.add(bi.end_us)
        black_ivs.append((bi.start_us, bi.end_us))

    for b in detection_result.boundaries:
        if b.kind == "hard_cut" and 0 < b.time_us < duration_us:
            cut_times.add(b.time_us)

    sorted_cuts = sorted(list(cut_times))

    # Build intervals
    shots: List[ShotDraft] = []
    for i in range(len(sorted_cuts) - 1):
        start = sorted_cuts[i]
        end = sorted_cuts[i + 1]
        if end <= start:
            continue

        # Check if segment is black
        segment_kind = "content"
        for bs, be in black_ivs:
            if start >= bs and end <= be:
                segment_kind = "black"
                break

        boundary_method = "ffmpeg_scene_score"
        boundary_kind = "hard_cut" if i > 0 else "asset_start"
        if segment_kind == "black":
            boundary_method = "ffmpeg_blackdetect"
            boundary_kind = "black_gap"

        shots.append(
            ShotDraft(
                id=f"shot-{len(shots)+1:03d}",
                start_us=start,
                end_us=end,
                segment_kind=segment_kind,
                boundary_method=boundary_method,
                boundary_kind=boundary_kind,
                analysis_status="analyzed",
            )
        )

    if not shots:
        shots.append(
            ShotDraft(
                id="shot-001",
                start_us=0,
                end_us=duration_us,
                segment_kind="content",
                boundary_method="initial_segment",
                boundary_kind="asset_start",
                analysis_status="analyzed",
            )
        )

    return shots, warnings
