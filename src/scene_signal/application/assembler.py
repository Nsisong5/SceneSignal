"""Document assembler combining job, media, shots, frames, and vision batches."""

from typing import Any, Dict, List, Optional
from scene_signal.schemas.job import ExtractionJob
from scene_signal.ports.media_probe import MediaInspection
from scene_signal.ports.visual_analysis import VisionAnalysisResponse, VisionCapabilities
from scene_signal.schemas.result import (
    SceneIntelligenceDocument,
    MediaMetadata,
    TimelineMetadata,
    Shot,
    FrameRecord,
    Entity,
    Observation,
    Event,
    EvidenceSpan,
    Provenance,
)
from scene_signal.application.shots import ShotDraft
from scene_signal.ports.frame_extraction import ExtractedFrame


def assemble_document(
    job: ExtractionJob,
    asset_fingerprint: str,
    checksum_status: str,
    inspection: MediaInspection,
    shot_drafts: List[ShotDraft],
    extracted_frames: List[ExtractedFrame],
    vision_results: List[VisionAnalysisResponse],
    capability_reports: List[Any],
    warnings: List[Any],
    provenance: Provenance,
) -> SceneIntelligenceDocument:
    """Assemble complete SceneIntelligenceDocument."""
    # Build media metadata
    media = MediaMetadata(
        duration_seconds=inspection.duration_seconds,
        container_duration_seconds=inspection.container_duration_seconds,
        width=inspection.width,
        height=inspection.height,
        display_width=inspection.display_width,
        display_height=inspection.display_height,
        rotation_degrees=inspection.rotation_degrees,
        pixel_aspect_ratio=inspection.pixel_aspect_ratio,
        has_video=inspection.has_video,
        has_audio=inspection.has_audio,
        frame_rate=inspection.frame_rate,
        frame_rate_mode=inspection.frame_rate_mode,
        frame_count=inspection.frame_count,
        video_codec=inspection.video_codec,
        audio_codec=inspection.audio_codec,
        container_format=inspection.container_format,
        video_time_base=inspection.video_time_base,
        file_size_bytes=inspection.file_size_bytes,
    )

    timeline = TimelineMetadata(
        unit="seconds",
        interval_convention="[start,end)",
        precision_decimals=6,
        timeline_kind="source_media",
        origin="first_video_frame",
        start_time_offset_seconds=0.0,
        source_time_base=inspection.video_time_base,
    )

    # Build shots
    shots: List[Shot] = []
    frames: List[FrameRecord] = []
    entities: List[Entity] = []
    observations: List[Observation] = []
    events: List[Event] = []

    # Map frames by shot or index
    frame_records_map: Dict[str, List[str]] = {}
    for i, ef in enumerate(extracted_frames):
        fid = f"frame-{i+1:03d}"
        # Determine shot ID based on actual_us
        assigned_shot_id = "shot-001"
        for sd in shot_drafts:
            if sd.start_us <= ef.actual_us < sd.end_us:
                assigned_shot_id = f"shot-{shot_drafts.index(sd)+1:03d}"
                break

        f_rec = FrameRecord(
            id=fid,
            timestamp_seconds=round(ef.actual_us / 1_000_000.0, 6),
            requested_timestamp_seconds=round(ef.requested_us / 1_000_000.0, 6),
            timestamp_source=ef.timestamp_source,
            pts=ef.pts,
            time_base=ef.time_base,
            frame_index=ef.frame_index,
            shot_id=assigned_shot_id,
            sampling_reason="shot_bin",
            width=ef.width,
            height=ef.height,
            artifact_ref=str(ef.path),
        )
        frames.append(f_rec)
        frame_records_map.setdefault(assigned_shot_id, []).append(fid)

    for i, sd in enumerate(shot_drafts):
        sid = f"shot-{i+1:03d}"
        f_ids = frame_records_map.get(sid, [])
        shots.append(
            Shot(
                id=sid,
                start_seconds=round(sd.start_us / 1_000_000.0, 6),
                end_seconds=round(sd.end_us / 1_000_000.0, 6),
                segment_kind=sd.segment_kind,
                boundary_method=sd.boundary_method,
                boundary_kind=sd.boundary_kind,
                boundary_score=sd.boundary_score,
                boundary_score_meaning=sd.boundary_score_meaning,
                boundary_uncertainty_seconds=sd.boundary_uncertainty_us / 1_000_000.0 if sd.boundary_uncertainty_us else None,
                frame_ids=f_ids,
                analysis_status=sd.analysis_status,
                summary=vision_results[i].shot_summary if i < len(vision_results) else None,
                observation_ids=[],
                event_ids=[],
            )
        )

    # Convert vision results to observations, entities, events
    obs_id_counter = 1
    ent_id_counter = 1
    ev_id_counter = 1

    for i, vr in enumerate(vision_results):
        sid = f"shot-{i+1:03d}"
        for ro in vr.observations:
            oid = f"obs-{obs_id_counter:03d}"
            obs_id_counter += 1
            observations.append(
                Observation(
                    id=oid,
                    category=ro.category,
                    scope=ro.scope,
                    timestamp_seconds=round(ro.timestamp_seconds, 6) if ro.timestamp_seconds is not None else None,
                    start_seconds=round(ro.start_seconds, 6) if ro.start_seconds is not None else None,
                    end_seconds=round(ro.end_seconds, 6) if ro.end_seconds is not None else None,
                    shot_id=sid,
                    description=ro.description,
                    value=ro.value,
                    entity_ids=[],
                    evidence_frame_ids=ro.evidence_frame_refs,
                    evidence_type=ro.evidence_type,
                    confidence=ro.confidence,
                    confidence_source=ro.confidence_source,
                    limitations=ro.limitations,
                )
            )

        for re_ent in vr.entities:
            eid = f"entity-{ent_id_counter:03d}"
            ent_id_counter += 1
            entities.append(
                Entity(
                    id=eid,
                    type=re_ent.type,
                    label=re_ent.label,
                    attributes=re_ent.attributes,
                    identity_scope=re_ent.identity_scope,
                    tracking_method=re_ent.tracking_method,
                    identity_notes=re_ent.identity_notes,
                    shot_ids=[sid],
                    first_observed_seconds=round(shot_drafts[i].start_us / 1_000_000.0, 6),
                    last_observed_seconds=round(shot_drafts[i].end_us / 1_000_000.0, 6),
                    observation_ids=[],
                )
            )

        for rev in vr.events:
            evid = f"event-{ev_id_counter:03d}"
            ev_id_counter += 1
            events.append(
                Event(
                    id=evid,
                    type=rev.type,
                    description=rev.description,
                    shot_id=sid,
                    entity_ids=[],
                    evidence_observation_ids=[],
                    evidence_span=EvidenceSpan(
                        first_seconds=round(rev.first_seconds, 6),
                        last_seconds=round(rev.last_seconds, 6),
                    ),
                    start_seconds=round(rev.start_seconds, 6) if rev.start_seconds is not None else None,
                    end_seconds=round(rev.end_seconds, 6) if rev.end_seconds is not None else None,
                    temporal_precision=rev.temporal_precision,
                    evidence_type=rev.evidence_type,
                    confidence=rev.confidence,
                    confidence_source=rev.confidence_source,
                    limitations=rev.limitations,
                )
            )

    job_dict = job.model_dump(mode="json")

    return SceneIntelligenceDocument(
        schema_version="1.0",
        outcome="complete",
        job=job_dict,
        asset_fingerprint=asset_fingerprint,
        checksum_status=checksum_status,
        media=media,
        timeline=timeline,
        capabilities=capability_reports,
        shots=shots,
        frames=frames,
        entities=entities,
        observations=observations,
        events=events,
        provenance=provenance,
        warnings=warnings,
    )
