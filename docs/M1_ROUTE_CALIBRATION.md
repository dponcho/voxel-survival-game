# Supplementary route-matched calibration

The title offers **Calibrate heavy-route measurements (~7 min + loading)**.
This experiment tests measurement repeatability and sensitivity to known closure
wall cost. It does not replace the original heavy/flat A/B verdicts, establish
frontier-probe cost or qualify M1. The 1% requirement and legacy stability rules
remain unchanged. Detailed target reports and measurements remain private.

## Actual workloads and controls

A fresh process performs the existing three-minute warm-up, then H1 and H2
quartets: reference, closure, closure, reference. Each repeat prepares a fresh
heavy fixture and executes exactly 1,800 fixed 60 Hz ticks. H1 keeps 12 proxy
actors; H2 keeps 24 actors, 256 rain instances, four accepted border edits per
second and a 32 KiB proxy storage write per second. Route origin, 6.5 m/s sprint,
15-second reversal, 1280 × 720 resolution, 96/128 m radii, chosen render blocks/
workers, native admission policy and collision safeguards match the existing
heavy comparison. Preparation, gameplay/edit settlement and retirement retain
separate operation evidence. No world/save semantics changed.

All four repeats disable the frontier scan. Its dispatch count and elapsed
switched bracket remain zero; coverage status, minima and exposed counts remain
unavailable/null. All shared operation/edit tracing, render queries, collision
metrics, detailed CSV/UI, command fingerprints and proxy storage stay enabled.
This is an identical-instrumentation null/positive control, not a shared-
instrumentation-off baseline.

The two closure repeats yield existing process frames after the last measured
callback, edit settlement, native phase closure and full writer drain. A monotonic
bracket records a requested 600,000 µs delay (nominally 2% of the 30-second
route) and its actual elapsed time, including scheduler overshoot. The loop yields rather than busy-spinning and caps at
10,000 yields; an incomplete or cancelled dose cannot resolve the control.
Scheduling stalls cannot be preempted by this cooperative bound. The delay is
outside gameplay and inside the complete measurement setup-through-report
window. It is separate from the nested writer-drain bracket. Ordinary callback,
formatting, finalization and file-I/O cost remain included; combined summary
hashing/serialization/writes retain `report-finalization.json`. Overlapping wall
brackets are not added.

This deliberately simple positive control validates sensitivity to added closure
wall time. It does **not** calibrate a per-frame CPU slowdown, GPU overlap,
critical-path frontier cost or total shared diagnostics. Those remain unavailable
causal estimates. A successful closure control is insufficient for overhead
qualification.

## Predeclared matching and assessment

The ledger retains six simulation-position sections and a seventh terminal/
acknowledgement bucket. At callback entry, ticks 0..300 map to section 1,
301..600 to section 2, through 1501..1799 in section 6. Tick 1,800 callbacks,
including final edit acknowledgement, remain separately retained. An interval
crossing a section boundary belongs wholly to its ending callback's tick; there
is no trimming, interpolation, reweighting or removal of partial intervals.
This diagnostic alignment does not assert identical physical rendering events.

Every interval and complete callback contributes once. Per-section sample/time/
callback totals reconcile to the unchanged raw frame CSV and diagnostic ledger.
Missing sections have explicit unavailable status and null means. The minimal
new ledger's call brackets are reported separately. They exclude clock reads;
callback-ledger tail bookkeeping follows the existing callback timer but remains
in frame intervals and the complete window. These observed brackets are not
causal instrumentation cost. Still-shared instrumentation has no uninstrumented
control, so its overhead remains null/inconclusive.

The supplementary assessment compares complete-window time per callback,
including all terminal rows and closure cost. The two reference repeats are the
null control. Reference and closure repeat pairs each need below-1% symmetric
relative difference in complete-window means and corresponding route/terminal
section means. Cost differences **between different sections** do not invalidate
perfectly repeated route shape. Section means are repeatability diagnostics;
the effect estimator uses every complete-trial sample and cost, not averaged
section ratios.

The minimum/maximum positive-to-reference ratios form a conservative envelope,
not a statistical confidence interval. Only a lower bound at or above 1%, with
all evidence/workload/repeatability/dose guards satisfied, gives
`controls_resolved`. Missing, short, stalled, reordered, failed, unstable,
threshold-crossing or apparent-speedup controls remain inconclusive. Raw envelope
arithmetic can still be reported for an inconclusive assessment. All qualification
flags stay false and legacy classifications remain authoritative. No section or
whole-trial tolerance becomes a replacement acceptance rule.

## Bounds and independent checks

There are seven aggregate buckets per repeat, four repeats per workload, no
retained per-frame array and no new queue or worker. Existing scan, trace, disk
queue, file and histogram caps remain. The ledger detects reversed/out-of-range
ticks and invalid intervals. The software-control JSON is bounded to 1 MiB in
Actions. Raw reconciliation streams CSV rows without retaining their timeline.

The clock controls use hypothetical eligible report contracts and modeled route
sections, rather than executing thirty-second terrain/actor workloads. Separate
runtime observations and release smoke exercise actual engine behavior.
The pinned-editor script exercises 26 software controls across H1/H2, including
stationary/varying null+closure quartets, incomplete/reordered/stalled/failed
workloads, matching-section drift with an unchanged whole-trial mean, missing/
overlapping doses, missing terminal data, contract mismatch, smoke and I/O failure.
An independent Python oracle uses exact rational means/envelopes and checks the
saved decisions. Static checks use direct aggregate fixtures and adversarial
saved CSV/phase boundaries. Actual runtime observations retain heavy preparation,
route/reversal, exact cutoff and zero switched dispatches. A separate release
smoke executes both real quartets, then independently reconciles saved route bins,
previous/final callbacks, unavailable coverage and delay/drain/report boundaries.
Smoke remains inconclusive and cannot establish hardware precision.

[CI 37556502450](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450) passed all three jobs October 7 UTC:
33 Python regressions, five native sanitizer suites, editor/debug/release
registrations, all 26 controls and their independent oracle, actual runtime
observations, release calibration/saved reconciliation and existing integration/
profile/startup/heavy/package checks. All sixteen legacy method-control expectations
remain unchanged. Downloaded archive/raw review verifies the exact candidate and
reconciles all ten smoke folders, 98 scenarios and
284 native phases. The actual calibration smoke retains explicit
unavailable later sections and inconclusive status; no target precision is implied.
Exact build, artifact, checksum and audit totals are in [M1_EVIDENCE.md](M1_EVIDENCE.md).

Two earlier runs completed the controls and actual release calibration, then
failed the final saved-report check because the independent reader used exact
floating equality for a JSON-rounded fractional mean. Integer sample/time/
callback totals reconciled. The correction accepts only serialization roundoff
(relative 1e-12, absolute 1e-9 µs), retains exact integer reconciliation and rejects
meaningful mean alterations. This is not a change to the 1% cost or legacy
stability rules. The actual first failed-run CSV subsequently reconciled through
the corrected reader; neither failed run supplies a verified Windows candidate.

## Smallest target check

Using the verified candidate linked in [M1_EVIDENCE.md](M1_EVIDENCE.md), run this
one menu choice once at **32³ / one worker**, on AC power with the foreground game
visible, and retain its complete report folder privately. No new full baseline
or profile matrix is needed. Review raw reconciliation, null repeatability and
positive sensitivity before further target requests. An inconclusive result is
useful evidence of the instrument's current precision; it is not permission to
trim unstable sections or weaken the 1% cost requirement. Existing coverage,
upload/phase-budget and shared-overhead failures remain separate M1 gates.
