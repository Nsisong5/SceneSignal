# SceneSignal Render Module — Acceptance Sign-Off

## Acceptance Criteria Mapping (Specification §18)

| # | Requirement | Evidence / Test Name | Command / Verification |
|---|---|---|---|
| 1 | Strict JSON loading & validation | `tests/render/unit/test_loading.py`, `test_plan_validation.py` | `python -m scene_signal.render validate-plan docs/render/examples/plans/three_clips.video_only.json` |
| 2 | Exact rational timing & derivation | `tests/render/unit/test_timing.py` | `python -m scene_signal.render timeline docs/render/examples/plans/three_clips.video_only.json` |
| 3 | Geometry fitting & letterbox/crop | `tests/render/unit/test_geometry.py` | `python -m scene_signal.render geometry --src 1080x1920 --out 1280x720 --fit letterbox` |
| 4 | Binary discovery & doctor | `tests/render/unit/test_ffmpeg_adapters.py` | `python -m scene_signal.render doctor` |
| 5 | Video-only hard-cut rendering | `tests/render/integration/test_render_integration.py` | `pytest -m requires_ffmpeg -v` |
| 6 | Output verification postconditions | `tests/render/unit/test_postconditions.py` | `python -m scene_signal.render verify-output docs/render/examples/plans/three_clips.video_only.json out_test/demo/output.mp4` |
| 7 | Audio behavior & sample-exact PCM | `tests/render/unit/test_render_service.py` | `pytest tests/render/unit/test_render_service.py` |
| 8 | Operational hardening & security | `tests/render/unit/test_architecture_render.py` | `pytest tests/render/unit/test_architecture_render.py` |
