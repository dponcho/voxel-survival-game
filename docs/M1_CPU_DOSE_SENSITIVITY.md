# Experimental per-callback CPU dose instrument validation

M1 remains blocked; no target profile is qualified. This cloud-only increment
validates a synchronous callback instrument with modeled clocks and real bounded
native CPU work. It changes no legacy/current assessor, 1% requirement, world/save
semantics or workload. Ordinary benchmark summaries retain
`cpu_dose_sensitivity.status: not_run` with null CPU service, GPU, causal probe and
shared-overhead estimates. No dose runs in gameplay or existing calibration.

## Estimand and limits

The experimental estimand is **mean synchronous callback body wall duration per
observed callback at matching route positions**. A body bracket covers the
callback's modeled or real work, including the injected native CPU span. Subsequent
ledger bookkeeping is separately retained in the complete diagnostic callback
and complete trial. These are monotonic wall spans: OS descheduling can contribute.
They are not OS CPU service measurements or the entire engine frame critical path.

The pooled mean is total body wall duration divided by callback count. A minimum/
maximum reference/positive repeat envelope uses exact integer cross-products at
the unchanged 1% boundary. Same-mode pooled and matching main-section body means
must each vary by less than 1%. Changed main-route callback composition rejects
attribution; rows are never trimmed, split or reweighted to repair the mean.
Every terminal interval/body and final callback remains in totals and raw evidence.

Callback-entry interval effects are reported separately. The exact 1% body-span
control is below 1% in its entry intervals because those include more work/wait
than the body. These controls validate the stated body-span estimand; they do not
establish 1% whole-frame CPU/GPU critical-path overhead resolution. The wait-masked
control has a 2% body effect and exactly zero entry-interval effect.

The existing fixed-work observation separately retains complete wall duration,
callback count, time per callback and terminal/acknowledgement uncertainty in
complete-trial units. Its complete/main duration, endpoint, workload, operation,
completion, stall, missing/phase and I/O guards also apply to this experiment.
The CPU dose is nested inside callbacks; it is never a post-drain closure dose.
Preparation/gameplay/retirement, native phase close, writer drain, setup/tails and
scenario report construction remain. Combined finalization remains external and
is never allocated across repeats or added to overlapping spans.

A stable valid null can yield `null_observed`; a known positive whose envelope is
wholly below or at/above 1% can yield `cpu_span_sensitivity_observed`. These labels
characterize software sensitivity only. Threshold overlap, apparent speedup,
changed route mix, unstable bodies/windows, incomplete/failed work or evidence
faults remain inconclusive. Invalid/missing measurements remain unavailable/null.
No result qualifies hardware or revises a saved target verdict.

## Predeclared exact controls

The matching editor drives the real CPU/diagnostic/route ledgers and new
experimental assessor using hypothetical eligible H1/H2 contracts from the
established precision fixtures. It models 1,800 ticks, six main sections with
250 callbacks each and four terminal callbacks. Main body costs alternate
800/1,200 µs; terminal bodies are 1,000 µs. The reference mean is exactly
1,000 µs. Complete diagnostic callbacks retain another 8 µs and a 2 µs external
ledger tail. Setup is 200 µs and ordinary closure 1,055 µs, with a nested
400 µs writer drain. These are software clocks, not executed terrain/actor work.

All 27 labels run separately for H1/H2: 54 controls, 216 persisted CSV phases.

| Controls | Declared observation / expected result |
| --- | --- |
| Null | Zero request, no dose timestamps, zero added effect; null observed |
| Below / at / above | 5 / 10 / 20 µs per callback: exactly 0.5% / 1% / 2% body effects; sensitivity observed |
| Threshold overlap | Request 9 µs, actual positive repeats 9/11 µs; inconclusive |
| Wait masked | 20 µs body dose fits inside an existing modeled wait; entry intervals unchanged, only final body tail affects complete duration; body sensitivity observed |
| Count masking | Five extra callbacks in each positive main section; full-window time per callback falls while body effect stays 2%; sensitivity observed |
| Unequal reference counts | Five extra callbacks per main section in second reference; body means retain exact dose response; sensitivity observed |
| Changed route mix | 200 extra callbacks in each fast positive section; pooled mean shows apparent speedup despite known 20 µs dose; inconclusive attribution, raw per-section dose remains |
| Endpoint redistribution / acknowledgement duration | Move 500 µs from last main section to terminal intervals / add 500 µs to terminal intervals in second same-mode repeats; all rows and body means retained; sensitivity observed |
| Incomplete / missing / reordered / stalled / short | Existing workload/completion/order/smoke guards fail; inconclusive |
| Failed actor workload / failed operation | Actor deficit / unchanged real evaluator rejects modeled 751 µs upload against 750 µs limit; inconclusive |
| Missing dose / overlapping dose / missing body / invalid phase | Evidence unavailable/null, inconclusive |
| Complete-window / main-route duration drift | Add 450,000 µs ordinary closure / move 100,000 µs between main sections in second reference; inconclusive |
| Pooled body / main body drift | Add 30 µs to second reference bodies / transfer 20 µs between fast and slow bodies at unchanged pooled mean; inconclusive |
| I/O failure | Saved-evidence guard fails; inconclusive |

