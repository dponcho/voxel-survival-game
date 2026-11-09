# Native CPU-cycle capability

Implementation of the counter-only increment in
[the adopted diagnostic-cost decision](M1_DIAGNOSTIC_COST_POLICY.md#next-bounded-implementation-and-completion).
**Cloud capability and source-matched Windows candidate verified in CI
`39073452514`. M1 remains blocked; no target profile or diagnostic cost qualified.**

## Bounded implementation

`CairnProbe.cpu_cycle_observation()` is a dedicated project interface. It calls
Windows `QueryProcessCycleTime` and `QueryThreadCycleTime` in nested order:
process low, current-thread low, current-thread high, process high. Each call
retains enclosing monotonic microsecond clocks, availability, success and its
immediate Win32 error. Raw unsigned cycles and wall clocks serialize as canonical
decimal strings. A failed/unavailable value is null. Reversed clocks/counters
are contradictory, never a passing zero. Unsupported platforms are explicit.
These calls do not enter ordinary snapshots or operational budget clocks.

`cpu_cycle_capability_smoke()` is an explicit fixture invoked once per matching
editor/release process with `--cpu-cycle-capability`. Each has a five-second
native fixture cap and a 60-second process timeout, with no retry. It retains:

- Native decimal controls at zero, 2^53+1, 2^63 and UINT64_MAX, round-tripped by
  the actual GDScript JSON codec; failed/unavailable/reversed records and two
  real invalid-handle API failures.
- Main-thread and joined short-lived worker SHA-256 work: 1,024 updates of
  4,096 bytes with byte `i % 251`. Python independently checks bytes/digests.
- A labelled 20 ms main-thread wait, without asserting zero process demand.
- The worker's own thread-cycle brackets captured before exit, plus an
  enclosing process bracket ending after join. The process lower demand bound
  must cover the worker's upper demand bound. Counter contradiction stops here.

The reader checks exact integers, monotonic and nested read order, native/game
identity, positive execution witnesses, complete work and the fixture cap.
Twelve saved corruption cases per binary must be rejected. Downloaded candidate
and evidence are independently rechecked on Linux without an engine.

## Verification routing and scope

The native source key changes; all three matching binaries must be compiled and
qualified in Actions. Existing native sanitizer, editor/import/export,
integration, package/dependency, offline extraction and independent saved audits
remain required. The historical v1 pilot/runtime preflight is now explicitly
opt-in in the reusable workflow, default false. Its identifiers, inventory,
implementation, pure reader controls and original failed evidence are preserved.
This increment does not rerun v1 or implement/run the v2 route pilot.

No world, save, generation, work, production admission, threshold or supported
hardware setting changes. Capability does not establish 1% sensitivity, CPU
seconds, GPU/driver/presentation cost or target performance. No laptop action.

## Result

[CI `39073452514`](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514)
completed successfully on October 18 UTC. Source implementation is
`8f1bc6636d4a2ff2fc716a24263557c591af44ed`, verification head
`1841e4c17cc91bfa10e5b24e1aec8fbdd3c5eb91`, exported PR-merge build
`b3ae6b70579507088522b8a16f483c65b0489e96`. Native source key:
`2045ec77931e23130c773d1c2e2645ce6a925b1eccc1e8f8347df7758e50faf3`.

Both bounded fixtures passed once, with no retry. The labelled 20 ms wait and
both 4 MiB hashes completed. Every hash has 1,024 successful 4,096-byte updates
and independent SHA-256
`e9e88a1c2e64ffc1ae98b9be4f423dba98d7b65fa119c1a04cf9c5ec934ae121`.
The real invalid-handle calls preserve Win32 error 6 and null cycle values.
Native decimal strings at 2^53+1, 2^63 and UINT64_MAX survive the engine JSON
round-trip. All observed counters and wall brackets are ordered/nondecreasing.

| Binary | Fixture elapsed (µs) | Enclosing process lower bound (raw cycles) | Exited worker upper bound (raw cycles) | Saved faults rejected |
| --- | ---: | ---: | ---: | ---: |
| Editor | 55,111 | 41,505,155 | 40,843,240 | 12 |
| Release | 55,887 | 41,830,882 | 41,154,511 | 12 |

In both cases the enclosing process lower bound covers the independently
witnessed worker upper bound after join. These are capability observations;
they do not infer timer resolution, convert cycles to seconds, compare the two
binaries' CPU cost, or establish 1% sensitivity.

All four active jobs passed: 141 Python regressions (55.981 s in Linux CI),
seven native ASan/UBSan suites with normal Actions settings, new editor/debug/
release compilation and individual qualification, editor import/parse and both
exports, the existing integration/profile suite, dependency/PE audit and fresh
offline extractions. The downloaded Windows audit verified eight self-tests,
91 PCK entries and all 50 preceding saved corruption cases, plus the 24 new
counter faults. The Linux job reproduced the downloaded candidate and saved
audits without executing an engine. Codex Cloud independently checked artifact
digests, ZIP/PE/PCK/native identity and both exact saved counter audits too.

Native compilation took 2,680.391 / 1,873.063 / 1,806.281 s for editor/debug/
release. The [qualified native bundle](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514/artifacts/12118359302)
is reusable only under this exact native key. Source pins, flags, world/save
compatibility, ordinary snapshots and terrain budget clocks are unchanged.

### Portable candidate and evidence

[Windows player artifact `12119108758`](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514/artifacts/12119108758)
contains `Cairn-windows-x86_64.zip`, `BUILD_INFO.json` and `SHA256SUMS.txt`.
The inner portable ZIP is 30,178,896 bytes, SHA-256
`ded598c70f1698d21ceba1ec37999b91f8d9c174f41a5f373a727deaaf64a937`.
Its release executable SHA-256 is
`723f26e568b33e702a584280c5792f88d39f31195da8ef594ba01cf4084437ef`,
identical to the qualified release template.

The [committed evidence](evidence/m1-cpu-cycle-capability-cloud-2026-10-18.json)
retains both raw capability records, exact independent audits, source/binary/
artifact identities, build timings and retained failures. Original artifacts:
[native qualification](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514/artifacts/12119065898),
[complete Windows evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514/artifacts/12119437269),
[downloaded Linux recheck](https://github.com/dponcho/voxel-survival-game/actions/runs/39073452514/artifacts/12118793570).

The standard full-height prepared cases retain zero coverage alarms, all 288
submitted edits and passing operation phases in editor/release; their baselines
retain 520 coverage alarms each. Broader research preparation retains deletion
overruns of 1,025 / 810 µs, and the 16³ one/two-worker H2 alternatives retain
edit-latency failures. Historical failures and legacy inconclusive diagnostic
verdicts remain unchanged. Cloud correctness/integrity is distinct from those
failed measurements and target qualification.

The historical v1 runtime pilot/preflight was skipped; no v2 route or positive
pilot ran in this counter-only increment. Its separate successor now implements
the v2 inventory, native dose and exact readers under another native key and
matching candidate. [That finite result](M1_SHIPPING_CPU_CYCLES.md) completed five
valid trials and stopped at unresolved null controls in CI `39088740702`.
Neither later quartet ran. The capability evidence above remains historical and
unchanged. No pilot retry or laptop action is requested by either result; read
[the current next decision](NEXT_TASK.md).

API contracts checked against the pinned Godot `core/os/thread.h`,
`core/crypto/crypto_core.h` and `core/string/ustring.h`, plus Microsoft's
[process-cycle](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryprocesscycletime)
and [thread-cycle](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime)
documentation. Raw cycles remain distinct from elapsed time.
