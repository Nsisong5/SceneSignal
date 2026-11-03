from pathlib import Path
from scene_signal.render.domain.execution_plan import RenderExecutionPlan, SegmentExecutionSpec

class CommandBuilder:
    @staticmethod
    def build_normalize_command(
        segment: SegmentExecutionSpec,
        target_width: int,
        target_height: int,
        has_audio_profile: bool = False,
        source_has_audio: bool = False,
    ) -> list[str]:
        if segment.fit == "letterbox":
            vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,fps={segment.fps}"
        else:
            vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},fps={segment.fps}"

        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-ss", str(segment.source_start_seconds),
            "-to", str(segment.source_end_seconds),
            "-i", f"file:{segment.source_path}",
            "-vf", vf,
            "-frames:v", str(segment.frame_count),
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
        ]

        if has_audio_profile:
            if segment.audio_mode == "source" and source_has_audio:
                af = "aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo"
                cmd.extend(["-af", af, "-c:a", "pcm_s16le"])
            else:
                # Generate silence PCM
                duration = float(segment.source_end_seconds - segment.source_start_seconds)
                cmd.extend(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}", "-c:a", "pcm_s16le"])
                # Adjust input mapping if needed, or use filter_complex for robustness
        else:
            cmd.append("-an")

        cmd.append(segment.intermediate_path)
        return cmd

    @staticmethod
    def build_assemble_command(
        concat_txt_path: Path,
        output_path: Path,
        has_audio: bool = False,
    ) -> list[str]:
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", f"file:{concat_txt_path}",
            "-c:v", "copy",
        ]
        if has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.append("-an")

        cmd.extend(["-movflags", "+faststart", str(output_path)])
        return cmd