Except in the explicit wait-masked control, each dose contributes to the following
entry interval. The first interval has no predecessor and the final callback has
no successor interval: its dose still appears in the final body and complete
window. This verifies endpoint alignment rather than inserting an invented last
interval. Native phase closure precedes drain; no CPU dose occurs after drain.

Bounds are 54 control reports, 216 CSVs/64 MiB, 4 MiB control JSON and a 60-second
clock command. The CPU ledger keeps seven aggregate bins and one final callback,
no growing sample queue. Existing sixteen method, 26 route, 28 endpoint and
44 fixed-work control expectations remain required and unchanged.

## Real native CPU callback placement

A separate cloud-only application probe runs 32 actual `Node._process` callbacks
per repeat, reference/positive/positive/reference, in the matching editor and
exported release. Every callback hashes eight 4 KiB blocks as common work.
Positive callbacks synchronously call native SHA-256 update on the same 4 KiB
buffer until the 500 µs minimum dose is observed, at most 512 updates. They never
sleep, yield, dispatch a worker or perform I/O within the CPU bracket. A dose
above 50,000 µs, an unmet request, hash error or missing evidence fails placement.
The bracket includes hash setup/finalization and dispatch overhead; it is not a
pure hashing CPU-service estimate. A single native call is not preemptible.

The probe retains all 128 rows, previous/final complete callbacks, body and dose
clocks, actual update counts and SHA-256 digests. At most 32 rows await a phase
write; buffers/rows do not grow with run duration. Writer flush/close and report
construction occur after the final callback, and combined summary finalization
has its own external record. Each invocation is capped at 1 MiB saved evidence
and 60 seconds. No terrain/actor/1,800-tick workload runs in this microprobe;
native voxel operation evidence is explicitly unavailable. Its observed envelope
is descriptive even if cloud repeat noise is large. `placement_verified` proves
native work and serialized callback placement, not 1% hardware resolution.

Pinned-source verification:

- [Main loop](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/main/main.cpp): process callbacks precede rendering sync/draw and frame delay. Template path-override guards can clear `--script`; the probe uses the ordinary project entry with `--cpu-dose-probe` instead.
- [HashingContext](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/core/crypto/hashing_context.cpp): `start`, `update` and `finish` synchronously invoke native crypto.
- [CryptoCore](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/core/crypto/crypto_core.cpp): SHA-256 uses synchronous mbedTLS start/update/finish, with no worker, yield or I/O.

This placement does not guarantee that an added CPU dose extends the actual frame
critical path: it can consume slack before a wait/GPU dependency. An elapsed
duration ratio, render callback throughput and a synchronous CPU bracket describe
different quantities. Total-frame CPU service, GPU overlap/sensitivity, physical
presentation, frontier probe causal cost and shared instrumentation overhead
remain unverified/null. No new target-side run or full matrix is requested.

## Independent evidence checks

`tools/qa/cpu_dose.py` uses rational arithmetic and closed-form section totals,
then independently streams every saved CSV to reconcile order, all clocks,
previous/final callbacks, counts/body/dose sums, timing blocks, seven route bins,
phase/drain/acknowledgement/finalization and every declared guard. It independently
checks classifications and saved assessor null semantics. The real-probe reader
recomputes every digest from the saved update count with Python SHA-256, checks
that all native work lies inside its body, and reconciles actual callback and
external finalization accounting plus exact exported build identity. Formal orchestration rejects script errors,
nonzero exit, missing reports and I/O failures. Ordinary benchmark smoke must
retain CPU sensitivity `not_run` and contain no CPU dose ledger.

Cloud execution and candidate provenance are pending.
