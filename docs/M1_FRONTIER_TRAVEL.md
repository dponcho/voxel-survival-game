# Bounded continuous H2 frontier travel

This cloud-only replay observes the production H2 benchmark continuously for
600 fixed 60 Hz ticks (ten simulation seconds), with one and two workers in the
matching editor and release player. It reuses the actual benchmark methods for
collision-safe 6.5 m/s motion, 24 actor/256 rain proxies, four due border edits
per second and the 32 KiB proxy-storage command every second. The independent
float32 route crosses x=16/32/48/64 at ticks 56/204/351/499 and ends at
x=74.99976348876953. No teleports or intervening settled single-edit scenes replace
these commands. Preparation precedes the continuous run; final edit settlement
and retirement follow it through the existing protocol.

The hidden `--frontier-travel-replay` entry subclasses `benchmark.gd`. The
600-tick endpoint uses the existing matched H2 command path; ordinary scenarios,
assessors and menu entries retain their behavior. The fixture, camera/fog/required
geometry 96 m, data 128 m, four preparation viewers, native caps, simulation,
collision safety, content/save semantics, 200 ms edit and 750 µs operation limits
remain unchanged. This task adds observation, with no speculative engine fix.

Predeclared evidence: every physics tick, a process observation when its tick
changes, every process opportunity within four ticks of each handover, and every
acknowledgement callback. The bounded native observer samples fifteen distinct
cells: old/current frontier columns, all six cells affected by the three production
edit locations (x=0/32/64), and a confirmed-empty control. Every edit attempt has
before/after desired/submitted revisions and a monotonic acceptance bracket.
A second two-cell native call observes the newly demanded lateral `z=-1` rows
after the first cloud run exposed pending coverage there. Resource identities
remain exact decimal strings. No mesh reference survives the
observer. Missing cells/measurements stay null/unavailable, never ready zeros.

Acceptance requires all 600 ticks, 14,400 actor updates, 40 accepted edits and ten
proxy saves; exact due-command fingerprint and float32 movement; actual overlapping
visual ownership at all four handovers; stable unedited resource identities/current
revisions; no non-edit supersession; and independent reconciliation of original
edit targets to native terminal events and observed actual submissions. Existing
H2 edit/coverage/operation failures remain visible. Functional evidence integrity
is separate from those measured guards and from hardware qualification.

Bounds per process: 4,096 observer rows / 32 MiB, each below 32 KiB, streamed
synchronously without an added worker or queue. At most fifteen primary and two
lateral cells per row, in separate bounded calls
(API maximum sixteen per call); two per edit-attempt snapshot. The existing native
64-record ring, disk 64-item/64 KiB queue, 128 operation-row buffer, 64 pending/
128 terminal edit limits, 64 MiB frame/operation files and 8 MiB edit file remain.
The independent reader additionally caps total operation rows at 100,000. Existing
three-minute loading/drain limits, 50-second gameplay wall bound and 600-second
Actions command timeout remain; no timeout erases partial evidence. Writer drain,
all terminal operation/frame/edit rows, final callback and external combined report
finalization remain. Synchronous observer/file costs perturb this experimental
run and stay in complete wall/callback durations; it estimates neither ordinary
throughput nor per-frame causal cost or total diagnostic overhead. Overlapping
brackets are never added.

Independent Python controls reject missing/reordered/stalled work, changed
actors/rain/storage/due commands, lost resources/ownership/revisions, unavailable
meshes, overflow, I/O loss and waived operation failures, including 749/750/751 µs
boundaries. Saved runtime verification retains phase-local failure reasons,
preparation/gameplay/retirement sums/first-tie maxima/clock boundaries, complete
callback partitions, final proxy content and full native drain. Prior controls
and replay expectations remain required.

## Verified cloud result — October 9 UTC

