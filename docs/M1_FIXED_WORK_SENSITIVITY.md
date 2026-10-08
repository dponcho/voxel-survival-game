# Experimental fixed-work elapsed/count sensitivity

M1 remains blocked; no target profile is qualified. This supplementary assessor
is saved as `fixed_work_sensitivity`, alongside the unchanged `route_calibration`,
flat and heavy assessments. It adopts no qualification policy, changes no 1%
requirement and cannot retroactively qualify a target report. Target identities,
measurements and raw reports remain private.

## Estimand and retained costs

The estimand is **complete measurement-setup-through-scenario-report wall duration
for matched 1,800-tick workloads**, in integer monotonic microseconds. Its ratio
uses elapsed duration directly. Render callback count is a separate observation,
not its denominator. Complete time per callback remains descriptive:
`time-per-callback ratio = duration ratio / callback-count ratio`.

The existing calibration workloads, fresh fixtures, actors/rain, routes/reversals,
accepted edits/storage, 1280×720 resolution, radii, workers, 60 Hz ticks, admission
caps, probe switching, collision safety and gameplay are unchanged. Preparation,
gameplay/edit settlement and retirement retain separate native operation evidence.
Preparation/retirement are outside the per-trial estimand; their evidence and
failures remain in the report and are not waived by this observation.

Every complete interval and final callback remains. Seven existing bins retain
six main sections plus all terminal/acknowledgement intervals. An interval belongs
wholly to its ending callback; rows are never trimmed, split or reweighted.
The full diagnostic window includes callback/CSV/UI costs, callback-ledger tails,
native closure bookkeeping, writer join/flush and scenario report construction.
New bounded closure/drain timestamps show the native phase has closed before the
writer drain and nonoverlapping dose. Closure bookkeeping finishes after the
native phase closes; it is not a substitute for native operation-row timestamps.
Writer drain, dose, callback and file-I/O brackets are nested descriptions of the
same complete wall window, never costs to add to it.

The exact additive *wall-window partition* is main interval sum + terminal interval
sum + setup/final-callback tail + finalization. Callback wall costs, acknowledgement
marker span, writer drain and dose are separately retained overlapping brackets.
The acknowledgement marker starts after the first terminal callback; its literal
span differs from the sum of terminal intervals. Neither is assumed causal cost.

Combined summary hashing/serialization/writes/flushes and final UI retain the
existing external `report-finalization.json`. This one-time cost occurs after the
repeat windows, has no matched control and is never allocated to individual
repeats. Its own record write/process exit/deferred renderer work remain explicitly
excluded. Failed final writes still fail saved evidence; the experimental result
cannot turn a missing final record into a successful complete report.

## Predeclared experimental observations and guards

Two reference and two closure repeats form a minimum/maximum duration-ratio
envelope. It is not a confidence interval. Exact integer comparisons classify a
lower bound ≥1% as `above_limit`; a nonnegative envelope wholly below 1% as
`below_limit`. Threshold overlap or apparent speedup stays inconclusive. Classification
is a fixed-work closure observation, not an overhead pass/fail.

Same-mode complete durations and matching *main section durations* must each
have symmetric variation below 1%. These checks retain complete-window instability
and main-route drift even when the total is unchanged. Count drift remains visible
but cannot cancel a closure-duration observation. No per-callback repeat stability
rule is adopted for this separate duration estimand; existing rules stay unchanged.

For each same-mode pair, terminal uncertainty is the larger absolute change of
terminal-interval sum and literal acknowledgement-marker span, divided by mean
complete-trial duration. These overlapping spans are not summed. Signed deltas,
microseconds, counts and complete-window variation remain visible. This observed
range is neither an estimated noise distribution nor proof of endpoint causation.
An uncertainty reaching 1% of the complete trial remains inconclusive. This is
an experimental observation guard, not replacement qualification policy.

A null declared dose can produce `null_observed`; a complete, stable, valid known
positive below/at/above-limit duration can produce `sensitivity_observed`. Neither
status qualifies hardware or changes a current calibration verdict. Invalid order,
short/incomplete/stalled work, missing terminal/phase/window accounting, failed
workload/operation/evidence, smoke or I/O failure remains inconclusive. Raw duration
classification stays visible for guard failures with valid accounting. Missing
measurements have explicit unavailable status and null values, never passing zeros.

## Predeclared software controls and bounds

The matching pinned editor drives the production assessor with the established
precision clocks. The common ordinary closure becomes 1,055 µs, making the normal
complete reference exactly 30,021,300 µs; no target timing is used. Counts are 250
per main section plus four terminal callbacks. Final-callback costs still vary
with count; they are retained exactly. All controls declare 1,800 ticks but model
clocks only; they do not execute the corresponding terrain/actor work. Separate
existing release smoke executes the real calibration machinery.

Twenty-two controls per H1/H2 workload are predeclared:

