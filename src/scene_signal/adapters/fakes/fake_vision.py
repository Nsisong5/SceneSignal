"""Fake visual analysis adapter for testing."""

from typing import List, Optional
from scene_signal.ports.visual_analysis import (
    VisualAnalysisPort,
    VisionCapabilities,
    VisionMode,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    RawObservation,
    RawEntity,
    RawEvent,
)


class FakeVisionAdapter(VisualAnalysisPort):
    def __init__(
        self,
        mode: VisionMode = VisionMode.STILL_FRAMES,
        supported_capabilities: Optional[List[str]] = None,
        fail_with: Optional[Exception] = None,
        supports_temporal_intervals: bool = False,
    ):
        self._mode = mode
        self._supported_capabilities = supported_capabilities or [
            "visual_observations",
            "shot_detection",
            "camera_analysis",
            "visible_text",
        ]
        self.fail_with = fail_with
        self._supports_temporal_intervals = supports_temporal_intervals

    def capabilities(self) -> VisionCapabilities:
        return VisionCapabilities(
            provider="fake",
            model="fake-1",
            adapter_version="1.0",
            analysis_mode=self._mode,
            supported_capabilities=self._supported_capabilities,
            supports_temporal_intervals=self._supports_temporal_intervals,
            max_frames_per_call=16,
        )

    def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        if self.fail_with:
            raise self.fail_with

        t = request.frame_timestamps_seconds[0] if request.frame_timestamps_seconds else 0.0
        obs = [
            RawObservation(
                id="obs-001",
                category="object_presence",
                scope="frame",
                timestamp_seconds=t,
                description=f"[FAKE] frame frame-001 at {t:.3f}s",
                evidence_frame_refs=["frame-001"],
            ),
            RawObservation(
                id="obs-002",
                category="environment",
                scope="shot",
                start_seconds=request.shot_start_seconds,
                end_seconds=request.shot_end_seconds,
                description="[FAKE] environment shot observation",
            ),
            RawObservation(
                id="obs-003",
                category="camera_movement",
                scope="shot",
                start_seconds=request.shot_start_seconds,
                end_seconds=request.shot_end_seconds,
                description="Camera movement unsupported in still frames mode.",
                value="unsupported",
            ),
        ]

        entities = [
            RawEntity(
                id="entity-001",
                type="person",
                label="fake subject",
            )
        ]

        events = [
            RawEvent(
                id="event-001",
                type="movement",
                description="[FAKE] movement event",
                first_seconds=request.shot_start_seconds,
                last_seconds=request.shot_end_seconds,
                temporal_precision="multi_sample_span",
            )
        ] if "temporal_events" in self._supported_capabilities and self._supports_temporal_intervals else []

        return VisionAnalysisResponse(
            shot_summary=f"A shot between {request.shot_start_seconds}s and {request.shot_end_seconds}s.",
            observations=obs,
            entities=entities,
            events=events,
        )
