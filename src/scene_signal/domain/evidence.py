"""Evidence and assertion rules (V-06, V-10, V-11, V-13)."""


def camera_movement_allowed(
    value: str, analysis_mode: str, evidence_frame_count: int, same_shot: bool
) -> bool:
    """Implement V-10 guards for camera movement / subject movement."""
    if value in ("unknown", "unsupported"):
        return True
    if analysis_mode == "still_frames" and evidence_frame_count < 2:
        return False
    if analysis_mode == "frame_sequence" and (evidence_frame_count < 2 or not same_shot):
        return False
    return True


def allowed_event_precision(temporal_precision: str, supports_temporal_intervals: bool) -> bool:
    """Implement event precision rules (C.3, V-11)."""
    if temporal_precision in ("adapter_reported_interval", "frame_accurate"):
        return supports_temporal_intervals
    return True


def observation_scope_allowed(scope: str, has_timestamp: bool, has_start_end: bool) -> bool:
    """Implement V-06 scope checks."""
    if scope == "frame":
        return has_timestamp and not has_start_end
    if scope in ("shot", "span"):
        return not has_timestamp and has_start_end
    return False
