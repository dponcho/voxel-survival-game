# Roadmap

Design baseline: 2026-09-05; core Java-style product requirements revised 2026-09-26. This is an evidence-gated sequence, not a calendar. Current implementation status is recorded separately: [M1 cloud evidence](docs/M1_EVIDENCE.md) and [target review](docs/M1_TARGET_REVIEW.md). M1 is blocked on qualification corrections; current evidence has not reached the representative target viability checkpoint described below.

## 1. Delivery rule

Every milestone produces a portable Windows candidate ZIP, build identity, test results, known limitations and the next bounded task. The user only downloads, extracts and runs builds. Codex Cloud and GitHub Actions own source editing, tools, tests and compilation.

Keep the main branch exportable after M0. Finish one working increment before opening the next. Correctness, save integrity and the 720p performance contract remain release gates throughout; content volume is not a substitute for passing them.

The product scope is [GAME_DESIGN.md](GAME_DESIGN.md). Implement the architecture in [ARCHITECTURE.md](ARCHITECTURE.md), budgets in [PERFORMANCE.md](PERFORMANCE.md) and checks in [TESTING.md](TESTING.md). Repository agents follow [AGENTS.md](AGENTS.md).

## 2. Milestones

| Milestone | Concrete deliverable | Exit evidence |
| --- | --- | --- |
| **M0 — Cloud build foundation** | Pinned engine/module sources; project module registration; Compatibility project; matching Windows editor/debug/release templates; automated export/package jobs; title screen and self-test entry | A cold-cache source-to-ZIP run succeeds; fresh extraction launches offline; native classes exist in the exported executable; dependency audit passes |
| **M1 — Target-machine engine proof** | Flat terrain and representative terrain stress fixtures; bounded streaming/meshing; 16-vs-32 render-chunk comparison; one-vs-two terrain-worker experiment; voxel-box movement; metrics and automated benchmark | Actual HD 620 release-build report passes the initial normal/heavy frame gates and memory ceilings; queues plateau; no collision holes; oversize uploads/geometry are bounded |
| **M2 — Deterministic editable world** | Native seeded regions, caves/deposits, safe spawn, cross-chunk structures; validated edit admission; mesh seams; sunlight/emissive data-to-shader prototype | Windows/Linux golden output matches under reordered/cancelled generation; boundary edits and light removal/reload tests pass; real-world route still fits M1 budgets |
| **M3 — Durable persistence** | Atomic terrain/inventory/player transactions; chunk snapshots, replay, recovery, version guards, three rotating backups and save UI | Crash/kill/disk-error tests preserve all committed state and never duplicate items; eviction/reload and old-world fixtures pass; saving does not break frame gates |
| **M4 — First playable survival slice** | One region; Java-style movement/mining/placement, tool tiers/durability, 9+27 inventory, 2×2/3×3 grid crafting, furnace, hunger/food, bed, hostile creature, transactional death drops, save/quit and first-session guidance | A fresh world supports gather → craft → build → survive → save → relaunch; transactions remain correct through death/crafting; ordinary-play benchmark passes |
| **M5 — Complete systemic survival** | Bounded creature AI/breeding, farming/hydration, cooking, loaded-area furnace/crop ticking, armour/combat/shields, weather, local water/lava and falling blocks, sleep/day/night and finished lighting | All scheduled systems obey budgets; loaded/unloaded state is consistent; no unbounded simulation; night/rain/combat/edit/save combined scenario passes |
| **M6 — Complete core progression and content** | Four regions, crafting table/furnace, three landmark families, at least five creature roles, full scoped building set and wood/stone/metal progression, original assets/audio and open-ended play | Scripted traversal proves core progression and building/food reachability; a full survival playthrough continues freely; Java core behaviour/visual comparisons and asset/recipe/licence checks pass |
| **M7 — Product hardening** | World manager, Creative-style free-build catalogue/flight, settings/remapping/accessibility, save restore, portable-data mode, diagnostics, polished onboarding | Clean-path/upgrade/input/focus tests pass; 30-minute traversal, 2-hour soak and dense-construction scenarios meet gates; no save loss or sustained memory growth |
| **M8 — 1.0 release candidate** | Final candidate ZIP, notices, release notes, checksums, retained build inputs and exact-build evidence | All scoped systems complete; three target-machine qualification runs pass; cloud gates green; previous saves migrate safely; release uses the exact validated package |

## 3. M0: first implementation task

When a repository is connected, implement this task before gameplay:

1. Put these documents at its root and create the minimal source layout.
2. Resolve the candidate Godot/Voxel Tools pair to exact immutable source revisions. Select/pin the cloud toolchain and verify build options against that source.
3. Register a small project-owned native module and assert `VoxelTerrain`, `VoxelMesherBlocky`, `VoxelBoxMover` and the project entry class exist.
4. Build the matching editor and both Windows templates in GitHub Actions, with fully automated setup and cache-miss handling.
5. Export a minimal Compatibility project that opens a title screen, displays build/renderer information and supports the proposed headless self-test route.
6. Extract its resulting ZIP into a clean path, run it headlessly, audit DLL imports, verify the data pack and publish a candidate artifact.
7. Record every command outcome and the source/engine/module hashes. Deliver the candidate, not instructions for the user to install Godot.

