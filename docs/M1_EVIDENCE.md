# M1 engine experiment evidence

Current milestone status: **blocked; target not qualified**. The original
[five-run laptop review](M1_TARGET_REVIEW.md) and subsequent private exact-build
reviews retain unresolved gates. The candidates below passed cloud checks;
none qualifies M1.

## Current Windows candidate: cloud endpoint/count precision

The October 7 bounded increment adds 28 cloud-only H1/H2 clock controls using the
production calibration/diagnostic ledgers and evaluator, persisted raw CSV and
independent exact aggregates/streamed reconciliation. It separates endpoint
redistribution, modeled acknowledgement-duration drift, complete-trial
callback-count drift and known closure-cost masking. All terminal rows, final
callbacks, timing blocks, closure/drain/I/O scope and preparation/measurement/
retirement boundaries are retained. The native phase closes before writer drain
and dose; the full diagnostic window still includes both. Actual gameplay,
workloads, probe switching, native/world/save behavior and the 1% rules are
unchanged. Read [M1_ENDPOINT_PRECISION.md](M1_ENDPOINT_PRECISION.md).

[CI 37677486748](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748) passed all three jobs, completed `2026-10-07T20:09:20Z`:
42 Python regressions (nine new precision checks), five native sanitizer suites,
exact cached editor/debug/release requalification, matching-editor import/export,
28 new software controls and independent saved-row oracle, all sixteen legacy
method and 26 route-control expectations unchanged, streaming/collision/edit/
eviction/cancellation, all four profiles, startup/heavy/calibration release smoke,
saved-report reconciliation, DLL audit and two fresh offline extractions. Static
job `112988204336`, native job `112988414246`
and export job `112988817451` all passed. No engine was
installed, compiled or executed locally.

The 928,417-byte saved precision JSON and 112 retained modeled
phases/168,596 raw rows reproduce the independent oracle and saved validation.
Normal known-cost controls resolve; the null case retains a zero raw effect but
fails the existing known-positive dose guard. Endpoint and acknowledgement cases
retain their terminal repeat failures despite a tiny complete-window contribution.
The count-masking case retains a below-limit raw time-per-callback effect and an
inconclusive known-positive decision even though full-window duration increases
above 1%. Failed, incomplete, unavailable, stalled and unstable controls remain
inconclusive. This characterizes precision; it adopts no successor policy, changes
no saved target verdict and qualifies neither per-frame CPU/GPU nor shared total
overhead. Detailed target data remains private.

