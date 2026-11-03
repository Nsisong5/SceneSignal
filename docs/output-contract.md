# SceneSignal — Output Contract (`SceneIntelligenceDocument`)

The `SceneIntelligenceDocument` represents the complete scene intelligence extracted from a video asset. Key top-level sections include:
- `schema_version`: `"1.0"`
- `outcome`: `complete` | `partial`
- `job`: request echo block
- `asset_fingerprint`: sha256 hash of the video file
- `media`: technical metadata (`duration_seconds`, dimensions, codecs, frame rate mode, etc.)
- `timeline`: timeline unit and interval definitions
- `capabilities`: report on requested and unsupported capabilities
- `shots`: structural video segments tiling `[0, duration)`
- `frames`: extracted frame records with actual presentation timestamps
- `entities`: identified entities (persons, objects, etc.)
- `observations`: frame, shot, or span observations
- `events`: timestamped events
- `provenance`: execution provenance metadata
- `warnings`: list of execution warnings
