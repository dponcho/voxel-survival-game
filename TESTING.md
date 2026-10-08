# Testing and build verification

Design baseline: 2026-09-05; Java core and target-report requirements revised 2026-09-26. Status: required test plan; executed results are recorded in milestone evidence. References to scripts and application flags below are interfaces to implement in M0 and subsequent milestones.

## 1. Evidence levels

| Level | Execution environment | Establishes | Does not establish |
| --- | --- | --- | --- |
| Static/native | Codex Cloud and GitHub Actions | Data validity, algorithm properties, supported compiler behaviour | Rendered appearance or laptop fps |
| Engine integration | Matching custom Linux/Windows editor or export, headless | Module availability, imports, world logic, save/reload and process lifecycle | Real GPU rendering correctness/performance |
| Render smoke | Cloud software-GL environment where available | Shaders load, expected objects appear, screenshots lack gross failures | HD 620 driver behaviour or speed |
| Portable artifact | Extracted Windows ZIP in Actions | Packaging, headless launch and dependency audit | Absence of all preinstalled runtime dependencies on a player's machine |
| Target execution | Same downloaded game running on the i7-7600U/HD 620 | Actual driver launch, frame pacing, memory and thermal performance | Every imaginable background task or future world |

The target check is built into the game and runs itself. The user downloads, extracts and launches the same executable used for play; no local test runner, profiler, compiler, scripts or self-hosted Actions agent is required. All development and formal test implementation remain in the cloud. If even running the game's diagnostic mode is outside the available feedback, target performance stays unverified.

## 2. Cloud gates by change type

| Change | Required checks |
| --- | --- |
| Documentation only | Links, internal consistency, explicit status/assumptions; no redundant game test run |
| UI/gameplay scripts | Matching-editor import/parse, affected integration test, Windows export and self-test |
| Native world/mesher/scheduler | Native unit/property tests, affected integration/stress tests, rebuilt custom templates and export; relevant target scenarios before acceptance |
| Generation/content IDs | Cross-platform golden hashes, seed/structure cases, progression/content validation, old-world compatibility |
| Persistence/inventory/crafting | Transaction invariants, replay, crash injection, disk-error cases, old-save fixtures |
| Engine/dependency/renderer change | Clean-cache build, full native/integration suite, package audit, render smoke and full target qualification |
| Release candidate | All mandatory checks, full progression run, soak, exact-build target evidence and package digest |

Measure cloud algorithm benchmarks as regression signals. Use normalized work counts and repeated timings on the same runner class; do not treat a noisy shared runner as an absolute hardware oracle. Flag a reproducible >10% algorithm regression for investigation, but a small percentage change does not excuse an absolute target failure.

## 3. Meaningful native tests

| System | Required cases and invariant |
| --- | --- |
| Coordinates | Floor division/local coordinates at -17, -16, -1, 0, 15, 16 and world limits; reconstruction returns the original coordinate |
| Generation | At least 32 fixed seeds and 1,024 selected chunks; identical canonical block/state hashes on Windows/Linux and repeated runs |
| Request ordering | Sequential, reversed, randomized and concurrent generation; cancellation/restart yields the same final chunks |
| Structures | Anchors on faces/edges/corners and overlapping features; no seams, duplicates or load-order dependence |
| Meshing | Single block, two blocks, solid volume, empty chunk, borders, checkerboard and mixed materials; correct visible faces/winding and bounded output |
| Greedy path, when implemented | Coverage equals a simple reference mesher; no merge across incompatible light/material/AO; tiled UVs remain correct |
| Light | Add/remove emitter, roof opened/closed, chunk unload/reload, boundary propagation; converge to the reference bounded solver |
| Collision | Negative coordinates, seams, crouch clearance, ledges, fast falling, stairs if supported, missing terrain and world boundaries |
| Transactions | Mine/place/craft/drop/collect/death/container transfers preserve item accounting and never apply only one side |
| Scheduling | Queue caps, stale result rejection, epoch reuse, fairness for saves, bounded catch-up and cancellation |
| Persistence | Snapshot plus journal replay equals authoritative state at the same sequence; pruning/migration cannot skip state |
| Content | Unique stable IDs, valid references, finite numeric values, recipe reachability and asset ownership/licences |

Use reference implementations only where they provide an independent oracle. Tests that repeat the production algorithm line-for-line add little confidence. Run sanitizers on the engine-independent native core in Linux CI; enable appropriate assertions in debug integration builds. Release performance tests use release code.

