# M1 bounded operation-event CPU witnesses

Implementation and cloud verification in progress. M1 remains blocked; no
attribution process, cost result or target qualification is declared here.
The finite acceptance contract is the [saved retirement review](M1_MESH_RETIREMENT_REVIEW.md#one-bounded-next-implementation).

## Capability and boundaries

The actual surface upload, `FreeMeshTask::run` deletion and completed-task
application brackets can opt into four raw `QueryThreadCycleTime` reads on the
calling OS thread. Every read retains API success/availability/error and its
own monotonic wall enclosure. The existing operational start/end clocks still
measure the entire synchronous operation, including the corrected final local
reference destruction. A non-owning ObjectDB control observes destruction
before both ending reads and the ending operational clock.

The inner interval (read 1 to read 2) measures captured body CPU demand; the outer
interval (read 0 to read 3) additionally encloses recorder bookkeeping. Their
difference is retained read/bookkeeping uncertainty in cycles. Both intervals
are **inside** the operation's wall bracket. Neither measures CPU demand over
the complete wall bracket. Cycles are unsigned exact integers, serialized as
binary integers and exposed to JSON as decimal strings. Failed/unavailable
reads have null derived intervals; a real measured zero remains observed.
There is no cycle-to-time conversion, CPU subtraction from wall time or causal
OS/driver/GPU inference.

This is one explicit opt-in, perturbing forensic recorder. `CairnProbe` exposes
start/finish for a later separately declared process; no current benchmark or
pilot arms it. The finite capability route arms it once per process. Ordinary
operations perform no new counter calls. Inactive dispatch branches remain
shared operational diagnostic work, with unqualified cost. The original
shipping inventory and all previous raw codecs/readers remain unchanged; the
[additional inventory](../game/diagnostics/operation_witness.json) declares
inside/outside-bracket work and the new bounds.

## Finite retention and accounting

The main-thread recorder uses fixed trivially copyable, standard-layout storage:
128 retained events and eight nested pending operations, with a compile-time
64 KiB bound on the whole recorder. Normal capture selects new first-tie
process per-kind/current-phase guard maxima, the first individual/frame/payload
failure, and counter/context errors. The first failure is retained separately
from later larger maxima. Count/overflow remains explicit; a full recorder
never turns missing observations into passing zeros or evicts the first failure.
Maxima unavailable after overflow stay unavailable in invalid evidence.

The wall guard remains 750 µs. The normal/heavy 1,000/2,000 µs time and
512 KiB/1 MiB payload budgets still latch across phase changes in one native
frame. Single uploads remain bounded at 256 KiB. Completed-task charging is
inclusive elapsed work minus already charged children. Refused/null attempts
have no completed operation; a real queue miss retains its cancelled read
attempt separately. Work/resource/readiness/coverage and ownership rules remain.
Generator and save formats do not change.

Record selection/copy and ordinary charging bookkeeping occur after the
operational ending clock. A retained commit-end clock bounds the observed
post-wall work through the copy, excluding final return dispatch. Start dispatch
and the interval beyond the last read are also disclosed, rather than assigned
zero cost. Binary serialization/open/write/flush/close/file release occurs at
explicit finish, enclosed by raw whole-process observations and actual wall
endpoints. Proof JSON serialization/write/close has a separate receipt. That
terminal receipt excludes its own write. The total witness/proof/receipt bytes
per process must be at most 256 KiB; the reader verifies actual file sizes.
No new worker, pool or per-operation allocation is introduced.

## Required controls and result interpretation

One editor process and one matching release process each exercise fifteen
finite cases. They enter the production upload helper used by
`ApplyMeshUpdateTask`, actual `FreeMeshTask::run/add`, and the same inclusive
completed-task charging hooks. The nested control supplies a real deletion
inside that bracket; it does not claim to replay a terrain queue selection.

The first two uploads contain explicitly injected wall-wait doses: 2,000 µs,
then the first actual elapsed duration plus 2,000 µs, capped at 20,000 µs.
Both remain measured guard failures; their CPU intervals cannot become a
performance or shipping-cost pass. A first dose too long for that declared cap
fails the control without retry. Sharing, one-surface postponement, final
destruction, admission refusal/resume, null work, nested charging and same-frame
normal-to-heavy phase carry remain independently observable.

One case calls the actual counter API with an invalid handle; another declares
an unavailable counter. A real cap control selects all events and performs
130 completed operations, retaining 128 and reporting exactly two dropped
events, plus one cancelled attempt. Thus `passed` means the finite capability
controls reproduced their declared outcomes. `operation_guards_valid` and
`witness_integrity_valid` remain **false**. The original ten-case rejected/
corrected lifetime controls also run unchanged in their own processes.

The saved reader reconciles the new little-endian `CAIRNOP1` header/events with
actual phase/frame counts, kinds, payloads, clocks, first-tie maxima, union
charging, ObjectDB liveness, native resources and complete writer evidence.
Twenty re-signed semantic corruptions per binary attack thread/kind/payload,
endpoints, first failure/maxima, guard verdicts, overflow, counters, ownership,
phase carry, charging, cancellation and qualification.

## Completion and next task

Completion requires matching editor/debug/release native qualification, both
actual controls, required integration/package checks, a new portable Windows
candidate and independent saved Windows/Linux audits. Compilation remains in
GitHub Actions. Cloud/headless results cannot qualify HD 620 performance.

After those checks, the next task is an exact saved review of the produced
candidate and evidence. Do not arm an attribution route, rerun a calibration,
request laptop work or start M2. All consumed request files stay false and the
permanent old reservation stays unchanged. A later finite observation needs its
own prospective exact-candidate declaration and stopping rule. The conditional
[M1 turn estimate](M1_MESH_RETIREMENT_REVIEW.md#remaining-turn-estimate) remains
a planning range, with target viability and diagnostic-cost qualification open.
