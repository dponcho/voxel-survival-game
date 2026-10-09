# M1 first moving-frontier boundary replay

This is a bounded cloud correctness correction, not HD 620 qualification, a
complete-route coverage pass, a fog change or a timing/overhead measurement.
All existing frontier/operation/evaluation thresholds and qualification flags
remain authoritative. No world generator, content ID or save semantics change.

## Captured failure and cause

`tests/fixtures/m1_frontier_boundary.json` preserves public release evidence
from CI 37804090619, evidence artifact 11562713891, build
`62a8da6e8d1fc9b81195b6b6707d1b4bba3c446b`. Its H1 CSV SHA-256 is
`1ce3505c3ec27f9755125bd83e692633ccd49959200bfcc31bec633b8a29f35d`.
Independent streamed source reconciliation checks frames 134/135/136, their
camera poses, nearest region `[7,0,0]`, missing/missing/pending states and exact
saved distances. The first alarm occurs at x = 16.0666809082031: region x = 7
begins at 112 m, leaving 95.9333190917969 m before unready coverage, inside the
unchanged 96 m fog boundary. Both public 16³ worker profiles show this first H1
and H2 boundary. These are public cloud observations, not private target data.

Pinned Voxel Tools `2ac9f5f8a8219bf499314cc0fad54ffc47df908f` plus the
existing `m1-admission.json` adaptation compute complete world-space viewer
demand. `VoxelTerrain::process_viewers` requests a mesh only when its cell first
intersects that demand; requesting does not mean a mesh has been submitted.
The data-only 128 m viewer cannot produce visual meshes. Thus this seed is
genuinely late visual demand, not a reason to count missing/pending geometry as
ready or to shrink the conservative required-region scan.

## Small correction and bounds

`m1_frontier_preparation.gd` owns exactly four auxiliary `VoxelViewer`s, each
with 1 m radius, visuals on and triangle collisions off. Only 16³ H1/H2 +X
benchmark routes enable them, including matched probe-off/on and calibration
phases equally. Normal/32³/exploration routes are unchanged. They prepare the
next +X column, the two fixed fixture surface rows (-1/0), and the route's two
nearest Z cells. They do not change required visual radius, camera, fog,
readiness, actor/edit/storage commands, simulation, workers or native admission/
result/submission budgets. Extra mesh generation/submission is real work and
remains in preparation/gameplay/retirement and diagnostic accounting.

The base 16³ demand is at most 13 × 13 × 3 = 507 regions. The four preparation
cells give at most 511, below the existing 512 cap. Their one-data-cell meshing
halos, clipped to the same finite fixture bounds, fit wholly inside existing
128 m data demand. They add no new data envelope, worker pool or result queue.
An independent geometric oracle tests fractional/negative positions and the
full halo, rather than duplicating the production position formula alone.
This policy is not enabled for 32³: a next-column preparation halo there is not
generally contained in the existing data envelope.

The helper retains its previous process pose for one engine processing
opportunity when the base viewer crosses a column boundary. Pinned terrain
code applies each viewer's old/new references sequentially; an immediate
retarget could drop the old column's last reference before base demand acquires
it. Pinned Godot `ed1daf0bf001b61586d9930840f2f1394092c079` SceneTree processing
flushes transform notifications and executes ordered node callbacks. The
cloud replay checks real submitted meshes throughout handover, not a delay
declared to imply readiness. Helpers are released during retirement and on
early finish/cancellation; native work and renderer retirement must drain.

## Predeclared replay and independent checks

The internal `--frontier-boundary-replay` entry runs in the matching editor and
packaged release. Each invocation runs baseline/corrected with one and two
workers. It settles the identical fixture at the saved before pose, crosses to
the saved alarm pose and observes before another native processing opportunity.
Baseline must have no submitted target and must reproduce the missing-region
alarm. Corrected must already have submitted all four preparation targets and
pass the **unchanged** native required-region scan/analytic assessment. Sixteen
subsequent observations must retain coverage while preparation hands over to
base demand. Base demand must eventually submit even without preparation.

A farther, deliberately unprepared move must still fail the same scan. Missing
terrain/camera measurements stay unavailable/inconclusive with null fields.
Confirmed-empty regions remain part of actual native evidence; cancellation,
native drain and resident/admission bounds are checked. This microreplay does
not pretend to run H1/H2 actors/edits/storage or certify their full-route timing:
existing ordinary/matched runtime smokes and edit/operation tests still run.

Bounds per invocation: four cases, 80 retained observations, a 128-row cap,
1 MiB JSON cap, no unbounded row queue and 60-second timeout per settlement/
drain inside the 600-second orchestration deadline. Settlement sampling only
retains aggregate peaks. `tools/qa/frontier_boundary.py` independently verifies
saved order/phase boundaries, rational fog arithmetic, nearest-AABB distances,
duration-independent readiness, reference handover, bounds, null semantics,
candidate identity and failure retention. Python mutation regressions reject
missing/reordered/stalled/failed evidence, passing zeros, lost readiness,
changed geometry/handover, undrained work and I/O failures.

## Verification status

Implementation `7c103af1c16d328b113a7c3cbf3666b20d630990` passed
[CI 37811968141](https://github.com/dponcho/voxel-survival-game/actions/runs/37811968141)
in all three jobs: 73 Python regressions, five native sanitizer suites,
matching-engine qualification/import, actual editor/release replay, every
existing control/runtime/profile/smoke, DLL audit and two fresh offline
extractions. No engine was installed, compiled or run locally.

Independent downloaded review reconciles eight native cases/160 observations,
the three exact public seed rows, baseline missing alarms at 95.9333190917969 m,
already-submitted corrected targets, sixteen handover observations per case,
confirmed-empty counts, retained unprepared failures and unavailable/null inputs.
Corrected cases peak at 511 meshes versus baseline 507; all have 867 data blocks,
no native overloads and complete drain. In ordinary one-second 16³ cloud smokes,
H1's 11 and H2's 23 exposed samples become zero for both worker counts. Simulation/
actor ticks, edits and proxy saves match; no first target is missing/pending.
This is not a four-minute route or target pass. All ten ordinary folders reconcile:
98 scenarios, 284 native phases, 37,390 operation rows, 12,883 frame rows and 94
edit events, including final callbacks and external finalization. Old controls,
thresholds and false qualification flags remain; calibration stays inconclusive.

Current [player 11566261601](https://github.com/dponcho/voxel-survival-game/actions/runs/37811968141/artifacts/11566261601)
exports `fcc317863e32e6787430880b493b53541fe0db9f`; build and implementation share
tree `803e845a251c657097582ce4e524d85e47ce89f6`. Portable ZIP SHA-256:
`b39bbe798c7eb7b464bc8f7593cae9e7027a94af0752413e091291daaeb11735`.
Archive/PE/PCK identity, all 70 entry MD5s, exact native templates, eight self-test
reports and 38 PE imports independently verify. Native inputs remain
`11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
An incomplete initial evidence download was rejected; the completed retry matches
GitHub's published size/digest and CRCs. See [the verification record](evidence/m1-frontier-boundary-cloud-2026-10-08.json).

The correction only addresses this demonstrated first boundary. Other frontier
gaps, H2 upload/operation failures, frame pacing, whole-route qualification,
GPU/presentation, hardware noise and shared instrumentation overhead remain
open unless separately demonstrated. No new target-side run is requested.
