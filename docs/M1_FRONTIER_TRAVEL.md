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
Resource identities remain exact decimal strings. No mesh reference survives the
observer. Missing cells/measurements stay null/unavailable, never ready zeros.

Acceptance requires all 600 ticks, 14,400 actor updates, 40 accepted edits and ten
proxy saves; exact due-command fingerprint and float32 movement; actual overlapping
visual ownership at all four handovers; stable unedited resource identities/current
revisions; no non-edit supersession; and independent reconciliation of original
edit targets to native terminal events and observed actual submissions. Existing
H2 edit/coverage/operation failures remain visible. Functional evidence integrity
is separate from those measured guards and from hardware qualification.

Bounds per process: 4,096 observer rows / 32 MiB, each below 32 KiB, streamed
synchronously without an added worker or queue. At most fifteen native cells per
row (API maximum sixteen); two per edit-attempt snapshot. The existing native
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