Golden files include format, generator/content hash, seed, coordinates and expected canonical data. Do not hash compressed blobs or unordered container iteration as the determinism oracle. A golden-output change is reviewed as a world-generation change, not automatically accepted to make tests green.

## 4. Engine integration tests

Create a small headless project route which instantiates native terrain and the project module, pumps the real engine loop, waits on explicit completion conditions and quits with an unambiguous exit code. Fixed sleeps are not readiness checks. Every test has a timeout, useful diagnostics and cleanup limited to its temporary directory.

Cover: create world; generate safe spawn; move and edit across borders; reject invalid/unready edits; save barrier; close; reopen; compare state; load a different world while old tasks are still completing; revisit evicted chunks; and exercise UI/state transitions without an editor session.

Missing data must never become air in collision or mining. Inventory is charged only for accepted placements. A stale meshing result cannot overwrite a newer edit. Reopening the same coordinate in another world cannot reuse an old session's result. These are blocking invariants.

Instantiate every shipping scene and content family through tests or a content-validation scene. Parsing only the main script does not validate all resources. Use warning/error policy appropriate to owned code; retain upstream warnings separately instead of suppressing meaningful project failures.

Review animated presentation in motion over several cycles and during movement,
turns, edits and transitions. Check repetition, synchronized resets, popping,
flicker and input responsiveness as well as still images. Record deliberate
visual compromises with their scope and replacement milestone; the M1 rain
proxy's synchronized appearance remains a deferred M5 defect, not a passed
weather-quality check. An optimization needs a measured benefit and preserved
behaviour, including these motion checks when relevant. No overall test-pass
percentage can override a failed correctness or performance gate.

### Core Java-style behaviour checks

Use [the core reference contract](docs/JAVA_CORE_REFERENCE.md) for movement/sneak ledges, target reach, block hardness/tool drops/durability, stairs/slab collision, 9+27 inventory/armour/offhand, shaped/shapeless 2×2/3×3 crafting and recipe-book assistance. Test furnace input/fuel/output transactions, hunger/saturation/regen, bed obstruction/respawn, death-drop expiry in loaded simulation time, bounded cap saturation without item loss, farming/breeding, local water/lava and falling-block borders. Unloaded crop/furnace work must stay paused. Verify Creative-style flight/instant breaking/catalogue independently of survival consumption.

Compare original rendered block materials, silhouettes, held tools, hotbar/grid and interaction feedback at 720p against the intended reference. Record intentional differences; a matching interface label is not behaviour or visual proof. Automation circuits, enchanting, brewing, extra dimensions and boss progression are post-1.0 and are not exit tests for core 1.0.

## 5. Persistence fault injection

Use temporary worlds and a deterministic driver. Inject failure before/after transaction append, commit, snapshot write, pruning watermark, backup and migration. The cloud process controller can terminate the game at declared test hooks; this is never performed against a player's saves.

After restart, assert that all durably acknowledged transactions remain, each mutation is atomic and later undurable work is either entirely present or absent according to committed sequence. Mining must not regenerate a block while retaining its awarded item; crafting and death recovery must not duplicate possessions.

Inject disk-full, write denial, damaged payload checksum, busy database and interrupted backup/migration. Ensure the game does not display “Saved” after a failed barrier. Validate recovery UI and refusal of unsupported future versions. Test competing game processes and verify a world lock prevents a second writer.

Keep fixtures for every supported released save format. Migrate a copy, compare the canonical world/player state and retain the original on failure. Use a consistent database backup mechanism; include WAL behaviour in tests. A killed process is not equivalent to a real power-loss test, so label that limitation and use storage fault simulation for the broader cases.

## 6. Portable Windows artifact checks

For every code-bearing candidate:

1. Export from the exact matching custom editor and template bundle. Record their hashes and module registrations.
2. Verify `Cairn.exe`, `Cairn.pck`, build metadata, notices and required runtime files exist. Confirm PE architecture is x86_64.
3. Audit transitive DLL imports. Compare against the intended Windows system-DLL allowlist; statically link or include approved non-system dependencies. A launch on a runner containing Visual Studio does not prove the VC runtime is bundled.
4. ZIP the distribution, calculate SHA-256, extract into a fresh directory and run the extracted executable's headless self-test with a timeout.
5. Repeat the path checks with spaces, non-ASCII characters and a different working directory. Launch-path resolution must use the executable/project paths, not the shell's current directory.
6. Verify offline operation, absent development tools on the launch path, writable default saves and a clear response when portable-data storage is read-only.
7. Retain the artifact, checksum, test report, build manifest and separate symbols. A release must reuse these exact package bytes.

