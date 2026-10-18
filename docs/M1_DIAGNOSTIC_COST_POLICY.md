# Diagnostic cost decision — October 17, 2026

**V2 cost method adopted; route implementation and qualification pending.**
Policy `m1-shipping-diagnostics-2`; proposed method `m1-shipping-cpu-cycles-1`.
This is the explicit measurement-policy decision required by the completed
[inconclusive pilot](M1_SHIPPING_DIAGNOSTICS.md#result). M1 remains blocked.

The counter-only prerequisite is now [cloud-verified with matching Windows
binaries and a portable candidate](M1_CPU_CYCLE_CAPABILITY.md) in CI
`39073452514`. The v2 inventory, in-route cycle dose, interval reader and finite
route pilot remain unimplemented; the decision and all limits below are unchanged.

## Decision and requirement change

Apply the existing **below-1% upper-bound rule to incremental whole-process
CPU-cycle demand** of the declared optional shipping inventory. Keep complete
elapsed lifecycle duration, frame capacity/pacing, edits, coverage/readiness,
resources and synchronous operation limits as separate required observations.
An elapsed-time result near zero cannot establish a CPU-cost pass.

This explicitly replaces complete elapsed duration as the denominator of the
shipping optional-cost gate. It changes the measured quantity, not the numerical
1% limit, supported world, worker count or operational limits. The scope remains
incremental optional inventory conditional on the declared common observers.
It does not establish total instrumentation overhead, CPU service seconds,
GPU cost, energy use or physical presentation. No individual component may be
called qualified merely because its files have verified integrity.

The existing v1 inventory, method, package and failed CI are historical evidence.
Do not edit their versions, hashes, measurements or verdicts. Implement v2 under
new identifiers and an updated executable inventory only in a later code task.

## Why this choice

The v1 positive trials' hash-work elapsed brackets totalled 1.605522 / 1.602053 s,
with native update/digest witnesses. No CPU-cycle or CPU-service totals were
captured. The complete fixed-60-Hz routes still took about 77.45 / 77.76 s. Two
operation failures also invalidate those controls. Repeating the same elapsed estimator
cannot remove the mechanism by which pacing wait absorbs work. These are
descriptive observations, not a retrospective CPU estimate.

Windows [QueryProcessCycleTime][process-cycles] reports user/kernel CPU cycles
across the process's threads. [QueryThreadCycleTime][thread-cycles] supplies the
same kind of observation for the dose thread. They support a whole-process cost
comparison and an independent witness of injected execution. Microsoft warns
against converting thread cycle counts to elapsed time because CPU timer
behaviour varies. Keep raw cycles and compare only within one exact-build,
same-machine sequence. CPU frequency/thermal/scheduling effects can still make
that sequence inconclusive; a counter is not a guarantee of 1% sensitivity.

[GetProcessTimes][process-times] may be retained as a separate user+kernel service
time observation. Its 100 ns representation is not an asserted measurement
resolution. Do not derive seconds from cycles, divide by nominal GHz, replace
an unavailable counter with elapsed time, or pool cloud/target cycle counts.

| Alternative | Decision |
| --- | --- |
| More unchanged elapsed-time repetitions | Reject: they do not remove idle absorption. |
| Raise the 1% limit | Reject: no evidence supports changing the cost allowance. |
| Remove pacing or change simulation speed to force sensitivity | Reject for this increment: it changes the workload being compared. |
| Instrument only the optional function's main-thread wall time | Reject as the whole-cost gate: it misses writer/worker and lifecycle work. |
| Whole-process raw CPU cycles, with elapsed impact reported separately | Adopt prospectively; require observable null/positive controls and the existing finite stop. |

## Scope, boundaries and records

Retain the same bare/shipping/forensic separation and operational safeguards.
Whole-process observations include in-process terrain, renderer and disk workers;
neither per-thread percentages nor overlapping spans are added to that total.
The diagnostic counter reader and correctness observers are common external
measurement work, disclosed in every arm. Driver/GPU execution and work outside
the process remain outside this CPU estimand. Blocking I/O remains visible in
elapsed lifecycle and frame checks even when it consumes few process cycles.

Use the same complete boundary: before optional setup and fixture preparation,
through 4,320 ticks, final edit acknowledgement, native closure, all writer drains,
terrain/preparation retirement, optional summary disposal and complete per-trial
report serialization/flush/close. Keep the five matching sections: preparation,
+X, -X, +Z and lifecycle tail. Do not remove setup/tail CPU cost or normalize by
callback count. Record callbacks, work counts and elapsed sections separately.

Each boundary has ordered native counter reads before/after its common snapshot
work. Retain their lower/upper raw values and enclosing monotonic wall clocks.
For start interval `[s_lo,s_hi]` and end interval `[e_lo,e_hi]`, retain complete
cycle demand `[max(0,e_lo-s_hi), e_hi-s_lo]`. Require ordered, successful,
nondecreasing counters and a positive reference lower bound. Store raw unsigned
64-bit counters as decimal strings so JSON/GDScript floating-point parsing cannot
round them. Readers use exact integer arithmetic. Reuse the same counter bracket
on both sides of each section boundary. Integer midpoint differences must
partition the complete midpoint difference exactly; conservative section interval
endpoints need not sum because their boundary uncertainties are correlated.
Retain that uncertainty rather than treating the midpoint as an exact reading.
Compute a midpoint as `lo + (hi-lo)//2`, avoiding an overflowing endpoint sum.

The per-trial final CPU boundary follows report flush; its own terminal marker
write remains common external work. Record that marker's cycle bracket and
expand the comparison by its conservative off+on cost, as v1 did for elapsed
markers. Do not silently assign an unmeasured marker zero. Final batch reporting
and process launch/exit remain explicitly excluded common harness work.

## Finite method and controls to implement later

The existing conservative repeat-envelope method is retained, with cycles as
its unit and interval arithmetic for boundary uncertainty. For each quartet,
the raw lower bound uses `min(B_lo)/max(A_hi)-1`; the raw upper uses
`max(B_hi)/min(A_lo)-1`. Expand by matching-section repeat drift and terminal
marker cost. For each repeated pair, conservatively bound each absolute section
difference by `max(abs(x_lo-y_hi), abs(x_hi-y_lo))`; sum those five bounds and
divide by the smallest reference complete lower bound. Use the larger off/on
repeat sum. Retain the pooled point estimate and the full bounds separately.
These are empirical conservative repeat ranges, not confidence intervals or
proof against every OS event. No fitted correction or discarded outlier is allowed.

Once counter capability is verified, permit **one** prospective sequence on one
32-cube/one-worker profile: one warm-up, one bare null quartet, one known-positive
bare quartet, then a shipping quartet only if both controls are usable. Maximum
9 / 13 trials, the same world/work/settings and complete boundaries as v1.
It does not authorize an immediate cloud or laptop rerun in this document.
Counter, work, I/O or operational guard failures may abort early: retain the
exact completed prefix and failed/partial trial with an explicit abort reason,
no cost estimate and an inconclusive result. Never pad or retry that sequence.

The positive request becomes `ceil(C_positive_A0 / (50 * 4320))` raw cycles per
real physics tick, fixed before either positive B. Use native SHA work in the
route, retaining update counts/digests, thread-cycle brackets and wall brackets.
The dose includes its positive-only loop/counter work; no observer subtraction
is fitted. Common witness overhead must remain declared. Limit each tick to
512 hash updates and 50 ms enclosing elapsed time; no sleep/yield, terminal-only
substitute, dose adjustment after B1, or extra repetition. A zero request,
unavailable counter, cap hit or incomplete work invalidates the control.
Here `C_positive_A0` is A0's complete midpoint difference, not wall duration.

For each positive B, sum its 4,320 actual injected cycle-demand intervals.
Divide that total conservatively by the complete positive reference demand:
`[dose_lo/max(A_hi), dose_hi/min(A_lo)]`, using A0/A3. Require this interval
to lie **above 1% and at/below 3%**; the requested
target is 2%, with that explicit finite overshoot allowance. Its interval must
overlap the measured positive effect range and that range must have a lower
bound at/above 1%. This replaces v1's wall-microsecond dose request and its
2,000 µs request cap; the elapsed safety cap and fixed work stay intact. If the
SHA granularity cannot meet this band, stop rather than quietly changing it.

The null range must contain zero and have width below 1%. Null and positive
matching-section drift must each be below 1%. Missing work, I/O errors, queue
or resource violations, failed edit/coverage/readiness or operation guards
invalidate a trial. In particular, the two v1 operation failures are not solved
by changing clocks. Positive injection does not waive native operation guards.

After usable controls, shipping upper **below** 1% passes this CPU-cycle gate;
lower **at/above** 1% fails. Overlap, a negative pooled effect, failed controls,
unavailable evidence or unresolved drift is inconclusive. Retain separate
integrity, measurement-validity, cycle-cost and target-performance results.
Elapsed-impact reports retain their raw sections and original v1-style range
as descriptive observations; they cannot override an invalid CPU-cycle control.
All existing target frame/edit/coverage/resource/operation requirements still
apply independently. GPU/deferred work is not certified by either metric.

On inconclusive, stop this sequence and record the unresolved quantity. No
automatic longer run, new injection family, threshold change or profile matrix.
A passing cloud control establishes implementation behaviour only; an eventual
target pilot needs the exact downloaded release and remains subject to review.

## Next bounded implementation and completion

**Implement counter capability only; do not implement/run the new route pilot
in that task.** Add a dedicated proposed `CairnProbe` observation method (not an
existing upstream API) for process/thread cycle counters, availability/error and
paired wall bounds, with optional separately labelled process service time.
Keep these readers out of ordinary per-frame snapshots and operational budget
enforcement. Preserve source pins, workload, saves, inventory IDs and the old v1
entry points. This native change requires a new native source key and matching
editor/debug/release builds in Actions; the old bundle cannot supply the method.

Completion requires exact integer/serialization and failed-call controls,
nondecreasing real counters, and one bounded matching-editor/release capability
smoke with known hash bytes/digest, a labelled wait and a joined short-lived
worker. Retain the worker's thread-cycle witness before it exits and verify that
the enclosing process-cycle interval still covers that work after join; a process
counter that loses terminated writer/worker demand is unusable for this policy.
The smoke is capped at
5 s of fixture execution per binary with a 60 s process timeout and no retry.
Process cycles need not be zero during a main-thread wait because other threads
can run. Do not infer counter resolution or a cycles/seconds conversion from it.
It proves capability/identity, not a below-1% effect or sensitivity. Keep native
sanitizer checks, package/identity checks and existing required integration gates;
produce a portable candidate containing the new method before marking that task
complete. The full v1 pilot is historical and is not a required rerun for this
counter-only change; preserve its implementation/reader checks and evidence.

After capability passes, the separate next task may implement the declared v2
inventory, exact-rational interval reader, controls and finite pilot. If capability
is unavailable or contradictory, stop there with the recorded error. Neither
stage selects a production profile, requests a laptop run now, or qualifies M1.

## Checks of this decision

Documentation links/anchors and unchanged runtime/inventory/evidence identities
were checked. Exact-rational arithmetic checks covered the strict 1% boundary,
an illustrative 2% cycle increase with zero elapsed increase, negative effects,
terminal uncertainty and overlapping counter bounds. They are analytical checks;
no runtime, counter capability, sensitivity or target result is claimed here.

[process-cycles]: https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryprocesscycletime
[thread-cycles]: https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime
[process-times]: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
