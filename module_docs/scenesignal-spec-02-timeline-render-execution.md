# SceneSignal — Specification 02: Timeline & Render Execution
## Architect deliverable (revision 1.0): Review, Corrections, Boundaries, Frozen Contracts, Architecture, Chunked Plan, Gemini CLI Prompts, Manual Test Guide

| Item | Value |
|---|---|
| Project | **SceneSignal** — *Turn video into timestamped editing intelligence.* |
| This document | Specification 02 = **logical Module 7: Timeline & Render Execution** (Spec 01 = logical Module 5, Scene Intelligence Extraction) |
| Python package | `scene_signal`, new sub-package **`scene_signal/render/`** |
| Role of this author | Senior Video Systems Architect, acting with Chief Engineer authority to **correct** architectural and systematic contradictions in the specification (every correction is listed in A.3) |
| Status | **DRAFT — awaiting your answers to Part H and your approval of the corrections in A.3** |
| Implementation language | Python ≥ 3.11 |
| Execution engine | FFmpeg / ffprobe (behind ports) |
| Coding model | Gemini CLI |

---

## 0. How to read this file

| Tag | Audience | Meaning |
|---|---|---|
| 🧑 **FOR YOU** | You (human) | Decisions, checks, and **manual tests**. Gemini ignores these. |
| 🤖 **FOR GEMINI** | Coding model | Implementation specs and copy-paste prompts. |
| 📎 **SHARED** | Both | Contracts and reference. After approval, Part C is the **source of truth**. |

### 🧑 FOR YOU — Workflow

1. Read **Part A** (review and corrections) and **Part H** (questions). Reply "approve all defaults" or list changes.
2. Put this file at `SceneSignal/docs/render/SPEC-02-timeline-render.md` (create the `docs/render/` folder; this is the only manual filesystem step, and it is inside the existing SceneSignal project).
3. For each chunk **R1 → R11**, in order: open Gemini CLI with the working directory set to `SceneSignal/`, paste **G.0 Standing Rules**, then that chunk's prompt from Part G, wait for the **Completion Report**, run the chunk's **🧑 manual test** box in Part E, then approve or send me the report.
4. Never give Gemini two chunks at once. Never skip a chunk.
5. Never run Gemini inside, or give it access to, the existing generation application or its notebook.

### 🧑 FOR YOU — Prerequisites (check before Chunk R1)

| Need | Check (run inside `SceneSignal/`) | Why |
|---|---|---|
| SceneSignal project exists (Module 01 Chunk 0 done: scaffold, `GEMINI.md`, own Git repo, virtualenv) | `git rev-parse --show-toplevel` prints the `SceneSignal` path; `pytest -q` is green | Module 02 lives inside the same project and package. If the project does not exist yet, **do Module 01's Pre-flight and Chunk 0 first**. I will not guess a path and Gemini will stop rather than create a project. |
| Python 3.11+ | `python --version` | |
| FFmpeg and ffprobe on PATH | `ffmpeg -version` and `ffprobe -version` | Needed from R5 |
| Encoders `libx264` and `aac` | macOS/Linux: `ffmpeg -hide_banner -encoders \| grep -E "libx264\|aac"` · Windows: `ffmpeg -hide_banner -encoders \| findstr "libx264 aac"` | Needed from R6 / R8 |
| Filters `xfade` and `acrossfade` | `ffmpeg -hide_banner -filters \| grep -E "xfade\|acrossfade"` (Windows: `findstr`) | Needed only for R9 |
| A video player (VLC, QuickTime, …) | — | You will **watch** rendered output in manual tests |

You need no API key, GPU, or paid service.

---

# PART A — Technical review

## A.1 🧑 FOR YOU — Verdict

The architecture is **sound**: separating *what to edit* (Module 6) from *how to execute* (Module 7), structured operations instead of commands, FFmpeg behind a port, a manifest for provenance, and contract-first TDD are all correct. However the specification as written contains **several contradictions and gaps that would have caused broken timelines, redundant data, or unsafe execution** if implemented literally. As Chief Engineer I have corrected them (A.3). The most important:

1. **Timeline positions and duration were stored in the plan *and* derivable** — two sources of truth that can disagree. They are now **derived**.
2. **The plan had no asset locations** but the renderer must resolve assets. An `assets` table is added.
3. **Frame math was undefined.** Without cumulative frame rounding, timelines drift or end up a frame off. The contract now defines exact frame boundaries and the tolerance.
4. **Source time was undefined across modules.** It is now pinned to the same origin as Spec 01 (first video frame = 0), otherwise timestamps from extraction would cut the wrong frames.
5. **The proposed chunk order put FFmpeg before any testable core.** That violates the spec's own §15. Added a pure timing kernel and a fake-backed render service **before** any FFmpeg code.
6. **Audio "mixing" was both in scope and deferred.** Resolved: sequential composition only; parallel mixing and background music are deferred.

There are **no blockers**. Part H has six questions, each with a safe default.

## A.2 📎 SHARED — What is established, what I recommend, what needs you

| Category | Items |
|---|---|
| **Established by the spec (preserved)** | Separate directory/project; FFmpeg as first engine; typed errors; no shell/LLM-supplied commands; hard cuts first, crossfade only after baseline works; versioned contracts; render manifest; no creative decisions in the renderer; renderer does not replace Output Validation; no GPU/paid services in tests; existing generation app and notebook untouched |
| **Recommended by me (decided unless you object)** | Corrections K-1…K-20 below; the `normalize-then-assemble` execution strategy; chunk plan R1–R11; no internal retries in v1.0; exact `Fraction` timing kernel; progressive capability gating |
| **Genuinely needs your input** | Part H only (6 questions) |

## A.3 📎 SHARED — Corrections and decisions made as Chief Engineer

| # | Contradiction / gap in the specification | Decision | Impact |
|---|---|---|---|
| K-1 | **Numbering.** "Specification 02" vs "Module 7". | Documents are identified by spec number; the logical module is stated in the title. This is Spec 02 / Module 7. | Naming only |
| K-2 | **Stored vs derived timeline.** The example stores `timeline_start_seconds` per segment and `timeline.duration_seconds`; both are derivable from ordered segments, so they can contradict each other. | **Derived.** v1.0 is **sequential and gap-free**. `timeline_start_seconds` and `timeline.duration_seconds` are **removed** from the input. An optional `expected_duration_seconds` remains as a planner-side *assertion* checked against the derived value (catches planner bugs). Derived positions appear in the manifest. | Contract |
| K-3 | **No asset locations.** The example references `asset_id` only, yet §13 requires asset resolution and no registry module exists yet. | Plan carries an **`assets` table** (`asset_id` → `asset_ref`, same `{scheme, uri, checksum}` shape as Spec 01). `checksum` lets the planner pin the exact bytes that Module 5 analyzed. A registry-based resolver is future work. | Contract |
| K-4 | **"Mixing supported audio sources"** (§4 item 9) vs §9's minimal audio set. | In v1.0 "mixing" means **sequential composition** of per-segment audio (and, with crossfade, fading at overlaps). Parallel multi-source mixing, background music, gain/volume are **deferred** (contract 1.1). | Scope |
| K-5 | **Chunk order.** The spec's Chunk 2 builds the FFmpeg adapter before any orchestration, while §15 demands that core logic is testable without FFmpeg. | Added **R2** (pure timing/geometry kernel) and **R3** (render service with fakes) before FFmpeg. Audio and crossfade are **capability-gated**, so contracts can be frozen before those features exist. | Plan |
| K-6 | **Retries.** §12 allows bounded retries; but most FFmpeg failures are deterministic, and retries add hidden complexity. | **No internal retries in v1.0.** Errors carry a `retryable` flag; the Orchestrator decides. Revisit only with evidence. | Behavior |
| K-7 | **Output inspection boundary.** §10 forbids declaring success from exit code alone, while "avoid duplicating Output Validation". | Renderer checks only **self-consistency postconditions** (file readable; promised streams present; dimensions and frame rate equal the profile; duration within tolerance). A failing postcondition means the render **fails**. Delivery/content/platform checks belong to Module 8. | Boundary |
| K-8 | **Module coupling.** Module 01's flat layout (`domain/`, `ports/`, … at package root) cannot hold a second module without mixing concerns; a shared error/time/probe library would couple modules. | Render lives in **`scene_signal/render/`** with its own `contracts/domain/ports/application/adapters`. **No imports across modules in either direction** (enforced by an architecture test). Small duplication (error shape, probe) is accepted now; a shared kernel is extracted only when a **third** consumer exists (Module 8 will need probing). A cross-probe parity test is planned (R11, optional). | Architecture |
| K-9 | **State files.** Spec 02 names `AI_RULES.md` / `SESSION_BOOT.md`; Module 01 created `GEMINI.md` and `docs/handoff.md`. A single "Next chunk" file cannot serve two modules. | Module 02 owns **`docs/render/handoff.md`** and `docs/render/decisions.md` (Module 01 files are not edited). It adds a short registry entry to `GEMINI.md`, and to `AI_RULES.md` / `SESSION_BOOT.md` **only if they exist**. | Docs |
| K-10 | **Numbers in JSON.** Python's `json` accepts `NaN`/`Infinity` and turns decimals into binary floats (0.1 is inexact). | Strict loader: reject `NaN`/`Infinity`/duplicate keys/trailing data; parse decimals as exact `Decimal`; max **6 decimal places** (microsecond grid); floats within 1e-9 of the grid are snapped, others rejected. | Correctness |
| K-11 | **Path exposure.** §11 says not to expose local paths unnecessarily, yet results must locate the artifact. | `RenderResult.output.ref` is **relative to the configured output root**. The manifest records asset ids, fingerprints and basenames, never absolute paths. | Security |
| K-12 | **"Named output profile"** (§5.2) vs explicit fields (§6). | Contract carries **explicit profile fields** plus an optional label `name` (provenance only). Named presets are a config/CLI convenience, not part of the contract. | Contract |
| K-13 | **Frame rate** as `30` vs rational. | `fps` accepts an integer or a string `"n/d"`; floats rejected; v1.0 **allowlist**: 24, 25, 30, 50, 60, 24000/1001, 30000/1001, 60000/1001. | Contract |
| K-14 | **Contradictory plans**: `audio_mode: source` while the profile has no audio. | Rejected as `INVALID_EDIT_PLAN` (never silently drop audio). With no output audio every segment must say `mute`. | Validation |
| K-15 | **Cancellation/timeouts "where practical"** has no home in the chunk list. | Cancellation token plumbing in R3, safe runner with timeout/kill in R5, end-to-end verification in R10. | Plan |
| K-16 | **Source time origin undefined** (spec distinguishes source vs timeline time but never defines source zero). | Source time = **media time with origin at the first video frame's presentation timestamp = 0**, identical to Spec 01. Both audio and video are trimmed by the same absolute container timestamps (`video_start_time + source_time`). | Cross-module correctness |
| K-17 | **Which duration validates a range?** The extraction module's duration or the renderer's? | The renderer's **own inspection** is authoritative. Extraction data is advisory. | Boundary |
| K-18 | **"Normalize" vs "must not invent edits".** | Defined an explicit **normalization allowlist** (C.8). Anything else (speed change, stretch, reorder, grading) is forbidden. | Boundary |
| K-19 | `production_id` required in the example. | **Optional** (ad-hoc renders must work). | Contract |
| K-20 | **Determinism claim.** | Same plan + same bytes + same renderer version/settings ⇒ same *decisions* (frame counts, order, geometry), recorded in the manifest. **No bit-for-bit promise.** | Honesty |

## A.4 📎 SHARED — Hidden risks prioritized (summary; full register in Part F)

1. **Wrong cuts from timestamp handling** (VFR, non-zero start time, rotation, B-frame offsets). Mitigation: exact timing kernel, absolute-timestamp trimming, per-segment frame-count verification, marker-based tests.
2. **Timeline drift from naive rounding.** Mitigation: cumulative frame boundaries (C.4).
3. **Unsafe execution** (arguments, protocols, playlists referencing other files). Mitigation: no plan strings reach FFmpeg, argument lists only, protocol and demuxer allowlists, security regression tests.
4. **Audible audio by accident / AAC join gaps.** Mitigation: explicit audio semantics; per-segment PCM at sample-exact lengths and **one** AAC encode.
5. **Unmaintainable coupling** to FFmpeg syntax or to Module 01. Mitigation: engine-neutral `RenderExecutionPlan`; dependency tests.

---

# PART B — Responsibility boundaries (📎 SHARED)

## B.1 Who owns what

| Module | Owns (decisions) | Owns (validation) | Does **not** |
|---|---|---|---|
| **5. Scene Intelligence Extraction** | Facts about source media: actual durations, shots, observations, timestamps (source time, first-frame origin) | Validity of its own output document | Know about plans; choose footage |
| **6. Edit Planning & Decision Engine** | **All creative decisions**: which assets, which ranges, order, transitions, audio modes, output profile choice (from the brief) | **Semantic validity**: do the ranges contain the intended content; is the plan feasible for the published `RendererCapabilities`; does it use only supported operations | Execute media; verify files |
| **7. Timeline & Render Execution (this module)** | **Execution only**: normalization policy per declared `fit`, derived timeline math, FFmpeg graph, encoding | **Technical executability**: schema, version, capabilities, asset resolution and checksums, source ranges against **its own inspection**, audio availability, timing math, self-consistency postconditions | Judge content quality; reorder/trim/replace anything not in the plan; decide delivery fitness |
| **8. Output Validation & Delivery** | Whether an artifact meets **delivery requirements** (platform specs, loudness, black frames, intended duration, playability checks) and the delivery action | Independent inspection of the final file | Re-render or edit |
| **2. Production Orchestrator** | Job lifecycle, submission, **retries**, whether to re-plan/regenerate on failure, registering artifacts, mapping errors to policy | Request completeness (ids, correlation) | Interpret media or edit |

## B.2 Decision / validation matrix

| Question | Decided by | Checked by |
|---|---|---|
| Which clips and ranges appear | Module 6 | Module 7 (ranges exist) |
| Do the ranges show what was intended | Module 6 (via Module 5 data) | Module 8 (outcome), not Module 7 |
| Is a source range inside the real media | — | **Module 7** (own probe) |
| Output resolution, fps, codec, fit | Module 6 / brief | Module 7 (supported?), Module 8 (delivered?) |
| Is a transition allowed/feasible | Module 6 chooses; Module 7 publishes capabilities | **Module 7** rejects unsupported/infeasible |
| Audio on/off per segment | Module 6 | Module 7 (availability, no unintended audio) |
| Retry or regenerate after failure | Module 2 | — |
| Produced file correct for delivery | — | Module 8 |

## B.3 Handoffs

`Module 5 → Module 6`: extraction documents. `Module 6 → Module 2 → Module 7`: `EditPlan` inside `RenderRequest`. `Module 7 → Module 2 → Module 8`: `RenderResult` + manifest + artifact reference. Module 7 never talks to Modules 5, 6, 8 directly.

---

# PART C — Frozen contracts (📎 SHARED)

> Gemini: this Part is frozen after approval. Do not rename fields, change enums, or relax rules. If you believe a rule is wrong, **stop and file a CONTRADICTION REPORT** (format in G.0).

## C.1 Conventions

