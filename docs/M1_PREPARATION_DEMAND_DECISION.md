# M1 preparation demand: saved decision

October 19, 2026. Saved evidence only; **zero engine processes**. This completes
the design task at `6380332`. M1, target performance and optional diagnostic cost
remain unqualified. The numerical 1% requirement and complete lifecycle remain.

## What the existing evidence identifies

The [original attribution proof](evidence/m1-shipping-observer-cloud-2026-10-19.json)
is unchanged (SHA-256
`c3f39903cf7c66028a9a8d6b5124404643e4f1f55c463b5ab4727294d10d4db1`).
The [derived record](evidence/m1-preparation-demand-review-2026-10-19.json)
rechecks all 80 raw files / 98,522,367 bytes and reproduces the original
Windows/Linux sequence audit exactly. Its reader executes no engine.

The six shared boundaries contain current-main-thread observations in addition
to process observations. All twelve observations in each trial retain TID 7280,
successful raw calls, exact unsigned decimal counters, sequential wall brackets
and monotone counters. For boundary B, use
`[B.before.thread_lo, B.after.thread_hi]`. Between boundaries S and E, main
demand is bounded by `[E.lo-S.hi, E.hi-S.lo]`; the lower bound is clamped at zero.
Boundary midpoints telescope across all five sections. These are direct thread
observations, never process-minus-thread estimates.

The safe inner preparation window runs from the start boundary's
`after.thread_hi` to the prepared boundary's `before.thread_lo`. Within that
window, complete main roots and their consecutive raw endpoint gaps partition
the same thread exactly. Nested children are included once in their root.

| Trial | Native preparation frames | Whole-main preparation bounds, cycles | Inner root cycles | Inner gap cycles |
| --- | ---: | --- | ---: | ---: |
| warm-up | 777 | [2,630,843,343, 2,631,298,233] | 30,752,771 | 2,600,090,572 |
| bare 0 | 824 | [2,782,657,997, 2,782,998,056] | 31,850,914 | 2,750,807,083 |
| bare 1 | 779 | [2,598,401,260, 2,598,722,871] | 31,008,430 | 2,567,392,830 |
| bare 2 | 821 | [2,776,120,144, 2,776,437,075] | 34,124,938 | 2,741,995,206 |
| bare 3 | 779 | [2,618,384,974, 2,618,704,502] | 31,045,683 | 2,587,339,291 |

There are respectively 781 / 826 / 781 / 823 / 781 inner roots, with one more
gap per trial. No root crosses an inner boundary. The prepared snapshot root
(slot 12) is inside the prepared boundary bracket and outside the safe inner
window; its original endpoints are retained, not clipped or charged to a gap.
The reader would retain a crossing root and mark its partition unavailable.

| Pair, later minus earlier | Process preparation midpoint change | Whole-main preparation midpoint change | Inner gap change |
| --- | ---: | ---: | ---: |
| bare 0 → bare 3 | −171,038,473 | −164,283,288 | −163,467,792 |
| bare 1 → bare 2 | +170,207,007 | +177,716,544 | +174,602,376 |

This localizes substantial preparation variation to **main-thread execution
outside the captured roots**. It does not identify a specific engine function,
prove a causal cost per native frame, or establish equal terrain-worker CPU
demand. Matching native work counts are retained by section, not interpreted as
equal demand. Native frame markers are `VoxelEngine::process()` invocations,
not a verified count of complete Godot iterations. Gaps can contain engine work,
orchestration, bindings, logging/UI and unscoped observer dispatch. They are not
observer-free time. Do not subtract any of these values from process demand,
normalize by frames/callbacks or fit a correction.

## Adopted prospective design

**First implement recorder disposal as a bounded capability, with controls and
a matching candidate only.** This is a demonstrated lifecycle defect and a
prerequisite to any new complete-trial observation. Do not optimize a captured
owner merely because it is large. Tick formatting, writers, readiness, workload,
terrain scheduling and the cost estimand are unchanged.

The present `CairnProbe::observer_finish()` seals, emits, flushes and closes the
trace but retains its `shared_ptr`. `CairnReportSink::finish()` joins its worker
but retains another `shared_ptr`; `_close_reports()` copies the worker witness
without detaching it. Allocation starts after the start counter boundary, but
its release can occur in the next setup or process teardown. The old result
cannot supply this disposal cost retroactively.

Add a distinct explicit disposal API and witness, preserving the old finish API,
v1/v2 IDs, codecs, readers and historical verdicts. Required lifetime ordering:

