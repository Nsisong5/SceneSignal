from fractions import Fraction
from pydantic import BaseModel, ConfigDict
from scene_signal.render.adapters.ffmpeg.binaries import FFmpegBinaries

class RendererFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    render_engine: bool = True

class RendererLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_segments: int = 100
    max_assets: int = 100
    max_timeline_seconds: int = 600
    max_width: int = 3840
    max_height: int = 2160
    max_asset_bytes: int = 4 * 1024 * 1024 * 1024
    max_plan_bytes: int = 1 * 1024 * 1024

class RendererCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_versions: list[str] = ["1.0"]
    schemes: list[str] = ["file"]
    containers: list[str] = ["mp4"]
    video_codecs: list[str] = ["h264"]
    audio_codecs: list[str] = ["aac"]
    audio_modes: list[str] = ["mute", "source"]
    fit_modes: list[str] = ["letterbox", "crop"]
    fps_allowlist: list[str] = [
        "24", "25", "30", "50", "60",
        "24000/1001", "30000/1001", "60000/1001"
    ]
    transition_types: list[str] = ["crossfade"]
    features: RendererFeatures = RendererFeatures(render_engine=True)
    limits: RendererLimits = RendererLimits()

    def is_fps_allowed(self, fps: Fraction) -> bool:
        allowed = {Fraction(x) for x in self.fps_allowlist}
        return fps in allowed
