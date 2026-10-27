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

The opt-in [operation-event capability](docs/M1_OPERATION_WITNESSES.md) adds a
twelfth engine-independent sanitizer suite, matching editor/release real-entry
controls and re-signed saved-reader faults. Its injected guard, counter and cap
failures must remain failed. Complete saved Windows/Linux candidate audits replay
the raw binary, phase/frame union accounting and full writer bounds. No new route
or target qualification follows from these capability controls.

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

### Continuous H2 travel replay

The cloud editor/release each run the production 600-tick H2 route with one/two
workers through four +X handovers. Independent saved evidence checks all movement,
actor/rain/edit/storage commands, actual resource ownership and current revisions,
all terminal frames/edits/native phases, operation guards and complete drain.
Storage and time limits, negative controls and scope are predeclared in
[M1_FRONTIER_TRAVEL.md](docs/M1_FRONTIER_TRAVEL.md). Failed timing guards remain
failures; functional cloud completion does not qualify a target profile.

### Native pending-mesh admission comparison

Eight additional fresh 600-tick H2 processes compare FIFO/priority in editor/
release with one/two workers. Six native sanitizer suites include an independent
geometric-minimum/FIFO/trace-bound test. Saved readers verify every pending vector,
actual admission permutation, four-task budget, phase boundaries and complete
matched travel evidence. Coverage and operation/diagnostic failures remain
visible. Bounds and stopping conditions are predeclared in
[M1_MESH_ADMISSION.md](docs/M1_MESH_ADMISSION.md).

The independent post-package audit downloads the published player and verifies
byte round-trip, inner ZIP CRC/paths, PE/PCK/entry MD5/native identity, eight
self-test reports and imports. It re-reads all saved trial/control evidence,
compares the 42 ordinary heavy contracts with a durable public baseline, and
rejects 26 mutations of actual saved reports. Pre-admission missing/null block
observations remain valid missing states; missing-after-admission and non-null
revision changes fail. CI 37878551633 verifies 88 Python regressions, six
sanitizer suites and all eight matched admission runs. The on-demand inspection
workflow is retained for explicit review of the original failing cloud evidence;
it is not an automatic qualification check. Engine execution stays in Actions.

### Bounded H2 camera reversal

Eight additional FIFO/priority editor/release processes with one/two workers run
1,200 fixed ticks on the original outward H2 route, with camera reversal at tick
900, all 80 due edits and 20 saves. The existing 600-tick checks remain required.
Independent controls check exact camera assignment/fingerprint, eight handovers,
current edit/revision/resource evidence and legitimate outside-96 m eviction;
missing states remain null. The post-package audit re-reads all saved trials,
coverage windows and terminal accounting, and rejects twelve further mutations
of actual reversal/retention/evidence guards. Limits and stopping conditions are
predeclared in [M1_FRONTIER_REVERSAL.md](docs/M1_FRONTIER_REVERSAL.md).

CI 38333317049 passes all three jobs, 91 Python regressions, six native sanitizer
suites, every prior check and the eight new processes. Published-download and
separate read-only saved audits verify all arithmetic/classification/phase/
witness fields, 78 PCK MD5s, eight self-tests and 38 imports; the preserved missing-
file mutation's OS exception text/temporary path is the sole environment
difference. All 26 older and twelve new saved mutations are rejected. Priority
has zero actual coverage alarms before/after the camera turn and all eighty
original edits submitted in each run. FIFO's four edit-duration failures and one
timeout remain. Evidence-reader success does not imply a passing scenario;
priority assessments remain inconclusive under the unchanged diagnostic guard.
No local engine execution or HD 620 qualification is claimed.

### Ordinary admission and complete terrain budget review controls