M0's source lock, scripts and workflow YAML are implementation deliverables. They do not exist merely because they are specified here. A supplied repository/authorized GitHub connection is needed to run that pipeline; do not invent a successful action run or a download URL.

## 4. M1: architecture kill gate

October 8 cloud increment: the first 16³ moving-frontier gap now has a verified
baseline/corrected native replay and a bounded four-viewer preparation fix.
[Evidence and next step](docs/M1_FRONTIER_BOUNDARY_REPLAY.md) retain M1 blocked,
no qualified target profile and separate unresolved operation/timing gates.
The second-boundary concurrent-edit follow-up now verifies actual resources,
accepted revisions, transfer/cancellation and complete drain in editor/release;
it fixes a demonstrated redundant-viewer supersession. See
[the bounded handover evidence](docs/M1_FRONTIER_EDIT_HANDOVER.md). October 9 adds
an independently verified 600-tick continuous production H2 replay in editor/
release with one/two workers. Four handovers and all forty edits complete, while
lateral queued meshes still fail conservative coverage beyond the earlier short
smoke. [Continuous evidence and the next admission experiment](docs/M1_FRONTIER_TRAVEL.md)
retain those failures; full/repeated travel and target qualification remain open.

The bounded opt-in admission follow-up now verifies a native FIFO selection
cause and priority correction in four matched editor/release one/two-worker
600-tick trials: FIFO has 23/24/22/24 coverage alarms; priority has zero, with all
32 lateral cells currently submitted before 96 m entry. Work, caps, accepted
revisions and retirement remain exact. Production stays FIFO while the correction
is experimental; diagnostic, operation, full-route and target gates remain open.
[Admission evidence](docs/M1_MESH_ADMISSION.md) is supplemented on October 13 by
four matched 1,200-tick comparisons through the original tick-900 camera turn:
priority has zero alarms before/after, all eighty edits submitted and all 64
lateral witnesses current before 96 m entry. Legitimate eviction and complete
drain remain visible; FIFO retains coverage/edit failures and one timeout.
The October 13 traced result left ordinary untraced priority, full/repeated
routes, diagnostic overhead and target qualification open.
[Reversal evidence](docs/M1_FRONTIER_REVERSAL.md) records that stage; the
[current gates](docs/NEXT_TASK.md) keep M1 blocked and M2 gated.

