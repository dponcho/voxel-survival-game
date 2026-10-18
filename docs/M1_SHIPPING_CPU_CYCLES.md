# V2 shipping diagnostic cycle method

Policy `m1-shipping-diagnostics-2`; method `m1-shipping-cpu-cycles-1`.
This implements [the adopted decision](M1_DIAGNOSTIC_COST_POLICY.md).
**Implemented; the finite cloud pilot is inconclusive.** Matching native binaries,
portable export, required integration/package checks and downloaded Windows/Linux
readers pass [CI `39088740702`](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702).
Five complete trials pass their work, I/O, resource, edit, coverage/readiness and
native operation guards. The null range is too wide and section drift exceeds
its limit. The sequence stopped before either later quartet. The 1% CPU-cost
gate and M1 remain unqualified; no laptop action is requested.

## Result

The only route launch completed one warm-up and the four bare null trials.
Every trial has 4,320 physics ticks, 103,680 actor ticks, 288 accepted/submitted
edits, 72 proxy saves, zero readiness/coverage alarms and complete drain.
All fifteen native phases pass. Peaks are 392 meshes / 5,104 data within the
unchanged 512 / 8,192 caps. Edit p95 bounds are 56 ms; the largest edit is
104,093 µs, below the separate 200 ms maximum.

| Trial | Complete cycle midpoint | Complete elapsed µs | Callbacks |
| --- | ---: | ---: | ---: |
| Warm-up | 44,186,540,707 | 77,490,353 | 10,440 |
| Null A0 | 44,467,716,901 | 77,791,614 | 10,440 |
| Null B1 | 43,966,882,152 | 77,495,554 | 10,441 |
| Null B2 | 44,266,402,137 | 77,805,736 | 10,440 |
| Null A3 | 44,469,850,995 | 77,495,203 | 10,441 |

The exact reader reproduces the empirical null range **[-2.217168530%,
+0.633380871%]**, pooled point -0.791885391%, width **2.850549401%**.
It contains zero, but the width is not below 1%. Conservative matching-section
drift is **1.073468789%**, also not below 1%; marker uncertainty contributes
0.011690191%. These are repeat-envelope observations, not confidence intervals.

| Shared section | Off-pair conservative drift / reference | On-pair conservative drift / reference |
| --- | ---: | ---: |
| Preparation | 0.393509% | 0.237326% |
| +X | 0.241386% | 0.271085% |
| -X | 0.269905% | 0.365658% |
| +Z | 0.123851% | 0.194109% |
| Lifecycle tail | 0.012504% | 0.005290% |
| Sum | 1.041155260% | 1.073468789% |

Off-pair complete totals nearly match while their section differences sum above
1%. The shared-section guard retains that cancellation. No section was removed,
no outlier discarded and no correction fitted. The positive request was never
created; no 4,320-tick positive dose or shipping quartet ran. There is **no
shipping-cost estimate** from this sequence.

The [committed evidence](evidence/m1-shipping-cpu-cycles-cloud-2026-10-18.json)
retains all five trial records, original cycle/wall bounds, sections, lifecycle
and operation evidence, trace hashes, exact assessments and artifact identities.
All raw files remain in the
[pilot artifact `12124742743`](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702/artifacts/12124742743).
The downloaded
[Linux recheck `12124668103`](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702/artifacts/12124668103)
and the current stricter reader exactly reproduce the Windows audit.

## Verified candidate and checks

[Portable player `12123649793`](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702/artifacts/12123649793)
contains the ZIP, `BUILD_INFO.json` and checksums. The inner ZIP is
**30,222,870 bytes**, SHA-256
`3e884fecd26b6b406943904fd1d197ca9789467f19bbcf6a3a64f2df3a21a57b`.
Runtime source is `7153ee46cb42ae925e08d48b2973d12adf4c58ee`; exported merge
identity is `41aa6e1cee6d3fea3a5e16d3c64e46fc8c1221eb`.

The new native key is
`9a92d280a853f8982e65a44b27c5ded11b7888883fb132686b5fd3acd31922cd`.
The [qualified native bundle](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702/artifacts/12124386850)
contains new editor/debug/release binaries with unchanged source/toolchain pins
and flags. Their compile times were 2,475.812 / 1,733.000 / 1,630.454 s.

| Binary | SHA-256 |
| --- | --- |
| Editor | `37d99e1a66b3d638563b8a0dc19ccf1d4dad024a05f9ede22c7e0a9c16b68274` |
| Debug template | `1aa1fe04f55a86eafdba62ef9751ae01b17bd67284832e179c8008b242f045f6` |
| Release template / Cairn.exe | `a80d3c6c650c7c268099d6d5d4098a8e1bc7c6987b39f76fae219dcd1e20a79f` |

157 Python regressions and eight native sanitizer suites pass in Actions. The
current saved-reader follow-up passes 162 Python regressions in Codex Cloud.
Each matching editor/release passes 28 pure method cases, eight exact request
vectors, five raw boundary controls, one zero/one bounded positive native API
call and four rejected requests. Both fixed counter capability smokes also pass.
The release API positive used one SHA update in 68 µs; this is API evidence,
not an in-route sensitivity result.

