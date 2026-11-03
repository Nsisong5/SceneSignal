# SceneSignal — Architectural Decisions

| ID | Decision | Status |
|---|---|---|
| AD-1 | Shot detection runs before sampling plan; sampling planned per shot. | Approved |
| AD-2 | Real FFmpeg adapters built early (Chunks 3–6). | Approved |
| AD-3 | Developer CLI (`python -m scene_signal`) built incrementally. | Approved |
| AD-4 | Output schema additions (outcome, capabilities report, evidence span, strict temporal precision, etc.). | Approved |
| AD-5 | Partial results allowed by default on provider failure. | Approved |
| AD-6 | Input contract additions (`provider_config_ref`, `rerun_of`, extra=forbid). | Approved |
| AD-7 | Context text (`source_prompt`, `global_prompt`) not sent to vision provider by default. | Approved |
| AD-8 | Identifiers: `SceneSignal/`, `scene_signal`, distribution `scene-signal`, CLI, env prefix `SCENE_SIGNAL_`. | Approved |
| AD-9 | Greenfield workspace: independent directory and git repo. | Approved |
| AD-10 | Integration boundary: versioned contracts and exported JSON Schemas. | Approved |
| D-01 | Internal time = integer microseconds (`TimeUs`); serialized as seconds rounded to 6 decimals. | Adopted |
| D-02 | Fingerprint format `sha256:<64 hex>`; computed by streaming whole local file. | Adopted |
| D-03 | Job identity: `job_id` + request hash. | Adopted |
| D-04 | Same `job_id` + same hash → idempotent. | Adopted |
| D-05 | Local repository layout `data_root/jobs/<job_id>/`. | Adopted |
| D-06 | Synchronous core; API runs in thread pool. | Adopted |
| D-07 | Adapters do not retry internally; application `RetryPolicy` does. | Adopted |
| D-08 | Frames written as JPEG, display-oriented, long edge ≤ 1024 px. | Adopted |
| D-09 | `confidence` never calibrated in v1.0. | Adopted |
