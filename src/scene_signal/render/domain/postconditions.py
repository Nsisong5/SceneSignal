from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from scene_signal.render.contracts.render_result import PostconditionCheck, OutputMetadata
from scene_signal.render.contracts.edit_plan import EditPlan
from scene_signal.render.domain.timing import derive_timeline, to_fraction

def verify_output_postconditions(
    output_path: Path,
    output_meta: OutputMetadata,
    plan: EditPlan,
) -> list[PostconditionCheck]:
    checks: list[PostconditionCheck] = []

    # 1. file_readable
    if output_path.exists() and output_path.is_file() and output_path.stat().st_size > 0:
        checks.append(PostconditionCheck(check="file_readable", status="passed", detail="Output file exists and is readable"))
    else:
        checks.append(PostconditionCheck(check="file_readable", status="failed", detail="Output file does not exist or is empty"))

    # 2. video_present
    if output_meta.has_video:
        checks.append(PostconditionCheck(check="video_present", status="passed", detail="Video stream present"))
    else:
        checks.append(PostconditionCheck(check="video_present", status="failed", detail="Missing video stream"))

    # 3. audio expectation (R7: video only, audio absent)
    profile = plan.output_profile
    if profile.audio is None:
        if not output_meta.has_audio:
            checks.append(PostconditionCheck(check="audio_absent", status="passed", detail="Audio stream absent as requested"))
        else:
            checks.append(PostconditionCheck(check="audio_absent", status="failed", detail="Audio stream present but profile requested audio: null"))
    else:
        if output_meta.has_audio:
            checks.append(PostconditionCheck(check="audio_present", status="passed", detail="Audio stream present"))
        else:
            checks.append(PostconditionCheck(check="audio_present", status="failed", detail="Audio stream missing"))

    # 4. dimensions_match
    if output_meta.width == profile.width and output_meta.height == profile.height:
        checks.append(PostconditionCheck(check="dimensions_match", status="passed", detail=f"Dimensions match {profile.width}x{profile.height}"))
    else:
        checks.append(PostconditionCheck(check="dimensions_match", status="failed", detail=f"Dimensions mismatch: got {output_meta.width}x{output_meta.height}, expected {profile.width}x{profile.height}"))

    # 5. frame_rate_match
    derived = derive_timeline(plan)
    expected_fps = to_fraction(profile.fps)
    actual_fps = to_fraction(output_meta.frame_rate)
    if actual_fps == expected_fps:
        checks.append(PostconditionCheck(check="frame_rate_match", status="passed", detail=f"Frame rate matches {expected_fps}"))
    else:
        checks.append(PostconditionCheck(check="frame_rate_match", status="failed", detail=f"Frame rate mismatch: got {actual_fps}, expected {expected_fps}"))

    # 6. frame_count_tolerance (±1 frame)
    expected_frames = derived.total_frames
    actual_frames = output_meta.frame_count
    if abs(actual_frames - expected_frames) <= 1:
        checks.append(PostconditionCheck(check="frame_count_tolerance", status="passed", detail=f"Frame count {actual_frames} within tolerance of expected {expected_frames}"))
    else:
        checks.append(PostconditionCheck(check="frame_count_tolerance", status="failed", detail=f"Frame count {actual_frames} exceeds tolerance from expected {expected_frames}"))

    # 7. duration_tolerance (within 1/fps)
    expected_dur = to_fraction(derived.derived_duration_seconds)
    actual_dur = to_fraction(output_meta.duration_seconds)
    tolerance = Fraction(1, 1) / expected_fps
    tolerance_dec = Decimal(tolerance.numerator) / Decimal(tolerance.denominator)
    if abs(actual_dur - expected_dur) <= tolerance_dec:
        checks.append(PostconditionCheck(check="duration_tolerance", status="passed", detail=f"Duration {actual_dur}s within tolerance of expected {expected_dur}s"))
    else:
        checks.append(PostconditionCheck(check="duration_tolerance", status="failed", detail=f"Duration {actual_dur}s exceeds tolerance from expected {expected_dur}s"))

    return checks