A standard hosted Windows VM may lack a usable OpenGL context. Headless success remains a logic/package result. If render smoke is unavailable, report it unavailable; do not fall back to claiming headless mode rendered the game. A Linux Mesa/software-GL smoke run is supplemental, with its renderer explicitly recorded.

Ordinary artifacts may expire under repository retention settings. Keep accepted milestone/release packages and their provenance in durable release storage according to repository access settings. Do not make a private project public to obtain different CI limits.

## 7. Built-in performance harness

Expose **Run performance check** in the main menu. It creates a temporary benchmark world and uses the fixed HD 620 profile. Display progress, allow cancel and write reports locally. It does not read or alter player worlds and does not automatically send telemetry.

A quick diagnostic may run fewer scenarios, but cannot claim full certification. The complete check performs a 3-minute warm-up followed by:

| ID | Scenario | Duration | Frame gate |
| --- | --- | ---: | --- |
| N1 | Settlement traversal: fixed camera route, 12 active creatures, storage/crops, day and night samples | 3 min | Normal 60 fps |
| N2 | Cave mining and border building: 2 accepted edits/sec, lamps placed/removed, regular autosaves | 3 min | Normal 60 fps |
| H1 | New-terrain sprint: 6.5 m/s, 180° turn every 15 sec, representative region/cave boundaries | 4 min | Heavy ≥30 fps |
| H2 | Combined streaming: sprint plus rain, 24 active creatures, autosaves and 4 edits/sec where valid | 4 min | Heavy ≥30 fps |
| N3 | Dense permitted construction: upper supported complexity, view rotation and ordinary interaction | 2 min | Normal 60 fps |
| R1 | Stop/recover and revisit previously edited terrain | 1 min | Normal after ≤5-sec backlog recovery; heavy gate during recovery |

The full check is approximately 20 minutes including warm-up. During development, run only applicable scenarios; M1 can use deterministic proxy actors/work loads before the final systems exist. Proxy results qualify only the engine experiment. Replace proxies with real systems and rerun before their milestones and 1.0 qualification.

The camera/input route, seeds, weather schedule and workload version are committed. Scenarios use simulation-time commands so a slow run cannot reduce the workload and then appear faster. Report simulated time versus wall time; stalled or dropped simulation ticks fail the run. Track actual accepted edits and creature activity so a silently empty test cannot pass.

Run the suite uncapped for deadline capacity, then a paced diagnostic pass for display/input behaviour. Record first-use rendering separately: shaders/content must be prepared during an explicit loading state or pass first-encounter gameplay deadlines. Shader caches from a prior run must not hide a recurring startup problem.

## 8. Measurements and report schema

Use monotonic high-resolution timing. Measure application frame intervals and engine phases directly, with asynchronous GPU timers only where supported; never block waiting for a GPU query. A missing GPU metric is `unavailable`, not zero. An engine frame callback is not proof of physical scanout time: label presentation estimates accurately. If pacing remains ambiguous, retain “inconclusive” rather than overstating the measurement.

Phase attribution is mandatory: label preparation, measured gameplay, paced diagnostics and retirement separately. Retain lifetime counters as context, but assess individual-operation limits using phase-local maxima and bounded per-frame payload/time records. Subtracting cumulative maxima is invalid. Include enough event context to distinguish native work, diagnostic work, renderer work and unavailable OS/driver attribution. Completion text must not imply a passing evaluation. Preserve first-use failures and raw paced misses. Missing measurements and unstable A/B comparisons remain inconclusive. These requirements address the [September 25 target review](docs/M1_TARGET_REVIEW.md) without relaxing any gate.

Each report contains:

| Field group | Required data |
| --- | --- |
| Identity | Game commit, engine/module commits, executable and package hashes, content/generator/scenario versions |
| Machine | CPU/GPU/driver/OS, renderer path, installed and available RAM, power state, display refresh; unknown values remain unknown |
| Configuration | Resolution, render scale, visual/data radii, worker count, all relevant effects and caps |
| Frame results | Sample counts, p50/p95/p99/p99.9/max, average fps, deadline-miss count and worst-event context |
| Resource results | Peak private bytes/working set, GPU counters or estimates, per-pool high-water marks, draw calls and triangles |
| Streaming | Requested/completed/cancelled jobs, queue high-water marks, service/arrival rate, upload/delete time, readiness stops |
| Correctness | Edits accepted/rejected, durable watermark/lag, stale results discarded, collision/readiness errors |
| Outcome | Per-scenario pass/fail/inconclusive, explicit reasons and raw-data filenames |

