# M1 phase-local operation evidence

Report schema 2 preserves the schema 1 lifetime `native_start`/`native_end`
counters. Scenario upload/deletion gates now use independently accumulated
`operation_phase.upload.max_usec` and `operation_phase.deletion.max_usec`.
The 750 microsecond limit is unchanged. Maxima are never subtracted.

`operation_phases` labels preparation, warm-up, gameplay, paced diagnostics,
overhead diagnostics and retirement. Phase transitions seal the current frame
segment without resetting admission budgets or lifetime measurements. Thus a
single native frame can have two non-overlapping phase segments. Preparation
and retirement costs remain evidence even when gameplay is within budget.

Each scenario has `<id>-frames.csv.operations.csv`, written through the existing
disk worker. Rows contain native frame and phase IDs, monotonic interval endpoints,
operation counts, estimated payload bytes, total times, and the slowest operation's
time, payload and start timestamp. Deletion kind 2 means surface removal; kind 3
means mesh reference release. Payload estimates use the existing 68 bytes per
vertex convention and do not measure driver allocation or deferred destruction.
The timed deletion scope remains the existing native removal/reference-release
block; renderer/driver work outside it is unavailable.

Join timestamps to `callback_usec` in the application frame CSV. Native frame
intervals and callback intervals have different boundaries; asynchronous renderer
CPU/GPU queries are context, not costs to add to the native timings.
`diagnostic_usec` is explicitly a partial callback measurement, not proof of
end-to-end diagnostic overhead. A/B-off phases retain phase totals while detailed
frame probes and traces are disabled. Preparation/retirement traces still exist.

Storage is bounded: 64 native records, at most 128 pending operation CSV rows,
64 KiB per disk queue item, the existing 64-item shared disk queue, and 64 MiB per
operation file. Overflow is reported and fails evidence integrity; no missing
record is treated as a zero. Existing frame CSV buffering is reduced to 128-row
batches (256-row ceiling) to accommodate its additional columns.

`completed` records whether the scenario finished. `evaluation`/legacy `outcome`
describe the measured checks. `qualified` remains false while required M1
observations and exact-build review are outstanding, even for a passed measured
subset. Summary text and UI distinguish completion from qualification.

Cloud checks cover isolated maxima after slower preparation, later over-budget
operations below lifetime peaks, idle phases, boundaries, A/B trace suppression,
bounded overflow, and actual saved CSV/phase/lifetime-total reconciliation through
the existing debug/release smoke route. No generator, save, workload, worker,
resolution or performance-threshold change is included. Target validation of the
corrected measurements remains required; M2 remains gated.
