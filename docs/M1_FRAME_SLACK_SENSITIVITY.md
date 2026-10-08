# Experimental frame-boundary and CPU-slack validation

M1 remains blocked; no profile is qualified. This increment validates a bounded
**owned callback cycle** observation alongside the completed body-span instrument.
Ordinary benchmarks retain `frame_slack_sensitivity.status: not_run`; gameplay,
calibration, fixtures, actors, edits/storage, radii/resolution, workers/admission,
ticks and safety behaviour are unchanged. No native/world/save semantics change.
All existing assessors, thresholds, failures and qualification flags remain.

## Estimand and boundaries

The estimand is mean wall duration from a process callback's entry through the
**successor process callback entry**, at matching positions. Each body owns one
complete cycle. A separate closing-anchor callback supplies the final successor;
the last dose is never omitted or given an invented interval. Every starting-body
position retains its whole cycle; rows are never trimmed, split or reweighted.
This independent starting-body convention does not alter the existing benchmark's
ending-callback interval convention.

The exclusive cycle partition is body wall span + observed callback remainder
(prefix/ledger work) + time after the observed callback bracket. The last component
can contain later script bookkeeping, engine/physics/render work, frame delay and
OS scheduling; it is **not measured wait service**. Nested dose/body/callback/cycle
spans are never added together. Closing-anchor callback cost and setup/closure/
writer flush/report construction stay in the complete phase window, outside the
owned-cycle mean. Snapshot/append/controller gaps are separately retained and
unallocated. Complete probe duration reconciles phase windows + disjoint gaps +
external combined report finalization; no cost is allocated across repeats.
The finalization record's own write and process exit remain explicitly excluded.

Body and cycle effects use separate reference/positive/positive/reference
envelopes and exact integer 1% comparisons. Their ratios describe different
quantities. A body dose can be absorbed before a wait, so a larger body does not
by itself establish an increased frame cycle. Callback-count/composition drift
refuses attribution while leaving raw duration/count/body/cycle effects visible.
Complete-window, pooled cycle/body and matching main-section instability remain
guards. Terminal/acknowledgement uncertainty uses the larger overlapping change,
divided by mean complete-trial duration, never their sum. Missing evidence remains
unavailable/null. Failed work/operations, missing/reordered/incomplete/stalled or
I/O evidence remains inconclusive.

These labels (`null_observed`, `slack_observed`, `frame_sensitivity_observed`)
characterize software controls. They never qualify M1. OS CPU service, actual GPU
overlap/completion, physical presentation, frontier causal cost and shared total
diagnostic overhead remain null. A process-cycle throughput is not rendered fps.

## Pinned source

Godot `ed1daf0bf001b61586d9930840f2f1394092c079` establishes placement:

- [SceneTree process](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/scene/main/scene_tree.cpp): `process_frame` signal/queue processing precedes node process callbacks; timers and later queue/scene work follow them.
- [Main iteration](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/main/main.cpp): physics/input work precedes scene processing, then rendering sync/draw, process-frame count increment and OS frame delay occur before the following iteration's callback.
- [OS frame delay](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/core/os/os.cpp): the dynamic limiter advances target ticks and delays only while ahead of that target; added CPU work can consume available delay. Headless mode also has a low-processor delay. The limiter's internal wait duration is not exposed by this probe.
- [Engine API](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/doc/classes/Engine.xml): process-frame identity and `max_fps` are supported; headless draw count does not represent rendered output.

The existing pinned native HashingContext/mbedTLS source verification in
[M1_CPU_DOSE_SENSITIVITY.md](M1_CPU_DOSE_SENSITIVITY.md) still applies. Render
signals can be asynchronous and are not GPU completion; they stay unavailable in
this headless experiment. No unobserved engine stage is assigned a passing zero.

## Predeclared modeled controls

Thirty controls each retain a quartet: 120 CSV phases. Each ordinary phase models
32 synchronous bodies and a separate closing-anchor callback. Seven bins contain
4/5/5/4/5/5 main callbacks and four terminal callbacks. Main body costs alternate
800/1,200 µs and terminal bodies cost 1,000 µs, giving mean body 1,000 µs. Ordinary
owned cycles are 20,000 µs: total 640,000 µs. Callback prefix/tail costs are 7/8 µs;
setup is 200 µs, closing anchor 15 µs and closure 1,055 µs with nested 400 µs drain.
Preparation/measurement/native-close/drain/retirement brackets are explicitly
modeled. These are software clocks and work-unit markers, not executed terrain,
actors, native voxel operations or the 1,800-tick heavy routes.

