# M1 full-height and actual movement experiment

Completed October 16, 2026 UTC. **Cloud correctness passed; M1 and target
performance remain unqualified.** Directional preparation reduces 521 coverage
alarms to zero in both editor and release runs. All 288 edits submit, all twelve
native phases pass their operation guards and the native queues fully drain.
This is a separate M1 fixture and route; existing outward H1/H2 workloads remain.

## Verified candidate

- Implementation: `5d84c4917878146ec4cba34c347157bccbc1d520`.
- Exported merge/build: `4e028d5b1cf762596d2da809385c9135367acfa7`; its tree is
  exactly the implementation tree, `5ef9e256360de3f7903b5eabae310db6ef55d596`.
- [CI 38922744175](https://github.com/dponcho/voxel-survival-game/actions/runs/38922744175):
  all three jobs pass, including 100 Python regressions, six native sanitizer
  suites, matching editor/debug/release qualification, all four new processes,
  preceding integration/profile/control checks and offline extraction tests.
- [Portable Windows player](https://github.com/dponcho/voxel-survival-game/actions/runs/38922744175/artifacts/12062934427):
  inner ZIP 30,142,671 bytes, SHA-256
  `fe3db7bcf2b92ae7ffdab312d5ca7f2ca3a2c1e4082015d4699a7d2230be1fa8`;
  artifact expires `2026-11-15T17:47:05Z`.
- [Saved evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/38922744175/artifacts/12064141035)
  and [native qualification evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/38922744175/artifacts/12062385706).
- Native key:
  `028f3967c2a5e63d2a647adef67ad425efa601daa6c2799ae6ce698f336fd019`.
  [CI 38918074711](https://github.com/dponcho/voxel-survival-game/actions/runs/38918074711)
  compiled and qualified the editor and both templates from native extension
  `3256632`. The final run reused those exact binaries and requalified all three
  against the exported game identity. The staging run alone did not validate
  the new route.

Published-download and separate read-only audits verify archive hashes/paths/CRC,
all 82 PCK entry MD5s, eight self-tests, 38 PE imports, source/native identity and
the complete saved comparisons. All 26 preceding, twelve reversal and twelve new
saved mutations are rejected. The separate audit reproduces every numeric,
verdict, phase and witness field; only the two deliberately missing-file
mutations' OS error text/temporary paths differ. No engine or compiler ran locally.

## Declared case and compatibility

Native fixture 3, `m1-full-height-1`, spans `Y[-64,192)`, with surface height
64–68, flat intersecting travel lanes at Y=64, solid bottom layers and tunnel
levels at -48, -16, 16 and 48. It exercises solid terrain below the old slab.
Fixtures 0–2 and content IDs remain unchanged; this is not a released generator
or save migration. The existing 64-position temporary edit overlay remains.

One 32³/one-worker candidate, four fresh processes: editor/release × directional
preparation off/on. Both use opt-in native geometric priority with admission
tracing disabled. This does not select a production profile or change FIFO as
the ordinary default.

| Command | Duration | Actual horizontal movement |
| --- | ---: | --- |
| Start `[10,72,10]`, settle on Y=64 support | Preparation | Complete visual/data demand before measurement |
| Leg 1 | 1,440 ticks / 24 s | +X 156 m at 6.5 m/s |
| Leg 2 | 1,440 ticks / 24 s | -X 156 m, revisiting genuinely evicted mesh/data |
| Leg 3 | 1,440 ticks / 24 s | +Z 156 m |

Every case retains 4,320 fixed 60 Hz ticks, 103,680 actor updates, rain, 288 due
border edits and 72 proxy saves. Edits snap X/Z to 32 m columns, Y=70 and Z
offset 13: eleven distinct positions, below the existing 64-position bound.
Data remains 16³, triangle colliders disabled and the four-step catch-up cap
unchanged. The route observer verifies actual player coordinates at every tick,
not only camera turns or requested coordinates.

## Demand and preparation

Required visuals/fog stay 96 m and the base data viewer stays 128 m. At the
interior altitude the 32³ base cube requests 343 mesh regions, rather than the
old slab's 98. The corresponding unchanged 16³ policy would need 2,197 against
the 512 cap; it is not added to this runtime matrix.

The corrected case adds one 96 m preparation viewer shifted 32 m along the next
actual movement direction. It retains the previous process pose for ownership
handover. The initial union is 392 mesh regions; opposing/cross-axis handovers
remain within the declared 448-region bound and unchanged 512 cap. The actual
128 m data-viewer/mesh-halo/preparation union is measured against 8,192 data
blocks, with retirement bounded at 768. No hidden height/radius reduction or
larger queue/result/upload allowance is allowed.

The baseline keeps preparation disabled; any coverage, edit or operation
failure remains evidence. The corrected case must have zero required coverage
alarms/readiness stops, all 288 original edits submitted within 100 ms p95 /
200 ms maximum, complete terrain-operation guards, bounded resources and full
drain. An implementation failure requires a narrow correction or an explicit
contract/profile decision before expanding the experiment.

## Measured comparison

| Executable | Preparation | Coverage alarms (+X / -X / +Z) | Submitted / 288 | Edit p95 ms | Edit maximum ms | Bounded acceptance |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Editor | Off | 521 (172 / 176 / 173) | 288 | 56 | 110.593 | Failed: coverage |
| Editor | On | 0 (0 / 0 / 0) | 288 | 56 | 96.875 | Passed |
| Release | Off | 521 (172 / 176 / 173) | 288 | 56 | 110.663 | Failed: coverage |
| Release | On | 0 (0 / 0 / 0) | 288 | 56 | 97.132 | Passed |

Every case has zero movement-readiness stops, rejected edits, superseded edits,
timeouts and unavailable edit outcomes. Actual movement settles onto voxel
support at Y=64.001 and ends at approximately `[10,64.001,165.99945]`.
The independent route fingerprint is `1241625024` in every case. Edited data and
previously loaded mesh regions genuinely unload on +X and reload on the return;
the native overlay's original values survive that reload.

Baseline peaks are 343 resident meshes / 4,624 data blocks; preparation peaks
are 392 / 5,104, within the declared 448 preparation bound and unchanged
512 / 8,192 caps. Generation/mesh/result queue peaks are 48 / 4 / 4. Retirement
high-water is two while travelling and at most 211 across complete retirement;
all queues and retirees drain, with zero overloads.

All twelve preparation/gameplay/retirement phases pass: maximum individual
upload/deletion/data-application spans are 154 / 711 / 381 microseconds, peak
native-frame terrain charge is 1,744 microseconds within the heavy 2 ms budget,
and maximum individual upload is 143,360 bytes. No cumulative time/payload
overrun occurs. These are headless cloud observations, not target timings.

## Evidence completeness and retained limits

100 Python regressions include full-height and negative-coordinate demand,
actual reversal/cross-axis work, data/mesh reload and eighteen corrupted-observation
cases. Native sanitizer controls include all four fixtures' bounded geometry
and an independent 16/32-cube geometric admission oracle.

Each run retains 4,322 observer rows at most / 16 MiB, ordinary frame/edit
ledgers, all three native phases and complete acknowledgement, writer drain and
report finalization. Original edits retain revisions and terminal outcomes;
unloaded data values and missing mesh fields remain null. Native vertical-voxel
samples and complete initial demand distinguish this fixture from a larger
air-only wrapper around the slab.

The four runs retain 17,288 observation rows / 38,185,414 bytes, 41,761 frame
rows and 44,764 operation rows. Individual observation files are 9.39–9.71 MB,
below their 16 MiB cap. The independent reader checks the route fingerprint and work,
conservative per-frame coverage, actual edited data unload/reload, resources,
phase/frame union budgets and terminal timing. Post-package audit re-reads all
four runs and rejects twelve additional saved mutations; the earlier 38 remain.
All 42 preceding heavy workload contracts match the durable baseline. Ten earlier
ordinary folders / 98 scenarios / 284 phases reconcile. Across all 42 CSV-backed
folders, the complete ledger covers 380 native phases / 160,089 operation rows.
Two broader research phases retain failed deletion measurements:
`CAL-H1-closure-2` preparation, 753 microseconds, and `CAL-H2-closure-2`
preparation, 794 microseconds. The five failures in the preceding
[ordinary admission record](M1_ORDINARY_ADMISSION.md) remain historical failures;
passing this representative fixture does not erase them or qualify target budgets.

Measured final CI stages: static 100 s, cached native qualification job 50 s,
Windows regressions 88 s, import/export 130 s, full integration 1,262 s,
packaging/offline checks 127 s and published-download audit 76 s. The source
native compilation itself took 7,545 s. No suite was pruned.

The observer is forensic and perturbs timing. Prepared scenario assessments
remain inconclusive under the unchanged legacy 1% diagnostic guard; the shipping
gate remains `not_run`. Headless draw/triangle counters are zero and do not
qualify rendered geometry or GPU limits. Native closure, observer flush,
writer drain and final report costs remain recorded. No diagnostic-cost estimate,
HD 620 rendering/presentation result or shipping qualification follows from
headless timing. No laptop run is requested before a representative candidate
and the focused shipping-diagnostic pilot are ready. Active gates remain in
[NEXT_TASK.md](NEXT_TASK.md).

## Decision and next bounded task

The full-height/directional cloud experiment is complete. Keep priority and
directional preparation opt-in; no production profile is selected. Define and
implement the shipping-versus-forensic diagnostic inventory and the adopted
matched fixed-work complete-trial method. Prepare one focused null/known-positive
target pilot with complete boundaries and preserved operational safeguards.
Validate its controls and exact Windows candidate before requesting a laptop
run. Do not repeat this completed four-case matrix or begin another calibration
family by default. Target viability, renderer/presentation/deferred accounting,
retention and qualification repeats remain open; M2/content expansion stays gated.