The ordinary check runs `--ordinary-admission-check` in fresh editor/release
one/two-worker FIFO/priority processes, twenty seconds / 1,200 fixed ticks each.
It inherits production route/camera/work and ordinary ledgers, disables admission
tracing and travel/resource observation, preserves all 80 due edits / 20 proxy
saves / 28,800 actor updates, and retains preparation/acknowledgement/retirement/
writer/finalization accounting. Missing trace/resource fields are unavailable/null.
Independent saved readers verify exact commands, original revision terminal
events, measured coverage, complete frame/operation evidence and full drain.
Integrity success and measured bounded acceptance are separate decisions.
This mode stops startup observation before gameplay, so it does not run the
six-phase startup-smoke validator. Dedicated startup checks retain that validator;
ordinary frame, edit, operation, drain and independent saved checks still run.

Terrain ledger v2 supplements the original eighteen CSV columns with data
application and ten frame-budget columns. Native and independent controls cover
two individually legal 600 µs operations exceeding a normal 1 ms allowance,
application spans above 750 µs, nested-child union accounting, phase-split native
frames, 512 KiB/1 MiB frame payload and independent 256 KiB individual payload.
Legacy rows remain partial evidence. Full-height cuboid demand feasibility is
checked before profile selection; actual vertical/directional runtime evidence
is still required. No cloud timing certifies target throughput or deferred work.

CI `38912228615` passes all three jobs, 97 Python regressions, six native
sanitizer suites, all prior engine checks and all eight ordinary processes.
Published-download and separate read-only saved audits verify every comparison,
80 PCK MD5s, eight self-tests, 38 imports and all 38 rejected mutations. All
four priority runs pass bounded acceptance; FIFO and broader operation failures
remain visible. Target and shipping diagnostic qualification remain open. See
[candidate, results and next task](docs/M1_ORDINARY_ADMISSION.md).

### Full-height and real direction changes

`--full-height-check` runs a separate 32³/one-worker native fixture over
`Y[-64,192)` with its surface at Y=64. Editor/release each run baseline and
`--directional-preparation` cases: 4,320 ticks, +X/-X/+Z actual movement, 288
original edits, 72 proxy saves and 103,680 actor updates. The independent reader
checks full initial demand, negative-coordinate demand arithmetic, the full
command/position history, genuine edited-data/mesh eviction and reload, complete
frame/edit/operation records and finalization. Corrupted observations and twelve
post-package saved mutations must fail. The preceding 42 heavy contracts remain
unchanged. Detailed bounds and stopping conditions are predeclared in
[the full-height experiment](docs/M1_FULL_HEIGHT.md). Matching CI `38922744175`
and the independent downloaded-file audit pass all four cases and reject all
twelve new saved mutations (50 total with earlier controls). Both prepared
cases pass bounded cloud acceptance; target performance remains unqualified.

### Shipping inventory and finite pilot

`--shipping-pilot-check` exercises the declared bare/shipping/forensic inventories
and the single finite null/known-positive protocol. The exact-rational reader
checks complete boundaries, all original route/callback/edit/save/dose records,
native phases and drains. Six editor/release single-mode companions and the
nine-trial release pilot completed in CI `38985239110`. The pilot is inconclusive:
two operation overruns invalidate controls; no shipping quartet or target run
followed. Retain that failed CI and its original evidence.

The saved reader separately reports `evidence_integrity`, `measurement_valid`
and the overhead assessment. A complete, honestly recorded operation failure can
pass evidence verification while remaining invalid for estimation. A mismatch
between phase evidence and validity flags fails verification. So do missing work,
incomplete boundaries, I/O failure, engine errors and unexpected process exits.
The cloud launcher checks the saved records before accepting the expected exit
code 1 of an inconclusive measurement. This does not relax operation thresholds.