| ID | Rule |
|---|---|
| C-01 | JSON, UTF-8. Pydantic v2 models, `extra="forbid"`, frozen. All modeled fields serialized (nulls written explicitly). |
| C-02 | Versions are `"MAJOR.MINOR"` strings; this release `"1.0"` for every contract below. Unknown major, or minor greater than supported → `UNSUPPORTED_CONTRACT_VERSION`. Additive changes bump the minor; plans are **never silently upgraded**; migrations would be explicit and outside the renderer. |
| C-03 | External IDs (`plan_id`, `production_id`, `asset_id`, `segment_id`, `transition_id`, `render_job_id`, `correlation_id`): `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`. |
| C-04 | **Time in the public contract = decimal seconds**: JSON numbers (never strings), parsed exactly as `Decimal`, ≥ 0, at most **6 decimal places**. Internally exact `Fraction`. |
| C-05 | **Source time** = position in the original media with **origin = presentation time of the first video frame** (identical to Spec 01). **Timeline time** = position in the assembled output, origin 0. The two are never mixed. |
| C-06 | Intervals are **half-open** `[start, end)`; segment duration = `end − start`; `end > start`. |
| C-07 | The plan contains **data only**: no commands, no filter strings, no free text that reaches FFmpeg. Free-text fields (`name`) are labels. |
| C-08 | Secrets never appear in plans, results, manifests or ordinary logs. |
| C-09 | Frame rate is an exact rational (C.2). Floats are rejected. |

## C.2 `EditPlan` v1.0 (input)

**Top level**

| Field | Type | Required | Notes |
|---|---|---|---|
| `contract_version` | string | yes | `"1.0"` |
| `plan_id` | id | yes | |
| `production_id` | id | no | K-19 |
| `assets` | list of `PlanAsset` | yes | 1…`max_assets` (default 100), unique `asset_id` |
| `output_profile` | `OutputProfile` | yes | |
| `timeline` | `Timeline` | yes | |
| `expected_duration_seconds` | decimal | no | Planner's assertion; checked in R2 against derived duration (tolerance: one output frame) |

**`PlanAsset`**: `{asset_id, asset_ref: {scheme: string, uri: string, checksum: string|null}}`. `checksum` format `sha256:<64 lowercase hex>`. v1.0 supports scheme `file` only (other schemes: `UNSUPPORTED_OPERATION`). Still images are **not** supported assets in v1.0 (K: deferred).

**`OutputProfile`**

| Field | Type | v1.0 allowed |
|---|---|---|
| `name` | string \| null | label only (≤ 64 chars) |
| `container` | string | `"mp4"` |
| `video_codec` | string | `"h264"` |
| `width`, `height` | int | even, `64 ≤ width ≤ 3840`, `64 ≤ height ≤ 2160` (configurable limits) |
| `fps` | int \| `"n/d"` string | allowlist in K-13 |
| `fit` | string | `"letterbox"` (scale to fit, pad black) or `"crop"` (scale to cover, center crop). **Required**, no default. Never stretch. |
| `audio` | object \| null | `null` = **output has no audio stream**. Otherwise `{codec: "aac", sample_rate: 48000, channels: 2}` (enabled by R8) |

Pixel format is fixed `yuv420p`; pad color fixed black; encoder quality is renderer configuration, not part of the plan (recorded in the manifest).

**`Timeline`**: `{segments: [Segment], transitions: [Transition]}`

**`Segment`** (list order **is** timeline order)

| Field | Type | Notes |
|---|---|---|
| `segment_id` | id | unique in the plan |
| `asset_id` | id | must exist in `assets` |
| `source_start_seconds` | decimal | ≥ 0 |
| `source_end_seconds` | decimal | `> source_start_seconds` |
| `audio_mode` | string | **Required.** `"source"` or `"mute"` (see C.6) |

Segments: 1…`max_segments` (default 100).

**`Transition`** (schema frozen now, **capability-gated**: renderer rejects it until R9)

| Field | Type | Notes |
|---|---|---|
| `transition_id` | id | |
| `type` | string | known: `"crossfade"`. Any other string → `UNSUPPORTED_OPERATION` |
| `from_segment_id`, `to_segment_id` | id | `to` must be the segment **immediately after** `from` |
| `duration_seconds` | decimal | constraints in C.5 |

At most one transition per adjacent pair. Hard cuts are the **implicit** default between adjacent segments; there is no explicit `cut` type.

### Plan validation rules (evaluated in this order)

| Rule | Check | Error |
|---|---|---|
| PR-01 | Input is strict JSON ≤ 1 MiB: no `NaN`/`Infinity`, no duplicate keys, no trailing data | `INVALID_EDIT_PLAN` |
| PR-02 | `contract_version` supported | `UNSUPPORTED_CONTRACT_VERSION` |
| PR-03 | Required fields present, no unknown fields, types correct | `INVALID_EDIT_PLAN` |
| PR-04 | IDs match C-03 | `INVALID_EDIT_PLAN` |
| PR-05 | `asset_id` unique; `segment_id` unique; `transition_id` unique; checksum format | `INVALID_EDIT_PLAN` |
| PR-06 | Every `segment.asset_id` exists (unreferenced assets → warning `UNUSED_ASSET`) | `INVALID_EDIT_PLAN` |
| PR-07 | Seconds fields: number (not bool), finite, ≥ 0, ≤ 6 decimals (K-10) | `INVALID_EDIT_PLAN` |
| PR-08 | `source_end_seconds > source_start_seconds` | `INVALID_EDIT_PLAN` |
| PR-09 | Profile: width/height even and within limits; `fps` parses (int or `"n/d"`, positive) | `INVALID_EDIT_PLAN` |
| PR-10 | Audio consistency: `output_profile.audio == null` ⇒ every `audio_mode == "mute"` (K-14) | `INVALID_EDIT_PLAN` |
| PR-11 | Transition structure (known types): ids exist; `to` immediately follows `from`; no duplicate pair; `duration_seconds > 0` | `INVALID_EDIT_PLAN` |
| PR-12 | Capabilities: scheme, container, video codec, fps allowlist, fit, audio codec/sample rate/channels, `audio_mode` value, transition type each ∈ `RendererCapabilities` | `UNSUPPORTED_OPERATION` (`details.unsupported[]` = `{rule, path, value, supported}`) |
| PR-13 | Limits: segment count, asset count, summed segment duration ≤ `max_timeline_seconds` (default 600 s) | `RESOURCE_LIMIT_EXCEEDED` |
| PR-14 (R2) | Derived timeline rules T-01…T-06 (C.4) | `INVALID_EDIT_PLAN` |

All violations of one stage are collected (max 50) and reported together: `details.violations[] = {rule, path, message}`. Structural errors (PR-01…PR-11) are reported before capability errors (PR-12) before limits (PR-13).

## C.3 `RendererCapabilities` v1.0

A versioned, published description of what the renderer accepts, so planners and orchestrators can discover limits instead of guessing. Gated progressively by chunk:

| Capability | After R1 (validation only) | After R6 | After R8 | After R9 |
|---|---|---|---|---|
| `contract_versions` | `["1.0"]` | same | same | same |
| `schemes` | `["file"]` | same | same | same |
| `containers` | `["mp4"]` | same | same | same |
| `video_codecs` | `["h264"]` | same | same | same |
| `audio_codecs` | `[]` | `[]` | `["aac"]` | same |
| `audio_modes` | `["mute"]` | `["mute"]` | `["source","mute"]` | same |
| `fit_modes` | `["letterbox","crop"]` | same | same | same |
| `fps_allowlist` | K-13 list | same | same | same |
| `transition_types` | `[]` | `[]` | `[]` | `["crossfade"]` (only if the local FFmpeg has `xfade` and `acrossfade`) |
| `features.render_engine` | `false` | `true` | `true` | `true` |
| `limits` | `max_segments 100`, `max_assets 100`, `max_timeline_seconds 600`, `max_width 3840`, `max_height 2160`, `max_asset_bytes 4 GiB`, `max_plan_bytes 1 MiB` | same | same | same |

A test in each chunk asserts that capabilities **exactly** equal this table, so the renderer cannot claim support it does not have.

## C.4 Timing semantics (normative)

**Notation.** Segment *i* (0-based) has exact duration `d_i = source_end − source_start` (`Fraction`). Output frame rate `fps = p/q` (`Fraction`). `F(t) = floor(t·fps + 1/2)` (**round half up**) maps timeline seconds to a frame index.

