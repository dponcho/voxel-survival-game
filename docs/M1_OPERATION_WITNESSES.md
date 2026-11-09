# M1 bounded operation-event CPU witnesses

Capability, matching portable candidate and independent saved audits verified
in [CI 42681602647](https://github.com/dponcho/voxel-survival-game/actions/runs/42681602647).
M1 remains blocked; no attribution process, cost result or target qualification
is declared here. The [exact saved review](M1_OPERATION_WITNESS_REVIEW.md) is
complete; its finite next implementation keeps observation launch disabled.
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

The required matching editor/debug/release qualification, both actual controls,
integration/package checks, portable Windows candidate and independent saved
Windows/Linux/local audits have passed. Compilation remains in GitHub Actions.
Cloud/headless results cannot qualify HD 620 performance.

The [exact saved review](M1_OPERATION_WITNESS_REVIEW.md) now reproduces the
produced candidate, controls, writer receipts and full audits. Its next task is
a bounded real-route controller and saved reader, with launch disabled. Do not
arm an attribution route, rerun a calibration, request laptop work or start M2.
All consumed request files stay false and the
permanent old reservation stays unchanged. A later finite observation needs its
own prospective exact-candidate declaration and stopping rule. The conditional
[M1 turn estimate](M1_MESH_RETIREMENT_REVIEW.md#remaining-turn-estimate) remains
a planning range, with target viability and diagnostic-cost qualification open.

## Executed result — November 9, 2026

Source `e8ae2a9ea38d0169c28e6ce7b6f692c9d4407d6a`, CI checkout/exported game
`75f8b0a9e2fcbfd61d830f420a20e91c9f49ccd2`. Both trees equal
`278661dadad5561672682253b4de49f88dfd280e`. All **303 Python regressions on each
platform and twelve native sanitizer suites** pass. Matching-editor import and
direct parser checks, editor/release controls, all required integration,
dependencies and offline extractions pass. The complete Windows and Linux saved
audits match a fresh local saved-only replay; no engine ran locally.

| Control binary | Complete native fixture, µs | Cases | Semantic faults rejected | Serialized process evidence, bytes |
| --- | ---: | ---: | ---: | ---: |
| editor | 8,775 | 15 | 20 | 105,839 |
| release | 8,812 | 15 | 20 | 105,839 |

Each recorder uses **40,456 bytes**, writes a **38,144-byte** trace, retains 128
of 130 completed events and reports two overflowed events, two counter errors,
one cancelled attempt and 522 reads. Both complete actual-entry controls pass,
while `operation_guards_valid=false` and `witness_integrity_valid=false` remain.
The injected first/later upload durations are **2,369 / 4,946 µs** (editor) and
**2,435 / 4,960 µs** (release). First failure remains event 1 and the later
maximum event 2. Failed/unavailable counters retain null CPU intervals; both
corrected last-owner witnesses precede the ending counter reads. All twenty
existing lifetime cases and 34 lifetime corruptions also reproduce.

The [portable artifact](https://github.com/dponcho/voxel-survival-game/actions/runs/42681602647/artifacts/13705042193)
contains a **30,372,525-byte** player ZIP, SHA-256
`f8d2fc1acebfbae3d769fac5aa8d0278d220df643d76080131f20cbf9c80ac09`.
Native key `ff3a84944e7120b6d6be80e78f7f70438906e57059400289f65339a1d4d9a540`
is unchanged from the original implementation. CI restored artifact `12768368615`
from run `40560322527`, verified its exact digest and requalified all three
binaries. No cold rebuild was needed. The final audit verifies 123 PCK entries,
38 PE imports and eight identity/self-test reports.

The original run's Windows `backslash` regression remains a failed preflight.
CPython normalized the fixture name while writing it, and the old reader also
checked only normalized names. The repair validates original ZIP names, signs
verified malicious header bytes and preserves local-header/CRC/expansion and
valid slash-path checks. The phase-carry corruption now changes even a genuine
zero; every mutation asserts it changed the input. No runtime code, numerical
gate, generator/save format or shipping inventory changed in that repair.

The [self-contained proof](evidence/m1-operation-witness-cloud-2026-11-09.json)
retains source bytes, raw control traces/proofs/writer receipts, derivations,
corruption rejections, artifact identities, qualification, complete audits and
the original failed archive/log. The ordinary audit reconciles 98 scenarios,
284 native phases and 37,355 operation rows. It retains kind-2 surface-removal
overruns of **803, 763 and 893 µs** against 750 µs, and H2 edit p95 bounds of
**166 ms** for both 16³ profiles against 100 ms. These remain failed observations;
their causes and target performance are unqualified. The earlier 819 µs failed
prefix, incomplete quartet and all historical failures remain unchanged.

Both preparation requests and all older pilots remain false; the permanent
reservation remains `8ab1624e0a74f153b6189afa837fb24f6688d8c9`. No attribution
process or replacement ran. The [subsequent saved review and finite decision](M1_OPERATION_WITNESS_REVIEW.md)
are complete without another engine run, new attribution declaration, laptop
request or M2.
