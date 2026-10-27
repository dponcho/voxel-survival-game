# Matched heavy-route frontier cost comparison

The title offers **Compare heavy-route probe cost (~7 min + loading)**. This
separate mode runs the existing three-minute warm-up, then H1 and H2 quartets in
off/on/on/off order. Each diagnostic route runs exactly 1,800 fixed 60 Hz ticks
(30 seconds), travelling outward at 6.5 m/s with the same 15-second camera
reversal. These bounded comparisons do not replace the unchanged four-minute
H1/H2 qualification routes, full baseline, paced pass or matrix.

Every repeat creates and fully prepares a fresh fixture 1 at the same origin.
H1 keeps 12 proxy actors; H2 keeps 24, 256 rain instances, four border edits per
second and one 32 KiB proxy storage write per second. Resolution/scale, 96 m
visual and 128 m data radii, render-block choice, worker count, fog, collision
safeguards, native admission caps and four-step physics catch-up cap remain.
Tick endpoints stop additional render-dependent tail commands. Contracts record
actual fixture/profile settings. Bounded command fingerprints and at most three
route checkpoints retain edit scheduling and camera intent. Different settings,
ticks, actor activity, accepted/deferred edits, storage counts, command schedules,
missing movement data or insufficient sprint distance invalidate equivalence.

## Switch and cost scope

The switch controls only `sample_frontier`, its analytic coverage ledger and
the shader-conversion model. The off path returns explicit unavailable coverage
without dispatching the native scan. Counts at the dispatch boundary prove zero
calls off and one per measured callback on, including edit-settlement callbacks.
Disabled distances, minima and exposed counts are unavailable/null, never passing
zeros. Enabled unavailable/invalid samples invalidate comparison integrity.
Existing conservative analytic failures and operation-budget evidence remain in
each report and continue to make a failed workload's comparison inconclusive.

The native edit tracker is observed enabled at setup; its disabled final flag is
normal closure, reconciled to accepted edit-event counts.

Both modes retain detailed frame CSV/UI/renderer queries, native lifetime and
phase counters, operation traces, edit tracing/settlement, collision timers,
proxy storage writes and the existing bounded disk worker. H2's final edit still
settles under the existing 200 ms rule; its frames and native work remain in the
measured phase. Preparation, measurement and retirement remain separate.

Schema 6 preserves the original 38 frame columns and appends
`diagnostic_switched_usec` and `diagnostic_shared_usec`. Both use the existing
previous-callback `diagnostic_frame` convention. The switched value is the nested
wall span for scan/evaluation/model processing; shared is the complete callback
remainder, including formatting and submissions. Summing each CSV column plus
its final callback value reconciles to separate totals and their sum reconciles
to complete callback wall time. The current native `frontier_probe_usec` remains
unchanged. These elapsed spans are not CPU service or causal added-overhead
estimates. Changed CSV payload/formatting cost is captured by the full A/B window.

The A/B ratio still uses complete measurement setup through callback completion,
phase closure, writer join/flush and scenario-report construction, per callback.
Writer drain is nested within finalization; worker/native/renderer spans are not
added. Combined file hashing, summary serialization/writes and final UI stay
separately timed in `report-finalization.json`. Preparation and retirement retain
their own operation evidence and remain outside the comparison window.

The 1% threshold, repeat-range rule and five-second block drift checks are
unchanged. Smoke, short/stalled, incomplete, failed, unstable, consistent apparent
speedup or threshold-crossing comparisons are inconclusive. A switched-cost pass
cannot qualify total diagnostic overhead: shared native hooks, physics timers and
bookkeeping have no uninstrumented control. Reports explicitly retain total
overhead as inconclusive with a null causal estimate. M1 stays blocked.

## Bounds and validation

No new worker or sample queue is introduced. The existing 1,024-region scan cap,
64 native records, 128 pending operation rows, bounded edit tracker, 64-item disk
queue, 64 KiB item cap, 64 MiB CSV files, 8 MiB edit file, 64 timing blocks and
bounded histograms remain. Per-repeat contracts, counters and three checkpoints
are constant-sized. Overflow or missing data fails evidence integrity.

Matching-editor tests observe the runtime switch, actual route targets, camera
reversals, heavy admission selection, actors/rain and exact tick cutoff.
Independent cases exercise workload mismatches, missing coverage, partitions,
failed budgets, stability and the 1% boundary. Debug/release smoke runs execute
real H1/H2 quartets with shortened one-second routes, then read the saved JSON and
reconcile both callback partitions, native phases, edit events and frontier CSV.
Cloud-only smoke output roots retain all raw CSV/edit/JSON evidence with the
existing Actions evidence artifact. Normal target reports stay local/private.
Smoke cannot qualify overhead, target rendering, physical pacing or HD 620.

The smallest target check is one baseline-profile run of this menu choice,
retaining its complete report folder privately. Review equivalence, probe
dispatch, raw reconciliation and stability before requesting any longer repeat
or full matrix. The historical startup stall's cause remains unresolved; this
later comparison does not measure startup instrumentation overhead.

## Verified cloud candidate

[CI 37515081002](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002)
passed all three jobs October 6. Three saved debug/release heavy smoke reports
independently reconcile both quartets, all 27 phases per report, callback
partitions, native operation counters, unavailable off coverage and accepted edit
events. Workload equivalence and switching are verified; smoke overhead and total
shared overhead remain inconclusive. All four existing profiles ran; their 16³
coverage/edit-latency failures remain. Exact portable identity/checksum and raw
cloud artifact provenance are in [M1_EVIDENCE.md](M1_EVIDENCE.md). The first exact-build HD 620
comparison has now been reviewed; see the target-review status below.

## First target review

The October 6 baseline-profile target check completes with independently verified
workload equivalence, probe switching and raw saved-report reconciliation.
Disabled coverage remains unavailable; shared traces, callback partitions, phase
closure, edit settlement and I/O/finalization retain their scope and bounds. The
short heavy routes have no raw deadline misses.

Both overhead comparisons remain inconclusive under the unchanged rules: timing
is unstable, enabled coverage fails, and one H2 upload exceeds its individual
operation limit. Shared total overhead still has no uninstrumented control. The
separate supported shader-conversion model retains alarms; pixel visibility and
causation remain unverified. Preparation/retirement budget exceedances and a
warm-up deadline miss remain unwaived. Detailed target measurements and reports
stay private. No additional target repeat/full matrix is requested solely for
this review. Follow [NEXT_TASK.md](NEXT_TASK.md) for the bounded cloud correction.

## Measurement-method review

The clock-control investigation is recorded in
[M1_MEASUREMENT_METHOD.md](M1_MEASUREMENT_METHOD.md). It tests the legacy evaluator's
stationarity assumption using identical repeats with known frame clocks and
closure costs. These controls are not physical A/A or executed heavy workloads.
The legacy classifier and the target report's inconclusive results remain
authoritative; coverage, operation and total-shared-overhead gates remain open.
Supplementary route-matched calibration is the next bounded measurement task.
