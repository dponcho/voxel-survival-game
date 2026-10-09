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
The actual probe window begins at its first phase clock; application startup,
initial input/ledger allocation and limiter setup precede that window.

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
Error storage retains at most the eleven distinct declared messages; repeated
native errors still fail without growing the message queue.
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

## Verified cloud result — October 8 UTC

[CI 37804090619](https://github.com/dponcho/voxel-survival-game/actions/runs/37804090619) passed all three jobs: 70 Python regressions,
five native sanitizer suites, exact matching-engine checks, 30 modeled controls,
real editor/release probes, every existing method/route/endpoint/fixed-work/CPU
expectation, runtime/profile/smoke checks, DLL audit and two fresh offline
extractions. Independent downloaded review reconciles 120 modeled
phases/3,856 rows, 678,187 JSON bytes and
272,269 raw bytes, within the predeclared 2 MiB limits.
All 512 actual body callbacks and 16 closing anchors reproduce native
digests and reconcile engine-frame successors, exclusive partitions, complete
callbacks, drain/controller gaps and external finalization. Both probes retain
placement verification, qualification false and unavailable/null causal costs.
Actual effects remain descriptive; cloud noise does not receive a passing verdict.

All ten ordinary smoke folders retain frame/CPU dose `not_run`, no dose ledgers,
no integration failures and qualification false. Independent review reconciles
98 scenarios/284 native phases, 37,340 operation rows,
12,877 frame rows and 94 edit events. Existing 54 CPU controls/
216 phases/327,444 rows and 256 real CPU callbacks,
44 fixed-work controls/176 phases/264,852 rows and 28 endpoint
controls/168,596 rows reconcile unchanged. All sixteen method and
26 route controls remain. Actual shortened calibration remains inconclusive;
16³ heavy coverage/edit alarms and operation failures remain unwaived. Hosted
OpenGL readback remains unavailable. No engine was installed, compiled or run locally.

Actual native effect envelopes (relative wall-span change; descriptive):

| Probe | Body envelope | Owned-cycle envelope | Cycle classification |
| --- | --- | --- | --- |
| editor, limiter_slack | 662.715% to 669.763% | -0.001% to 6.622% | inconclusive |
| editor, beyond_limiter | 25591.923% to 26573.807% | 100.984% to 101.545% | above_limit |
| release, limiter_slack | 662.875% to 667.929% | -0.001% to 6.625% | inconclusive |
| release, beyond_limiter | 26586.213% to 26878.254% | 101.000% to 101.547% | above_limit |

Both small-dose cycle envelopes cross zero and remain inconclusive. The large
native dose extends the observed cycle in both builds. The exact modeled slack
control retains zero cycle effect with a 50% body increase. Neither observation
calibrates 1% hardware noise or estimates frontier/shared causal cost. Stalls and
all individual observations remain in saved evidence.

Three failed attempts (37801519338, 37801991626, 37802839475) stopped
at script loading. Direct matching-editor parse checks exposed a duplicate `de`
variable in the observation scope; its rename corrected the cause. Parser
preflights remain. Corrected run 37803676081 passed; the current candidate also
includes bounded distinct error-message storage. Failed attempts are not candidates.

[Windows player 11563412804](https://github.com/dponcho/voxel-survival-game/actions/runs/37804090619/artifacts/11563412804) expires
`2026-11-07T16:11:49Z`. Exact exported merge/build: `62a8da6e8d1fc9b81195b6b6707d1b4bba3c446b`.
Portable ZIP SHA-256: `673d82bdd74c1d745e95a5aa3e5738037cf4621328c59ab3312064355cb9564d`; bytes: `30079503`.
Implementation `14581835677bf0bb403fb35a8b58d90eaf6e0595` and exported build share tree `5a35b2281b956c0b65752c764ed37e0f21603618`.
Native key remains `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
Archive/PE/PCK identity, all 66 PCK entry MD5s, pinned native templates,
eight native/game/offline self-test reports and all 38 PE imports independently verify.
Full public provenance is in [the verification record](evidence/m1-frame-slack-cloud-2026-10-08.json).

M1 remains blocked. No target-side action is needed now.