The QA-only follow-up reuses the original downloaded ZIP and reports. It runs
pure Python regressions, seven-folder reconciliation, 12 saved corruption cases,
and an isolated replay of all preceding evidence and 50 preceding saved faults;
it executes no engine and does not repeat the runtime pilot. The independent
Windows/Linux comparison normalizes only missing-file OS error wording. All
verdicts, counters, hashes and other fields remain exact.
See [the protocol/result](docs/M1_SHIPPING_DIAGNOSTICS.md) and its committed audit
record. The October 17 [v2 decision](docs/M1_DIAGNOSTIC_COST_POLICY.md) now selects
raw process-cycle demand and defines the prospective finite sequence. Its first
implementation increment verifies counter capability only: exact integer/raw
decimal serialization, unavailable/failed counters, ordered read brackets and
one bounded native hash/wait/joined-worker smoke per matching editor/release.
The process counter must retain the exited worker's witnessed demand. A wait does not
require zero process cycles because other threads can run. These checks establish
capability, not sensitivity or a cost pass. Rebuild matching native templates,
retain existing required correctness/package checks and produce a new candidate.
The counter-only implementation and exact evidence checks are documented in
[M1_CPU_CYCLE_CAPABILITY.md](docs/M1_CPU_CYCLE_CAPABILITY.md). The reusable workflow
defaults `historical_v1_pilot` to false, preserving v1's pure checks/entry points
without repeating the completed runtime pilot during this increment.
CI `39073452514` passes all 141 Python regressions, seven native sanitizer
suites, matching binary qualification, both bounded capability smokes, existing
integration/offline package checks and downloaded Windows/Linux audits. Each
smoke rejects 12 saved counter corruptions; all 50 preceding saved faults remain
checked. Raw records, hashes and retained broader failures are in the linked
counter evidence record. No cost sensitivity or target qualification follows.
Do not rerun v1 or start the v2 route pilot in that increment. V2's later controls
require a whole-process null plus an in-route thread-cycle-witnessed positive,
with exact interval arithmetic, all workload/operation guards and the declared
9/13-trial stop. No target qualification follows from synthetic/CI controls.

### V2 cycle-demand method and finite pilot

`--shipping-cycles-check` runs 28 pure rational-method cases, eight unsigned
request vectors, five shared-boundary/failure controls, and one zero/one bounded
positive native SHA API check plus four rejected requests per matching editor/
release. `m1_cycle_exact.gd` keeps raw counters and rational cross products as
canonical decimal strings. The independent `shipping_cycles.py` reader uses
integers and `Fraction`; no floating-point value selects a CPU gate outcome.
Native loop tests cover exact requests, failed/decreasing counters, SHA failure,
512-update and 50 ms hard caps. Ordinary snapshots and terrain clocks are unchanged.

The only `--shipping-cycles-pilot` launch in CI `39088740702` completed warm-up
plus four bare null trials. Every trial passes 4,320-tick work, all 288 edit
submissions, I/O, resources, coverage/readiness, complete drain and native
operations. CPU sections share the same six raw snapshot brackets; integer
midpoints partition exactly. Report serialization/flush precedes the final CPU
boundary. Original terminal-marker bounds conservatively expand both arms.

The empirical null range [-2.217168530%, +0.633380871%] contains zero but has
2.850549401% width; matching-section drift is 1.073468789%. Both strict below-1%
controls fail. Measurement validity is false and cost inconclusive despite
verified integrity and valid trial guards. No positive request or either later
quartet was run. Preserve the exact five-trial prefix; never pad or retry it.

157 Python tests and eight native sanitizer suites pass in Actions. The current
QA follow-up adds five saved-reader controls and passes all 162 Python tests in
Codex Cloud, checks native witnesses against their real ticks/route brackets,
and preserves honest counter failures. Saved corruption controls always change
the original value, including usable-control and measured-zero marker cases.
All 50 prior, 24 counter and 14 v2 saved faults are rejected. Windows/Linux and
the current stricter reader reproduce the same original candidate/pilot values;
rechecks launch no engine. Runtime tests were not repeated for QA/prose changes.

The native key, matching binary hashes, exact ZIP and all original trial records
are in [the v2 result](docs/M1_SHIPPING_CPU_CYCLES.md) and its committed evidence.
The live `shipping_cycles_pilot` input defaults to false. The
[saved review and prospective decision](docs/M1_SHIPPING_NULL_REVIEW.md) now verify
all 75 raw files and reproduce the original audit without an engine. Its new
reader decomposes width and section cancellation with exact rational arithmetic,
compares recorded native work and retains nested witness scopes. Eight new pure
tests cover incompatible zero/width requirements, strict boundaries, cancellation,
invalid trials, work counters, raw tampering and escaping links. No runtime suite
is repeated for this QA/review-only increment.

