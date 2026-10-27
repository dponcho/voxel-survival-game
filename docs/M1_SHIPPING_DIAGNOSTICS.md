# Shipping diagnostic inventory and finite pilot

Protocol `m1-shipping-complete-trial-1`; inventory `m1-shipping-inventory-1`.
This increment implements the adopted review policy. **M1 and target performance
remain unqualified.** The inventory and finite cloud pilot are implemented.
The completed pilot is **inconclusive**; the result below is not a request for
another laptop run. The protocol text retains its predeclared requirements.

## Inventory and comparison

The versioned executable inventory is
[`game/diagnostics/shipping_inventory.json`](../game/diagnostics/shipping_inventory.json).
Its exact bytes/hash travel inside the PCK, build identity and every complete
trial. The three explicit modes are `bare`, `shipping` and `forensic`. These are
opt-in representative fixture modes, not a global production-policy selection.

| Inventory | Bare | Shipping | Forensic companion |
| --- | --- | --- | --- |
| Collision/readiness, transaction revisions, native admission/enforcement clocks and whole-frame carry | on | on | on |
| Identical priority policy, 96 m visuals, 128 m data and one bounded 32 m directional lead viewer | on | on | on |
| Optional interval counters, one native/resource telemetry row per simulation second (72 maximum), bounded shipping summary write/flush | off | on | on |
| Native operation CSV, renderer query/detail JSONL and live diagnostic labels | off | off | on |
| Common external correctness observers: native lifetime/phase aggregates, collision timers, per-callback frontier/resource checks and CSV, edit submissions/ack, per-physics route/work/handover CSV, callback/lifecycle clocks and complete report | on | on | on |
| Admission selection trace and deep mesh-resource/vertical-voxel observer | off | off | off |

The common external observers perturb all measured modes. Their setup, hashing,
serialization, buffering, disk worker/drain and report costs are explicitly
retained. Required operational safety clocks are not optional diagnostic cost.
The estimand is **incremental declared shipping optional inventory**, conditional
on these common observers/operational work. It is not total instrumentation
overhead, CPU service time, GPU time or physical presentation. Selection, exact
mesh-resource identities and driver-deferred work are unavailable in this pilot.
The forensic companion checks actual mode dispatch/correctness; it cannot replace
coverage, edits, readiness or enforcement observations in the shipping path.

## Predeclared work and finite sequence

Every trial prepares a fresh full-height native fixture, `Y[-64,192)`, 32-cube
render / 16-cube data, one terrain worker, unchanged 720p Compatibility settings
and all existing limits. Real +X 156 m / -X 156 m / +Z 156 m movement takes 4,320
fixed 60 Hz ticks: 24 actor proxies / 103,680 updates, 256 rain instances, 288
4 Hz edits and 72 32 KiB proxy saves. Preparation and full terrain/preparation
retirement are retained, not replaced by a clipped slab or off-route clock.

One complete warm-up precedes one null quartet (bare/bare/bare/bare) and one
known-positive quartet (bare/bare+dose/bare+dose/bare). Only usable null **and**
positive controls append the predeclared shipping quartet
(bare/shipping/shipping/bare). Otherwise stop after nine trials. There is no
automatic retry, second sensitivity family or unchanged profile matrix.

The positive A0 complete duration sets one request before either positive B:
`ceil(0.02 * positive_A0_complete_usec / 4320)` microseconds per physics tick.
Immediately after each real fixed-work tick, synchronous native SHA256 updates
on a 4 KiB buffer run until that request is met, capped at 512 updates. The request
must be 1–2,000 µs; every actual span must meet it and remain at/below 50 ms.
Every tick retains placement clocks, actual duration, update count and digest;
the independent reader recomputes digests and sums, not just nominal labels.
There is no injected sleep/yield/I/O, terminal-only replacement or count-normalized
effect. The separately measured aggregate must really be above 1% and consistent
with nominal 2% work. Fixed-tick pacing may absorb this real cost: that is a masked
positive/inconclusive sensitivity result, never permission to report a passing zero.

The implementation/observer boundary was reviewed before execution against those
failure modes: idle absorption, callback-count cancellation, last-callback loss,
missing edit acknowledgement, missing writer/retirement closure and terminal
uncertainty. Matching native enforcement is unchanged; no native rebuild is needed.

## Complete boundary and method