| ID | Rule |
|---|---|
| T-01 | **Derived timeline.** With no transitions: `T_0 = 0`, `T_{i+1} = T_i + d_i`. With crossfade of length `x_i` between *i* and *i+1*: `T_{i+1} = T_i + d_i − x_i` (overlap; **no source handles are added**: a transition never reads media outside a segment's declared range). `x_i = 0` for a hard cut. |
| T-02 | **Frame boundaries use cumulative rounding** (no drift): `f_i = F(T_i)`; `n_i = F(T_i + d_i) − f_i` output frames for segment *i*; total frames `N = F(T_end)` where `T_end = T_last + d_last`; overlap frames `m_i = f_i + n_i − f_{i+1}` (0 for cuts). |
| T-03 | `expected_duration = N / fps` (exact rational; reported as decimal seconds rounded to 6 places **and** as the fraction). Always `|expected_duration − (Σd − Σx)| ≤ 0.5 / fps`. |
| T-04 | Every segment must produce **≥ 1 frame** (`n_i ≥ 1`), else `INVALID_EDIT_PLAN` (`SEGMENT_TOO_SHORT`). |
| T-05 | If `expected_duration_seconds` is given, `|derived − asserted| ≤ 1 / fps`, else `INVALID_EDIT_PLAN` (`PLAN_DURATION_MISMATCH`). |
| T-06 | `T_end ≤ max_timeline_seconds`. |
| T-07 | **Source frame selection.** Output frame *k* of segment *i* shows the source picture at `source_start + k/fps`, taking the source frame whose presentation interval contains that time (nearest-previous); if the source runs out within tolerance, the last frame is held. |
| T-08 | **Frame-accuracy definition (what is promised).** (a) segment order exactly as planned; (b) per-segment frame counts `n_i` and total `N` exactly as derived; (c) the picture shown for any output frame comes from within **±1 frame period** (the larger of the source and output frame periods) of the ideal source time; (d) the render never shows content outside `[source_start − 1 frame, source_end + 1 frame]`. **Not promised**: bit-exact decoding across FFmpeg builds. |
| T-09 | **Range validity against media.** With `D` = verified **video-stream duration** from the renderer's own inspection: `source_end ≤ D + range_tolerance`, `range_tolerance = max(1 / source_fps, 0.05 s)`. If `D < source_end ≤ D + tolerance` the render proceeds with warning `SOURCE_END_WITHIN_TOLERANCE`; beyond that → `SOURCE_RANGE_INVALID`. |
| T-10 | **Absolute trimming.** Trims use `video_start_time + source_time` for **both** audio and video so a non-zero container start time never shifts the cut. |

**Examples (test vectors).**

| Case | Derived values |
|---|---|
| 30 fps; durations 4, 4, 4 | `T = 0, 4, 8, 12`; `f = 0, 120, 240`; `n = 120, 120, 120`; `N = 360`; 12.000 s |
| `24000/1001` fps (23.976…); durations 4, 4, 4 | `fps·T = 95.904, 191.808, 287.712` → `f = 96, 192, 288`; `n = 96, 96, 96`; `N = 288`; `N/fps = 12.012 s` (vs 12.000; error 0.012 s ≤ 0.5 frame = 20.8 ms) |
| 30 fps; one segment 0.01 s | `n = F(0.01) = 0` → `SEGMENT_TOO_SHORT` |
| 30 fps; crossfade 1.0 s between two 5.0 s segments | `T = 0, 4.0`; `T_end = 9.0`; `f_1 = 120`; `n_0 = 150`; `m_0 = 0+150−120 = 30`; `n_1 = F(4+5) − 120 = 150`; `N = 270` |

**Output duration tolerances (postconditions; reasons in italics).**

| Quantity | Design target | Postcondition tolerance | Why |
|---|---|---|---|
| Video frame count | exactly `N` | `±1` frame | Segments are trimmed to exact frame counts, so exactness is expected; ±1 absorbs muxer edge cases without hiding real errors |
| Video stream duration | `N/fps` | `±1 / fps` | CFR quantization |
| Audio stream duration (R8) | `N/fps` | `±50 ms` | AAC works in 1024-sample frames (21.3 ms at 48 kHz) plus encoder priming; 50 ms ≈ 2.3 AAC frames |
| Container duration | `N/fps` | `±max(1/fps, 50 ms)` | Container reports the longest stream |

## C.5 Transition semantics (crossfade; implemented in R9)

| Aspect | Rule |
|---|---|
| Adjacency | Only between **adjacent** segments; one per pair |
| Timing | Overlap model (T-01). Total = `Σd − Σx`. Source ranges unchanged; no handles |
| Duration | `0.1 s ≤ x ≤ 3.0 s` (configurable); `x ≤ 0.5·min(d_i, d_{i+1})`; frame-quantized overlap `m ≥ 2`; for any segment `m_in + m_out ≤ n_i − 1` (at least one un-faded frame) |
| Video | Linear dissolve of the last `m` frames of *i* with the first `m` frames of *i+1* |
| Audio | Linear crossfade over the same overlap. A `mute` side contributes silence (fades against silence). Applies only if the output has audio |
| Invalid | Violations → `INVALID_EDIT_PLAN` (structure/constraints); unsupported type or disabled capability → `UNSUPPORTED_OPERATION` |

## C.6 Audio semantics (implemented in R8; R6/R7 outputs are video-only)

| Rule | Behavior |
|---|---|
| A-01 | `output_profile.audio == null` ⇒ the output has **no audio stream**, regardless of source audio. |
| A-02 | Otherwise the output **always** has one audio stream, 48 kHz, stereo AAC, continuous for the whole timeline. |
| A-03 | `audio_mode: "mute"` ⇒ **silence** of exactly the segment's duration. Source audio never leaks through. |
| A-04 | `audio_mode: "source"` ⇒ audio from the asset's **first/default audio stream** over the same source range (T-10). If the asset has **no audio stream** → `SOURCE_AUDIO_MISSING` (permanent). Rationale: silently muting would hide a planner bug (question H-1). |
| A-05 | Differing sample rates/channel layouts are normalized: resample to 48 kHz; mono → stereo duplicate; >2 channels → FFmpeg default stereo downmix; recorded as warnings (`AUDIO_RESAMPLED`, `AUDIO_CHANNELS_REMAPPED`). |
| A-06 | Source audio shorter than the range → pad with silence, warning `AUDIO_SHORTER_THAN_VIDEO`; longer → trimmed. |
| A-07 | Per-segment audio is produced as PCM at **sample-exact length** from cumulative boundaries `a_i = round(f_i/fps · 48000)`; all audio is concatenated and encoded to AAC **once** (no AAC joins; no priming gaps at cuts). |
| A-08 | No gain, normalization, limiting, background music, or parallel mixing in v1.0 (deferred). |

## C.7 Geometry / fit (pure function, implemented in R2)

Inputs: stored width/height, pixel aspect ratio (`Fraction`), rotation (0/90/180/270), output `W×H`, `fit`.

1. Display size: `dw = width·SAR`, `dh = height`; swap if rotation is 90/270 (display orientation is the truth; FFmpeg autorotation is used).
2. **letterbox**: `s = min(W/dw, H/dh)`; `w' = floor_even(dw·s)`, `h' = floor_even(dh·s)`; pad offsets `x = floor_even((W−w')/2)`, `y = floor_even((H−h')/2)`; pad black.
3. **crop**: `s = max(W/dw, H/dh)`; `w' = ceil_even(dw·s)`, `h' = ceil_even(dh·s)`; crop offsets `x = floor_even((w'−W)/2)`, `y = floor_even((h'−H)/2)`.
4. Upscaling is allowed; stretching never.

| Test vector | Result |
|---|---|
| 1920×1080 → 1280×720 letterbox | scaled 1280×720, pad (0,0) |
| 640×360 → 1280×720 letterbox | scaled 1280×720 (2×), pad (0,0) |
| 1080×1920 (portrait) → 1280×720 letterbox | `s = 0.375`; scaled **404×720**; pad x = 438, y = 0 |
| 1080×1920 → 1280×720 crop | `s = 1.185185…`; scaled **1280×2276**; crop x = 0, y = 778 |

## C.8 Normalization allowlist (what "execute deterministically" may do)

Allowed: trim to declared range; autorotate by metadata; apply SAR; scale/pad/crop **per the declared `fit`**; convert frame rate to the profile (drop/duplicate frames only); convert pixel format to `yuv420p`; audio resample/channel mapping/silence per C.6; encode with renderer-configured quality. **Forbidden**: speed changes, time stretching, reordering, extending a segment beyond its range (other than the ≤ tolerance last-frame hold), stretching the picture, color grading, adding or removing content not in the plan.

## C.9 `RenderRequest` v1.0 (application input)

```json
{
  "contract_version": "1.0",
  "render_job_id": "render-001",
  "plan": { "...an EditPlan..." },
  "correlation_id": null
}
```

`render_job_id` and `correlation_id` follow C-03. The plan is **embedded** (so the fingerprint refers to exactly what ran). The request carries **no filesystem paths** for outputs: the renderer owns output location (security). Request validation errors from the plan carry the path prefix `plan.`.

**Idempotency.** `request_hash` = sha256 of the canonical JSON of the validated request excluding `correlation_id`; `plan_fingerprint` = sha256 of the canonical JSON of the plan (sorted keys, decimals as normalized strings, no whitespace, UTF-8). Same `render_job_id` + same hash: completed → stored result returned without re-rendering; previously failed/cancelled → re-run; running → `RENDER_JOB_IN_PROGRESS`. Same id + different hash → `RENDER_JOB_CONFLICT`. Explicit re-render = new `render_job_id`. No distributed exactly-once promise.

## C.10 `RenderResult` v1.0 (output)

| Field | Notes |
|---|---|
| `contract_version`, `render_job_id`, `plan_id` | |
| `status` | `succeeded` \| `failed` \| `cancelled` |
| `output` | `null` unless succeeded. `{ref: {scheme:"file", uri:"<render_job_id>/output.mp4", checksum:"sha256:…"}` (**relative to the configured output root**), `container`, `video_codec`, `audio_codec` (nullable), `duration_seconds`, `width`, `height`, `frame_rate` (`"n/d"`), `frame_count`, `has_video`, `has_audio`, `file_size_bytes}` — all **measured**, not copied from the plan |
| `expected` | `{duration_seconds, duration_fraction, frame_count}` derived by T-03 |
| `timing` | `{started_at, completed_at, elapsed_seconds}` (UTC ISO-8601) |
| `renderer` | `{name, version, ffmpeg_version, ffprobe_version, encoder_settings}` |
| `postconditions` | list of `{check, status: passed\|failed\|skipped, detail}` |
| `warnings` | list of `{code, message, phase, related_ids}` |
| `manifest_ref` | `{scheme:"file", uri:"<render_job_id>/manifest.json", checksum}` |
| `error` | `ErrorInfo` or `null` (set iff status is `failed`/`cancelled`) |

A `failed` or `cancelled` result **never** contains an `output`. Exit status zero from FFmpeg is never sufficient for `succeeded`; postconditions must pass.

## C.11 Render manifest v1.0

Written for every render that passes validation (success **and** failure). Contents:

- `render_job_id`, `plan_id`, `plan_fingerprint`, `request_hash`, `production_id?`, `outcome` (`succeeded|failed|cancelled`), `phase_reached`.
- `profile` (as executed), `renderer` (versions, `encoder_settings`, config digest), `strategy: "normalize_then_assemble"`, `limits_applied`.
- `sources[]`: `asset_id`, `fingerprint`, `size_bytes`, `display_name` (basename only), probed `duration_seconds`, `width`, `height`, `sar`, `rotation_degrees`, `frame_rate`, `frame_rate_mode`, `start_time_seconds`, `has_audio`, audio properties, `container_format`.
- `segments[]`: `segment_id`, `asset_id`, `source_start_seconds`, `source_end_seconds`, derived `timeline_start_seconds`, `timeline_end_seconds`, `frame_start`, `frame_count`, geometry (`scaled`, `pad`/`crop`), `audio_source` (`source`\|`silence`), `measured_frame_count` of the intermediate, warnings.
- `transitions[]` (R9), `postconditions[]`, `warnings[]`, `error?`.
- `commands[]`: **sanitized** invocation templates (paths replaced by tokens like `{asset:asset-a}` and `{workspace}/seg-001.mkv`), exit codes, elapsed seconds.
- **No** absolute paths, no secrets, no raw stderr beyond a capped, sanitized tail inside `error.details`.

## C.12 Structured errors

`ErrorInfo = {code, message, retryable, phase, details}`; `phase ∈ validate|resolve|inspect|plan|normalize|assemble|verify|finalize`. `details` is sanitized and size-capped.

| Code | Retryable | Notes |
|---|---|---|
| `UNSUPPORTED_CONTRACT_VERSION` | no | |
| `INVALID_EDIT_PLAN` | no | `details.violations[]` |
| `UNSUPPORTED_OPERATION` | no | `details.unsupported[]` incl. what **is** supported |
| `RESOURCE_LIMIT_EXCEEDED` | no | plan or media limits |
| `RENDER_JOB_CONFLICT` / `RENDER_JOB_IN_PROGRESS` | no | |
| `ASSET_NOT_FOUND` | no | |
| `ASSET_ACCESS_DENIED` | no | outside allowed roots, permissions |
| `ASSET_CHECKSUM_MISMATCH` | no | |
| `SOURCE_MEDIA_INVALID` | no | `details.reason ∈ corrupt\|unsupported_codec\|unsupported_container\|no_video_stream\|not_video` |
| `SOURCE_RANGE_INVALID` | no | range outside verified duration (T-09) |
| `SOURCE_AUDIO_MISSING` | no | A-04 |
| `FFMPEG_NOT_FOUND` | no | configuration |
| `FFMPEG_FAILED` | no (orchestrator may decide) | `details`: phase, segment_id?, exit_code, sanitized stderr tail |
| `RENDER_TIMEOUT` | **yes** | |
| `INSUFFICIENT_STORAGE` | **yes** | |
| `OUTPUT_ARTIFACT_INVALID` | no | missing/unreadable output or failed postcondition |
| `PERSISTENCE_FAILED` | **yes** | job record or manifest write failed |
| `RENDER_CANCELLED` | no | accompanies status `cancelled` |
| `INTERNAL_ERROR` | no | |

## C.13 Examples

**Valid plan (the spec's A 2–6, B 4–8, C 1–5 example, corrected):**

```json
{
  "contract_version": "1.0",
  "plan_id": "plan-example-001",
  "production_id": "production-example-001",
  "assets": [
    {"asset_id": "asset-a", "asset_ref": {"scheme": "file", "uri": "clip_a_8s_640x360_24.mp4", "checksum": null}},
    {"asset_id": "asset-b", "asset_ref": {"scheme": "file", "uri": "clip_b_8s_640x360_24.mp4", "checksum": null}},
    {"asset_id": "asset-c", "asset_ref": {"scheme": "file", "uri": "clip_c_8s_640x360_24.mp4", "checksum": null}}
  ],
  "output_profile": {"name": "mp4-h264-720p30", "container": "mp4", "video_codec": "h264",
                     "width": 1280, "height": 720, "fps": "30", "fit": "letterbox", "audio": null},
  "timeline": {
    "segments": [
      {"segment_id": "segment-001", "asset_id": "asset-a", "source_start_seconds": 2.0, "source_end_seconds": 6.0, "audio_mode": "mute"},
      {"segment_id": "segment-002", "asset_id": "asset-b", "source_start_seconds": 4.0, "source_end_seconds": 8.0, "audio_mode": "mute"},
      {"segment_id": "segment-003", "asset_id": "asset-c", "source_start_seconds": 1.0, "source_end_seconds": 5.0, "audio_mode": "mute"}
    ],
    "transitions": []
  },
  "expected_duration_seconds": 12.0
}
```

*(Compared with the spec's example: `timeline_start_seconds` and `timeline.duration_seconds` removed (K-2), `assets` added (K-3), `audio_codec`/`container` regrouped, `fit` made explicit, `audio: null` because audio is enabled in R8.)*

**Plan with audio (valid from R8):** same plan with `"audio": {"codec": "aac", "sample_rate": 48000, "channels": 2}` and `segment-001` `"audio_mode": "source"`.

**Invalid plan (each reported with rule IDs):** `source_end_seconds` ≤ start → `PR-08`; unknown `asset_id` → `PR-06`; `audio` null with `audio_mode: "source"` → `PR-10`; `"fps": 29.97` (float) → `PR-09`; transition `{"type":"wipe"}` → `UNSUPPORTED_OPERATION` (`PR-12`).

**Succeeded result (abridged):**

```json
{
  "contract_version": "1.0", "render_job_id": "render-001", "plan_id": "plan-example-001", "status": "succeeded",
  "output": {"ref": {"scheme": "file", "uri": "render-001/output.mp4", "checksum": "sha256:<64 hex>"},
             "container": "mp4", "video_codec": "h264", "audio_codec": null,
             "duration_seconds": 12.0, "width": 1280, "height": 720, "frame_rate": "30",
             "frame_count": 360, "has_video": true, "has_audio": false, "file_size_bytes": 2048000},
  "expected": {"duration_seconds": 12.0, "duration_fraction": "12/1", "frame_count": 360},
  "timing": {"started_at": "2026-10-12T10:00:00Z", "completed_at": "2026-10-12T10:00:09Z", "elapsed_seconds": 9.2},
  "renderer": {"name": "scene_signal.render", "version": "0.1.0", "ffmpeg_version": "x.y", "ffprobe_version": "x.y",
               "encoder_settings": {"video": {"encoder": "libx264", "preset": "medium", "crf": 20, "pix_fmt": "yuv420p"}}},
  "postconditions": [{"check": "frame_count", "status": "passed", "detail": "360 == 360"}],
  "warnings": [], "manifest_ref": {"scheme": "file", "uri": "render-001/manifest.json", "checksum": "sha256:<64 hex>"},
  "error": null
}
```

**Failed result (abridged):** `status: "failed"`, `output: null`, `error: {"code": "SOURCE_RANGE_INVALID", "message": "segment-002 ends at 8.0 s but asset-b is 7.5 s long", "retryable": false, "phase": "inspect", "details": {"segment_id": "segment-002", "asset_id": "asset-b", "verified_duration_seconds": 7.5}}`.

## C.14 Deferred (deliberate, recorded)

Still-image segments (need explicit duration); gaps/black fillers; overlaps and multiple tracks; background music, volume/gain, ducking; additional transitions; text/graphics; speed changes; hardware encoders; non-`file` storage backends; HDR / >8-bit; loudness normalization; subtitles/chapters; resumable renders; parallel segment normalization; a stream-copy concat fast path and a single-process fast path (optimizations once correctness is proven); multiple outputs per plan; contract 1.1 additions (`audio_tracks`, segment `kind`).

---

# PART D — Architecture and file layout

## D.1 📎 SHARED — Layout (inside the existing `SceneSignal/`; created incrementally, no empty folders)

```
SceneSignal/
├── GEMINI.md                     # (existing) gets a short Module 02 registry entry
├── scripts/make_render_fixtures.py
├── src/scene_signal/
│   ├── ... (Module 01 packages: UNTOUCHED)
│   └── render/                   # Module 02
│       ├── __init__.py, __main__.py, cli.py
│       ├── contracts/            # edit_plan.py, render_request.py, render_result.py, manifest.py,
│       │                         # error_info.py, common.py, versions.py, loading.py, canonical.py, export.py
│       ├── domain/               # errors.py, capabilities.py, plan_validation.py, timing.py, geometry.py,
│       │                         # timeline_rules.py, postconditions.py, execution_plan.py, policies.py
│       ├── ports/                # asset_resolver.py, media_inspector.py, render_engine.py,
│       │                         # workspace.py, repository.py, progress.py, cancellation.py, clock.py
│       ├── application/          # render_service.py, manifest_builder.py, lifecycle.py
│       └── adapters/
│           ├── ffmpeg/           # binaries.py, runner.py, inspector.py, command_builder.py,
│           │                     # engine.py, progress_parser.py
│           ├── storage/          # local_assets.py, local_workspace.py, local_repository.py
│           └── fakes/            # fake_assets.py, fake_inspector.py, fake_engine.py
├── tests/render/{unit,contract,integration,helpers,fixtures}/
└── docs/render/                  # SPEC-02-timeline-render.md, architecture.md, edit-plan-contract.md,
                                  # render-result-contract.md, timing.md, ffmpeg-security.md, testing.md,
                                  # decisions.md, handoff.md, integration-boundary.md, acceptance.md,
                                  # examples/plans/*.json, schemas/*.json
```

**Naming guard:** no file in the tree may be named like a stdlib module (`time.py`, `types.py`, `queue.py`, `profile.py`, `parser.py`, `signal.py`, `logging.py`, …). That is why the files are `timing.py`, `output profile` lives in `edit_plan.py`, etc. Module 01's architecture test (`sys.stdlib_module_names`) scans the whole package and will catch violations.

## D.2 📎 SHARED — Dependency rules (enforced by an architecture test in R1)

| Package | May import |
|---|---|
| `render.contracts` | pydantic, stdlib |
| `render.domain` | `render.contracts`, stdlib (**no** `subprocess`, no FFmpeg strings) |
| `render.ports` | `render.domain`, `render.contracts`, stdlib |
| `render.application` | `render.ports`, `render.domain`, `render.contracts`, stdlib (**no** `subprocess`) |
| `render.adapters.*` | ports, domain, contracts, stdlib, their own libraries |
| `render.cli` | application, adapters |
| **Cross-module** | `scene_signal.render` imports **nothing** from Module 01 (`scene_signal.domain/schemas/ports/application/adapters/config/api/cli`), and Module 01 imports nothing from `scene_signal.render` |
| **Everywhere** | no `shell=True`, no absolute paths hard-coded, no generation-application imports |

## D.3 📎 SHARED — Execution strategy decision: `normalize_then_assemble`

| Option | Pros | Cons |
|---|---|---|
| One FFmpeg process for everything | No temp files; one generation of encoding; fastest | Huge filter graph with many inputs; failures hard to localize; per-segment timing cannot be verified in isolation; every feature touches one fragile command |
| Per-segment intermediates, then concatenate | Failures localized to a segment; **each segment's frame count and format can be verified**; assembly graph is trivial because every input is identical; crossfade and audio assembly are simple on uniform streams | Temporary disk; an extra encode generation |
| **Hybrid (chosen)** | Phase 1 normalizes each segment to an intermediate and **verifies it**; Phase 2 assembles the verified intermediates and encodes once to the final profile | Same costs as option 2, mitigated below |

**Why it fits this project:** timing correctness is the central requirement. Verifying every segment (exact frame count, dimensions, frame rate, pixel format) catches an off-by-one **before** assembly and tells you *which segment* failed. Intermediates are near-lossless (default `libx264 -crf 12`, configurable) so the extra generation is visually negligible; assembly re-encodes through the concat demuxer for robustness instead of risking stream-copy joins (H.264 parameter-set and timestamp pitfalls). Audio is built as sample-exact PCM per segment and encoded to AAC **once** (A-07). The engine-neutral `RenderExecutionPlan` keeps single-process and stream-copy fast paths available later (C.14).

## D.4 📎 SHARED — Normalization reference chain (guidance; Gemini must verify on the installed FFmpeg)

Per segment, video: select by **absolute** timestamps (`start = video_start_time + source_start`), reset timestamps, convert to the profile fps, scale to the computed geometry (C.7), pad/crop, set SAR 1, `yuv420p`, then limit to exactly `n_i` frames (hold the last frame if short within tolerance). Audio (R8): trim by the same absolute times, resample to 48 kHz stereo PCM, then pad/trim to exactly `a_{i+1} − a_i` samples. **Acceptance for this chain is empirical**: measured frame count must equal `n_i` for every fixture; if not, report instead of adding workarounds.

## D.5 📎 SHARED — FFmpeg safety design

| Measure | Detail |
|---|---|
| No plan string reaches FFmpeg | Only validated numbers (formatted by code with fixed formats; `fps` as `n/d`) and **resolver-produced paths** enter the command |
| Argument lists only | `subprocess` with `shell=False`; `-nostdin`; `-n` (never overwrite) |
| Inputs | Passed as `file:<absolute path>`; `-protocol_whitelist file` (and `pipe` only if used); concat list lives in the workspace with relative names and the default safe mode |
| Demuxer allowlist | Before rendering, ffprobe `format_name` must be in the supported set (`mov,mp4,m4a,3gp,3g2,mj2`; `matroska,webm`); anything else (HLS, concat/ffconcat text, image sequences, `lavfi`) → `SOURCE_MEDIA_INVALID(reason=unsupported_container)`. Where the installed FFmpeg supports it, also pass a format whitelist so probing and decoding cannot open other demuxers |
| Path control | Resolver canonicalizes (`realpath`), requires an allowed root, rejects assets inside the work/output roots; file names starting with `-` are neutralized by absolute paths |
| Output control | Written to `*.partial` in the workspace, verified, then atomically moved; `result.json` is the only success marker |
| Logging | Command templates sanitized; stderr tail capped and sanitized; no secrets (there are none) |

## D.6 📎 SHARED — Lifecycle, ownership and persistence (answers spec §13)

| Question | Decision |
|---|---|
| Who creates working directories | `WorkspacePort` (local: `<work_root>/<render_job_id>.<random>/`), created by `RenderService` when normalization starts |
| Where final artifacts go | `<data_root>/renders/<render_job_id>/` containing `output.mp4`, `manifest.json`, `result.json`, `status.json`, `request.json` |
| Who cleans intermediates | The renderer: workspace removed on success, failure **and** cancellation (`keep_workspace_on_failure` is a debug option, default off); stale workspaces removed by a janitor command (R10) |
| Source immutability | Sources opened read-only; never copied into or processed inside the source folder; checksum verified when supplied |
| Registration | The renderer returns `RenderResult` and writes the files; the Orchestrator/Persistence module registers the artifact |
| Status recovery | `status.json` (`pending/running/succeeded/failed/cancelled` + phase) and `result.json`; `get_status` / `get_result` by `render_job_id` |
| Partial files | Never named `output.mp4` until verified; absence of `result.json` means not successful |
| Database | None required |

**Configuration (env prefix `SCENE_SIGNAL_RENDER_`, documented in `.env.example`; no secrets):** `ASSET_ROOTS`, `DATA_ROOT`, `WORK_ROOT`, `FFMPEG_PATH`, `FFPROBE_PATH`, `RENDER_TIMEOUT_SECONDS` (default 1800), per-phase timeouts, `MAX_CONCURRENT_RENDERS` (default 1), `KEEP_WORKSPACE_ON_FAILURE`, `VERIFY_CHECKSUMS` (default true), limits from C.3, encoder settings (`CRF` 20, `PRESET` medium, intermediate `CRF` 12).

---

# PART E — Implementation chunks

Chunks are **R1 … R11**. Mapping to the spec's initial eight: spec C1 → R1 (+R2); spec C2 → R5 (+R3, R4); spec C3 → R6; spec C4 → R7; spec C5 → R8; spec C6 → R9; spec C7 → R10; spec C8 → R11.

## E.0 🧑 FOR YOU — Overview

| Chunk | Title | Depends on | Size | Manual test |
|---|---|---|---|---|
| R1 | Scaffold, contracts, capabilities, plan validation | Module 01 Chunk 0 | M | Yes: validate JSON plans |
| R2 | Timing and geometry kernel (pure) | R1 | M | Yes: derived timelines, geometry |
| R3 | Ports, fakes, render service, manifest builder | R2 | L | Yes: fake-engine demo |
| R4 | Local storage adapters: assets, workspace, job repository | R3 | M | Yes: asset check, idempotency |
| R5 | FFmpeg foundation: discovery, safe runner, inspector, fixtures | R4 | L | **Yes**: `doctor`, `inspect-source` |
| R6 | First real render: hard cuts, video-only | R5 | L | **Yes: watch real videos** |
| R7 | Output verification, timing tolerance, edge-case timing | R6 | M | **Yes**: `verify-output` |
| R8 | Audio behavior | R7 | L | **Yes: listen** |
| R9 | Crossfade transition | R8 | M | **Yes: watch** |
| R10 | Operational hardening | R9 | L | **Yes**: cancel, timeout, cleanup |
| R11 | Integration boundary docs, CLI finalize, acceptance | R10 | M | **Yes**: full smoke |

### 🧑 FOR YOU — Common setup (always inside `SceneSignal/`, virtualenv active)

```
cd <PARENT_DIR>/SceneSignal        # Windows: cd <PARENT_DIR>\SceneSignal
pip install -e ".[dev]"
pytest -q                          # whole suite: Module 01 tests must stay green too
```

### 🧑 FOR YOU — The test media (from R5) and how to read it

`python scripts/make_render_fixtures.py` creates tiny synthetic clips in `tests/render/fixtures/media/` (git-ignored). Every clip is designed so you can **see** what the renderer did:

- Each clip has a **fixed background color** identifying the clip.
- Each source second *k* (0-based) shows **k+1 white squares** in a row. So source second 0 = 1 square, second 5 = 6 squares.
- Each audio-bearing clip has a **fixed tone** (A 440 Hz, B 660 Hz, C 880 Hz).

| File | Background | Size / fps | Tone | Purpose |
|---|---|---|---|---|
| `clip_a_8s_640x360_24.mp4` | red | 640×360 @24 | 440 Hz | main clip A |
| `clip_b_8s_640x360_24.mp4` | green | 640×360 @24 | 660 Hz | main clip B |
| `clip_c_8s_640x360_24.mp4` | blue | 640×360 @24 | 880 Hz | main clip C |
| `clip_portrait_6s_360x640_30.mp4` | yellow | 360×640 @30 | 440 Hz | portrait |
| `clip_wide_6s_1280x720_30.mp4` | purple | 1280×720 @30 | 440 Hz | mixed resolution |
| `clip_ntsc_6s_480x270_2997.mp4` | orange | 480×270 @30000/1001 | 440 Hz | fractional fps |
| `clip_noaudio_6s_640x360_24.mp4` | cyan | 640×360 @24 | none | no audio |
| `clip_mono22k_6s_640x360_24.mp4` | magenta | 640×360 @24 | 440 Hz mono 22.05 kHz | audio mismatch |
| `clip_offset_6s_640x360_24.mp4` | gray | 640×360 @24, container start time 1.5 s | 440 Hz | non-zero start |
| `clip_rotated_6s.mp4` | white | stored 640×360 + 90° rotation metadata | 440 Hz | rotation (best effort) |
| `clip_sar_6s.mp4` | pink | non-square pixels | 440 Hz | pixel aspect ratio |
| `clip_vfr_6s.mp4` | teal | variable frame rate | 440 Hz | VFR (best effort) |
| `bad_truncated.mp4`, `bad_zero.mp4`, `bad_not_video.mp4`, `bad_still.png`, `bad_audio_only.m4a`, `bad_playlist.mp4` | — | — | — | failure and security cases |

**Expected view for the spec's example plan (A 2–6, B 4–8, C 1–5, 30 fps, 12 s):** seconds 0–4 **red** with **3, 4, 5, 6** squares (one count per second); seconds 4–8 **green** with **5, 6, 7, 8** squares; seconds 8–12 **blue** with **2, 3, 4, 5** squares.

---

## Chunk R1 — Scaffold, contracts, capabilities, plan validation

### 🤖 FOR GEMINI — Spec

**Objective:** create the `render` sub-package skeleton for the code that exists in this chunk, freeze the contracts in C.1–C.13 as Pydantic models, implement strict loading and plan validation (PR-01…PR-13), `RendererCapabilities`, typed errors, JSON-Schema export, and the CLI `validate-plan` / `capabilities` / `export-schemas`.

**Preconditions (check first, STOP and report if false):** working directory is the `SceneSignal` root (contains `pyproject.toml` with distribution `scene-signal` and `src/scene_signal/`); the baseline `pytest -q` passes (record the exact result); Module 01 files are read-only for you.

**Files likely created** (under `src/scene_signal/render/`): `__init__.py`, `__main__.py`, `cli.py`; `contracts/{common,edit_plan,render_request,render_result,manifest,error_info,versions,loading,canonical,export}.py`; `domain/{errors,capabilities,plan_validation}.py`. Tests under `tests/render/unit/`. Docs under `docs/render/` (`architecture.md`, `edit-plan-contract.md`, `render-result-contract.md`, `timing.md` (semantics from C.4 marked "implemented in R2"), `testing.md`, `decisions.md`, `handoff.md`), `docs/render/examples/plans/` (valid and invalid examples, one invalid file per rule, named `invalid_<rule>_*.json`), `docs/render/schemas/`. Registry entries in `GEMINI.md` (and `AI_RULES.md` / `SESSION_BOOT.md` **only if they exist**). `.env.example` gets documented `SCENE_SIGNAL_RENDER_*` names that exist so far (none required).

**Implement exactly**
- Strict loader (K-10): reject `NaN`/`Infinity`, duplicate keys, trailing data, > 1 MiB; decimals parsed as `Decimal`; float snap rule; booleans never accepted as numbers.
- Models per C.2, C.9, C.10, C.11, C.12 (`ErrorInfo`, enum of codes). `fps` as an exact `Fraction` accepting int or `"n/d"`, serialized canonically (`"30"`, `"30000/1001"`); floats rejected.
- `RenderError` hierarchy with `code`, `message`, `retryable`, `phase`, `details`.
- `RendererCapabilities` exactly as the "After R1" column of C.3, plus a test that pins it.
- `validate_edit_plan(raw, capabilities=...) -> EditPlan` implementing PR-01…PR-13 in the stated precedence, collecting all violations per stage; `validate_render_request(raw)` (plan errors prefixed `plan.`).
- `canonical_json`, `plan_fingerprint`, `request_hash` (C.9).
- Architecture test `tests/render/unit/test_architecture_render.py` implementing D.2 (including the two cross-module directions and the `shell=True` grep). Self-test with temporary fake packages.

**Out of scope:** timing/frame math (R2), any I/O beyond reading the plan file, FFmpeg, services, storage.

**Tests to write FIRST** (show the red run)
- Loader: NaN, Infinity, duplicate key, trailing garbage, oversize, non-UTF-8, decimals with 7 places, float 0.1 accepted, float 0.30000000000000004 snapped, float 0.1234567 rejected, `true` as seconds rejected, string seconds rejected.
- Versions: `"1.0"` ok; `"2.0"`, `"1.1"`, `"abc"` handled per C-02.
- One test **per rule PR-01…PR-13** using the invalid examples (each asserts error code, rule ID and JSON path), including: unknown field, bad id (`../x`), duplicate segment/asset/transition ids, unknown asset reference, unused asset warning, `end <= start`, negative start, odd width, float fps, `audio` null with `source`, crossfade with non-adjacent segments, duplicate pair, unknown transition type (→ unsupported), crossfade (→ unsupported until R9), `audio_mode: "source"` (→ unsupported until R8), non-`file` scheme, codec `h265`, fps `29.97` string `"2997/100"` (not on allowlist → unsupported), over-limit segment count, over-limit duration.
- Precedence: a plan with both a structural error and an unsupported operation reports only the structural error first; all structural errors are collected together.
- Valid plans: the spec example, single clip, `crop`, fractional fps `"30000/1001"`, optional fields omitted.
- `RenderRequest`: `plan.` path prefixing; request hash excludes `correlation_id`; fingerprint stable under key order and decimal formatting (`2.0` vs `2.00`).
- Capabilities equal the C.3 table; snapshot test.
- Models: `extra=forbid`; round trip; JSON Schema export deterministic and every valid example validates against the exported schema (`jsonschema`).
- Architecture test self-tests.

**Acceptance criteria:** all PR rules covered by tests that fail without the implementation; all examples behave as labeled; CLI works; baseline Module 01 tests unchanged and green; docs updated; nothing outside the SceneSignal root touched.

**Completion evidence:** red run, final full `pytest -q`, CLI transcript, list of changed files, `docs/render/handoff.md` showing "Next chunk: R2".

### 🧑 FOR YOU — Review and manual test

1. `pytest -q` → green (Module 01 count plus many new render tests; the count is not important, **no failures**).
2. `python -m scene_signal.render capabilities` → shows containers `["mp4"]`, codecs `["h264"]`, `audio_codecs: []`, `audio_modes: ["mute"]`, `transition_types: []`, `features.render_engine: false`.
3. `python -m scene_signal.render validate-plan docs/render/examples/plans/three_clips.video_only.json` → `OK`.
4. Run each `docs/render/examples/plans/invalid_*.json` → a JSON error with the right **rule ID** and path (e.g. `PR-08` for end ≤ start; `PR-10` for audio contradiction). Each exit code non-zero.
5. `.../validate-plan docs/render/examples/plans/three_clips.with_audio.json` → `UNSUPPORTED_OPERATION` (audio comes in R8) with a `supported` list. **This is correct.**
6. **Your own edits** (copy a plan and change it): `"source_end_seconds": 1.5` where start is 2.0 → PR-08; `"fps": 29.97` → PR-09; add `"wipe"` transition → unsupported; add a stray field `"foo": 1` → PR-03; set `"width": 1281` → PR-09.
7. `python -m scene_signal.render export-schemas --out docs/render/schemas` twice → identical files.
8. Read `docs/render/edit-plan-contract.md`: could a planner author write a valid plan from it alone? Tell me what is unclear.
9. `git status` → only new/changed files inside `SceneSignal/`; the generation app is untouched.

---

## Chunk R2 — Timing and geometry kernel (pure)

### 🤖 FOR GEMINI — Spec

**Objective:** implement T-01…T-06 and C.7 as pure, exact functions. No I/O, no FFmpeg.

**Files:** `render/domain/{timing,geometry,timeline_rules,policies}.py`; tests `tests/render/unit/{test_timing,test_geometry,test_timeline_rules}.py`; CLI `timeline PLAN.json [--json]` and `geometry --src WxH [--sar n:d] [--rotation 0|90|180|270] --out WxH --fit letterbox|crop`; docs `timing.md` finalized with all examples; update `validate_edit_plan` to run PR-14 (T-04, T-05, T-06) after PR-13.

**Implement**
- `Fps` (exact `Fraction`), `frame_index(t, fps)` = `floor(t·fps + 1/2)` using `Fraction` only (no floats anywhere).
- `derive_timeline(plan) -> DerivedTimeline` with segments (`index, id, source_start, source_end, duration, timeline_start, timeline_end, frame_start, frame_count`), overlaps `m_i`, `total_frames`, `expected_duration` (Fraction + 6-decimal decimal). Fully implement the **transition-aware** formulas (x ≥ 0) even though transitions stay unsupported.
- `compute_fit(...)` per C.7 including `floor_even`/`ceil_even`, SAR and rotation.
- Timeline rules T-04/T-05/T-06 raising `INVALID_EDIT_PLAN` with `SEGMENT_TOO_SHORT`, `PLAN_DURATION_MISMATCH`, or `RESOURCE_LIMIT_EXCEEDED`.

**Tests FIRST:** every example in C.4 and C.7 exactly; cumulative-rounding bound (`|N/fps − (Σd − Σx)| ≤ 0.5/fps`, `Σ n_i − Σ m_i = N`, all `n_i ≥ 1`) over a **seeded, deterministic** sweep of at least 500 random plans across the whole fps allowlist; round-half-up tie cases using a generic `Fps` (e.g. 2 fps, `t = 0.25` → 1 not 0); crossfade vector (30 fps, 5+5 with 1.0 s → `N = 270`, `m = 30`); `expected_duration_seconds` accepted within one frame and rejected beyond; segment 0.01 s at 30 fps rejected; timeline over 600 s rejected; geometry vectors, symmetric padding, crop covering the target, always even, never exceeding or under-covering; SAR 16:15 and rotation 90 cases; no `float` used (a test that scans the module source for `float(` and `/` on non-Fraction values is **not** required, but inputs and outputs must be `Fraction`/`Decimal`/`int`).

**Acceptance:** exact vectors pass; sweep passes; CLI output matches the vectors; no regressions.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal.render timeline docs/render/examples/plans/three_clips.video_only.json` → a table: segments with timeline start/end `0–4`, `4–8`, `8–12`; frames `0–120`, `120–240`, `240–360`; total **360 frames = 12.0 s**.
2. `... timeline docs/render/examples/plans/fractional_fps_three_clips.json` (30000/1001 fps, three 4 s segments) → frames **96, 96, 96**, total **288**, duration **12.012 s** (explained as 0.012 s above 12.0, within half a frame).
3. `... geometry --src 1080x1920 --out 1280x720 --fit letterbox` → scaled **404×720**, pad **438,0**. With `--fit crop` → scaled **1280×2276**, crop **0,778**.
4. `... geometry --src 640x360 --out 1280x720 --fit letterbox` → scaled 1280×720, no padding.
5. `... timeline docs/render/examples/plans/invalid_segment_too_short.json` → `SEGMENT_TOO_SHORT`. Edit the three-clip plan to say `"expected_duration_seconds": 11.0` → `PLAN_DURATION_MISMATCH`.
6. Sanity-check the math yourself for the first example: do the numbers match what you expect?

---

## Chunk R3 — Ports, fakes, render service, manifest builder

### 🤖 FOR GEMINI — Spec

**Objective:** implement the whole render **lifecycle** against fakes, with no FFmpeg and no disk adapters beyond a temp directory in tests.

**Files:** `render/ports/*` (asset resolver, media inspector, render engine, workspace, repository, progress, cancellation, clock); `render/domain/{execution_plan,postconditions?}` (engine-neutral `RenderExecutionPlan`: per-segment normalization spec with geometry, frame counts, source times as `Fraction`; assemble spec; profile; audio spec reserved); `render/application/{render_service,manifest_builder,lifecycle}.py`; `render/adapters/fakes/*`; CLI `demo-fake PLAN.json --out DIR`; tests `tests/render/unit/test_render_service*.py`, `test_manifest_builder.py`.

**Ports (signatures in prose):** `AssetResolverPort.resolve(asset)`→resolved asset (opaque handle with `local_path()` context, fingerprint, size); `MediaInspectorPort.inspect(path)`→`SourceMediaInfo` (verified video duration, start time, stored size, SAR, rotation, frame rate and mode, has_audio and audio properties, container format name, codecs, stream counts); `RenderEnginePort.render(execution_plan, workspace, progress, cancel_token)`→`EngineResult` (output path and engine notes); `WorkspacePort`; `RenderRepositoryPort` (claim job with request hash, update status, save request/result/manifest, load status/result); `ProgressReporterPort.report(phase, fraction, message)`; `CancellationToken` (is_cancelled/raise_if_cancelled); `Clock`.

**Service flow (`RenderService.render(request) -> RenderResult`):** validate request/plan (R1+R2) → claim job (idempotency per C.9) → resolve assets (+checksums when supplied) → inspect sources → validate source ranges (T-09), audio availability (A-04), source container/codec support → derive timeline + build `RenderExecutionPlan` → create workspace → `engine.render` → inspect output → postconditions (stub that always passes until R7 defines them; clearly marked) → build manifest → persist result → cleanup workspace → return. Any typed error → failed result with failure manifest (only if the plan passed validation). Cancellation checked between phases. Progress phases and weights as in D (validate 2%, resolve/inspect 8%, normalize 60%, assemble 25%, verify 5%).

**Tests FIRST:** success path (fake engine) builds a result and manifest with all required fields; **ordering**: engine call count is 0 when validation, resolution, inspection or range checks fail (assert via spies); every error code in C.12 reachable via a fake and mapped to the right `ErrorInfo` (`retryable`, `phase`); idempotency matrix (same id+hash completed → stored result, engine not called; failed → re-run; running → `RENDER_JOB_IN_PROGRESS`; different hash → conflict); cancellation before and during the fake engine → status `cancelled`, workspace cleaned, no output; failed result never has an output; manifest has no absolute paths and no secrets (scan the serialized manifest for the temp directory path); progress monotonic and ends at 1.0; `SOURCE_END_WITHIN_TOLERANCE` warning case; `SOURCE_RANGE_INVALID` case; `SOURCE_AUDIO_MISSING` (using a fake inspector with `has_audio=false` and a plan that requests `source` — validation of this rule here uses a test-only capability override since audio is gated); determinism: same inputs ⇒ identical execution plan and manifest (except timestamps).

**Acceptance:** lifecycle fully tested with fakes; domain/application do not import `subprocess`; architecture test green.

### 🧑 FOR YOU — Review and manual test

1. `pytest tests/render -q` → green.
2. `python -m scene_signal.render demo-fake docs/render/examples/plans/three_clips.video_only.json --out out_fake` (this uses fake adapters with **invented** metadata; it exists only to show the lifecycle). Open the files it wrote: `request.json`, `status.json` (`succeeded`), `result.json`, `manifest.json`, and a placeholder `output.mp4` (not a real video).
3. In `manifest.json` check: segments show derived timeline times and frame counts from R2; **no absolute paths**; commands are sanitized templates.
4. Run `demo-fake` again with the same plan and job id → it reports the stored result (idempotent). Run with the same job id but a changed plan → `RENDER_JOB_CONFLICT`.
5. `python -m scene_signal.render demo-fake docs/render/examples/plans/invalid_end_before_start.json --out out_fake2` → fails at **validate**; no manifest, no workspace left.

---

## Chunk R4 — Local storage adapters: assets, workspace, job repository

### 🤖 FOR GEMINI — Spec

**Objective:** real local implementations of `AssetResolverPort`, `WorkspacePort`, `RenderRepositoryPort`.

**Files:** `render/adapters/storage/{local_assets,local_workspace,local_repository}.py`; tests unit + `tests/render/contract/` (shared port contract suites run against fake and local); CLI `check-assets PLAN.json --assets-root DIR` and `render --engine fake` (fake engine/inspector with real local storage).

**Implement**
- Local resolver: scheme `file` only; allowed roots from settings; relative URIs resolved against the first allowed root; `realpath` + containment; reject symlink escapes, assets inside work/output roots, directories, and special files; size limit; supplied checksum **always verified** (streaming sha256) when `VERIFY_CHECKSUMS`; errors `ASSET_NOT_FOUND`, `ASSET_ACCESS_DENIED`, `ASSET_CHECKSUM_MISMATCH`, `RESOURCE_LIMIT_EXCEEDED`; unsupported scheme → `UNSUPPORTED_OPERATION`.
- Local workspace: `<work_root>/<render_job_id>.<random>/`, context manager, removes everything on success/failure/cancel unless `keep_workspace_on_failure`.
- Local repository per D.6: atomic writes (temp + rename), atomic claim via exclusive directory creation, valid status transitions, request-hash idempotency per C.9, crash-safe (no half-written `result.json`).

**Tests FIRST:** traversal (`../`), absolute path outside roots, symlink escape (skip where unsupported, with reason), asset inside work/output root, directory, missing, unreadable (skip where impossible), checksum correct/wrong, fingerprint equals `hashlib`, **source bytes and mtime unchanged**; workspace creation/cleanup on normal exit and exception, keep-on-failure; repository round trip, simulated crash between temp write and rename leaves no corrupt result, two threads claiming the same id → exactly one winner, status transition rules, idempotency matrix on disk; shared contract suites for fake vs local.

**Acceptance:** contract suites pass for both; no secrets or absolute paths in persisted files except `request.json` (documented as local).

### 🧑 FOR YOU — Review and manual test

1. `pytest tests/render -q` → green.
2. Put any small file `x.mp4` (any content) in a folder, e.g. `tests/render/fixtures/media/`; run `python -m scene_signal.render check-assets docs/render/examples/plans/three_clips.video_only.json --assets-root tests/render/fixtures/media`. Before R5 you do not have the real fixtures, so for this step create three dummy files with the three asset names; expect each asset listed with size and a `sha256:` fingerprint. Remove one → `ASSET_NOT_FOUND`.
3. Set a wrong checksum in a copy of the plan → `ASSET_CHECKSUM_MISMATCH`. Use `"uri": "../outside.mp4"` → `ASSET_ACCESS_DENIED`.
4. `render --engine fake ... --data-root ./.scene_signal/render` twice with the same job id → second run served from storage; check the job folder under `.scene_signal/render/renders/<id>/`.
5. After every run, the work folder (`.scene_signal/work`) is empty.
6. Confirm your dummy source files are unchanged (size/date).

---

## Chunk R5 — FFmpeg foundation: discovery, safe runner, inspector, fixtures

### 🤖 FOR GEMINI — Spec

**Objective:** safe process execution and source inspection through FFmpeg tools, plus synthetic fixtures. No rendering yet.

**Files:** `render/adapters/ffmpeg/{binaries,runner,inspector,progress_parser}.py`; `scripts/make_render_fixtures.py`; `tests/render/fixtures/manifest.json`; `tests/render/helpers/` (frame/marker decoding helpers used later); CLI `doctor`, `inspect-source FILE`; docs `ffmpeg-security.md`, `testing.md`.

**Implement**
- Binary discovery: configured path or PATH; version parsing; verify `libx264` present (and report `aac`, `xfade`, `acrossfade` availability); `FFMPEG_NOT_FOUND` with an actionable message.
- `runner.run(args, timeout, cancel_token, cwd, line_callback, stderr_tail_bytes)`: `shell=False`, argument list only, `-nostdin` enforced by callers' builders, bounded stdout/stderr capture, **timeout kills the whole process tree** (POSIX: new session + `killpg`; Windows: new process group + tree kill), cancellation kills likewise, returns exit code, elapsed time, capped stderr tail; secrets/paths sanitized in anything surfaced.
- Progress parser for `-progress pipe:1` key/value output.
- `FfprobeInspector` implementing `MediaInspectorPort`: content-based format check against the demuxer allowlist (D.5); video stream selection (default disposition, else first; attached pictures excluded); verified duration (video stream, container fallback); **start time** (video origin); stored dimensions, SAR, rotation (sign-normalized clockwise), frame rate with VFR classification (sorted packet timestamps), audio presence/rate/channels; still images and audio-only rejected; typed errors `SOURCE_MEDIA_INVALID(reason)`, `FFMPEG_NOT_FOUND`; probe timeout.
- Fixture script: generates the table in section E.0 using FFmpeg `lavfi` sources only (no downloads), small and fast; "best effort" fixtures recorded as `unavailable` with a reason if the local FFmpeg cannot create them; fails loudly for all others; writes `manifest.json` with expectations. Markers: background color per clip, **k+1 white squares in source second k** (proportional coordinates so portrait/wide variants work), tones per clip. Includes `bad_playlist.mp4` (a text playlist/ffconcat file pointing at a canary file) for security tests.

**Tests FIRST:** runner using `sys.executable -c ...` child processes: normal exit, non-zero exit, timeout kills a child **and its grandchild** (verify both gone), cancellation, stderr cap, no shell interpretation of special characters, huge output does not blow memory; inspector parsing with canned ffprobe JSON (rotation sign, SAR, multiple video streams, attached picture, missing duration, unknown codec); real inspector on fixtures (`requires_ffmpeg`): durations, dimensions, fps and fractional fps, start time 1.5 s on the offset fixture, rotation, SAR, audio presence, mono 22.05 kHz audio properties, VFR (or documented unavailable), `bad_*` fixtures map to the right `SOURCE_MEDIA_INVALID` reasons including `unsupported_container` for the playlist trap; binary discovery errors (fake PATH).

**Acceptance:** all pass; `doctor` informative; fixtures reproducible.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal.render doctor` → FFmpeg/ffprobe versions and a checklist: `libx264 ✓`, `aac ✓`, `xfade ✓/✗`, `acrossfade ✓/✗`. (✗ for the last two only blocks R9.)
2. `python scripts/make_render_fixtures.py` → table of created files; `rotated`/`vfr` may be `unavailable` (acceptable, tell me).
3. **Watch** `clip_a_8s_640x360_24.mp4`: red background; the number of white squares increases once per second (1, 2, … 8). Listen: a steady tone. `clip_noaudio…` is silent.
4. `python -m scene_signal.render inspect-source tests/render/fixtures/media/<file>`:

| File | Expect |
|---|---|
| `clip_a_8s_640x360_24.mp4` | duration ≈ 8.0, 640×360, fps 24 (constant), has_audio true |
| `clip_ntsc_6s_480x270_2997.mp4` | fps `30000/1001` |
| `clip_offset_6s_640x360_24.mp4` | start time **1.5** |
| `clip_portrait_6s_360x640_30.mp4` | 360×640 |
| `clip_noaudio_6s_640x360_24.mp4` | has_audio false (valid) |
| `clip_mono22k_6s_640x360_24.mp4` | audio 22050 Hz, 1 channel |
| `bad_zero.mp4`, `bad_truncated.mp4`, `bad_not_video.mp4` | `SOURCE_MEDIA_INVALID` (reason `corrupt`/`not_video`) |
| `bad_still.png` | `SOURCE_MEDIA_INVALID` (reason `not_video`) |
| `bad_audio_only.m4a` | `SOURCE_MEDIA_INVALID` (reason `no_video_stream`) |
| `bad_playlist.mp4` | `SOURCE_MEDIA_INVALID` (reason `unsupported_container`) — **security case** |

5. `pytest -q -m requires_ffmpeg` passes; with FFmpeg removed from PATH, FFmpeg tests are **skipped**, the rest pass.

---

## Chunk R6 — First real render: hard cuts, video-only

### 🤖 FOR GEMINI — Spec

**Objective:** produce a playable MP4 and manifest from a hand-written plan with ≥ 2 clips. Plans require `audio: null` in this chunk (audio capability still gated).

**Files:** `render/adapters/ffmpeg/{command_builder,engine}.py`; capabilities updated to the "After R6" column (`render_engine: true`); CLI `render PLAN.json --assets-root DIR --data-root DIR [--job-id ID]`; integration tests `tests/render/integration/`; golden-argument tests `tests/render/unit/test_command_builder.py`; docs updated.

**Implement**
- Pure `command_builder`: `RenderExecutionPlan` → argument lists for (1) per-segment normalization (D.4: absolute-timestamp trim, fps conversion, geometry from R2, pad/crop, SAR 1, `yuv420p`, exact `n_i` frames, near-lossless intermediate) and (2) assembly (concat demuxer over the verified intermediates with relative names in the workspace, final libx264 CRF/preset from settings, `yuv420p`, `+faststart`, **no audio**). Safety measures D.5 (`-nostdin`, `-n`, `file:` inputs, protocol whitelist, numbers only, fixed formats).
- `FfmpegRenderEngine`: Phase 1 per segment with progress; **verify each intermediate** (frame count == `n_i`, dimensions, fps, pixel format) before continuing — mismatch → `FFMPEG_FAILED` naming the segment; Phase 2 assemble to `output.partial.mp4`; return to the service, which inspects the output (basic measured metadata into `RenderResult`: duration, width, height, fps, streams, frame count, size, sha256), atomically moves it to `output.mp4`, writes manifest/result.
- Errors: FFmpeg non-zero exit → `FFMPEG_FAILED` (phase, segment, exit code, sanitized stderr tail); missing output → `OUTPUT_ARTIFACT_INVALID`; timeouts → `RENDER_TIMEOUT`.
- Manifest includes sanitized command templates, derived and **measured** per-segment frame counts.

**Tests FIRST**
- Command-builder golden tests (no FFmpeg): argument lists contain no plan strings, no `shell`, numbers formatted without exponents, fractional fps as `30000/1001`, all paths are resolver/workspace tokens; hostile asset names (leading `-`, spaces, quotes, `;`, unicode) never alter the argument structure.
- Integration (`requires_ffmpeg`), each verifying output exists, is readable, order via the markers, and frame counts:
  1. single clip; 2. two clips hard cut; 3. the spec's three-clip example in order; 4. trim starting after zero (A 2–6: markers show 3,4,5,6 squares); 5. mixed resolutions (wide + 640×360 + portrait) with letterbox, plus a `crop` render; 6. fractional fps output `30000/1001` and a fractional-fps source; 7. portrait source in a landscape profile (black side bars verified at known pixels); 8. invalid range, missing file, corrupt file, FFmpeg missing, forced timeout via a tiny timeout setting (all typed, no output, no leftover workspace, no `output.mp4`).
- Marker helpers decode raw frames and read squares/background without heavy dependencies.

**Acceptance:** milestone behavior of spec §18 items 1–7 for video-only; failed jobs cannot report outputs; sources unchanged.

### 🧑 FOR YOU — Review and manual test (**watch the videos**)

1. `python -m scene_signal.render render docs/render/examples/plans/three_clips.video_only.json --assets-root tests/render/fixtures/media --data-root ./.scene_signal/render --job-id demo-1`
2. Open `./.scene_signal/render/renders/demo-1/output.mp4` in your player. Expected:
   - 12 seconds, 1280×720, no audio.
   - **0–4 s red**, squares **3 → 4 → 5 → 6** (one change per second).
   - **4–8 s green**, squares **5 → 6 → 7 → 8**.
   - **8–12 s blue**, squares **2 → 3 → 4 → 5**.
   - Cuts are instantaneous. Picture fills the frame (640×360 scaled exactly 2×, no bars).
3. Open `result.json`: `status: succeeded`, measured `frame_count: 360`, `has_audio: false`, `sha256:` checksum, **relative** output path. Open `manifest.json`: per-segment derived times and `measured_frame_count` equal to expected; no absolute paths.
4. Render `docs/render/examples/plans/portrait_letterbox.json` → portrait yellow clip centered with **black bars** left/right, nothing stretched; `portrait_crop.json` → fills the frame, top/bottom cut.
5. Render `fractional_fps_three_clips.json` → plays smoothly; result says frame rate `30000/1001`, **288 frames**, 12.012 s.
6. Failure cases: `invalid_range_past_end.json` → `SOURCE_RANGE_INVALID` naming the segment; plan pointing at `bad_truncated.mp4` → `SOURCE_MEDIA_INVALID`; **no** `output.mp4` in those job folders; `.scene_signal/work` empty.
7. Run the same job id again → served from storage (no re-render).
8. Confirm `tests/render/fixtures/media/*` are unchanged.

---

## Chunk R7 — Output verification, timing tolerance and edge-case timing

### 🤖 FOR GEMINI — Spec

**Objective:** make timing claims **measured and enforced**; harden timing against awkward inputs.

**Files:** `render/domain/postconditions.py` (pure), `render/application` integration, tolerance constants in `policies.py`, CLI `inspect-output FILE` and `verify-output PLAN OUTPUT`; tests `tests/render/unit/test_postconditions.py`, `tests/render/integration/test_timing_*.py`; docs `timing.md` finalized with **measured** error statistics from the fixtures.

**Implement:** postconditions (C.4 tolerances): file readable; video stream present; audio stream presence matches the profile (until R8: absent); dimensions and frame rate equal the profile; frame count within ±1 of `N`; video duration within `1/fps`; container within its tolerance. A failed postcondition makes the render **fail** with `OUTPUT_ARTIFACT_INVALID` (details list the failed checks); results list every check with `passed/failed/skipped`.

**Tests FIRST:** pure tests with synthetic measurements (each check passing, failing at boundary ±, skipped); integration timing tests: **frame-accurate source selection** (marker boundary at source second 3 appears at output frame `3·fps ± 1` when the segment starts at source 0, and shifts correctly when starting at 1.0 or 2.5), segment boundaries at exact derived frames, **non-zero container start** fixture (cut still at the right source time, T-10), **rotated** source (best effort), **SAR** source, **VFR** source (best effort; if unavailable, a documented xfail with reason), fractional fps in and out, a 0.5-s segment, a segment of exactly one frame, `SOURCE_END_WITHIN_TOLERANCE`, timing error never accumulates across 20 short segments (total frames equal `N` exactly).

**Acceptance:** tolerances documented with justification; unit tests distinguish exact math tests from approximate measured tests (names reflect it); timing.md lists measured worst-case deviations.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal.render inspect-output ./.scene_signal/render/renders/demo-1/output.mp4` → duration 12.0, 1280×720, fps 30, 360 frames, video only.
2. `python -m scene_signal.render verify-output docs/render/examples/plans/three_clips.video_only.json ./.scene_signal/render/renders/demo-1/output.mp4` → every postcondition `passed`.
3. Render `offset_start_trim.json` (uses the clip whose container starts at 1.5 s, trimming source 2–6). **Watch**: squares **3,4,5,6** (not shifted by 1.5 s).
4. Render `twenty_short_segments.json` (20 segments of 0.5 s from clip A). Result frame count equals the derived total exactly.
5. `verify-output` against a **different** plan's output (e.g. the demo-1 output with the fractional-fps plan) → fails with the offending checks listed.
6. Read `docs/render/timing.md`: the measured deviations should be within the stated tolerances. If any fixture is skipped/xfailed, note which.

---

## Chunk R8 — Audio behavior

### 🤖 FOR GEMINI — Spec

**Objective:** implement A-01…A-08. Capabilities → "After R8".

**Files:** command builder and engine audio paths; `domain/execution_plan` audio spec; postcondition audio checks; tests; plans `three_clips.with_audio.json`, `all_mute_with_audio_profile.json`, `source_audio_on_noaudio_asset.json`, `mono22k_source.json`.

**Implement:** per-segment PCM at sample-exact lengths (`a_i = round(f_i/fps·48000)` cumulative), silence for `mute`, resample/remap per A-05 with warnings, `SOURCE_AUDIO_MISSING` per A-04, concatenate PCM and encode AAC **once**, mux with the video stream copy, `audio: null` → no audio stream even if sources have audio. Postconditions: audio presence/codec/rate/channels match the profile; audio duration within ±50 ms.

**Tests FIRST:** sample-boundary arithmetic (pure); with FFmpeg: output with audio has one stream, 48 kHz stereo AAC; **tone verification** with a pure-Python Goertzel helper on decoded PCM: segment from clip A (`source`) contains 440 Hz and **not** 660/880; `mute` segments are silent (RMS below a defined threshold) **even when the asset has loud audio**; profile audio null → no audio stream; `source` on a no-audio asset → `SOURCE_AUDIO_MISSING`; mono 22.05 kHz source normalized to stereo 48 kHz with warnings; source audio shorter than range → silence padded + warning; audio duration within ±50 ms; no audible click/gap at cuts (sample discontinuity check at boundaries is **not** required; sample counts must be exact).

**Acceptance:** audio never audible unless requested; semantics documented in `docs/render/` including deferred features (background music, gain).

### 🧑 FOR YOU — Review and manual test (**listen**)

1. `python -m scene_signal.render render docs/render/examples/plans/three_clips.with_audio.json --assets-root tests/render/fixtures/media --data-root ./.scene_signal/render --job-id demo-audio`
2. Play the output: **0–4 s** the **440 Hz tone** (clip A, `source`) over the red segment; **4–12 s silence** (`mute`). Visuals as in R6.
3. `all_mute_with_audio_profile.json` → output **has** an audio track that is completely silent although the sources have tones. (Check the track exists in your player's info panel.)
4. A profile with `audio: null` → no audio track at all (R6 plans still behave that way).
5. `source_audio_on_noaudio_asset.json` → `SOURCE_AUDIO_MISSING`; no output.
6. `mono22k_source.json` → plays normally; `result.json` warnings mention resampling and channel remap.
7. `inspect-output` → audio codec `aac`, 48000 Hz, 2 channels; audio duration within 50 ms of video.
8. `pytest -q` stays green.

---

## Chunk R9 — Crossfade transition

### 🤖 FOR GEMINI — Spec

**Objective:** implement C.5. Capabilities → "After R9" (crossfade only when the local FFmpeg has `xfade` and `acrossfade`; otherwise `UNSUPPORTED_OPERATION` with that reason).

**Files:** command builder assembly with `xfade`/`acrossfade` on uniform normalized streams; plan validation of C.5 constraints (frame-quantized overlap rules: `m ≥ 2`, `m_in + m_out ≤ n_i − 1`, duration bounds); tests; plans `crossfade_two_clips.json`, `crossfade_chain.json`, invalid ones (`crossfade_too_long.json`, `crossfade_non_adjacent.json`, `crossfade_duplicate_pair.json`).

**Tests FIRST:** timing: total frames equal the T-02 formula (vector from C.4: 5+5 s with 1.0 s at 30 fps → 270 frames); overlap frames show blended colors (middle frame of the overlap is neither pure source color; first/last overlap frames approach the respective clip colors, within tolerance); frames outside overlaps are the unblended source frames; source ranges never exceeded (marker check); audio crossfade (tone A fades out while tone B fades in) when audio is enabled; `mute` side fades against silence; each invalid case rejected with the right error; behavior when FFmpeg lacks the filters.

**Acceptance:** baseline hard-cut tests unchanged; transition timing matches the contract; no source handles added.

### 🧑 FOR YOU — Review and manual test (**watch**)

1. Render `crossfade_two_clips.json` (A 0–5 s, B 0–5 s, 1.0 s crossfade, 30 fps). Expected: total **9.0 s**; red clip dissolves smoothly into green over 1 second starting at **4.0 s**; square counts during the fade belong to both clips.
2. `result.json`: frame count **270**.
3. Render `crossfade_chain.json` (three clips, two crossfades) → total duration equals Σ durations − Σ overlaps; no flicker at the joins.
4. Invalid plans each fail with a clear error: too long (> 3 s or > half a segment), non-adjacent, duplicate pair.
5. If `doctor` showed `xfade ✗`, then a crossfade plan must report `UNSUPPORTED_OPERATION` mentioning the missing filter.
6. Re-render `three_clips.video_only.json` → identical frame counts as in R6 (**no regression**).

---

## Chunk R10 — Operational hardening

### 🤖 FOR GEMINI — Spec

**Objective:** make failure and abuse paths reliable.

**Files:** runner and service hardening; `INSUFFICIENT_STORAGE` pre-check; workspace janitor; concurrency guard; security regression tests; CLI `cleanup-stale --older-than-hours N`, `render --timeout SECONDS`, cancellation handling for Ctrl+C; docs `ffmpeg-security.md` finalized.

**Implement/verify:** cancellation end to end (kill FFmpeg tree mid-render → status `cancelled`, workspace and partial files removed, no `output.mp4`, no `result.json` success marker); per-phase and total timeouts → `RENDER_TIMEOUT`; disk check before rendering (free space ≥ estimated intermediates × 1.5 + output) → `INSUFFICIENT_STORAGE`; stale workspace cleanup without touching active jobs; `MAX_CONCURRENT_RENDERS` enforced (second render waits or fails fast with a documented behavior); limits enforced end to end; sanitized, size-capped `FFMPEG_FAILED` details; no internal retries (K-6) — assert the engine is called once on failure.

**Security regression tests (must all pass):** path traversal and symlink escape rejected; asset inside work/output roots rejected; `bad_playlist.mp4` (ffconcat/HLS-style text pointing at a canary file) rejected before any decoding and the canary is never opened (assert via a canary whose absence/permission change would error, plus the typed error); file names with leading `-`, spaces, quotes, `;`, `$()`, newlines and unicode render correctly or fail typed — never alter the command; a grep test that no `shell=True`, `os.system`, `eval` or `exec` exists in `render/`; logs and manifests contain no absolute paths or secrets (scan after a full run); plan strings never appear in any argument list (property test over generated plans).

**Tests FIRST:** all of the above plus: forced failure at **every phase** leaves no workspace, no `output.mp4`, a failure manifest, and a `failed` status; killing the process (simulated crash) leaves `status.json` as `running` and a stale workspace that the janitor can remove; re-running after a crash works.

**Acceptance:** failures are typed, diagnosable and leave no artifacts mistakable for success.

### 🧑 FOR YOU — Review and manual test

1. **Timeout:** `python -m scene_signal.render render docs/render/examples/plans/long_90s.json --assets-root … --data-root … --job-id t1 --timeout 2` → `RENDER_TIMEOUT` quickly; job folder has **no** `output.mp4`; `.scene_signal/work` empty.
2. **Cancel:** start `long_90s.json` and press **Ctrl+C** mid-render → status `cancelled`; no leftover FFmpeg processes (`ps`/Task Manager show none); work folder clean.
3. **Crash simulation:** start a render, force-kill the Python process (`kill -9` / Task Manager). Then `python -m scene_signal.render status t2 --data-root …` shows `running` (stale). Run `cleanup-stale --older-than-hours 0` → work folder removed; re-run the job → succeeds.
4. **Security:** render a plan using `bad_playlist.mp4` → `SOURCE_MEDIA_INVALID (unsupported_container)`; and a plan whose asset URI is `../outside.mp4` → `ASSET_ACCESS_DENIED`.
5. **Hostile names:** copy `clip_a_8s_640x360_24.mp4` to `-weird name; $(echo hi).mp4` (macOS/Linux; Windows: a name with spaces and `&`), render a plan using it → renders correctly; nothing executed.
6. Fill the disk is **not** required; trust the unit test for `INSUFFICIENT_STORAGE`.
7. `pytest -q` green; `grep -rn "shell=True" src/scene_signal/render` → nothing.

---

## Chunk R11 — Integration boundary, CLI finalization, acceptance sign-off

### 🤖 FOR GEMINI — Spec

**Objective:** document how the Production Orchestrator will use the renderer and prove the milestone. **Do not integrate with the generation application.**

**Files:** `docs/render/integration-boundary.md`, `docs/render/acceptance.md`, finalized `edit-plan-contract.md`, `render-result-contract.md`, `README` section, `GEMINI.md` and (if present) `AI_RULES.md`/`SESSION_BOOT.md` updates, `docs/render/schemas/*.json` regenerated, CLI help texts and consistent exit codes (0 success, 1 failed render, 2 invalid input, 3 internal), optional parity test `tests/integration/cross_module/test_probe_parity.py` (skipped if Module 01's probe is absent; test code only, not `src/`).

**`integration-boundary.md` must cover:** how the Orchestrator submits a `RenderRequest` (Python service call; CLI; file-based), idempotency keys (`render_job_id` rules), discovering `RendererCapabilities`, tracking status (`status.json`), receiving `RenderResult` and the manifest, error → recommended action table (retryable vs permanent; what to re-plan vs retry), artifact handoff to Output Validation (path = output root + relative ref + checksum), versioning and compatibility policy, how Module 5 data feeds Module 6 (including pinning `checksum` from extraction fingerprints), what the Orchestrator must provide (asset resolution/roots, config), and an explicit list of **future** work (storage backends, asynchronous API, queueing, generation adapter, shared media kernel).

**Acceptance:** every item of spec §18 mapped to evidence in `acceptance.md` (test names or reproducible commands); full `pytest -q` including Module 01 green; independence check (grep: no generation-app references; no cross-module imports); docs match verified behavior.

### 🧑 FOR YOU — Final acceptance

1. `pytest -q` → green; note skipped tests and reasons.
2. Run the full demo: render the spec example with audio (`three_clips.with_audio.json`) → watch **and** listen; then run `verify-output`.
3. `python -m scene_signal.render capabilities` → matches the "After R9" column.
4. Read `docs/render/integration-boundary.md` as the Orchestrator's developer: could you call the renderer from the Production Orchestrator using only this document? Anything missing → send it back.
5. Read `docs/render/acceptance.md` line by line: any ✅ without evidence → send it back.
6. Confirm isolation: `git status` in the generation app (if it is a Git repository) is clean.
7. **Independence drill:** commit, `git clone . ../SceneSignal-drill`, new virtualenv, `pip install -e ".[dev]"`, `pytest -q` → green; delete the clone.
8. Decide next: Module 6 (Edit Planning) specification, or Module 8 (Output Validation) — which would justify extracting the shared media kernel.

---

# PART F — Risk register (📎 SHARED)

| # | Risk | Consequence | Mitigation | Validation |
|---|---|---|---|---|
| R-1 | **Timestamp accuracy** (VFR, non-zero start, B-frame offsets, rotation) | Wrong frames cut; drifting sync | Exact `Fraction` kernel; absolute-timestamp trims (T-10); per-segment frame-count verification | R2 vectors and sweep; R6/R7 marker tests incl. offset, rotated, VFR fixtures; measured deviations in `timing.md` |
| R-2 | **Cumulative duration drift** | Total length wrong by many frames | Cumulative boundaries `F(T_i)` (T-02), ≤ 0.5 frame total error | 500-plan seeded sweep; 20-short-segment render |
| R-3 | **Mixed input formats** (resolution, fps, SAR, rotation, audio) | Stretched, wrong-orientation or out-of-sync output | Declared `fit`; pure geometry; normalization allowlist; autorotate + SAR | Geometry vectors; R6 portrait/wide/crop tests; SAR/rotation fixtures |
| R-4 | **Transitions** | Wrong total duration, invisible/glitchy fades, silent handle insertion | Overlap model, no handles, frame-quantized constraints, capability-gated until baseline is solid | R2 crossfade vector; R9 blend and total-frame tests |
| R-5 | **Audio behavior** (unintended audio, AAC join gaps, mismatched sources) | Unwanted sound, clicks, drift | Explicit A-rules; PCM sample-exact then **one** AAC encode; `mute` = silence; strict missing-audio error | R8 Goertzel tone tests, silence-with-loud-source test, ±50 ms duration |
| R-6 | **FFmpeg failures** (exit codes, partial outputs, version differences, missing filters) | Broken or misleading artifacts | Per-segment verification; `.partial` then atomic move; postconditions; `doctor`; runtime capability detection for `xfade`/`acrossfade`; versions in manifest | R5–R7 integration; R9 missing-filter test; R10 failure-at-every-phase tests |
| R-7 | **Storage limits** (intermediates; large sources) | Disk full mid-render; huge temp usage | Plan limits; disk pre-check; workspace cleanup + janitor; configurable intermediate CRF | R10 storage and janitor tests; documented intermediate size estimate |
| R-8 | **Unsafe command construction / hidden file or network reads** | Arbitrary file reads, injection | No plan strings in arguments; argument lists; protocol and demuxer allowlists; path containment; security regression suite; grep for shell use | R6 golden-argument tests; R10 security suite incl. playlist trap and hostile file names |
| R-9 | **Double-generation quality and time** | Slight quality loss; slower renders | Near-lossless intermediates; fast paths deferred until correctness proven | R7 quality sanity (visual); benchmark note in `testing.md` |
| R-10 | **Decoding long sources to reach a late trim point** | Slow renders on long sources | Limits; documented; seek-based pre-roll optimization deferred with tests required | Manual timing note in R7; future chunk |
| R-11 | **Coupling to Module 01 or the generation app** | Untestable, fragile monolith | `render` namespace; no cross-module imports (tested both directions); contracts only | R1 architecture test; R11 independence drill |
| R-12 | **Contract drift / silent upgrades** | Old plans render differently | Versioned contracts, `extra=forbid`, capability discovery, snapshot tests of capabilities and schemas | R1 snapshot tests; schema export diffs |
| R-13 | **Synthetic fixtures misrepresent real footage** | Passing tests, failing real videos | Fixtures documented as synthetic; encourage real clips in manual tests; `inspect-source` on your own files | Manual tests in R5–R8 with your clips |
| R-14 | **Concurrency / resource exhaustion** | OOM, thrashing | `MAX_CONCURRENT_RENDERS` default 1; timeouts; limits | R10 concurrency test |

---

# PART G — Gemini CLI prompts

## G.0 🤖 FOR GEMINI — Standing Rules (paste FIRST in every session, before the chunk prompt)

````
You are the implementation engineer for SceneSignal Module 02 ("Timeline & Render Execution", package
scene_signal.render). SceneSignal is a standalone project; the existing video-generation application and its notebook are
OUT OF BOUNDS. Your working directory must be the SceneSignal project root. You implement exactly ONE chunk per session.
The specification is docs/render/SPEC-02-timeline-render.md.

BEFORE CODING
1. Print pwd and list the directory. Confirm it is the SceneSignal root: pyproject.toml with distribution "scene-signal"
   and src/scene_signal/. If not, STOP and report. Never guess or invent an absolute path; never create the project here.
2. Read, in this order, the files that exist INSIDE this project: GEMINI.md, AI_RULES.md, SESSION_BOOT.md (if present),
   docs/render/handoff.md, docs/render/decisions.md. Module 01 files (docs/handoff.md, docs/decisions.md, src/scene_signal
   packages other than render, tests other than tests/render) are READ-ONLY for you.
3. Read the spec: Part C (contracts, frozen), Part D (architecture) and the "FOR GEMINI - Spec" of YOUR chunk in Part E.
   Ignore sections tagged "FOR YOU".
4. Check docs/render/handoff.md "Next chunk". If it does not match the requested chunk, STOP and report.
5. Run `pytest -q` BEFORE changing anything and record the exact result as the baseline.

RULES
1. SCOPE: only the requested chunk. No extra features, no unrelated refactoring, no new public names beyond the spec.
   If you need something from a later chunk, STOP and report.
2. BOUNDARIES: never read, list, search, import, copy or modify anything outside this project. Never touch the generation
   application or notebook. Do not modify Module 01 code, tests or docs. The only shared files you may edit are the
   project registry files (GEMINI.md, AI_RULES.md/SESSION_BOOT.md if present), pyproject.toml/.gitignore/.env.example
   additions that this chunk needs, and the README section for Module 02.
3. TDD (mandatory): write failing tests first; run them and show the red result (exact command and summary) BEFORE
   implementing; then implement until green. Never weaken, delete or skip tests to get green (allowed skips: the
   documented requires_ffmpeg / integration markers).
4. ARCHITECTURE: follow spec D.2. contracts/domain/ports/application never import subprocess, fastapi or adapters.
   scene_signal.render imports nothing from Module 01 and Module 01 imports nothing from render. No module may be named like
   a stdlib module. The architecture tests must stay green.
5. CONTRACTS: Part C is frozen. Do not rename fields, change enums or relax rules. The renderer executes plans; it NEVER makes
   creative decisions, reorders, trims beyond the plan, or substitutes an alternative edit when something fails - it returns a
   typed error. If a rule seems wrong or contradictory, STOP and write a CONTRADICTION REPORT.
6. SAFETY: no shell (shell=False, argument lists only); no plan-supplied strings in FFmpeg arguments, filters or paths other
   than resolver-produced paths; never log or store secrets; no network access; never modify source media; never hard-code
   absolute paths; temporary output must never be named like a finished artifact.
7. DEPENDENCIES: only those named in the spec (stdlib, pydantic, pytest, ruff, jsonschema). Ask before adding any other.
   No numpy/OpenCV: media checks use FFmpeg plus small pure-Python helpers.
8. UNSPECIFIED DETAILS: do not ask about minor details; choose the documented default or the most conservative reversible
   option and record it in docs/render/decisions.md.
9. QUALITY GATES: before reporting run the whole suite `pytest -q`, `ruff check .`, `ruff format --check .` (mypy if
   configured). Paste exact summary lines. Never claim a test passed without running it. Compare with the baseline: Module 01
   tests must be unchanged and green.
10. DOCS: update docs/render/handoff.md (verified state only), docs/render/decisions.md and every doc your chunk names; update
    registry files per rule 2. Mark a feature complete only with passing tests as evidence.
11. GIT: do not commit or push unless the user tells you to.

FINISH with a COMPLETION REPORT in exactly this format:

COMPLETION REPORT - Chunk R<N>
- Working directory confirmed: <pwd>
- Baseline before changes: <exact pytest summary>
- Implemented: <bullets>
- Files created/modified: <list>
- Interfaces introduced: <list>
- Red run (before implementation): <command + summary>
- Final test run: <commands + exact summary lines; passed/failed/skipped and why skipped>
- Lint/format: <results>
- Decisions made within scope (also in docs/render/decisions.md): <list or none>
- Measured results relevant to the chunk (timings, deviations, FFmpeg version): <list>
- Known limitations: <list>
- Unresolved issues / contradictions: <list or none>
- Manual-test notes for the Chief Engineer: <exact commands you verified>
- Docs and state files updated: <list>
- Anything changed outside the SceneSignal root, or in Module 01: <must be "none">
- Next recommended task: <chunk and first step>

CONTRADICTION REPORT format (use instead of continuing):
CONTRADICTION REPORT - Chunk R<N>
- Spec reference: <part/section/rule id>
- Problem: <what cannot be satisfied or is ambiguous>
- Evidence: <test/command output>
- Options: <A / B, with consequences>
- Recommendation: <one option>
- Work completed so far: <files/tests, left in a consistent state>
````

## G.0b 🤖 FOR GEMINI — `docs/render/handoff.md` template (R1 creates it; every chunk updates it)

````
# Handoff state - SceneSignal Module 02 (Timeline & Render Execution)
Last updated: <date> by Chunk R<N>

## Verified state (only what passes tests)
- R<N>: <what exists> - evidence: <test command + result>

## Chunk log
| Chunk | Status | Evidence | Date |
|---|---|---|---|

## Next chunk
<Chunk id and title exactly as in the spec>. Start by: <first step>.

## Do not repeat
- <work already done>

## Open issues / limitations
- <list>

## Environment notes
- Python <ver>, FFmpeg <ver or "not installed">, encoders/filters found: <list>
````

## G.1 🤖 FOR GEMINI — Chunk R1 prompt (self-contained; paste after G.0)

````
CHUNK R1 - Scaffold, contracts, capabilities, plan validation (Module 02: scene_signal.render).

STEP 1 - INSPECT BEFORE CHANGING ANYTHING
  a) Print the working directory and list it. Confirm it is the SceneSignal project root: it must contain pyproject.toml
     whose distribution name is "scene-signal" and the directory src/scene_signal/. Do NOT guess any absolute path and do NOT
     create a new project. If this is not the SceneSignal root (or the project has not been created), STOP and report that the
     user must complete Module 01's Pre-flight and Chunk 0 first.
  b) Read the project instruction/state files that exist inside this project, in this order: GEMINI.md, AI_RULES.md,
     SESSION_BOOT.md, docs/render/handoff.md (if present), docs/render/decisions.md (if present). Respect them. Module 01's
     docs/handoff.md and decisions.md are read-only.
  c) Read docs/render/SPEC-02-timeline-render.md: Part C (all), Part D and Part E "Chunk R1".
  d) Run `pytest -q` and record the exact baseline result.

STEP 2 - IMPLEMENT ONLY THE APPROVED CONTRACTS AND VALIDATION (Chunk R1 scope in the spec):
  - src/scene_signal/render/ with only the files this chunk needs: __init__.py, __main__.py, cli.py;
    contracts/{common,edit_plan,render_request,render_result,manifest,error_info,versions,loading,canonical,export}.py;
    domain/{errors,capabilities,plan_validation}.py.
  - Strict JSON loader (reject NaN/Infinity/duplicate keys/trailing data/>1 MiB; decimals as Decimal; <=6 decimal places;
    float snap rule; booleans never numbers). Exact Fraction fps accepting an int or "n/d" string, floats rejected.
  - Models exactly as spec C.2, C.9, C.10, C.11, C.12 (extra=forbid, frozen). RenderError hierarchy. RendererCapabilities
    exactly as the "After R1" column of C.3, pinned by a test.
  - validate_edit_plan / validate_render_request implementing PR-01..PR-13 in the stated precedence, collecting all violations
    of a stage with rule IDs and JSON paths. canonical_json, plan_fingerprint, request_hash.
  - CLI: python -m scene_signal.render validate-plan FILE | capabilities | export-schemas --out DIR (exit code 0 ok, 2 invalid).
  - Architecture test for the render package (spec D.2) including both cross-module directions, the shell=True grep and the
    stdlib-name check, with self-tests.
  - Examples under docs/render/examples/plans/ (valid: three_clips.video_only.json, three_clips.with_audio.json, single clip,
    crop, fractional fps; one invalid_<rule>_*.json per rule) and generated docs/render/schemas/.
  - Docs: docs/render/{architecture,edit-plan-contract,render-result-contract,timing,testing,decisions,handoff}.md (handoff
    "Next chunk: R2"); registry entry in GEMINI.md (and AI_RULES.md / SESSION_BOOT.md ONLY if they already exist); documented
    SCENE_SIGNAL_RENDER_* names in .env.example.
  DO NOT implement frame/timing math, FFmpeg, services, storage or any rendering. DO NOT modify Module 01 code, tests or docs.
  DO NOT touch the generation application or its notebook.

STEP 3 - TDD: write all tests listed in the spec's "Tests to write FIRST" for R1 before implementing; show the failing run.
STEP 4 - Run the whole suite, ruff check, ruff format --check, and the CLI on the examples. Report ACTUAL results.
STEP 5 - Finish with the COMPLETION REPORT: changed files, tests executed and exact results (compared with the baseline),
limitations, unresolved issues, anything changed outside the SceneSignal root or in Module 01 (must be "none"), and the next
recommended task.
````

## G.2 🤖 FOR GEMINI — Chunk R2 prompt

````
CHUNK R2 - Timing and geometry kernel (pure).
Read docs/render/handoff.md (Next chunk must be R2), spec Part C.4 and C.7 and Part E "Chunk R2".
Implement render/domain/{timing,geometry,timeline_rules,policies}.py: exact Fraction timing (round-half-up F(t)), derive_timeline
with transition-aware cumulative frame boundaries, compute_fit with floor_even/ceil_even/SAR/rotation, timeline rules T-04/T-05/
T-06 wired into validate_edit_plan as PR-14, and the CLI `timeline` and `geometry`. No floats anywhere in timing math; no I/O; no
FFmpeg. Assert every example vector in C.4 and C.7 exactly, plus the seeded 500-plan cumulative-rounding sweep. Do not implement
transitions in rendering; the math only. TDD first. Finish with the COMPLETION REPORT.
````

## G.3 🤖 FOR GEMINI — Chunk R3 prompt

````
CHUNK R3 - Ports, fakes, render service, manifest builder.
Read docs/render/handoff.md (Next chunk must be R3), spec Part C, D.6 and Part E "Chunk R3".
Implement render/ports/*, render/domain/execution_plan.py (engine-neutral RenderExecutionPlan), render/application/
{render_service,manifest_builder,lifecycle}.py, render/adapters/fakes/*, and the CLI `demo-fake`. The service validates before any
resolution, resolves and inspects before any engine call, verifies source ranges (T-09) and audio availability (A-04), derives the
timeline, runs the engine, builds the manifest, persists via the repository port, and always cleans the workspace. Implement
idempotency (C.9), cancellation checks between phases, progress reporting, and typed error mapping for every code in C.12. The
postconditions step is a documented stub that passes until Chunk R7. domain/application must not import subprocess. The renderer
never substitutes an alternative edit on failure. TDD first (ordering spies: engine call count 0 on any early failure).
Finish with the COMPLETION REPORT.
````

## G.4 🤖 FOR GEMINI — Chunk R4 prompt

````
CHUNK R4 - Local storage adapters: assets, workspace, job repository.
Read docs/render/handoff.md (Next chunk must be R4), spec Part C.9, D.5, D.6 and Part E "Chunk R4".
Implement render/adapters/storage/{local_assets,local_workspace,local_repository}.py and shared port contract tests (fake vs
local), plus CLI `check-assets` and `render --engine fake`. Resolver: scheme file only, allowed roots, realpath containment,
symlink/work-root/output-root rejection, size limit, supplied checksum always verified. Workspace: guaranteed cleanup incl. on
exceptions. Repository: atomic writes, atomic claim, valid transitions, request-hash idempotency, crash safety. Sources must stay
byte- and mtime-identical (test it). Never hard-code absolute paths. TDD first. Finish with the COMPLETION REPORT.
````

## G.5 🤖 FOR GEMINI — Chunk R5 prompt

````
CHUNK R5 - FFmpeg foundation: discovery, safe runner, inspector, fixtures.
Read docs/render/handoff.md (Next chunk must be R5), spec D.5, Part E "Chunk R5" and the fixture table in E.0.
Implement render/adapters/ffmpeg/{binaries,runner,inspector,progress_parser}.py, scripts/make_render_fixtures.py (FFmpeg lavfi
only; background color per clip, k+1 white squares in source second k with proportional coordinates, fixed tones; best-effort
fixtures may be recorded unavailable with a reason; includes bad_* cases and the bad_playlist.mp4 trap), tests/render/fixtures/
manifest.json, tests/render/helpers/, and CLI `doctor` and `inspect-source`. The runner: shell=False, argument lists, bounded
capture, timeout and cancellation kill the whole process TREE (test with a grandchild process). The inspector: content-based
format allowlist, default-disposition video stream, start time as the video origin, sign-normalized rotation, SAR, VFR
classification, audio properties, typed errors. No rendering in this chunk. TDD first (canned ffprobe JSON before real files).
Finish with the COMPLETION REPORT including FFmpeg version and which fixtures were unavailable.
````

## G.6 🤖 FOR GEMINI — Chunk R6 prompt

````
CHUNK R6 - First real render: hard cuts, video-only.
Read docs/render/handoff.md (Next chunk must be R6), spec C.4, C.7, D.3, D.4, D.5 and Part E "Chunk R6".
Implement render/adapters/ffmpeg/{command_builder,engine}.py (pure command builder with golden-argument tests; strategy
normalize_then_assemble: per-segment normalization with absolute-timestamp trim, fps conversion, geometry from R2, exact n_i
frames, VERIFIED intermediates; then assembly through the concat demuxer with relative names and one final encode, no audio),
update capabilities to the "After R6" column, wire the engine into the service so the output is inspected, moved atomically from
*.partial, and the manifest/result are written, and add CLI `render`. Plans must have audio: null. No plan string may enter an
argument. Verify the normalization chain empirically: measured frame counts must equal the derived counts; if not, REPORT it, do not
patch around it. Integration tests per the spec (order via markers, trim offset, mixed resolutions, letterbox and crop, fractional
fps, portrait in landscape, failure cases with no leftover files). TDD first. Finish with the COMPLETION REPORT.
````

## G.7 🤖 FOR GEMINI — Chunk R7 prompt

````
CHUNK R7 - Output verification, timing tolerance, edge-case timing.
Read docs/render/handoff.md (Next chunk must be R7), spec C.4 (T-07..T-10, tolerance table) and Part E "Chunk R7".
Implement render/domain/postconditions.py (pure), integrate it in the service (a failed postcondition fails the render with
OUTPUT_ARTIFACT_INVALID), CLI `inspect-output` and `verify-output`, and the timing integration tests (frame-accurate source
selection via markers, non-zero container start, rotated/SAR/VFR best-effort, fractional fps, tiny segments, no accumulation across
20 segments). Name exact-math tests and approximate measured tests differently. Finalize docs/render/timing.md with MEASURED
deviations. If a fixture cannot be produced, use a documented xfail with the reason. TDD first. Finish with the COMPLETION REPORT.
````

## G.8 🤖 FOR GEMINI — Chunk R8 prompt

````
CHUNK R8 - Audio behavior.
Read docs/render/handoff.md (Next chunk must be R8), spec C.6 (A-01..A-08) and Part E "Chunk R8".
Implement the audio path: per-segment PCM at sample-exact lengths from cumulative boundaries, silence for mute, resample/channel
remap with warnings, SOURCE_AUDIO_MISSING, concatenate PCM and encode AAC ONCE, mux with the video, audio:null => no audio stream.
Update capabilities to the "After R8" column and the audio postconditions. Source audio must never be audible unless audio_mode is
"source". Verify tones with a pure-Python Goertzel helper (no numpy). Do not add background music, gain or mixing. TDD first.
Finish with the COMPLETION REPORT.
````

## G.9 🤖 FOR GEMINI — Chunk R9 prompt

````
CHUNK R9 - Crossfade transition.
Read docs/render/handoff.md (Next chunk must be R9), spec C.4 (T-01, T-02), C.5 and Part E "Chunk R9".
Implement crossfade assembly on the uniform normalized streams (video and, when enabled, audio), the frame-quantized validation
rules (m >= 2, m_in + m_out <= n_i - 1, duration bounds, adjacency, one per pair), and runtime capability detection (crossfade only
when the local FFmpeg has xfade and acrossfade). Update capabilities to the "After R9" column. No source handles may be added: the
renderer never reads outside a segment's declared range. Baseline hard-cut tests must remain unchanged. TDD first. Finish with the
COMPLETION REPORT.
````

## G.10 🤖 FOR GEMINI — Chunk R10 prompt

````
CHUNK R10 - Operational hardening.
Read docs/render/handoff.md (Next chunk must be R10), spec D.5, D.6 and Part E "Chunk R10".
Implement end-to-end cancellation and timeouts, the INSUFFICIENT_STORAGE pre-check, the stale-workspace janitor (CLI
`cleanup-stale`), the concurrency guard, sanitized and capped FFMPEG_FAILED details, and the security regression suite listed in
the spec (traversal, symlink escape, playlist trap with canary, hostile file names, no shell/eval/exec grep, no absolute paths or
secrets in logs and manifests, plan strings never in arguments). There are NO internal retries: assert the engine is called once on
failure. Forced failure at every phase must leave no workspace, no output.mp4, a failure manifest and a failed status. TDD first.
Finish with the COMPLETION REPORT.
````

## G.11 🤖 FOR GEMINI — Chunk R11 prompt

````
CHUNK R11 - Integration boundary, CLI finalization, acceptance sign-off.
Read docs/render/handoff.md (Next chunk must be R11), spec Part E "Chunk R11" and the spec's section 18 definition of done
(reproduced in Appendix 1).
Write docs/render/integration-boundary.md and docs/render/acceptance.md as specified, finalize the contract docs, regenerate
docs/render/schemas/, finalize CLI help texts and exit codes, add the optional cross-module probe parity test (test code only;
skipped when Module 01's probe is absent), and run the full suite including Module 01. Do NOT integrate with the generation
application. Do NOT mark any acceptance item complete without a passing test or reproducible command as evidence. Finish with the
COMPLETION REPORT including the full pytest summary.
````

---

# PART H — Questions for you (only what materially affects correctness)

| # | Question | Why it matters | Recommended default |
|---|---|---|---|
| H-1 | If a segment says `audio_mode: "source"` but the asset has **no audio**, should the renderer **fail** (`SOURCE_AUDIO_MISSING`) or **substitute silence with a warning**? | Failing exposes planner mistakes; silence is more forgiving but hides them (generated clips often have no audio). | **Fail.** The planner can read `has_audio` from Module 5 and use `mute`. Revisit if it becomes noisy. |
| H-2 | Are the limits acceptable: **600 s** timeline, **100** segments, up to **3840×2160**, **4 GiB** per asset? | They bound time, disk and memory. | Keep as defaults (all configurable). |
| H-3 | Is accepting the **extra encode generation** (near-lossless intermediates, final re-encode) and temporary disk use acceptable for v1.0? | It buys per-segment verification and robust assembly. | **Yes**; add stream-copy/single-process fast paths later only if needed. |
| H-4 | Accept **small duplication** (error shape, ffprobe parsing) between Module 01 and Module 02 until Module 8 forces a shared kernel? | Avoids cross-module coupling now. | **Yes**, with the optional parity test in R11. |
| H-5 | Is **MP4 / H.264 / AAC / 8-bit yuv420p** the only delivery target for v1.0? | Keeps the capability surface small and testable. | **Yes.** |
| H-6 | Does your SceneSignal project already exist (Module 01 Chunk 0 done) and are `AI_RULES.md` / `SESSION_BOOT.md` real files in it? | Decides whether R1 can start immediately and which state files get registry entries. | Gemini inspects and adapts; if the project does not exist, **do Module 01's Pre-flight and Chunk 0 first** (I will not create or place it for you). |

---

# APPENDIX 1 — Spec §18 "Definition of done" mapping (📎 SHARED)

| Spec §18 item | Satisfied in |
|---|---|
| A versioned EditPlan can be validated | R1 (+R2) |
| The renderer consumes a manually written plan | R6 |
| Selects source ranges from at least two clips | R6 |
| FFmpeg produces a playable output in the requested order | R6 |
| Basic output metadata can be inspected | R6, R7 |
| Render manifest records plan, sources, profile, output | R3 (builder), R6 |
| Invalid plans and common FFmpeg failures produce typed errors | R1, R3, R5, R6, R10 |
| Unit tests run without paid services | all |
| Integration tests pass where FFmpeg exists | R5–R10 |
| The renderer does not make creative editing decisions | C.8 allowlist; R1–R10 tests |
| Existing generation application and notebook untouched | every chunk's report; R11 isolation check |
| Documentation accurately describes supported behavior and limitations | R1 onward; R11 |

---

# APPENDIX 2 — 🧑 FOR YOU — Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| Gemini stops saying "not the SceneSignal root" | Wrong working directory or project not created | `cd` into `SceneSignal/`; if it does not exist, do Module 01 Pre-flight and Chunk 0 |
| `FFMPEG_NOT_FOUND` / FFmpeg tests skipped | FFmpeg not on PATH | Install FFmpeg; reopen the terminal; run `doctor` |
| Crossfade reported unsupported | Local FFmpeg lacks `xfade`/`acrossfade` | Install a fuller FFmpeg build; `doctor` shows ✓ |
| `rotated`/`vfr` fixtures `unavailable` | Your FFmpeg cannot create them | Acceptable; tell me, I will adjust tests |
| Output looks right but `verify-output` fails | A postcondition outside tolerance | Paste the report; do not loosen tolerances yourself |
| Squares/colors do not match the guide | Wrong plan or fixture | Re-run `make_render_fixtures.py`; check the plan's `source_start_seconds` |
| Gemini edits Module 01 files | Standing Rules not pasted | Paste G.0, ask it to revert out-of-scope changes |
| Gemini asks about the generation app | It is out of bounds | Refuse; remind it of rule 2 |
| Old work folders left behind | A crash | `cleanup-stale --older-than-hours 0` (after R10) |

**End of the Specification 02 document.** Next deliverable after R11 passes: Specification for Module 6 (Edit Planning & Decision Engine) or Module 8 (Output Validation & Delivery), which would also justify extracting the shared media kernel.
