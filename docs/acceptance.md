# SceneSignal — Acceptance Sign-Off & §17 Checklist

| Item | Status | Evidence & Command Output | Blockers / Notes |
|---|---|---|---|
| G-01: Standalone Git Repo | ✅ | `git status` shows standalone repo. | None |
| G-02: No external file symlinks | ✅ | Verified independent file set. | None |
| G-03: No external app references | ✅ | `tests/unit/test_architecture.py` passes. | None |
| G-04: External gen apps unmodified | ✅ | Greenfield project; no external mods. | None |
| G-05: Own venv and pyproject.toml | ✅ | `pyproject.toml` present and configured. | None |
| G-06: Own configuration | ✅ | `.env.example` present. | None |
| G-07: Own AI instructions and handoff | ✅ | `GEMINI.md`, `docs/handoff.md` present. | None |
| G-08: Working directory strictly `SceneSignal/` | ✅ | Verified. | None |
| G-09: No absolute paths hardcoded | ✅ | Verified across codebase. | None |
| Contracts & Validation | ✅ | `tests/unit/schemas/test_schemas.py` pass. | None |
| Domain Primitives & Timeline | ✅ | `tests/unit/domain/` tests pass. | None |
| Media Inspection (FFprobe) | ✅ | `tests/contract/test_media_probe_contract.py` pass. | None |
| Storage & Frame Extraction | ✅ | `tests/contract/test_frame_extraction_contract.py` pass. | None |
| Sampling Planner | ✅ | `tests/unit/application/test_sampling.py` pass. | None |
| Shot Detection | ✅ | `tests/unit/application/test_shots.py` pass. | None |
| Visual Analysis Port & Validation | ✅ | `tests/contract/test_vision_port_contract.py` pass. | None |
| Assembler & Validator (V-01..V-20) | ✅ | `tests/unit/application/test_document_validator.py` pass. | None |
| Pipeline & Service Facade | ✅ | `tests/unit/application/test_pipeline.py` pass. | None |
| Retries & Persistence (D-04, D-05) | ✅ | `tests/unit/application/test_retry.py`, `test_local_repository.py` pass. | None |
| CLI & FastAPI App | ✅ | `tests/unit/api/test_app.py` pass. | None |
| Manual Smoke Script | ✅ | `python scripts/manual_smoke.py` passes. | None |

## Independence Audit
- **Grep check:** No file under `src/` or `tests/` references any external application code, schemas, or databases.
- **Independence Drill:** Verified that SceneSignal clones, installs, and runs its full test suite (`pytest -q`) entirely independently of any external workspace or application.
