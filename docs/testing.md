# SceneSignal — Testing Guide

SceneSignal follows Test-Driven Development (TDD).

## Test Suites

- **Unit Tests (`tests/unit/`)**: Pure domain, schema validation, and architecture guard tests. No external dependencies or FFmpeg required.
- **Contract Tests (`tests/contract/`)**: Validating ports and adapters against expected behaviors. FFmpeg-dependent tests are marked with `@pytest.mark.requires_ffmpeg` and automatically skipped if FFmpeg/ffprobe is absent from PATH.
- **Integration Tests (`tests/integration/`)**: Optional end-to-end tests.

## Running Tests

```bash
pytest
```