| Controls | Predeclared observation / result |
| --- | --- |
| Null | No dose clocks or work; exact zero effect; null observed |
| Below / at / above | 100/200/400 µs added in every positive body/cycle: exactly 0.5%/1%/2% cycle effect; sensitivity observed |
| Threshold overlap | Request 199 µs; actual positive repeats 199/201 µs; inconclusive |
| Slack | 500 µs added to every body within the unchanged 20,000 µs cycle; 50% body effect, zero cycle effect; slack observed |
| Final dose | Only the final positive body receives 400 µs; body effect 1.25%, cycle effect 0.0625%; final successor retained; sensitivity observed |
| Count drift / route mix | Four extra reference terminal callbacks / eight extra positive fast-section callbacks with alternating 16,000/24,000 µs main cycles; inconclusive attribution, apparent pooled speedup remains |
| Endpoint / acknowledgement | Redistribute 500 µs from last main cycle to first terminal cycle / add 500 µs to final terminal cycle in second repeats; all rows and uncertainty retained; sensitivity observed |
| Incomplete / missing / reordered / short | Completion/quartet/order/exact 32-body contract guard fails; inconclusive |
| Stalled / failed work / operation | Add 300,000 µs to one cycle / baseline work marker 7 instead of 8 / real evaluator rejects modeled 751 µs upload against 750 µs; inconclusive |
| Missing dose/body/successor / overlap / invalid phase | Missing dose or terminal aggregate, absent final successor, dose/cycle overlap or native-close after drain; unavailable/null, inconclusive |
| Window/cycle/body drift | Add 20,000 µs closure / 500 µs per reference cycle / 30 µs per reference body; inconclusive |
| Main cycle/body drift | Offset matched main sections at unchanged pooled total; inconclusive |
| I/O | Failed saved-evidence guard; inconclusive |

Bounds: 30 controls, 120 CSVs/2 MiB, 2 MiB JSON and a 60-second command.
The production ledger keeps seven bins and one final row, without a growing queue.
Existing sixteen method, 26 route, 28 endpoint, 44 fixed-work and 54 CPU-body
control expectations remain required and unchanged.

## Actual bounded native placement

An internal `--frame-slack-probe` application entry runs separate cloud-only
quartets for 500 µs and 20,000 µs native CPU dose requests in matching editor and
packaged release. It temporarily sets `Engine.max_fps = 100` only in this probe
and restores the previous value. Every body hashes eight common 4 KiB blocks;
positive bodies synchronously hash until the requested wall minimum, at most
8,192 updates and an observed 100,000 µs dose cap. No sleep, yield, worker or I/O
occurs inside the CPU bracket. Native calls cannot be preempted by this cap.

Each invocation retains 256 body callbacks and eight closing anchors (264 actual
callbacks). Engine process-frame IDs independently join each body with its
successor, including the final dose. A phase keeps at most 32 pending rows and a
4 KiB input. Files drain after the anchor; no phase I/O contaminates an owned
cycle. Saved evidence is capped at 2 MiB and invocation at 60 seconds.
Actual voxel operations/preparation/retirement are unavailable because no terrain
workload runs. Actual callback closure is labelled as such, never native closure.

These doses exercise expected limiter slack and work beyond its nominal 10 ms
period. Actual effect envelopes remain descriptive even when repeats are noisy,
negative or overlap 1%; the cloud check verifies placement/accounting, not a
hardware precision verdict or a measured wait cause. Every raw observation and
stall stays visible. No target repeat, calibration or full matrix is requested.

## Independent acceptance

`tools/qa/frame_slack.py` independently checks rational classifications, closed-
form section totals, streamed CSV clocks, exclusive partitions, counts, final
bodies/successors, phase/drain/acknowledgement bounds, guard/null semantics and
saved results. The native reader recomputes every SHA-256 digest with a bounded
4 KiB buffer, checks consecutive engine-frame identities, closing-anchor/complete-
callback costs, disjoint phase/controller/report windows and exact exported build.
Static regressions corrupt endpoints, native digests, counts, classifications,
phase/finalization scopes and unavailable values. Orchestration rejects missing
reports, script errors, nonzero exits and I/O faults. Ordinary smokes must retain
frame sensitivity `not_run` with no dose ledger.

Cloud runtime execution and candidate verification are pending.