[CI 37861287881](https://github.com/dponcho/voxel-survival-game/actions/runs/37861287881)
passed all three jobs at implementation
`abb94bf4a4eecf6de0bd9bc68f37ae261c9c9cf4`: 81 Python regressions, five native
sanitizer suites, matching-engine checks, all four continuous runs and every
earlier control/replay/runtime/profile/smoke, DLL audit and two fresh offline
extractions. Independent downloaded review repeats the saved-report readers,
rejects 21 additional mutations of actual saved evidence, and verifies archive
size/digests/CRC/paths, x64 PE, all 74 PCK entry MD5s, exact template identity,
eight self-tests and 38 PE imports. No engine was installed, built or run locally.

Each run completes 600 ticks, 14,400 actor updates, 40 current submitted edits,
ten proxy saves, all four actual `1 -> 2 -> 1` handovers and full native drain.
Unedited prepared resources/revisions remain stable; no edit is superseded,
cancelled, timed out or unavailable. These functional checks pass while the
unchanged scenario evaluation **fails** coverage and diagnostic cost in all four
runs. The observer adds measured synchronous costs; this result qualifies neither
diagnostic overhead nor target timing.

| Run | Observation rows | Operation rows | Frame rows | Coverage alarms | Lateral observations inside 96 m | Edit max / p95 upper (µs) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Editor, one worker | 1,254 | 1,904 | 1,452 | 23 | 39 | 166,097 / 84,000 |
| Editor, two workers | 1,255 | 1,906 | 1,453 | 23 | 37 | 172,516 / 76,000 |
| Release, one worker | 1,255 | 1,905 | 1,453 | 22 | 37 | 166,091 / 76,000 |
| Release, two workers | 1,254 | 1,905 | 1,452 | 22 | 37 | 172,985 / 76,000 |

The four reports reconcile 5,018 observations (27,163,457 bytes), all twelve
native phases/7,620 operation rows and 5,810 frame rows. Per-run observation files
are below 6.8 MB, within the predeclared 32 MiB cap. Peak mesh/data is 511/867,
travel retirement high-water is two and complete retirement high-water is 285,
with zero overloads and no pending native work after drain. Every replay phase
passes the unchanged individual-operation limit; the largest replay upload is
135 µs and deletion 444 µs. Edit-duration guards also pass for these ten-second
replays. The ordinary smoke reports separately retain H2 edit-latency/diagnostic
failures and three retirement deletion exceedances (871/955/1,320 µs). Recorded
target upload failures remain unresolved, independently of these cloud results.

The first raw coverage alarm is tick 61 / 1.016667 simulation seconds, just beyond
the previous one-second smoke. At camera x=16.6083488464355, y=1.65100002288818,
z=10, cell `(7, 0, -1)` is pending at 95.9143676757812 m. Native observation
also shows `(7, -1, -1)` pending, with one base visual owner, a queued update,
null submitted revision/resource and 28 pending meshes. Equivalent failures recur
at the following columns `(8..10, -1/0, -1)`. The four preparation cells in Z=0/1
are already submitted; their successful ownership transfer does not establish
coverage of these lateral cells. These are conservative region alarms; rendered
pixels remain unverified.

[Pinned fixed-LOD `VoxelTerrain::process_meshing`](https://github.com/Zylann/godot_voxel/blob/2ac9f5f8a8219bf499314cc0fad54ffc47df908f/terrain/fixed_lod/voxel_terrain.cpp)
visits the pending vector in
insertion order. The current admission patch stops at four admitted/result tasks
and retains its unadmitted suffix; worker priority is initialized only after
selection. This is a concrete candidate mechanism to characterize next, **not a
proven causal correction**. Native pending-admission order, submission deadlines
and current revisions should be compared under the same caps and 600-tick work
before changing that scheduling path. No extra viewers, enlarged envelopes,
trimmed alarms or weakened gates are authorized by this observation.

[Windows player 11587137036](https://github.com/dponcho/voxel-survival-game/actions/runs/37861287881/artifacts/11587137036)
expires `2026-11-08T00:10:16Z`. Exported merge/build:
`7f37595af6bb8d30191770c644a2b9ea5da80c92`; build/implementation tree:
`5d3877168732610f3d418f30411d66ba59389875`. Portable ZIP: 30,110,198 bytes,
SHA-256 `c58afe5aa3178212c438ca02202f695e344d41605e36f8dd00d5e68d1a8e4ba2`.
The native key remains
`25581a8d31f5a500c585135069db3a143ac7edc69d984601768910f10ce53348`.
All 42 ordinary heavy work-unit records and available exact contracts match the
previous candidate. The [public record](evidence/m1-frontier-travel-cloud-2026-10-09.json)
retains file digests, failure seeds and prior attempts. Ten seconds does not cover
the 15-second reversal, full/repeated routes, HD 620 throughput or physical
presentation. M1 remains blocked, all qualification flags stay false, and **no
new target-side action is needed now**.


## First cloud attempt

CI 37859891722 at implementation `39dde208f257cbd8e91fd97adc38f491d69d27b8`
passed 80 Python regressions, five sanitizer suites, native qualification, all
parse checks, earlier controls and replays. Its first actual editor/one-worker
600-tick H2 run completed; the new independent reader then failed because it
compared Godot's 15-digit serialized yaw against the full float32 decimal exactly.
The correction allows only 1e-12 radians of serialization roundoff, with unchanged
route, native and timing gates. No approved candidate was produced by this run.

Downloaded evidence artifact `11586241096` is 15,470,349 bytes, SHA-256
`649ef6824a312749f2bf421d366fb7364699c29c2740b9de6a6842dc3eb6c995`.
Before the lateral-observer extension, the corrected reader independently
reconciled 600 ticks, 14,400 actor updates,
40 current submitted edits, ten proxy saves, all four actual `1 -> 2 -> 1`
handovers, 1,254 observations (6,148,012 bytes), 1,905 operation rows and 1,452
frame rows. No edit-duration or operation guard fails in this first run.
Nevertheless 23 measured coverage rows fail: lateral cells `(7..10, -1/0, -1)`
remain pending after base acquisition while their conservative distance falls
inside 96 m. Four prepared cells stay submitted, with stable resources/revisions;
this does not cover every newly demanded lateral cell. Diagnostic cost also fails
the existing 1% guard. The new bounded lateral observer records this distinction
in subsequent editor/release runs; it does not change scheduling or suppress the
alarm. Peak mesh/data remains 511/867 and travel retirement high-water two
(285 including final terrain retirement). All native work
drains. The observed coverage failure is separate from target H2 upload evidence.
