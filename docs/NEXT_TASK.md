# Development handoff

Branch: `codex/m1-engine-proof`. Milestone: **M1 blocked; no target profile qualified**.

Completed October 7: **cloud endpoint/last-edit-settlement and callback-count
precision validation**, code `501d572e84cd90480d81c27abb6e27ad34799222`. Read
[M1_ENDPOINT_PRECISION.md](M1_ENDPOINT_PRECISION.md). [CI 37677486748](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748) passed
all three jobs: 42 Python checks, five sanitizer suites, matching-engine checks,
28 new controls with independent exact/raw reconciliation, all sixteen legacy
method and 26 route controls unchanged, existing runtime/profile/smoke checks,
DLL audit and two fresh offline extractions. Independent downloaded review
reconciles 112 modeled phases/168,596 rows plus ten actual smoke folders,
98 scenarios and 284 native phases. All failures/qualification limits remain.

Current [Windows player 11508552310](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748/artifacts/11508552310) expires
`2026-11-06T20:08:54Z`. Exact exported merge/build ID:
`c1c4f87de6268044ddc4a61955f3fa0556643d2d`. Portable `Cairn-windows-x86_64.zip` SHA-256:
`64a875d6a82c76c27e0953170e5e1432abaeac742c874f45013eafd46e642072`. Native key remains
`11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`. Archive/PE/PCK/identity/raw checks pass;
full provenance is in [M1_EVIDENCE.md](M1_EVIDENCE.md). This candidate adds cloud
controls; no new target-side run or download is required now.

The precision gap is concrete: a tiny terminal contribution can violate the
unweighted terminal repeat guard, while increased callback count can conceal
known added closure duration in time per callback. All terminal rows, complete-
window costs, final callbacks, writer drain, file-I/O and phase boundaries remain.
The production known-positive, failed-workload/upload, missing/unavailable, stalled,
unstable and I/O verdicts are preserved. The 1% threshold is unchanged. These
software controls characterize the current instrument; they do not calibrate
hardware noise, per-frame CPU/GPU sensitivity or shared total overhead.

## Earlier implementation and target reviews

Completed October 6: matched H1/H2 frontier-cost comparison. The title offers
**Compare heavy-route probe cost (~7 min + loading)**: the existing three-minute
warm-up, then separate H1 and H2 off/on/on/off quartets, each exactly 1,800 fixed
60 Hz ticks. Fresh heavy fixtures, actors/rain, routes/camera turns, edits/storage,
resolution, radii, workers, collision safeguards and native admission caps match.
The full baseline/matrix and four-minute heavy qualification routes remain.
Read [M1_HEAVY_DIAGNOSTIC_AB.md](M1_HEAVY_DIAGNOSTIC_AB.md).

Only the native frontier scan and analytic/shader-model ledger switch off.
Dispatch counters prove zero calls off and one per measured callback on. Disabled
coverage is explicitly unavailable with null minima/exposed counts. Both modes
retain native operation/edit tracing, collision timers, renderer queries, detailed
CSV/UI, bounded command fingerprints and proxy storage. Schema 6 separately
reconciles switched/shared complete-callback costs, final callbacks, phase closure,
writer drain and combined report finalization. The original 1% threshold and
stability rules remain; incomplete, stalled, unstable or failed comparisons stay
inconclusive. Shared instrumentation has no uninstrumented control, so a switched
probe pass cannot qualify total diagnostic overhead. Its causal estimate stays null.

Earlier runtime calibration code: `84de20f35853ec79d658660ac1418fc82bc47a58`.
The new supplementary route-matched null/closure experiment is implemented;
read [M1_ROUTE_CALIBRATION.md](M1_ROUTE_CALIBRATION.md). It retains all four
frontier-off controls, shared instrumentation, exact heavy gameplay contracts,
seven bounded route/terminal bins and separately timed closure delay. Its results
cannot replace legacy classifications, establish per-frame probe cost or qualify
shared total overhead.

[CI 37556502450](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450) passed all three jobs October 7 UTC, completed
`2026-10-07T01:35:20Z`: 33 Python regressions, five native sanitizer suites,
editor/debug/release registration checks, 26 new software controls and independent
oracle, all sixteen legacy method controls unchanged, existing matching-editor/
runtime/evaluator checks, all four profiles, streaming/collision/edit/eviction/
cancellation, startup/heavy smoke, actual calibration release smoke and independent
saved-report reconciliation, DLL audit and two fresh offline extractions.
Two earlier attempts failed only final fractional-mean serialization equality;
the corrected reader preserves exact integer totals and the original 1% rules.
No engine was installed, compiled or run locally.