The earlier [CI 37677134115](https://github.com/dponcho/voxel-survival-game/actions/runs/37677134115)
also passed. Its synthetic lifecycle placed drain after dose and included closure
inside its modeled native phase. The bounded follow-up aligns both with the actual
production harness before candidate verification. Use the corrected candidate
below; the earlier prototype supplied no target qualification.

Independent downloaded review verifies GitHub archive digests, ZIP CRC/path safety,
portable checksum/size, x64 PE, every PCK entry's MD5 against the pinned pack
format, outer/inner/PCK build identity, native pins/template hashes and
8 native/game/offline self-test reports. All ten actual smoke folders complete
with no integration failures and qualification false: 98 scenarios,
284 native phases, 37,306 operation rows, 12,868 frame rows
and 94 edit events. Phase counters/bytes/maxima, previous/final callbacks,
full/partial blocks, writer drain and combined finalization reconcile. Actual
calibration saved reconciliation retains 1,171 heavy frame rows,
unavailable later sections and inconclusive hardware precision. Both 16³ profiles
retain analytic coverage and H2 edit-latency failures; all heavy smoke overhead
verdicts stay inconclusive. OpenGL readback remains unavailable. Previous target
upload/phase-budget failures remain unwaived. Cloud success is not HD 620 qualification.

[Windows player 11508552310](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748/artifacts/11508552310) expires `2026-11-06T20:08:54Z`.
[Export evidence 11507753214](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748/artifacts/11507753214) and
[native evidence 11508366174](https://github.com/dponcho/voxel-survival-game/actions/runs/37677486748/artifacts/11508366174) preserve raw cloud provenance.
Symbols remain separate and were not downloaded. Code `501d572e84cd90480d81c27abb6e27ad34799222` and exported
merge/build `c1c4f87de6268044ddc4a61955f3fa0556643d2d` have identical Git trees; native inputs are unchanged.

| Identity | Verified value |
| --- | --- |
| Precision code commit | `501d572e84cd90480d81c27abb6e27ad34799222` |
| Exported merge / build ID | `c1c4f87de6268044ddc4a61955f3fa0556643d2d` |
| Native key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Portable ZIP SHA-256 | `64a875d6a82c76c27e0953170e5e1432abaeac742c874f45013eafd46e642072` |
| Portable ZIP bytes | `30026666` |
| Outer player archive SHA-256 | `74fa9235626e35bbe1b6735a4bd9ad9e9e045c16804433014a243d6f6e4443c3` |
| Executable SHA-256 | `9fc689a2a78e75b6ee846d307925051d882fa417beb23b90af45636fe33fac35` |
| PCK SHA-256 | `bd98cf6b42ea82c70db539996da853d61dae34f8f661b6aad4a7d5524bccc073` |
| Export evidence ZIP SHA-256 | `89cbf80427d067433cf8067dc9501cb30ab6c8e0483a660b074d5723f38b9312` |
| Native evidence ZIP SHA-256 | `8b28408be9e6f803e49412209547a5bf52449818f08b6ba93a5c7b04baa67bb1` |

**No new target check is needed for this cloud-only increment.** The next bounded
correction is supplementary fixed-work elapsed/count sensitivity, with independent
controls and all existing verdicts authoritative. No target repeat or full matrix
is requested until the proposed instrument is trustworthy. M1 remains blocked.

## Previous Windows candidate: supplementary route-matched calibration

The October 7 UTC increment adds **Calibrate heavy-route measurements (~7 min +
loading)**. Each actual H1/H2 quartet is reference/closure/closure/reference,
using the same heavy fixtures, route, actors/rain, edits/storage, resolution,
radii, fixed ticks, workers, native admission caps and safety behavior. All four
repeats keep the frontier probe off and shared instrumentation on. Disabled
coverage remains unavailable/null. The positive control yields a requested
600,000 µs closure delay after gameplay/edit settlement, native phase closure
and full writer drain; actual delay and overshoot are retained inside the complete
trial window. Seven bounded aggregate sections retain terminal/acknowledgement
rows and reconcile to raw CSV. No new queue, worker, world/save or native semantics.

This tests repeatability and sensitivity to added closure wall time. It does not
calibrate per-frame CPU/GPU critical-path effects, establish frontier-probe cost
or qualify shared total overhead. The minimal harness brackets are separately
scoped observations, with no causal overhead estimate. The supplementary
conservative envelope retains the 1% requirement; it never replaces legacy
classifications or stability rules. No target profile is qualified. Read
[M1_ROUTE_CALIBRATION.md](M1_ROUTE_CALIBRATION.md).

Code `84de20f35853ec79d658660ac1418fc82bc47a58` is exported in synthetic merge/
build `6d25fe9b8bee88c0c78bed72573706672bd2f16e`; Git trees match exactly.
[CI 37556502450](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450) passed all three jobs October 7 UTC, completed
`2026-10-07T01:35:20Z`. Static job `112585407016` passed 33 Python regressions and
five native sanitizer suites. Native job `112585512324` reused the exact cache
and independently requalified editor/debug/release registrations. Export job
`112585759059` passed matching-editor import, 26 new clock controls and the
independent exact-rational oracle, actual calibration preparation/route/tick-end/
zero-dispatch observations, existing runtime/evaluation checks, streaming/
collision/edit/eviction/cancellation, all four profiles, startup smoke, debug/
release heavy smoke, actual release calibration, saved CSV reconciliation, DLL
audit and two fresh offline extractions (including a space/Unicode path).
No engine was installed, compiled or run locally.

The 26 controls cover H1/H2 stationary and perfectly repeated varying routes,
incomplete/reordered/stalled/failed workloads, matching-section drift, unavailable
sections, contract mismatch, missing/overlapping doses, shortened smoke and I/O
failure. They use hypothetical eligible workload contracts and modeled clocks,
rather than executing thirty-second terrain/actor routes. The 711,422-byte
saved report reproduces the independent oracle. Both valid modeled shapes resolve
the known above-limit closure control; invalid cases remain inconclusive.
All sixteen earlier legacy method controls still pass their declared expectations,
including the varying-route counterexample that leaves the legacy general method
unvalidated. No existing report is retroactively passed.

Attempts [37555721834](https://github.com/dponcho/voxel-survival-game/actions/runs/37555721834)
and [37556123803](https://github.com/dponcho/voxel-survival-game/actions/runs/37556123803)
completed the controls and actual release calibration, then failed independent
saved-report reconciliation because it compared JSON-rounded fractional means
with exact floating equality. The bounded correction accepts serialization
roundoff only (relative 1e-12, absolute 1e-9 µs), keeps integer totals exact and
rejects meaningful mean alteration. The first failed-run raw CSV also reconciles
through the corrected reader. Neither failed run supplies a verified player
candidate; no 1% threshold or stability rule was weakened.

Independent downloaded-archive review verifies all three digests against GitHub,
ZIP CRCs/path safety, portable checksum/size, inner/outer build identity, x64 PE/
PCK, pinned native manifest/template hashes and eight native/game/offline self-test
reports. All ten raw smoke folders complete with qualification false and no
integration failures: 98 scenarios, 284 native
phases, 37,327 operation rows, 12,873 frame rows and
94 edit events. Callback partitions and final callbacks, full/partial
timing blocks, native phase/lifetime counters, bytes/maxima, phase boundaries,
writer drain, closure and combined finalization/file-I/O evidence reconcile.

All three existing heavy smoke reports still verify matched workload equivalence
and off/on switching, and remain inconclusive. The actual calibration release
smoke reconciles 1,174 heavy frame rows, both
quartets, requested/actual delay scope, command schedules and native admission
caps. Short routes and unavailable later route sections remain inconclusive;
cloud smoke does not calibrate target noise. Flat off CSV/tracing remains
explicitly disabled/unavailable. Both 16³ profiles retain H1/H2 analytic coverage
failures and H2 edit-latency failures. Headless shader-model decisions remain
inconclusive; OpenGL readback is unavailable. Private target upload/phase-budget
failures remain unwaived. Cloud success is not HD 620 qualification.

Download [Windows player 11454954432](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450/artifacts/11454954432), expiry `2026-11-06T01:34:55Z`.
Separate [export evidence 11455403992](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450/artifacts/11455403992),
[native evidence 11455027996](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450/artifacts/11455027996) and [symbols 11454904506](https://github.com/dponcho/voxel-survival-game/actions/runs/37556502450/artifacts/11454904506)
retain provenance. Symbols were not downloaded for verification.

| Identity | Verified value |
| --- | --- |
| Calibration code commit | `84de20f35853ec79d658660ac1418fc82bc47a58` |
| Exported merge / game build ID | `6d25fe9b8bee88c0c78bed72573706672bd2f16e` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `6cebecc8f21856272167ccf1ebded45e219140e301c9c2835d807388f10a8d69` |
| Portable ZIP SHA-256 | `441ea7d6f556ef6f720d963fdbe51d1cdfc10b70405ecf9000f17efa57279c79` |
| Portable ZIP bytes | `30020482` |
| Executable SHA-256 | `9fc689a2a78e75b6ee846d307925051d882fa417beb23b90af45636fe33fac35` |
| PCK SHA-256 | `cd0151fc1bbe8324bf35e5afefc26465a21b758c0f7bdceec6c24b2cf16e4ab3` |
| Export evidence ZIP SHA-256 | `54711ce7a1acac2501520cf9faf073a32aa93f1bc2035b5de83a7c46606227b4` |
| Native evidence ZIP SHA-256 | `141ee754db74df5d7c54a606e01b9939abea41de652a60d049758e796ceac142` |

## Exact-build target calibration review — October 7

The focused baseline calibration was supplied and reviewed. Build, executable/
PCK identity, profile and both ordered workload quartets match the candidate.
Fixed simulation/actor activity, route/command evidence, edits/storage, radii,
worker count, native admission caps and zero switched dispatches reconcile.
Coverage remains unavailable/null. Independent streamed raw review reconciles
frame clocks/order, histograms/percentiles/deadline misses, previous/final
callbacks, timing blocks, native phase counters/bytes/maxima/lifetime deltas,
edit events and dose/drain/report-finalization scope. No evidence-integrity
failure was found. Detailed measurements and raw report identity remain private.

Both supplementary outcomes stay **inconclusive**. H1 has whole-trial and
matching-main-section repeat drift, and a measured individual-upload failure.
H2's raw complete-window envelope identifies the known above-limit closure cost;
its six main route section pairs satisfy the repeat guard. Its small terminal/
last-edit-settlement section still fails repeatability, so it does not resolve
hardware calibration. Every terminal row and final callback remains included.
The scoped preparation/retirement upload/deletion exceedances and warm-up raw
deadline misses remain separate evidence. Causation by shader, driver, OS or
background process is unverified.

These results support a bounded cloud endpoint/acknowledgement precision
investigation before another target request. Preserve all current verdicts and
the 1% requirement. Do not trim the terminal bucket or adopt a new classifier to
make this report pass. Per-frame sensitivity, total shared diagnostics and
existing enabled-frontier/operation failures remain unresolved. No new laptop
repeat or full matrix is requested now. See [NEXT_TASK.md](NEXT_TASK.md).
This is a documentation-only review; the verified player above is unchanged.
M1 remains blocked; no profile qualified.

## Previous Windows candidate: measurement-method controls

The October 6 validation adds cloud-only injected-clock controls through the
production diagnostic ledger and heavy evaluator, plus a closed-form independent
Python oracle. Sixteen cases cover both H1/H2 contracts, stationary/varying routes,
null/nominal +0.5%/+2% frame intervals and added closure cost. They retain callback
partitions, final callbacks, setup/closure/drain scope and partial blocks. These
are hypothetical eligible contracts and modeled clocks, not executed terrain,
physical A/A, target noise calibration or shared instrumentation qualification.

Stationary null/below-limit controls pass and above-limit/closure controls fail.
Every perfectly repeatable varying control is inconclusive: the unchanged
within-phase rule tests stationarity across different route sections. This
counterexample leaves the general varying-heavy method **unvalidated** while
confirming its arithmetic and declared classifications. No workload or acceptance
rule changed. Existing target verdicts remain authoritative. Read
[M1_MEASUREMENT_METHOD.md](M1_MEASUREMENT_METHOD.md).

Code `eaa86172ae4c5fadf19e9241b9c4f700ff841b70` is exported in synthetic merge
`c89ee2f6562d4c89c7bf8746d9f8693f1ebba812`; Git trees match exactly.
[CI 37529525432](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432)
passed all three jobs October 6, completed 21:01 UTC. Static job `112495026269`
passed 25 Python regressions and five native sanitizer suites. Native job
`112495196764` independently requalified the exact cached editor/debug/release
registrations; native inputs are unchanged. Windows job `112495961162` passed
matching-editor import, all sixteen controls and independent oracle, all existing
runtime/evaluator/saved-report checks, debug/release heavy smoke, streaming/
collision/edit/eviction/cancellation, four profiles, startup smoke, DLL audit and
two fresh offline extractions (including space/Unicode). No engine installed,
compiled or ran locally.

The first attempt [37527915469](https://github.com/dponcho/voxel-survival-game/actions/runs/37527915469)
failed on pinned-engine typed-array construction before producing controls.
Direct typed initialization fixed it; the new clock-only check timeout is 60
seconds. The failed run supplies no measurement verdict or candidate qualification.

Independent downloaded-file review verifies all three artifact digests against
GitHub, ZIP CRCs/path safety, portable SHA/size, inner/outer build identity, x64 PE/
PCK, native manifest/template hashes and eight native/game/offline self-test
reports. The 258,381-byte saved control report (64 modeled phases) reproduces the
saved independent oracle exactly. All nine raw smoke folders complete with
qualification false and no integration failures: 89 scenarios, 257 native phases,
34,028 operation rows, 11,525 frame rows and 78 edit events. Raw callback partitions
and final callbacks, full/partial timing blocks, native phase operation counters/
bytes/maxima/lifetime deltas, final report timing and heavy contracts/switching
reconcile. Flat off CSV/tracing remains explicitly disabled and unavailable.
Heavy off coverage remains unavailable/null with zero dispatches; heavy on
retains one dispatch per measured callback. All three shortened heavy quartets
remain inconclusive. Both 16³ profiles retain H1/H2 analytic coverage failures
and H2 edit-latency failures. Headless shader-model decisions remain inconclusive;
OpenGL readback is unavailable. Earlier private target upload/phase-budget failures
remain unwaived. Cloud success is not HD 620 qualification.

Download [Windows player 11444855103](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432/artifacts/11444855103),
expiry November 5 at 21:01 UTC. Separate
[export evidence 11443763979](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432/artifacts/11443763979),
[native evidence 11443308611](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432/artifacts/11443308611)
and [symbols 11444830206](https://github.com/dponcho/voxel-survival-game/actions/runs/37529525432/artifacts/11444830206)
retain provenance. Symbols were not downloaded for verification.

| Identity | Verified value |
| --- | --- |
| Validation code commit | `eaa86172ae4c5fadf19e9241b9c4f700ff841b70` |
| Exported merge / game build ID | `c89ee2f6562d4c89c7bf8746d9f8693f1ebba812` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `95859821e26ee51600c282bd6fccad7dc7fef5b5617c1ae5ccb265174bf80fd6` |
| Portable ZIP SHA-256 | `e2cb15fd4319b2cebc59bdaefefdc947d31fb35edf16b80f071827f51dd82c21` |
| Portable ZIP bytes | `30005765` |
| Executable SHA-256 | `9fc689a2a78e75b6ee846d307925051d882fa417beb23b90af45636fe33fac35` |
| PCK SHA-256 | `9ed6fbcb291b68ece1d348036077659b8886e1a803ff303bf5122ace500fe2b3` |
| Export evidence ZIP SHA-256 | `44010534cb062147d58ec8d722199e4547073b823145108a6de0a0ba2ce68637` |
| Native evidence ZIP SHA-256 | `2647e80672530c5d4b25eeb475a8e8c64d682968a60f82f7351a51fda5996a9c` |

The target-review entry below concerns the earlier build, not this candidate.
No new laptop run is requested solely for method validation. The next bounded
work is supplementary route-matched calibration with legacy gates preserved;
see [NEXT_TASK.md](NEXT_TASK.md). M1 remains blocked; no target profile qualified.

## Previous Windows candidate: matched heavy-route frontier cost comparison

The October 6 increment adds a separate seven-minute H1/H2 off/on/on/off check
with exact 1,800-tick routes, fresh matching heavy fixtures and bounded workload
contracts/command fingerprints. Off disables the native frontier scan and its
analytic/shader-model ledger; shared operation/edit tracing, CSV/UI/renderer
queries, collision timers, safety and gameplay remain. Disabled coverage retains
unavailable/null values. Schema 6 partitions complete callback wall time into
switched/shared spans and preserves last callbacks, preparation/measurement/
retirement, writer drain and combined finalization/file-I/O evidence. A switched
result cannot certify total shared diagnostic overhead. The 1% threshold, existing
stability rules, qualification workloads and world/save/native inputs remain.
See [measurement semantics and targeted check](M1_HEAVY_DIAGNOSTIC_AB.md).

Implementation `d80aa2514403c0abb88ece4f1b92ebda13c1b256` and bounded saved-verifier/
raw-evidence corrections through `92e69794aa5026baa740e92154b60126ef8a5a0d` are
in exported synthetic merge `2216a08bc97676d772e41dee57d6c3bac824be54`. Its tree
matches the runtime code branch. [CI 37515081002](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002)
passed all three jobs October 6, completed 19:07 UTC. Static job `112446347243`
passed 18 Python regressions and five native sanitizer suites. Native job
`112446482807` reused the exact cache and independently qualified editor/debug/
release registrations. Export job `112446923547` passed matching-editor import,
actual route/fixture/actor/rain/tick-end/switch observation, workload mismatch,
1% boundary/stability/incomplete/failed-evidence classifications, JSON round trips,
saved CSV/phase/lifetime/edit/frontier reconciliation, existing geometry/streaming/
collision/eviction/cancellation, all four profiles, short startup route,
debug/release exports, DLL audit and two fresh offline extractions, including a
space/Unicode path. No engine installation, compilation or execution ran locally.

Earlier attempts caught saved-verifier defects, not a passing measurement:
[CI 37513767685](https://github.com/dponcho/voxel-survival-game/actions/runs/37513767685),
[37514384031](https://github.com/dponcho/voxel-survival-game/actions/runs/37514384031)
and [37514759975](https://github.com/dponcho/voxel-survival-game/actions/runs/37514759975).
Godot JSON numbers decode as floats while array membership/equality uses strict
Variant types. The verifier now normalizes numeric profile values; a round-trip
regression caught the remaining enum-membership mismatch before export. Edit
collection is verified from the setup snapshot plus accepted event counts; the
final tracker is intentionally disabled by normal closure. Regressions retain
that lifecycle. No coverage or operation gate was suppressed.

All nine raw cloud smoke folders complete without integration failures, retain
qualification false and include summary/finalization JSON, frame/operation CSVs
and edit events. An independent downloaded-file audit reconciles 89 scenarios,
257 native phases, 34,041 operation rows, 11,545 frame rows and 78 edit events.
Each of three heavy reports contains 27 preparation/measurement/retirement phases
and both matched quartets: exactly 60 smoke ticks per repeat, corresponding actor
activity, four H2 accepted edits and one storage write, identical contracts/command
fingerprints/checkpoints, zero off scan dispatches and one on dispatch per callback.
Their workload-equivalence and probe-switch verdicts are verified; overhead is
inconclusive because smoke is short. Shared total overhead remains inconclusive
with a null causal estimate. The first release target check was subsequently
reviewed below; its cost verdicts remain inconclusive.

Both 16³ profiles still fail analytic H1/H2 coverage and H2 edit latency; all four
coverage alarms and two latency failures remain in saved reports. Every heavy
headless shader-model verdict is inconclusive, and the optional OpenGL conversion
probe is explicitly unavailable. Prior private target upload/terrain-budget
failures remain unwaived. Green integration checks do not establish target
rendering, physical pacing, diagnostic overhead, startup cause or qualification.

Download [Windows player 11437078383](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002/artifacts/11437078383),
expiry November 5 at 19:06 UTC. Separate
[export evidence 11436784553](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002/artifacts/11436784553),
[native evidence 11436018586](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002/artifacts/11436018586)
and [symbols 11437208486](https://github.com/dponcho/voxel-survival-game/actions/runs/37515081002/artifacts/11437208486)
retain provenance. The downloaded player/export/native archive digests match
GitHub's artifact digests; ZIP CRCs, portable checksum/size, x64 PE/PCK, executable/
pack/report hashes, build IDs, native manifest hashes and eight native/game/offline
self-test reports match. Completed logs and saved reports were read. Symbols
remain a separate artifact and were not downloaded for this verification.

| Identity | Verified value |
| --- | --- |
| Runtime code branch commit | `92e69794aa5026baa740e92154b60126ef8a5a0d` |
| Exported merge / game build ID | `2216a08bc97676d772e41dee57d6c3bac824be54` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `b3612f5d5ef7dd894b6ed0a225e0071e802600cb6e07d21754faf0f98d156f7a` |
| Portable ZIP SHA-256 | `50e5cb6d0e7311fdd4c5ebc265b33fb3950a85332366141a29ddcaa34e41f468` |
| Portable ZIP bytes | `30002026` |
| Executable SHA-256 | `9fc689a2a78e75b6ee846d307925051d882fa417beb23b90af45636fe33fac35` |
| PCK SHA-256 | `22778b435db7ff839e7079969901a9be00fcbdecee0e9918fff8e917ba950c35` |
| Export evidence ZIP SHA-256 | `9147ad92b48a0c63f28f1f2f86a8961ab457cbb781fff48a7cad3d382994ff5f` |
| Native evidence ZIP SHA-256 | `87032cbde78f14fc8766f36833d79c4938804bddded6f41740828a7e2fd2b7d2` |

Startup investigation/report review is complete; its wall spans do not establish
shader, driver or background-process causation. The first baseline-profile target
check has been reviewed below; measurement
integrity verifies while cost/stability/coverage gates remain unresolved. No
additional repeat/full matrix is requested solely for that review. **M1 remains
blocked; no target profile qualified.**
Follow [NEXT_TASK.md](NEXT_TASK.md).

## October 6 first matched heavy-route target review

The actual HD 620 baseline-profile report from build
`2216a08bc97676d772e41dee57d6c3bac824be54` matches the verified executable/PCK
hashes. It completes without integration failures. Both matched quartets preserve
actual fixture/profile settings, route/camera intent, actors/rain, fixed ticks,
accepted edits and storage workload. The off path dispatches no frontier scan
and retains unavailable coverage; the on path dispatches per measured callback,
including final edit settlement. Shared operation/edit/CSV/render/safety evidence
remains enabled.

An independent raw-file audit reconciles callback switched/shared/final totals,
phase and lifetime operation counters/bytes/maxima, native interval boundaries,
frame histograms/percentiles/deadlines, five-second blocks/partial blocks, edit
events/latency bins, acknowledgement frames, proxy storage endpoint and combined
finalization scope. Analytic fog and the independently reconstructed supported
desktop truncating-half projection reproduce the saved counts and worst samples.
There are no missing/drop/overflow/invalid-partition or invalid-GPU findings.
Detailed target measurements, report names/hashes and raw files remain private.

All shortened heavy routes have no raw heavy deadline misses. Both switched-cost
comparisons nevertheless remain **inconclusive**: within-phase timing is unstable,
enabled H2 repetitions also violate repeat stability, every enabled heavy route
fails conservative coverage and one H2 measured upload exceeds its individual
operation limit. Preparation/retirement exceedances and a warm-up deadline miss
remain separately attributed to their phases, without a causal explanation or
waiver. The conversion-only model retains nonzero transmittance for the alarms;
these are conservative regions, not verified visible pixels. Neither a favorable
mean ratio nor passing raw reconciliation establishes the 1% overhead requirement.
Shared total diagnostic overhead remains inconclusive with a null causal estimate.

The report supports measurement integrity and repeatable readiness investigation;
it does not qualify full H1/H2 workloads, pacing, retention or M1. No additional
laptop baseline, heavy repeat or full matrix is requested solely for this review.
Next isolate/correct the existing fog-frontier readiness gap in bounded cloud
replay, preserving all workload/budget/coverage/stability requirements. Follow
[NEXT_TASK.md](NEXT_TASK.md). **M1 remains blocked; no target profile qualified.**

## Previous Windows candidate: bounded startup attribution

The October 4 increment adds script, benchmark physics and render-signal wall
spans during initialization/preparation/warm-up/retirement and the first N1
gameplay intervals. Six groups retain bounded prefixes and maxima; intervals
record overlap, outside-stage time, both phase IDs at transitions and explicit
missing/partial evidence. Asynchronous viewport results retain unknown origin
frames. No timing implies CPU service, GPU completion, presentation or a cause.
See [startup semantics and pinned sources](M1_STARTUP_ATTRIBUTION.md).

The original early 184.252 ms warm-up interval contains less than 1 ms of
preceding diagnostic callback time and no overlapping traced terrain upload or
deletion. A similarly large viewport CPU elapsed result arrives later. Rendering
or waiting is a supported investigation direction; laptop background activity,
shader first use, driver waits and OS scheduling remain unverified alternatives.
This investigation does not waive either recorded slow interval.

The title now offers **Run startup timing check (~20 s + loading)**, a fresh
process with ten-second warm-up and N1 routes. This is a targeted reproduction,
not a full baseline or qualification run. Normal full/matrix durations, CSV
columns, demand, ticks, workload, budgets and world/save versions remain.

Implementation `b5a7e122198b5fea4de251a34d024a19d6d6498f` and JSON-verifier
correction `4df6cc2042f9778350b8ade48b16872c052e7c2a` are in exported synthetic
merge `b7506f9ca2184ee3d59fa5cb1b8fcdd1914182b2`. Its tree matches the code branch.
[CI 37225602689](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689)
passed all three jobs, completed October 4 at 18:54 UTC. Static job `111504496131`
passed 18 Python regressions and five native sanitizer suites. Native job
`111504567249` reused the exact cache and independently qualified editor/debug/
release registrations. Export job `111504725104` passed matching-editor import,
endpoint-sweep/phase/cap/cancellation/JSON regressions, saved interval and
diagnostic CSV reconciliation, existing geometry/frontier/edit checks, all four
profiles, the short startup route, debug/release exports, DLL audit and two fresh
offline extractions, including a space/Unicode path.

The first attempt, [CI 37225288006](https://github.com/dponcho/voxel-survival-game/actions/runs/37225288006),
caught a verifier type mismatch: Godot JSON numbers decode as floats while
dictionary equality requires identical types. Its 273 retained partitions passed
an independent numeric sweep. The corrected verifier compares numeric durations
and explicitly regresses JSON round trips. No measured gate was suppressed.

Six smoke reports complete with no integration failures or startup overflow/
invalid/dropped spans. Downloaded reports independently reconcile 1,632 retained
timing partitions. The short route contains only warm-up/N1. Both 16³ profiles
still record analytic H1/H2 coverage failures; every heavy headless renderer-model
verdict is inconclusive. The optional OpenGL conversion probe remains unavailable.
Headless signal brackets and green logic checks do not establish HD 620 rendering,
startup overhead, the historical stall's cause or target performance.

Download [Windows player 11311923130](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689/artifacts/11311923130),
expiry November 3 at 18:53 UTC. Separate
[export evidence 11312236921](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689/artifacts/11312236921),
[native evidence 11311564370](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689/artifacts/11311564370)
and [symbols 11312232050](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689/artifacts/11312232050)
retain provenance. Downloaded player/export/native archive digests and CRCs,
portable checksum, x86_64 PE, PCK, executable/report hashes, build IDs and native
manifest hashes match. Completed logs and saved smoke/self-test reports were read.

| Identity | Verified value |
| --- | --- |
| Code branch commit | `4df6cc2042f9778350b8ade48b16872c052e7c2a` |
| Exported merge / game build ID | `b7506f9ca2184ee3d59fa5cb1b8fcdd1914182b2` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `023c09ab69fe04a423a1e3001361827af1419ef5cd457570b66124c145ef7836` |
| Portable ZIP SHA-256 | `5d92cdcb885c2243015ae9ef856e4e774f1f6f32271ff999658c1d3d45b40437` |

No local engine installation, compilation or execution ran. No new full target
baseline or matrix is requested solely for this reporting change. All target
upload/coverage, diagnostic overhead, pacing, retention and qualification gates
remain in [the handoff](NEXT_TASK.md). **M1 remains blocked; no profile qualified.**

## October 6 target startup repetitions

Two short startup reports from the current candidate's actual HD 620 executable
and PCK were reviewed. Both complete with no integration failures and preserve
qualification false. Their build identity and binary hashes match the verified
player. Raw frame/diagnostic accounting, native phase/lifetime totals, histogram
metrics, ticks, finalization timing, 585 retained stage partitions and 260 eligible
CSV interval joins reconcile. Both traces stop at 64 N1 intervals, without
overflow, invalid/dropped spans or unmatched render signals.

The historical 184.252 ms stall did not recur. A smaller early warm-up hitch
recurs in both fresh launches, with almost all of its interval inside the
render-signal bracket. Neither shortened prepared N1 route has a raw normal
deadline miss. This observes a recurring early rendering/wait-stage delay;
it does not establish shader compilation, driver waits or background activity
as its cause. Viewport result origins, CPU service time and physical presentation
remain unavailable. The later full-route N1 maxima lie outside the retained
startup-stage window; they retain raw latency evidence only.

No mesh uploads/deletions occur in measured warm-up/N1; some generation/data
queue activity occurs later, separate from the early hitch samples. Preparation
and retirement retain individual-operation budget exceedances and are not
silently relabelled as gameplay. Full callback wall fractions do not establish
causal diagnostic overhead. Detailed target report identities and measurements
remain private. These two ten-second routes do not qualify the full M1 workload,
heavy coverage, pacing, overhead or retention. No additional full baseline or
matrix is requested solely for this review; follow [NEXT_TASK.md](NEXT_TASK.md).

## Previous Windows candidate: separate shader conversion evidence

The October 4 increment adds a separate conversion-only coverage verdict and
actual rendering driver/platform/display identity. It preserves the raw analytic
verdict and every runtime setting/workload/cap. The pinned desktop shader uses
a truncating polyfill, overturning the prior nearest-rounding inference. Complete
baseline H1/H2 replay retains 879 of 896 analytic alarms with nonzero packed
transmittance; the remaining 17 stay inconclusive. Prior reports do not identify
the exact driver. These are conservative region alarms, not target pixel proof.
See [the verified source path and model limits](M1_FOG_FRONTIER.md).

Implementation `d4883032c1c80dc9d59a2cb20550ba3c6156242e` and observed-hosted-error
correction `919dc3b8ff75f58525647c1c3e6d3c99833cf402` are in exported synthetic
merge `a082beed4e7df1c7378050a8a09ee2699cdfd2cd`. Its tree matches the code branch.
[CI 37204596489](https://github.com/dponcho/voxel-survival-game/actions/runs/37204596489)
passed all three jobs on October 4, completed 13:18 UTC. Static job `111443046643`
passed 18 Python regressions, owned-script compile checks and five native
sanitizer suites. Native job `111443100328` reused the exact cache and separately
qualified editor/debug/release registrations. Export job `111443261093` passed
matching-editor import, independent binary16 conversion/boundary/invalid-context
regressions, both saved verdicts' CSV reconciliation, geometry, collision, edits,
eviction/cancellation, all four profiles, debug/release export/self-test, DLL audit
and two fresh offline extractions, including a space/Unicode path.

Five smoke reports complete with no integration failures. The 32³ short cloud
profiles pass analytic coverage; both 16³ profiles retain H1/H2 failures.
Every heavy headless conversion-model verdict is inconclusive with zero supported
model samples; other scenarios record `not_run`. Green logic tests do not erase
recorded performance/coverage gates. The optional canvas probe cannot create a
native OpenGL window on this runner and reports **unavailable** in candidate
metadata. The observed startup error is independently tested; script/shader
defects and unknown failures still block CI. No terrain rendering is claimed.

Download [Windows player 11303699005](https://github.com/dponcho/voxel-survival-game/actions/runs/37204596489/artifacts/11303699005),
expiry November 3 at 13:17 UTC. Separate
[export evidence 11303359843](https://github.com/dponcho/voxel-survival-game/actions/runs/37204596489/artifacts/11303359843),
[native evidence 11304281903](https://github.com/dponcho/voxel-survival-game/actions/runs/37204596489/artifacts/11304281903)
and [symbols 11303279958](https://github.com/dponcho/voxel-survival-game/actions/runs/37204596489/artifacts/11303279958)
retain provenance. Downloaded archives passed SHA-256 and CRC checks; the inner
portable checksum, PE x86_64 header, PCK, executable/report hashes, manifests and
build identity match. Completed logs and saved smoke/self-test reports were read.

| Identity | Verified value |
| --- | --- |
| Code branch commit | `919dc3b8ff75f58525647c1c3e6d3c99833cf402` |
| Exported merge / game build ID | `a082beed4e7df1c7378050a8a09ee2699cdfd2cd` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `a9fd56332702b5d026f3998ae5a5483bf0139cfed90e140ce79ef86785b5dc0f` |
| Portable ZIP SHA-256 | `f092ba31ace018c3ff029e08ea8ddc2267cf8a4233e37a9185ab0cf93999ca8a` |

World/save versions, native inputs, fog, radii, workload and caps are unchanged.
No local engine installation, compilation or execution ran. The startup hitch,
target upload limits, conservative coverage and all outstanding qualification
gates remain. No new target baseline is required solely for this reporting
increment. Heavy diagnostic overhead and HD 620 rendering/performance remain
unverified. The current candidate adds bounded startup attribution; follow
[the handoff](NEXT_TASK.md) for subsequent work.

## Previous Windows candidate: finite shader-matched fog boundary

Implementation `f1fea7bc56dc7aeef4f372e26baada84bbce7132` configures the actual
Environment with Compatibility depth fog: begin 16 m, opaque end 96 m,
density 1, curve 1 and no height fog. The pinned radial smoothstep equation
matches the conservative frontier distance. Reports record the actual settings;
the existing density field is no longer hardcoded. The analytic boundary is
evaluated before shader half packing and does not prove rendered pixel coverage.
See [fog/frontier semantics](M1_FOG_FRONTIER.md). Visual/data demand remains
96/128 m; resolution, routes, ticks, workloads and resource/time caps remain.

[CI 37160455260](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260)
passed all three jobs on 2026-10-03 UTC. Static job `111312633017` passed
12 packaging/cache regressions, Python compile checks and five native sanitizer
suites. Native job `111312696593` reused the exact native cache and independently
requalified editor/debug/release binaries; compilation was skipped. Export job
`111312843050` passed engine import, actual-Environment fog regressions,
independent smoothstep values and before/at/after-96 m crossings, invalid-input
handling, saved-report reconciliation, geometry, edits, collision,
eviction/cancellation, all four streaming profiles, dependency audit and two
fresh offline extractions. The 20 demand cases and four mesh-only halo checks
still pass. Five smoke exports completed with no integration failures; every
accepted N2/H2 edit submitted, with no cancellations, timeouts or pending edits
at closure. Every report records the configured finite fog profile.

The short cloud 32³ smoke runs pass the conservative H1/H2 coverage check.
Both 16³ profiles still fail it: pending regions reach approximately 95.5 m,
inside the 96 m boundary. Those failures remain recorded and prevent scenario
qualification; green integration tests do not erase them. Prior target upload
failures have no new target evidence resolving them. Hosted render smoke says
`not_run`; exact-build HD 620 rendering/performance, moving-frontier readiness,
full heavy diagnostics overhead, retention and qualification repeats remain
unverified. Frame/pacing attribution and A/B remain inconclusive.
**M1 remains blocked; no profile is qualified.**

Download [Windows player 11287845333](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287845333)
and extract its contained portable ZIP. Expiry: 2026-11-02 at 23:10 UTC.
[Export evidence 11287477678](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287477678),
[native evidence 11286619792](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11286619792)
and [symbols 11287422754](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287422754)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `f1fea7bc56dc7aeef4f372e26baada84bbce7132` |
| Exported synthetic merge / game build ID | `c1a71cdf77fe4ee9810eff3573f93460c9c2cc0a` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `bcdeb9f91c476505be7ed785faa8ccd4b66951984bd459e41817ce998ee56058` |
| Contained portable ZIP SHA-256 | `0eb379163e88441d0380b48ede68ecb5510037d2d4a6f80bad387feecfd4d130` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. The synthetic merge includes the implementation
commit. No local engine installation, compilation or execution ran.
Its exact-build 32³/one-worker laptop baseline was subsequently reviewed; detailed
uploaded measurements remain private. Use the current [development handoff](NEXT_TASK.md)
before requesting another full matrix or qualification repeat.

## Previous Windows candidate: world-space demand and meshing halo

Implementation `c1ad85b55359a3e013ef43d017223116617a0bca` covers the full fixed
96 m visual and 128 m data-only envelopes from the actual viewer position.
It replaces a block-snapped demand box that could omit required edge regions.
Meshing data follows every demanded render block plus its existing neighbouring
data-block halo. Bounds are clipped before coordinate narrowing; widened
intermediates and empty-demand handling avoid invalid or phantom requests.
The existing viewer/reference/difference lifecycle, settings, budgets and
save/generator formats remain. Two overlapping patch pairs were consolidated
with identical emitted code; repeat application against pinned source is stable.

[CI 37024767302](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302)
passed all three jobs on 2026-10-02 UTC. Static job `110896469348` passed
12 packaging/cache regressions, Python compile checks and five native sanitizer
suites, including an independent geometric demand/halo oracle. Native job
`110896642681` freshly built and qualified matching editor/debug/release binaries.
Export job `110946829805` passed import/export, native geometry, collision,
border edits, eviction/cancellation, all four profiles, dependency audit and two
fresh offline extractions.

The engine log contains 20 passing world-space demand cases across 32/1, 16/1,
32/2 and 16/2: fractional and negative positions, an exact block boundary and a
clipped world corner. Required and resident render counts match the independent
block-intersection oracle. The fractional pose requires 507 regions at 16³
or 98 at 32³ in the clipped M1 slab, within the unchanged 512-region cap.
Four fresh mesh-only checks prove the full clipped meshing-data halo loads
without a wider data-only viewer hiding omissions. Resident data and retirement
remain within existing caps. Five smoke exports completed with no integration
failures; all accepted N2/H2 edits submitted, with zero cancellations, timeouts
or pending edits at closure. Saved-report reconciliation passed.

Download [Windows player 11242141810](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242141810)
and extract its contained portable ZIP. GitHub reports expiry on 2026-11-01
at 17:25 UTC. [Export evidence 11242421606](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242421606),
[native evidence 11242440353](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242440353)
and [symbols 11242116942](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242116942)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `c1ad85b55359a3e013ef43d017223116617a0bca` |
| Exported synthetic merge / game build ID | `77be48ed0ac431da50f7fd9d267873feee403123` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `4f2627ef0be796e70e2bf1a9bc00a2bb7138d9d3191469354af3eb3c6c83b484` |
| Contained portable ZIP SHA-256 | `0151f42967f371384fb7c77d5763489b001fe77a91720bc9ab4d3ed11c99c374` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. The synthetic merge includes the implementation
commit. No local engine installation, compilation or execution ran.

These are settled demand and cloud correctness checks, not rendered HD 620
coverage or performance qualification. Exponential fog is unchanged; its analytic
model has no finite opaque boundary. Moving-frontier readiness, prior target
upload failures, frame/pacing attribution, full diagnostic overhead, retention
and qualification repeats remained unresolved. The finite-boundary candidate
above supersedes this build. Detailed uploaded target measurements remain private.

## Previous Windows candidate: indexed upload batches

Implementation `1a03f16747fa01563150b8a03f6cf6a219718312` preserves source vertex
reuse within the existing 1,024-triangle upload batches. Triangle order,
normals, UVs, color/AO, tangents, materials and surface/draw counts are retained.
The worker-local remap is bounded; malformed indices or channel layouts fail
admission. Upload and retirement estimates now use actual vertex and index counts,
with conservative tangent reserve and no renderer buffer readback.
A full quad batch estimates 143,360 bytes instead of 208,896 (about 31% less).
This is an input-payload reduction, not a measured target timing improvement.
[Measurement semantics](M1_OPERATION_DIAGNOSTICS.md) describe its limits.
Workloads, settings, budgets and save/generator formats are unchanged.

[CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
passed all three jobs on 2026-10-01 UTC. Static job `110474396180` passed
12 packaging/cache regressions, Python compile checks and four native sanitizer
suites, including remap reconstruction, resets, malformed indices and bounds.
Native job `110474542921` built and independently qualified the matching
editor/debug/release binaries after an exact native-cache miss.
Export job `110528071000` passed native geometry/attribute/winding and
unchanged-surface-count regressions, import/export, debug/release smoke,
all four streaming profiles, collision/edit/eviction/cancellation checks,
dependency audit and two fresh offline extractions.
All five smoke exports completed with no integration failures; every N2/H2
accepted edit submitted, with zero cancellations, timeouts or pending edits at
closure. Saved-report reconciliation passed. No CI check in this run failed.

Download [Windows player 11186079360](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11186079360)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-31
at 18:52 UTC. [Export evidence 11185869587](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185869587),
[native evidence 11185868553](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185868553)
and [symbols 11185219665](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185219665)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `1a03f16747fa01563150b8a03f6cf6a219718312` |
| Exported synthetic merge / game build ID | `25e4501360187b3a6afc56e507ac74f841c788b7` |
| Native source key | `bb20d80d8e527335a7cb2e9a728c0eb1328812fd0650b66dcc494daea121763b` |
| Outer player archive SHA-256 | `c62f2e9217158957a470134a26dff5c678c6e76ce574f42a098987f4d6cf7ea4` |
| Contained portable ZIP SHA-256 | `374fa1830097c6f19894b1e9271b2dd1311ff14b9adf9001eaf9e1e2b92fd4fa` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. No local engine compilation or execution ran.
Cloud/headless checks do not establish rendered HD 620 performance.
The exact-build 32³/one-worker laptop baseline was reviewed privately on
2026-10-02 UTC. Build identity and raw evidence reconciled; accepted edit
submission met its latency gate in that run, with no missing-data movement
stops. Conservative heavy-streaming coverage and isolated upload limits still
failed. Frame/pacing attribution, rendered fog coverage, full diagnostic
overhead, allocation/retention and qualification repeats remain unresolved.
**M1 remains blocked; target not qualified.** That review motivated the
world-space demand correction above. Detailed uploaded measurements remain private.

## Previous Windows candidate: lifecycle correction

Implementation `5ce757dfdce039dea5cfbe1f4ceff76635a272d8` initializes fixture
camera/viewer pose before measurement and allows final accepted N2/H2 edits
their existing bounded acknowledgement window. Those final frames/native costs
stay measured; route commands stop at the original endpoint. Genuine timeouts
and explicit cancellation remain observable. Invalid GPU query values stay in
raw CSV, with validity counts and a separately scoped valid-sample peak.
[Measurement semantics](M1_OPERATION_DIAGNOSTICS.md) describe the limits.
Settings, workloads, formats and thresholds are unchanged.

[CI 36803692007](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007)
passed all three jobs. Static job `110183343579` passed 12 packaging/cache
regressions, Python compile checks and three native sanitizer suites. Native
job `110183424337` reused and requalified the matching binaries. Export job
`110183626534` passed import, native/evaluation/diagnostic/lifecycle tests,
debug/release smoke, all four streaming profiles, dependency audit and two
fresh offline extractions. All five smoke exports reconciled saved evidence;
every N2/H2 accepted edit submitted, with zero cancellations, timeouts or pending
edits at closure. Cloud timings do not establish HD 620 performance.

Download [Windows player 11137310682](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11137310682)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-31
at 02:06 UTC. [Export evidence 11136737690](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11136737690)
and [symbols 11136633094](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11136633094)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `5ce757dfdce039dea5cfbe1f4ceff76635a272d8` |
| Exported synthetic merge / game build ID | `f3eb4ce72dd659f96df6d5e4804331c1fd4e1642` |
| Native source key | `81d54daaa9ffc8907de4e024c6f999f60b00dec21c21883608df1a49fc487f3e` |
| Outer player archive SHA-256 | `f56bbe77e7bdf5dd69b78343cf6a93321c76bb306ea85b473596c55030b34511` |
| Contained portable ZIP SHA-256 | `f9d4e963bbfdfe07d2939d25239f152518bbe8b8d17d69231c61ccd67dfb1769` |

Completed logs and downloaded player/evidence archives were inspected. Digests,
ZIP CRCs, the contained checksum and build identity matched. No local engine
compilation or game execution ran. Exact-build target performance remains
unverified; **M1 remains blocked**, and these fixes do not certify it.

## Previous Windows candidate: fog/frontier evidence

Implementation commit `7024be977653ffbe03376cda215323be58cb6835` on
`codex/m1-engine-proof` adds bounded [H1/H2 fog/frontier evidence](M1_FOG_FRONTIER.md):
mesh readiness, camera pose, conservative frontier distance and analytic fog
transmittance. Schema 5 retains missing boundaries/samples and reconciles saved
CSV rows with summary counts/minima. Settings, workloads, acceptance thresholds
and save/generator formats are unchanged.

[CI 36775406042](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042)
passed all three jobs. Static job `110091931750` passed the 12 packaging/cache
regressions, Python compile checks and three native sanitizer suites. Native job
`110092054562` built and qualified matching editor/debug/release binaries.
Windows export job `110137002347` verified native identity, passed Windows
packaging regressions, import, native/evaluation/helper tests, debug/release
smoke with saved-report reconciliation, all four streaming profiles, dependency
audit and two fresh offline extractions. All 33 ordered Voxel Tools patch entries
matched the pinned source. No check in this run failed.

Download [Windows player 11131500525](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131500525)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-30 at
23:08 UTC. [Export evidence 11131505658](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131505658)
and [symbols 11131026214](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131026214)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `7024be977653ffbe03376cda215323be58cb6835` |
| Exported synthetic merge / game build ID | `e51d00d0d3e847e4b1c04362df6642eef695c3ad` |
| Native source key | `81d54daaa9ffc8907de4e024c6f999f60b00dec21c21883608df1a49fc487f3e` |
| GitHub-reported outer player archive SHA-256 | `01ab158d2a8ce8ea2fe207c32a04a17903d292aeaf9e0d6ae0dc5df2318b94bd` |

Completed logs and artifact metadata were inspected. The archive was not
independently downloaded/hashed or executed locally. No local engine compilation
or game execution ran. Exact-build HD 620 coverage, edit latency, full diagnostic
overhead and pacing, shader/driver precision, allocation completeness, retention
and qualification repeats remain unverified. No corrected target baseline was
supplied; **M1 remains blocked**.

The exponential model has no finite analytic opaque boundary. The shader's
half-precision packing can round opacity; analytic transmittance and conservative
box/frustum overlap do not establish rendered-opacity boundaries or pixel
visibility. Unavailable boundary evidence remains inconclusive.

## Previous Windows candidate: edit visibility evidence

Implementation commit `525a079c414aa1c7c2ff531018b447d2b538ce8d` on
`codex/m1-engine-proof` adds bounded N2/H2 edit-to-mesh-submission evidence and
border/stale-result regressions. Save and generator formats, benchmark workloads
and thresholds are unchanged. Ordered patch entries matched the pinned Voxel
Tools source; local compilation/game execution did not run under the cloud build
rule.

[CI 36364646208](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208)
passed all three jobs. Static checks passed packaging/cache regressions, Python
compile checks and native fixture, operation and edit-visibility sanitizer tests.
The native job built and qualified the matching editor, Windows debug and release
templates. The export job verified their exact native identity, passed Windows
packaging regressions, native mesher and benchmark integration checks, debug and
release smoke, all four streaming profiles including border edits, dependency
audit and two fresh offline extractions. No check in this run failed.

Download [Windows player artifact 10950256937](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10950256937)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-28 at
03:21 UTC. [Export evidence 10949963015](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10949963015)
and [symbols 10949808351](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10949808351)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `525a079c414aa1c7c2ff531018b447d2b538ce8d` |
| Exported synthetic merge / game build ID | `3aa0b73091de21d860f3aaf12bc0fe26d654628c` |
| Native source key | `26d6169a6b9c2c8417a241ecae4ec3fee6829cfb9b4859edc39404b482320a1d` |
| GitHub-reported outer player archive SHA-256 | `2dcbb82c801507b079b7a36bd6e4dcc3520d8b74a22d3e7d2428aec7127baa59` |

The logs and artifact metadata were inspected. The player archive was not
independently downloaded/hashed or executed locally. Exact-build HD 620 edit
latency, diagnostic overhead, pacing/driver attribution, allocation completeness,
retention and qualification repeats remain unverified; M1 stays blocked.

## Previous Windows candidate: diagnostic-overhead accounting

[CI 36287728890](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890)
completed successfully on 2026-09-27 UTC (September 26 locally).
Download [Windows player artifact 10921940219](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921940219)
and extract the contained portable ZIP. GitHub reports expiry on 2026-10-27
at 02:17 UTC. Symbols are separate from the player distribution.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `1c9b7c638bb6154ce78c06f50831a7eda1db737e` |
| Exported synthetic merge / game build ID | `404af829964d341524f6c7ae29b4aebdac683b2a` |
| Native source key | `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803` |
| GitHub-reported outer player archive SHA-256 | `e6ae070fbbf6000ad7f479891b421e39f3e5dedada12a0ff90dca3e86551cbac` |

The user approved publication to existing public PR #2. Schema 3 now accounts
for callback formatting, CSV submission and UI work, preserves the final callback,
drains each measurement writer before retirement, and separately times final
summary assembly/hash/write/UI work. Both A/B modes retain bounded histograms and
five-second timing blocks. Conservative evaluation rejects unstable repeats in
either mode, within-phase drift, incomplete workloads and ranges crossing 1%.
[Measurement semantics and limits](M1_OPERATION_DIAGNOSTICS.md) remain explicit:
wall time is not CPU service time, overlapping costs are not added, shared native
counters remain enabled, and switched A/B success cannot certify total overhead.

Static job `108531574512` passed 12 packaging/cache regressions, Python compile
checks and both native sanitizer suites. Native job `108531629036` used the exact
cache, requalified editor/debug/release and skipped compiler installation/build.
It reused qualified native artifact `10920566667`; no new native source was built.
Windows job `108531756571` passed 12 Windows regressions, import, native/evaluation
and queue-rejection tests, debug/release smoke with actual CSV reconciliation,
all four correctness profiles, streaming/collision/edit/eviction/cancellation,
dependency audit and two fresh offline extractions. No check in this run failed.

[Export evidence 10921845799](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921845799)
and [symbols 10921516464](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921516464)
are retained. Completed logs and artifact metadata were inspected; the new player
archive was not independently downloaded/hashed or executed locally.

Initial validation [36287222011](https://github.com/dponcho/voxel-survival-game/actions/runs/36287222011)
failed 32³/two-worker report integrity after earlier checks passed.
[Preserved evidence 10920778828](https://github.com/dponcho/voxel-survival-game/actions/runs/36287222011/artifacts/10920778828)
was downloaded and reviewed: incomplete output began after N1; no script error
was logged. Source review identified one-shot final-batch submission despite
transient native queue rejection. The follow-up adds bounded between-frame retries
outside gameplay and regressions for transient rejection, permanent blockage and
writer failure. The corrected full run passed; the original failure is preserved.

No native inputs, save/generator behavior, simulation workload or acceptance
threshold changed. Exact-build HD 620 overhead, edit visibility, pacing/driver
attribution, allocation and retention/qualification evidence remain unverified.
M2 remains gated. Review one corrected baseline before another full comparison
or final repeats. The [handoff](NEXT_TASK.md) names the next bounded implementation.

## September 26 candidate: phase-local attribution correction

[CI run 36280383637](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637)
completed successfully on 2026-09-27 at 01:29 UTC (September 26 locally).
Download [Windows player artifact 10920027865](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920027865)
and extract its contained portable ZIP. The artifact contains the ZIP, checksum
file and build identity. GitHub reports expiry on 2026-10-27 at 01:29 UTC.

| Identity | Value verified from CI logs/artifact metadata |
| --- | --- |
| Implementation branch commit | `3685dd472e5ffd3429ba5d35b7ee63c949b374e5` |
| Exported synthetic merge / game build ID | `b65ba3e409ba7a80da282b5297783533de2f6fc6` |
| Native source key | `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803` |
| GitHub-reported outer player archive SHA-256 | `acf8f7b1c32a00c8a33ab38a5dc9f50ad9f5a428a0d08e91c0fba192c71c76b8` |

The source pins, compiler and flags are unchanged. The native instrumentation
changed the source key, so the ordinary reuse-enabled workflow built matching
editor/debug/release binaries after an exact cache/artifact miss. Native job
`108511005497` qualified them, saved the exact cache and published
[native artifact 10920566667](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920566667)
before game export. No manual cold build or redundant CI run was launched.

Static job `108510956501` passed all 12 packaging/cache regressions, Python
compile checks, the existing native fixture checks and the new phase/frame
regressions with address/undefined-behaviour sanitizers. Windows job `108525026003`
verified native identity/digests, passed all 12 Windows regressions, matching-editor
import and native/evaluation tests, debug/release smoke, all four correctness
profiles, streaming/collision/edit/eviction/cancellation, dependency audit and two
fresh offline extractions. Every smoke report checks actual operation CSV totals,
maxima, timestamps and phase isolation against phase/lifetime counters.

[Export evidence 10920157662](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920157662)
and [separate symbols 10919853233](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10919853233)
are retained. This session inspected completed logs and artifact metadata; it did
not independently download/hash the new archives or run the game locally.

The [correction](M1_OPERATION_DIAGNOSTICS.md) adds phase-local upload/deletion
maxima, bounded per-frame operation evidence and explicit completion versus
qualification. Lifetime counters, thresholds, workload, generator and saves are
unchanged. No current cloud check failed. Corrected exact-build HD 620 results,
end-to-end overhead, edit visibility, pacing/driver attribution, allocation and
retention/qualification evidence remain unverified. M2 remains gated. The
[handoff](NEXT_TASK.md) names the next bounded implementation task.

## September 25 reviewed candidate

The previous candidate's immutable cloud result was **cloud_passed_target_unverified** from
[GitHub run 36183549961](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961),
completed successfully on 2026-09-25. This is not an M1 target-performance pass.
Run status, completed job logs, artifact metadata and downloaded player/evidence
archives were inspected on 2026-09-25.

Download [player artifact 10889930434](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889930434),
then extract the contained `Cairn-windows-x86_64.zip` into a fresh folder.
GitHub reports an expiry of **2026-10-25 21:58 UTC**; retention can change.
The artifact includes the portable ZIP, `SHA256SUMS.txt` and `BUILD_INFO.json`.

| Identity | Verified value |
| --- | --- |
| Source branch commit | `68918f2a8ad63325b2be7d4c02ce05fa753aef63` |
| Exported synthetic merge / game build ID | `6874b8809094d22b33e05c60ef61c2e1c333494a` |
| Native source key and actual embedded engine identity | `6adda08d3b832e3e5c40a41fd5b7bcd527bd2d1d6b274cd37b039a2371b61d7f` |
| Godot source | `ed1daf0bf001b61586d9930840f2f1394092c079` |
| Voxel Tools source | `2ac9f5f8a8219bf499314cc0fad54ffc47df908f` |
| Inner portable ZIP SHA-256 | `0dd72b172cade30c7a0a7fb8b005490fac39567ff8afcc0f049c209561b4346b` |
| Inner portable ZIP size | 29,892,003 bytes |
| Outer Actions player archive SHA-256 | `c0c4ee6ab2f15aaf1067ccad281416d6888ad446434966915eda4533530e5c92` |

The downloaded outer archive matched GitHub's digest. The inner ZIP was hashed
independently and matched both `SHA256SUMS.txt` and `reports/candidate.json`.
These are different archives and checksums. The current engine identity is the
new source key above; the historical legacy identity was not used by this build.

Supporting artifacts are [export evidence 10889685801](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889685801),
[separate symbols 10888974332](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888974332)
and [native reuse evidence 10888649212](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888649212).
The export evidence archive SHA-256 is
`d7d2414bcd7cb2b7f9f266721380f74961419a74793943c6ab33267aa4772837`,
also verified after download.

## September 25 executed cloud checks

The follow-up static job `108264637172` passed all 12 packaging/native-reuse
regression tests, Python compile checks and native fixture checks with address
and undefined-behaviour sanitizers on Linux.

Native job `108264737945` restored the exact cache and requalified the custom
editor and both Windows templates. Compiler installation and native compilation
were skipped. It reused native artifact `10888733603` from the successful producer
[run 36180365572](https://github.com/dponcho/voxel-survival-game/actions/runs/36180365572);
the follow-up's native-bundle upload was skipped too.

Windows export job `108264995129` downloaded that same producer artifact and
verified its digest and bundle identity/files. It passed:

- All 12 Windows packaging/native-reuse regression tests.
- Matching-editor import, module self-tests and native split-mesher coverage.
- Debug/release scenario smoke and all four render-block/worker profile
  **cloud integration/correctness checks**.
- Streaming collision, edits, eviction and cancellation integration checks.
- Executable dependency audit and both fresh offline extraction self-tests,
  including paths with spaces/non-ASCII characters and a different working directory.
- Portable player ZIP, separate symbols and evidence publication.

`reports/candidate.json` records `native_bundle_source: cache`,
`cold_cache: false`, `status: cloud_passed_target_unverified` and
`target_performance: not_run`. Both extraction reports have `passed: true`,
no errors and the expected build/native identities.

The producer also passed its static, native qualification and separate export
jobs. Its source commit was `f7a02589601a9339c9bdf54c135f9e3d949c99f3`, exported
as `4aeb6029b602328c439815c99864cc93c167c5c9`. The latest candidate above adds
actual window-size reporting without changing native inputs. It includes the
recent N3 rotation, fixture-fall detection, comparison-launch failure reporting,
fixed 720p window and stronger mesher checks. The current cloud results supersede
their previously pending validation status. See the [CI architecture evidence](CI_ARCHITECTURE.md#acceptance-evidence)
for the exact bundle, reuse proof and remaining fallback-path limitation.

## September 25 target evidence and remaining scope

Hosted Windows rendered smoke was **not run**. The user supplied one standalone
baseline and a complete four-profile comparison from the actual i7-7600U / HD 620.
All five report identities and executable/PCK hashes match the September 25 candidate;
1,682,025 CSV rows were independently checked against their summaries. See the
[target review](M1_TARGET_REVIEW.md) and [machine-readable results](evidence/m1-target-2026-09-25-review.json).
Frame-rate capacity, memory and recorded collision/readiness results are promising,
but lifetime native timing contaminates scenario outcomes, diagnostic overhead is
inconclusive and frame-pacing/other required observations remain unresolved.
No profile is qualified and M2 remains gated.

The experiment uses stock blocky meshing with bounded split uploads, not greedy
meshing. Every comparison uses the finite fixture slab Y [-16,32), visual radius
96 m and data radius 128 m. Edits use a bounded temporary session overlay; actor,
weather and storage workloads are proxies. There is no durable save format or
complete-world vertical qualification. That report review did not change runtime
inputs. The user's [2026-09-26 Java core requirements](JAVA_CORE_REFERENCE.md)
apply to future implementation and do not retroactively change the reviewed candidate.

The attribution correction above addresses one part of the target review.
The schema 3 overhead correction above now has cloud evidence; exact-build target overhead remains unverified.
Do not request another four-profile run or the final three
qualification repeats until the corrected evidence path is ready. The
[laptop guide](M1_TESTING.md) remains the procedure for the next exact-build
candidate. A startup-check pass alone does not qualify M1.

## Earlier candidate history

[Run 34036830778](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778)
and Windows job `101496360796` passed the earlier native build, integration and
portable-package checks on September 6. Source commit:
`fe5cadc2876fc5a889c72b097373f544f4ed9fff`; exported synthetic merge:
`4e6c761c26950111ffd6af1bd496c81a6c9ed04b`; legacy native identity:
`f90df9f55adb77e131cd1f575a50caded0e8fbd17f5b0f96877e7884320197b1`.

Its [player artifact 9992504297](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992504297)
had outer archive SHA-256
`005138342e079611dee69bf1ae0c88a0eb245685e49b4d85aacb950577b86504`
and recorded expiry 2026-10-06; availability was not rechecked in this continuation.
Its [evidence artifact 9992510088](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992510088)
and the earlier failed run `34003770515` / corrective run `34007283054` remain
historical provenance. Use the corrected candidate above for subsequent
instrumentation checks; review remaining measurement gaps before qualification repeats.
