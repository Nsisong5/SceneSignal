from decimal import Decimal
from fractions import Fraction
from scene_signal.render.contracts.edit_plan import EditPlan
from scene_signal.render.domain.timing import derive_timeline, to_fraction
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.domain.capabilities import RendererCapabilities

def validate_timeline_rules(plan: EditPlan, capabilities: RendererCapabilities | None = None) -> None:
    if capabilities is None:
        capabilities = RendererCapabilities()

    derived = derive_timeline(plan)
    fps = to_fraction(derived.fps)

    # T-04: Segment too short (< 1 frame)
    for i, seg in enumerate(derived.segments):
        dur_f = to_fraction(seg.duration_seconds)
        if seg.frame_count < 1 or dur_f * fps < 1:
            raise RenderError(
                code="INVALID_EDIT_PLAN",
                message=f"Segment {seg.segment_id} is shorter than one frame",
                retryable=False,
                phase="validate",
                details={
                    "rule": "T-04",
                    "code": "SEGMENT_TOO_SHORT",
                    "path": f"timeline.segments[{i}]",
                    "segment_id": seg.segment_id,
                },
            )

    # T-05: Plan duration mismatch
    if plan.expected_duration_seconds is not None:
        expected = to_fraction(plan.expected_duration_seconds)
        derived_dur = to_fraction(derived.derived_duration_seconds)
        tolerance = Fraction(1, 1) / fps  # 1 frame tolerance
        if abs(derived_dur - expected) > tolerance:
            raise RenderError(
                code="INVALID_EDIT_PLAN",
                message=f"Plan expected duration {expected}s does not match derived duration {derived_dur}s",
                retryable=False,
                phase="validate",
                details={
                    "rule": "T-05",
                    "code": "PLAN_DURATION_MISMATCH",
                    "path": "expected_duration_seconds",
                    "expected": float(expected),
                    "derived": float(derived_dur),
                },
            )

    # T-06: Resource limit exceeded (timeline duration > max_timeline_seconds)
    if to_fraction(derived.derived_duration_seconds) > capabilities.limits.max_timeline_seconds:
        raise RenderError(
            code="RESOURCE_LIMIT_EXCEEDED",
            message=f"Derived timeline duration exceeds limit ({float(derived.derived_duration_seconds)}s > {capabilities.limits.max_timeline_seconds}s)",
            retryable=False,
            phase="validate",
            details={
                "rule": "T-06",
                "code": "RESOURCE_LIMIT_EXCEEDED",
                "path": "timeline",
                "duration_seconds": float(derived.derived_duration_seconds),
                "limit": capabilities.limits.max_timeline_seconds,
            },
        )
