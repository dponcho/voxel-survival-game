# Diagnostic measurement-method validation

## Question and scope

Can the current heavy-route evaluator distinguish a cost below or above the
unchanged 1% limit when route cost varies reproducibly? This is a validation of
the decision method, not an optimization, a new target measurement or M1
qualification. The legacy classifier and all workload/coverage/operation limits
remain unchanged. Target reports and detailed target measurements stay private.

## Controlled counterexample

The cloud-only `benchmark_method_validation.gd` drives the real diagnostic ledger
and evaluator with injected clocks. It reuses hypothetical eligible H1/H2 report
contracts, not executed terrain or actor measurements. Each quartet preserves
30 seconds of frame intervals, 1,800 declared fixed ticks and matching contracts.
All intervals, callbacks, switched/shared totals, final callbacks, five-second
blocks and final partial blocks are generated together. No report mean or elapsed
value is independently edited to manufacture a result.

The synthetic stationary route uses a 5,000 µs frame interval. The varying route
alternates 4,000 and 5,000 µs intervals over six five-second sections. Both repeats
in each mode receive identical clocks. These are deliberately artificial inputs,
not target measurements. Separate cases scale the enabled frame interval by
0.5% or 2%; endpoint quantization is retained. Another case adds 600,000 µs to the
enabled closure window, retaining its scope after the final callback. Setup is
200 µs; ordinary closure is 1,000 µs, with a nested 400 µs writer-drain bracket.

| Control | Stationary route | Perfectly repeatable varying route |
| --- | --- | --- |
| Identical frame clocks / null added wall cost | Passed | Inconclusive |
| Nominal frame interval +0.5% | Passed | Inconclusive |
| Nominal frame interval +2% | Failed | Inconclusive |
| Extra enabled closure cost | Failed | Inconclusive |

The current rule compares mean frame intervals from different five-second
sections within one repeat. It requires their range, divided by their mean, to
be below 1%. The varying null control violates this stationarity assumption even
though every same-mode repeat is identical and the true injected wall-cost
difference is zero. The known positive controls are rejected for the same reason.
This is a feasibility limitation of the rule's application to varying routes;
the implementation correctly retains inconclusive under that rule.

## Independent reconciliation

`tools/qa/diagnostic_method_validation.py` uses closed-form counts over constant
interval runs and exact rational full-window ratios. It does not call the
production ledger or classifier and does not expand the frame loop. It checks
the real engine's saved counts, all full/partial timing blocks, clock boundaries,
callback partitions, closure/drain scope, effect envelope, stationarity arithmetic,
classification and explicit absence of hardware/shared-overhead qualification.
Corrupt/missing controls, incorrect effects, lost tails/callbacks, scope changes
and altered decisions fail validation. The independent CLI rejects reports above 512 KiB; the
engine retains sixteen controls, four phases each, and bounded timing ledgers.
No event-time sample array or new runtime queue is introduced.

The matching-engine check is part of the existing Windows integration workflow.
JSON round trips retain decisions. Static tests separately compare the closed-form
oracle with direct event expansion across section and terminal boundaries.

[CI 37529525432](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432)
passed all three jobs October 6, completed 21:01 UTC, at code
`eaa86172ae4c5fadf19e9241b9c4f700ff841b70`. The pinned Windows editor ran
all sixteen controls (64 modeled phases); the independently downloaded 258,381-byte
control JSON exactly reproduces the saved oracle result. All stationary controls
classify as shown; all varying controls remain inconclusive. Twenty-five Python
regressions, native sanitizer/registration checks and the existing integration,
profile, startup and heavy smoke checks passed. The verified release candidate
and archive/report reconciliation are recorded in [M1_EVIDENCE.md](M1_EVIDENCE.md).

The first attempt, [CI 37527915469](https://github.com/dponcho/voxel-survival-game/actions/runs/37527915469),
failed before producing controls: the pinned engine rejected a conditional
untyped array assigned to `Array[int]`. Direct typed initialization fixes that
construction; the clock-only command now has a 60-second timeout. That failed
run supplies no measurement verdict. No engine ran or compiled locally.

## What remains unverified

These software null and positive controls are not a physical target A/A trial or
an injected CPU slowdown running against the real GPU. They validate the
classifier's response to known frame clocks. They do not measure hardware noise,
critical-path effects, CPU service, physical presentation or total instrumentation
overhead. The shared-instrumentation control is still absent and its causal
estimate remains null/inconclusive.

Private same-mode target analysis retains all raw rows, simulation-position bins,
terminal acknowledgement rows and final partial blocks. It supports investigating
repeatable route shape, but retains mismatches after alignment and does not prove
route-matched stability. Existing heavy coverage, upload, warm-up and phase-budget
failures remain unwaived. Neither a revised estimator nor this cloud check can
retroactively qualify those reports.

## Next bounded correction

Build a supplementary calibration experiment that separates repeatable route
shape from between-repeat drift: identical-mode controls, a calibrated positive
control, predeclared comparisons at matching simulation/route positions and a
complete whole-trial cost window. Keep actual fixtures/routes/actors/edits/ticks,
resolution/radii/workers/caps and unavailable coverage semantics. Account for the
minimal common harness and the still-shared instrumentation separately.

Keep the legacy classifier and saved verdicts authoritative while this successor
is tested. Adopting a replacement for qualification is a separate measurement-policy
decision; this validation changes no acceptance rule. A successor needs independent
null/positive, incomplete/unstable/failed-workload and saved-report tests, the pinned
cloud checks and a verified portable Windows candidate before a focused target
calibration. No additional target baseline, repeat or full matrix is requested
solely for the completed method review. M1 remains blocked; no profile qualified.

The supplementary runtime implementation is described in
[M1_ROUTE_CALIBRATION.md](M1_ROUTE_CALIBRATION.md). It remains an experiment and
does not adopt a replacement qualification policy.
