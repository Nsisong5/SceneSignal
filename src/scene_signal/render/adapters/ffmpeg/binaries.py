import shutil
import subprocess
from scene_signal.render.domain.errors import RenderError

class FFmpegBinaries:
    @staticmethod
    def locate_binary(name: str) -> str:
        path = shutil.which(name)
        if not path:
            raise RenderError(
                code="FFMPEG_NOT_FOUND",
                message=f"Required binary '{name}' not found on PATH or configuration",
                retryable=False,
                phase="render",
            )
        return path

    @classmethod
    def verify(cls) -> dict[str, bool]:
        ffmpeg_bin = cls.locate_binary("ffmpeg")
        ffprobe_bin = cls.locate_binary("ffprobe")

        caps = {
            "ffmpeg": bool(ffmpeg_bin),
            "ffprobe": bool(ffprobe_bin),
            "libx264": False,
            "aac": False,
            "xfade": False,
            "acrossfade": False,
        }

        try:
            res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, check=True, timeout=10)
            if "libx264" in res.stdout:
                caps["libx264"] = True
            if "aac" in res.stdout:
                caps["aac"] = True
        except Exception:
            pass

        try:
            res = subprocess.run([ffmpeg_bin, "-filters"], capture_output=True, text=True, check=True, timeout=10)
            if "xfade" in res.stdout:
                caps["xfade"] = True
            if "acrossfade" in res.stdout:
                caps["acrossfade"] = True
        except Exception:
            pass

        return caps