Each trial uses **one end minus start**, from before optional setup/fixture
preparation through route end, final edit acknowledgement, native closure, all
three writer drains, terrain/preparation retirement, optional telemetry summary
serialization/flush/close and complete per-trial report serialization/flush/close.
Optional retained telemetry is disposed before this end, not charged to the next
bare trial's setup. Between-trial report retention/deep-copy and finite protocol
selection are declared common external harness work, bounded to thirteen records.
Separate setup, native close, writer drain and report spans remain evidence;
overlapping spans are never added. Five disjoint sections partition the total:
setup/preparation, +X, -X, +Z, and complete lifecycle tail. Repeat drift compares
these *matching* sections, never different sections within one route.

A terminal boundary marker cannot include its own write. Its start/end cost is
separately retained in the batch summary and conservatively expands the effect
range. Process launch/common scene initialization, warm-up, that marker and the
combined legacy/harness summary/identity audit are declared common external work,
not optional shipping features. The actual per-trial shipping and complete report
costs are inside the trial. Final harness serialization remains separately clocked
in `report-finalization.json`; it is not silently treated as zero diagnostic CPU.

For off durations A0/A3 and on durations B1/B2, the raw range is
`[min(B)/max(A)-1, max(B)/min(A)-1]`. Expand both ends by (a) the larger sum of
absolute matching-section repeat differences, divided by `min(A)`, and (b) the
largest off+on terminal-marker cost, divided by `min(A)`. Report the pooled
complete-duration point effect, callback counts and raw sections separately.
This conservative repeat envelope is **not a statistical confidence interval**.
Neither callbacks nor physics ticks divide elapsed cost.
The implementation subtracts exact whole-microsecond durations before division,
and uses an integer ceiling for nominal dose requests. The independent exact-
rational oracle rejects rounding-induced verdict changes; no epsilon relaxes the
1% gate or the positive-control overlap.

Null must contain zero with width below 1%; both quartets need matching-section
drift below 1%. Positive must have a lower bound at/above 1%, an actual dose above
1%, and an envelope containing/overlapping its measured dose range. After valid
controls: upper below 1% passes; lower at/above 1% fails; overlap, a negative pooled
effect, unresolved drift or missing/failed work/I/O/operation evidence is
inconclusive. Missing measurements never become zero. Cloud/headless results
cannot qualify target hardware; even a target-shaped runtime result requires
independent review and leaves full M1 unqualified.

On inconclusive, **stop and retain the shipping gate as unqualified**. Record the
observed resolution and obtain one explicit supported measurement, repetition or
threshold policy decision before any further pilot. Do not add a calibration
branch merely to obtain a passing result.

## Verification and player handoff

Pure Python exact-rational edge/fault controls cover thresholds, unequal callback
counts, repeatable varying routes, cancelled section drift, masked real positives,
missing work/dose/boundaries and terminal uncertainty. Matching-engine controls
are independently recomputed, not accepted by their runtime `passed` label.

Cloud verification retains the entire existing integration/package/native suite.
A separate bounded Windows job verifies the published ZIP/PCK/build/template and
inventory, exercises all three real modes with matching editor and release, then
runs the single finite release pilot. An independent saved-file reader reconciles
every actual pose/work row, callback, original edit submission, operation aggregate,
boundary/drain, telemetry switch and native dose digest. Saved-file mutations must
be rejected. A second read-only downloaded-artifact audit precedes handoff. It runs in an
isolated Linux job after the Windows checks: download the published candidate,
original export/native/pilot evidence, verify the transferred editor files byte
for byte and reproduce all saved verdicts, counters and mutations without an
engine or compiler. This also preserves verification through an executor disconnect.

The prior complete export job took 1,808 s, including 1,262 s of terrain checks.
Cheap dispatch/rational controls now run first; the existing 72 s editor/bare case
also runs before that long suite and its original raw files are transferred into
the final seven-folder audit. It is not an extra trial or a removed test. This
moves about 80 s into the 35-minute export allowance (about 31.5 minutes total on
the observed runner), removing the wait for the full suite before the first real
pilot-path/reader check. All preceding suites remain; no native rebuild is added.

The title has one focused pilot button, fixed at 32-cube/one worker regardless of
the legacy dropdown. No installation, script entry or tools are required. Cancel
preserves partial unqualified evidence; reports are never uploaded automatically.
Only after candidate/control review should one relevant target pilot be requested.
The old flatness/calibration outputs and historical failing evidence are unchanged.

## Result