1. Capture the shared start boundary **before** recorder allocation, lane stack
   reservation, attachment or owner registration. Charge setup and failures.
2. Stop new submissions. Use existing terrain/report drain barriers; wait for
   admitted scopes to return. Copy immutable counts, bytes, lane identities and
   joined-writer evidence. Detach every joined sink and any native publisher.
   A live worker, open scope or foreign strong owner prevents disposal.
3. Seal and emit the complete trace or honest failed prefix; retain raw errors.
   Flush/close files, copy immutable metadata and release serialization storage.
4. Release the final recorder reference, its record allocation and lane storage
   inside the originating trial. Return an explicit destruction witness from an
   independent weak reference, without keeping a hidden strong reference alive.
   Failed disposal is unavailable/invalid, never a passing zero. Do not block
   indefinitely waiting for a reference count.
5. Only then hash retained files and take the final shared counter boundary.
   Keep the separately measured terminal marker and original closure/report
   rules. Actual allocator/OS page retention remains distinct from object
   destruction; no claim that process committed memory immediately falls.

The **next bounded implementation** adds this capability and its controls only.
It does not modify or rerun the consumed route modes and adds no owner scopes.
Use a new native key, matching editor/debug/release, required integration/package
checks and a portable candidate. Keep all three pilot inputs false. One bounded
new disposal control per matching editor/release is sufficient; retain the
existing API controls. Each new control has a five-second wall cap, finite work,
no route/dose and no automatic retry. Test refusal while active/attached/live,
success after join/detach/seal, last-owner destruction, readable trace after
destruction, post-disposal API rejection, repeated disposal, and allocation,
counter/cap/write failures. Preserve failing bytes and original controls.

### Narrow owner extension after lifetime capability passes

A later separately selected implementation may extend the existing ledger with
exactly these four direct scopes. This is a prospective specification, **not
implementation or engine-run authorization in this saved task**.

| Owner | Verified entry | Observation and deliberate limit |
| --- | --- | --- |
| Native generation | `CairnFixture::generate_block()` in `native/sandbox_world/godot/fixture_generator.cpp` | Current executing thread's raw cycles around the entire function, including overlay/compression and every exit. Does not cover task preparation, queueing, allocator work outside this function or the entire worker. |
| Native meshing | `CairnMesher::build()` in the same file | Entire function including face guard, stock mesher and splitting, with overload/early-return outcome. Successful meshed count alone is insufficient to reconcile attempts. |
| Engine completion/application | `VoxelEngine::process()` in pinned `engine/voxel_engine.cpp` | Main thread; includes result application/destruction, time-spread/progressive work and viewer synchronization. Does not cover the rest of Godot. |
| Terrain update | `VoxelTerrain::process()` in pinned `terrain/fixed_lod/voxel_terrain.cpp` | Main thread; includes quick reload, viewers and meshing submission between readiness polls. Does not cover all scene/renderer processing. |

These upstream entries were checked at Voxel Tools
`2ac9f5f8a8219bf499314cc0fad54ffc47df908f`; the project patch puts its native
frame marker at `VoxelEngine::process()` entry. Godot `Main::iteration()` was
also checked at `ed1daf0bf001b61586d9930840f2f1394092c079`: its physics,
scene/server/draw, queue flush and pacing scope is broader and can straddle
script boundaries. A whole-iteration root or general engine profiler is deferred.

Reuse the bounded ledger's current-thread reads, raw error representation,
nesting, caps and independent decoding. Use a **new** method
`m1-preparation-demand-attribution-1`, inventory
`m1-preparation-demand-inventory-1`, and raw version 2 / magic `CAIRNOB2` if
implemented. Preserve slots 1–12 and add generation/meshing/engine/terrain as
13–16 in that version alone. Old readers must reject it, not reinterpret it;
the existing v1 codec and old runtime evidence remain untouched.

Ownership and measurement rules for that extension:

- Main scopes run on the boundary thread and use the same stack as existing
  main scopes. Report inclusive full, body and bookkeeping separately; charge
  nested roots/children by their union, never summing an inclusive parent again.
  Reject a main scope crossing a section; do not repair it with clipping.
- Admit new native scopes only while preparation context is active. Retain
  each admitted worker scope through its actual return even after a handover.
  Record begin/end section and attempted/completed/overload outcome, plus original
  native counts. Cross-boundary demand stays separate; do not allocate all of it
  to preparation or split it using wall time.