Required prior integration, PE/DLL audit, eight qualification/game/offline
self-tests, 100 PCK entry MD5 checks and published-byte identity checks pass.
All 50 preceding, 24 counter and 14 new saved faults are rejected. The current
reader additionally checks each native witness against its real physics tick
and shared route brackets, preserves honest unavailable-counter evidence and
reproduces the original audit without another engine launch.

The latest broader saved phases have no operation-limit failures. Historical
1,025 / 810 µs, 753 / 794 µs and the five preceding broader failures remain
retained measurements. Current 16³ one/two-worker release H2 cases still fail
edit p95 (166 / 173 ms); FIFO coverage/edit failures and the standard full-height
baselines' 520 alarms each remain visible. Prepared full-height cases retain
zero alarms and all 288 submitted edits. These observations select no target
profile or production scheduling policy.

## Next bounded action

Review these saved null records and shared observers, then make an explicit
prospective measurement/repetition decision that retains the 1% limit and
complete lifecycle. Preparation and all three route legs contribute to the
observed drift. The cause is not isolated by this pilot. No automatic retry,
longer trial, fitted correction, profile matrix or laptop action follows.
Production remains FIFO, priority opt-in, and M2/content expansion remains gated.
Use GPT-6.1 Sol Max; the live CI pilot input defaults to false.

## Executable scope and boundaries

`game/diagnostics/shipping_cycles_inventory.json` is a separate v2 inventory.
The v1 inventory, runtime, method and CLI entry points remain intact, with their
historical evidence and failed verdicts preserved. Production scheduling remains
FIFO; this fixture keeps its existing opt-in priority policy and directional
preparation viewer. No world generation, save/content IDs, workload, worker count,
resource cap, operation limit or edit threshold changes.

`--shipping-cycles-pilot` selects one fixed 32³/one-worker process. It records
process/current-thread observations around common snapshot work at six shared
boundaries: before optional setup/preparation, prepared, +X, -X, +Z and after
complete per-trial report flush/close. The last boundary includes native phase
closure, writer joins, final edit acknowledgement, terrain/preparation retirement
and optional summary write/disposal. The same boundary object serves both adjacent
sections. Unsigned counters remain decimal strings. Integer midpoint differences
partition the complete midpoint difference exactly; conservative interval bounds
retain shared uncertainty. Thread totals are never added to process totals.

The terminal boundary marker write has separate process-cycle/wall brackets.
Both arms' conservative marker costs expand the comparison. Shared boundary
arithmetic, evidence retention, protocol selection and final batch reporting are
declared common harness work outside the complete trial. Cycles are never
converted to time. Raw elapsed sections and the original elapsed repeat envelope
remain descriptive, separate from the cycle decision and operational guards.

## Native dose and exact controls

`CairnProbe.cpu_cycle_dose(decimal_request)` uses native SHA256 updates of 4,096
fixed `Z` bytes. Its positive-only loop, counter checks and hash initialization/
finalization remain inside the thread-cycle witness. A zero-request common witness
runs in every other arm. Each real physics tick retains original ordered native
observations, enclosing wall clocks, update count and digest in bounded JSONL.
The common witness/serialization is disclosed; no observer subtraction is fitted.

The fixed positive request is `ceil(positive_A0_midpoint / (50 * 4320))` raw
cycles per tick. A request is never adjusted after B1. A tick reaching 512 SHA
updates, exceeding 50 ms, losing a counter or failing a hash stops the sequence.
The actual 4,320 dose intervals must each reconcile and their sums/reference
ratios must lie above 1% and at/below 3%, overlap the measured positive range,
and leave its lower bound at/above 1%. No sleep, yield or terminal dose is used.

The portable runtime uses decimal integer arithmetic and rational cross products
without signed-counter casts or floating-point gate decisions. The independent
Python reader uses integers and `Fraction`. Matching-editor/release controls
check exact thresholds, dose ceilings, section drift, marker uncertainty, masked
work, missing/invalid trials, unsigned values through UINT64_MAX, cross products,
shared boundary failures and one bounded native zero/positive API witness each.
These synthetic/API checks do not establish sensitivity or a cost pass.

## One finite sequence

The release launcher declares the exact candidate and maximum order before its
only engine launch: one complete warm-up, a bare null quartet, a bare known-
positive quartet, then a shipping quartet only after usable controls. It stops
after any failed work/counter/I/O/operation guard, unresolved null (up to five
trials), unresolved positive (up to nine) or the shipping comparison (up to 13).
Every completed prefix and failed/partial trial is retained. No padding, retry,
v1 repetition, longer trial, new calibration family or profile matrix is allowed.

The null interval must contain zero with width below 1%; null/positive matching-
section drift must each remain below 1%. Shipping upper below 1% passes this
conditional CPU gate; lower at/above 1% fails. Overlap, negative pooled effect,
failed guards or unavailable controls remain inconclusive. Integrity verification,
trial guards, measurement validity, cycle cost and target performance are separate
fields. All existing frame, edit, coverage/readiness, memory and operation gates
remain independent. No cloud result qualifies the HD 620 or M1.

The Actions pilot switch is prospective and opt-in. Disable the implementation
commit's one-shot CI request once its evidence is retained. Saved Windows/Linux
readers and corruption controls execute no engine and cannot repeat the pilot.