CI [38985239110](https://github.com/dponcho/voxel-survival-game/actions/runs/38985239110)
used implementation `e208cbbbc9ded194d80e38a038a528ecf45b25a1` and exported build
`5a5012534afdc64c444e148b2a4a92804650e570`. Static, qualified native binaries,
export, all existing integration/package checks and the first downloaded-player
audit passed. Six editor/release single-mode companions completed. The full
release pilot completed its predeclared nine trials and did not append the
shipping quartet because its controls were unusable.

| Trial | Complete seconds | Process callbacks | Actual added work seconds | Measurement validity |
| --- | ---: | ---: | ---: | --- |
| Warm-up | 77.461136 | 10,441 | 0 | valid |
| Null A0 | 77.762452 | 10,439 | 0 | operation limit failed |
| Null B1 | 77.452278 | 10,440 | 0 | valid |
| Null B2 | 77.761903 | 10,439 | 0 | valid |
| Null A3 | 77.452110 | 10,439 | 0 | valid |
| Positive A0 | 77.762781 | 10,439 | 0 | valid |
| Positive B1 | 77.446024 | 10,438 | 1.605522 | operation limit failed |
| Positive B2 | 77.756037 | 10,438 | 1.602053 | valid |
| Positive A3 | 77.443335 | 10,438 | 0 | valid |

Null A0 preparation had a **1,185 µs upload**; positive B1 retirement had a
**1,041 µs deletion**, against the unchanged 750 µs limit. All other recorded
per-trial checks passed, including 4,320 actual ticks, 288 submitted edits,
72 saves, 103,680 actor updates, coverage/readiness, resources, closure and drain.
These failures invalidate both control quartets. They are not waived as cloud
noise, and the cloud observations do not establish a target-machine failure.

The known-positive trials also demonstrate the expected sensitivity problem:
about 1.60 s of independently verified native SHA work did not produce a similar
whole-trial elapsed increase. The observed durations are descriptive only; the
invalid control samples cannot support an overhead bound. Fixed 60 Hz route
pacing can absorb added work inside idle time. There is no measured shipping
effect, valid below-1% bound or target qualification.

The original CI pilot job failed before its saved-file audit because it reused
a helper that requires every measurement to pass. The subsequent **QA-only**
correction separates evidence integrity from measurement validity: native
failures must agree with all saved validity flags, remain listed as failures,
and force an inconclusive estimate. Missing work, corrupt files, engine errors,
unexpected exits and fabricated passes still fail verification. Cross-platform
replay normalizes only the missing-file fault's `[WinError 2]`/`[Errno 2]` wording.
It compares every other saved field exactly. The original failed CI remains red;
no passing runtime result has been substituted.

The original downloaded evidence and candidate are independently rechecked in
Codex Cloud without executing an engine. Seven folders, all 24 method controls,
50 preceding saved faults and 12 shipping saved faults are checked. The committed
[saved audit record](evidence/m1-shipping-saved-audit-2026-10-17.json) retains
the exact candidate, results, operation failures and reader identities. The QA
correction changes no game/native source or inventory bytes and needs no new
export or repeat of the runtime pilot.

The retained portable candidate is
[artifact 12082779545](https://github.com/dponcho/voxel-survival-game/actions/runs/38985239110/artifacts/12082779545):
30,170,627 bytes; inner ZIP SHA256
`3e9241c46edca867fc0ac0aa7306125a420539f18b80d96b54882c61eb88b175`.
This is an inspected **unqualified research candidate**, not a target handoff.
The immutable original pilot evidence is
[artifact 12084093542](https://github.com/dponcho/voxel-survival-game/actions/runs/38985239110/artifacts/12084093542).

**Stop v1 calibration here.** The October 17
[policy decision](M1_DIAGNOSTIC_COST_POLICY.md) now explicitly adopts raw
whole-process CPU-cycle demand for the 1% optional-cost gate, with complete
elapsed impact and operational gates retained separately. V2 is unimplemented;
the immediate next increment is counter capability, not another pilot.
The decision required by this result was a written policy on an
observable cost that cannot be hidden by fixed-tick idle time, while retaining
complete-lifecycle accounting and paced frame checks. Recommended direction:
separate busy execution cost from elapsed player-visible impact. That estimand
change is now explicit in the linked decision. More identical repetitions do not
resolve the demonstrated masking mechanism. Keep the 1% threshold and existing operation gates unchanged;
do not implement another injection family or request a laptop pilot yet.