October 16 closes that bounded ordinary-path cloud comparison: all four priority
runs have zero coverage alarms, all eighty edits submitted, passing complete
terrain guards and full drain. FIFO retains coverage/edit failures, and five
broader phases retain operation-limit failures. The source-matched Windows
candidate and independent audits are in
[ordinary admission evidence](docs/M1_ORDINARY_ADMISSION.md). Priority stays
opt-in. That checkpoint led to the full-height/directional experiment, now
completed in CI `38922744175`: both 32³/one-worker prepared cases have zero
coverage alarms versus 521 in each baseline, all 288 edits submitted, actual
+X/-X/+Z movement, genuine edited-data/mesh reload and passing operation guards.
Peaks are 392 meshes / 5,104 data within unchanged caps. No target profile is
selected or qualified. [Full-height evidence](docs/M1_FULL_HEIGHT.md) gives the
verified Windows candidate and retained broader failures. The shipping/forensic
diagnostic inventory and focused pilot in [the gate register](docs/NEXT_TASK.md)
are now implemented: CI
`38985239110` completed the finite nine-trial pilot, with an inconclusive result
and two retained operation overruns. The QA-only saved audit distinguishes verified
evidence from invalid measurements. The [pilot result](docs/M1_SHIPPING_DIAGNOSTICS.md#result)
stops v1 calibration. The October 17 [measurement-policy decision](docs/M1_DIAGNOSTIC_COST_POLICY.md)
explicitly selects raw whole-process CPU-cycle demand for the unchanged 1% cost
threshold while retaining separate elapsed/frame/operation evidence. The
[counter-capability increment](docs/M1_CPU_CYCLE_CAPABILITY.md) now passes CI
`39073452514` with new matching editor/debug/release binaries, two bounded
capability smokes and a verified portable candidate. V2 inventory, native dose,
exact readers and the one finite sequence now pass implementation/integrity checks
in CI `39088740702` with a new matching Windows candidate. Warm-up plus the null
quartet pass all work/operation guards, but the null width is 2.850549401% and
matching-section drift 1.073468789%, failing their below-1% controls. The sequence
stopped before positive/shipping quartets. The
[saved null review and decision](docs/M1_SHIPPING_NULL_REVIEW.md) are now complete:
the raw quartet cannot meet zero containment and strict <1% width together, and
recorded native work matches while common observer attribution is incomplete.
The next task implements a separate bounded observer-attribution prerequisite,
with at most one five-trial bare cloud probe and no shipping continuation,
automatic retry or laptop action. M1 remains blocked.

Do not spend weeks building content on an unqualified engine. The first representative engine experiment must include: a visible surface, cave-heavy geometry, a permitted dense-build fixture, one-block edits on borders, persistent-direction sprinting, rapid turns and resource eviction. A flat plane alone does not qualify the architecture.

Compare the stock 32³ render path with 16³ render blocks and one versus two terrain workers. Keep the same resolution, scene and view distance. Record cost attribution: generation, meshing, upload, deletion, draw submission, collision and GPU work.

If the contract fails, isolate the bottleneck and perform one bounded optimization experiment. Implement native greedy meshing or finer upload work only when evidence identifies its benefit. If upstream queue/admission/locking behaviour prevents compliance, patch the narrow integration point and test it. Replacing the entire voxel backend is the last escalation after a measured comparison.

If no actual laptop report is available, M1 remains **target-unverified**. Cloud work may continue on deterministic generation and persistence correctness, but do not certify M1 or substantially expand content. Running the game's own automated check is sufficient; the user never installs a test harness or serves as a CI runner.

### Review-adopted decision gates — October 16 UTC

Before selecting a production profile, test full-height `Y[-64,192)` demand and
actual travel reversal/cross-axis travel in a deterministic fixture. The existing
slab is a bounded integration experiment, not that architecture qualification.
The unchanged cuboid 16³ policy needs 2,197 interior render regions against a
512 cap; 32³ needs 343. Arithmetic alone does not qualify the latter. Preserve
existing outward routes, world height, 96/128 m radii and resource limits.

Separate architecture viability from full qualification: only after a
representative exact-build target candidate passes frame, coverage/readiness,
edit, synchronous operation and resource gates may bounded M2 generation/M3
persistence logic correctness proceed while M1 qualification continues against
its frozen candidate. Existing slab/cloud evidence does not satisfy that
checkpoint. M1 remains unqualified until all its remaining measurements and
three complete runs pass. Real generation/storage integration requires relevant
performance requalification. Content remains at its original milestone.

The user-authorized independent review prospectively separates optional shipping
diagnostics (<1% measured incremental cost) from explicit perturbing forensic
modes and adopts a finite matched-route pilot, without changing prior reports or
any threshold. See [review decisions](docs/M1_REVIEW_RESPONSE.md) and the active
[gate register](docs/NEXT_TASK.md). An inconclusive pilot requires a declared
policy decision; another instrument family is not the default next task.

## 5. Per-task completion contract

Each implementation task should name one observable result, its touched systems, acceptance checks and an explicit stopping point. Example: “After editing a border voxel, both adjacent meshes update once, survive unload/reload and produce no stale replacement.” Avoid tasks such as “finish the engine” that hide multiple unproven dependencies.

For every completed increment:

- Include its implementation and the tests needed for the actual risk.
- Run affected cloud checks and produce an export if runtime behaviour changed.
- Compare the relevant budgets with the last accepted baseline.
- Update the milestone/evidence record and preserve world/version compatibility.
- Report passed, failed and unverified outcomes separately.

If CI fails, repair the failure before layering on another feature. A claimed milestone cannot depend on an uncommitted fix or an expired, untraceable binary.

## 6. Scope and regression control

The user selected Java Edition as the core reference and deferred automation circuits, enchanting, brewing, additional dimensions and boss progression until after 1.0. Multiplayer, modding, moving voxel structures, general-purpose fluids and longer view distances remain outside 1.0. Implement [the core reference contract](docs/JAVA_CORE_REFERENCE.md) first, without bypassing M1 or expanding the hardware envelope.

Keep the last accepted build and its test fixture worlds available. Generator upgrades, ID-map changes and save migrations require explicit compatibility evidence. A rollback may restore the previous executable, but it must not overwrite worlds already migrated by a newer build; offer recovery from the retained backup.

A feature that exceeds its allowance first loses optional visual complexity, then receives an implementation optimization. Changes to product scope or the certified envelope are recorded plainly. The 720p/60-normal and 720p/30-heavy requirements do not move to make a milestone appear complete.

## 7. Evidence record to create in M0

Maintain a compact versioned milestone record containing milestone/task, status, game commit, engine/module pins, artifact digest, CI run, tests, performance-report identity, known defects and next task. Use statuses `planned`, `in_progress`, `cloud_passed_target_unverified`, `passed` or `blocked`.

The final release can be built and packaged automatically. Human hardware feedback supplies evidence the cloud cannot reproduce, without moving any development or compilation onto the player's machine.