The chosen bounded native observer-attribution ledger and separate opt-in mode
are now verified in CI `39179723675`. Its one declared cloud process completes
warm-up + four bare trials, with every work/operation/attribution guard passing.
It stops at five with no positive request or shipping continuation. Independent
span/nesting/thread/worker-exit/count/byte audits pass on Windows and Linux.
Cost remains inconclusive and all original limits apply. No target qualification,
laptop action or M2 expansion follows.

### Common-observer attribution prerequisite

The separate `--shipping-observer-check` verifies nested raw spans, real UTF-8
qualification/proxy writes, a joined writer's retained cycle witness and three
failed API controls in each matching editor/release. The native core has a ninth
sanitizer suite for fixed-format unsigned serialization, ownership, nesting,
caps, counters, section errors and worker incarnations. The new independent
Python reader verifies bounded 192-byte raw records and charges nested spans
once. Its pure regressions reject false owners, missing/reversed/failed spans,
thread-ID reuse errors and finite-prefix violations.

The opt-in Actions attribution job is separate from both stopped v1/v2 pilots.
It permits at most warm-up plus four bare trials and has no positive/shipping
continuation. Before launch it verifies the exact portable candidate, source/
inventory/native identity and both API controls, and writes its prospective
declaration. Every original work/operation guard remains active. Twenty saved
semantic corruptions and a separate downloaded Linux replay execute no engine.
Read [scope, perturbation and acceptance](docs/M1_SHIPPING_OBSERVER_ATTRIBUTION.md).
This prerequisite cannot qualify cost, the HD 620 or M1.

CI `39179723675` passes all 188 Python regressions and nine native sanitizer
suites, both real matching API checks, required integration/export/offline/package
checks, eight self-tests and 105 PCK entry hashes. The five trials retain 204,693
spans and fifteen joined writers; all eighty raw files reproduce without an
engine. Twenty saved semantic faults are rejected on each platform. The
one-shot request is disabled in `f48992c`; all pilot inputs remain false.

Earlier CI `39165715618` stops before the route in its candidate audit. The
[retained idle segments](docs/evidence/m1-observer-preflight-reader-2026-10-19.json)
expose a reader defect: before any terrain operation, a native frame's emitted
allowance is only the current configuration. Two regressions distinguish that
idle snapshot from limits latched by real work, including zero-duration
upload/deletion/data application across later idle segments. Used allowances,
cumulative work, payload and individual limits remain strict. The original
downloaded candidate passes the corrected saved audit without another engine.

The attribution spans alone do not isolate the larger preparation variation.
The saved-only `preparation_demand_review.py` additionally verifies all 80 raw
files, reproduces the old sequence audit, derives whole-main shared bounds and
reconciles the exact inner same-thread root/gap union. Seven pure regressions
cover large unsigned values, raw errors/identity/order, nesting, boundary snapshots,
crossing spans and false owners. No engine runs; no cost verdict changes. Read
[the evidence, reproduction command and prospective decision](docs/M1_PREPARATION_DEMAND_DECISION.md).
All 195 pure regressions pass for this saved-only change.
Recorder allocation disposal remains outside the old trial boundary. The distinct
capability below now verifies release independently, preserving that old result.
The preceding observer candidate retains 1,332 / 756 µs operation failures; the earlier
preflight's 1,088 / 802 µs and all historical failures remain unchanged.

### Explicit recorder disposal capability

The distinct `--observer-disposal-check` and `CairnProbe.observer_dispose()`
pass CI `39300074494` with a new matching editor/debug/release and portable
candidate. Read [the result and self-contained replay](docs/M1_OBSERVER_DISPOSAL.md).
The tenth native sanitizer suite verifies last-owner destruction, active/open/
retained-owner refusal, allocation rejection and failed-prefix cleanup. Eight
new reader cases bring the pure suite to 203 passing regressions. The control
executes once per matching editor/release, with a five-second native cap and
fifteen saved semantic corruptions. It retains actual joined-writer evidence,
post-disposal trace bytes and explicit counter/cap/write failures. Downloaded
candidate audits on both platforms verify the same source/native metadata and
reproduce both controls exactly. Fixtures take 3,930 / 3,163 µs, retain failure
codes and reject fifteen corruptions per binary. All 203 pure regressions and
ten full native sanitizer suites pass. The broader candidate retains a 905 µs
deletion overrun and unqualified cost/target gates. Existing suites and all three
disabled pilot inputs remain; no owner extension or route ran in this task.

