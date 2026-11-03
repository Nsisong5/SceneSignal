from fractions import Fraction
from scene_signal.render.domain.timing import frame_index, derive_timeline
from scene_signal.render.contracts.edit_plan import EditPlan, OutputProfile, Timeline, Segment, PlanAsset, AssetRef

def test_frame_index():
    fps = Fraction(30, 1)
    assert frame_index(0, fps) == 0
    assert frame_index(1, fps) == 30
    assert frame_index(Fraction(1, 30), fps) == 1

def test_derive_timeline_three_clips():
    plan = EditPlan(
        plan_id="p-1",
        assets=[
            PlanAsset(asset_id="a1", asset_ref=AssetRef(uri="clip1.mp4")),
            PlanAsset(asset_id="a2", asset_ref=AssetRef(uri="clip2.mp4")),
            PlanAsset(asset_id="a3", asset_ref=AssetRef(uri="clip3.mp4")),
        ],
        output_profile=OutputProfile(
            container="mp4",
            video_codec="h264",
            width=1280,
            height=720,
            fps=30,
            fit="letterbox",
            audio=None,
        ),
        timeline=Timeline(
            segments=[
                Segment(segment_id="s1", asset_id="a1", source_start_seconds=0, source_end_seconds=4, audio_mode="mute"),
                Segment(segment_id="s2", asset_id="a2", source_start_seconds=0, source_end_seconds=4, audio_mode="mute"),
                Segment(segment_id="s3", asset_id="a3", source_start_seconds=0, source_end_seconds=4, audio_mode="mute"),
            ]
        ),
        expected_duration_seconds=12.0,
    )
    derived = derive_timeline(plan)
    assert derived.total_frames == 360
    assert len(derived.segments) == 3
    assert derived.segments[0].frame_count == 120
    assert derived.segments[1].frame_count == 120
    assert derived.segments[2].frame_count == 120