Write `summary.json`, `summary.txt` and a bounded/streamed frame CSV under a diagnostics directory. Keep diagnostic overhead below 1% in an A/B check and account for file I/O. Long runs stream buffered samples rather than growing an unbounded array. Exclude personal usernames, full save paths, private world contents and credentials from the shareable report.

For a candidate to be target-certified, its exact executable and content must match the accepted report. A report from a debug editor or an older game commit cannot certify the release. The evaluator compares against PERFORMANCE.md; p99 alone cannot override maximum-frame or throughput failures.

## 9. Long-run and adversarial checks

Before M7 completion, run a 30-minute outward journey and a 2-hour automated cloud logic/save soak; perform a sustained target gameplay run to capture thermal/memory behaviour. Reopen worlds five times, retrace edited regions, saturate permitted entities, cancel loading, switch worlds, pause/resume, alt-tab and exercise loss/regain of mouse capture.

Construct a checkerboard volume **beyond** the admitted envelope. Correct behaviour is bounded rejection or a clear overload response, not allocation failure, invisible blocks or a false performance pass. Separately, the densest **permitted** construction must satisfy normal gameplay requirements. Test fluid/light queue saturation and recovery without lost updates.

Pause the application for a long interval, then resume. Do not simulate thousands of catch-up steps in one frame. Quit while saves are pending; terminate the process in a temporary test world; reopen it. Measure actual world-load/save time on cold and warm paths.

## 10. Result policy

Use `passed`, `failed`, `inconclusive` and `not_run`. Include a command/CI run and artifact identity for executed checks. Fix implementation failures before expanding the affected system. Preserve failing seeds and reports as compact regression fixtures where they identify a real bug.

Cloud-only success is reported as **cloud passed; target performance unverified**. Without a target-hardware report, the project may ship a clearly labelled experimental candidate for the user to run, but it must not claim the hard performance requirements are achieved.

### Cloud endpoint/count precision controls

`benchmark_endpoint_precision_tests.gd` uses the production route ledger,
diagnostic ledger and evaluator with injected clocks. It saves bounded CSV rows
for 28 H1/H2 controls, including null/known closure, endpoint redistribution,
acknowledgement duration, callback-count masking/drift, missing/reordered/stalled
workloads, failed actor activity/individual upload, unavailable terminal data,
I/O failure and overlapping dose. It executes no target or terrain measurement.

`tools/qa/endpoint_precision.py` independently checks closed-form integer totals,
streams each saved CSV, and reconciles previous/final callbacks, timing blocks,
seven route bins, acknowledgement markers, nested callback writes, writer drain,
closure dose and preparation/measurement/retirement boundaries. It checks saved
production decisions using the existing exact-rational oracle. Supplemental
duration/count decomposition and unscaled terminal contributions are descriptive
only. A null quartet deliberately cannot satisfy the production known-positive
dose guard. Missing data stays unavailable/null; no terminal rows are trimmed.

Actions enforces 1 MiB control JSON, 112 fixed raw CSV files totaling at most
32 MiB, and a 60-second injected-clock command timeout. The runtime ledger still
has seven bins and no retained per-frame array or new queue. The existing sixteen
method controls, 26 route controls, thresholds and verdicts remain unchanged.
Static regressions expand independent clocks and reject corrupt rows, lost tails,
changed phase/I/O scope, waived operation failures, altered decisions and bounds.
These checks do not qualify HD 620 precision, per-frame CPU/GPU sensitivity or
shared instrumentation overhead. See [docs/M1_ENDPOINT_PRECISION.md](docs/M1_ENDPOINT_PRECISION.md).

### Experimental fixed-work elapsed/count controls

`benchmark_fixed_work_tests.gd` adds 44 clock controls, retaining the old sixteen
method, 26 route and 28 endpoint controls. `tools/qa/fixed_work.py` independently
reconciles exact duration thresholds, count cancellation, terminal/acknowledgement
uncertainty, phase/drain/dose scope, unavailable/null values and saved raw rows.
Existing release calibration smoke also checks the supplementary saved assessor
and external combined finalization. Bounds: 176 CSVs/64 MiB, 3 MiB control JSON,
60-second clock command; no new runtime queue. All legacy assessments and
qualification flags remain authoritative. See [M1_FIXED_WORK_SENSITIVITY.md](docs/M1_FIXED_WORK_SENSITIVITY.md).

