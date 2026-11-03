# SceneSignal — Module 01: Scene Intelligence Extraction
## Consolidated Specification 01 (revision 2.0, incorporating Addendum 01): Review, Contracts, Chunked Plan, Gemini CLI Prompts, Manual Test Guide

| Item | Value |
|---|---|
| Project | **SceneSignal** — *Turn video into timestamped editing intelligence.* |
| Project root (new, independent) | `SceneSignal/`, inside a parent directory **you** choose (see Pre-flight, D.0b) |
| Python package / distribution / CLI | `scene_signal` / `scene-signal` / `python -m scene_signal` |
| This module | Module 01 — Scene Intelligence Extraction |
| Source specifications | "Claude Specification 01" v1.0 + "Addendum 01: Project Identity, Greenfield Directory, and Integration Boundaries" |
| This document | Consolidated architect deliverable, **revision 2.0** (supersedes revision 1.0, which used the working name `scene_intelligence` and did not require a separate workspace) |
| Author role | Technical Architect / Implementation Planner |
| Status | **DRAFT — awaiting Chief Engineer approval of Part B.2 and the Pre-flight answers** |
| Implementation language | Python ≥ 3.11 |
| Coding model | Gemini CLI |

### 📎 What changed in revision 2.0

- Project identity is now **SceneSignal** (`SceneSignal/`, `scene_signal`). Contract type names (`ExtractionJob`, `SceneIntelligenceDocument`) and the module name are unchanged because they are part of the approved Specification 01.
- SceneSignal is a **greenfield, standalone project in its own new directory**. It never reads, modifies, imports from or is initialised inside the existing generation application. Chunk 0 now verifies this.
- The location is **not guessed**: you supply the parent directory in the Pre-flight (D.0b) before any filesystem instruction is run.
- **Contract-first integration**: the contract is the boundary; the generation adapter is documented (C.7b, Part G) but **not built** in the first milestone.
- New consolidated Part S (boundaries, minimum asset requirements, validation and failure semantics, manual development mode), new Part N (naming/directory assessment), new Part G (future integration work).
- Plan changes: explicit job documents (`extract --job`), content-based format validation (MKV, extensionless files, still images rejected), `GEMINI.md` and `docs/integration-boundary.md` created inside SceneSignal.

---

## 0. How to read this file

Every section is tagged with who it is for. Tags appear at the start of headings.

| Tag | Audience | Meaning |
|---|---|---|
| 🧑 **FOR YOU** | Chief Engineer (human) | Decisions to make, things to check, **manual tests to run**. Gemini should ignore these. |
| 🤖 **FOR GEMINI** | Coding model | Instructions and specs to implement. Copy-paste blocks are inside fenced boxes. |
| 📎 **SHARED** | Both | Contracts and reference. Once you approve Part B, Part C is the **source of truth** for Gemini. |

### 🧑 FOR YOU — Workflow (read once)

1. Read **Part N** (naming and directory), **Part A** (review) and **Part B** (frozen decisions). Answer the approval table in **B.2** (AD-1 … AD-10). Replying "approve all defaults" is acceptable.
2. Complete the **Pre-flight (D.0b)**. It makes you choose the parent directory (I do not guess absolute paths), run the collision checks, create the empty `SceneSignal/` folder, drop this file into `SceneSignal/docs/SPEC-01-scenesignal.md`, and start Gemini CLI **inside** `SceneSignal/`.
3. For **each chunk** (0 → 12), in order:
   1. Open Gemini CLI with the working directory set to `SceneSignal/`.
   2. Paste **E.0 Standing Rules** first, then the chunk's prompt from **Part E** (Chunk 0 needs one placeholder filled in, see E.1).
   3. Wait for Gemini's **Completion Report** (template in E.0).
   4. Run the chunk's **🧑 Review and manual test** box in Part D.
   5. If everything matches, move to the next chunk. If not, paste the report and the problem back to me (Claude) before continuing.
4. Never give Gemini two chunks at once. Never skip a chunk.
5. **Never run Gemini CLI inside the existing generation application's directory, and never add that directory to Gemini's workspace.** SceneSignal is developed in isolation.

### 🧑 FOR YOU — What you need installed

| Need | Check command | Needed from |
|---|---|---|
| Python 3.11 or newer | `python --version` | Pre-flight |
| Git (recommended; SceneSignal gets its **own** repository) | `git --version` | Chunk 0 |
| FFmpeg **and** ffprobe on PATH (with libx264 and aac) | `ffmpeg -version` and `ffprobe -version` | Chunk 3 |
| Gemini CLI | whatever you already use | Chunk 0 |

You do **not** need any API key, GPU, or paid service for this module. If you later add a real vision provider, that is a separate approved step.

Activating a virtual environment (Chunk 0 creates it, inside `SceneSignal/`):
- macOS / Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

---

# PART N — Naming and directory-structure assessment

## N.1 📎 SHARED — Identifier decisions (proposed; approve via AD-8)

| Item | Value | Notes |
|---|---|---|
| Project name | **SceneSignal** | Proposed project decision. Domain names and trademarks are **not** claimed to be cleared. |
| Tagline | *Turn video into timestamped editing intelligence.* | |
| Project root | `SceneSignal/` | New directory; a **sibling** of, never inside, the generation application. |
| Python package (import name) | `scene_signal` | |
| Distribution name | `scene-signal` | PEP 503 normalisation makes `scene-signal`, `scene_signal` and `Scene.Signal` the same name. Installed locally only; no publishing planned. |
| CLI | `python -m scene_signal` | |
| Environment prefix | `SCENE_SIGNAL_` | Defined in `.env.example` (no secrets). |
| Local runtime folder | `.scene_signal/` (`work/`, `data/`) | Git-ignored. |
| Contract type names | `ExtractionJob`, `SceneIntelligenceDocument` | **Unchanged** from Specification 01 (approved contract names). |
| Module name | Module 01 — Scene Intelligence Extraction | SceneSignal is the project; this is its first module. |

## N.2 🧑 FOR YOU — Conflict checks

What I could verify from here:

| Check | Result |
|---|---|
| Valid Python identifier, PEP 8 style (lowercase with underscores) | ✅ `scene_signal` |
| Collision with a standard-library module name | ✅ none (`signal` exists in the stdlib, `scene_signal` does not). |
| **Packaging finding** | ⚠ My revision 1.0 plan had `domain/timeline.py`. A module named like a stdlib module can shadow it if its folder ever lands on `sys.path`. **Renamed to `domain/timeline.py`.** Added rules: no module inside the package may use a stdlib top-level name (enforced by the architecture test using `sys.stdlib_module_names`), and never put package subfolders on `sys.path` or run files from inside them. |
| Exact-name package/product conflict on the public web | A quick web search found no package or product with exactly this name, only unrelated near-names. The search was limited, so this is **not clearance**. |
| Conflict with names in the **existing generation application** | ❓ **Cannot be verified from here.** I have not seen its directory listing or environment. Run the checks below. |

**Run these before the Pre-flight** (replace `<PARENT_DIR>` with the absolute path you choose in D.0b):

