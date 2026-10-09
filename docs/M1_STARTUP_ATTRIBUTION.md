# Bounded startup timing

The October 3 baseline contains an early warm-up interval of 184.252 ms. Its
preceding diagnostic callback took less than 1 ms, with no traced native upload
or deletion overlapping the slow interval and no terrain work queued at the
ending sample. A similarly large viewport CPU elapsed result appeared five
samples later. The isolated N2 near-deadline interval has a similar delayed
result. This supports investigating rendering/wait time; it does not establish
the original frame or the cause. Detailed target reports remain private.

Background laptop activity is plausible. The pinned engine's so-called render
CPU time uses elapsed monotonic timestamps, not CPU service time. A driver wait,
first-use compilation or OS descheduling can all contribute. The old report
cannot distinguish them, and its renderer results have no origin-frame ID.
Do not subtract asynchronous CPU/GPU results from a callback interval or assume
a fixed five-frame delivery delay.

## Source semantics

Pinned Godot: `ed1daf0bf001b61586d9930840f2f1394092c079`.

- [GLES3 timestamp capture](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/storage/utilities.cpp)
  records `OS::get_ticks_usec()` and consumes earlier GPU timestamp queries.
- [Viewport measurement](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/rendering/renderer_viewport.cpp)
  returns the elapsed difference between those CPU timestamps.
- [Draw signal delivery](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/rendering/rendering_server_default.cpp)
  can include a render-thread queue and deferred post-draw delivery.
  `frame_pre_draw`/`frame_post_draw` do not mean GPU completion or display scanout.

## Retained evidence

`summary.json.startup_attribution` adds a process-monotonic timing ledger. The
six logical groups cover benchmark initialization, warm-up preparation,
warm-up, retirement, N1 preparation and the first N1 gameplay intervals.
Initialization starts in the benchmark's `_ready`; earlier engine/scene boot
is unavailable. Closing/report-drain gaps remain in the current logical group
until the next phase hook. Crossing intervals retain both phase IDs.

Every callback-entry interval contributes to its group count and maximum.
Storage retains the first 64 intervals plus one worst interval per group,
at most 16 pending completed spans, and the first 64 asynchronous renderer
observations plus one worst CPU elapsed observation per group. The render hooks
disconnect after 64 N1 intervals or early scenario completion. Overflow, invalid
spans, unmatched render signals, open brackets and terminal partial intervals
are explicit. No sample queue grows with run duration.

Completed script, benchmark physics and render-signal spans are clipped to the
callback interval. Per-stage unions, total union, overlap and time outside the
observed stages are retained. Overlapping wall spans are not added. The script
span excludes the callback ledger write and asynchronous scenario continuations;
the existing complete diagnostic callback timer still includes new bookkeeping.
Physics spans cover the benchmark callback, not the engine's entire physics
step. A render-signal bracket can include driver/queue/scheduling waits and may
overlap scripts. A large outside-stage gap is evidence of elapsed time, not
proof of background activity.

Native operation CSVs use the same clock and phase IDs; their operation time
may overlap these spans. Existing frame CSV columns, native limits and raw
deadline misses remain intact. Latest viewport results stay separately labelled
asynchronous observations with `origin_frame: null`; `observed_usec` identifies
the polling callback's entry clock, not the exact query-read instant or original
render frame. Causal attribution remains
inconclusive, background activity unverified and qualification false. Startup
instrumentation overhead, shader/driver/OS causes and physical pacing require
target evidence; the later A/B does not certify these startup hooks.

## Reproduction and verification

The title offers **Run startup timing check (~20 s + loading)**. It starts a new
portable game process using the selected profile, prepares the existing warm-up
and N1 fixtures and runs each for ten simulation seconds. Preparation and
retirement are additional elapsed time. Normal full/matrix durations, workload,
resolution, radii, ticks, native source key and world/save versions are unchanged.
This two-route check cannot qualify M1 or replace the full baseline.

Independent endpoint-sweep regressions check clipping, overlap, large unexplained
gaps, cancellation, phase crossing, missing/dropped spans, caps, asynchronous
origins and the exact 64-interval stop. Cloud smoke checks JSON-round-trip the
retained payload, reconcile its clocks/previous diagnostic durations against
saved frame CSVs and match native phase identities. The release integration also
executes the short route. Headless checks establish data integrity; target
rendering, overhead and the historical hitch's cause remain unverified.

## October 6 repetition outcome

Two current-build target reports now establish that a smaller early warm-up
delay repeats inside the render-signal bracket, while the historical 184.252 ms
stall does not recur. Both shortened prepared N1 routes have no raw deadline
misses. The retained stage clocks reconcile to saved CSVs, with no lost or
invalid spans. This localizes the observed delay without establishing its
driver/shader/OS cause. Completed short repetitions do not qualify startup
overhead, physical pacing or the full M1 workload. Detailed measurements remain
private; [evidence](M1_EVIDENCE.md) records the bounded conclusion.
