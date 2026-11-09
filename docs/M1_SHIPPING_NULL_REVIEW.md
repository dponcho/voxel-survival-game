# Saved null review and observer-attribution decision — October 18, 2026

**Review complete. Keep the stopped v2 result inconclusive. Implement bounded
common-observer attribution before another shipping-cost qualification sequence.**
No engine ran for this review. No laptop test is needed at this stage. The 1%
requirement, complete lifecycle and independent operational gates remain intact;
M1 and the target viability checkpoint remain unqualified.

## Evidence and reproducibility

The input is the [unchanged five-trial record](evidence/m1-shipping-cpu-cycles-cloud-2026-10-18.json),
SHA-256 `ad12675546382519f826613b5a46714960ebe15fdda837bfc3f980cc2f66d945`,
and [original raw artifact 12124742743](https://github.com/dponcho/voxel-survival-game/actions/runs/39088740702/artifacts/12124742743).
Its downloaded ZIP matches SHA-256
`67ba5610b3c8cde86095b14d15da6b9719e3b440430196effaf28fdcdcfcbea8`
and passes ZIP CRC checks. All 75 extracted files match the committed size/hash
manifest. The unchanged independent v2 reader reproduces the original saved
audit exactly, including valid work guards, invalid controls and the stop.

[The new review reader](../tools/qa/shipping_cycles_review.py) produces
[an exact derived record](evidence/m1-shipping-cycles-null-review-2026-10-18.json).
It uses integer arithmetic and rational fractions, verifies the original raw
reconciler before analysis, and invokes no game/build command. Reproduce after
extracting the artifact, substituting its one raw sequence directory:

```bash
python tools/qa/shipping_cycles_review.py --raw /path/to/raw/M1-2026-10-18T04-13-48-32-1-2988 --output docs/evidence/m1-shipping-cycles-null-review-2026-10-18.json --check
python -m unittest discover -s tests/integration -p 'test_shipping_cycles_review.py' -v
```

This review changes no runtime, native source, executable inventory, dependency
pin or candidate byte. [The verified v2 Windows candidate](M1_SHIPPING_CPU_CYCLES.md#verified-candidate-and-checks)
remains the latest runtime. V1/v2 measurements and verdicts remain historical
evidence, with their original IDs. Warm-up is retained but is not a null repeat.

## What the stopped quartet distinguishes

The complete-trial repeat envelope decomposes as follows. Percentages are rounded
for display; the linked record retains exact rational values.

| Width contribution | Percentage points |
| --- | ---: |
| Unexpanded complete-trial repeat range | 0.680231440 |
| Two-sided matching-section drift expansion | 2.146937579 |
| Two-sided terminal-marker expansion | 0.023380382 |
| Original total width | **2.850549401** |

The unexpanded range itself is **[-1.132009550%, -0.451778109%]**. Both B trials
use bare mode, like both A trials; no optional shipping work or positive dose was
enabled. This is an observed order-associated difference, with no isolated cause.
It is not a shipping saving or evidence of positive-work masking.

Let `E >= 0` be any symmetric expansion of that saved raw range. Including zero
requires `E >= 0.451778109%`. Width strictly below 1% requires
`E < 0.159884280%`. These constraints are incompatible. The narrowest symmetrically
expanded range containing zero would have width **1.583787659%**. This algebra
does not apply a correction or create another verdict: it explains why changing
only drift/marker uncertainty cannot rescue the recorded quartet.

Even ignoring zero containment, the saved raw range and marker cost leave a
drift allowance below **0.148194089%** for the width rule. Reducing the observed
1.073468789% drift merely below its separate 1% limit would therefore be
insufficient. This is a diagnostic constraint on these records, not a new limit
or a prediction that a later sample will have the same raw range.

| Null repeated pair | Signed complete midpoint difference, cycles | Sum of absolute section midpoint differences | Conservative section difference sum | Boundary-uncertainty part of that sum |
| --- | ---: | ---: | ---: | ---: |
| A0 → A3 | +2,134,094 | 460,033,942 | 462,975,829 | 2,941,887 |
| B1 → B2 | +299,519,985 | 474,443,257 | 477,344,851 | 2,901,594 |

The A pair's small net total hides opposing section differences. More than 99%
of each conservative section sum is already present in the absolute midpoint
differences. Counter-bracket precision alone does not account for this variation.
Preparation and all three route legs contribute; tail and marker costs are small
in this particular comparison. All remain inside their declared boundaries.

## Work and observer findings

Every recorded section has identical native generation/meshing/upload work counts
and upload bytes across all five trials, including warm-up. Per complete trial:
13,984 generated data blocks, 1,801 meshed blocks, 3,353 uploads and 360,441,760
upload bytes; no stale result or overload. All five retain the verified 4,320
physics ticks, 103,680 actor ticks, 288 accepted/submitted edits, 72 saves, zero
readiness/coverage alarms, full drain and passing operations. Equal recorded work
does not establish equal unobserved engine, observer, allocation or OS activity.

| Common observer / operational work | What is saved | Remaining distinction |
| --- | --- | --- |
| Preparation and readiness polling | Preparation native phase has 777, 822, 778, 824, 778 frames; each prepares 5,104 data blocks, 392 meshes and 659 uploads | Different polling/frame counts coexist with matched native work. No saved CPU span isolates polling from preparation. |
| Per-callback qualification | 10,440 / 10,441 gameplay rows; native/process-memory snapshots, terrain/pool statistics, frontier scan, histogram and CSV batching; six acknowledgement rows in each trial | Existing callback and frontier spans are **elapsed wall time**, not CPU-cycle attribution. No callback normalization or observer subtraction is valid. |
| Per-tick native zero-request witness | 4,320 ordered native witnesses per trial; their enclosed thread-cycle sums are 1.312–1.366% of complete process demand across these trials | These are nested witnesses, not incremental optional cost or total observer cost. They exclude later GDScript exact arithmetic, JSON/pose formatting and writes. Never add them to process totals. |
| Per-tick evidence serialization | 8,330,741–8,453,133 cycle-JSONL bytes per trial, plus pose CSV | Byte counts are recorded work, not a CPU-cost model. Those operations have no separate saved cycle spans. |
| Asynchronous common writer | Frame/edit writes, proxy writes, flush and joined drain remain inside complete process/lifecycle bounds | No saved worker-cycle attribution separates qualification output from proxy-save work. Blocking time cannot be inferred from cycles. |
| Tail and correctness reporting | Final acknowledgement, native closure, retirement, hashes, report serialization/flush/close and separately measured marker | Complete process cost is retained; individual report/writer ownership is not fully attributed. |

The [executable inventory](../game/diagnostics/shipping_cycles_inventory.json)
and source establish these ownership boundaries. In particular,
`CairnProbe.snapshot()` calls process-memory accounting as well as native stats;
the native zero-request witness builds dictionaries; GDScript then computes exact
intervals and serializes full records every tick. These are concrete candidate
owners for attribution, not demonstrated causes of the null difference. The
saved records cannot identify a removable observer or justify a timing correction.

## Prospective decision

Retain policy `m1-shipping-diagnostics-2`, method `m1-shipping-cpu-cycles-1`, the
shipping inventory and all numerical gates. **Do not repeat the unchanged pilot,
average away its range, fit a correction, remove a section, change pacing/work,
or start another injection family.** Four null observations establish no
confidence interval or warranted repetition count that would certify <1%.

The chosen next implementation is a separate, explicitly perturbing
**common-observer attribution prerequisite** (`m1-shipping-observer-attribution-1`).
It answers where shared measurement work and its variation occur. It does not
estimate shipping overhead or replace a sensitivity control. Implement it under
a new opt-in mode/inventory, preserving v1/v2 entry points, readers and records.

1. Add a bounded native cycle-span ledger for main-thread qualification groups
   and the existing report worker. Retain ordered raw unsigned endpoints,
   availability/errors, thread identity, enclosing wall brackets, phase/section,
   call counts, byte/work counts and inclusive/exclusive ownership. Use fixed
   slots and bounded batched records; perform decimal formatting/reporting at
   declared phase drains. Cap the additional trace at 32 MiB per trial and fail
   on overflow, missing spans, nesting errors, counter errors or I/O failure.
   Never discard samples or treat an unavailable observation as zero.
2. Separate preparation qualification, callback resource/native queries,
   frontier evaluation, callback formatting/submission, per-tick native witness,
   post-witness exact arithmetic/JSON/pose output, and report/hash/flush closure.
   Profile report-worker qualification writes separately from operational proxy
   saves; retain the worker's final witness before exit and verify join/closure.
   Operational collision, edits, admission, terrain enforcement and route
   preparation continue unchanged. Account for nesting once; keep unobserved
   engine/worker/deferred work explicitly unavailable. Thread spans are attribution
   evidence within the complete process observation, never additive process cost.
3. Keep all common qualification observers and safeguards enabled. Attribute
   the new ledger/serialization work as perturbation; make no subtraction or
   total-overhead claim. Preserve the same six shared complete boundaries, five
   sections, terminal marker, 32³/one-worker profile, 4,320-tick route and caps.
4. After pure/native fault controls and matching editor/debug/release/package
   checks pass, permit **one cloud release process with at most five trials**:
   one complete warm-up followed by four bare attribution trials. Predeclare
   order, exact candidate, new inventory, source hashes, trace cap and 1,500 s
   process timeout before launch. Stop at the first work, counter, span, I/O,
   operation or resource failure and retain the failed/partial prefix. No retry
   or padding. Stop after five even if the descriptive null becomes usable;
   create no positive request and append no positive/shipping quartet.
5. Reconcile the new raw spans independently, including closed-worker retention,
   counts, nesting, full lifecycle and original work/operation guards. Test
   missing/duplicate/reversed spans, failed counters, overflow, false ownership
   and forged qualification. Classify the result only as attribution evidence;
   cost remains inconclusive, qualification false and target not run. Review
   whether a concrete observer implementation change is supported. If variation
   remains outside attributed scopes, record that limit and stop. No subsequent
   optimization, cost sequence or target run is automatic.

This task implements only the saved reader/review and records that decision.
The new ledger, mode, inventory and finite attribution process are **not yet
implemented or run**. Both current pilot switches stay false. Native changes in
the next task need a new source key and matching Windows binaries; the existing
candidate cannot supply a proposed API. No save/generator/content compatibility
change is planned. A later shipping qualification attempt still needs valid null
and known-positive controls and the unchanged below-1% upper bound. A laptop
test follows only after usable controls and an explicit exact-build target plan.

## Validation

All 64 affected shipping-method/reader regressions pass, including eight new
pure tests covering incompatible zero/width requirements,
strict equality, exact decomposition, cancellation, observed native work,
invalid trials, same-size raw tampering, missing/extra files and escaping links.
The downloaded artifact and all 75 raw files were verified; the original audit
and derived record reproduce exactly without an engine. Only affected Python
checks and source/document consistency checks are required for this increment;
native/runtime suites and the completed pilot are not repeated for this review.
