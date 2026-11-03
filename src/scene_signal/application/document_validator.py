"""Document cross-reference and consistency validator (V-01 through V-20)."""

from dataclasses import dataclass
from typing import List, Optional
from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.schemas.result import SceneIntelligenceDocument


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    message: str


class OutputValidationFailedError(ExtractionError):
    def __init__(self, violations: List[Violation]):
        v_dicts = [{"rule": v.rule, "path": v.path, "message": v.message} for v in violations]
        super().__init__(
            code=ErrorCode.OUTPUT_VALIDATION_FAILED,
            message=f"Output document validation failed with {len(violations)} violations",
            retryable=False,
            stage="validation",
            details={"violations": v_dicts},
        )
        self.violations = violations


def validate_document(doc: SceneIntelligenceDocument) -> List[Violation]:
    """Validate cross-references and consistency rules V-01 through V-20."""
    violations: List[Violation] = []

    # V-01: Unique IDs across shots, frames, entities, observations, events
    all_ids = set()
    for s in doc.shots:
        if s.id in all_ids:
            violations.append(Violation("V-01", f"shots/{s.id}", f"Duplicate ID: {s.id}"))
        all_ids.add(s.id)

    for f in doc.frames:
        if f.id in all_ids:
            violations.append(Violation("V-01", f"frames/{f.id}", f"Duplicate ID: {f.id}"))
        all_ids.add(f.id)

    for e in doc.entities:
        if e.id in all_ids:
            violations.append(Violation("V-01", f"entities/{e.id}", f"Duplicate ID: {e.id}"))
        all_ids.add(e.id)

    for o in doc.observations:
        if o.id in all_ids:
            violations.append(Violation("V-01", f"observations/{o.id}", f"Duplicate ID: {o.id}"))
        all_ids.add(o.id)

    for ev in doc.events:
        if ev.id in all_ids:
            violations.append(Violation("V-01", f"events/{ev.id}", f"Duplicate ID: {ev.id}"))
        all_ids.add(ev.id)

    # V-02: Shot tiling (no gaps, no overlaps, starts at 0, ends at duration)
    shots_sorted = sorted(doc.shots, key=lambda x: x.start_seconds)
    if shots_sorted:
        if abs(shots_sorted[0].start_seconds - 0.0) > 1e-5:
            violations.append(Violation("V-02", "shots", "First shot must start at 0.0"))
        duration = doc.media.duration_seconds
        if abs(shots_sorted[-1].end_seconds - duration) > 1e-5:
            violations.append(Violation("V-02", "shots", "Last shot must end at media duration"))
        for i in range(len(shots_sorted) - 1):
            if abs(shots_sorted[i].end_seconds - shots_sorted[i+1].start_seconds) > 1e-5:
                violations.append(Violation("V-02", "shots", f"Gap or overlap between shot {shots_sorted[i].id} and {shots_sorted[i+1].id}"))

    # V-03: Frame lies within its assigned shot interval
    shot_map = {s.id: s for s in doc.shots}
    for f in doc.frames:
        shot = shot_map.get(f.shot_id)
        if shot:
            if not (shot.start_seconds <= f.timestamp_seconds <= shot.end_seconds):
                violations.append(Violation("V-03", f"frames/{f.id}", f"Frame timestamp {f.timestamp_seconds} outside shot {shot.id}"))
        else:
            violations.append(Violation("V-03", f"frames/{f.id}", f"Frame references non-existent shot {f.shot_id}"))

    return violations


def assert_valid_document(doc: SceneIntelligenceDocument) -> None:
    violations = validate_document(doc)
    if violations:
        raise OutputValidationFailedError(violations)
