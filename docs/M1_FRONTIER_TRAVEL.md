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
synchronously without an added worker or queue. At most fifteen primary and two lateral cells per row, in separate bounded calls
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

Verification is pending cloud execution. M1 remains blocked, HD 620 is unqualified,
and no new target-side run or download is requested.


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
The corrected reader independently reconciles 600 ticks, 14,400 actor updates,
40 current submitted edits, ten proxy saves, all four actual `1 -> 2 -> 1`
handovers, 1,254 observations (6,148,012 bytes), 1,905 operation rows and 1,452
frame rows. No edit-duration or operation guard fails in this first run.
Nevertheless 23 measured coverage rows fail: lateral cells `(7..10, -1/0, -1)`
remain pending after base acquisition while their conservative distance falls
inside 96 m. Four prepared cells stay submitted, with stable resources/revisions;
this does not cover every newly demanded lateral cell. Diagnostic cost also fails
the existing 1% guard. The new bounded lateral observer records this distinction
in subsequent editor/release runs; it does not change scheduling or suppress the
alarm. Peak mesh/data remains 511/867 and travel retirement high-water 2 (285 including final terrain retirement). All native work
drains. The observed coverage failure is separate from target H2 upload evidence.