| Control | Injected observation / expected experimental status |
| --- | --- |
| Null | Zero declared/actual dose; zero effect; `null_observed` |
| Below | 150,106 µs closure; below 1%; `sensitivity_observed` |
| At | 300,213 µs closure; exactly 1%; above-limit boundary; `sensitivity_observed` |
| Above | 600,000 µs closure; above 1%; `sensitivity_observed` |
| Threshold overlap | Requested 299,000 µs; actual 299,000/301,000 µs; inconclusive |
| Endpoint redistribution | Move 500 µs from last main section to first terminal interval in second same-mode repeats; total unchanged; sensitivity observed |
| Acknowledgement duration | Add 500 µs to last terminal interval in second repeats; complete duration and literal span increase; sensitivity observed |
| Count masking / unequal reference counts | Add five callbacks per main section to closure pair / second reference; duration retains final-callback cost; sensitivity observed |
| Incomplete / missing / reordered / stalled | Their workload/order/completion guards fail; inconclusive |
| Failed actor workload / failed operation | Actor deficit / real 751 µs operation evaluator against unchanged 750 µs limit; inconclusive |
| Unavailable terminal / missing wall window | Observation unavailable/null; inconclusive |
| I/O failure / overlapping dose / invalid phase sequence | Evidence/scope guards fail; inconclusive |
| Complete-window drift | Add 450,000 µs ordinary closure to second reference; complete duration instability remains inconclusive |
| Main-route drift | Move 100,000 µs between two main sections in second reference with total unchanged; inconclusive |

The count-masking duration increases 599,995 µs after retaining the changed last
callback cost, while time per callback remains below 1%. Callback count cannot
conceal this above-limit duration observation. Existing calibration still rejects
this control. Existing endpoint and acknowledgement terminal guards remain
inconclusive in the old assessor; only the separate experimental observation uses
complete-trial terminal units.

Storage is capped at 44 control reports, 176 streamed raw CSV files totaling
64 MiB, 3 MiB control JSON and a 60-second clock-command timeout. Runtime keeps
four observations, two pairs and six main section values per workload, reusing
seven existing aggregate bins; no new per-frame array, queue, worker or disk path.
Invalid complete windows beyond ten minutes or two million callbacks are unavailable,
without changing runtime workload bounds or hiding their existing failures.

`tools/qa/fixed_work.py` independently uses exact rational arithmetic, closed-form
clock/count/cost sums and the streamed established precision reader. It checks
classifications, additive/nonadditive scope, all phase/dose/ack clocks, raw final
rows, declared faults, unavailable/null semantics and saved production results.
It also reconciles the unchanged calibration outputs. Existing sixteen method,
26 route and 28 endpoint control expectations remain required. Actual release
calibration smoke independently reconciles the new result plus the external
combined finalization, alongside existing native/frame/edit evidence.

## Meaning and remaining uncertainty

Fixed-work closure sensitivity concerns full-trial wall duration. Render callback
throughput and time per callback concern counts and pacing. Per-frame CPU/GPU
critical-path probe sensitivity concerns causal frame-service effects and overlap.
Shared instrumentation overhead needs a sufficient uninstrumented control. These
are distinct quantities: a duration ratio establishes neither per-frame probe cost
nor total diagnostic overhead. Their causal estimates remain null; hardware noise
is uncalibrated. Cloud/headless success cannot qualify HD 620.

## Executed cloud verification

Implementation `34a92122704faa9953036dd4aee4995ed6e9f6c9` passed
[CI 37707455386](https://github.com/dponcho/voxel-survival-game/actions/runs/37707455386),
completed `2026-10-08T00:33:11Z`. All three jobs passed: 52 Python regressions,
five native sanitizer suites, exact editor/debug/release requalification,
matching-engine import/export, all 44 fixed-work controls, the independent
saved-row oracle, existing sixteen method/26 route/28 endpoint controls, real
runtime/profile/calibration smoke, DLL audit and two fresh offline extractions.
No engine was installed, compiled or run locally.

Independent downloaded verification reconciles all 176 modeled phases and
264,852 saved rows. The control JSON is 1,765,195 bytes; raw CSV totals
15,133,996 bytes, within the predeclared bounds. Exact-at-1%, null, endpoint,
acknowledgement, unequal-count, complete/main drift and every invalid guard retain
their declared outcomes. The above-limit duration remains visible in the count-
masking case even though time per callback is below 1%. Existing control
expectations and production assessments are unchanged.

The first attempt, [CI 37684349942](https://github.com/dponcho/voxel-survival-game/actions/runs/37684349942),
correctly failed formal checks: its new true-zero-dose fixture also called the
legacy known-positive assessor, which tried to cast a null dose timestamp. The
corrected test wrapper omits only that optional legacy assessment for the new
zero-dose control. It changes neither production legacy code nor any established
null/positive control expectation. The successful candidate contains this fix.

All ten actual cloud smoke folders complete without integration failures.
Independent review reconciles 98 scenarios, 284 native phases, 37,330 operation
rows, 12,871 frame rows and 94 edit events. The shortened real calibration retains
1,173 raw frames, explicit unavailable later bins and inconclusive legacy and
experimental decisions. Its combined finalization stays external; it is not
allocated to the repeats. Both 16³ profiles retain their coverage and H2 edit-
latency failures; target upload/phase-budget failures remain unwaived. Hosted
OpenGL readback is unavailable. These results qualify no target profile.

The verified [Windows player 11520043769](https://github.com/dponcho/voxel-survival-game/actions/runs/37707455386/artifacts/11520043769)
exports build `23a5615f8f29cffa739da8cb8447d26c2e43bcaf`, with the same Git tree
as the implementation. Portable ZIP SHA-256:
`7d0c3d08f68fa2b9c7f4ab5ba7b7fa91d1f74fd321d155b0af14a83b4f2e56fd`.
Archive, x64 PE, all PCK entry checksums, build identities, native pins, saved
evidence and offline self-tests independently verify; full provenance is in
[M1_EVIDENCE.md](M1_EVIDENCE.md) and the
[cloud verification record](evidence/m1-fixed-work-cloud-2026-10-08.json).
No new target-side run, download or full matrix is requested for this correction.
