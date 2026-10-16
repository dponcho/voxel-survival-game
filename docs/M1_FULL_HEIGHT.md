# M1 full-height and actual movement experiment

Prepared October 16, 2026 UTC. **Runtime verification pending; no profile or
target performance qualified.** This is a separate M1 fixture and route. Existing
H1/H2 outward commands, slab fixtures, thresholds and historical evidence remain.

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

## Evidence and checks

The full-height native fixture/support controls passed the first source run's
static checks. Native key
`028f3967c2a5e63d2a647adef67ad425efa601daa6c2799ae6ce698f336fd019`
is rebuilding in CI `38918074711`; this staging run does not contain the route.
The complete route's engine/export/candidate verification follows that build.
100 Python regressions pass in the cloud workspace, including full-height and
negative-coordinate demand, actual reversal/cross-axis work, data/mesh reload
and eighteen corrupted-observation cases. Runtime results remain pending.

Each run retains 4,322 observer rows at most / 16 MiB, ordinary frame/edit
ledgers, all three native phases and complete acknowledgement, writer drain and
report finalization. Original edits retain revisions and terminal outcomes;
unloaded data values and missing mesh fields remain null. Native vertical-voxel
samples and complete initial demand distinguish this fixture from a larger
air-only wrapper around the slab.

The independent reader checks the complete route fingerprint and work,
conservative per-frame coverage, actual edited data unload/reload, resources,
phase/frame union budgets and terminal timing. Post-package audit re-reads all
four runs and rejects twelve additional saved mutations; the earlier 38 remain.
The old 42 heavy workload contracts remain an independent unchanged baseline.

The observer is forensic and perturbs timing. Native closure, observer flush,
writer drain and final report costs remain recorded. No diagnostic-cost estimate,
HD 620 rendering/presentation result or shipping qualification follows from
headless timing. No laptop run is requested before a representative candidate
and the focused shipping-diagnostic pilot are ready. Active gates remain in
[NEXT_TASK.md](NEXT_TASK.md).
