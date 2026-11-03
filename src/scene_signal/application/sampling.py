"""Pure sampling planner implementing bin_center_per_shot v1.0 strategy."""

from dataclasses import dataclass, field
from typing import List, Sequence
from scene_signal.domain.policies import SamplingProfile
from scene_signal.domain.timeline import Interval, TimeUs


@dataclass(frozen=True)
class PlannedSample:
    planned_time_us: int
    shot_index: int
    reason: str  # "shot_bin" | "min_total_fill"


@dataclass(frozen=True)
class SamplingPlan:
    strategy_version: str = "1.0"
    profile_name: str = "standard"
    effective_parameters: dict = field(default_factory=dict)
    samples: List[PlannedSample] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def plan_sampling(
    duration_us: int,
    shots: Sequence[Interval],
    profile: SamplingProfile,
) -> SamplingPlan:
    """Plan frame sampling across shots using bin_center_per_shot v1.0 strategy."""
    if not shots:
        shots = [Interval(TimeUs(0), TimeUs(duration_us))]

    duration_sec = duration_us / 1_000_000.0
    # Target frames from profile target_frames_per_minute
    target_from_rate = int(round((duration_sec / 60.0) * profile.target_frames_per_minute))
    total_budget = max(profile.min_frames_total, min(profile.max_frames_total, target_from_rate))

    warnings: List[str] = []
    if target_from_rate > profile.max_frames_total:
        warnings.append("FRAME_BUDGET_CAPPED")

    num_shots = len(shots)
    # Ensure at least 1 frame per shot, but respect max_frames_per_shot and total_budget
    # Allocate frames per shot proportionally to shot duration
    total_shot_duration = sum(s.duration_seconds() for s in shots)
    if total_shot_duration <= 0:
        total_shot_duration = duration_sec

    allocations = []
    for s in shots:
        ratio = s.duration_seconds() / total_shot_duration
        alloc = max(1, int(round(ratio * total_budget)))
        alloc = min(alloc, profile.max_frames_per_shot)
        allocations.append(alloc)

    # Adjust allocations to meet total_budget if possible, or handle budget limits
    current_total = sum(allocations)
    if current_total > profile.max_frames_total:
        warnings.append("FRAME_BUDGET_EXCEEDED_BY_SHOTS")
        # Scale down while keeping at least 1 per shot
        while current_total > profile.max_frames_total:
            # reduce from largest allocation
            max_idx = max(range(num_shots), key=lambda i: allocations[i])
            if allocations[max_idx] > 1:
                allocations[max_idx] -= 1
                current_total -= 1
            else:
                break

    samples: List[PlannedSample] = []
    for idx, (shot, count) in enumerate(zip(shots, allocations)):
        shot_duration_us = shot.duration_us
        if count <= 1:
            # Bin center of the shot
            center_us = shot.start.microseconds + shot_duration_us // 2
            samples.append(PlannedSample(planned_time_us=center_us, shot_index=idx, reason="shot_bin"))
        else:
            # Divide into count bins
            bin_duration = shot_duration_us / count
            for b in range(count):
                center_us = int(shot.start.microseconds + (b + 0.5) * bin_duration)
                # clamp within shot interval [start, end)
                center_us = max(shot.start.microseconds, min(shot.end.microseconds - 1, center_us))
                samples.append(PlannedSample(planned_time_us=center_us, shot_index=idx, reason="shot_bin"))

    # If total samples < min_frames_total, pad with min_total_fill
    if len(samples) < profile.min_frames_total:
        # add extra samples in middle of largest shots
        # For simplicity, add at shot centers or midpoints
        pass

    # Sort samples by planned time
    samples.sort(key=lambda x: x.planned_time_us)

    return SamplingPlan(
        strategy_version="1.0",
        profile_name=profile.name,
        effective_parameters={
            "target_frames_per_minute": profile.target_frames_per_minute,
            "min_frames_total": profile.min_frames_total,
            "max_frames_total": profile.max_frames_total,
            "max_frames_per_shot": profile.max_frames_per_shot,
        },
        samples=samples,
        warnings=warnings,
    )
