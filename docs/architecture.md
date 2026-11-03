# SceneSignal — Architecture

SceneSignal uses a strict **Ports and Adapters** (Hexagonal) architecture to decouple domain logic and data contracts from infrastructure and vision providers.

## Layers

1. **Domain (`src/scene_signal/domain/`)**: Pure business logic, value objects (`TimeUs`, `Interval`), policies, and invariant rules. Zero dependencies on I/O, storage, or external libraries (except Pydantic if needed for value objects).
2. **Contracts / Schemas (`src/scene_signal/schemas/`)**: Pydantic v2 models defining `ExtractionJob`, `SceneIntelligenceDocument`, and typed error structures.
3. **Application (`src/scene_signal/application/`)**: Pipeline orchestration and stage execution.
4. **Ports (`src/scene_signal/ports/`)**: Abstract interfaces for storage (`AssetStoragePort`), media probe (`MediaProbePort`), frame extraction (`FrameExtractionPort`), shot detection (`ShotDetectionPort`), and vision analysis (`VisionPort`).
5. **Adapters (`src/scene_signal/adapters/`)**: Concrete implementations (FFmpeg/ffprobe, local filesystem, fakes, and future vision provider clients).
6. **Interface (`src/scene_signal/cli.py`, optional API)**: CLI entry points and service wrappers.
