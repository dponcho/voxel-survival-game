# Preparation owner launch review

October 25, 2026. Saved evidence and source review complete. **Do not declare or
launch the preparation attribution process with the current candidate.** A
post-boundary prefix-write failure can start the next trial. This is a source
control-flow finding; no engine fault injection or attribution route ran.

The capability result in [the owner-scope proof](M1_PREPARATION_OWNER_SCOPES.md#result)
remains verified. It does not establish the batch failure branch examined here.
M1, target performance and optional diagnostic cost remain unqualified.

## Exact evidence reviewed

The [reproducible review](evidence/m1-preparation-owner-launch-review-2026-10-25.json)
binds branch head `b6b36a4b1186f064d11e5a94140fe3539c6fbf77`, the original proof
SHA-256 `3bf79439713d668a8ccf68f327bc13fa19d5f736b02e58fc2d759a6f8e845f09`,
the downloaded portable ZIP, source metadata, native key, actual executable/PCK
hashes, all 112 PCK entry MD5s and 38 PE imports. No executable is started.

| Item | Exact identity |
| --- | --- |
| Verified runtime CI | [40216786118](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118), all four required jobs passed |
| [Portable candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118/artifacts/12609121247) | Inner ZIP 30,306,108 bytes; SHA-256 `3b894f209a1b9976fa2b79dfcc60878895d4219c1557eb4b8078e5622b1f48b1` |
| Native key | `777879f5d9b2bd461e37dcac74102b5adc370381342d60250fcebed7002c360a` |
| Preparation inventory SHA-256 | `269adac80b939b85b0ddc8d1030b5e9b0568d0737d2dc97279582d7d8b4a9f0c` |
| Exported source | `d6e14a545e31dcd62e74e263442e6849459b5d8c` |

Both current controls and both controls from cancelled CI `39998646163`
reproduce from exact embedded bytes: 48 files / 1,624,650 bytes, with all 84
saved semantic corruptions rejected. The current traces have 1,680 / 1,182
records; the cancelled run's traces have 1,536 / 2,620. That cancelled run stays
cancelled. Raw ownership, handover, attempts/completions, nested main union,
unsigned errors, failed prefixes and both destruction witnesses remain intact.

Seven new saved-review regressions pass, including re-signed unjoined-writer and
retained-recorder evidence, forged qualification, altered/compressed bytes and
the wrong candidate. The ten affected preparation-reader regressions also pass.
The review changes no runtime, inventory, native/dependency, workload, save or
generator bytes. Existing CI and candidate identities remain; an unchanged
integration or native build is unnecessary for this saved review.

## Stop-rule finding

After an otherwise valid warm-up, assume the actual `sequence-prefix.json`
write fails. The exact source and line excerpts are retained in the review:

1. In `m1_preparation_demand_runtime.gd:457–461`, `_finish_trial()` copies the
   completed trial, then attempts the prefix write. The failure sets only
   `report_io_failed`. It occurs after `trial.checks.io` and `trial.valid` were
   evaluated. `abort_reason` remains empty, so the scenario list is not shortened.
2. In `benchmark.gd:766–770`, the inherited drain path returns from
   `_scenario_drained()`, increments the scenario index and immediately calls
   `_start_scenario()` when another scenario remains. There is no intervening
   prefix-I/O or abort check. Its earlier `_close_reports()` ran before this
   new failure.
3. The new mode starts another recorder and terrain setup. Later observation of
   the sticky I/O flag can invalidate output, but cannot undo this continuation
   after an already detected failure.

The native control's write/open failure exercises observer emission. It does
not inject this later batch-prefix publication failure. The independent reader
also does not currently reconcile `sequence-prefix.json` or represent a
post-boundary publication failure separately. Source inspection is sufficient
to withhold the finite process; runtime reproduction remains required for the
correction. No engine failure or new performance result is claimed here.

## Next bounded implementation

Correct only the new preparation-demand mode's prefix-failure stopping and its
reader. Keep old v1/v2 entry points, codecs, inventories and historical verdicts.

- Stop before any later `_start_scenario()` or recorder/terrain publication when
  a sequence-prefix write fails. Retain an explicit batch failure and the honest
  successfully written evidence; missing output remains unavailable.
- Keep the original complete-trial boundary and its immutable complete/terminal
  snapshots and hashes. A later batch write failure needs a separate witness;
  do not retroactively rewrite an inside-trial I/O observation or charge this
  common reporting work to the finished trial.
- Make the reader accept an honest early prefix caused by that explicit batch
  failure and reject any following trial. Reconcile a successfully written prefix
  with final saved trials; retain failed/missing prefix status without inventing
  a valid file or a passing zero.
- Add a bounded matching-editor/release control that exercises the real new-mode
  publication/handover path with an injected prefix-write failure after an
  otherwise valid synthetic completion. It must prove zero next-scenario,
  recorder and terrain starts. Cover normal handover, a pre-existing failed
  trial, and failure at the last trial. This is a controller fault fixture, not
  an attribution route or shortened route pretending to be one.
- Verify affected reader regressions, matching parsing and real controller
  controls, required integration/package checks, and a new portable PCK. Reuse
  and requalify the exact native bundle unless native code actually changes.

After that correction and candidate pass, review the exact proof before any
prospective one-process declaration. Preserve warm-up plus four bare trials,
32³/one terrain worker, 4,320 ticks / 103,680 actor ticks / 288 edits / 72 saves,
full height, radii, caps, complete lifecycle and numerical 1%. No retry,
positive/shipping continuation, fitted correction, frame normalization, clipping,
process/thread subtraction, laptop action or M2 expansion follows here. All three
consumed pilot inputs remain false. Use **GPT-6.1 Sol Max**.

## Replay this review

`CANDIDATE` is the inner portable ZIP from artifact `12609121247`, available in
the cloud workspace or downloaded/extracted through the connected GitHub tools.
From the repository root:

```bash
python tools/qa/preparation_owner_review.py --candidate "$CANDIDATE" --check docs/evidence/m1-preparation-owner-launch-review-2026-10-25.json
python -m unittest discover -s tests/integration -p 'test_preparation_owner_review.py' -v
python -m unittest discover -s tests/integration -p 'test_preparation_demand.py' -v
```

The replay checks source and file identity and replays raw controls; it does not
execute the GDScript failure path or start an engine.
