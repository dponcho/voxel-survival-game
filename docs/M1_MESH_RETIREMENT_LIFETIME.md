# Mesh retirement lifetime correction

October 26–27, 2026. The lifetime correction, actual matching-binary controls
and downloaded candidate audits are complete. This increment runs no attribution
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

The [pinned headless backend source](evidence/m1-retirement-headless-source-2026-10-26.json)
confirms that this Godot dummy backend allocates owned mesh RIDs and CPU mesh
storage. It supports a real allocated-resource control without a GPU claim.

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

The capability fixture explicitly advances that native-frame ledger between
direct production-entry calls. It does not manufacture route work, rendered
frames or a pacing result.

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

The [initial native build checkpoint](evidence/m1-mesh-retirement-native-preflight-2026-10-26.json)
preserves CI `40427167568`'s fixture include-path failure, verified artifact and
original logs. It ran no capability controls and published no candidate. The
relocated frozen header now includes the pinned voxel module by its complete
module path; its rejected run body is unchanged. CI `40427845266` compiles and
qualifies all three binaries with native key `a10b5a4e`, but stops before the
capability controls during a Windows regression test.

The [Windows fixture checkpoint](evidence/m1-mesh-retirement-windows-preflight-2026-10-27.json)
preserves that failed job, exact artifact and all three successful native
qualification reports. A historical mutation test decoded UTF-8 with Windows'
default codepage, then signed a different UTF-8 string from the saved source.
The source-identity check correctly rejected it before the intended boundary
mutation. A controlled simulation reproduces this with cp1252/LF; UTF-8/LF and
UTF-8/CRLF both reach the intended boundary rejection because this historical
reader normalizes newlines. This corrects the initial line-ending diagnosis.
The test now reads/writes explicit UTF-8/LF and signs the actual saved bytes.
All thirteen affected regressions pass locally; the production reader remains
strict. Native inputs are unchanged. CI `40440351282` reuses and requalifies the
verified binaries. The ordinary CI concurrency group was restored with this
test correction.

## Executed result and exact candidate

[CI 40440351282](https://github.com/dponcho/voxel-survival-game/actions/runs/40440351282) passes **280 Python regressions on each platform, eleven
native sanitizer suites**, matching editor/debug/release qualification, required
integration/package checks and the downloaded Windows/Linux audits. This is the
corrected source `2489baaa0f2686634a1bec15b7977608372b6c35`; its exported game identity is
`856537ab2ca7a6c58b8168cfe975fb7c7994c302`. Both earlier preflight failures are
preserved above.

| Matching binary | Complete fixture, µs | Actual cases verified | Semantic faults rejected |
| --- | ---: | ---: | ---: |
| editor | 555 | 10 / 10 | 17 / 17 |
| release | 550 | 10 / 10 | 17 / 17 |

| Binary | Empty-mesh path | Witness offset, µs | Ending-clock offset, µs | Alive at witness | Alive after call |
| --- | --- | ---: | ---: | --- | --- |
| editor | rejected-empty | 7 | 7 | true | false |
| editor | empty | 1 | 1 | false | false |
| release | rejected-empty | 2 | 2 | true | false |
| release | empty | 0 | 0 | false | false |

Offsets are from each actual operation start. The endpoint hook executes before
the ending-clock read; equal timestamps are allowed at microsecond resolution.
Exact call/witness order, ObjectIDs and raw endpoints are retained in the proof.

Both frozen rejected controls observe the empty ArrayMesh still alive at the
operation endpoint and gone after return. Both corrected controls observe the
empty, final surfaced and non-ArrayMesh objects already absent from ObjectDB
before the ending clock, with exact single charging. Surface removal, shared
ownership, admission refusal/resume and null-add behavior also pass. The hook
is cleared and no native work is retained. These are synchronous object-lifetime
observations; they do not qualify renderer-deferred work or target performance.

The [portable candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/40440351282/artifacts/12707720103) contains an inner ZIP of
**30,342,929 bytes**, SHA-256
`439d13d0d5a45f37e23876126027b945ce1d6f02bb2a0720af1b3fd5fe3200b8`. Its release executable SHA-256 is
`7b1fcbb7fe09e0da2bd17933a97764a2306623f4f0bc77c207556304d4853281`; PCK SHA-256 is
`b2499d1c344da4de213712f5acd1722e4443ab0bd9fa9ea924acd441522c2ea8`. Native key: `a10b5a4e72741182ffc2f8984302936f835f86d75de054bb5d5039e93ac4b0f5`.
The [self-contained cloud proof](evidence/m1-mesh-retirement-cloud-2026-10-26.json)
retains both raw controls, all seventeen corruptions per binary, source hashes,
qualification and Windows/Linux replay results. The downloaded complete Linux
audit matches the Windows audit; a fresh local saved-control replay agrees.

The saved record retains both broader operation-phase failures from this
candidate's diagnostic reports:

| Diagnostic | Operation | Maximum, µs | Limit, µs |
| --- | --- | ---: | ---: |
| Debug H2 retirement | Kind-2 surface removal | 1,488 | 750 |
| Release AB-H1-on-2 preparation | Upload | 824 | 750 |

The original 819 µs kind-2 failure also remains failed and unexplained. All
lifetime-control operation guards pass; that does not waive these broader
failures. No attribution route or
replacement process ran. All request flags remain false and the permanent
consumed reservation is unchanged. M1 remains blocked; no laptop action follows.
