# SceneSignal — AI Instructions & Guidelines

## Project Identity
- **Project:** SceneSignal — *Turn video into timestamped editing intelligence.*
- **Package:** `scene_signal` (`scene-signal`)
- **Modules:** Module 01 (Scene Intelligence Extraction) & Module 02 (Timeline & Render Execution, `scene_signal.render`)

## Greenfield Rules (G-01 … G-09)
1. SceneSignal has its own Git repository. Never a subfolder or submodule of any other application.
2. No file is copied from, moved out of, or symlinked to any external application.
3. SceneSignal never reads, imports, parses or references external application code, databases, or schemas.
4. External generation applications are never modified.
5. Own virtual environment, own `pyproject.toml`, own dependency set.
6. Own configuration (`.env.example`, `SCENE_SIGNAL_*`); no secrets committed.
7. Own AI instructions (`GEMINI.md`) and handoff documentation (`docs/handoff.md`, `docs/decisions.md`).
8. Gemini CLI runs with its working directory set strictly to `SceneSignal/`.
9. No absolute paths hardcoded.

## Architecture & Conventions
- Ports and Adapters architecture: Domain / Application / Ports / Adapters / Schemas.
- Pydantic v2 for data contracts (`extra="forbid"`, frozen).
- Strict dependency boundary enforced by `tests/unit/test_architecture.py`: domain/application/ports cannot import fastapi, uvicorn, httpx, adapters, or provider SDKs. Stdlib-shadowing module names are strictly prohibited.
- Testing: TDD approach with pytest. Markers: `requires_ffmpeg`, `contract`, `integration`.