### Four direct preparation owners

The distinct `--preparation-demand-check` exercises the four actual native entries,
real one-worker replacement, overload/early return, section handover, nested main
ownership, UTF-8 writer join/detach and five failed-prefix/cleanup controls.
The new `CAIRNOB2` reader preserves old codecs and checks attempts, completions,
incarnations, raw counters and both object destructions; twenty-one saved corruptions
are rejected per matching binary. Ten pure cases bring the suite to 213; the
eleventh native sanitizer suite covers publication, thread/lane reuse, crossing,
depth/cap, failed counters and disposal. Required CI runs controls and the matching
portable audits only. Read [the scope and live verification](docs/M1_PREPARATION_OWNER_SCOPES.md).
No route or laptop qualification is included.

### Saved preparation owner launch review

`tools/qa/preparation_owner_review.py` checks the exact downloaded portable ZIP,
native/PCK/source/inventory identity and all 48 embedded control files, replaying
four controls and 84 saved semantic corruptions without an engine. Seven new
regressions reject altered/compressed bytes, escaped paths, re-signed unjoined
writers or retained recorders, forged qualification and a different candidate.
The ten affected preparation-reader cases also pass. Source inspection finds a
late prefix-write failure can start another trial; it is not an executed engine
fault fixture. The [review and next controls](docs/M1_PREPARATION_OWNER_LAUNCH_REVIEW.md)
withhold the route until the narrow stopping/reader correction and matching PCK
are verified. No unchanged runtime suite, new native build or pilot ran here.

### Prefix publication stopping and immutable observations

`--preparation-prefix-check` exercises the production JSON writer/publication,
start guard and inherited drain/handover with synthetic completed trials and a
counted setup seam. A real failed FileAccess open reproduces one next setup in
the frozen rejected tail. Seven corrected cases cover normal handover, warm-up/
middle/last prefix failure, prior trial failure, normal final termination and
combined trial/publication failure. Failed publication dispatches zero later
setups, including direct stopped-entry attempts, and preserves immutable files,
trial flags and the first stop reason. Native snapshots show no added terrain
work or active observer. These are controller controls, not shortened routes.