Ten saved smoke folders complete with no integration failures. Independent
downloaded evidence reconciles 98 scenarios, 284
native phases, 37,327 operation rows, 12,873 frame rows and
94 edit events. All three heavy smoke reports retain verified
workload/probe switching and inconclusive overhead. The new shortened calibration
quartets retain explicit unavailable sections and inconclusive hardware precision.
Both 16³ profiles retain H1/H2 analytic coverage and H2 edit-latency failures.
Headless shader-model decisions remain inconclusive; OpenGL readback unavailable.
Target upload/phase-budget failures remain unwaived. Cloud success is not HD 620
qualification.

[Previous calibration player 11454954432](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450/artifacts/11454954432) expires `2026-11-06T01:34:55Z`.
Exact exported merge/build ID: `6d25fe9b8bee88c0c78bed72573706672bd2f16e`; its tree matches
the calibration code. Portable `Cairn-windows-x86_64.zip` SHA-256:
`441ea7d6f556ef6f720d963fdbe51d1cdfc10b70405ecf9000f17efa57279c79`.
Native key remains `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
Downloaded archives/CRCs/checksums, x64 PE/PCK, identities, native registrations
and raw reports reconcile. [Evidence](M1_EVIDENCE.md) retains provenance and
earlier candidates. Target measurements and raw reports stay private.
The earlier frontier comparison belongs to build
`2216a08bc97676d772e41dee57d6c3bac824be54`. The exact-build target
calibration for that earlier candidate was reviewed October 7; its detailed
measurements and raw identity remain private.

The startup investigation and two exact-build HD 620 short repetitions are
complete. The historical stall did not recur; smaller early warm-up hitches
recurred mainly inside the render-signal bracket. Neither shortened N1 route had
a deadline miss. This observes wall-time rendering/wait delay; shader, driver,
background-process cause, CPU service and physical presentation remain unverified.
No further startup reproduction is requested solely for that completed review.
The heavy comparison does not qualify startup instrumentation overhead.

The first exact-build HD 620 matched heavy comparison was reviewed October 6.
It completes with matching fixture/profile/route/actor/edit/storage contracts,
fixed ticks, command fingerprints and probe dispatch. Disabled coverage remains
unavailable. Raw callback partitions, native phase/lifetime operation evidence,
frame histograms/timing blocks, edit events/latencies, file-I/O/finalization and
analytic/renderer-model counts independently reconcile. No evidence-integrity
failure was found. All shortened heavy routes retain zero raw deadline misses;
this does not qualify the required full heavy workloads or physical pacing.

Both switched-cost verdicts remain **inconclusive**: every repeat fails the
existing within-phase stability rule, enabled H2 repeats also fail repeat
stability, and all enabled routes retain coverage failures. One measured H2 upload
also exceeds the individual-operation limit. Preparation/retirement operation
exceedances and a warm-up deadline miss remain separate, unwaived evidence.
Supported desktop conversion-model alarms retain nonzero transmittance; visible
pixels and the underlying readiness/scheduling/driver causes remain unverified.
Shared total overhead remains inconclusive with a null causal estimate. Detailed
target measurements, report identities and raw reports stay private.

The measurement-method investigation now takes precedence over another target
repeat or the coverage correction. The legacy rule requires different five-second
sections of a route to have nearly constant mean frame cost. Synthetic injected
clocks demonstrate that this can reject perfectly repeatable varying routes at
both zero and known above-limit added cost. The independent arithmetic control
and pinned-engine execution are recorded in
[M1_MEASUREMENT_METHOD.md](M1_MEASUREMENT_METHOD.md). These are software controls,
not physical target A/A or a qualification result. Matched private target analysis
also retains between-repeat mismatches; a successor cannot retroactively pass the
existing report. The legacy rule and recorded verdicts remain authoritative.

**Focused target calibration reviewed October 7:** the report matches the
earlier calibration candidate and baseline profile, completes both ordered H1/H2 quartets,
and preserves fixed ticks, fixtures, routes, actors, edits/storage, command
fingerprints, admission caps and disabled probe behavior. Independent raw review
reconciles all frames, native phases/lifetime deltas, callback partitions/final
callbacks, histograms/timing blocks, edit events, dose/drain/finalization and I/O
scope. No evidence-integrity failure was found. Disabled coverage remains
unavailable/null; target details stay private.

Both supplementary decisions remain **inconclusive**. H1 has whole-trial and
matching-main-section drift plus a measured upload-budget failure. H2's raw
complete-window envelope identifies the above-limit closure effect, and its six
main route section pairs satisfy the repeat guard, but its retained terminal/
last-edit-settlement section fails. The H2 observation is useful sensitivity
evidence, not resolved hardware calibration. Preparation/retirement operation
exceedances and warm-up raw deadline misses remain separate, unwaived evidence.
Driver, shader and background-process causation remain unknown. Legacy decisions
and the 1% requirement are unchanged; shared total overhead is still null/
inconclusive. Read [M1_ROUTE_CALIBRATION.md](M1_ROUTE_CALIBRATION.md).

## Next bounded step

**Single next implementation task:** implement a supplementary fixed-work
elapsed/count sensitivity assessor alongside the current calibration assessment.
Use the complete measurement-setup-through-report wall window for matched 1,800-
tick workloads, separately retain callback count/time-per-callback, terminal/
acknowledgement contributions and every phase/I/O cost. Predeclare exact null,
known closure, endpoint redistribution, actual acknowledgement duration, unequal
counts and invalid/failed/stalled controls. Independently prove that count changes
cannot hide the declared closure effect in its duration observation, and that
terminal uncertainty is reported in complete-trial units without trimming rows.
Keep missing precision unavailable/null and storage bounded.

This assessor remains an experiment: all legacy/current saved assessments and the
1% requirement stay authoritative; every qualification flag remains false. Do
not adopt a replacement policy, retroactively pass the target report, relax any
workload/operation/coverage guard or call a fixed-work duration ratio a per-frame
probe cost. Distinguish fixed-work closure sensitivity, render callback throughput,
CPU/GPU critical-path sensitivity and shared instrumentation explicitly. Give the
experimental assessor independent threshold/null/positive/invalid/saved-report
checks and a pinned cloud candidate when runtime code changes. A qualification
policy adoption is a separate decision after those controls are trustworthy.

The observable result is a trustworthy supplementary elapsed/count observation
and bounded uncertainty account; not a qualified profile or total-overhead pass.
Per-frame CPU/GPU dose sensitivity and a sufficient shared-instrumentation control
remain later gaps. Cloud/headless success stays distinct from HD 620 evidence.

**No new target-side action is needed now.** Do not repeat the unchanged
calibration or request another baseline/profile matrix before the proposed bounded
correction and its controls are trustworthy. The current precision controls are complete.

The recurring frontier readiness gap and recorded H2 upload remain separate
workload corrections: use the private alarms for a deterministic cloud boundary
replay, inspect required-region geometry and demand/admission/submission state,
and correct the demonstrated cause. Do not widen fog, weaken coverage, suppress
operation failures or trim samples. Timing instability and shared total overhead
remain unresolved. Startup attribution/review remains complete.

Unresolved M1 gates include pacing, conservative heavy coverage, recorded upload/
terrain limits, unstable flat A/B, total diagnostic overhead, allocation/deferred
renderer accounting, retention, profile comparison and qualification repeats.
Rain remains an M1 proxy defect deferred to M5. No acceptance threshold, world/save
semantics or workload requirement changed; M2 remains gated.

Read `docs/M1_ENDPOINT_PRECISION.md`, `AGENTS.md`, the active M1 roadmap, relevant `ARCHITECTURE.md`, `PERFORMANCE.md`
and `TESTING.md`, `docs/M1_HEAVY_DIAGNOSTIC_AB.md`, `docs/M1_MEASUREMENT_METHOD.md`,
`docs/M1_ROUTE_CALIBRATION.md`, `docs/M1_FOG_FRONTIER.md`,
`docs/M1_OPERATION_DIAGNOSTICS.md`, `docs/M1_STARTUP_ATTRIBUTION.md`, the benchmark/
diagnostics/frontier/evaluation scripts and existing operation/trace tests.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
