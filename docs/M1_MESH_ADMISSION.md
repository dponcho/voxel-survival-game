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

## Verified cloud result — October 9, 2026

[CI 37878551633](https://github.com/dponcho/voxel-survival-game/actions/runs/37878551633)
passes all three jobs, completed `2026-10-09T03:41:25Z`: 88 Python regressions,
six native sanitizer suites, matching editor/debug/release qualification and all
existing checks. The fresh native source build is CI 37869341867. The independent
audit runs in Actions after the editing executor disconnect, downloads the actual
published player, checks byte round-trip, inner ZIP CRC/paths, all 76 PCK entry
MD5s, PE/native identity, eight self-tests and 38 DLL imports, and reconciles all
saved controls/trials. All 26 actual saved-evidence mutations are rejected.

| Engine / workers | FIFO coverage alarms | FIFO lateral unready observations | Priority alarms / lateral unready | Priority submitted before entry |
| --- | ---: | ---: | ---: | ---: |
| Editor / 1 | 23 | 37 | 0 / 0 | 8 / 8 |
| Editor / 2 | 24 | 40 | 0 / 0 | 8 / 8 |
| Release / 1 | 22 | 37 | 0 / 0 | 8 / 8 |
| Release / 2 | 24 | 38 | 0 / 0 | 8 / 8 |

Each FIFO trial independently demonstrates farther-before-closer admission for
all eight lateral cells. Priority moves their actual original ranks 15/16 to
selected ranks 1/0. All 32 priority witnesses have current submission before the
last outside and first inside samples; all 32 FIFO entry samples are unready.
This demonstrates the bounded selection cause/correction. Submission times remain
brackets; no physical-presentation timestamp is invented.

The first physics observation at each handover precedes native block creation.
Its state is genuinely missing and all identities are null. The initial reader
incorrectly demanded a revision there. Saved inspection proves every later
desired/admitted/submitted identity matches; the corrected reader retains that
initial null observation and accepts it only before admission. Missing after
admission, changed revisions, stale submission, failed work/operations, lost clocks,
I/O evidence and unavailable origins still fail. The new control covers both
sides of this boundary. Failed attempts remain in the public record.

Every trial retains 600 ticks, 14,400 actor updates, 40 submitted original edits,
ten saves, all four handovers and complete drain. Eight trials reconcile
15,177 native records / 24,737,695 bytes, 10,036 observation rows / 54,343,565 bytes,
24 native phases / 15,238 operation rows and 11,617 frame rows. Pending peaks at
459; mesh/data peaks are 511/867, travel retirement high-water two, complete
retirement high-water 285 and overloads zero. No closed-phase gap records occur in
these saved runs; the reader retains and separately validates such rows when
present. No edit or operation guard fails in the eight trials. Selection-span
maxima range 9–28 µs across modes; those observations exclude trace formatting,
copying and file I/O and do not estimate CPU service or total instrumentation cost.

Priority scenario assessments remain inconclusive because the 1% diagnostic
guard is unresolved; FIFO remains failed for coverage plus diagnostic cost.
Ordinary production stays FIFO. Ten ordinary folders / 98 scenarios / 284 phases
reconcile 37,345 operation rows and 94 edits; all 42 preceding heavy work records,
configuration and available exact contracts match the durable public baseline.
A 786 µs debug `AB-on-1` preparation deletion remains over the 750 µs threshold.
Short 16³ H2 still retains edit-latency/diagnostic failures. Every earlier method,
route, endpoint, fixed-work, CPU, frame, boundary and concurrent-edit expectation
and false qualification flag remains.

[Windows player 11593794161](https://github.com/dponcho/voxel-survival-game/actions/runs/37878551633/artifacts/11593794161) expires
`2026-11-08T03:40:21Z`; exported build
`41527690339ba965bbc36a126fc790522bb0e9f3`; latest implementation
`f79f4ecd2748a3b5d67afd8f4dea6a1e6fad288e` shares tree
`09d85f59b37e715e5f9a925693d222fa33ab0bec`. Portable ZIP: 30,127,069 bytes;
SHA-256 `ec2cd5d89774173ff55072362cafc6b3fde253d6b86547bc5c3a29078735ac4f`.
See [the exact public record](evidence/m1-mesh-admission-cloud-2026-10-09.json) and
[the durable ordinary contract baseline](evidence/m1-frontier-travel-contracts-2026-10-09.json).

The prototype correction is experimental. Full/repeated routes and the 15-second
reversal are not yet tested with it; target pixels, driver behavior, HD 620 timing,
per-frame CPU/GPU sensitivity and shared causal overhead remain unverified.
M1 remains blocked, M2 gated and no target profile qualified. No new target-side
run/download is requested. No engine ran locally.