### Experimental per-callback CPU dose controls

`benchmark_cpu_dose_tests.gd` adds 54 clock controls/216 saved phases, bounded at
4 MiB JSON, 64 MiB raw CSV and 60 seconds. The independent rational/streamed
oracle verifies exact threshold/null semantics, count/wait/route-mix masking,
body/window drift, all guard faults and previous/final callbacks. A separate
native SHA-256 `Node._process` probe executes 128 real callbacks each in the
matching editor and exported release; every digest, body/dose span, writer drain
and external finalization is independently reconciled. Bounds: 4 KiB buffer,
512 updates per dose, 32 pending rows, 1 MiB evidence/60 seconds per invocation.
This verifies software sensitivity and CPU placement, never CPU service,
hardware precision, GPU cost or shared overhead. Ordinary benchmark smoke must
retain CPU sensitivity `not_run`; all old control expectations stay unchanged.
See [M1_CPU_DOSE_SENSITIVITY.md](docs/M1_CPU_DOSE_SENSITIVITY.md).

### Experimental frame-boundary/slack controls

`benchmark_frame_slack_tests.gd` retains 30 modeled quartets/120 CSV phases,
bounded at 2 MiB JSON, 2 MiB raw and 60 seconds. The rational/raw oracle validates
owned callback-to-successor cycles, exact 1% boundaries, slack/count masking,
final-only dose, endpoint uncertainty and every missing/failed/unstable guard.
An internal application probe runs 256 native-hash bodies plus eight closing
anchors in both editor and release, with temporary 100-fps limiter/restoration.
Bounds: 4 KiB input, 8,192 updates per dose, 32 pending rows and 2 MiB/60 seconds
per invocation. Every digest, engine-frame successor, last body, exclusive cycle,
callback/anchor/drain/controller gap and external finalization reconciles.
Ordinary smokes retain `frame_slack_sensitivity: not_run`; old controls remain.
These are software placement checks, with actual effect envelopes descriptive;
CPU service, GPU/presentation, hardware precision and shared overhead stay null.
See [M1_FRAME_SLACK_SENSITIVITY.md](docs/M1_FRAME_SLACK_SENSITIVITY.md).

### First moving-frontier boundary replay

Matching editor and packaged release each run four actual native baseline/
corrected cases (16³, one/two workers) from the hashed public first-alarm seed.
Baseline must reproduce missing submitted geometry inside 96 m; corrected must
already be submitted and retain unchanged scan coverage through reference
handover. A new unprepared gap still fails, missing inputs remain null, and
native cancellation/drain and existing bounds remain visible. Each invocation
retains 80 observations, capped at 128 rows/1 MiB, with per-case 60-second
settlement/drain limits and a 600-second command deadline. The independent
saved-report/source/geometry oracle and mutation tests supplement, never replace,
existing frontier/operation/edit/evaluation and profile smokes. See
[M1_FRONTIER_BOUNDARY_REPLAY.md](docs/M1_FRONTIER_BOUNDARY_REPLAY.md).

### Concurrent edit during the next frontier handover

Matching editor/release each run eight actual native cases at the public second
16³ +X boundary: stationary, transfer, cancellation requested before acquisition
and during overlapping ownership, each with one/two workers and one accepted
border edit. The independent saved oracle checks both current edit revisions,
actual resource identities and `1 -> 2 -> 1` visual references, next-column
submission, preserved confirmed-empty coverage, cancelled/completed terminal
source, native drain and unchanged 200 ms acknowledgement / 750 µs operation
guards. Collection close never becomes native acknowledgement. All 24 native
preparation/transfer/retirement phases reconcile with streamed operation rows.
Bounds are 160 observations, ten observed blocks per row (native API maximum
16), 1 MiB summary, 20,000 operation rows / 8 MiB, 60-second settlement/drain
and 600-second command deadline. Null/invalid/oversized/malformed/duplicate and
absent-block native controls, exact saved sums/peaks/phase closures and Python
mutation regressions supplement all earlier controls. See
[M1_FRONTIER_EDIT_HANDOVER.md](docs/M1_FRONTIER_EDIT_HANDOVER.md).
