from decimal import Decimal
from typing import Any

from scene_signal.render.contracts.common import CHECKSUM_REGEX
from scene_signal.render.contracts.edit_plan import EditPlan
from scene_signal.render.contracts.loading import load_strict_json
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.domain.capabilities import RendererCapabilities
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.domain.timeline_rules import validate_timeline_rules


def validate_edit_plan(raw_input: str | bytes | dict[str, Any], capabilities: RendererCapabilities | None = None) -> EditPlan:
    if capabilities is None:
        capabilities = RendererCapabilities()

    # PR-01: Load strict JSON if input is str or bytes
    if isinstance(raw_input, (str, bytes)):
        try:
            data = load_strict_json(raw_input)
        except Exception as e:
            raise RenderError(
                code="INVALID_EDIT_PLAN",
                message=f"Strict JSON loading failed: {e}",
                retryable=False,
                phase="validate",
                details={"violations": [{"rule": "PR-01", "path": "$", "message": str(e)}]}
            )
    elif isinstance(raw_input, dict):
        data = raw_input
    else:
        raise RenderError(
            code="INVALID_EDIT_PLAN",
            message="Invalid input type for edit plan validation",
            retryable=False,
            phase="validate",
            details={"violations": [{"rule": "PR-01", "path": "$", "message": "Input must be JSON string, bytes, or dict"}]}
        )

    violations: list[dict[str, Any]] = []

    # PR-02: Contract version
    cv = data.get("contract_version")
    if cv != "1.0":
        if cv not in capabilities.contract_versions:
            raise RenderError(
                code="UNSUPPORTED_CONTRACT_VERSION",
                message=f"Unsupported contract version: {cv}",
                retryable=False,
                phase="validate",
                details={"supported": capabilities.contract_versions, "received": cv}
            )
        violations.append({"rule": "PR-02", "path": "contract_version", "message": f"Unsupported version {cv}"})

    # Pydantic parsing for PR-03, PR-04, PR-07 etc.
    try:
        plan = EditPlan.model_validate(data)
    except Exception as e:
        # Extract Pydantic validation errors into violations
        from pydantic import ValidationError
        if isinstance(e, ValidationError):
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                violations.append({"rule": "PR-03", "path": loc, "message": msg})
        else:
            violations.append({"rule": "PR-03", "path": "$", "message": str(e)})

        raise RenderError(
            code="INVALID_EDIT_PLAN",
            message="Plan structural validation failed",
            retryable=False,
            phase="validate",
            details={"violations": violations}
        )

    # PR-04: IDs match C-03 (already validated by Pydantic types, but check explicitly if needed)
    # PR-05: Uniqueness and checksum format
    asset_ids = set()
    for a in plan.assets:
        if a.asset_id in asset_ids:
            violations.append({"rule": "PR-05", "path": "assets", "message": f"Duplicate asset_id: {a.asset_id}"})
        asset_ids.add(a.asset_id)
        if a.asset_ref.checksum and not CHECKSUM_REGEX.match(a.asset_ref.checksum):
            violations.append({"rule": "PR-05", "path": f"assets.{a.asset_id}.asset_ref.checksum", "message": "Invalid checksum format"})

    segment_ids = set()
    for s in plan.timeline.segments:
        if s.segment_id in segment_ids:
            violations.append({"rule": "PR-05", "path": "timeline.segments", "message": f"Duplicate segment_id: {s.segment_id}"})
        segment_ids.add(s.segment_id)

    transition_ids = set()
    for t in plan.timeline.transitions:
        if t.transition_id in transition_ids:
            violations.append({"rule": "PR-05", "path": "timeline.transitions", "message": f"Duplicate transition_id: {t.transition_id}"})
        transition_ids.add(t.transition_id)

    # PR-06: Referenced assets exist
    warnings = []
    referenced_assets = {s.asset_id for s in plan.timeline.segments}
    for aid in referenced_assets:
        if aid not in asset_ids:
            violations.append({"rule": "PR-06", "path": "timeline.segments", "message": f"Referenced asset_id not found in assets: {aid}"})

    for aid in asset_ids:
        if aid not in referenced_assets:
            warnings.append({"code": "UNUSED_ASSET", "message": f"Asset {aid} is defined in assets but never referenced in timeline", "phase": "validate", "related_ids": [aid]})

    # PR-07: Seconds fields decimal places <= 6, finite, >= 0
    def check_seconds(val: Decimal, path: str) -> None:
        if val < 0:
            violations.append({"rule": "PR-07", "path": path, "message": f"Seconds must be >= 0: {val}"})
        # Check decimal places <= 6
        as_str = format(val.normalize(), 'f')
        if '.' in as_str:
            dec_part = as_str.split('.')[1]
            if len(dec_part) > 6:
                violations.append({"rule": "PR-07", "path": path, "message": f"Seconds precision exceeds 6 decimal places: {val}"})

    for i, s in enumerate(plan.timeline.segments):
        check_seconds(s.source_start_seconds, f"timeline.segments[{i}].source_start_seconds")
        check_seconds(s.source_end_seconds, f"timeline.segments[{i}].source_end_seconds")
        # PR-08: source_end_seconds > source_start_seconds
        if s.source_end_seconds <= s.source_start_seconds:
            violations.append({"rule": "PR-08", "path": f"timeline.segments[{i}]", "message": f"source_end_seconds ({s.source_end_seconds}) must be > source_start_seconds ({s.source_start_seconds})"})

    for i, t in enumerate(plan.timeline.transitions):
        check_seconds(t.duration_seconds, f"timeline.transitions[{i}].duration_seconds")
        if t.duration_seconds <= 0:
            violations.append({"rule": "PR-11", "path": f"timeline.transitions[{i}]", "message": "Transition duration must be > 0"})

    # PR-09: Profile width/height even and within limits; fps parses
    prof = plan.output_profile
    if prof.width % 2 != 0 or prof.height % 2 != 0:
        violations.append({"rule": "PR-09", "path": "output_profile", "message": f"Width ({prof.width}) and height ({prof.height}) must be even numbers"})
    if not (64 <= prof.width <= capabilities.limits.max_width and 64 <= prof.height <= capabilities.limits.max_height):
        violations.append({"rule": "PR-09", "path": "output_profile", "message": "Width/height out of limits"})

    # PR-10: Audio consistency: output_profile.audio == null => every audio_mode == "mute"
    if prof.audio is None:
        for i, s in enumerate(plan.timeline.segments):
            if s.audio_mode != "mute":
                violations.append({"rule": "PR-10", "path": f"timeline.segments[{i}].audio_mode", "message": "audio_mode must be 'mute' when output_profile.audio is null"})

    # PR-11: Transition structure
    seg_id_list = [s.segment_id for s in plan.timeline.segments]
    seg_index_map = {sid: idx for idx, sid in enumerate(seg_id_list)}
    seen_pairs = set()

    for i, t in enumerate(plan.timeline.transitions):
        if t.from_segment_id not in seg_index_map or t.to_segment_id not in seg_index_map:
            violations.append({"rule": "PR-11", "path": f"timeline.transitions[{i}]", "message": "Transition references unknown segment ID"})
            continue
        from_idx = seg_index_map[t.from_segment_id]
        to_idx = seg_index_map[t.to_segment_id]
        if to_idx != from_idx + 1:
            violations.append({"rule": "PR-11", "path": f"timeline.transitions[{i}]", "message": f"Transition segments must be adjacent: {t.from_segment_id} and {t.to_segment_id}"})

        pair = (t.from_segment_id, t.to_segment_id)
        if pair in seen_pairs:
            violations.append({"rule": "PR-11", "path": f"timeline.transitions[{i}]", "message": f"Duplicate transition between {pair}"})
        seen_pairs.add(pair)

    if violations:
        raise RenderError(
            code="INVALID_EDIT_PLAN",
            message="Plan validation failed with structural/constraint violations",
            retryable=False,
            phase="validate",
            details={"violations": violations}
        )

    # PR-12: Capabilities check
    unsupported = []

    # Scheme
    for a in plan.assets:
        if a.asset_ref.scheme not in capabilities.schemes:
            unsupported.append({"rule": "PR-12", "path": f"assets.{a.asset_id}.asset_ref.scheme", "value": a.asset_ref.scheme, "supported": capabilities.schemes})

    # Container & Video Codec
    if prof.container not in capabilities.containers:
        unsupported.append({"rule": "PR-12", "path": "output_profile.container", "value": prof.container, "supported": capabilities.containers})
    if prof.video_codec not in capabilities.video_codecs:
        unsupported.append({"rule": "PR-12", "path": "output_profile.video_codec", "value": prof.video_codec, "supported": capabilities.video_codecs})

    # FPS allowlist
    if not capabilities.is_fps_allowed(prof.fps):
        unsupported.append({"rule": "PR-12", "path": "output_profile.fps", "value": str(prof.fps), "supported": capabilities.fps_allowlist})

    # Fit
    if prof.fit not in capabilities.fit_modes:
        unsupported.append({"rule": "PR-12", "path": "output_profile.fit", "value": prof.fit, "supported": capabilities.fit_modes})

    # Audio profile & mode
    if prof.audio is not None:
        if prof.audio.codec not in capabilities.audio_codecs:
            unsupported.append({"rule": "PR-12", "path": "output_profile.audio.codec", "value": prof.audio.codec, "supported": capabilities.audio_codecs})

    for i, s in enumerate(plan.timeline.segments):
        if s.audio_mode not in capabilities.audio_modes:
            unsupported.append({"rule": "PR-12", "path": f"timeline.segments[{i}].audio_mode", "value": s.audio_mode, "supported": capabilities.audio_modes})

    # Transitions
    for i, t in enumerate(plan.timeline.transitions):
        if t.type not in capabilities.transition_types:
            unsupported.append({"rule": "PR-12", "path": f"timeline.transitions[{i}].type", "value": t.type, "supported": capabilities.transition_types})

    if unsupported:
        raise RenderError(
            code="UNSUPPORTED_OPERATION",
            message="Plan requests unsupported capabilities",
            retryable=False,
            phase="validate",
            details={"unsupported": unsupported}
        )

    # PR-13: Resource limits
    if len(plan.assets) > capabilities.limits.max_assets:
        raise RenderError(
            code="RESOURCE_LIMIT_EXCEEDED",
            message=f"Asset count exceeds limit ({len(plan.assets)} > {capabilities.limits.max_assets})",
            retryable=False,
            phase="validate",
            details={"limit": "max_assets", "value": len(plan.assets), "max": capabilities.limits.max_assets}
        )
    if len(plan.timeline.segments) > capabilities.limits.max_segments:
        raise RenderError(
            code="RESOURCE_LIMIT_EXCEEDED",
            message=f"Segment count exceeds limit ({len(plan.timeline.segments)} > {capabilities.limits.max_segments})",
            retryable=False,
            phase="validate",
            details={"limit": "max_segments", "value": len(plan.timeline.segments), "max": capabilities.limits.max_segments}
        )

    total_duration = sum((s.source_end_seconds - s.source_start_seconds for s in plan.timeline.segments), Decimal('0'))
    if total_duration > capabilities.limits.max_timeline_seconds:
        raise RenderError(
            code="RESOURCE_LIMIT_EXCEEDED",
            message=f"Total timeline duration exceeds limit ({total_duration} > {capabilities.limits.max_timeline_seconds})",
            retryable=False,
            phase="validate",
            details={"limit": "max_timeline_seconds", "value": float(total_duration), "max": capabilities.limits.max_timeline_seconds}
        )

    # PR-14: Timeline timing rules (T-04, T-05, T-06)
    validate_timeline_rules(plan, capabilities)

    return plan

