"""Configuration policies and Settings."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SamplingProfile:
    name: str
    target_frames_per_minute: int
    min_frames_total: int
    max_frames_total: int
    max_frames_per_shot: int


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_delay_seconds: int = 30


@dataclass(frozen=True)
class LimitsPolicy:
    max_duration_seconds: float = 3600.0
    max_file_size_bytes: int = 10 * 1024 * 1024 * 1024  # 10 GB
    max_width: int = 8192
    max_height: int = 8192


@dataclass(frozen=True)
class ShotPolicy:
    scene_threshold: float = 0.30
    min_shot_duration_seconds: float = 0.5


@dataclass(frozen=True)
class VisionPolicy:
    timeout_seconds: float = 30.0
    include_context_in_analysis: bool = False
    allow_partial_results: bool = True


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    timeout_seconds: float = 30.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    limits: LimitsPolicy = field(default_factory=LimitsPolicy)
    shot: ShotPolicy = field(default_factory=ShotPolicy)
    vision: VisionPolicy = field(default_factory=VisionPolicy)
    profiles: dict[str, SamplingProfile] = field(
        default_factory=lambda: {
            "quick": SamplingProfile("quick", target_frames_per_minute=12, min_frames_total=3, max_frames_total=12, max_frames_per_shot=4),
            "standard": SamplingProfile("standard", target_frames_per_minute=36, min_frames_total=5, max_frames_total=32, max_frames_per_shot=8),
            "thorough": SamplingProfile("thorough", target_frames_per_minute=120, min_frames_total=10, max_frames_total=90, max_frames_per_shot=16),
        }
    )

    @classmethod
    def load(cls, env: Optional[dict[str, str]] = None) -> "Settings":
        env_map = env if env is not None else os.environ

        log_level = env_map.get("SCENE_SIGNAL_LOG_LEVEL", "INFO")
        timeout_us_str = env_map.get("SCENE_SIGNAL_TIMEOUT_SECONDS", "30.0")
        timeout_seconds = float(timeout_us_str)
        if timeout_seconds <= 0:
            raise ValueError("Timeout seconds must be positive")

        max_attempts_str = env_map.get("SCENE_SIGNAL_MAX_ATTEMPTS", "3")
        max_attempts = int(max_attempts_str)
        if max_attempts < 1:
            raise ValueError("Max attempts must be at least 1")

        retry = RetryPolicy(max_attempts=max_attempts)
        vision = VisionPolicy(timeout_seconds=timeout_seconds)

        return cls(
            log_level=log_level,
            timeout_seconds=timeout_seconds,
            retry=retry,
            vision=vision,
        )
