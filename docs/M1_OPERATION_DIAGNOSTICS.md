# M1 phase-local operation evidence

Report schema 5 preserves the schema 1 lifetime `native_start`/`native_end`
counters. Scenario upload/deletion gates now use independently accumulated
`operation_phase.upload.max_usec` and `operation_phase.deletion.max_usec`.
The 750 microsecond limit is unchanged. Maxima are never subtracted.

`operation_phases` labels preparation, warm-up, gameplay, paced diagnostics,
overhead diagnostics and retirement. Phase transitions seal the current frame
segment without resetting admission budgets or lifetime measurements. Thus a
single native frame can have two non-overlapping phase segments. Preparation
and retirement costs remain evidence even when gameplay is within budget.

Each measured scenario has `<id>-frames.csv.operations.csv`, written through the
existing disk worker. Preparation and retirement use separate files with
`-preparation`/`-retirement` suffixes before `-frames.csv`. Rows contain native frame and phase IDs, monotonic interval endpoints,
operation counts, estimated payload bytes, total times, and the slowest operation's
time, payload and start timestamp. Deletion kind 2 means surface removal; kind 3
means mesh reference release. Payload estimates use 64 bytes per unique vertex
(position/normal/UV/color and tangent reserve) plus four bytes per actual index.
They do not measure driver allocation, compressed GPU buffers or deferred destruction.
The timed deletion scope remains the existing native removal/reference-release
block; renderer/driver work outside it is unavailable.

Join timestamps to `callback_usec` in the application frame CSV. Native frame
intervals and callback intervals have different boundaries; asynchronous renderer
CPU/GPU queries are context, not costs to add to the native timings.
`diagnostic_usec` now covers the **previous complete callback**, including row
formatting, CSV batch submission and live UI updates. `diagnostic_frame` identifies
that callback (zero on the first row); the last callback is retained in scenario
`diagnostic_accounting`. Summing those CSV values plus the final callback reconciles
to the callback total. These are elapsed wall times, not CPU service measurements.
The old misleading `diagnostic_cpu_fraction` field is replaced by
`diagnostic_callback_wall_fraction`.

Each scenario also records the window from measurement setup through the last
callback, phase closure, writer join/flush and report construction. The writer is
closed before terrain retirement; preparation I/O drains before this window opens.
Final partial batches rejected by the sink's nonblocking queue are retried between
frames outside gameplay, for at most 120 attempts or one second. Permanent failure
still fails evidence integrity. Cancellation waits for that bounded submission
step; it cannot start a second concurrent close. The existing final writer join
remains outside gameplay and has no new timeout guarantee.
`writer_drain_usec` is nested within finalization, never added to overlapping
callback/worker/GPU times. No disk join is introduced within measured gameplay.
`report-finalization.json` separately times combined summary construction, hashing,
serialization, writes/flushes and final UI. Its own terminal record write and
deferred renderer/OS work are explicitly excluded. Smoke timing includes verification
and logging, so smoke can never pass overhead qualification.

A/B remains the fixed 30-second off/on/on/off workload. Both modes retain phase
totals, sparse 10-microsecond histograms (the last bin includes >=1-second values),
and up to 64 five-second timing blocks plus a partial block. Baseline detailed
frame probes/traces remain disabled. The comparison uses complete-window time per
callback and checks both repeats and within-phase block drift against 1%. The
minimum/maximum repeat ratios give a conservative range, not a statistical
confidence interval. A range crossing 1%, consistent apparent speedup, short or
stalled workloads, incomplete evidence or unstable phases are inconclusive.
Shared native counters, collision timers and minimal timing bookkeeping stay on;
the switched A/B result alone cannot qualify total diagnostic overhead or M1.

Storage is bounded: 64 native records, at most 128 pending operation CSV rows,
64 KiB per disk queue item, the existing 64-item shared disk queue, and 64 MiB per
operation file. Overflow is reported and fails evidence integrity; no missing
record is treated as a zero. Existing frame CSV buffering is reduced to 128-row
batches (256-row ceiling) to accommodate its additional columns.

`completed` records whether the scenario finished. `evaluation`/legacy `outcome`
describe the measured checks. `qualified` remains false while required M1
observations and exact-build review are outstanding, even for a passed measured
subset. Summary text and UI distinguish completion from qualification.

Cloud regression coverage includes callback/finalization boundaries, bounded
timing storage, A/B classifications, and saved CSV callback-total reconciliation.
Cloud checks also cover isolated maxima after slower preparation, later over-budget
operations below lifetime peaks, idle phases, boundaries, A/B trace suppression,
bounded overflow, and actual saved CSV/phase/lifetime-total reconciliation through
the existing debug/release smoke route. No generator, save, workload, worker,
resolution or performance-threshold change is included. Target validation of the
corrected measurements remains required; M2 remains gated.

Schema 4 adds N2/H2 edit evidence. An accepted proxy edit records every current
render block touched by Voxel Tools' padded invalidation and its mesh revision.
The endpoint is the last affected mesh submitted to the renderer. Physical
presentation remains unavailable. Superseded, cancelled, timed-out (>200 ms)
and unavailable edits retain separate outcomes; none becomes a zero-latency
sample. Per-edit records go to `<id>-frames.csv.edits.jsonl` through the same
bounded disk worker. The tracker caps pending edits at 64, queued events at 128
and each edit at eight affected render blocks. The event file caps at 8 MiB;
overflow or missing rows fails evidence integrity. The p95 value is a
conservative 1 ms upper bin, checked against 100 ms alongside the 200 ms
maximum. This instrumentation changes neither the edit workload nor the
thresholds. It requires a matching Windows build and exact-build target report
before the visibility gate can pass.

Fixture preparation and measurement both initialize the player/viewer/camera
pose before any measured frame. At the route's end, N2/H2 stop issuing commands
and continue measured callbacks and native phase accounting until pending edits
submit or reach the existing 200 ms timeout. `edit_acknowledgement` labels these
final frames and their wall time; the route clock and edit count stay fixed.
Their frame deadlines, native costs and edit latencies remain in the scenario
results. Writer drain and retirement start only after settlement. Explicit user
cancellation still closes a partial run immediately. A broken tracker that stays
pending beyond this bounded window fails the run.

GPU query values remain unchanged in the frame CSV. Zero is unavailable;
non-finite, negative or process-age-exceeding elapsed values are invalid.
`invalid_gpu_samples` records them, `render_gpu_ms` covers valid samples only,
and any invalid sample makes GPU timing inconclusive. No GPU wait is introduced.

Indexed upload batches retain the same 1,024-triangle limit and surface/material
order. Original source vertex IDs preserve attribute seams; equal positions are
never welded. The worker copies each referenced vertex once per batch, resets
only touched lookup entries, and preserves every ordered triangle index.
Scratch lookup is capped at 98,304 entries (384 KiB), plus two 3,072-entry arrays
(24 KiB) per active mesh worker. Invalid indices or unsupported channel/count
layouts fail native admission. Face, worker, queue, byte and time caps are unchanged.
Upload and surface-retirement payloads use actual vertex/index counts without
reading renderer buffers back. A full cube-quad batch has 2,048 vertices and
3,072 indices: 143,360 estimated input bytes versus 208,896 in the old expanded
batch. This data-size reduction alone does not establish a target timing gain.