| Purpose | macOS / Linux | Windows PowerShell | Expected |
|---|---|---|---|
| Target folder does not exist yet | `ls -d "<PARENT_DIR>/SceneSignal"` | `Test-Path "<PARENT_DIR>\SceneSignal"` | "No such file" / `False` |
| Parent is not inside another Git repository | `git -C "<PARENT_DIR>" rev-parse --show-toplevel` | same command | An error like "not a git repository". If it prints a path, **choose another parent** (SceneSignal must not live inside the generation app's repo). |
| No existing `scene_signal` module in the **generation application's** Python environment (activate that environment first) | `python -c "import importlib.util as u; print(u.find_spec('scene_signal'))"` | same command | `None` |
| Informational: public package index | `pip index versions scene-signal` | same command | "No matching distribution" (or something clearly unrelated). Informational only. |

## N.3 📎 SHARED — Directory structure and greenfield rules

```
<PARENT_DIR>/                      <- you choose; NOT the generation app's folder or any of its subfolders
├── <existing generation application>/   <- untouched; never read, imported, reorganised or modified
└── SceneSignal/                   <- NEW, independent project, own Git repository
    ├── GEMINI.md                  <- SceneSignal's own AI instructions
    ├── pyproject.toml, README.md, .gitignore, .env.example
    ├── src/scene_signal/          <- package (layout in C.9)
    ├── tests/   scripts/   docs/  <- docs/handoff.md is SceneSignal's own session handoff
    └── .venv/  .scene_signal/     <- own environment and runtime data (git-ignored)
```

| ID | Greenfield rule |
|---|---|
| G-01 | SceneSignal has its **own Git repository**, created by Chunk 0 (`git init`) in `SceneSignal/`. Never a subfolder or submodule of the generation application's repository. |
| G-02 | No file is copied from, moved out of, or symlinked to the generation application. |
| G-03 | SceneSignal never reads, imports, parses or references the generation application's classes, database schema, filesystem layout, notebook or framework objects. |
| G-04 | The generation application is **not modified** in any way, including its notebook. |
| G-05 | Own virtual environment, own `pyproject.toml`, own dependency set. |
| G-06 | Own configuration and environment-variable definitions (`.env.example`, `SCENE_SIGNAL_*`); no secrets committed. |
| G-07 | Own AI instructions (`GEMINI.md`) and own handoff documentation (`docs/handoff.md`, `docs/decisions.md`). |
| G-08 | Gemini CLI always runs with its working directory set to `SceneSignal/` and does not traverse above it. |
| G-09 | No absolute path is hard-coded anywhere in the code or docs. The parent directory is a value **you** provide (Pre-flight). |

**Assessment:** the name is syntactically safe and has no known conflict. The structure satisfies the Addendum. Two adjustments came out of this assessment: `domain/timeline.py` → `domain/timeline.py`, and the stdlib-shadowing guard in the architecture test.

## N.4 📎 SHARED — Where each item of the Addendum's required response lives

| Addendum §7 item | Location |
|---|---|
| 1. Naming and directory-structure assessment | Part N |
| 2. Technical review with the addendum incorporated | Part A (conflicts in A.3b) |
| 3. Consolidated, revised Specification 01 | Part S (this whole document is the consolidated specification) |
| 4. Finalized input and output contract proposal | Part C |
| 5. Independent project structure and dependency boundaries | C.9 |
| 6. Dependency-ordered, TDD-driven plan | Part D |
| 7. First Gemini CLI prompt (first approved chunk only) | E.0 + E.1 |
| 8. Future integration work for the existing generation application | Part G |

---

# PART A — Technical review

## A.1 🧑 FOR YOU — Verdict

The specification (with Addendum 01 incorporated) is **sound, implementable, and internally consistent enough to start**. There are **no genuine blockers** for starting Chunk 0 and Chunk 1. There are **ten decisions (B.2) that I recommend you confirm before Chunk 1**, plus the Pre-flight answers (parent directory) before Chunk 0,, because they touch the public contract and would be expensive to change later. Each has a safe, reversible default.

## A.2 🧑 FOR YOU — Missing information (defaults adopted unless you object)

| # | Missing item | Default adopted |
|---|---|---|
| **M-0** | **The parent directory where `SceneSignal/` will live.** | **No default. I will not guess an absolute path.** You provide it in the Pre-flight (D.0b). Chunk 0 cannot start without it. |
| M-1 | Conventions for the new project (AI instructions, state files, commit policy) | SceneSignal defines its own in Chunk 0: `GEMINI.md`, `docs/handoff.md`, `docs/decisions.md`. Gemini does **not** commit unless you tell it to. The generation application's conventions are irrelevant and are never read. |
| M-2 | Python version / packaging tool | Python ≥ 3.11, `pyproject.toml` with `hatchling`, `src/` layout, `pytest`, `ruff`. |
| M-4 | Allowed values of `extraction_profile` | `quick`, `standard`, `thorough` (see C.8). |
| M-5 | Default numeric limits and timeouts | Table in C.8. All configurable. |
| M-6 | Operating system | Commands are given for macOS/Linux and Windows where they differ. |
| M-7 | Details of the generation application's outputs (file layout, metadata, IDs) | Deliberately **not needed** for Milestone 1. The boundary is the contract; the mapping is future work (C.7b, Part G). |

## A.3 📎 SHARED — Contradictions, gaps and ordering issues found in the specification

None of these is a blocker. Each has a resolution that preserves your fixed decisions.

| # | Finding | Resolution | Needs approval? |
|---|---|---|---|
| F-1 | **Stage order.** §8 plans sampling (Stage 4) *before* shot detection (Stage 5), but good sampling needs shot boundaries (at least one frame per shot, no frame sampled across a cut). | Keep the ten stages. Split Stage 4/5 internally: shot detection runs first (it needs no sampled frames — it scans the video), then the sampling plan is built **per shot**, then frames are extracted. | **Yes — AD-1** |
| F-2 | **Illustrative output has a schema gap.** An event with `start_seconds: null` and `end_seconds: null` has nowhere to record *where* its evidence lies. | Add `evidence_span` (first/last supporting sample timestamps) and strict `temporal_precision` rules (C.3). | **Yes — AD-4** |
| F-3 | **Example vs. rules.** The example output shows `asset_fingerprint: null` and `frame_rate_mode: "unknown"`, but §6.4/§7 require computing a fingerprint and detecting variable frame rate. | The example is illustrative. In the standard flow the fingerprint is computed (`sha256:…`) and frame-rate mode is `constant`/`variable`/`unknown` only when truly undeterminable. | No |
| F-4 | **Example path vs. security.** The example request uses an absolute path `/test-assets/...`, while §13 requires preventing path access outside permitted locations. | Local storage adapter enforces configured **allowed roots** (symlink-safe). The example path is valid only if its root is allowed. | No |
| F-5 | **Requested capabilities vs. adapter limits.** A request may ask for `temporal_events` and `camera_analysis` while the available vision adapter only understands still images. | Capability negotiation: the result carries a per-capability **capability report** (`completed` / `partial` / `unsupported` / `failed` / `not_requested`). Unsupported is reported, never faked. | **Yes — AD-4** |
| F-6 | **Fixtures vs. "no external downloads".** §14.2 asks for real media fixtures but forbids external downloads. | Fixtures are **generated locally** with FFmpeg synthetic sources (`lavfi`) by a script; only a manifest is committed. Core unit tests need no FFmpeg; media tests are marked `requires_ffmpeg` and auto-skip if FFmpeg is absent. Limitation documented: synthetic fixtures have no semantic content. | No |
| F-7 | **Idempotency needs persistence.** §11 requires documented same-`job_id` behavior, but persistence is "optional". | Idempotency and conflict detection are only guaranteed **with a repository**. Stateless mode executes every call and documents that. | No |
| F-8 | **Interval convention vs. instants.** `[start, end)` cannot express an instant (zero-length). | Intervals require `start < end` strictly. Instants use `timestamp_seconds`. Shots tile `[0, duration)` with no gaps or overlaps. | No |
| F-9 | **Context text can poison analysis.** `source_prompt` / `global_prompt` could make a vision model "see" things the prompt says should be there. That would violate "evidence before interpretation". | By default context text is **not** sent to the vision provider (`include_context_in_analysis=false`). It is carried as context for downstream modules only. | **Yes — AD-7** |
| F-10 | **Fingerprint ownership.** §7 lists "fingerprint" under inspection output; fingerprinting works for any storage, not only ffprobe. | Fingerprint is computed by the **storage port** at resolve time; the probe port reports technical metadata only. Both land in the document. | No |
| F-11 | **Pipeline vs. no-CLI.** You need to test manually; the spec lists only an optional API. | Add a thin developer CLI (`python -m scene_signal …`), grown chunk by chunk. | **Yes — AD-3** |

## A.3b 📎 SHARED — Addendum 01 conflicts and their resolutions

None of these removes an original requirement. Each is a conflict between my revision 1.0 plan (or a literal reading of Specification 01) and the Addendum.

| # | Conflict | Resolution |
|---|---|---|
| AC-1 | **Workspace.** Revision 1.0 Chunk 0 said "discover and follow existing repo conventions", created the module in the current repository and checked `git status` from the repo root. The Addendum requires a new, independent directory and forbids reading or reorganising the existing application. | Removed. Conventions now come from SceneSignal's **own** files created in Chunk 0. Specification 01 §16 ("follow the repository's existing conventions") is read as *SceneSignal's own conventions once Chunk 0 establishes them*, **not** as "inspect the generation app". |
| AC-2 | **Absolute path.** Revision 1.0 defaulted to "wherever you run Chunk 0". The Addendum says: do not guess an absolute path; request the minimum necessary information. | Pre-flight D.0b requires you to supply `<PARENT_DIR>`. Chunk 0 verifies the location and stops on any mismatch. No absolute path appears anywhere in code or docs. |
| AC-3 | **Names.** Addendum renames the project, but Specification 01 fixes `SceneIntelligenceDocument`, the module title and a `scene_intelligence/` layout (§15). | Project = SceneSignal, package = `scene_signal`. Approved contract names and the module title are **kept**. §15's layout is re-rooted at `SceneSignal/`. |
| AC-4 | **"Do not assume every asset is a local MP4".** Specification 01's example uses `scheme: "file"` and `.mp4`; revision 1.0 supported only `file`. | The contract accepts any scheme string; the **v1.0 adapter** supports `file` only (documented constraint, typed error otherwise). Format validity is decided by **content** (ffprobe), never by extension. Fixtures now include Matroska and extensionless files; still images and audio-only files fail with typed errors (Part S.4). |
| AC-5 | **"Explicit, versioned job documents."** Revision 1.0 CLI `extract FILE` built the job implicitly. | CLI gains `extract --job JOB.json`; job documents are committed under `docs/examples/` and generated for fixtures. `extract FILE` stays as a convenience that prints the job it builds. |
| AC-6 | **Scope of "do not modify".** Specification 01 protects only the notebook; the Addendum protects the generation **application** too. | Extended everywhere (Standing Rules, G-04, Gemini GREENFIELD rule). |
| AC-7 | **Ingestion vs. extraction.** Specification 01 lists "asset resolution and basic media validation" as in scope; the Addendum separates ingestion/preparation from extraction. | Clarified: SceneSignal contains only **asset access and inspection** (what it needs to analyse). Ingestion and preparation (download, transcode, copy to shared storage) is upstream, outside the core, and listed as future work (Part G). |
| AC-8 | **Source kind must not change behavior.** The Addendum says uploaded, imported and generated assets converge at the same boundary. Revision 1.0 only required identical *shape*. | Strengthened: C-11 and a Chunk 9 test require identical analysis for the same media regardless of `source_kind`. |

## A.4 📎 SHARED — Feasibility notes by area

1. **Timestamps and variable frame rate (highest technical risk).** Never derive time from `frame_index / fps` for unknown-CFR media. Work in time (seconds → integer microseconds internally), record the *actual* decoded presentation timestamp for every extracted frame, and record frame index/pts only when known. Container `start_time` may be non-zero: the source timeline origin is defined as the first video frame's presentation time, normalized to 0.0, with the offset recorded.
2. **Sparse frames cannot establish actions.** A still-frame provider can say "a person is visible at t=2.5". It cannot say when walking started. The contract therefore separates *evidence span* from *claimed start/end*, and only a temporal-capable adapter may populate start/end (C.3, V-rules).
3. **Camera movement from stills is not valid.** Camera movement observations from still-only adapters must be `unsupported`. Multi-frame adapters may report `inference`; temporal video adapters may report `direct_observation`. Enforced in domain rules, not left to adapters.
4. **Shot detection with FFmpeg scene score.** Reliable for hard cuts; weak for dissolves/fades; sensitive to threshold; fast motion can false-positive. Complemented by `blackdetect` for black gaps. The first frame whose score exceeds the threshold is the first frame of the new shot. Limitations are reported in the capability report. Gradual transitions are **not** claimed.
5. **Provider heterogeneity.** The port declares capabilities (still / frame sequence / video clip; max frames per call; supported analyses). The application negotiates; adapters never decide the canonical schema. Adapters perform **no hidden retries**; the application retry policy does (so retry behavior is testable once).
6. **Cost and latency.** Cost scales with number of frames × calls. Controls: profile frame budgets, batching by shot (≤ 8 frames per call by default), image downscale (long edge 1024 px default), hard caps. Estimates are only meaningful once a real adapter exists; the fake provider validates mechanics, not cost.
7. **Security.** Path traversal and symlink escape, prompt injection through `source_prompt` and through on-screen text, provider output treated as untrusted data, secrets by reference only, no shell invocation (`subprocess` with argument lists), temp-file cleanup on all failure paths.
8. **Sync core.** Recommended: synchronous application core, run in a thread pool by FastAPI. Simpler TDD, fully adequate for I/O-bound adapters. Reversible (D-06).

## A.5 🧑 FOR YOU — Minor recommendations (adopted by default)

- Pydantic v2 models in `schemas/` are the canonical contracts; the `domain/` layer holds value objects, rules and errors (no duplicate model hierarchy).
- No `pydantic-settings` dependency: settings are a frozen dataclass loaded from environment variables and optional TOML (`tomllib`).
- Fakes live in `adapters/fakes/` (shipped, because the CLI and tests both use them).
- Real FFmpeg adapters are pulled **earlier** than the spec's example sequence (Chunks 3–6), because timestamp handling is the highest risk and manual testing needs real media.
- An architecture test enforces the dependency rule (no provider SDK / FastAPI / adapter imports in `domain`, `application`, `ports`).

---

# PART B — Frozen architecture decisions

## B.1 📎 SHARED — Decisions preserved exactly

| ID | Decision (from spec) |
|---|---|
| 4.1 | Independent module (now a standalone project, **SceneSignal**): own directory, package, dependencies, config, tests, docs. Callable directly as a Python application service; optional lightweight FastAPI interface; **no** mandatory microservice. |
| 4.2 | Ports and adapters. Provider SDKs never leak into the domain. Swapping a vision provider never changes the canonical schema. |
| 4.3 | One asset per extraction job. Production grouping/order are optional context. A merged video is one asset with multiple shots. |
| 4.4 | Provider-neutral core. No paid API or GPU for unit tests. |
| 4.5 | Versioned input and output contracts; changes documented and tested. |
| 4.6 | Evidence before interpretation; uncertain interpretations are never presented as facts. |
| 4.7 | Source media immutable; all proxies/frames/thumbnails are derived artifacts. |
| — | FFmpeg/ffprobe adapters behind ports. Half-open `[start, end)` intervals, seconds as canonical unit, source timeline distinct from edited timeline. |
| — | No new microservice, no specific paid vision provider, no unrelated features, **no modification of the existing video-generation notebook or application**. |
| — | Excluded: scene planning, generation, editing decisions, rendering, regeneration, YouTube publishing, channel config management, frontend, mandatory embeddings/vector DB/transcription, universal ingestion, autonomous editing agent. |

## B.1b 📎 SHARED — Decisions fixed by Addendum 01

| ID | Decision |
|---|---|
| N-01 | Project name **SceneSignal**; root `SceneSignal/`; package `scene_signal` (proposed, subject to AD-8). |
| N-02 | Greenfield: new, independent directory with its own source, dependencies, tests, fixtures, docs, configuration, AI instructions, handoff and version control. Never initialised inside, and never reusing files from, the existing application. |
| N-03 | Contract-first integration. Direct integration with the generation application is **not** part of the first milestone. |
| N-04 | The extraction pipeline never depends on the generation application's classes, database schema, filesystem layout, notebook or framework objects. No shared database, runtime, deployment or storage is assumed. |
| N-05 | One canonical request for generated, uploaded and imported assets; they converge at the same boundary after any upstream resolution/preparation. |
| N-06 | Five concerns stay separate: ingestion/preparation, SceneSignal extraction, generation integration, future editing intelligence, future rendering/publishing. Milestone 1 implements only extraction and the contracts it needs. |
| N-07 | The future generation adapter is a **documented integration boundary** (C.7b), not a first-milestone task, and lives outside the extraction core. |
| N-08 | Development uses hand-curated local assets and explicit, versioned job documents. Channel configuration, production context, generation metadata and source prompts stay optional. |

## B.2 🧑 FOR YOU — Proposed changes that need your approval

Reply with **"approve all defaults"**, or list IDs you want changed. Nothing here changes a fixed decision; each is a clarification or an addition. **AD-8 to AD-10 are new in revision 2.0.**

| ID | Proposal | Why | Default if you approve |
|---|---|---|---|
| **AD-1** | Shot detection runs **before** the final sampling plan; sampling is planned per shot (F-1). | Guarantees ≥ 1 frame per shot and no samples straddling cuts. | Adopted |
| **AD-2** | Real FFmpeg adapters are built in Chunks 3–6, before orchestration. | Retires timestamp risk early; enables manual tests. | Adopted |
| **AD-3** | Add a thin developer CLI (`python -m scene_signal …`) built incrementally. | You asked to manually test. Not in spec; no new dependency (stdlib `argparse`). | Adopted |
| **AD-4** | Output schema additions to the illustrative example (all additive): `outcome`, `capabilities` report, `evidence_span`, strict `temporal_precision`, observation `scope`, `confidence_source`, shot `boundary_score` / `boundary_score_meaning` / `boundary_uncertainty_seconds` / `segment_kind`, media `display_width`/`display_height`/`start_time_offset_seconds`. | Closes gaps F-2 and F-5; prevents fabricated precision. | Adopted |
| **AD-5** | Partial results allowed by default: if deterministic stages succeed but a visual capability fails after bounded retries, return `outcome: "partial"` (never fabricated observations). Configurable (`allow_partial_results`). | Spec §11 allows partial results if the contract distinguishes them. | Adopted (true) |
| **AD-6** | Input contract additions: optional `provider_config_ref` (reference to secure config, never a key) and optional `rerun_of`. Unknown fields are **rejected** (`extra=forbid`). | Spec §6.2 requires a *reference* to secure config; `rerun_of` documents explicit reruns. | Adopted |
| **AD-7** | Context text (`source_prompt`, `global_prompt`) is **not** sent to the vision provider by default. | F-9: avoids hallucination from prompt bias. | Adopted (off) |
| **AD-8** | Identifiers: `SceneSignal/`, `scene_signal`, distribution `scene-signal`, CLI `python -m scene_signal`, env prefix `SCENE_SIGNAL_`, runtime folder `.scene_signal/`; module file `domain/timeline.py` instead of `domain/timeline.py`. | Addendum §1; packaging safety (N.2). | Adopted |
| **AD-9** | Greenfield workspace: you create the empty `SceneSignal/` folder and supply `<PARENT_DIR>`; Chunk 0 verifies location, runs `git init`, and creates `GEMINI.md`. Gemini never reads or touches anything above `SceneSignal/`. | Addendum §2; no guessed paths. | Adopted |
| **AD-10** | Integration boundary: SceneSignal's integration surface is the **versioned contract + exported JSON Schemas** (and the CLI/service entry points). The generation adapter lives **outside** `src/scene_signal`, is documented in C.7b, and is **not built** in Milestone 1. | Addendum §3, §5, §6. | Adopted |

## B.3 📎 SHARED — Reversible implementation defaults (recorded in `docs/decisions.md` by Chunk 0)

| ID | Default |
|---|---|
| D-01 | Internal time = integer microseconds (`TimeUs`); serialized as seconds rounded to 6 decimals using round-half-even. |
| D-02 | Fingerprint format `sha256:<64 hex>`; computed by streaming the whole local file. Supplied checksum is **always verified** (same format); mismatch is a permanent error. |
| D-03 | Job identity: `job_id` + request hash (sha256 of canonical JSON of the validated job, excluding `correlation_id`). |
| D-04 | Same `job_id` + same hash → idempotent (return stored result if terminal-success; re-execute if previously failed; error if running). Same `job_id` + different hash → `JOB_ID_CONFLICT`. Explicit rerun = **new** `job_id` (optionally `rerun_of`). |
| D-05 | Local repository layout `data_root/jobs/<job_id>/{request.json,status.json,result.json}` written atomically (temp file + rename). |
| D-06 | Synchronous core; API runs it in a thread pool. |
| D-07 | Adapters do not retry internally; the application `RetryPolicy` does. |
| D-08 | Frames are written as JPEG, display-oriented (rotation applied), long edge ≤ 1024 px. |
| D-09 | `confidence` is never calibrated in v1.0; always accompanied by `confidence_source`. |

---

# PART S — Consolidated Specification 01: SceneSignal (📎 SHARED)

> This document as a whole is the consolidated Specification 01. Part S restates the project-level requirements added or sharpened by Addendum 01. Everything else (scope, architecture, pipeline stages, contracts, errors, sampling, safeguards, testing, documentation, acceptance) is preserved in Parts B–D and Appendix 1.

## S.1 Identity and purpose

**SceneSignal** transforms raw video into structured, timestamped, evidence-grounded intelligence that can support automated video editing and production. *Turn video into timestamped editing intelligence.* Module 01 (Scene Intelligence Extraction) **describes** the video. It does not decide how the video should be edited.

## S.2 The five concerns (kept separate)

| Concern | Responsibility | In Milestone 1? | Interface to its neighbors |
|---|---|---|---|
| **Asset ingestion and preparation** | Makes an input asset accessible and establishes its technical properties (download, copy, transcode, move to shared storage). | **Only the minimum SceneSignal needs:** `AssetStoragePort` (access) + `MediaProbePort` (inspection). Upstream ingestion is **not** built. | An `asset_ref` the storage port can resolve |
| **SceneSignal extraction** | Analyzes accessible media and produces structured video intelligence. | **Yes — this project.** | In: `ExtractionJob`. Out: `JobResult` / `SceneIntelligenceDocument`. |
| **Generation integration** | Adapts outputs of the existing generation application into the SceneSignal input contract. | **No.** Documented boundary only (C.7b, Part G). | Produces `ExtractionJob` documents |
| **Future editing intelligence** | Decides how clips are selected, arranged, changed or regenerated, using extraction results. | **No.** | Consumes `SceneIntelligenceDocument` |
| **Future rendering and publishing** | Executes editing plans and prepares final outputs. | **No.** | Consumes editing plans |

## S.3 Integration boundary

```
 existing generation app ──(future adapter, outside SceneSignal core)──▶  ExtractionJob (JSON, versioned)
 user uploads ─────────────(future ingestion/prep, or manual in M1)────▶        │
 imported assets ──────────(future ingestion/prep, or manual in M1)────▶        ▼
                                                           SceneSignal core: validate → resolve → inspect → … → validate
                                                                               │
                                                                               ▼
                                                         SceneIntelligenceDocument (JSON, versioned) ──▶ future editing intelligence
```

| ID | Boundary rule (Addendum §3) |
|---|---|
| B-1 | The generation application can later submit an **asset reference and metadata** through a documented interface: the `ExtractionJob` contract (JSON), via the Python service, the CLI or the optional HTTP API. |
| B-2 | SceneSignal resolves and inspects the asset with **its own** abstractions (`AssetStoragePort`, `MediaProbePort`). |
| B-3 | The core never depends on the generation application's internal classes, database schema, filesystem layout, notebook implementation or framework objects. Contract fields are opaque strings and references (C-10). |
| B-4 | The same contract serves uploaded, imported and generated assets. `source_kind` is **provenance metadata only** and never changes pipeline behavior (C-11). |
| B-5 | A future adapter translates generation output into `ExtractionJob` **without any change** to domain or application code (C.7b). |
| B-6 | No shared database, runtime, deployment environment or storage backend is assumed. These are future integration decisions (Part G). |

## S.4 Minimum asset requirements and supported input constraints

| Aspect | Requirement / constraint |
|---|---|
| Accessibility | Resolvable through `AssetStoragePort`, readable, and unchanged for the duration of the job. **v1.0 adapter: local `file` scheme only** (other schemes are reserved and fail with `ASSET_SCHEME_UNSUPPORTED`). |
| Container and codec | Any container/codec that the installed FFmpeg/ffprobe can open **and** decode. Decided by **content**, never by file extension or MIME type. The validated set in fixtures: H.264/AAC in MP4, the same in Matroska, and an extensionless copy. |
| Video stream | At least one decodable video stream with positive duration and **more than one frame**. Still images (including image containers), audio-only files and cover-art-only files are rejected. If several video streams exist, the default-disposition stream (else the first) is analyzed and `MULTIPLE_VIDEO_STREAMS` is warned. |
| Audio stream | **Optional.** A missing audio stream never rejects a file. |
| Size, duration, dimensions | Policy limits in C.8 (configurable). |
| Declared technical metadata | **Not accepted by the contract.** Duration, frame rate, resolution, codecs, rotation and so on come only from inspection (Spec 01 §6.4). A supplied `checksum` is optional and, when present, is verified. |
| Unsupported in v1.0 | Network streams and playlists (HLS/DASH), image sequences, DRM/encrypted media, non-`file` schemes. Each fails with a typed error and an actionable message. |
| Immutability | The source is never modified. Everything produced is a derived artifact. |

## S.5 Validation order and failure semantics

| Step | Check | Failure code(s) | Result |
|---|---|---|---|
| 1 | Contract validation (no I/O performed yet) | `INVALID_JOB_CONTRACT`, `UNSUPPORTED_CONTRACT_VERSION` | `failed`, no document |
| 2 | Job claim / idempotency (only with a repository) | `JOB_ID_CONFLICT`, `JOB_IN_PROGRESS` | error or stored result |
| 3 | Asset resolution, size limit, checksum | `ASSET_SCHEME_UNSUPPORTED`, `ASSET_ACCESS_DENIED`, `ASSET_NOT_FOUND`, `MEDIA_LIMIT_EXCEEDED`, `CHECKSUM_MISMATCH` | `failed` |
| 4 | Media inspection | `MEDIA_INVALID_OR_CORRUPT`, `MEDIA_UNSUPPORTED_FORMAT`, `MEDIA_NO_VIDEO_STREAM`, `MEDIA_LIMIT_EXCEEDED`, `MEDIA_INSPECTION_FAILED` | `failed` |
| 5 | Shot detection | internal `SHOT_DETECTION_FAILED` | **degrades** to one `whole_asset` shot + warning + capability `failed` |
| 6 | Frame extraction | `FRAME_EXTRACTION_FAILED` | `failed` |
| 7 | Visual analysis | `PROVIDER_*` | retries (transient only), then `partial` (default) or `failed` per AD-5 |
| 8 | Output validation | `OUTPUT_VALIDATION_FAILED` | `failed` (never returned or persisted) |
| 9 | Persistence | `PERSISTENCE_FAILED` | bounded retry, then `failed` |

General rules: a failure in a deterministic stage (steps 1–4, 6) never produces a partial document; a provider failure never produces fabricated observations; temporary artifacts are always cleaned; retryable vs. permanent classes are in C.4.

## S.6 Manual development mode

Until upstream integration exists, SceneSignal is developed and tested with **hand-curated local assets** and **explicit, versioned job documents**:
- Fixtures are generated locally (Chunk 3) and your own videos can be added.
- Job documents live in `docs/examples/` and `tests/fixtures/jobs/`; `python -m scene_signal extract --job JOB.json` runs one.
- Production context, channel configuration and source prompts are optional; any valid video can be extracted without them.

## S.7 Traceability of original Specification 01

| Spec 01 | Where preserved |
|---|---|
| §1, §18, §19 (role, response order, stepwise approach) | This document's structure; E.0 rules |
| §2–§3 (context, objective) | Part S, Part C |
| §4.1–4.7 (fixed decisions) | B.1, B.1b |
| §5 (scope, exclusions) | B.1 and S.2 |
| §6 (input contract) | C.2, C.6 |
| §7 (inspection, timeline) | C.1 (C-05), C.3, Chunks 2–3 |
| §8 (ten pipeline stages) | Chunk 9 (AD-1 reorder explained in A.3) |
| §9 (output contract) | C.3, C.5, C.6 |
| §10 (ports) | C.7, C.7b |
| §11 (errors, retries, idempotency) | C.4, S.5, Chunk 10 |
| §12 (sampling, temporal accuracy) | C.8, Chunks 5–8, Part F |
| §13 (security) | C-09, Chunks 4 and 10, Part F |
| §14 (TDD, fixtures, fakes, contract tests) | Part D (tests per chunk), Chunk 12 |
| §15 (layout) | C.9 (re-rooted at `SceneSignal/`) |
| §16 (documentation, handoff) | Chunk 0 and every chunk's handoff update |
| §17 (acceptance) | Appendix 1 |

---

# PART C — Final contract proposal (📎 SHARED)

> Gemini: this Part is frozen once the Chief Engineer approves Part B. Do not rename fields, change enums or relax rules. If you think a rule is wrong, **stop and file a CONTRADICTION REPORT** (format in E.0).

## C.1 Conventions

| ID | Rule |
|---|---|
| C-01 | JSON, UTF-8. Pydantic v2 models, `extra="forbid"`, frozen. All modeled fields are serialized explicitly (nulls are written, never omitted). |
| C-02 | Versions are `"MAJOR.MINOR"` strings. This release: input `contract_version = "1.0"`, output `schema_version = "1.0"`. Unknown major → `UNSUPPORTED_CONTRACT_VERSION`. Minor greater than supported → `UNSUPPORTED_CONTRACT_VERSION`. Any contract change = version bump + entry in `docs/decisions.md` + test update. |
| C-03 | **External IDs** (`job_id`, `asset_id`, `production_id`, `scene_id`, `correlation_id`, `rerun_of`): regex `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` (these may become directory names; this also blocks path traversal). |
| C-04 | **Document-internal IDs**: `{prefix}-{n}`, `n` zero-padded to at least 3 digits: `shot-001`, `frame-001`, `obs-001`, `entity-001`, `event-001`. Unique within the document. Assigned by the assembler in deterministic order (C.5, V-20). |
| C-05 | **Time**: seconds (float ≥ 0), rounded to 6 decimals on output. Domain uses integer microseconds. Intervals are half-open `[start, end)` with `start < end` strictly. Instants use `timestamp_seconds`. Source-media time only; the origin (0.0) is the presentation time of the first video frame. |
| C-06 | **Evidence type**: `direct_observation` means *claimed by the analyzer as visible in the cited evidence frame(s)*; `inference` means *derived or interpreted*. Neither means "verified truth". |
| C-07 | **Confidence**: nullable float in `[0,1]`. If non-null, `confidence_source` is required: `model_self_reported`, `detector_score`, or `heuristic`. Never calibrated in v1.0. Downstream must not treat it as a probability. |
| C-08 | **Unknown vs. unsupported**: enum values `unknown` (attempted, not determinable) and `unsupported` (adapter/profile cannot determine this) exist where relevant. Never invent a value. |
| C-09 | Secrets never appear in requests, results, status, provenance or ordinary logs. Provider configuration is passed only as a reference name. |
| C-10 | **The contract is the integration boundary.** No field may carry generation-application internals (class names, database row semantics, notebook paths, framework objects). `production_id`, `scene_id`, `asset_id` and `job_id` are **opaque strings**. |
| C-11 | **`source_kind` is provenance only.** The same media with `generated`, `user_upload` or `imported` produces identical analysis (the documents differ only in `job.source_kind`, `request_hash` and timestamps). |

## C.2 `ExtractionJob` (input, `contract_version` "1.0")

**Required**

| Field | Type | Validation / notes |
|---|---|---|
| `contract_version` | string | `^\d+\.\d+$`; supported set `{"1.0"}` |
| `job_id` | string | C-03 |
| `asset_id` | string | C-03 |
| `source_kind` | enum | `generated` \| `user_upload` \| `imported` |
| `asset_ref` | `AssetRef` | see below |
| `extraction_profile` | enum | `quick` \| `standard` \| `thorough` |

**Optional** (all default `null`, except lists default `[]`)

| Field | Type | Notes |
|---|---|---|
| `production_id`, `scene_id`, `correlation_id` | string | C-03 |
| `order_index` | int ≥ 0 | position in production |
| `source_prompt`, `global_prompt` | string ≤ 8000 chars | context only; see AD-7 |
| `channel_context` | `ChannelContext` | all subfields optional: `channel_id`, `style_guidance`, `audience` (strings), `conventions` (list of strings). The module works with this `null`. |
| `language` | string | BCP-47 tag, e.g. `en`, `pt-BR` |
| `transcript_ref` | `AssetRef` | reference only; not a dependency |
| `related_assets` | list of `RelatedAsset` | `{asset_id, relation ∈ source_clip\|sibling\|derived_from, asset_ref?}` |
| `source_timeline` | `SourceTimeline` | `{segments: [{segment_id, start_seconds, end_seconds, order_index?, label?}]}`. **Hints only.** Never overrides detected shots; mismatches produce warnings. |
| `user_preferences_ref` | string | opaque reference |
| `requested_capabilities` | list of enum | `visual_observations`, `temporal_events`, `shot_detection`, `camera_analysis`, `visible_text`. Reserved (accepted, reported `unsupported`): `audio_transcript`, `embeddings`. Unknown strings → `INVALID_JOB_CONTRACT`. If omitted, defaults by profile (C.8). |
| `provider_config_ref` | string | name of secure provider configuration. **Never a key.** (AD-6) |
| `rerun_of` | string | C-03; informational (AD-6) |

**`AssetRef`**: `{scheme: "file", uri: string (non-empty), checksum: string|null}`. `scheme` is a string; v1 storage supports only `file`; other schemes → `ASSET_SCHEME_UNSUPPORTED` at resolve time. For `file`, `uri` is an absolute path or a path relative to a configured allowed root; it must resolve (after `realpath`) inside an allowed root. `checksum`, if present, must match `^sha256:[0-9a-f]{64}$`.

**Boundary notes** (Addendum §3–§4): the request deliberately has **no technical-metadata fields**; anything an upstream system knows about duration, resolution or codec is not accepted, because SceneSignal inspects the media itself. Production, scene, channel, prompt and generation context are optional hints. `uri` may be any string the storage port understands; v1.0 understands local files only.

**Validation outcomes**: malformed input → `INVALID_JOB_CONTRACT` with `details` listing field paths. Wrong version → `UNSUPPORTED_CONTRACT_VERSION`.

## C.3 `SceneIntelligenceDocument` (output, `schema_version` "1.0")

Top-level fields (all required unless stated):

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | "1.0" |
| `outcome` | enum | `complete` \| `partial` (a failed job has **no** document) |
| `job` | object | `{job_id, asset_id, source_kind, extraction_profile, production_id?, scene_id?, order_index?, correlation_id?, rerun_of?}` |
| `asset_fingerprint` | string | `sha256:<hex>` (nullable only if storage cannot supply one; then a warning is required) |
| `checksum_status` | enum | `verified` \| `not_supplied` |
| `media` | `MediaMetadata` | below |
| `timeline` | `TimelineMetadata` | below |
| `capabilities` | list of `CapabilityReport` | one entry for every capability in the request **and** every capability that was reserved/unsupported |
| `shots` | list of `Shot` | ≥ 1; tile `[0, duration)` |
| `frames` | list of `FrameRecord` | may be empty only if every shot is `skipped`/`failed` and warnings explain |
| `entities` | list of `Entity` | |
| `observations` | list of `Observation` | |
| `events` | list of `Event` | |
| `provenance` | `Provenance` | |
| `warnings` | list of `Warning` | |

**`MediaMetadata`**: `duration_seconds` (video-stream duration, falling back to container duration), `container_duration_seconds` (nullable), `width`, `height` (stored dimensions), `display_width`, `display_height` (after rotation and pixel aspect ratio), `rotation_degrees` ∈ {0,90,180,270} (clockwise as displayed), `pixel_aspect_ratio` (`"n:d"` or null), `has_video` (must be true), `has_audio`, `frame_rate` (float or null), `frame_rate_mode` ∈ `constant|variable|unknown`, `frame_count` (int or null), `video_codec`, `audio_codec` (nullable), `container_format`, `video_time_base` (`"n/d"` or null), `file_size_bytes`.

**`TimelineMetadata`**: `unit: "seconds"`, `interval_convention: "[start,end)"`, `precision_decimals: 6`, `timeline_kind: "source_media"`, `origin: "first_video_frame"`, `start_time_offset_seconds` (container offset removed; default 0.0), `source_time_base` (string or null).

**`CapabilityReport`**: `{capability, requested: bool, status ∈ completed|partial|unsupported|failed|not_requested, analysis_mode (nullable: still_frames|frame_sequence|video_clip|deterministic), limitations: [string], error_code: string|null}`.

**`Shot`** (a structural segment, **not** a narrative scene)

| Field | Notes |
|---|---|
| `id` | `shot-NNN` |
| `start_seconds`, `end_seconds` | `start < end`; contiguous with neighbors |
| `segment_kind` | `content` \| `black` |
| `boundary_method` | how the **start** boundary was determined: `initial_segment` \| `whole_asset` \| `ffmpeg_scene_score` \| `ffmpeg_blackdetect` \| `external` |
| `boundary_kind` | `asset_start` \| `hard_cut` \| `black_gap` \| `none` |
| `boundary_score` | float or null (detector score; **not** a probability) |
| `boundary_score_meaning` | string or null (e.g. "ffmpeg lavfi.scene_score, 0–1 frame difference") |
| `boundary_uncertainty_seconds` | float or null (at least one frame period when known) |
| `frame_ids` | list, sorted by time |
| `analysis_status` | `analyzed` \| `failed` \| `skipped` \| `not_requested` |
| `summary` | string or null (from the vision provider only; null if not analyzed) |
| `observation_ids`, `event_ids` | derived deterministically; must match each record's `shot_id` |

**`FrameRecord`**: `id`, `timestamp_seconds` (**actual** decoded presentation time), `requested_timestamp_seconds`, `timestamp_source` (`decoded_pts` \| `requested_unverified`), `pts` (int or null), `time_base` (string or null), `frame_index` (int or null; only when determinable), `shot_id`, `sampling_reason` (`shot_bin` \| `min_total_fill`), `width`, `height` (as written to the derived image), `artifact_ref` (string or null; only if artifacts are kept).

**`Entity`**: `id`, `type` (`person|animal|object|vehicle|text_element|place|other`), `label` (short noun phrase), `attributes` (list of strings), `identity_scope` (`frame|shot`; `asset` is **reserved** and only allowed if the adapter declares cross-shot linking and supplies link evidence), `tracking_method` (`none|provider_local_grouping`), `identity_notes` (string or null), `shot_ids`, `first_observed_seconds`, `last_observed_seconds` (sample timestamps where seen, **not** appearance/disappearance times), `observation_ids`.

**`Observation`**

| Field | Notes |
|---|---|
| `id` | `obs-NNN` |
| `category` | `object_presence` \| `action` \| `environment` \| `composition` \| `lighting` \| `style` \| `shot_size` \| `camera_angle` \| `camera_movement` \| `subject_movement` \| `visible_text` \| `visual_transition` \| `other` |
| `scope` | `frame` (single sample) \| `shot` (applies to the whole shot) \| `span` (adapter-reported interval) |
| `timestamp_seconds` | required iff `scope=frame` |
| `start_seconds`, `end_seconds` | required iff `scope ∈ {shot, span}`; for `shot` they must equal the shot's interval |
| `shot_id` | required |
| `description` | non-empty string |
| `value` | normalized enum string for `shot_size`, `camera_angle`, `camera_movement`; free text for `visible_text`; else null |
| `entity_ids` | list |
| `evidence_frame_ids` | ≥ 1 |
| `evidence_type` | `direct_observation` \| `inference` |
| `confidence`, `confidence_source` | C-07 |
| `limitations` | list of strings |

Normalized values — `shot_size`: `extreme_wide|wide|medium_wide|medium|medium_close|close_up|extreme_close_up|unknown`; `camera_angle`: `eye_level|high|low|overhead|dutch|unknown`; `camera_movement`: `static|pan_left|pan_right|tilt_up|tilt_down|zoom_in|zoom_out|dolly_in|dolly_out|tracking|handheld|complex|unknown|unsupported`.

**`Event`**

| Field | Notes |
|---|---|
| `id` | `event-NNN` |
| `type` | `movement|interaction|appearance|disappearance|state_change|transition|other` |
| `description` | non-empty |
| `shot_id` | required (events do not cross shots in v1.0) |
| `entity_ids` | list |
| `evidence_observation_ids` | ≥ 1 |
| `evidence_span` | `{first_seconds, last_seconds}`: earliest and latest supporting **sample** timestamps (`first ≤ last`) |
| `start_seconds`, `end_seconds` | both null or both set, `start < end` |
| `temporal_precision` | `single_sample_only` \| `multi_sample_span` \| `adapter_reported_interval` \| `frame_accurate` |
| `evidence_type`, `confidence`, `confidence_source`, `limitations` | as above |

Precision rules: `single_sample_only` ⇒ `first == last`, start/end null. `multi_sample_span` ⇒ `first < last`, start/end **null** (the action was *seen* during the span; its true bounds are unknown). `adapter_reported_interval` / `frame_accurate` ⇒ start/end set, only allowed when the adapter declares temporal capability.

**`Provenance`**: `job_id`, `asset_id`, `asset_fingerprint`, `contract_version`, `schema_version`, `extraction_profile`, `request_hash`, `sampling_strategy_version`, `sampling_parameters` (effective numbers), `media_probe` `{name, version}`, `frame_extractor` `{name, version}`, `shot_detector` `{name, version, parameters}`, `vision` `{provider, model, adapter_version, analysis_mode}` (all nullable if no vision ran), `started_at`, `completed_at` (UTC ISO-8601), `stage_attempts` (map stage → attempts used), `warning_count`. **No secrets, no credentials, no provider config values.**

**`Warning`**: `{code, message, stage, severity ∈ info|warning, related_ids: [string]}`. Codes used in v1.0: `VARIABLE_FRAME_RATE`, `ROTATION_APPLIED`, `PIXEL_ASPECT_APPLIED`, `START_TIME_OFFSET_APPLIED`, `TIMESTAMPS_SYNTHESIZED`, `DURATION_MISMATCH`, `TIMESTAMP_UNVERIFIED`, `SHOT_DETECTION_DEGRADED`, `GRADUAL_TRANSITIONS_NOT_DETECTED`, `CAPABILITY_UNSUPPORTED`, `PROVIDER_PARTIAL`, `PROVIDER_ITEM_DROPPED`, `FRAME_BUDGET_CAPPED`, `FRAME_BUDGET_EXCEEDED_BY_SHOTS`, `SOURCE_TIMELINE_MISMATCH`, `FINGERPRINT_UNAVAILABLE`, `MULTIPLE_VIDEO_STREAMS`.

## C.4 Result envelope, status and errors

**`JobResult`** (returned by the service): `{job_id, status ∈ succeeded|partial|failed, document: SceneIntelligenceDocument|null, error: ErrorInfo|null}`. `succeeded` ⇒ document with `outcome=complete`; `partial` ⇒ document with `outcome=partial`; `failed` ⇒ `error` set, `document` null.

**`JobStatusRecord`** (persisted): `{job_id, request_hash, status ∈ pending|running|succeeded|partial|failed, current_stage, attempt, created_at, updated_at, error: ErrorInfo|null}`.

**`ErrorInfo`**: `{code, message, retryable: bool, stage, attempts: int, details: object}`. `details` is sanitized: no secrets, no raw provider payloads, no media content.

| Code | Retryable | Notes |
|---|---|---|
| `INVALID_JOB_CONTRACT` | no | `details.fields` lists offending paths |
| `UNSUPPORTED_CONTRACT_VERSION` | no | |
| `JOB_ID_CONFLICT` | no | same `job_id`, different request hash |
| `JOB_IN_PROGRESS` | no (caller may retry later) | |
| `ASSET_SCHEME_UNSUPPORTED` | no | |
| `ASSET_NOT_FOUND` | no | |
| `ASSET_ACCESS_DENIED` | no | includes outside-allowed-roots and permission errors |
| `CHECKSUM_MISMATCH` | no | |
| `MEDIA_INVALID_OR_CORRUPT` | no | zero-byte, truncated, not media |
| `MEDIA_UNSUPPORTED_FORMAT` | no | unknown/undecodable codec or container; still images; non-video assets |
| `MEDIA_NO_VIDEO_STREAM` | no | audio-only is *not* valid for this module; a missing **audio** stream is fine |
| `MEDIA_LIMIT_EXCEEDED` | no | size / duration / dimension policy |
| `MEDIA_INSPECTION_FAILED` | only on timeout | ffprobe missing = permanent configuration error |
| `FRAME_EXTRACTION_FAILED` | only on timeout | |
| `SHOT_DETECTION_FAILED` | no | degrades to a single `whole_asset` shot + warning + capability `failed` (job continues) |
| `PROVIDER_TIMEOUT` | **yes** | |
| `PROVIDER_RATE_LIMITED` | **yes** | honors `retry_after` |
| `PROVIDER_UNAVAILABLE` | **yes** | |
| `PROVIDER_RESPONSE_INVALID` | limited | up to `invalid_response_retries` (default 1) |
| `PROVIDER_CONFIGURATION_ERROR` | no | unresolved/invalid `provider_config_ref` |
| `OUTPUT_VALIDATION_FAILED` | no | `details.violations` lists V-rule IDs |
| `PERSISTENCE_FAILED` | **yes** (bounded) | |
| `INTERNAL_ERROR` | no | |

## C.5 Validation invariants (enforced by `document_validator`, Chunk 8; structural ones also in schemas, Chunk 1)

| ID | Rule |
|---|---|
| V-01 | All IDs unique within their collection and follow C-04. |
| V-02 | `has_video` is true; `duration_seconds > 0`. |
| V-03 | Shots are sorted, `start < end`, first starts at 0.0, last ends at `duration_seconds`, each `end` equals the next `start` (tiling). |
| V-04 | Every frame: `0 ≤ timestamp < duration`, `shot_id` exists, timestamp lies inside that shot's `[start,end)`. |
| V-05 | Frames within a shot are sorted by time; `shot.frame_ids` matches frames whose `shot_id` is that shot. |
| V-06 | Observation `scope=frame` ⇒ `timestamp_seconds` present, start/end null, timestamp inside the shot; `scope=shot` ⇒ start/end equal the shot interval; `scope=span` ⇒ start/end set inside the shot, only if the adapter declared temporal capability. |
| V-07 | Every observation has ≥ 1 `evidence_frame_ids`, each existing and belonging to the observation's shot. |
| V-08 | All `entity_ids`, `observation_ids`, `event_ids`, `shot_id` references exist. Shot lists are consistent with record `shot_id`s. |
| V-09 | `confidence` in `[0,1]`; non-null ⇒ `confidence_source` present. |
| V-10 | `camera_movement` observation with any value other than `unknown`/`unsupported` requires: ≥ 2 evidence frames in the same shot (analysis mode `frame_sequence`; evidence_type must be `inference`) **or** analysis mode `video_clip`. Otherwise value must be `unsupported` (or `unknown`). Same guard for `subject_movement`. |
| V-11 | Event precision rules (C.3) are respected; `evidence_span.first ≤ last`; evidence span matches the min/max timestamp of its evidence observations. |
| V-12 | Events never reference observations from a different shot. |
| V-13 | Entity `identity_scope=asset` is invalid unless the adapter declared cross-shot linking. Entities in multiple shots without that declaration are invalid. |
| V-14 | Entity `first_observed ≤ last_observed`, and equal the min/max timestamps of their observations. |
| V-15 | `capabilities` contains an entry for every requested capability; `completed` is only allowed if no shot with `analysis_status=failed` exists for visual capabilities; `outcome=partial` iff at least one capability is `partial`/`failed` or any shot is `failed`/`skipped` for a requested capability. |
| V-16 | A shot with `analysis_status ∈ {failed, skipped, not_requested}` has no provider-derived observations, no summary, and no events. |
| V-17 | Provenance has every required field; no key matches the secret-like patterns (`key`, `token`, `secret`, `password`, `credential`, `authorization`) with a non-reference value. |
| V-18 | `timeline` fields equal the constants in C.3. |
| V-19 | `schema_version` is supported; `job` block matches the request. |
| V-20 | Deterministic ordering: shots by start; frames by timestamp; observations by (timestamp or start, shot, category, provider order); entities by first observed; events by `evidence_span.first`. IDs are assigned in that order. Same inputs + same provider output ⇒ identical document except `started_at`/`completed_at`. |

## C.6 Examples

### Minimal request

```json
{
  "contract_version": "1.0",
  "job_id": "extract-001",
  "asset_id": "asset-001",
  "source_kind": "generated",
  "asset_ref": {"scheme": "file", "uri": "clip_5s_landscape_audio.mp4", "checksum": null},
  "extraction_profile": "standard"
}
```

### Full request

```json
{
  "contract_version": "1.0",
  "job_id": "extract-002",
  "asset_id": "asset-002",
  "source_kind": "user_upload",
  "asset_ref": {"scheme": "file", "uri": "multishot_12s.mp4", "checksum": null},
  "extraction_profile": "thorough",
  "production_id": "production-001",
  "scene_id": "scene-003",
  "order_index": 3,
  "source_prompt": "A hiker walking through a misty forest",
  "global_prompt": null,
  "channel_context": null,
  "language": "en",
  "transcript_ref": null,
  "related_assets": [],
  "requested_capabilities": ["visual_observations", "temporal_events", "shot_detection", "camera_analysis"],
  "provider_config_ref": null,
  "correlation_id": "corr-77"
}
```

### Same boundary, any origin (Addendum §4)

These three requests differ **only** in `source_kind` and optional context; the pipeline treats them identically (C-11).

```json
{"contract_version": "1.0", "job_id": "gen-clip-0007", "asset_id": "asset-0007", "source_kind": "generated",
 "asset_ref": {"scheme": "file", "uri": "clip_5s_landscape_audio.mp4", "checksum": null},
 "extraction_profile": "standard", "production_id": "production-001", "scene_id": "scene-007", "order_index": 7,
 "source_prompt": "A hiker walking through a misty forest"}
```
```json
{"contract_version": "1.0", "job_id": "upload-0001", "asset_id": "asset-0008", "source_kind": "user_upload",
 "asset_ref": {"scheme": "file", "uri": "clip_5s_landscape_audio.mp4", "checksum": null},
 "extraction_profile": "standard"}
```
```json
{"contract_version": "1.0", "job_id": "import-0001", "asset_id": "asset-0009", "source_kind": "imported",
 "asset_ref": {"scheme": "file", "uri": "clip_5s_matroska.mkv", "checksum": null},
 "extraction_profile": "quick", "language": "en"}
```

### Result example (single shot, still-image adapter) — structurally valid per C.5

```json
{
  "schema_version": "1.0",
  "outcome": "partial",
  "job": {"job_id": "extract-001", "asset_id": "asset-001", "source_kind": "generated",
          "extraction_profile": "standard", "production_id": null, "scene_id": null,
          "order_index": null, "correlation_id": null, "rerun_of": null},
  "asset_fingerprint": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "checksum_status": "not_supplied",
  "media": {"duration_seconds": 5.0, "container_duration_seconds": 5.0, "width": 1280, "height": 720,
            "display_width": 1280, "display_height": 720, "rotation_degrees": 0,
            "pixel_aspect_ratio": "1:1", "has_video": true, "has_audio": false,
            "frame_rate": 24.0, "frame_rate_mode": "constant", "frame_count": 120,
            "video_codec": "h264", "audio_codec": null,
            "container_format": "mov,mp4,m4a,3gp,3g2,mj2", "video_time_base": "1/12288",
            "file_size_bytes": 123456},
  "timeline": {"unit": "seconds", "interval_convention": "[start,end)", "precision_decimals": 6,
               "timeline_kind": "source_media", "origin": "first_video_frame",
               "start_time_offset_seconds": 0.0, "source_time_base": "1/12288"},
  "capabilities": [
    {"capability": "shot_detection", "requested": true, "status": "completed", "analysis_mode": "deterministic",
     "limitations": ["Detects hard cuts and black gaps only; gradual transitions are not detected."], "error_code": null},
    {"capability": "visual_observations", "requested": true, "status": "completed", "analysis_mode": "still_frames",
     "limitations": [], "error_code": null},
    {"capability": "temporal_events", "requested": true, "status": "partial", "analysis_mode": "still_frames",
     "limitations": ["Events are inferred from sampled stills; start and end times are not established."], "error_code": null},
    {"capability": "camera_analysis", "requested": true, "status": "partial", "analysis_mode": "still_frames",
     "limitations": ["Shot size and angle estimated from stills; camera movement cannot be established from stills."], "error_code": null},
    {"capability": "visible_text", "requested": false, "status": "not_requested", "analysis_mode": null,
     "limitations": [], "error_code": null}
  ],
  "shots": [
    {"id": "shot-001", "start_seconds": 0.0, "end_seconds": 5.0, "segment_kind": "content",
     "boundary_method": "initial_segment", "boundary_kind": "asset_start", "boundary_score": null,
     "boundary_score_meaning": null, "boundary_uncertainty_seconds": null,
     "frame_ids": ["frame-001", "frame-002", "frame-003"], "analysis_status": "analyzed",
     "summary": "A person with a backpack walks through a misty forest.",
     "observation_ids": ["obs-001", "obs-002", "obs-003", "obs-004", "obs-005", "obs-006"],
     "event_ids": ["event-001"]}
  ],
  "frames": [
    {"id": "frame-001", "timestamp_seconds": 0.833333, "requested_timestamp_seconds": 0.833333,
     "timestamp_source": "decoded_pts", "pts": 10240, "time_base": "1/12288", "frame_index": 20,
     "shot_id": "shot-001", "sampling_reason": "shot_bin", "width": 1024, "height": 576, "artifact_ref": null},
    {"id": "frame-002", "timestamp_seconds": 2.5, "requested_timestamp_seconds": 2.5,
     "timestamp_source": "decoded_pts", "pts": 30720, "time_base": "1/12288", "frame_index": 60,
     "shot_id": "shot-001", "sampling_reason": "shot_bin", "width": 1024, "height": 576, "artifact_ref": null},
    {"id": "frame-003", "timestamp_seconds": 4.166667, "requested_timestamp_seconds": 4.166667,
     "timestamp_source": "decoded_pts", "pts": 51200, "time_base": "1/12288", "frame_index": 100,
     "shot_id": "shot-001", "sampling_reason": "shot_bin", "width": 1024, "height": 576, "artifact_ref": null}
  ],
  "entities": [
    {"id": "entity-001", "type": "person", "label": "hiker", "attributes": ["wearing a backpack"],
     "identity_scope": "shot", "tracking_method": "provider_local_grouping", "identity_notes": null,
     "shot_ids": ["shot-001"], "first_observed_seconds": 0.833333, "last_observed_seconds": 4.166667,
     "observation_ids": ["obs-001", "obs-003", "obs-004"]}
  ],
  "observations": [
    {"id": "obs-001", "category": "object_presence", "scope": "frame", "timestamp_seconds": 0.833333,
     "start_seconds": null, "end_seconds": null, "shot_id": "shot-001",
     "description": "A person wearing a backpack is visible among trees.", "value": null,
     "entity_ids": ["entity-001"], "evidence_frame_ids": ["frame-001"], "evidence_type": "direct_observation",
     "confidence": null, "confidence_source": null, "limitations": []},
    {"id": "obs-002", "category": "environment", "scope": "shot", "timestamp_seconds": null,
     "start_seconds": 0.0, "end_seconds": 5.0, "shot_id": "shot-001",
     "description": "Misty forest with tall trees.", "value": null, "entity_ids": [],
     "evidence_frame_ids": ["frame-001", "frame-002", "frame-003"], "evidence_type": "direct_observation",
     "confidence": null, "confidence_source": null, "limitations": []},
    {"id": "obs-003", "category": "action", "scope": "frame", "timestamp_seconds": 2.5,
     "start_seconds": null, "end_seconds": null, "shot_id": "shot-001",
     "description": "The person appears to be walking along a path.", "value": null,
     "entity_ids": ["entity-001"], "evidence_frame_ids": ["frame-002"], "evidence_type": "inference",
     "confidence": 0.7, "confidence_source": "model_self_reported",
     "limitations": ["Motion inferred from a single still frame."]},
    {"id": "obs-004", "category": "action", "scope": "frame", "timestamp_seconds": 4.166667,
     "start_seconds": null, "end_seconds": null, "shot_id": "shot-001",
     "description": "The person appears to be walking along a path.", "value": null,
     "entity_ids": ["entity-001"], "evidence_frame_ids": ["frame-003"], "evidence_type": "inference",
     "confidence": null, "confidence_source": null,
     "limitations": ["Motion inferred from a single still frame."]},
    {"id": "obs-005", "category": "shot_size", "scope": "shot", "timestamp_seconds": null,
     "start_seconds": 0.0, "end_seconds": 5.0, "shot_id": "shot-001",
     "description": "Wide framing showing the subject small within the environment.", "value": "wide",
     "entity_ids": [], "evidence_frame_ids": ["frame-001", "frame-002"], "evidence_type": "direct_observation",
     "confidence": null, "confidence_source": null, "limitations": []},
    {"id": "obs-006", "category": "camera_movement", "scope": "shot", "timestamp_seconds": null,
     "start_seconds": 0.0, "end_seconds": 5.0, "shot_id": "shot-001",
     "description": "Camera movement cannot be established from still frames.", "value": "unsupported",
     "entity_ids": [], "evidence_frame_ids": ["frame-001", "frame-002", "frame-003"],
     "evidence_type": "inference", "confidence": null, "confidence_source": null,
     "limitations": ["Still-frame analysis cannot establish camera movement."]}
  ],
  "events": [
    {"id": "event-001", "type": "movement", "description": "The person appears to be walking.",
     "shot_id": "shot-001", "entity_ids": ["entity-001"],
     "evidence_observation_ids": ["obs-003", "obs-004"],
     "evidence_span": {"first_seconds": 2.5, "last_seconds": 4.166667},
     "start_seconds": null, "end_seconds": null, "temporal_precision": "multi_sample_span",
     "evidence_type": "inference", "confidence": null, "confidence_source": null,
     "limitations": ["Seen in two samples; true start and end are unknown."]}
  ],
  "provenance": {
    "job_id": "extract-001", "asset_id": "asset-001",
    "asset_fingerprint": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "contract_version": "1.0", "schema_version": "1.0", "extraction_profile": "standard",
    "request_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    "sampling_strategy_version": "1.0",
    "sampling_parameters": {"target_interval_seconds": 2.0, "min_frames_total": 3, "max_frames_total": 32,
                            "min_frames_per_shot": 1},
    "media_probe": {"name": "ffprobe", "version": "unknown"},
    "frame_extractor": {"name": "ffmpeg", "version": "unknown"},
    "shot_detector": {"name": "ffmpeg_scene_score+blackdetect", "version": "1.0",
                      "parameters": {"scene_threshold": 0.30, "black_min_duration": 0.2}},
    "vision": {"provider": "example-provider", "model": "example-model", "adapter_version": "1.0",
               "analysis_mode": "still_frames"},
    "started_at": "2026-10-12T10:00:00Z", "completed_at": "2026-10-12T10:00:05Z",
    "stage_attempts": {"analyze": 1}, "warning_count": 1
  },
  "warnings": [
    {"code": "CAPABILITY_UNSUPPORTED", "message": "Camera movement is not supported by a still-frame adapter.",
     "stage": "analyze", "severity": "info", "related_ids": ["obs-006"]}
  ]
}
```

*(The example deliberately does not claim that walking started or ended at a specific time.)*

## C.7 Ports (signatures — Python `typing.Protocol`, synchronous)

```python
# ports/media_probe.py
class MediaProbePort(Protocol):
    def inspect(self, local_path: Path) -> MediaInspection: ...   # raises MediaError subclasses

# ports/asset_storage.py
class AssetStoragePort(Protocol):
    def resolve(self, ref: AssetRef) -> ResolvedAsset: ...        # verifies checksum if supplied; computes fingerprint
    def open_workspace(self, job_id: str) -> Workspace: ...       # context manager; cleans up per policy

class ResolvedAsset:  # fingerprint, size_bytes, checksum_status; local_path() context manager
    ...

# ports/frame_extraction.py
class FrameExtractionPort(Protocol):
    def extract(self, local_path: Path, media: MediaInspection, requests: Sequence[FrameRequest],
                workspace: Workspace, max_long_edge: int) -> list[ExtractedFrame]: ...

# ports/shot_detection.py
class ShotDetectionPort(Protocol):
    def detect(self, local_path: Path, media: MediaInspection, params: ShotDetectionParams) -> ShotDetectionResult: ...

# ports/visual_analysis.py
class VisualAnalysisPort(Protocol):
    def capabilities(self) -> VisionCapabilities: ...
    def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse: ...  # raises ProviderError subclasses

# ports/repository.py
class ExtractionRepositoryPort(Protocol):
    def claim_job(self, job: ExtractionJob, request_hash: str) -> ClaimResult: ...
    def update_status(self, record: JobStatusRecord) -> None: ...
    def save_result(self, job_id: str, result: JobResult) -> None: ...
    def load_status(self, job_id: str) -> JobStatusRecord | None: ...
    def load_result(self, job_id: str) -> JobResult | None: ...
```

`VisionCapabilities`: `provider`, `model`, `adapter_version`, `supported_modes` (subset of `still_frames|frame_sequence|video_clip`), `supported_analyses` (subset of the five capabilities), `max_frames_per_call`, `max_image_long_edge`, `supports_temporal_intervals` (bool), `supports_cross_shot_identity` (bool), `default_timeout_seconds`.

`VisionAnalysisRequest`: `batch_id`, `shot_ref`, `mode`, `frames` (list of `{frame_ref, timestamp_us, image handle, width, height}`), `requested_analyses`, `context_hints` (null unless the Chunk-9 policy allows it), `timeout_seconds`.

`VisionAnalysisResponse` (provider-local, **untrusted**): `observations` (local ids, category, description, `frame_refs`, `value`, `confidence`, `confidence_source`, `evidence_type`, `entity_local_ids`, `limitations`), `entities` (local ids, type, label, attributes, `frame_refs`), `events` (type, description, `observation_local_ids`, optional `start_us`/`end_us`), `shot_summary`, `notes`. The application validates and maps it to canonical records; **adapters never assign canonical IDs**.

Errors raised by ports derive from `ExtractionError` carrying `code`, `retryable`, `retry_after_seconds` (optional).

## C.7b Integration boundary: generation adapter (documented, **NOT implemented in Milestone 1**)

```python
# NOT part of src/scene_signal. Lives in the generation application's side, or in a separate integration package.
class GenerationAssetAdapter(Protocol):
    def to_extraction_job(self, generation_output: Mapping[str, Any]) -> dict:
        """Return a dict that validates as ExtractionJob (contract_version "1.0")."""
```

Rules: the adapter depends on the **published contract/JSON Schemas** of SceneSignal, never the reverse; SceneSignal's core never imports an adapter; swapping or changing the adapter requires no change in `domain`, `application` or `ports`. Transport (Python call, CLI, HTTP, file drop) is a future decision (Part G).

Illustrative mapping (field names on the generation side are **unknown and must be confirmed in the integration phase**):

| Generation-side concept | `ExtractionJob` field | Note |
|---|---|---|
| A generated clip's location | `asset_ref` | Must be resolvable by a SceneSignal storage adapter (shared path, object-store URI, or an upload step done upstream) |
| Clip/scene identifier | `asset_id`, `scene_id` | Opaque strings |
| Production / video project identifier | `production_id` | Opaque |
| Position of the clip in the production | `order_index` | |
| Prompt used to generate the clip | `source_prompt` | Context only (AD-7) |
| Overall production brief | `global_prompt` | Context only |
| A unique id for this extraction request | `job_id` | Adapter-generated, deterministic per clip to enable idempotent retries |
| Anything channel-related | `channel_context` | Optional |
| (nothing) | `source_kind` | Always `generated` |

## C.8 Defaults (configurable; recorded in `config/settings`)

**Profiles**

| Profile | Default capabilities | `target_interval_s` | `min_frames_total` | `max_frames_total` | `min_frames_per_shot` |
|---|---|---|---|---|---|
| `quick` | `shot_detection`, `visual_observations` | 4.0 | 3 | 12 | 1 |
| `standard` | + `temporal_events`, `camera_analysis` | 2.0 | 3 | 32 | 1 |
| `thorough` | + `visible_text` | 1.0 | 5 | 96 | 2 |

Absolute frame ceiling: 256 (shots beyond it become `skipped` with warning).

**Sampling strategy v1.0 (`bin_center_per_shot`)**: for each shot of length *L*: `n = max(min_frames_per_shot, ceil(L / target_interval))`; place samples at bin centers `s + (k + 0.5) * L / n`. If the total exceeds `max_frames_total`, reduce proportionally (largest-remainder, ties by shot order) keeping ≥ 1 per shot (warn `FRAME_BUDGET_CAPPED`; if shots alone exceed the cap, keep 1 per shot and warn `FRAME_BUDGET_EXCEEDED_BY_SHOTS`). If the total is below `min_frames_total`, split the longest bins deterministically. Examples (standard): 3 s → 3 frames at 0.5, 1.5, 2.5; 5 s → 3 frames at 0.833333, 2.5, 4.166667; 30 s → 15 frames; 90 s → 32 frames (capped).

**Limits and timeouts**: `max_file_bytes` 2 GiB; `max_duration_seconds` 1800; `max_dimension` 8192; probe timeout 30 s; frame-extraction timeout 20 s per frame; shot-detection timeout `max(60, 2 × duration)` s; vision call timeout 60 s; job deadline 900 s.

**Retry**: `max_attempts` 3 (total tries), base delay 1.0 s, max delay 20 s, full jitter, honors `retry_after`; `invalid_response_retries` 1; persistence retry 3 attempts, base 0.2 s.

**Shots**: `scene_threshold` 0.30; `min_shot_seconds` 0.25; black detect `min_duration` 0.2 s, `pix_th` 0.10; detection runs on frames downscaled to width 320 for speed.

**Vision**: `max_frames_per_call` 8; `image_max_long_edge` 1024; `include_context_in_analysis` false.

**Other**: `allow_partial_results` true; `keep_artifacts` false; `allowed_asset_roots` empty by default (must be configured; the CLI adds the asset's folder explicitly because it is a trusted local tool).

## C.9 Independent project structure and dependency boundaries

Created incrementally by the chunks (no empty folders). Root is `SceneSignal/`.

```
SceneSignal/
├── GEMINI.md                    # SceneSignal's own AI instructions (Chunk 0)
├── pyproject.toml   README.md   .gitignore   .env.example
├── scripts/                     # make_fixtures.py, make_job_documents.py, manual_smoke.py
├── src/scene_signal/
│   ├── __init__.py, __main__.py, cli.py
│   ├── domain/                  # timeline.py, ids.py, errors.py, policies.py, evidence.py, canonical.py
│   ├── schemas/                 # common.py, job.py, result.py, versions.py, export.py
│   ├── ports/                   # one file per port
│   ├── application/             # sampling.py, shots.py, provider_response.py, assembler.py,
│   │                            # document_validator.py, provenance.py, retry.py, pipeline.py, service.py
│   ├── adapters/
│   │   ├── media/               # ffprobe.py, ffmpeg_frames.py, ffmpeg_shots.py
│   │   ├── storage/             # local_fs.py, local_repository.py
│   │   └── fakes/               # fake_media_probe.py, fake_frames.py, fake_shots.py, fake_vision.py, ...
│   ├── config/                  # settings.py
│   └── api/                     # app.py (optional extra)
├── tests/{unit,contract,integration}/  + fixtures/{manifest.json, jobs/}
└── docs/                        # SPEC-01-scenesignal.md, architecture.md, input-contract.md, output-contract.md,
                                 # integration-boundary.md, testing.md, decisions.md, handoff.md,
                                 # vision-adapter-guide.md, acceptance.md, examples/, schemas/
```

**Dependency boundaries (enforced by the architecture test)**

| From → may import | Rule |
|---|---|
| `schemas` | pydantic and stdlib only |
| `domain` | `schemas`, stdlib |
| `ports` | `domain`, `schemas`, stdlib |
| `application` | `ports`, `domain`, `schemas`, stdlib |
| `adapters` | `ports`, `domain`, `schemas`, third-party libraries needed by that adapter |
| `api`, `cli` | `application`, `adapters`, `config`, FastAPI (only in `api`) |
| **Everything** | **never** imports the generation application, its notebook, or any module not declared in `pyproject.toml`; no module is named like a stdlib module; no absolute paths are hard-coded |
| External systems | The generation application (or any other client) depends on SceneSignal only through the contract, exported JSON Schemas, CLI or HTTP API; SceneSignal never depends on them. |

---

# PART D — Dependency-ordered implementation plan

## D.0 🧑 FOR YOU — Overview

| Chunk | Title | Depends on | Size | You can manually test? |
|---|---|---|---|---|
| **Pre-flight** | Choose parent directory, collision checks, create empty `SceneSignal/` (D.0b) | — | S | **You do this yourself** |
| 0 | Greenfield verification, scaffold, AI instructions, handoff state, architecture test | Pre-flight | S | Yes (install, run tests) |
| 1 | Contracts, typed errors, validation CLI, integration-boundary doc | 0 | M | Yes (validate JSON files) |
| 2 | Domain primitives: time, IDs, policies, evidence rules | 1 | M | Yes (tests + one-liners) |
| 3 | Media inspection (port, fake, ffprobe) + fixture generator | 2 | L | **Yes** (`inspect` on real clips) |
| 4 | Local asset storage + frame extraction | 3 | L | **Yes** (`extract-frames`, view images) |
| 5 | Sampling planner (pure) | 2 | M | Yes (`plan-sampling`) |
| 6 | Shot detection + shot builder | 3, 5 | L | **Yes** (`detect-shots`) |
| 7 | Visual-analysis port, fake provider, response validation | 2 | M | Yes (tests) |
| 8 | Assembler, document validator, provenance | 2, 5, 6, 7 | L | Yes (tests + validate output) |
| 9 | Orchestration (stateless pipeline) and explicit job documents | 3–8 | L | **Yes** (`extract --job` end-to-end) |
| 10 | Errors, retries, partial results, idempotency, persistence | 9 | L | **Yes** (failure injection, reruns) |
| 11 | CLI completion and optional FastAPI | 10 | M | **Yes** (curl / browser) |
| 12 | Contract tests, ground truth, docs, independence drill, acceptance sign-off | 11 | M | **Yes** (smoke script) |

Chunk 5 only depends on Chunk 2, so it can run any time after it; the order above is the recommended one.

**Common manual-test setup (after Chunk 0), 🧑 FOR YOU** — always from inside `SceneSignal/`:
```
cd <PARENT_DIR>/SceneSignal      # Windows: cd <PARENT_DIR>\SceneSignal
python -m venv .venv             # only if Chunk 0 did not already create it
# activate it (see Section 0), then:
pip install -e ".[dev]"
pytest -q
```

## D.0b 🧑 FOR YOU — Pre-flight (required before Chunk 0; I do not guess absolute paths)

1. **Choose `<PARENT_DIR>`**: an absolute path of a folder that already exists and that is **not** the generation application's folder or inside it. (Examples of the *kind* of path: `~/projects` or `D:\projects`. These are illustrations, not assumptions.)
2. **Run the collision checks** in N.2 (target folder absent; parent not inside another Git repo; no `scene_signal` module in the generation app's environment).
3. **Create the empty project folders yourself** (this doubles as the collision check, because `mkdir` fails if the folder exists):
   - macOS / Linux: `mkdir "<PARENT_DIR>/SceneSignal"` then `mkdir "<PARENT_DIR>/SceneSignal/docs"`
   - Windows PowerShell: `New-Item -ItemType Directory "<PARENT_DIR>\SceneSignal"` then `New-Item -ItemType Directory "<PARENT_DIR>\SceneSignal\docs"`
4. **Copy this file** to `<PARENT_DIR>/SceneSignal/docs/SPEC-01-scenesignal.md`.
5. **Start Gemini CLI with `SceneSignal/` as the working directory** (`cd` into it first). Do not add the generation application's folder to Gemini's workspace or allowed directories.
6. In the Chunk 0 prompt (E.1), replace the placeholder `<PARENT_DIR>` with the same path.

If you are unsure about any step, tell me what the generation application's folder is called and where it lives and I will propose a parent directory. I will still not run or assume anything on your filesystem.

---

## Chunk 0 — Greenfield verification, scaffold, AI instructions, handoff state, architecture test

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- **Greenfield checks first** (stop and report on any failure; make no changes before they pass): (a) the current directory's name is `SceneSignal` and its parent equals the `<PARENT_DIR>` given in the prompt; (b) the directory contains only `docs/SPEC-01-scenesignal.md` (plus harmless OS files); (c) the directory is **not** inside any existing Git repository (`git rev-parse --show-toplevel` must fail); (d) you will not list, read, write or search anything outside this directory. Print the evidence (`pwd`, listing, git result).
- `git init` (default branch `main`, **no** remote, **no** commit unless the user asks).
- `GEMINI.md` at the root: project identity (SceneSignal, Module 01), the greenfield rules G-01…G-09, TDD, the dependency rule, pointers to `docs/SPEC-01-scenesignal.md`, `docs/handoff.md` and `docs/decisions.md`, and a condensed version of the Standing Rules.
- `pyproject.toml`: distribution `scene-signal`, `hatchling`, `src/` layout, `requires-python >=3.11`, dependency `pydantic>=2.6,<3`; extras `dev` (`pytest`, `ruff`, `jsonschema`, `mypy` optional) and `api` (`fastapi`, `uvicorn`, `httpx`). `pytest` with `--strict-markers` and markers `requires_ffmpeg`, `contract`, `integration` (network/credentials only). `ruff` configuration.
- `.env.example` documenting every `SCENE_SIGNAL_*` variable that exists so far (none required; **no secrets, no real values**). `.gitignore` (venv, caches, `.env`, `.scene_signal/`, `tests/fixtures/media/`, `__pycache__`).
- Package: `src/scene_signal/{__init__.py (with __version__ = "0.1.0"), __main__.py, cli.py (argparse with a subcommand registry; only --version for now), py.typed}`. **No empty placeholder subpackages.**
- `tests/conftest.py`: auto-skip `requires_ffmpeg` tests when `ffmpeg`/`ffprobe` are missing from PATH (skip reason shown).
- `tests/unit/test_architecture.py`: AST-scan modules under `domain/`, `application/`, `ports/`, `schemas/`; fail on imports of `fastapi`, `uvicorn`, `httpx`, anything under `adapters`/`api`, or known provider SDKs (`openai`, `anthropic`, `google`, `boto3`). Also fail if **any** module file under `src/scene_signal` is named like a stdlib top-level module (`sys.stdlib_module_names`). Include self-tests with temporary fake packages proving both checks detect violations.
- Docs: `README.md` (short), `docs/architecture.md` (layers, dependency table from C.9, ports from C.7), `docs/decisions.md` (record AD-1…AD-10 as approved, N-01…N-08, D-01…D-09), `docs/testing.md`, `docs/integration-boundary.md` (skeleton: purpose, B-1…B-6, C.7b), `docs/handoff.md` (template in E.0b; "Next chunk: 1").
- Name-collision proof inside the new virtualenv: before installing, `python -c "import importlib.util as u; print(u.find_spec('scene_signal'))"` prints `None`; after `pip install -e ".[dev]"`, `scene_signal.__file__` resolves inside `SceneSignal/src/`.

**Out of scope:** any contract, domain or adapter code; any file outside this directory; the generation application in any form.

**Tests to write first**
1. Package imports and `__version__` is a non-empty string.
2. `python -m scene_signal --version` prints the version, exit code 0.
3. `requires_ffmpeg` skip behavior (monkeypatch `shutil.which`).
4. Architecture checker: forbidden-import self-test and stdlib-shadow self-test both detect violations; the real package passes.

**Acceptance criteria**
- Greenfield checks passed and evidence printed; `git init` done; own `GEMINI.md`, `.env.example`, handoff and decisions files exist.
- `pip install -e ".[dev]"` succeeds; `pytest -q`, `ruff check .`, `ruff format --check .` pass; `python -m scene_signal --version` works.
- Nothing exists or changed outside `SceneSignal/`.

**Completion evidence:** the greenfield evidence block, exact command outputs for the commands above, list of created files.

### 🧑 FOR YOU — Review and manual test

1. In the terminal: `pwd` (Windows: `Get-Location`) → ends with `.../SceneSignal`. `git rev-parse --show-toplevel` → prints **that same** `SceneSignal` path (it is its own repository). `git status` → shows untracked files, no commits.
2. Run the common setup (D.0). `pytest -q` ends green (≈ 6 tests; exact count may vary). `ruff check .` passes.
3. `python -m scene_signal --version` → `0.1.0`.
4. `python -c "import scene_signal; print(scene_signal.__file__)"` → a path **inside** `SceneSignal/src/scene_signal/`.
5. Open `GEMINI.md`, `docs/handoff.md` (must say Chunk 0 complete and **Next chunk: 1**) and `docs/decisions.md` (AD-1…AD-10, N-01…N-08, D-01…D-09 listed).
6. **Isolation check:** if the generation application is a Git repository, run `git status` there → **clean**. Nothing new should exist in `<PARENT_DIR>` except `SceneSignal/`. If anything outside `SceneSignal/` changed, stop and tell me.
7. Optional: make your own first commit (`git add -A && git commit -m "Chunk 0"`). Gemini will not do it for you.

---

## Chunk 1 — Contracts, typed errors, validation CLI, integration-boundary doc

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `domain/errors.py`: `ExtractionError` base (`code`, `message`, `retryable`, `stage`, `details`, `retry_after_seconds`) and one subclass per code in C.4. A single `ErrorCode` string enum. No logic beyond data.
- `schemas/common.py`, `schemas/job.py`, `schemas/result.py`, `schemas/versions.py`: Pydantic v2 models exactly as in C.2–C.4 (including `JobResult`, `JobStatusRecord`, `ErrorInfo`). Intra-record validators only (structural rules): ID patterns, regexes, enum values, `start < end`, null-or-both, scope/timestamp consistency, confidence/source pairing, event precision rules, `extra=forbid`.
- `schemas/versions.py`: `check_contract_version(str)`; unknown major/greater minor → `UnsupportedContractVersionError`.
- `parse_extraction_job(raw: str | bytes | dict) -> ExtractionJob`: maps Pydantic validation errors to `InvalidJobContractError` with `details.fields` = list of dotted paths.
- `schemas/export.py`: deterministic JSON Schema export (sorted keys) for `ExtractionJob` and `SceneIntelligenceDocument`.
- CLI subcommands: `validate-request FILE`, `validate-result FILE`, `export-schemas --out DIR`. Success prints `OK` (exit 0). Failure prints a JSON error object with `code` and `details.fields` and exits with code 2.
- `docs/examples/`: `request.minimal.json`, `request.full.json` (C.6), `request.generated.json`, `request.user_upload.json`, `request.imported.json` (the three "same boundary, any origin" examples in C.6), `request.invalid_source_kind.json`, `result.valid.json` (C.6 example, with a sample real-looking fingerprint), `result.invalid_event_precision.json` (event with `multi_sample_span` and non-null `start_seconds`).
- Docs: `docs/input-contract.md` (including the **asset requirements** S.4 and **validation/failure semantics** S.5), `docs/output-contract.md` (explain every field in plain language, referencing C.2–C.5), `docs/integration-boundary.md` (complete: B-1…B-6, C-10, C-11, C.7b mapping table marked "to be confirmed", how a future client validates against the exported JSON Schemas), update `docs/decisions.md`, `docs/handoff.md`.

**Out of scope:** cross-document reference checks (V-03…V-20 beyond intra-record) — Chunk 8.

**Tests to write first** (all in `tests/unit/schemas/`)
- Minimal request valid; full request valid; `generated`, `user_upload` and `imported` example requests all validate and are structurally identical apart from `source_kind` and optional context (C-11). A request with no production, scene, channel or prompt context validates.
- The request model has **no technical-metadata fields** (no duration, resolution, codec, frame rate) and no field named after generation-application internals (C-10).
- Missing each required field → `INVALID_JOB_CONTRACT` with that path.
- Unknown `source_kind`, `extraction_profile`, `requested_capabilities` entry → invalid; reserved capabilities (`audio_transcript`, `embeddings`) → accepted.
- Extra/unknown field rejected (including a field named `api_key`).
- ID patterns: `../x`, `a/b`, empty, 129 chars rejected; `extract-001` accepted.
- `contract_version`: `"2.0"` and `"1.1"` → `UNSUPPORTED_CONTRACT_VERSION`; `"abc"` → invalid contract.
- `asset_ref`: empty uri rejected; checksum must match `sha256:` + 64 hex; null accepted; scheme other than file is **accepted by the schema** (rejected later by storage).
- `order_index` negative rejected; `channel_context` null OK; `channel_context` with all subfields null OK.
- `source_timeline` segment with `end <= start` rejected.
- Result: shot with `end <= start`; observation with `scope=frame` but no timestamp; `scope=shot` without start/end; non-null `confidence` without `confidence_source`; `confidence` 1.2; event `single_sample_only` with `first != last`; `multi_sample_span` with start set; `adapter_reported_interval` with start null; unknown enum values → each rejected.
- JSON round trip (`model_dump_json` → parse) equals the original for both examples.
- Exported JSON Schemas are deterministic (two exports byte-identical) and both examples validate against them using `jsonschema`.
- No model field name matches a secret-like pattern (`api_key`, `token`, `secret`, `password`, `authorization`).

**Acceptance criteria**
- One canonical versioned request and one canonical versioned result contract exist (C-02).
- All tests pass; CLI behaves as specified; docs updated.

**Completion evidence:** red run, then green run output; CLI transcript for the five example files.

### 🧑 FOR YOU — Review and manual test

From the module folder with the venv active:

1. `python -m scene_signal validate-request docs/examples/request.minimal.json` → `OK`.
2. `python -m scene_signal validate-request docs/examples/request.full.json` → `OK`. Then the three origins: `request.generated.json`, `request.user_upload.json`, `request.imported.json` → each `OK`. Open them side by side: they should differ only in `source_kind` and optional context.
3. `python -m scene_signal validate-request docs/examples/request.invalid_source_kind.json` → JSON error with `"code": "INVALID_JOB_CONTRACT"` and a field path mentioning `source_kind`; exit code non-zero (`echo $?` / `echo $LASTEXITCODE`).
4. `python -m scene_signal validate-result docs/examples/result.valid.json` → `OK`.
5. `python -m scene_signal validate-result docs/examples/result.invalid_event_precision.json` → error mentioning the event's precision rule.
6. **Your own mutations** (copy a file, edit by hand): set `"contract_version": "2.0"` → `UNSUPPORTED_CONTRACT_VERSION`; add `"api_key": "x"` → rejected; set `job_id` to `"../etc"` → rejected; set `channel_context` to `null` and delete `production_id` → still valid.
7. `python -m scene_signal export-schemas --out docs/schemas` creates two `.json` schema files. Run it twice: files are identical (`git diff` shows no change).
8. Read `docs/output-contract.md`: can you understand every field without reading code? If not, tell me what is unclear.
9. Read `docs/integration-boundary.md`: could the owner of the generation application build a client from it **without ever seeing SceneSignal's code**? If not, tell me what is missing.

---

## Chunk 2 — Domain primitives: time, IDs, policies, evidence rules

### 🤖 FOR GEMINI — Implementation spec

**Scope** (pure Python, no I/O)
- `domain/timeline.py`: `TimeUs` (integer microseconds, non-negative, comparable); constructors `from_seconds_decimal(str|Decimal)`, `from_pts(pts:int, time_base:Fraction|"n/d")`, `from_float_seconds(float)` (round-half-even at 1 µs); `to_seconds()` → float rounded to 6 decimals; `Interval(start: TimeUs, end: TimeUs)` with `start < end`, `contains(t)` (half-open), `overlaps`, `is_adjacent_to`, `duration`; `tile_check(intervals, total)`; helper `snap_to_nearest(t, candidates)`.
- `domain/ids.py`: `IdAllocator(prefix)` → `shot-001` …, widening beyond 999 (`shot-1000`).
- `domain/policies.py`: frozen dataclasses for the C.8 defaults: `SamplingProfile`, `RetryPolicy`, `LimitsPolicy`, `ShotPolicy`, `VisionPolicy`, and `Settings` (loaded from env vars with prefix `SCENE_SIGNAL_` and optional TOML file; validation of ranges; no secrets).
- `domain/evidence.py`: pure rules used later by the assembler: `camera_movement_allowed(value, mode, evidence_frame_count, same_shot)`, `allowed_event_precision(mode, supports_temporal_intervals)`, `observation_scope_allowed(...)` implementing V-06, V-10, V-11, V-13.
- `domain/canonical.py`: `canonical_json(obj)` (sorted keys, no whitespace variance, floats normalized) and `request_hash(job)` = `sha256:` of canonical JSON of the validated job excluding `correlation_id`.

**Out of scope:** any ffmpeg/ffprobe handling, any use of the schemas beyond importing them.

**Tests to write first** (`tests/unit/domain/`)
- Exact conversions: pts 30030 at `1/30000` → 1.001 s; pts 450450 at `1/90000` → 5.005 s; `"5.005000"` → 5_005_000 µs; `1/3` seconds → 333_333 µs (half-even rule shown with a tie case such as 0.0000005 s → 0 µs and 0.0000015 s → 2 µs).
- Precision: 0.041708 s survives round trip (no rounding to whole or tenth seconds); `to_seconds()` never returns more than 6 decimals.
- Negative times rejected; `Interval` rejects `start >= end`; `contains` honors `[start,end)` (start in, end out); adjacency; overlap; `tile_check` passes for contiguous tiling and fails for gap/overlap/short coverage.
- `IdAllocator` ordering and widening.
- `canonical_json` independent of key order; `request_hash` identical when only `correlation_id` differs; different when `asset_ref.uri` differs.
- Settings: defaults equal C.8; env override works; invalid values (negative timeout, `max_attempts=0`) rejected; no field holds a secret.
- Evidence rules: camera movement from a single still → only `unsupported`/`unknown` allowed; ≥ 2 frames same shot in `frame_sequence` → allowed only as inference; `video_clip` → allowed; event precision `adapter_reported_interval` rejected for still-only adapters; `identity_scope=asset` rejected without cross-shot capability.

**Acceptance criteria:** timeline conversion and timestamp precision have dedicated tests; all pass; docs (`architecture.md` timeline section, `decisions.md`, `handoff.md`) updated; architecture test still green.

**Completion evidence:** red/green runs.

### 🧑 FOR YOU — Review and manual test

1. `pytest tests/unit/domain -v` → all pass; scan the test names: they should read like the list above.
2. One-liners (should print the shown values):
   - `python -c "from fractions import Fraction; from scene_signal.domain.timeline import TimeUs; print(TimeUs.from_pts(30030, Fraction(1,30000)).to_seconds())"` → `1.001`
   - `python -c "from scene_signal.domain.timeline import TimeUs; print(TimeUs.from_seconds_decimal('0.041708').to_seconds())"` → `0.041708`
   - `python -c "from scene_signal.domain.timeline import TimeUs, Interval; i=Interval(TimeUs.from_seconds_decimal('1'),TimeUs.from_seconds_decimal('2')); print(i.contains(TimeUs.from_seconds_decimal('1')), i.contains(TimeUs.from_seconds_decimal('2')))"` → `True False`
   (If Gemini named a function differently, ask it for the equivalent command; the **values** must match.)
3. `SCENE_SIGNAL_MAX_ATTEMPTS=5 python -c "from scene_signal.domain.policies import Settings; print(Settings.load().retry.max_attempts)"` → `5` (on Windows PowerShell: `$env:SCENE_SIGNAL_MAX_ATTEMPTS=5` first). If Gemini used a different variable name, check `docs/decisions.md`.

---

## Chunk 3 — Media inspection: port, fake, ffprobe adapter, fixture generator

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `ports/media_probe.py`: `MediaProbePort`, `MediaInspection` (frozen dataclass mirroring C.3 `MediaMetadata` plus `start_time_us`, `warnings`, and `probe_name`/`probe_version`). The probe returns technical metadata only (fingerprint is storage's job — F-10).
- `adapters/media/ffprobe.py`: subprocess with an **argument list** (never `shell=True`), timeout from settings, JSON output. Obtain streams and format via `-show_format -show_streams -of json`. Detect VFR with a **packet scan** of the first video stream (`-show_entries packet=pts_time,duration_time` in a compact output format): sort by pts (B-frames reorder), compute inter-packet deltas, classify `constant` if the spread is within a tolerance (document the tolerance), `variable` otherwise, `unknown` if too few packets. Cap the scan by a policy limit for very long files.
- Normalization rules: duration from the video stream, falling back to the format duration (record both; warn `DURATION_MISMATCH` if they differ by more than 0.1 s); rotation from the display-matrix side data (ffprobe reports a sign-inverted rotation; normalize to clockwise ∈ {0,90,180,270}) with fallback to a legacy `rotate` tag; `display_width/height` swap for 90/270 and apply sample aspect ratio first; `start_time_us` from the video stream; missing pts → synthesize and warn `TIMESTAMPS_SYNTHESIZED`; parse decimal strings with `Decimal`/`Fraction` (never float).
- Error mapping: zero-byte, unreadable header, truncated MP4 without index → `MEDIA_INVALID_OR_CORRUPT`; no video stream → `MEDIA_NO_VIDEO_STREAM`; codec unknown/undecodable → `MEDIA_UNSUPPORTED_FORMAT`; limits exceeded → `MEDIA_LIMIT_EXCEEDED`; ffprobe missing → `MEDIA_INSPECTION_FAILED` (non-retryable, message says ffprobe not found); probe timeout → `MEDIA_INSPECTION_FAILED` with `retryable=true`. A file with **no audio** is valid. **Content-based validation:** the container and codec are decided by ffprobe output, never by extension or MIME type; still images (an image container, or a "video" stream with a single frame or no duration) → `MEDIA_UNSUPPORTED_FORMAT`; attached pictures (cover art) are not video streams; if several video streams exist, use the default-disposition one (else the first) and warn `MULTIPLE_VIDEO_STREAMS`.
- `adapters/fakes/fake_media_probe.py`: returns configured `MediaInspection` objects keyed by path or by a default; can simulate each error code.
- `scripts/make_fixtures.py` + `tests/fixtures/manifest.json` (see the fixture table below). Generated media goes to `tests/fixtures/media/` (git-ignored). Generation uses FFmpeg `lavfi` synthetic sources only (no downloads). The script prints a table of what was created and **fails loudly** (non-zero exit) for fixtures it could not produce, except the two marked "best effort", which are recorded as `unavailable` in the manifest with the reason.
- Shared contract test suite `tests/contract/test_media_probe_contract.py` parameterized over fake and ffprobe adapters (ffprobe variant marked `requires_ffmpeg`).
- CLI: `inspect FILE` prints the `MediaInspection` as JSON.
- Docs: `docs/testing.md` fixture section (purpose and limitations of each fixture), `decisions.md`, `handoff.md`.

**Fixture set (generated locally)**

| File | Content | Purpose |
|---|---|---|
| `clip_3s_landscape_noaudio.mp4` | 1280×720, 24 fps, 3 s, no audio | short clip, no-audio validity |
| `clip_5s_landscape_audio.mp4` | 1280×720, 24 fps, 5 s, 440 Hz tone | audio present |
| `clip_30s_continuous.mp4` | 640×360, 30 fps, 30 s | medium clip, one continuous shot |
| `clip_90s_continuous.mp4` | 320×180, 15 fps, 90 s | long clip |
| `clip_portrait_5s.mp4` | 720×1280, 24 fps, 5 s | portrait |
| `rotated_90_5s.mp4` | stored 640×360 with 90° display rotation metadata | rotation handling (best effort if the installed FFmpeg cannot write the matrix; then recorded `unavailable`) |
| `multishot_12s.mp4` | 4 × 3 s visually distinct synthetic segments, 640×360, 24 fps; cuts at 3.0, 6.0, 9.0 s | shot detection ground truth |
| `black_transition_9s.mp4` | 4 s pattern → 1 s black → 4 s pattern; black gap [4.0, 5.0) | black-frame detection |
| `vfr_6s.mp4` | irregular frame timestamps | variable frame rate (best effort) |
| `corrupt_truncated.mp4` | first ~40 % of `clip_5s_landscape_audio.mp4` | corrupt media |
| `zero_byte.mp4` | empty file | zero-byte |
| `not_a_video.mp4` | plain text with .mp4 name | malformed input |
| `audio_only.m4a` | 3 s tone, no video | missing video stream |
| `still_image.png` | a single generated image | still images are **not** video (`MEDIA_UNSUPPORTED_FORMAT`) |
| `clip_5s_matroska.mkv` | the 5 s clip re-muxed into Matroska (`-c copy`) | proves the pipeline is not MP4-only |
| `clip_5s_no_extension` | byte-for-byte copy of the 5 s clip with **no** file extension | format is decided by content, not extension |

The manifest lists, per fixture: expected duration (± tolerance), dimensions, display dimensions, has_audio, expected frame-rate mode, expected shot boundaries with tolerance (± 0.10 s default), black intervals, and notes.

**Out of scope:** hashing/fingerprints (Chunk 4), frame extraction.

**Tests to write first**
- Fake probe: returns configured results; raises each typed error on demand.
- Content-based validation: `clip_5s_matroska.mkv` and `clip_5s_no_extension` inspect successfully with the same duration and dimensions as the MP4; `still_image.png` → `MEDIA_UNSUPPORTED_FORMAT`; canned ffprobe JSON with an attached-picture stream and with two video streams behave as specified above.
- Contract suite (both adapters): audio-less file valid with `has_audio=false`; durations within manifest tolerance for 3/5/30/90 s; stored vs. display dimensions for portrait and rotated; zero-byte → `MEDIA_INVALID_OR_CORRUPT`; truncated → `MEDIA_INVALID_OR_CORRUPT`; text file → `MEDIA_INVALID_OR_CORRUPT`; audio-only → `MEDIA_NO_VIDEO_STREAM`; non-existent path is **not** the probe's concern (storage handles it) but must not crash with an unclassified exception; VFR fixture → `variable` (or recorded unavailable); CFR fixtures → `constant`.
- Parsing unit tests with canned ffprobe JSON (no FFmpeg needed): rotation sign normalization, SAR application, missing duration fallback, missing pts warning, codec unknown → unsupported.
- Timeout test with a fake runner (injectable subprocess runner) → retryable `MEDIA_INSPECTION_FAILED`.

**Acceptance criteria:** pipeline can inspect actual media rather than trusting supplied metadata; short and long clips handled without assumptions about duration; typed failures for invalid media; all tests pass (FFmpeg-dependent ones pass on a machine with FFmpeg, auto-skip otherwise — report which).

**Completion evidence:** test summary showing counts of passed/skipped; `make_fixtures.py` output table; `inspect` output for two fixtures.

### 🧑 FOR YOU — Review and manual test

Requires FFmpeg (`ffmpeg -version`).

1. `python scripts/make_fixtures.py` → prints a table; all fixtures `created` except possibly `rotated_90_5s` / `vfr_6s` which may say `unavailable` with a reason (acceptable, but tell me which).
2. Open `tests/fixtures/media/multishot_12s.mp4` in any video player: you should see **four visually different segments**, 3 seconds each. Open `black_transition_9s.mp4`: a black second in the middle.
3. Run each and compare with the expected values:

| Command (`python -m scene_signal inspect tests/fixtures/media/<file>`) | Expect |
|---|---|
| `clip_5s_landscape_audio.mp4` | duration ≈ 5.0, 1280×720, `has_audio: true`, frame rate 24, mode `constant` |
| `clip_3s_landscape_noaudio.mp4` | duration ≈ 3.0, `has_audio: false`, **no error** |
| `clip_portrait_5s.mp4` | width 720, height 1280, rotation 0 |
| `rotated_90_5s.mp4` | stored 640×360, `rotation_degrees: 90`, display 360×640 |
| `clip_90s_continuous.mp4` | duration ≈ 90.0 |
| `zero_byte.mp4` | error `MEDIA_INVALID_OR_CORRUPT` |
| `corrupt_truncated.mp4` | error `MEDIA_INVALID_OR_CORRUPT` |
| `not_a_video.mp4` | error `MEDIA_INVALID_OR_CORRUPT` |
| `audio_only.m4a` | error `MEDIA_NO_VIDEO_STREAM` |
| `still_image.png` | error `MEDIA_UNSUPPORTED_FORMAT` |
| `clip_5s_matroska.mkv` | same duration/dimensions as the MP4, container mentions `matroska` |
| `clip_5s_no_extension` | works exactly like the MP4 (**not** an error) |

4. `pytest -q -m requires_ffmpeg` → passes. Rename ffmpeg temporarily off your PATH and run `pytest -q` → FFmpeg tests show as **skipped**, others pass.
5. Try one of your own real videos (e.g. phone clip): inspect should show sensible duration and dimensions; a phone portrait video usually shows rotation 90 or 270 with swapped display dimensions.

---

## Chunk 4 — Local asset storage and frame extraction

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `ports/asset_storage.py`: `AssetStoragePort`, `ResolvedAsset`, `Workspace` (per C.7).
- `adapters/storage/local_fs.py`: `scheme=file` only. Allowed roots from settings; resolve relative URIs against the first allowed root; `realpath` both sides so `..` and symlinks cannot escape; accept `file://` URI forms and plain paths (including Windows drive paths). Errors: not found → `ASSET_NOT_FOUND`; outside roots / permission denied → `ASSET_ACCESS_DENIED`; other scheme → `ASSET_SCHEME_UNSUPPORTED`; size limit → `MEDIA_LIMIT_EXCEEDED`. **Always** stream-hash the file (sha256) to produce the fingerprint; if a checksum was supplied, compare and raise `CHECKSUM_MISMATCH` on difference; set `checksum_status`.
- `Workspace`: temp directory under `work_root/<job_id>/`; context manager; removes everything on exit unless `keep_artifacts=true`; removes on exceptions as well.
- `ports/frame_extraction.py`: `FrameRequest(planned_time_us)`, `ExtractedFrame(path, requested_us, actual_us, pts, time_base, frame_index|None, width, height, timestamp_source)`; `FrameExtractionPort.extract(...)`.
- `adapters/media/ffmpeg_frames.py`: one FFmpeg invocation per requested timestamp using input seeking, a single JPEG per request (`-q:v 3`), autorotation applied (display-oriented output), downscale so the long edge ≤ `max_long_edge` (never upscale), subprocess with argument list, per-frame timeout. Obtain the **actual** frame timestamp by parsing the `showinfo` filter's `pts_time` (preserving source timestamps, e.g. `-copyts`, or adding the seek offset — **verify empirically** against the ffprobe packet/frame timestamps and document the chosen approach in `decisions.md`). If the actual time cannot be verified: `timestamp_source=requested_unverified` and a `TIMESTAMP_UNVERIFIED` warning. For CFR media, also report `frame_index`; for VFR, `frame_index=None`.
- `adapters/fakes/fake_frames.py`: writes tiny placeholder images (or in-memory handles) at exactly the requested timestamps; configurable failures.
- CLI: `extract-frames FILE --times 0.5,1.5,2.5 --out DIR [--long-edge 1024]` (CLI adds the file's folder as an allowed root; prints a table of requested vs. actual times and image sizes).
- Contract tests for both ports (storage: local only; frames: fake + ffmpeg).
- Docs: `decisions.md` (timestamp approach), `testing.md`, `handoff.md`.

**Out of scope:** sampling decisions, shot detection.

**Tests to write first**
- Storage: relative and absolute paths inside the root OK; `../` escape → denied; a symlink pointing outside the root → denied (skip on platforms without symlink rights, say so); missing file → not found; unreadable file → denied (skip where impossible); `https://…` → scheme unsupported; supplied checksum correct → `verified`; wrong → `CHECKSUM_MISMATCH`; fingerprint equals `hashlib.sha256` of the file; file bytes and mtime unchanged after resolve + extraction (**source immutability**); size limit enforced.
- Workspace: directory exists inside the context, is gone after normal exit **and** after an exception; `keep_artifacts=true` retains.
- Frames (ffmpeg, `requires_ffmpeg`): requested times 0.5/1.5/2.5 on the 3 s clip produce 3 JPEGs; actual timestamp within one frame period of requested on CFR fixtures and **equal to a real frame timestamp** from an independent ffprobe frame table; portrait and rotated fixtures produce display-oriented images (dimensions match display dimensions after scaling); long-edge downscale; time ≥ duration or negative → typed error; unreadable input → `FRAME_EXTRACTION_FAILED`; two runs on the same input yield the same set of actual timestamps.
- Fake: returns exactly the requested times.

**Acceptance criteria:** frames are extracted at recorded timestamps; source immutable; derived artifacts cleaned according to policy; contract tests pass for fake and ffmpeg adapters.

**Completion evidence:** test summary; a short note on the verified timestamp approach and any FFmpeg version observations.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal extract-frames tests/fixtures/media/clip_5s_landscape_audio.mp4 --times 0.5,2.5,4.5 --out /tmp/frames` (Windows: use any folder such as `out_frames`). Expect 3 JPEG files, and a table where "actual" is within ~0.05 s of "requested".
2. **Look at the images.** They should show the numbered/animated test pattern at different moments (the pattern's clock/counter changes between images).
3. `... extract-frames tests/fixtures/media/clip_portrait_5s.mp4 --times 1,3 --out out_portrait` → images are **tall** (portrait).
4. `... extract-frames tests/fixtures/media/rotated_90_5s.mp4 --times 1 --out out_rot` (if that fixture exists) → image is **tall** (display orientation), not wide.
5. `... extract-frames tests/fixtures/media/clip_5s_landscape_audio.mp4 --times 99 --out x` → typed error, no crash.
6. Check the original fixture is untouched: its size/date unchanged (`ls -l` / `dir`).
7. Confirm no leftover work folder under `.scene_signal/work` after the run (unless you used a keep option).

---

## Chunk 5 — Sampling planner (pure)

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `application/sampling.py`: `plan_sampling(duration_us, shots: Sequence[Interval], profile: SamplingProfile) -> SamplingPlan` implementing strategy `bin_center_per_shot` v1.0 exactly as in C.8. `SamplingPlan`: `strategy_version="1.0"`, effective parameters, `samples` (planned time, shot index, reason `shot_bin`|`min_total_fill`), `warnings` (`FRAME_BUDGET_CAPPED`, `FRAME_BUDGET_EXCEEDED_BY_SHOTS`). Deterministic; no randomness; no I/O.
- Absolute ceiling handling (shots beyond the ceiling marked skipped in the plan).
- CLI: `plan-sampling --duration 90 --profile standard [--shots 0,12.5,40]` (shots given as start times; the final shot ends at the duration). Prints the plan as a table and JSON.
- Docs: `docs/architecture.md` sampling section; `decisions.md`; `handoff.md`.

**Out of scope:** extracting frames; detecting shots.

**Tests to write first**
- Exact expected samples for: 3 s / 5 s / 30 s / 90 s single shot at `quick`, `standard`, `thorough` (assert counts and exact times, e.g. standard 3 s → 0.5, 1.5, 2.5; standard 5 s → 0.833333, 2.5, 4.166667).
- Multi-shot (4 × 3 s) → at least one sample inside each shot; every sample strictly inside its shot `[start,end)`; no sample at `t ≥ duration`.
- Budget: 90 s standard capped to 32; cap keeps ≥ 1 per shot; > cap shots → 1 per shot with `FRAME_BUDGET_EXCEEDED_BY_SHOTS`; > ceiling → skipped shots.
- Minimum total frames honored on very short clips (e.g. 0.4 s clip → `min_frames_total` or physically possible count, documented).
- Determinism: same input → identical plan (compare serialized plans); sorted by time.
- Parametrized sweep over durations 0.2 … 600 s asserting invariants (sorted, in-range, unique, within budget unless the warning is present).
- Configurability: a custom profile changes the plan; strategy version is recorded.

**Acceptance criteria:** sampling is configurable and independently testable; short clips are not over-sampled; long clips do not exceed the budget; all pass.

**Completion evidence:** test summary; CLI output for 3, 5, 30, 90 s.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal plan-sampling --duration 3 --profile standard` → 3 samples at 0.5, 1.5, 2.5.
2. `... --duration 5 --profile standard` → 3 samples (≈ 0.833, 2.5, 4.167).
3. `... --duration 90 --profile standard` → **32** samples, evenly spread, with a `FRAME_BUDGET_CAPPED` warning.
4. `... --duration 90 --profile thorough` → up to 90 samples; `... --duration 90 --profile quick` → 12.
5. `... --duration 12 --profile standard --shots 0,3,6,9` → 8 samples, two in each 3-second shot, none exactly on 3.0 / 6.0 / 9.0.
6. Judge: for a 5-second clip, are 3 frames enough? If you want denser sampling, tell me; it is a one-line profile default (C.8).

---

## Chunk 6 — Shot detection and shot builder

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `ports/shot_detection.py`: `ShotDetectionPort.detect(...)` returning `ShotDetectionResult{boundaries: [BoundaryCandidate{time_us, kind (hard_cut|black_gap_start|black_gap_end), score|None, score_meaning, uncertainty_us}], black_intervals, method_name, method_version, parameters, limitations}`.
- `adapters/media/ffmpeg_shots.py`: deterministic FFmpeg-based detection: scene score via the `select`/scene-score metadata output (frames downscaled to width 320 for speed), threshold from settings; plus `blackdetect` for black gaps. The boundary time is the timestamp of the **first frame of the new shot**; `uncertainty_us` is at least one frame period when known. Timeouts per settings. Always report limitations: "hard cuts and black gaps only; gradual transitions not detected".
- `adapters/fakes/fake_shots.py`: configured boundaries; failure injection.
- `application/shots.py`: `build_shots(result, media_duration_us, policy, requested: bool) -> (list[ShotDraft], warnings)` — pure. Sorts, de-duplicates, merges boundaries closer than `min_shot_seconds`, converts black intervals to `segment_kind=black` shots, merges a scene cut that falls within tolerance of a black-gap edge into that edge, guarantees tiling of `[0,duration)`, first shot `initial_segment`/`asset_start`; if detection was not requested → single `whole_asset` shot (`analysis_status` decided later); on `SHOT_DETECTION_FAILED` → single `whole_asset` shot + warning `SHOT_DETECTION_DEGRADED` + capability `failed`. Always adds `GRADUAL_TRANSITIONS_NOT_DETECTED` info when detection ran.
- CLI: `detect-shots FILE [--threshold 0.30]` prints boundaries and the resulting shot list.
- Ground-truth tests read expected boundaries and tolerances from `tests/fixtures/manifest.json`.
- Docs: `decisions.md` (threshold rationale, measured behavior), `testing.md` (ground-truth tolerance explanation), `handoff.md`.

**Out of scope:** semantic scene grouping (a shot is not a scene), gradual transition detection, multi-detector ensembles.

**Tests to write first**
- `build_shots` (pure): tiling for 0/1/3 boundaries; closeness merge; black interval → black shot with correct neighbors; scene cut near a black edge deduplicated; unsorted/duplicate input; boundary at 0 or at duration ignored; not-requested → whole asset; failure → degraded single shot.
- Fake detector through `build_shots`.
- FFmpeg ground truth (`requires_ffmpeg`): `clip_*_continuous` → **zero** cuts at the default threshold; `multishot_12s` → exactly 3 cuts within the manifest tolerance of 3.0/6.0/9.0; `black_transition_9s` → black interval [4.0, 5.0) within tolerance and shots content/black/content; detector failure on corrupt input → `SHOT_DETECTION_FAILED`.
- If a continuous fixture produces false cuts at the default threshold, **do not tune thresholds per fixture to pass**: report the finding in the Completion Report with the measured scores and propose a justified default.
- Distinguish exact tests (tiling arithmetic) from approximate ones (detected times with tolerance); name them accordingly.

**Acceptance criteria:** detected shots/segments have valid intervals tiling the media; shots are not described as narrative scenes; limitations documented; all pass.

**Completion evidence:** test summary; measured boundary times for the three fixtures.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal detect-shots tests/fixtures/media/multishot_12s.mp4` → 4 shots; boundaries ≈ **3.0, 6.0, 9.0** (±0.1).
2. `... detect-shots tests/fixtures/media/clip_30s_continuous.mp4` → **1 shot**, 0.0–30.0.
3. `... detect-shots tests/fixtures/media/black_transition_9s.mp4` → 3 shots: content [0,4), **black** [4,5), content [5,9).
4. `... detect-shots tests/fixtures/media/multishot_12s.mp4 --threshold 0.95` → fewer or zero cuts (shows the threshold matters); `--threshold 0.05` → possibly extra cuts. Note what happens and tell me if the default 0.30 feels wrong on your own videos.
5. **Your real videos matter here:** run `detect-shots` on one real edited clip you know the cuts of (e.g. a short ad). Compare with what you see. Fades/dissolves will be **missed by design**; tell me what you observe.
6. Confirm the output says "gradual transitions not detected" somewhere (limitations).

---

## Chunk 7 — Visual-analysis port, fake provider, provider-response validation

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `ports/visual_analysis.py`: `VisualAnalysisPort`, `VisionCapabilities`, `VisionMode` enum, `VisionAnalysisRequest`, `VisionAnalysisResponse` and raw record types exactly as C.7. Document timeouts and error semantics in the docstrings (adapters raise typed `ProviderTimeout`, `ProviderRateLimited(retry_after)`, `ProviderUnavailable`, `ProviderResponseInvalid`, `ProviderConfigurationError`; **no hidden retries**).
- `application/provider_response.py`: `negotiate(requested_capabilities, caps, available_mode) -> NegotiationResult` (which capabilities are supported, which are `unsupported` with limitation text; chooses the analysis mode per shot: `video_clip` > `frame_sequence` > `still_frames` according to capabilities and frame count) and `validate_response(request, response, caps) -> ValidatedResponse` (untrusted-data validation: unknown `frame_refs` → invalid; empty descriptions dropped; unknown categories dropped with warning `PROVIDER_ITEM_DROPPED`; confidence out of range dropped to null; camera/subject movement from a single still coerced to `unsupported`; event times ignored unless `supports_temporal_intervals`; structurally malformed payload → `ProviderResponseInvalid`).
- `adapters/fakes/fake_vision.py`: deterministic fake (`provider="fake"`, `model="fake-1"`). Constructor options: `mode` (`still_frames|frame_sequence|video_clip`), `supported_analyses`, `fail_with` script (per call: timeout, rate_limit(retry_after), unavailable, invalid_response, malformed JSON, partial), `latency` via an injectable sleeper, and deterministic content: per frame one `object_presence` observation `"[FAKE] frame frame-003 at 1.500s"`, one `environment` shot-level observation, one entity `"fake subject"` grouped within the batch, a `shot_size` observation, a `camera_movement=unsupported` observation for still mode, one `movement` event across ≥ 2 frames (`multi_sample_span` semantics) when `temporal_events` supported.
- `tests/contract/test_vision_port_contract.py`: behavior suite any `VisualAnalysisPort` must satisfy, parameterized over fake variants, and an env-driven hook (`SCENE_SIGNAL_VISION_ADAPTER=module:factory`) for future real adapters, marked `integration` and **skipped** by default.
- `docs/vision-adapter-guide.md` (how to write a real adapter, what the contract tests require, the "no hidden retries" rule, secrets by reference).
- Docs: `decisions.md`, `handoff.md`.

**Out of scope:** any real provider adapter; assembling the canonical document.

**Tests to write first**
- Negotiation matrix: still-only adapter requested all five capabilities → camera movement and events marked partial/unsupported with limitation texts; sequence adapter allows inference; video adapter allows all; unsupported capability never silently "completed".
- Response validation: each corruption case (unknown frame ref, empty description, bad category, confidence 7, movement from one still, forged event times on a still-only adapter, missing required key, wrong types) behaves as listed above.
- Fake behaviors: deterministic output (twice = identical), each injected failure raises the right typed error with `retryable` and `retry_after`, slow provider honors the timeout via the injectable sleeper/clock.
- Contract suite passes for every fake variant; capabilities are self-consistent.

**Acceptance criteria:** the application can be tested without real vision calls; provider output is treated as untrusted; capability limits are explicit; all pass.

**Completion evidence:** test summary.

### 🧑 FOR YOU — Review and manual test

No new CLI. Verify by reading and running tests:
1. `pytest tests/unit tests/contract -k "vision or negotiat or provider_response" -v` → all pass.
2. Open `docs/vision-adapter-guide.md`. Judge: could a developer write a real adapter (say, for a provider you pick later) from this alone? Anything unclear → tell me.
3. Quick look: `python -c "from scene_signal.adapters.fakes.fake_vision import FakeVision; print(FakeVision().capabilities())"` → shows provider `fake`, mode `still_frames`, and **no** support for temporal intervals. (Class/constructor names may differ slightly; ask Gemini for the exact one-liner if so.)

---

## Chunk 8 — Assembler, document validator, provenance

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `application/assembler.py`: pure function building a `SceneIntelligenceDocument` from: job, resolved-asset info (fingerprint, checksum status), `MediaInspection`, shot list, extracted frames, validated vision batches (per shot), capability reports, warnings, and provenance inputs. Assigns canonical IDs in the deterministic order of V-20; maps provider-local entities to canonical entities (**within a shot only**; never merges across shots unless the adapter declared cross-shot identity and supplied link evidence); maps events with precision per `domain/evidence`; sets `analysis_status` per shot; sets `outcome` and capability statuses per V-15; converts microseconds to 6-decimal seconds; copies provider `shot_summary` to `summary` only for analyzed shots.
- `application/document_validator.py`: `validate_document(doc, adapter_caps) -> list[Violation]`; raises `OutputValidationFailedError` with `details.violations` (list of `{rule: "V-xx", path, message}`) via `assert_valid`. Implements V-01 … V-20.
- `application/provenance.py`: builds `Provenance` from an **allow-list** of fields (never copies arbitrary dicts); redaction guard.
- Docs: `output-contract.md` (validation rules in plain language), `decisions.md`, `handoff.md`.

**Out of scope:** running ports, retries, persistence (Chunks 9–10).

**Tests to write first** (`tests/unit/application/`)
- Golden test: a fixed set of inputs (fake probe/frames/shots/vision) → document equal to a checked-in golden JSON; and the golden validates (Chunk 1 schema + V-rules).
- Determinism: same inputs twice → identical output except timestamps; input order of provider items shuffled → same output order and IDs (V-20).
- Entity scope: two shots each with a "person" → two entities, never merged; adapter declaring cross-shot identity with link evidence → allowed (`asset` scope).
- Event precision: still adapter with 2 supporting samples → `multi_sample_span` with null start/end; single sample → `single_sample_only`; temporal adapter with start/end → `adapter_reported_interval`; start/end from a still adapter are stripped with a `PROVIDER_ITEM_DROPPED`-style warning.
- Camera movement guard (V-10) for still/sequence/video modes.
- Partial: a failed shot → `analysis_status=failed`, no observations, `outcome=partial`, capability `partial`; skipped shots; unsupported capability reported.
- Validator corruption table (≥ 20 cases, one per rule V-01…V-19: duplicate id, gap between shots, frame outside its shot, observation referencing a missing frame, evidence frame from another shot, event across shots, confidence without source, precision mismatch, missing provenance field, secret-like key in provenance, bad timeline constants, …), each yielding the right rule ID.
- Provenance: required fields present; a config dict containing `api_key`/`token` is never copied.

**Acceptance criteria:** the document is built and validated against the versioned schema plus cross-reference rules; provenance and warnings recorded; temporal claims distinguish direct evidence from inference; all pass.

**Completion evidence:** test summary; the golden file path.

### 🧑 FOR YOU — Review and manual test

1. `pytest tests/unit/application -v` → all pass; the list of validator-corruption tests should be visibly long (≥ 20).
2. Open the golden JSON file (path in the report). Check against your own understanding:
   - Events from stills have `start_seconds: null` and a `multi_sample_span` or `single_sample_only` precision.
   - There is a `camera_movement` observation with value `unsupported`.
   - No observation exists for any failed shot.
3. `python -m scene_signal validate-result <golden path>` → `OK`.
4. Edit a copy of the golden: change one shot `end_seconds` so it leaves a gap → `validate-result` should now fail **only if** Gemini wired the cross-reference validator into this command; if it says OK, that is acceptable at this stage (the validator is exercised in Chunk 9) — just note it for me.

---

## Chunk 9 — Orchestration (stateless pipeline) and explicit job documents

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `application/pipeline.py`: explicit stages as separate functions/classes with a shared `StageContext`: 1 validate → 2 resolve → 3 inspect → 4a shot detection → 4b sampling plan (per shot, AD-1) → 5 extract frames → 6 analyze (batched per shot, ≤ `max_frames_per_call`) → 7 assemble → 8 validate → 9 return (stateless; persistence added in Chunk 10) → 10 provenance recorded during assembly. All collaborators injected through a `Ports` bundle plus `Clock`/`IdSource` for tests.
- `application/service.py`: `SceneIntelligenceService.extract(job: ExtractionJob | dict) -> JobResult` (synchronous, framework-free).
- Capability gating: `shot_detection` not requested → `whole_asset` shot; vision stage skipped entirely if no visual capability requested (shots `not_requested`); `include_context_in_analysis=false` → `context_hints=None` (AD-7); `source_timeline` mismatches → warning only.
- Cleanup: workspace context manager around stages 5–6; guaranteed cleanup on every failure path.
- Failures in this chunk are surfaced as typed `JobResult(status="failed")` with `ErrorInfo` (retry logic arrives in Chunk 10; here a first failure ends the job).
- A full-document validation (Chunk 8) is mandatory before returning success.
- CLI (explicit job documents are primary, Addendum §4): `extract --job JOB.json [--assets-root DIR] [--provider fake] [--out DIR]` → validates the versioned job document, runs the pipeline, writes `<out>/result.json`, prints a short summary table. Convenience form `extract FILE --profile standard --provider fake [--capabilities ...] [--job-id ID] [--source-kind generated|user_upload|imported]` builds a job, **prints the job document it built**, then runs it. `scripts/make_job_documents.py` writes one job document per fixture per source kind into `tests/fixtures/jobs/` (`<fixture>.generated.json`, `.user_upload.json`, `.imported.json`; paths relative to the assets root).
- Docs: `architecture.md` (pipeline diagram in text), `decisions.md`, `handoff.md`.

**Out of scope:** retries, idempotency, repository, HTTP.

**Tests to write first**
- All-fake end-to-end for inspected durations 3, 5, 30, 90 s (no FFmpeg): success documents validate; frame counts per C.8 examples.
- Stage-order spy: shot detection **before** frame extraction; analyze after; assemble last.
- **C-11:** the same media submitted as `generated`, `user_upload` and `imported` jobs yields documents that are identical except `job.source_kind`, `request_hash`, `provenance.job_id`/`request_hash` and timestamps. No pipeline code path branches on `source_kind`. `channel_context`, `production_id`, `scene_id` and `source_prompt` absent works.
- Requested-capability gating (list above); no vision calls when not requested (assert zero calls).
- Failure paths: asset not found, corrupt media, no video stream → typed failures, **zero** vision calls, workspace cleaned; frame extraction failure → typed failure, cleanup.
- Source immutability (hash before/after on a temp file).
- AD-7: the vision request's `context_hints` is `None` by default and set only when the setting is on.
- Real-adapter end-to-end with the FFmpeg fixtures + fake vision (`requires_ffmpeg`): `clip_3s…`, `clip_5s…`, `multishot_12s`, `black_transition_9s`, `clip_portrait_5s` all complete and validate; shot boundaries match ground truth; frames lie in their shots.
- Determinism: same job twice → identical documents except timestamps.

**Acceptance criteria:** module callable without the HTTP API; works without paid services; inspects actual media; handles short and longer clips; no fabricated analysis on failure; documents validated before return.

**Completion evidence:** test summary; CLI transcript for two fixtures.

### 🧑 FOR YOU — Review and manual test

1. `python -m scene_signal extract tests/fixtures/media/multishot_12s.mp4 --profile standard --provider fake --out out_multishot` → summary: outcome `complete`; **4 shots**; **8 frames**; observations and entities with `[FAKE]` text. Open `out_multishot/result.json`.
2. Check in the JSON: shot boundaries ≈ 3.0/6.0/9.0; each frame's `timestamp_seconds` lies inside its shot; `provenance.vision.provider` is `fake`; `asset_fingerprint` is a `sha256:…` value (**not** null); no secrets anywhere.
3. `python -m scene_signal validate-result out_multishot/result.json` → `OK`.
4. Run for `clip_3s_landscape_noaudio.mp4`, `clip_5s_landscape_audio.mp4`, `clip_portrait_5s.mp4` (display size 720×1280 → frame images/records tall), `black_transition_9s.mp4` (three shots with a black one), `clip_90s_continuous.mp4` (32 frames for `standard`).
5. Try `--capabilities shot_detection` only → no observations, shots with `analysis_status: not_requested`, capability reports show the other capabilities as `not_requested`.
6. Try `extract tests/fixtures/media/zero_byte.mp4 ...` → typed error `MEDIA_INVALID_OR_CORRUPT`, **no** result.json written (or one containing only the error — whichever Gemini documented), and no leftover work folder.
7. Run the same command twice → same shots/frames/observations (only timestamps differ).
8. **Explicit job documents:** `python scripts/make_job_documents.py`, then run `python -m scene_signal extract --job tests/fixtures/jobs/multishot_12s.generated.json --assets-root tests/fixtures/media --provider fake --out out_gen`, and the same with `.user_upload.json` (`--out out_up`) and `.imported.json` (`--out out_imp`). Compare the three `result.json` files with a diff tool: they must differ **only** in `source_kind`, request/job identifiers and timestamps.
9. Edit one job document by hand (change `asset_ref.uri` to a missing file) → `ASSET_NOT_FOUND`; remove `source_kind` → `INVALID_JOB_CONTRACT`; the failure appears **before** any media is touched.

---

## Chunk 10 — Errors, retries, partial results, idempotency, persistence

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- `application/retry.py`: `RetryExecutor` with injectable `sleeper`, `clock`, `rng`; bounded attempts; exponential backoff with full jitter capped at `max_delay`; honors `retry_after`; per-stage and per-job deadlines; retries **only** errors with `retryable=true` (C.4); `PROVIDER_RESPONSE_INVALID` limited to `invalid_response_retries`; records attempts per stage into `stage_attempts`.
- Wrap provider calls, probe and extraction timeouts, and persistence operations with the executor. Permanent errors never retried.
- Partial outcome logic per AD-5 and V-15/V-16: provider failure after retries for a shot → shot `failed`, capability `partial`/`failed`, `outcome=partial`; if **all** visual analysis fails and `allow_partial_results` is true → partial document (shots + media, no observations); if false → failed job. **Never** fabricate observations.
- `ports/repository.py` + `adapters/storage/local_repository.py`: layout D-05; atomic writes (temp + rename); `claim_job` uses atomic directory creation; status transitions `pending → running → succeeded|partial|failed`; request hash recorded.
- Idempotency (D-04): same id + same hash → stored result returned (no pipeline run, provider call count 0) when terminal-success/partial; failed → re-execute with `attempt+1`; running → `JOB_IN_PROGRESS`; same id + different hash → `JOB_ID_CONFLICT`; rerun via new `job_id` with `rerun_of`. Stateless mode (no repository) documents that idempotency is not provided.
- Cleanup policy: workspace removed on every failure path (fault-injection test at each stage); `keep_artifacts` honored.
- Logging: structured logs with `job_id`/`correlation_id`; a redaction filter; no payloads, no media content.
- CLI: `extract` gains `--data-root DIR` (enables persistence), `--rerun-of`, and failure-injection flags for the fake (`--fake-fail rate_limit:2`, `--fake-fail timeout:5`, `--fake-fail invalid:1`, `--fake-fail unavailable:always`); new subcommands `status JOB_ID --data-root DIR`, `result JOB_ID --data-root DIR`.
- Docs: `architecture.md` (execution semantics), `decisions.md` (idempotency, partial policy), `testing.md`, `handoff.md`.

**Out of scope:** distributed locking, queues, background workers, exactly-once guarantees (**do not promise them**).

**Tests to write first**
- Retry table (fake sleeper): transient error twice then success → 3 provider calls, backoff delays within the jitter bounds, `stage_attempts.analyze == 3`; exhausted → failed/partial per policy with `attempts == max_attempts`; permanent error → exactly 1 call; `retry_after` respected; invalid response retried once then fails; job deadline stops retries; every error code in C.4 has a test asserting its retry class.
- Partial: provider fails for shot 2 only → shot 2 `failed`, others analyzed, `outcome=partial`, no observations for shot 2, `PROVIDER_PARTIAL` warning; all fail with `allow_partial_results=false` → failed.
- Repository: save/load round trip; simulated crash between temp write and rename leaves no corrupt `result.json`; status transitions valid; concurrent claim of the same job id → exactly one winner (two threads).
- Idempotency matrix (D-04) including provider call counts; rerun with new id and `rerun_of`.
- Persistence failure (fake repository raising) → retried then `PERSISTENCE_FAILED`.
- Cleanup: parametrized fault injection at every stage leaves no work files.
- Secrets: run a job with `provider_config_ref="sk-test-SECRET-123"`; assert the string appears in **none** of: logs (caplog), status, result, error details, provenance.
- Never-fabricate: when the provider always fails, assert zero provider-derived observations exist in the output.

**Acceptance criteria:** invalid and corrupt media fail clearly; bounded retries for transient provider errors; no pointless retries; output validated before persistence; provenance and warnings recorded; temp artifacts cleaned.

**Completion evidence:** test summary; CLI transcripts for the manual tests below.

### 🧑 FOR YOU — Review and manual test

Use a data folder, e.g. `--data-root ./.scene_signal/data`.

1. **Normal run + idempotency**
   - `python -m scene_signal extract tests/fixtures/media/clip_5s_landscape_audio.mp4 --provider fake --job-id demo-1 --data-root ./.scene_signal/data --out out1` → complete.
   - Run the **identical** command again → returns the stored result immediately (the summary should say it was served from storage / no provider calls).
   - `python -m scene_signal status demo-1 --data-root ./.scene_signal/data` → `succeeded`. `... result demo-1 ...` → prints the document.
2. **Conflict**: run with `--job-id demo-1` but `--profile quick` → error `JOB_ID_CONFLICT`.
3. **Explicit rerun**: `--job-id demo-2 --rerun-of demo-1` → new job completes; `demo-1` untouched.
4. **Retries**: `... --job-id retry-1 --fake-fail rate_limit:2 --data-root ...` → succeeds; summary/provenance shows the analyze stage used **3 attempts**.
5. **Exhausted retries**: `--job-id retry-2 --fake-fail unavailable:always` → outcome `partial` (default) with **zero** observations and a warning; status `partial`. Rerun with `--no-partial` (if provided, else set `SCENE_SIGNAL_ALLOW_PARTIAL_RESULTS=false`) → `failed`, error `PROVIDER_UNAVAILABLE`.
6. **Permanent error does not retry**: use `zero_byte.mp4` → fails once, `attempts: 1`.
7. **Partial on one shot**: `multishot_12s.mp4` with `--fake-fail unavailable:shot=2` (if Gemini implemented shot targeting; otherwise skip) → shot 2 marked `failed`, others analyzed.
8. **Cleanup**: after every run above, `.scene_signal/work` is empty.
9. **Crash safety (optional)**: while a long run is in progress (`clip_90s_continuous.mp4` with `thorough`), press Ctrl+C; check `.scene_signal/data/jobs/<id>/` has no half-written `result.json` and `.scene_signal/work` is cleaned.
10. Search all outputs for secrets: `grep -ri "sk-" .scene_signal` (Windows: `findstr /s /i "sk-" .scene_signal\*`) → nothing.

---

## Chunk 11 — CLI completion and optional FastAPI interface

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- Finalize the CLI: consistent exit codes (0 success, 1 failed job, 2 invalid input, 3 internal), `--json` for machine output, help texts for every subcommand, a `doctor` subcommand that reports Python version, FFmpeg/ffprobe versions and settings (with secrets redacted).
- `api/app.py`: `create_app(service, settings)` (FastAPI app factory; extra `api`). Endpoints: `POST /v1/extractions` (body = `ExtractionJob`; synchronous run in a thread pool; returns `JobResult`), `GET /v1/extractions/{job_id}` (status), `GET /v1/extractions/{job_id}/result`, `GET /healthz`. Error mapping: `INVALID_JOB_CONTRACT`/`UNSUPPORTED_CONTRACT_VERSION` → 422; `ASSET_NOT_FOUND` → 404; `ASSET_ACCESS_DENIED` → 403; `JOB_ID_CONFLICT`/`JOB_IN_PROGRESS` → 409; `MEDIA_*` → 415 for unsupported/invalid, 422 for limits; provider transient → 503 (with `Retry-After` when known); `INTERNAL_ERROR` → 500. Error bodies are `ErrorInfo`.
- The core remains importable and usable **without** FastAPI installed (test via a subprocess that blocks the import).
- Wiring for the API uses the fake vision provider by default; a documented factory hook selects a real adapter later.
- Docs: `README.md` (how to run the API), `architecture.md`, `decisions.md`, `handoff.md`.

**Out of scope:** authentication, queues, background jobs, a frontend.

**Tests to write first**
- API tests (FastAPI `TestClient`, fakes): success, each error mapping row, idempotent repeat, status/result retrieval for unknown id → 404, request body with extra fields → 422.
- Core import test without FastAPI.
- CLI exit-code tests; `doctor` output contains no secrets.
- OpenAPI schema generated and contains `ExtractionJob` and `SceneIntelligenceDocument`.

**Acceptance criteria:** lightweight API exposes the capability; the core is callable without HTTP.

**Completion evidence:** test summary; transcript of curl calls below.

### 🧑 FOR YOU — Review and manual test

1. `pip install -e ".[dev,api]"`
2. `python -m scene_signal doctor` → shows Python, FFmpeg/ffprobe versions, and settings.
3. Start the API (the exact command is in README; typically): `uvicorn scene_signal.api.app:create_app --factory --port 8000`
4. Open `http://localhost:8000/docs` in a browser → interactive docs; use **Try it out** on `POST /v1/extractions` with the minimal request (adjust `uri` and make sure the file's folder is an allowed root — README explains the env var).
5. curl (macOS/Linux; PowerShell users can use the browser docs page):
   - `curl -s localhost:8000/healthz`
   - `curl -s -X POST localhost:8000/v1/extractions -H "content-type: application/json" -d @docs/examples/request.minimal.json`
   - repeat the same call → same result (idempotent); `curl -s localhost:8000/v1/extractions/extract-001`
6. Error checks: send a body with `"source_kind": "banana"` → HTTP 422; a nonexistent file → 404; a path outside the allowed root such as `/etc/passwd` → **403**; same `job_id` with a different profile → 409.
7. Stop the server. Uninstall the extra (`pip uninstall fastapi uvicorn`) and run `python -m scene_signal extract ...` → still works (**core independent of the API**).

---

## Chunk 12 — Contract tests, temporal ground truth, documentation, independence drill, acceptance sign-off

### 🤖 FOR GEMINI — Implementation spec

**Scope**
- Complete adapter contract coverage: each concrete adapter (ffprobe, ffmpeg frames, ffmpeg shots, local storage, local repository, every fake) passes the shared port contract suites; real-provider hook tests remain `integration` and skipped by default.
- Temporal ground-truth tests from the manifest, **named to distinguish** exact media-time conversion tests from approximate shot-boundary/event-localization tests with explicit tolerances.
- `scripts/manual_smoke.py`: runs all fixtures through the pipeline (each via an explicit job document under `tests/fixtures/jobs/`) with the fake provider and prints a table (fixture, status, outcome, error code, #shots, #frames, #observations, #events, warnings, seconds). Exit code non-zero if any fixture deviates from its manifest expectation.
- Documentation complete and consistent with the verified state: `architecture.md`, `input-contract.md`, `output-contract.md`, `integration-boundary.md`, `testing.md` (fixtures and limitations), `decisions.md`, `vision-adapter-guide.md`, `README.md`, `GEMINI.md`. Generate and commit the JSON Schemas in `docs/schemas/`.
- **Independence checks** recorded in `docs/acceptance.md`: (1) a grep-based test that no file under `src/` or `tests/` references the generation application, its notebook or any path outside the project; (2) the **independence drill** (see manual test #5): fresh clone, fresh virtualenv, `pip install -e ".[dev]"`, `pytest -q` passes on a machine path that does not include the generation application.
- `docs/acceptance.md`: the §17 checklist with, for each item, status (✅/❌/⏭), evidence (test names and command outputs) and blockers. **No item is ✅ without a passing test or reproducible command.**
- `docs/handoff.md`: final state; "Next approved capability" section listing **proposals only** (real vision adapter — requires your provider authorization; optional motion analysis for camera/subject movement; OCR/text; audio transcript; scene planning consumer), without starting any.

**Out of scope:** any real provider integration or new feature.

**Tests to write first:** the contract suites and ground-truth tests above (expected to fail until wiring is complete), then the smoke script's own manifest check.

**Acceptance criteria:** every applicable item in spec §17 is satisfied or has a documented blocker and bounded alternative.

**Completion evidence:** full `pytest -q` output (with the count of skipped tests and why), `manual_smoke.py` table, `docs/acceptance.md`.

### 🧑 FOR YOU — Review and manual test (final acceptance)

1. `pytest -q` → all pass; note skipped tests (should only be platform/FFmpeg/integration ones, each with a reason).
2. `python scripts/manual_smoke.py` → table with one row per fixture:
   - the 3 s, 5 s, 30 s, 90 s, portrait, multishot, black-transition rows → `succeeded / complete`,
   - corrupt, zero-byte, not-a-video, audio-only rows → `failed` with the **expected error codes**,
   - script exits 0 only if everything matches the manifest.
3. Read `docs/acceptance.md` line by line. Anything marked ✅ without evidence → send it back.
4. Run a few of **your own** videos (different lengths, a phone portrait clip, an edited multi-cut clip) through `extract --provider fake`. Check shots/frames/timestamps make sense. (Fake observations are placeholders; this tests mechanics, not AI quality.)
5. **Independence drill** (proves SceneSignal stands alone): commit everything (`git add -A && git commit -m "Module 01"`), then `git clone . ../SceneSignal-drill`, `cd ../SceneSignal-drill`, create a new virtualenv, `pip install -e ".[dev]"`, `pytest -q` → passes. Then delete `SceneSignal-drill`. This must work without the generation application present.
6. Read `docs/integration-boundary.md` once more as if you were the generation application's developer: is everything needed to build the adapter there (Part G lists what is still open)?
7. Decide the next step: provide a vision provider you authorize (I will then design the real adapter spec against the existing contract), or proceed to the next module.

---

# PART E — Gemini CLI prompts

## E.0 🤖 FOR GEMINI — Standing Rules (paste this FIRST in every session, before the chunk prompt)

````
You are the implementation engineer for SceneSignal, Module 01 ("Scene Intelligence Extraction").
SceneSignal is a GREENFIELD, standalone project. Your working directory is SceneSignal/ and it is the ONLY
directory you may read from or write to. You implement exactly ONE chunk per session.
The specification file is docs/SPEC-01-scenesignal.md (inside this directory).

BEFORE CODING
1. Confirm your working directory is SceneSignal/ (print pwd). If it is not, STOP and report.
2. Read, in this order, the files that exist INSIDE this directory: GEMINI.md, docs/handoff.md, docs/decisions.md.
   Follow the conventions SceneSignal defines for itself. Do not look for, read or follow files from any other project.
3. Read the spec: Part C (contracts, frozen), Part S (boundaries and asset requirements) and the "FOR GEMINI -
   Implementation spec" of YOUR chunk in Part D. Ignore sections tagged "FOR YOU".
4. Check docs/handoff.md "Next chunk". If it does not match the chunk you were asked to implement, STOP and report.

RULES
1. SCOPE: implement only the requested chunk. No extra features, no unrelated refactoring, no new public names
   beyond the spec. If you need something from a later chunk, STOP and report instead of stubbing around it.
2. GREENFIELD: never read, list, search, import, copy, reference or modify anything outside SceneSignal/ - in particular
   never touch the existing video-generation application, its notebook, its database or its files. Do not walk to parent
   directories. SceneSignal must never depend on that application. If any instruction seems to require touching
   anything outside SceneSignal/, STOP and report.
3. TDD (mandatory): write the failing tests first. Run them and show the failing result (exact command and failure
   summary) BEFORE writing implementation. Then implement until green. Never weaken, delete or skip tests to get
   green (the only allowed skips are the documented requires_ffmpeg / integration markers).
4. ARCHITECTURE: follow the dependency table in spec C.9. domain/, application/, ports/ and schemas/ never import
   fastapi, uvicorn, httpx, any provider SDK, or anything from adapters/ or api/. Adapters never define the canonical
   output schema. No module may be named like a stdlib module. The architecture test must stay green.
5. CONTRACTS: Part C is frozen. Do not rename fields, change enums or relax rules. The contract is the integration
   boundary: no field may carry generation-application internals. If you believe a rule is wrong or contradictory,
   STOP and write a CONTRADICTION REPORT (what, where in the spec, why it fails, 1-2 options). Do not make an
   unapproved architectural change.
6. SAFETY: never log, print, store or commit secrets; no network access; no paid or GPU services; never modify source
   media (treat inputs as read-only); never hard-code absolute paths; run subprocesses with argument lists, never
   shell=True.
7. DEPENDENCIES: only those named in the spec. Ask before adding any other.
8. UNSPECIFIED DETAILS: do not ask about minor details. Choose the documented default or the most conservative reversible
   option, and record it in docs/decisions.md.
9. QUALITY GATES before reporting: run `pytest -q` (whole suite), `ruff check .`, `ruff format --check .` (and mypy if
   configured). Paste the exact summary lines. Never claim a test passed without running it.
10. DOCS: update docs/handoff.md (verified state only), docs/decisions.md and every doc named in your chunk. Mark a
    feature complete only with passing tests as evidence.
11. GIT: SceneSignal has its own repository. Do not commit or push unless the user tells you to. Leave changes in the
    working tree.

FINISH with a COMPLETION REPORT in exactly this format:

COMPLETION REPORT - Chunk <N>
- Working directory confirmed: <pwd>
- Implemented: <bullets>
- Files created/modified: <list>
- Interfaces introduced: <list>
- Red run (before implementation): <command + summary>
- Final test run: <commands + exact summary lines, counts of passed/failed/skipped and why skipped>
- Lint/format: <results>
- Decisions made within scope (also in docs/decisions.md): <list or none>
- Known limitations: <list>
- Unresolved issues / contradictions: <list or none>
- Manual-test notes for the Chief Engineer: <exact commands you verified>
- Handoff updated: <yes + what "Next chunk" now says>
- Anything created or changed outside SceneSignal/: <must be "none">
- Avoid repeating: <anything the next session must not redo>

CONTRADICTION REPORT format (use instead of continuing):
CONTRADICTION REPORT - Chunk <N>
- Spec reference: <part/section/rule id>
- Problem: <what cannot be satisfied or is ambiguous>
- Evidence: <test/command output>
- Options: <A / B, with consequences>
- Recommendation: <one option>
- Work completed so far: <files/tests, left in a consistent state>
````

## E.0b 🤖 FOR GEMINI — `docs/handoff.md` template (Chunk 0 creates it; every chunk updates it)

````
# Handoff state - SceneSignal, Module 01 (Scene Intelligence Extraction)
Last updated: <date> by Chunk <N>

## Verified state (only what passes tests)
- Chunk <N>: <what exists> - evidence: <test command + result>

## Chunk log
| Chunk | Status | Evidence | Date |
|---|---|---|---|

## Next chunk
<Chunk number and title, exactly as in the spec>. Start by: <first step>.

## Do not repeat
- <work already done>

## Open issues / limitations
- <list>

## Environment notes
- Python <ver>, FFmpeg <ver or "not installed">
````

## E.1 🤖 FOR GEMINI — Chunk 0 prompt (self-contained; paste after E.0). 🧑 Replace `<PARENT_DIR>` first.

````
CHUNK 0 - Greenfield verification, scaffold, AI instructions, handoff state, architecture test.

EXPECTED_PARENT_DIR: <PARENT_DIR>

Your working directory must be SceneSignal/ (a NEW, empty project folder that already contains only
docs/SPEC-01-scenesignal.md). Read that spec: Part C, Part S and Part D "Chunk 0".

STEP 1 - GREENFIELD CHECKS (make no changes until all pass; print the evidence):
  a) pwd ends with /SceneSignal (or \SceneSignal) and its parent equals EXPECTED_PARENT_DIR.
  b) The directory contains only docs/SPEC-01-scenesignal.md (ignore harmless OS files).
  c) It is NOT inside any existing Git repository: `git rev-parse --show-toplevel` must fail.
  d) You will not list, read, write or search anything outside this directory.
If any check fails, STOP and report. Do not guess or "fix" the location.

STEP 2 - Implement exactly the Chunk 0 scope from the spec:
  - git init (branch main, no remote, no commit).
  - GEMINI.md, pyproject.toml (distribution scene-signal; hatchling; src layout; Python >=3.11; pydantic>=2.6,<3;
    extras dev = pytest, ruff, jsonschema (mypy optional); api = fastapi, uvicorn, httpx), pytest markers
    requires_ffmpeg / contract / integration with --strict-markers, ruff config, .env.example (documented SCENE_SIGNAL_*
    variables, no secrets), .gitignore.
  - src/scene_signal/{__init__.py (__version__ = "0.1.0"), __main__.py, cli.py (argparse subcommand registry; only
    --version for now), py.typed}. Do NOT create empty placeholder subpackages.
  - tests/conftest.py (auto-skip requires_ffmpeg when ffmpeg/ffprobe are missing).
  - tests/unit/test_architecture.py: AST scan of domain/, application/, ports/, schemas/ for forbidden imports AND a
    check that no module under src/scene_signal is named like a stdlib top-level module (sys.stdlib_module_names),
    each with a self-test using a temporary fake package.
  - docs/README.md is not needed; create README.md at the root, plus docs/architecture.md, docs/decisions.md (record
    AD-1..AD-10, N-01..N-08, D-01..D-09 from the spec), docs/testing.md, docs/integration-boundary.md (skeleton),
    docs/handoff.md (use the template in the spec; Next chunk = 1).
STEP 3 - TDD: write the tests first (package import + __version__; `python -m scene_signal --version`; requires_ffmpeg
skip via monkeypatching shutil.which; both architecture checks and their self-tests) and show them failing.
STEP 4 - Create .venv inside SceneSignal/, verify `python -c "import importlib.util as u; print(u.find_spec('scene_signal'))"`
prints None BEFORE installing, then `pip install -e ".[dev]"`, then run: pytest -q, ruff check ., ruff format --check .,
python -m scene_signal --version. Paste the exact outputs.
Do not implement anything from later chunks. Do not touch anything outside SceneSignal/. Finish with the COMPLETION REPORT.
````

## E.2 🤖 FOR GEMINI — Chunk 1 prompt (paste after E.0)

````
CHUNK 1 - Contracts, typed errors, validation CLI, integration-boundary doc.
Read docs/handoff.md (Next chunk must be 1), then spec Part C (all), Part S and Part D "Chunk 1".
Implement exactly the Chunk 1 scope: domain/errors.py, schemas/{common,job,result,versions,export}.py,
parse_extraction_job, the CLI subcommands validate-request / validate-result / export-schemas, the example JSON files under
docs/examples/ (including request.generated.json, request.user_upload.json and request.imported.json), docs/input-contract.md
(with the asset requirements S.4 and failure semantics S.5), docs/output-contract.md and docs/integration-boundary.md.
Models must match Part C.2-C.4 exactly (field names, enums, extra=forbid, intra-record validators). The request has NO
technical-metadata fields and no field named after generation-application internals. Cross-document checks (V-03..V-20
beyond intra-record) are NOT part of this chunk.
TDD: write every test listed in "Tests to write first" before implementing; show the red run. Do not touch other
chunks' areas or anything outside SceneSignal/. Finish with the COMPLETION REPORT (include the CLI transcript for the
example files).
````

## E.3 🤖 FOR GEMINI — Chunk 2 prompt

````
CHUNK 2 - Domain primitives: time, IDs, policies, evidence rules.
Read docs/handoff.md (Next chunk must be 2), spec Part C.1, C.5, C.8 and Part D "Chunk 2".
Implement domain/timeline.py (TimeUs, Interval, conversions, tile_check, snap_to_nearest), domain/ids.py, domain/policies.py
(Settings with env prefix SCENE_SIGNAL_ and optional TOML), domain/evidence.py, domain/canonical.py (canonical_json,
request_hash excluding correlation_id). Pure Python, no I/O except reading the optional TOML in Settings.load().
Internal time is integer microseconds; seconds output has at most 6 decimals using round-half-even; never round to whole
seconds. TDD with the exact-conversion and precision tests listed. In docs/decisions.md document the exact public function
names so the manual one-liners in the spec can be run, and give the user the exact one-liner commands in your report.
Finish with the COMPLETION REPORT.
````

## E.4 🤖 FOR GEMINI — Chunk 3 prompt

````
CHUNK 3 - Media inspection: port, fake, ffprobe adapter, fixture generator.
Read docs/handoff.md (Next chunk must be 3), spec Part C.3/C.4/C.7, Part S.4 and Part D "Chunk 3".
Implement ports/media_probe.py, adapters/media/ffprobe.py, adapters/fakes/fake_media_probe.py, scripts/make_fixtures.py
with tests/fixtures/manifest.json, the shared contract tests, and the CLI subcommand `inspect FILE`.
Key rules: ffprobe via subprocess argument lists; parse decimals with Decimal/Fraction, never float; duration from the
video stream with container fallback; VFR detection via sorted packet-timestamp analysis; rotation sign normalized to
clockwise {0,90,180,270}; display dimensions apply SAR then swap on 90/270; missing audio is valid; map errors exactly as
specified. CONTENT-BASED VALIDATION: never decide format by extension; still images -> MEDIA_UNSUPPORTED_FORMAT; attached
pictures are not video streams; several video streams -> default-disposition (else first) + MULTIPLE_VIDEO_STREAMS warning.
Fixtures include the Matroska and extensionless copies and a still image. Generate fixtures only with FFmpeg lavfi synthetic
sources and local re-muxing (no downloads). Fixtures marked "best effort" may be recorded as unavailable with a reason.
FFmpeg-dependent tests use the requires_ffmpeg marker. TDD: parsing unit tests with canned ffprobe JSON come first.
Report which tests ran vs. skipped. Do not touch anything outside SceneSignal/. Finish with the COMPLETION REPORT.
````

## E.5 🤖 FOR GEMINI — Chunk 4 prompt

````
CHUNK 4 - Local asset storage and frame extraction.
Read docs/handoff.md (Next chunk must be 4), spec Part C.7/C.8 and Part D "Chunk 4".
Implement ports/asset_storage.py, adapters/storage/local_fs.py (allowed roots, realpath/symlink safety, sha256 fingerprint
always computed, supplied checksum verified, Workspace with guaranteed cleanup), ports/frame_extraction.py,
adapters/media/ffmpeg_frames.py (input seek, single JPEG per request, autorotate, long-edge downscale, actual timestamp via
showinfo parsing - VERIFY empirically against an independent ffprobe frame table and document the approach in
docs/decisions.md), adapters/fakes/fake_frames.py, contract tests, and CLI `extract-frames`.
Source media must remain byte- and mtime-identical (test it). Work only with the allowed-root policy; never read outside it.
TDD first; FFmpeg tests use requires_ffmpeg. Finish with the COMPLETION REPORT including FFmpeg version observations.
````

## E.6 🤖 FOR GEMINI — Chunk 5 prompt

````
CHUNK 5 - Sampling planner (pure).
Read docs/handoff.md (Next chunk must be 5), spec Part C.8 (sampling strategy v1.0 and profile table) and Part D "Chunk 5".
Implement application/sampling.py exactly as specified (bin_center_per_shot, versioned, deterministic, budget capping with
largest-remainder, >=1 sample per shot, absolute ceiling, min_total_fill) and the CLI `plan-sampling`. No I/O, no ffmpeg.
Assert the exact sample times given in the spec (e.g. standard 3 s -> 0.5, 1.5, 2.5). Include the invariant sweep test.
TDD first. Finish with the COMPLETION REPORT (include CLI output for 3, 5, 30, 90 s).
````

## E.7 🤖 FOR GEMINI — Chunk 6 prompt

````
CHUNK 6 - Shot detection and shot builder.
Read docs/handoff.md (Next chunk must be 6), spec Part C.3 (Shot), C.8 and Part D "Chunk 6".
Implement ports/shot_detection.py, adapters/media/ffmpeg_shots.py (scene score + blackdetect, boundary = first frame of the
new shot, downscaled analysis), adapters/fakes/fake_shots.py, application/shots.py (pure build_shots producing a tiling of
[0,duration), black segments, degradation to a whole_asset shot on failure or when not requested), and CLI `detect-shots`.
A shot is a structural segment, never described as a narrative scene. Always report the limitation that gradual transitions
are not detected. Ground-truth tests use tests/fixtures/manifest.json tolerances. Do NOT tune thresholds per fixture to pass
tests: if the default 0.30 misbehaves on a fixture, report measured scores and propose a justified default.
Exact tests (tiling arithmetic) and approximate tests (detected times with tolerance) must be named differently.
TDD first. Finish with the COMPLETION REPORT including measured boundary times.
````

## E.8 🤖 FOR GEMINI — Chunk 7 prompt

````
CHUNK 7 - Visual-analysis port, fake provider, provider-response validation.
Read docs/handoff.md (Next chunk must be 7), spec Part C.7 and Part D "Chunk 7".
Implement ports/visual_analysis.py, application/provider_response.py (negotiate + validate_response treating provider output
as untrusted), adapters/fakes/fake_vision.py (deterministic, configurable mode/capabilities/failure scripts/injectable
sleeper), the shared port contract tests (with the env-driven real-adapter hook marked integration and skipped by default),
and docs/vision-adapter-guide.md. Adapters perform NO hidden retries and never assign canonical IDs. Do not implement any
real provider adapter and do not add any provider SDK dependency. TDD first. Finish with the COMPLETION REPORT.
````

## E.9 🤖 FOR GEMINI — Chunk 8 prompt

````
CHUNK 8 - Assembler, document validator, provenance.
Read docs/handoff.md (Next chunk must be 8), spec Part C (all, especially C.3 and C.5) and Part D "Chunk 8".
Implement application/assembler.py (pure; deterministic IDs per V-20; entities mapped within a shot only unless cross-shot
identity is declared with link evidence; event precision per evidence rules; partial outcome logic), application/
document_validator.py (V-01..V-20 with rule IDs in violations; assert_valid raising OUTPUT_VALIDATION_FAILED), and
application/provenance.py (allow-list builder; never copies arbitrary dicts; no secrets). Produce a golden JSON test fixture.
Include the validator corruption table (at least 20 cases). TDD first. Finish with the COMPLETION REPORT (give the golden file path).
````

## E.10 🤖 FOR GEMINI — Chunk 9 prompt

````
CHUNK 9 - Orchestration (stateless pipeline) and explicit job documents.
Read docs/handoff.md (Next chunk must be 9), spec Part C, Part S, Part A.3 (F-1, F-9) and Part D "Chunk 9".
Implement application/pipeline.py (explicit stages; shot detection BEFORE the per-shot sampling plan, then frame extraction,
batched analysis per shot, assembly, mandatory validation), application/service.py (SceneIntelligenceService.extract(job) -> JobResult, synchronous, framework-free), the CLI `extract --job JOB.json
[--assets-root DIR] [--provider fake] [--out DIR]` plus the convenience form `extract FILE ...` that prints the job it
builds, and scripts/make_job_documents.py (one job document per fixture per source kind in tests/fixtures/jobs/).
Ports are injected; Clock/IdSource injectable. source_kind is provenance only: NO code path may branch on it (C-11) - include
the three-source-kind identical-analysis test. Context text is NOT sent to the vision provider unless the setting is on. First
failure ends the job in this chunk (retries come in Chunk 10). No vision call may happen when a deterministic stage fails or no
visual capability is requested. Workspace cleanup on every path. Include the all-fake end-to-end tests for 3/5/30/90 s, the
stage-order spy test, and the FFmpeg fixture end-to-end tests (requires_ffmpeg). TDD first. Do not touch anything outside
SceneSignal/. Finish with the COMPLETION REPORT including CLI transcripts for two fixtures and for the job-document path.
````

## E.11 🤖 FOR GEMINI — Chunk 10 prompt

````
CHUNK 10 - Errors, retries, partial results, idempotency, persistence.
Read docs/handoff.md (Next chunk must be 10), spec Part C.4, C.5 (V-15, V-16), B.3 (D-04, D-05, D-07), AD-5 and Part D "Chunk 10".
Implement application/retry.py (injectable sleeper/clock/rng; bounded; full-jitter backoff; retry_after; per-stage and job
deadlines; retry only retryable errors), ports/repository.py, adapters/storage/local_repository.py (atomic writes, atomic job
claim), partial-outcome logic, idempotency per D-04, a log redaction filter, and the CLI additions (--data-root, --rerun-of,
--fake-fail ..., status, result). Do not promise distributed or exactly-once processing. Never fabricate observations when the
provider fails. Include the secret-leak test with provider_config_ref="sk-test-SECRET-123", fault-injection cleanup tests at
every stage, concurrency test for job claim, and the full retry table (every error code in C.4). TDD first.
Finish with the COMPLETION REPORT including the CLI transcripts used for manual testing.
````

## E.12 🤖 FOR GEMINI — Chunk 11 prompt

````
CHUNK 11 - CLI completion and optional FastAPI interface.
Read docs/handoff.md (Next chunk must be 11), spec Part D "Chunk 11".
Finalize the CLI (exit codes 0/1/2/3, --json, help texts, doctor subcommand with redacted settings) and implement api/app.py
(create_app factory; POST /v1/extractions, GET /v1/extractions/{job_id}, GET /v1/extractions/{job_id}/result, GET /healthz;
error mapping table from the spec; sync core run in a thread pool; fake vision provider by default with a documented factory
hook for real adapters). The core must remain importable and usable without FastAPI installed (test with a subprocess that
blocks the import). No authentication, queues or frontend. TDD first. Finish with the COMPLETION REPORT including the curl
transcript.
````

## E.13 🤖 FOR GEMINI — Chunk 12 prompt

````
CHUNK 12 - Contract tests, temporal ground truth, documentation, independence checks, acceptance sign-off.
Read docs/handoff.md (Next chunk must be 12), spec section 17 acceptance criteria (reproduced in Appendix 1) and Part D "Chunk 12".
Complete shared port contract coverage for every concrete adapter and fake, add temporal ground-truth tests (exact media-time
tests and approximate boundary tests named distinctly, with explicit tolerances), write scripts/manual_smoke.py (each fixture
run through an explicit job document; table output; non-zero exit if any fixture deviates from its manifest), generate and commit
docs/schemas/, finalize all docs including docs/integration-boundary.md and GEMINI.md, add the grep-based independence test
(no references to the generation application, its notebook or paths outside the project), and write docs/acceptance.md with
every checklist item marked pass/fail/skipped WITH evidence (test names or reproducible commands). Do not mark anything
complete without evidence. In docs/handoff.md list next capabilities as PROPOSALS only (real vision adapter requires the
Chief Engineer's provider authorization; the generation adapter is future integration work listed in Part G). Do not implement
any new feature and do not touch anything outside SceneSignal/. Finish with the COMPLETION REPORT including the full pytest
summary and the smoke table.
````

---

# PART F — Risk register (📎 SHARED)

| # | Risk | Consequence | Mitigation | Validation (test or experiment) |
|---|---|---|---|---|
| R-1 | **Temporal accuracy from sparse frames** | Downstream editing trusts invented action times and cuts at wrong moments | Contract separates `evidence_span` from `start/end`; start/end only from temporal-capable adapters; `single_sample_only` / `multi_sample_span` precision; V-10/V-11 guards | Chunk 8 corruption table (precision rules); Chunk 12 ground-truth: no still-adapter event ever has start/end |
| R-2 | **Shot-boundary detection reliability** (fades missed, false cuts on fast motion/flash) | Wrong segmentation → wrong per-shot analysis and sampling | Hard-cut + black-gap scope declared; limitations always reported; threshold configurable; `boundary_score` ≠ confidence; minimum shot length; never "scene" | Chunk 6 ground truth on synthetic fixtures; **experiment on your real videos** (Chunk 6 manual test #5); later add a second detector behind the same port if needed |
| R-3 | **Vision provider capability differences** | Adapter A claims motion it cannot see; schema drift per provider | `VisionCapabilities` declaration; negotiation; response validation; domain evidence rules; adapters never decide schema | Chunk 7 negotiation matrix and contract suite; every real adapter must pass the same suite |
| R-4 | **Cost and latency of real analysis** | Runaway spend; slow jobs | Frame budgets per profile, per-shot batching, downscale, hard ceilings, bounded retries, job deadline | Chunk 5 budget tests; Chunk 10 deadline tests; **experiment** once a real provider exists: measure cost per minute of video per profile and set defaults |
| R-5 | **Variable frame rate and timestamp handling** (frame-index math, container offsets, rotation) | Frames described at the wrong time; off-by-N errors | Time-based sampling; actual decoded pts recorded; `start_time_offset` normalization; VFR classification; `timestamp_source` honesty | Chunk 3 VFR/rotation fixtures; Chunk 4 actual-vs-ffprobe frame table test; Chunk 2 exact conversion tests |
| R-6 | **Long-clip sampling and resource limits** | Memory/time blow-ups, huge frame counts | Policy limits (size/duration/dimensions), sampling ceiling, shot detection on downscaled frames, timeouts, workspace cleanup | Chunk 5 sweep to 600 s; Chunk 9 90 s end-to-end; **experiment**: run a 20–30 min video and record time/RAM (limits adjustable) |
| R-7 | **Entity consistency across frames and shots** | False identity merges ("same person") mislead continuity decisions | Identity scope `frame`/`shot` only; no cross-shot linking without declared capability + evidence; `identity_notes` | Chunk 8 entity-scope tests; V-13 validator case |
| R-8 | **FFmpeg version differences** (field names, flags like display rotation, showinfo output) | Adapter works on one machine and fails on another | Parse defensively; verify behavior empirically against ffprobe; record versions in provenance and handoff; `doctor` command | Chunk 3/4 contract tests; `doctor` output in bug reports |
| R-9 | **Prompt injection / bias via context or on-screen text** | Provider output manipulated or biased by `source_prompt` or text in frames | Context text off by default (AD-7); provider output untrusted and validated; no execution of provider text; descriptions are data | Chunk 9 AD-7 test; Chunk 7 response-validation cases |
| R-10 | **Path traversal / unsafe asset access** | Reading files outside permitted locations | Allowed roots + realpath; no shell; ID regex prevents path tricks via `job_id` | Chunk 4 traversal/symlink tests; Chunk 11 403 check |
| R-11 | **Synthetic fixtures misrepresent real footage** | Tests pass but real videos behave differently | Documented limitations; manual runs on your real videos in Chunks 3, 6, 12; add small real clips later if you have legal ones | Manual tests listed per chunk; extend the manifest when real clips are added |
| R-12 | **Greenfield contamination / accidental coupling** to the generation application (imports, shared paths, copied files, edits to its repo) | SceneSignal cannot be tested or deployed alone; the generation app gets broken | Separate directory and Git repo (G-01…G-09); Gemini confined to `SceneSignal/`; dependency table; grep-based independence test; "Anything changed outside SceneSignal/" line in every report | Chunk 0 isolation check; Chunk 12 independence drill (fresh clone + fresh venv) |
| R-13 | **Contract drift when the generation adapter is finally built** (it needs fields we did not foresee, or its metadata conflicts with inspected facts) | Pressure to bend the core to one client | Contract is versioned; C-10/C-11; unknown fields rejected; additive changes only via version bump; mapping table is a documented, unimplemented boundary | Part G prerequisites; a consumer-driven contract test written with the real adapter before integration starts |
| R-14 | **Non-video or odd assets passing as video** (still images, cover art, extensionless or unusual containers, multiple video streams) | Nonsense timelines, crashes, wrong analysis | Content-based validation; frame-count and duration checks; `MULTIPLE_VIDEO_STREAMS`; typed errors | Chunk 3 fixtures (`still_image.png`, MKV, extensionless) and canned ffprobe JSON tests |

---

# PART G — Future integration work (not part of Milestone 1) (🧑 FOR YOU + 📎 SHARED)

Everything below is required to connect SceneSignal to the existing generation application. **None of it is implemented, started or assumed in Milestone 1.** It becomes actionable only after Chunk 12 passes acceptance.

## G.1 Integration work items

| ID | Work item | Why it is needed | Prerequisite / open question | Where it lives |
|---|---|---|---|---|
| G-01 | **Write the generation adapter** (`GenerationAssetAdapter`, C.7b): turn a generation output into a valid `ExtractionJob`. | Addendum §3 point 5 | Learn the generation app's real output shape (not needed before). | Generation-app side or a separate integration package. **Not** in `src/scene_signal`. |
| G-02 | **Decide the transport**: in-process Python call, CLI invocation, HTTP API, or file-drop/queue. | Today only the service, CLI and optional API exist. | Do both apps share a machine/runtime? | Integration design |
| G-03 | **Asset handoff**: how clips become resolvable by SceneSignal (shared folder, mounted volume, object storage, or an upload step). | SceneSignal must resolve assets with its own storage port. | Where do the generation app's outputs (e.g. artifacts returned from the Kaggle notebook) finally land? | Possibly a new `AssetStoragePort` adapter (e.g. S3-style) in SceneSignal; upstream copy step on the other side |
| G-04 | **Asset preparation rules**: transcoding or normalising unusual formats before extraction (if wanted). | Keeps the extraction core free of ingestion logic. | Which formats the generation app and users really produce | Upstream ingestion/preparation component |
| G-05 | **Per-clip vs. merged-video analysis policy**: analyze each generated clip separately (one asset per job) and/or the stitched result. | Spec 4.3 supports both; production grouping rides in `production_id` / `order_index`. | When in the generation workflow should extraction run (before or after stitching)? | Integration design |
| G-06 | **Identifier mapping and idempotency keys**: deterministic `job_id` / `asset_id` per generated clip. | Idempotent retries (D-04). | The generation app's own scene/clip identifiers | Adapter |
| G-07 | **Result consumption**: sync response vs. polling `status`/`result` vs. callback; where results are stored and for how long. | The editing intelligence module will consume the document. | Latency expectations; sync/async decision (needs Chunk 11 behavior in practice) | Integration design; possibly new SceneSignal endpoints |
| G-08 | **Error and retry mapping**: how SceneSignal error codes (C.4) translate to the generation app's retry/regeneration logic. | Avoid double retries and silent failures. | The generation app's failure model | Adapter |
| G-09 | **Authentication, authorization, network boundaries, secrets** between the apps. | Chunk 11's API has none by design. | Deployment topology | Integration design |
| G-10 | **Deployment and runtime separation**: shared vs. separate environment, FFmpeg availability, GPU/vision provider configuration. | Addendum §3: no shared runtime assumed. | Hosting decisions | Ops |
| G-11 | **Vision provider selection and real adapter** behind `VisualAnalysisPort`. | Milestone 1 uses fakes only. | **Your authorization** of a specific provider and budget; cost measurements (Part F, R-4) | New SceneSignal adapter + contract tests |
| G-12 | **Consumer-driven contract tests** between SceneSignal and the adapter, using the exported JSON Schemas in `docs/schemas/` and shared example jobs. | Detect drift (R-13). | Adapter exists | Both repos |
| G-13 | **Version negotiation and upgrade policy** for `contract_version` / `schema_version`. | Independent release cycles. | Release process for both apps | Both |
| G-14 | **Observability**: propagate `correlation_id`, define log/metrics/trace conventions across both apps. | Debugging cross-app failures. | Logging stack of the generation app | Both |
| G-15 | **Data retention and privacy**: retention of results and derived frames, deletion on request. | Derived artifacts can contain user content. | Policy decision | SceneSignal config + integration |
| G-16 | **Feedback loop to future editing intelligence and regeneration decisions.** | Spec excludes it from Module 01. | Module 02 (editing intelligence) specification | Future modules |
| G-17 | **Rollout plan**: feature flag, shadow runs on real productions, comparison against manual review. | Safe introduction. | G-01…G-08 done | Integration |

## G.2 🧑 FOR YOU — Questions to answer when you are ready to integrate (not now)

1. Where do generated clips end up after the Kaggle notebook returns its artifacts, and who copies them there?
2. Should extraction run per generated clip, on the stitched video, or both?
3. Do the two applications run on the same machine and storage, or separately?
4. Should SceneSignal be called synchronously or as a background job?
5. What identifiers does the generation application already assign to scenes, clips and productions?

---

# APPENDIX 1 — Spec §17 acceptance checklist mapping (📎 SHARED)

| Spec §17 criterion | Satisfied in chunk |
|---|---|
| One canonical versioned extraction-job contract | 1 |
| One canonical versioned result contract | 1 |
| Generated and uploaded clip use the same contract | 1, 9 |
| Channel and production context optional | 1, 9 |
| Application core depends on ports, not provider SDKs | 0 (architecture test), 9 |
| Module callable without starting the HTTP API | 9, 11 |
| Local test setup works without paid services or keys | 0–12 |
| Inspects actual media, not supplied metadata | 3, 9 |
| Handles short and longer clips without assuming duration | 3, 5, 9 |
| Extracts frames at recorded timestamps | 4, 9 |
| Represents detected shots with valid intervals | 6, 8 |
| Structured visual observations via a fake provider | 7, 8, 9 |
| Temporal claims distinguish direct evidence from inference | 2, 8 |
| No fabricated analysis when a provider fails | 10 |
| Invalid and corrupt media produce typed failures | 3, 9 |
| Bounded retries for transient provider errors | 10 |
| No pointless retries for permanent failures | 10 |
| Output validated before return or persistence | 8, 9, 10 |
| Provenance and warnings recorded | 8 |
| Temporary artifacts cleaned according to policy | 4, 9, 10 |
| Unit tests pass without paid providers | all |
| Port contract tests cover implemented adapters | 3, 4, 6, 7, 12 |
| Timeline conversion and timestamp precision tests | 2 |
| Fixtures and limitations documented | 3, 12 |
| All completed work documented in expected locations | every chunk (handoff), 12 |
| Handoff note identifies next module/capability | 12 |
| **Addendum 01** — new, independent project directory (greenfield) | 0 (checks, own repo), 12 (independence drill) |
| **Addendum 01** — standalone project documented and distinct from the generation application | 0, 1 (`integration-boundary.md`), 12 |
| **Addendum 01** — integration is future work; contracts are the immediate requirement | Part G; 1; 12 (`acceptance.md`) |
| **Addendum 01** — generation adapter documented as a boundary, not implemented | C.7b; 1 (`integration-boundary.md`); Part G |
| **Addendum 01** — uploaded, imported and generated assets share one extraction boundary | 1 (examples), 9 (C-11 test) |
| **Addendum 01** — minimum asset requirements, input constraints, validation behavior, failure semantics documented | S.4, S.5; 1 (`input-contract.md`); 3 (content-based validation) |
| **Addendum 01** — explicit versioned job documents for manual development | 1, 9 (`extract --job`), 12 (smoke script) |
| **Addendum 01** — channel/production/prompt context optional; arbitrary valid video extractable | 1, 9 |

---

# APPENDIX 2 — 🧑 FOR YOU — Quick troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| `ffprobe not found` error | FFmpeg not on PATH | Install FFmpeg; reopen terminal; `ffprobe -version` |
| FFmpeg tests skipped | Same as above | Expected when FFmpeg is absent; install it to run them |
| A fixture says `unavailable` | Your FFmpeg build cannot make it (e.g. rotation matrix, VFR) | Acceptable for "best effort" fixtures; tell me which |
| `ASSET_ACCESS_DENIED` for a file you own | File is outside the allowed roots | CLI: the file's folder is added automatically; API: set the allowed-roots env var (see README) |
| Gemini changes things outside the chunk | Standing Rules not pasted | Paste E.0 again, ask it to revert out-of-scope changes |
| Gemini says "contradiction" | Rule collision found | Paste its CONTRADICTION REPORT to me; I will resolve it and update this file |
| Test count differs from my notes | Counts are approximate | Only failures and missing expected behaviors matter |
| Gemini asks to read or change the generation application | It is outside the greenfield boundary | Refuse. Re-paste E.0. Its working directory must be `SceneSignal/` |
| Chunk 0 stops at "greenfield checks" | `<PARENT_DIR>` not replaced, folder not empty, or parent is inside another Git repo | Redo the Pre-flight (D.0b); pick another parent if needed |
| `git rev-parse` in `SceneSignal/` shows a path above it | The project was created inside another repository | Move/recreate `SceneSignal/` elsewhere and restart Chunk 0 |
| Unsure where the generation app lives | — | Tell me its folder name and location; I will propose a parent directory |


**End of the SceneSignal Module 01 document (revision 2.0).** Next deliverable after approval and completion of Chunk 12: either the real vision-adapter specification (needs your provider authorization) or Module 02.
