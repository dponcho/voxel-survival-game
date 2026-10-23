# M1 direct preparation owner scopes

October 23, 2026. Implementation and controls only; **no attribution route or
laptop run**. M1, diagnostic cost and target performance remain unqualified.
The [adopted design](M1_PREPARATION_DEMAND_DECISION.md#narrow-owner-extension-after-lifetime-capability-passes)
is implemented as `m1-preparation-demand-attribution-1`, inventory
`m1-preparation-demand-inventory-1`, raw version 2 / `CAIRNOB2`.

## Scope and raw contract

| Slot | Real entry | Deliberate limit |
| --- | --- | --- |
| 13 | `CairnFixture::generate_block()` | Whole function, including overlay/compression and return; excludes task scheduling and other worker work. |
| 14 | `CairnMesher::build()` | Whole face guard, stock mesher and bounded split, including every overload return. |
| 15 | `VoxelEngine::process()` | Completion/application/destruction, time-spread/progressive work and viewer synchronization, including the existing frame marker. |
| 16 | `VoxelTerrain::process()` | Quick reload, viewer processing and meshing submission. |

The 40-byte header and 192-byte little-endian record layout remain bounded by
32 MiB wire bytes, eight lanes and depth eight. Old version 1 encoding and its
slots 1–12 remain unchanged; its reader rejects version 2. Only version 2 admits
slots 13–16. Each new native record uses `units=1` for the attempt and the old
`bytes` field as an explicitly versioned **outcome tag**, not bytes: 1 normal,
2 meshing overload. `complete=1` witnesses actual RAII completion. Attempt,
completion, overload and crossing populations are independently reconciled.

All four raw current-thread reads retain unsigned cycles, wall brackets,
availability, success and OS error. Counter/owner/context/cap failure stops new
version 2 admission and retains its prefix; admitted scopes still return.
No sampling, zero replacement, cycle/time conversion or fitted correction.

Main owners use the original main stack and shared boundary OS TID. Inclusive
full, body, bookkeeping and exclusive body remain distinct; nested unions are
charged once. A main section crossing fails. Only preparation (section 0)
admits new native scopes. An admitted worker completes after handover on its
actual executing thread; its original begin/end/submission context and outcome
remain. Crossing demand is separate, without clipping or wall-time splitting.

## Pool and lifetime

The pinned pool's real thread entry installs a unique monotonically assigned
incarnation token and thread-local pool/index/count identity. Registration binds
that token, the actual executing OS TID and a bounded lane on its first admitted
call. A replacement requires real retirement of the previous incarnation.
Unexpected pool/index/count, reused live identity and mismatched completion fail.
The existing pool retains one terrain worker; no pool or worker is added.

A single publication mutex safely acquires bounded strong session references
and closes acquisition/unpublish races. Each scope releases its reference on
return. Disabled function entries perform the atomic dispatch check and no new
counter read, trace lock, allocation, I/O or worker scheduling. Pool bootstrap
only assigns its thread-local identity and monotonic incarnation; it does not
read CPU/wall counters, allocate or acquire the trace lock when disabled.

The distinct opt-in mode orders start observation before allocation, reservation
and publication. It preserves the existing work, operation, resource, readiness,
coverage, edit and writer guards. Normal and failed closure stop submissions,
drain admitted work, join/detach writers, unpublish, copy immutable counts/owners,
witness session destruction, seal/emit/flush/close, explicitly dispose the last
recorder owner, hash, then take the ending shared boundary. An abandoned native
caller unpublishes as failed; it cannot leave a hidden publisher owner.

Persistent pool threads have a drained registration detach witness, **not a pool
join**. Actual retirement is recorded separately when a worker really exits.
Record/vector capacities, the fixed session/owner table and bounded serialization
capacity are reported separately. Weak-reference expiry witnesses requested
object/vector destruction, not allocator/OS page retention. Additional reads,
shared locks and dispatch perturb scheduling; bookkeeping spans do not bound all
of that perturbation. No total engine/worker/GPU/driver or causal cost is inferred.

## Bounded verification

`--preparation-demand-check` calls the real four functions in each matching
editor/release, under a five-second native cap and 60-second outer timeout. Its
existing pool executes finite generation, real stock meshing/splitting and a
checkerboard face-guard early return. It exercises actual one-worker replacement,
a gated generation return across handover, nested main scopes, a persistent
worker detach and joined UTF-8 qualification/proxy writes. Separate real-entry
counter/cap/unregistered-owner/main-crossing/write faults retain failed prefixes
and reclaim their owners. Twenty saved metadata corruptions must be rejected.

The eleventh native sanitizer suite covers disabled dispatch, real thread entry/
exit identities, legal same-TID reuse, overlap refusal, nested union, crossing,
unsigned/raw failure, saturation/depth, foreign-thread completion, unpublish with
an admitted scope and retained lifetime. Ten new Python cases cover the independent
version 2 reader and required controls. All **213 Python regressions** and the
three affected native ASan/UBSan suites pass locally. Local LeakSanitizer is
unavailable under the executor's `/proc` restrictions; CI retains full sanitizer
settings and all eleven suites.

Required CI parses the new mode, runs both new controls, rebuilds/requalifies
all three exact-key Windows binaries, exports the portable player, retains all
existing integration/offline checks and replays the downloaded candidate and
saved controls on Windows and Linux. These cloud checks and the candidate are
**pending** until their actual result is recorded here.

## Run boundary and next decision

Required CI has no preparation route input. All three consumed pilot flags stay
false. The new `--preparation-demand-pilot` entry additionally requires a separate
prospective exact-native-key/inventory declaration, one process, at most five
trials, no retry and no positive/shipping continuation. No such declaration or
route process is created by this increment. The independent reader retains the
original complete fixed-work/lifecycle checks and adds version 2 ownership and
destruction; a failed or unavailable attribution never becomes a passing zero.

After controls and matching candidate pass, the next bounded task is to review
their exact proof and prospectively decide whether to declare **at most one
process, warm-up plus four bare trials**, as already specified in the adopted
design. Preserve 32³/one worker, complete 4,320 ticks / 103,680 actor ticks /
288 edits / 72 saves, full height and radii, all deadlines/caps and numerical 1%.
That future decision is separate; no route, laptop action or M2 follows now.
