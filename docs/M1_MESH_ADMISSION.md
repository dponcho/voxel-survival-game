# Bounded native pending-mesh admission experiment

The continuous 600-tick H2 replay preserves a concrete cloud failure: lateral
cells `(7..10, -1/0, -1)` are queued with one visual owner and no submitted
revision/resource after +X handover, then enter the conservative 96 m boundary.
The first raw alarm is tick 61, beyond the prior one-second smoke. Pinned fixed-LOD
`VoxelTerrain::process_meshing` consumes the pending vector in insertion order
before assigning worker priority. The existing four-task admission break retains
the unadmitted suffix. This suggests an admission-order cause; it is not yet a
demonstrated causal correction. See [the exact baseline](M1_FRONTIER_TRAVEL.md).

Predeclared comparison: fresh FIFO and priority processes, each executing the
same production 600 fixed 60 Hz ticks, H2 fixture/camera, 24 actor/256 rain proxies,
40 due edits and ten proxy saves, in editor/release with one/two workers. Loading
uses FIFO in both. The optional priority intervention applies only during
gameplay/acknowledgement: current loaded replacement revisions first in FIFO order,
then never-submitted visual requests by squared distance to their closed render
box from the actual camera, then remaining work in FIFO order. Equal distances
retain original order. This reorders only the existing bounded pending vector;
it changes no demand, revision, mesh/resource ownership, worker/admission cap,
simulation, safety, world/save content, fog/radius, geometry or threshold.
The production default remains FIFO while this intervention is experimental.

The new native trace records every pending vector before selection, exact decimal
desired/submitted revisions (null means not submitted), origin, permutation,
actual admission prefix and measured task load before each admission, monotonic
decision brackets and phase identity. The independent reader reconstructs the
geometric minimum, replacement precedence, FIFO ties and complete permutation;
it joins exact preparation/gameplay/retirement CSV boundaries. Records during
closed-phase writer gaps retain phase zero and must lie between the adjacent
exact native endpoints; priority is disabled before phase closure. No such row
is discarded or attributed to a closed native phase. The reader retains every
terminal frame/edit/operation, final callback, writer drain and combined report
finalization through the existing travel reader. Both modes retain observation
and all existing assessment outputs/qualification flags.

For each lateral cell, the reader joins its exact admitted desired revision to
actual native submission observations and the last outside/first inside 96 m
samples. Submission time remains a bracket between admission/last unready and
first current observation. Current coverage before entry is proven when the
last outside and first inside samples are current; an inside unready sample
remains failed. A first ready sample coincident with first inside remains null
for ordering within that interval. These are software submission bounds, not
physical presentation or pixel visibility.

Bounds: 512 pending candidates, 64 native trace records, fixed trace storage at
most 2 MiB, fixed 512-entry index/distance scratch and no added worker. Native
selection uses bounded index sorting, not a world scan or a new job queue. Per
process, the additional trace is streamed synchronously: at most 4,096 rows /
32 MiB and less than 64 KiB per row. Existing 4,096-row/32 MiB travel observation,
native operation ring, 128 operation-row buffer, bounded disk/edit queues and
file limits remain. Native overflow, invalid state, missing/null measurements,
I/O errors and all guard failures remain failures. The 600-second command timeout
and existing loading/gameplay/drain limits remain. Trace finalization after the
combined report is separately bracketed, with its terminal record write excluded;
overlapping wall intervals are never added.

Acceptance: exact matched work and current accepted revisions/resources at all
four handovers; independently verified native selection/ranks/budget boundaries
and complete drain. Establish whether FIFO admits farther fresh regions ahead
of a nearer queued lateral target and whether that target still becomes unready
inside 96 m. A successful bounded correction additionally needs zero actual
travel coverage alarms and zero lateral unready observations in each priority
run. A remaining alarm stays failed and identifies the next measured cause;
cloud functional success never changes that verdict. No production scheduling
change is adopted solely from a hypothesis or timing improvement.

Controls reject unavailable/inexact revisions, duplicate/missing/reordered pending
work, invalid origins, unsupported geometry, mode escaping preparation/retirement,
incorrect geometric/FIFO order, bypassed four-task admission, lost clock/phase/
finalization boundaries, truncated/overflowed/I/O evidence and suppressed guards.
Native sanitizer controls independently compare exhaustive geometric minima at
negative coordinates, equal-distance ties, exact 512/513 bounds, invalid inputs
and ring saturation. All earlier replay/control expectations remain required.

Trace copying/formatting, sorting and synchronous file I/O perturb wall timing.
Measured decision spans are elapsed software observations, not CPU service,
render throughput, per-frame CPU/GPU critical-path cost or shared diagnostic
overhead. No replacement qualification policy, target calibration or threshold
change is proposed. The 1%, p95 100 ms/max 200 ms edit and 750 µs operation limits
remain. Full/repeated routes, the 15-second reversal, target pixels and HD 620
performance remain unverified. M1 stays blocked; no new target action is needed.

Verification pending cloud execution; no measured correction is claimed.
