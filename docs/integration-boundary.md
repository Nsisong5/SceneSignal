# SceneSignal — Integration Boundary

SceneSignal is an independent greenfield project. Its integration surface with external systems (such as the existing video-generation application) is strictly defined by:
1. Versioned contract documents (`ExtractionJob` input, `SceneIntelligenceDocument` output).
2. Exported JSON Schemas (`docs/schemas/`).
3. CLI (`python -m scene_signal`) and service interfaces.

## Rules (B-1 … B-6)
- B-1: Upstream systems submit extraction requests via the `ExtractionJob` contract.
- B-2: SceneSignal resolves and inspects assets using its own storage and probe ports.
- B-3: SceneSignal core never depends on upstream internal classes, database schemas, or framework objects.
- B-4: `source_kind` is provenance metadata only and never changes pipeline behavior.
- B-5: Future upstream integration adapters live outside the core and translate generation outputs into `ExtractionJob` documents.
- B-6: No shared runtime, database, or internal storage backend is assumed.
