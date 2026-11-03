# SceneSignal Render Module — Integration Boundary

## Overview
This document defines the integration boundary for Module 02 (Timeline & Render Execution), specifying how the Production Orchestrator or external consumers interact with the `scene_signal.render` package and its CLI.

## 1. Invocation Interfaces
Consumers can interact with the render module via two primary interfaces:
1. **Python Application Service (`RenderService`)**: Programmatic invocation using ports and adapters (`RenderService.render(request, progress, cancel_token)`).
2. **CLI (`python -m scene_signal.render`)**: Command-line interface for local rendering, diagnostics, capability inspection, schema export, and verification.

## 2. Idempotency & Job Claims (`render_job_id`)
- Every render request requires a unique `render_job_id`.
- The repository (`RenderRepositoryPort`) enforces atomic job claiming based on `render_job_id` and the request content hash (`request_hash`):
  - **New Job**: Claimed successfully, status set to `claimed`/`running`.
  - **Duplicate Successful Job**: Returns cached successful `RenderResult` idempotently without re-rendering.
  - **In Progress**: Returns `RENDER_JOB_IN_PROGRESS`.
  - **Conflict**: Returns `RENDER_JOB_CONFLICT` if a different request is submitted with the same `render_job_id`.

## 3. Capability Discovery
- Consumers can inspect renderer capabilities using `python -m scene_signal.render capabilities` or querying `RendererCapabilities`.
- Supported containers (`mp4`), codecs (`h264`, `aac`), frame rates (allowlist), and feature flags (`render_engine`) are explicitly gated.

## 4. Status Tracking & Artifacts
- Jobs persist state under `data_root/renders/{render_job_id}/`:
  - `request.json`: Submitted render request.
  - `status.json`: Current job status (`claimed`, `running`, `succeeded`, `failed`, `cancelled`).
  - `result.json`: Detailed execution result (`RenderResult`).
  - `manifest.json`: Detailed run manifest (`RenderManifest`).
  - `output.mp4`: Final rendered artifact.

## 5. Error & Retry Guidelines
| Error Code | Category | Action |
|---|---|---|
| `INVALID_EDIT_PLAN` / `UNSUPPORTED_CONTRACT_VERSION` | Permanent | Fix plan structure or version; do not retry. |
| `ASSET_NOT_FOUND` / `ASSET_ACCESS_DENIED` | Permanent / Configuration | Verify asset path and permissions. |
| `SOURCE_MEDIA_INVALID` / `SOURCE_AUDIO_MISSING` | Permanent | Fix source media or segment audio mode. |
| `FFMPEG_FAILED` / `OUTPUT_ARTIFACT_INVALID` | Permanent / System | Inspect stderr details; check FFmpeg setup. |
| `RENDER_TIMEOUT` / `RENDER_JOB_IN_PROGRESS` | Retryable | Retry with increased timeout or after completion. |
| `INSUFFICIENT_STORAGE` | Retryable | Free disk space and retry. |

## 6. Future Work
- Distributed storage backends (S3 / GCS).
- Asynchronous Celery/Queue workers.
- Shared media extraction kernel unification with Module 01.
