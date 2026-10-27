# Mesh retirement lifetime correction

October 26, 2026. Implementation prepared; matching native build, real controls
and downloaded candidate audits are pending. This increment runs no attribution
route and does not change a numerical performance limit.

## Correction and observable proof

The [saved review](M1_PREPARATION_FAILED_PREFIX_REVIEW.md) found that
`FreeMeshTask::run()` kept a local owning `Ref<ArrayMesh>` alive after
`record_deletion()` sampled and charged the ending clock. On the empty ArrayMesh
path, the possible final destructor therefore ran outside that operation's
measurement. The kind-2 819 µs surface-removal failure remains separate and failed.

The production correction adds an inner lexical scope. Surface queries,
one-surface removal or task-reference release, and destruction of every local
mesh reference now finish before the existing `record_deletion()` call. External
owners are preserved, and the task still postpones after each removed surface.
Operational start/end clocks, 750 µs individual limit, 1/2 ms frame budgets,
nested union accounting, phase carry and all workload/resource gates remain.

The hidden `--mesh-retirement-check` capability runs once per matching editor
and release. It calls the actual patched `FreeMeshTask::run()` and the frozen
rejected native run body with real Godot ArrayMesh resources. Empty ArrayMeshes
have a real allocated RenderingServer RID. No fake resource/destructor stands
in for the engine object.

A main-thread-only test hook in `record_deletion()` observes ObjectDB without
taking a new owning reference, immediately before the unchanged ending clock
read. This hook stores a bounded POD observation; dictionaries and file output
are constructed afterward. It is null in ordinary gameplay. Its inspection cost
stays inside the control's measured operation. Object identity, reference count,
surface count, liveness, actual start/end, thread, order and elapsed charge are
retained. A missing ObjectDB instance at that point proves the real synchronous
object lifetime ended before the measured endpoint. Renderer-deferred work and
GPU/allocator memory reclamation remain unverified.

The required control observations are:

| Case | Before the operation endpoint | After return |
| --- | --- | --- |
| Frozen rejected empty ArrayMesh | Object still alive under the local reference | Object gone |
| Corrected empty / final surfaced ArrayMesh release | Object already gone | Object gone |
| Two individual surface removals | Same object remains, exactly one surface removed per call | Postponed |
| External shared owner | Object retained by that external owner | Remains until explicit external cleanup |
| Admission refusal / next-frame release | No endpoint on refusal; next real call releases inside its bracket | No fabricated measured zero |
| Non-ArrayMesh | Actual PlaceholderMesh destroyed inside the bracket | Object gone |
| Null add | No task or measured endpoint | No retained work |

The admission-refusal case explicitly injects a 251 µs prior-charge precondition
against the unchanged normal 1 ms budget; it does not manufacture elapsed work.
Its resumed call begins in a new native frame. Every real deletion is charged
exactly once and reconciles against the existing phase/frame ledger. There are
ten fixed case records, an internal five-second cap and a sixty-second process
cap; there is no automatic retry.

## Verification and compatibility

`tools/qa/mesh_retirement.py` binds the new native/control sources in BUILD_INFO
and PCK metadata, verifies the unchanged frozen rejected body, independently
reconciles the actual controls and rejects seventeen re-signed semantic faults.
Eight new pure regressions cover lifetime observations, shared/null ownership,
counter failures, exact integer/object identities and phase charging. An
additional historical-proof test rejects attempts to reuse the old candidate's
source metadata for this changed native implementation. The archived CI-verdict
test uses its original metadata fixture, while the production source-identity
check remains strict.

The candidate build retains all eleven native sanitizer suites, required
integration/package checks and downloaded Windows/Linux audits. Performance
guard outcomes remain separate from lifetime-control validity: a complete
over-limit deletion is retained as failed, even when destruction order is
correct. Capability proof never qualifies operation performance or shipping cost.

No save, generator, content ID, observer inventory or existing raw codec changes.
The native key changes because the production patch and probe change; matching
editor/debug/release binaries and a new portable candidate are required. Both
preparation requests, all three older consumed pilot inputs and the permanent
run reservation retain their consumed states. M1 remains blocked and no laptop
action is requested.
