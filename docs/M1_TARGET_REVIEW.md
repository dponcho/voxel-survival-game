# M1 target report review — September 25 candidate

Reviewed 2026-09-26. Milestone status: **blocked; target not qualified**.
All five supplied runs completed, but completion is not a performance pass.
M2 implementation remains gated. No acceptance threshold or runtime setting was
changed during this review, and no new engine build was launched.

## Identity and evidence integrity

The standalone baseline ZIP and the four comparison folders all identify game
commit `6874b8809094d22b33e05c60ef61c2e1c333494a`, matching the screenshot's
`6874b8809094` build label and [candidate run 36183549961](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961).
The screenshot establishes the rendered title/build screen; it does not show
terrain or establish visual correctness during the workload.

Executable SHA-256:
`bf56bd5adfbff3f0caba0eefb0e694c7e5cb0c7b4431d1b3fb404238633f996a`.
PCK SHA-256:
`dfb677a9405f0770d04de89bb1231c330a602c2d8db8eb6c1890b1675e538d23`.
Both match files read directly from the previously verified portable player ZIP.
The native identity is recorded in [M1_EVIDENCE.md](M1_EVIDENCE.md).

Every report identifies the i7-7600U, Intel HD 620, four logical processors,
8,422,072,320 usable physical RAM bytes, Windows `10.0.22000`, OpenGL driver
`3.3.0 - Build 30.0.100.9865`, AC power and approximately 60.0314 Hz refresh.
Requested and reported window sizes are 1280 × 720, render scale is 1.0, radii
are 96/128 m and actual worker counts match each selected profile. Initial
hardware/configuration snapshots do not prove foreground focus or AC state
throughout each run; power-profile and thermal attribution are unavailable.

[The machine-readable review](evidence/m1-target-2026-09-25-review.json) preserves
input basenames, file sizes and SHA-256 hashes, reported counters/reasons and
independent CSV aggregates. It excludes absolute input paths. All **1,682,025**
recorded CSV rows were checked for sequential frame numbers, sample count,
average fps, maximum interval, deadline misses and shared peak counters; they
match their summaries. Exact CSV percentiles are retained separately from the
game's upward-rounded 0.01 ms histogram percentiles. A/B-off CSVs intentionally
contain headers only, so their interval distribution cannot be independently
reconstructed. Original user reports remain the raw evidence; they were not
modified or uploaded wholesale.

## Observed results

The range below covers each run's N1/N2/H1/H2/N3/R1 scenario averages; it is not
a claim about minimum fps or final survival gameplay. All results use M1 proxies.

| Run / render block / workers | Scenario average fps range | Worst gameplay interval (ms) | Gameplay deadline misses | Paced misses / samples | Peak private / working set (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Standalone 20:22 / 32 / 1 | 225.7–264.5 | 15.641 | 0 | 3,306 / 7,201 | 179.16 / 232.92 |
| Comparison 21:10 / 32 / 1 | 233.6–265.4 | 15.819 | 0 | 3,342 / 7,202 | 179.06 / 226.70 |
| Comparison 21:34 / 16 / 1 | 241.6–266.2 | 15.390 | 0 | 3,408 / 7,201 | 180.36 / 236.34 |
| Comparison 21:58 / 32 / 2 | 232.2–268.6 | 17.456 | 1 (N2) | 3,396 / 7,201 | 181.09 / 235.57 |
| Comparison 22:22 / 16 / 2 | 239.7–262.3 | 13.720 | 0 | 3,363 / 7,201 | 180.01 / 237.23 |

Across these runs, gameplay p99 is at most 6.25 ms. There are no recorded
integration failures or movement-readiness stops. Each N2 accepted 360 edits,
each H2 accepted 960, and both H1/H2 travelled 1,560 m over 240 simulated seconds.
N2/H2 recorded 180/240 proxy storage writes. R1 checked two retained edited
positions and reported queue recovery in 0.013655–0.044842 seconds. These proxy
writes do not test durable saving.

Observed geometry stayed within the relevant caps (at most 213 draws / 188,726
triangles); resident data/render regions peaked at 768/432. The simultaneous
generation-plus-mesh queue peaked at 52 and the result queue at 4. GPU resource
estimates peaked at 55.20 MiB, excluding unreported driver allocations. Process
memory stayed comfortably below the ceilings. These checks do not establish all
allocation-pool, driver-retention, edit-visibility or long-soak gates.

## Why M1 is not qualified

1. **Native operation timing is not scoped to measured phases.** Recorded
   lifetime upload maxima range from 1.829 to 12.320 ms, above the 0.75 ms
   individual-operation target. Deletion maxima range from 1.603 to 2.655 ms.
   Every upload maximum already exists in that phase's `native_start` snapshot;
   all above-budget deletion maxima also predate their measured phases.
   [The native counters](../native/sandbox_world/godot/m1_hooks.h) are lifetime
   maxima, while [the scenario evaluator](../game/scripts/benchmark.gd) tests
   their absolute final values. Preparation/retirement therefore contaminates
   per-scenario failure labels. Unchanged maxima cannot prove that no later
   operation exceeded 0.75 ms, and subtracting two maxima cannot recover a
   phase maximum. Preserve these failures; add scoped measurement before
   deciding which gameplay operations need optimization.
2. **Diagnostic overhead is unresolved.** Directly timed diagnostic work occupies
   2.61–3.22% of gameplay interval time (up to 4.18% in diagnostic phases).
   Every A/B result is inconclusive because baseline drift is 2.09–5.35%, above
   the 1% qualification tolerance. Negative added-cost estimates are noise,
   not proof of zero overhead. The timed section also omits some UI work.
3. **Frame pacing still needs attribution.** The 32/2 N2 run has a 17.456 ms
   interval against 16.667 ms. Three comparison warm-ups each contain one miss
   (18.373, 19.903 and 20.001 ms); retain first-use evidence separately. Paced
   intervals peak at 21.234–22.305 ms with thousands of raw deadline misses.
   Physical presentation timing is unavailable. Do not discard these misses
   as refresh noise or blame the game/OS without evidence.
4. **Several required observations are absent.** The reports lack per-edit
   visual acknowledgement latency, a measured fog/frontier relationship,
   per-frame upload/deletion payload-and-time traces, complete allocation-pool
   accounting and driver-deferred deletion attribution. Five open/close-cycle
   retention and final qualification repeats are also outstanding. No missing
   metric is converted to a zero or a pass.

All recorded scenario outcomes are `failed`, largely because the lifetime native
maxima are reused in every phase. The reviewer outcome is **not qualified**;
the attribution defect is neither evidence of poor sustained fps nor permission
to override the gate. 16³/one worker is a useful next comparison candidate, but
one ordered comparison cannot certify a winner or establish a need for two
workers. Keep the current default until a qualified comparison supports a change.

## Next bounded M1 task

Correct diagnostic attribution and overhead before M2: separate loading,
gameplay and retirement measurements; retain lifetime counters while adding
phase-local maxima and bounded per-frame upload/deletion totals and event context;
measure end-to-end edit visibility; make outcome text distinguish completion
from qualification; and obtain a stable overhead/pacing comparison. Preserve
thresholds, workloads, old reports and failing fixtures. Do not subtract maxima,
remove costly required probes without equivalent evidence, or reduce simulation.

Any necessary native instrumentation change requires matching editor/templates,
cloud integration/package checks and a new exact-build laptop report. First
complete the patch and identify the changed native key; reuse unaffected outputs
where valid. Do not rebuild merely to publish this evidence or change requirements.
Review corrected measurements before requesting another four-profile run or the
three final repeats. M2 has not been implemented in this continuation.