Both matching fixtures pass in [CI 40247195315](https://github.com/dponcho/voxel-survival-game/actions/runs/40247195315), taking
265,539 / 170,954 µs under the unchanged five-second cap. Twelve saved semantic
corruptions per binary and twelve pure prefix-reader cases pass; the complete
pure suite is 232 tests per platform. The reader reconciles successful files,
retains missing/stale/partial/empty failed evidence, checks post-terminal
chronology and rejects any continuation. Required integration/package checks,
the new PCK, both downloaded platform audits and a fresh local saved replay pass.
Read [the exact result and proof](docs/M1_PREPARATION_PREFIX_STOP.md).
No attribution process/declaration ran; all consumed pilot flags remain false.

### Corrected saved launch review and finite declaration

`tools/qa/preparation_prefix_review.py` verifies the exact corrected portable ZIP,
PCK/source/inventory/native identity, original proof hash, CI/qualification
records and immutable-boundary source witness. It decodes and replays all 140
files / 860,237 bytes, both prefix controls and both current owner controls,
with 66 rejected saved corruptions. Eleven new review regressions reject
re-signed continuation/trial/immutable-file changes, escaped or missing nested
files, forged verdicts, changed boundaries, wrong candidate/proof and enlarged
or retried declarations. Together with the twelve prefix and ten owner reader
cases, 33 focused tests pass. No unchanged full engine/native suite is rerun.

The [saved decision](docs/M1_PREPARATION_PREFIX_LAUNCH_REVIEW.md) closes the
stopping prerequisite and creates an exact prospective one-process declaration.
Canonical declaration comparison also rejects numeric/boolean substitution.
The review runs no engine, changes no runtime/inventory/candidate, enables no
consumed pilot, and qualifies no cost/target gate. The future launcher must
reserve once, preserve the first failure/timeout and audit without another run.

### Declared preparation launcher

Thirteen new cases cover the permanent create-only reservation, remote conflict
and uncertain-result refusal, owned first-attempt context, exact one-spawn
command, credential-free child environment, cap/kill/OS-launch outcomes,
preserved failed-trial exits, altered console/path/scope, changed reservation,
and stable unfinalized replay with unknown trial counts. The former blanket
no-route regression now requires dispatch through the separately declared
launcher while preserving ordinary controls and old disabled pilots.
All 256 pure regressions pass locally. Runtime, inventory and the frozen
candidate stayed unchanged; the actual one-process result is now recorded below.
Read [the launch and retention boundary](docs/M1_PREPARATION_DEMAND_RUN.md).

The first cloud preflight's Windows default-codepage failure is retained before
any reservation or process. Explicit UTF-8 source reading reproduces the same
frozen review on both platforms. A codepage regression and a structured
preflight-failure/zero-process replay regression bring the suite to 258 cases;
all 26 affected launcher/review cases pass after the correction.

The reservation permission preflight is also retained before any process:
CI's Contents-write token receives HTTP 403. The permanent claim is instead
created by the connected account and bound to one verified Actions context.
CI verifies it with read-only GETs and its Git-blob digest. Fifteen launcher
cases cover this assignment, including refusal to adopt another run's claim;
the total pure suite is 259. No engine or candidate change follows from either
preflight correction.

The declared process completes three fixed-work trials, stopping at bare-1's
819 µs retirement deletion against 750 µs. Native ownership/disposal and prefix
publication integrity pass; measurement/attribution validity stays false.
The original Windows audit rejects eight saved corruptions. Its first Linux
transfer recheck fails because upload omitted two `.github` source snapshots.
Exact pinned Git bytes restore only those source files in derived copies;
all measured files stay untouched and the complete Windows audit reproduces
locally. Four recovery/mode regressions bring the pure suite to 263. The next
cloud jobs are saved-only readers, with the process request permanently false.


Final saved-only CI `40389612694` passes all **263 Python regressions** and
**eleven native AddressSanitizer/UndefinedBehaviorSanitizer suites**. Both actual
Windows/Linux saved-reader jobs pass; the engine and ordinary Windows build
jobs are skipped. Downloaded replay artifacts pass SHA-256/size/CRC/path checks,
match each other and reproduce a fresh exact-archive local replay: 66 original
audit entries, 144,055 spans, eight rejected corruptions, zero additional engines.
Only the two preflight/Git-bound source snapshots are restored in derived copies.
The complete original run `40259410841` remains failed on its first Linux
transfer replay, with the third trial's 819 µs operation failure intact.
Both preparation request files are now false. The launcher/execution increment
is complete; [the result and reproduction instructions](docs/M1_PREPARATION_DEMAND_RUN.md#final-saved-verification-and-handoff)
lead only to a saved failed-prefix review. No unchanged engine suite or candidate
rebuild is required for this final evidence/prose commit.


### Saved failed preparation-prefix review

`tools/qa/preparation_failed_prefix_review.py` verifies the exact original ZIP,
all 65 transferred files and all 66 original audit entries after recovery of
only the two preflight/Git-bound workflow snapshots. It verifies the frozen
candidate/native/inventory, reproduces the original preflight controls,
sequence and eight semantic corruptions, and compares all retained platform
replays. It derives exact same-thread inner root/gap unions and retains the
invalid third trial without filling the missing bare quartet or estimating cost.

Eight new regressions reject altered members, re-signed escaped/duplicate/link
paths, false owners, bad counters, reversed roots, clipped crossings, changed
kind/payload/failure scope, changed source lifetime and forged consumed proof.
All **75 affected preparation regressions pass**; compile and whitespace checks
pass. The real raw derivation and committed-record reproduction both run no
engine. Native/runtime/inventory/candidate bytes are unchanged; no expensive
engine suite or native build is repeated for this saved-review increment.

The [source-bound finding and next controls](docs/M1_PREPARATION_FAILED_PREFIX_REVIEW.md)
select correction of a local ArrayMesh reference whose final destruction can
occur after deletion measurement. This is a source finding, not an executed
engine lifetime control or an explanation of the retained 819 µs surface-removal
failure. The next implementation must demonstrate actual destruction before
the measured endpoint, preserve external owners/guards and produce matching
binaries/candidate; no consumed attribution process is authorized by this review.


### Mesh retirement lifetime and actual destruction

The production FreeMeshTask body now ends the local ArrayMesh reference scope
before `record_deletion()` samples/charges its existing ending clock. The hidden
`--mesh-retirement-check` runs once per matching editor/release with a five-second
fixture cap and ten bounded cases. A test-only POD endpoint hook observes real
ObjectDB liveness/refcounts without retaining the object; it is cleared on exit
and null during ordinary gameplay. It compares the frozen old body, allocated
empty/two-surface ArrayMesh, external sharing, declared admission refusal/resume,
actual non-ArrayMesh and null add. It preserves operation kind/payload, actual
start/end, reference/surface counts, native frame/phase, exact charge and counters.

The new saved reader rejects seventeen semantic corruptions. Eight new pure
cases also verify that a 751 µs operation stays failed despite correct lifetime
order, missing observations remain null, identities remain exact and refused
work invents no endpoint. The historical source check explicitly rejects the
new implementation inheriting the old candidate identity. Existing eleven
native sanitizer suites and all required runtime/package checks remain. Source
and native metadata, compiled scripts and both downloaded platform audits match
the new exact candidate in CI `40440351282`. All 280 Python regressions pass on both
platforms, as do the eleven sanitizer suites, three native qualification reports,
required integration/package checks and complete downloaded Windows/Linux audit
replays. Both actual ten-case lifetime controls and all seventeen corruptions
per binary reproduce locally from saved files, with no engine. The
[result and self-contained proof](docs/M1_MESH_RETIREMENT_LIFETIME.md) retain raw
ObjectDB observations, exact timing/charging, candidate identity and every
broader failure. The preserved Windows preflight exposed a historical test
fixture decoding UTF-8 with Windows' default codepage and signing a different
UTF-8 string from its saved source. Controlled simulation reproduces that error;
the test now writes UTF-8/LF and signs its actual bytes. The production identity
reader remains strict. The broader diagnostics retain 1,488 µs debug kind-2
retirement and 824 µs release upload failures against 750 µs. These controls
prove synchronous object lifetime only, not target or renderer-deferred cost.


### Saved retirement review and event-level next decision

`tools/qa/mesh_retirement_review.py` verifies four original artifact archives,
the exact current and frozen old portable identities, both embedded lifetime
controls and all seventeen corruptions per binary. It runs the complete saved
candidate audit on an isolated copy and compares the entire original Windows,
downloaded Linux and fresh local results. The ordinary portion reconciles 98
scenarios, 284 native phases and 37,359 native-frame operation rows. Review
success does not turn an invalid operation into a performance pass.

The original failed process archive and all 66 audited files reproduce. Actual
raw same-thread roots/gaps are grouped by adjacent slot endpoints, with exact
sums and no process subtraction, cycle/time conversion or causal owner label.
All three original partitions and the 819 µs failed event remain unchanged.

Eleven new pure tests reject re-signed lifetime claims, scope/clock regressions,
changed archive/player/native/CI identities, escaped/duplicate/link members,
platform-audit disagreements and false gap ownership. All 95 affected pure
regressions pass. A fresh `--check` reproduces the committed review record; no
engine, new candidate, inventory/codec change, native build or laptop run is
part of this increment. Read the [decision and prospective event-witness
acceptance checks](docs/M1_MESH_RETIREMENT_REVIEW.md). Current 1,488 µs debug
surface-removal and 824 µs release upload failures remain failed against 750 µs;
target performance and shipping cost are unqualified.
