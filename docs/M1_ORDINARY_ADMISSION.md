# M1 ordinary admission and terrain-budget evidence

Completed October 16, 2026 UTC. **Cloud correctness passed; M1 and target
performance remain unqualified.** Priority passes the bounded ordinary-path
comparison below and remains opt-in pending representative-world and target
evidence. No laptop action is requested now.

The subsequent [full-height/directional follow-up](M1_FULL_HEIGHT.md) now has
the latest verified candidate. The measurements below remain this increment's
historical record; current next actions are in [NEXT_TASK.md](NEXT_TASK.md).

## Candidate and verification

- Implementation: `5d4621f20f86481dae732dfc2de7e1829462644d`, following review
  implementation `3b411d0854a5a468f4d3e2e99162d5fe527bcfd1`.
- Exported merge/build: `9de780dbcf80f769e66eab8590c8cec8f02cede1`; its tree is
  exactly the implementation tree, `1111a0f81eefc9611994e1ef409e1a46266b282f`.
- [CI 38912228615](https://github.com/dponcho/voxel-survival-game/actions/runs/38912228615):
  all three jobs passed, 97 Python regressions, six native sanitizer suites,
  matching editor/debug/release qualification, all prior engine/profile/control
  checks, eight ordinary trials, DLL audit and two fresh offline extractions.
- [Portable Windows player](https://github.com/dponcho/voxel-survival-game/actions/runs/38912228615/artifacts/12052521294):
  inner ZIP 30,132,632 bytes, SHA-256
  `f993e2de3586f60ab2ec592b5e455754952edbc343bf1f998955a42e47f43584`;
  artifact expires `2026-11-15T14:22:26Z`.
- [Saved evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/38912228615/artifacts/12051568420)
  and [native qualification evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/38912228615/artifacts/12050513156).
- Native key:
  `558a7276457cd5caeb422cbfe2749e38554d9c439912cb2e2ac3dece35987b2c`.
  The source-matched binaries built in CI `38838162724` were reused and
  requalified; no native source changed in the validator correction.

The published-download audit verifies byte round-trip, ZIP CRC/paths, all 80
PCK entry MD5s, native/build identity, eight self-tests and 38 PE imports. All
26 earlier and twelve reversal mutations are rejected. A second read-only audit
of the downloaded player/native/evidence reproduces every numeric, verdict,
phase and witness field; only the deliberately missing-file mutation's OS error
text/temporary path differs. No engine or compiler ran locally.

## Validator correction

CI `38838162724` built the new native ledger successfully, but ordinary mode
incorrectly invoked `benchmark_startup_tests.verify_saved` after deliberately
stopping startup observation. The validator required six startup phases, so the
first FIFO process exited unsuccessfully despite completing its 1,200 ticks.

`benchmark.gd` now scopes that startup validator to modes that collect its
evidence. Dedicated startup tests retain it. Ordinary frame/edit/operation,
I/O, phase closure, finalization, drain and independent saved checks still run.
The earlier FIFO run's 37 coverage alarms and 125 ms edit p95 remain failed
historical observations; correcting the harness does not relabel them as passes.

## Matched ordinary results

Each fresh process runs the original H2 outward route for twenty seconds /
1,200 fixed ticks, retaining the camera turn at tick 900, 28,800 actor updates,
80 accepted edits and twenty proxy saves. Render blocks remain 16³, visuals/fog
96 m, data 128 m, four preparation viewers and the 512-region cap. Native
admission tracing and travel/resource observation are disabled; ordinary
frontier, edit and operation ledgers remain enabled. Selection/resource
witnesses stay unavailable/null. Elapsed time is not a causal overhead estimate.

| Executable | Workers | Policy | Coverage alarms | Submitted / 80 | Timed out | Edit p95 ms | Submitted max ms | Bounded acceptance |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Editor | 1 | FIFO | 38 | 78 | 2 | 76 | 186.311 | Failed |
| Editor | 1 | Priority | 0 | 80 | 0 | 21 | 69.149 | Passed |
| Editor | 2 | FIFO | 38 | 79 | 1 | 125 | 186.438 | Failed |
| Editor | 2 | Priority | 0 | 80 | 0 | 15 | 41.814 | Passed |
| Release | 1 | FIFO | 35 | 79 | 1 | 132 | 186.401 | Failed |
| Release | 1 | Priority | 0 | 80 | 0 | 21 | 41.433 | Passed |
| Release | 2 | FIFO | 36 | 80 | 0 | 125 | 193.444 | Failed |
| Release | 2 | Priority | 0 | 80 | 0 | 15 | 41.450 | Passed |

Latency aggregates cover submitted edits; timeouts are separate failed outcomes.
Editor/one-worker FIFO retains edit 4 at `[32,6,13]`, 206,133 µs, and edit 53
at `[96,6,13]`, 200,097 µs. Editor/two-worker FIFO retains edit 53 at 200,096 µs;
release/one-worker FIFO retains edit 53 at 206,772 µs. Their original target
revisions and unsubmitted flags remain in the saved events. Editor/one-worker
FIFO also retains raw frame-deadline misses.

All eight integrity checks pass. All four priority runs meet the 100/200 ms
edit limits with zero conservative coverage alarms, zero movement-readiness
stops, all original edits submitted and full native drain. All 24 ordinary
native phases pass the complete operation guards. These trials reconcile 26,813
operation records and 23,201 frame rows; observed resident peaks are 511 meshes
and 867 data blocks. Maximum ordinary upload/deletion/application spans are
417/454/406 µs, peak native-frame terrain charge 1,562 µs within the heavy 2 ms
allowance, and largest individual payload 143,360 bytes.

Priority scenario assessments remain **inconclusive** under the unchanged
legacy 1% diagnostic guard. The shipping inventory/sensitivity pilot remains
`not_run`. Headless results do not measure HD 620 rendering or presentation.

## Complete terrain ledger and retained failures

V2 native and independent fault controls pass for cumulative time/payload,
inclusive application/nested-child charging, phase carry and the 750 µs
reservation. The 38 CSV-backed benchmark folders retain 368 native phases /
115,135 operation records. The broader suite still contains these failures:

| Case | Phase | Retained limit failure |
| --- | --- | --- |
| Debug ordinary, paced | Retirement | Deletion 781 µs |
| Traced reversal, release/two-worker FIFO | Gameplay | Upload 923 µs |
| Heavy A/B `AB-H2-off-1` | Retirement | Deletion 1,488 µs |
| 32³/two-worker `R1` | Retirement | Deletion 993 µs; two cumulative overrun records, peak 1,134 µs against 1 ms |
| Calibration `CAL-H1-reference-2` | Preparation | Deletion 1,451 µs and data application 919 µs |

These remain failed measurements, not failing evidence readers. No guard is
waived, no clock cause is invented and no profile is qualified. Renderer-deferred
work, target operation timing and the broader performance gates remain open.
The ten preceding ordinary folders / 98 scenarios / 284 phases reconcile, and
all 42 heavy fixed-work/configuration contracts match the durable baseline.

Measured CI stages: static 49 s, cached native qualification job 51 s,
import/export 124 s, full integration 908 s, packaging/offline checks 89 s and
published-download audit 39 s. No suite was pruned or timing saving inferred.

## Decision and next bounded task

The ordinary cloud comparison is complete; repeating the same eight-case matrix
is not the next action. Keep priority opt-in and production FIFO. Build one
deterministic full-height `Y[-64,192)` fixture at an interior altitude with
actual movement reversal and cross-axis travel, starting with the feasible 32³
candidate. Retain the existing outward H1/H2 workloads and all current limits.
Require exact work, bounded preparation/eviction/drain and zero coverage/readiness
failures; retain operation failures and isolate any blocking code path before
expanding the experiment. Arithmetic does not select or qualify 32³.

Representative target timing, shipping diagnostics, physical pacing, deferred
accounting/retention and qualification repeats remain in [NEXT_TASK.md](NEXT_TASK.md).
No M2/content expansion or new laptop run follows from this cloud result.
