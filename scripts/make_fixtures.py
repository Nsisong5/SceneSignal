"""Generate synthetic media fixtures using FFmpeg for testing."""

import json
import shutil
import subprocess
from pathlib import Path


def generate_fixtures() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("FFmpeg/ffprobe not found on PATH. Skipping fixture generation.")
        return

    out_dir = Path("tests/fixtures/media")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. clip_5s_landscape_audio.mp4 (5s landscape video with tone audio)
    clip_5s = out_dir / "clip_5s_landscape_audio.mp4"
    if not clip_5s.exists():
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=24:duration=5",
                "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                str(clip_5s),
            ],
            capture_output=True,
            check=True,
        )

    # 2. clip_portrait_5s.mp4 (720x1280 portrait)
    clip_portrait = out_dir / "clip_portrait_5s.mp4"
    if not clip_portrait.exists():
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=size=720x1280:rate=24:duration=5",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_portrait),
            ],
            capture_output=True,
            check=True,
        )

    # 3. clip_30s_continuous.mp4
    clip_30s = out_dir / "clip_30s_continuous.mp4"
    if not clip_30s.exists():
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_30s),
            ],
            capture_output=True,
            check=True,
        )

    # 4. multishot_12s.mp4 (concatenation or color transitions at 3s, 6s, 9s)
    multishot = out_dir / "multishot_12s.mp4"
    if not multishot.exists():
        # Generate 4 chunks of 3s with different colors, then concat
        chunks = []
        colors = ["red", "green", "blue", "yellow"]
        for i, color in enumerate(colors):
            chunk_path = out_dir / f"chunk_{i}.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"color=c={color}:s=640x360:r=24:d=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(chunk_path),
                ],
                capture_output=True,
                check=True,
            )
            chunks.append(chunk_path)

        concat_list = out_dir / "concat.txt"
        concat_list.write_text("\n".join(f"file 'chunk_{i}.mp4'" for i in range(4)), encoding="utf-8")

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy",
                str(multishot),
            ],
            capture_output=True,
            check=True,
        )
        for chunk_path in chunks:
            chunk_path.unlink(missing_ok=True)
        concat_list.unlink(missing_ok=True)

    # 5. black_transition_9s.mp4 (content 4s, black 1s, content 4s)
    black_trans = out_dir / "black_transition_9s.mp4"
    if not black_trans.exists():
        c1 = out_dir / "c1.mp4"
        cb = out_dir / "cb.mp4"
        c2 = out_dir / "c2.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=640x360:r=24:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(c1)], capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:r=24:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cb)], capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:r=24:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(c2)], capture_output=True, check=True)

        clist = out_dir / "concat_bt.txt"
        clist.write_text("file 'c1.mp4'\nfile 'cb.mp4'\nfile 'c2.mp4'", encoding="utf-8")

        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(clist), "-c", "copy", str(black_trans)], capture_output=True, check=True)
        c1.unlink(missing_ok=True)
        cb.unlink(missing_ok=True)
        c2.unlink(missing_ok=True)
        clist.unlink(missing_ok=True)

    manifest = {
        "multishot_12s.mp4": {"expected_cuts": [3.0, 6.0, 9.0], "tolerance": 0.1},
        "clip_30s_continuous.mp4": {"expected_cuts": [], "tolerance": 0.1},
        "black_transition_9s.mp4": {"black_intervals": [[4.0, 5.0]], "tolerance": 0.1},
    }
    Path("tests/fixtures/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Fixtures generated successfully.")


if __name__ == "__main__":
    generate_fixtures()