- Bind a terrain lane to the actual pool incarnation and OS thread identity,
  with explicit registration/retirement proof. TID alone is not an incarnation.
  Keep one terrain worker and the same existing pool; add no worker or pool.
  Reject unregistered/overlapping reused identities, unexpected workers, missing
  attempts, double completion or live owners at seal. Persistent pool threads
  need a drained scope/registration detach witness, not a fictitious pool join.
- Publish one recorder session safely before terrain admission; scopes acquire
  a bounded strong reference and release it on every return. Unpublish before
  seal, with zero in-flight scopes and the existing native drain. The disabled
  path takes no new counter, allocation, trace lock or worker scheduling action.
  Verify this source/behavior property before declaring the new mode ready.
- Retain all four per-span read results, availability, success, OS error and
  monotonic wall brackets, with exact unsigned cycles. An unavailable/failed,
  decreasing, reversed, incomplete or mismatched observation invalidates the
  affected attribution and stops the prefix. Preserve the raw failure; no zero,
  time conversion, sampling, repair or fitted process residual.
- Keep the 32 MiB **wire trace** cap, eight lanes, depth eight and first-failure
  stop. Account for actual recorder/vector capacities, lane registration and
  serialization allocations separately; wire size is not resident memory.
  Reserve before admission inside the start boundary, free before the end.
  No growing allocation or trace I/O in terrain callbacks. Existing global
  ledger contention and the additional reads perturb execution and scheduling;
  full/body bookkeeping cannot bound all that perturbation.

The extension needs pure native controls for early returns, nesting/union,
worker incarnation reuse, cross-boundary completion, counters/errors, saturation
and disposal; matching editor/release controls must call the real four entries
with bounded fixture work, not synthetic slot calls alone. The independent
reader must reject corrupt ownership/sections/populations and reconcile original
work, writer bytes and complete closure without weakening operation guards.
New patches/module code require a new exact key and all three matching Windows
binaries, a portable candidate and existing required checks.

Only after those prerequisites pass may a new prospective declaration choose
**at most one process, warm-up plus four bare trials**, fixed original H2 work,
32³/one worker, 4,320 ticks / 103,680 actor ticks / 288 edits / 72 saves, full
Y[-64,192), 96/128 m radii and existing 512/8,192 resource caps. Retain existing
preparation/closure deadlines, complete elapsed/process boundaries and all
readiness/coverage/resource/edit/operation limits. Use no new frame-count target,
replay, calibration, positive/shipping continuation or profile matrix. Stop on
the first raw/API/ownership/lifetime/work/guard failure, missing file or cap;
retain the prefix. A complete prefix also stops after trial five regardless of
its numbers. Another process needs a new evidence-based decision.

That future observation could compare **direct generation/meshing demand**
with **direct main engine/terrain demand** in corresponding preparation windows,
alongside whole-main/process bounds and remaining gaps. A large worker change
would identify demand inside those functions; a large main-owner change would
locate demand inside that owner. Neither establishes causality, per-frame cost,
total worker demand, an observer-free baseline, whole-engine/GPU/driver costs,
shipping incremental cost or target performance. Uncaptured work and boundary
crossings remain unavailable. Stable new scopes would not prove other work
stable. The original 2.850549401% v2 width and 1.073468789% drift remain failed;
the perturbing attribution width 1.788237675% remains descriptive only.

## Reproduce this saved task

Download/extract the original
[observer artifact 12156439319](https://github.com/dponcho/voxel-survival-game/actions/runs/39179723675/artifacts/12156439319)
(ZIP SHA-256 `c471fd040ff3c750965cb859d66d0244ed10029d69ddb777fdcc5e22c025d91c`).
`PILOT_ROOT` below is its directory containing `independent-audit.json` and `raw/`.

```bash
python tools/qa/preparation_demand_review.py --artifact-root "$PILOT_ROOT" --check docs/evidence/m1-preparation-demand-review-2026-10-19.json
python -m unittest discover -s tests/integration -p 'test_preparation_demand_review.py'
```

Seven focused regressions cover exact saved main bounds, unsigned values above
the signed maximum, raw failures/identity/order, nested ownership, boundary
snapshots, crossing spans and false/overlapping owners. No native/runtime,
inventory, dependency, save/generator or workload bytes change in this task.
The complete pure regression suite passes all 195 cases; the saved replay
matches the committed derived record and the original sequence audit exactly.
No laptop test, new route or M2 expansion is needed at this stage. Continue with
**GPT-6.1 Sol Max**.