def validate_render_request(raw_input: str | bytes | dict[str, Any], capabilities: RendererCapabilities | None = None) -> RenderRequest:
    if isinstance(raw_input, (str, bytes)):
        try:
            data = load_strict_json(raw_input)
        except Exception as e:
            raise RenderError(
                code="INVALID_EDIT_PLAN",
                message=f"Strict JSON loading failed: {e}",
                retryable=False,
                phase="validate",
                details={"violations": [{"rule": "PR-01", "path": "$", "message": str(e)}]}
            )
    elif isinstance(raw_input, dict):
        data = raw_input
    else:
        raise RenderError(
            code="INVALID_EDIT_PLAN",
            message="Invalid input type for render request validation",
            retryable=False,
            phase="validate",
            details={"violations": [{"rule": "PR-01", "path": "$", "message": "Input must be JSON string, bytes, or dict"}]}
        )

    try:
        req = RenderRequest.model_validate(data)
    except Exception as e:
        from pydantic import ValidationError
        violations = []
        if isinstance(e, ValidationError):
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                violations.append({"rule": "PR-03", "path": loc, "message": err["msg"]})
        else:
            violations.append({"rule": "PR-03", "path": "$", "message": str(e)})
        raise RenderError(
            code="INVALID_EDIT_PLAN",
            message="Render request structural validation failed",
            retryable=False,
            phase="validate",
            details={"violations": violations}
        )

    # Validate plan part with plan. prefix if it fails
    try:
        validate_edit_plan(data.get("plan", {}), capabilities)
    except RenderError as e:
        # Prefix paths in violations with plan.
        details = dict(e.details)
        if "violations" in details:
            for v in details["violations"]:
                v["path"] = f"plan.{v['path']}" if v["path"] != "$" else "plan"
        elif "unsupported" in details:
            for u in details["unsupported"]:
                u["path"] = f"plan.{u['path']}"
        raise RenderError(
            code=e.code,
            message=e.message,
            retryable=e.retryable,
            phase=e.phase,
            details=details
        )

    return req
