# Native CPU-cycle capability

Implementation of the counter-only increment in
[the adopted diagnostic-cost decision](M1_DIAGNOSTIC_COST_POLICY.md#next-bounded-implementation-and-completion).
**Source prepared in `441d0cd`; matching Windows verification/candidate pending.
M1 remains blocked.**

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

Publication of the prepared commit to the existing `codex/m1-engine-proof`
branch was rejected by automatic approval review, which requires direct
publication authorization rather than recovered prior authorization. The
destination was verified as the same public `dponcho/voxel-survival-game`
repository; no repository visibility change or alternative destination is used.
No push or new Actions/native/candidate result is claimed.

Completed in the Codex Cloud workspace against the prepared source:

- All 141 Python integration/reader regressions pass (91.088 s), including six
  new counter-reader tests and synthetic saved-failure checks.
- All seven engine-independent native suites pass with AddressSanitizer and
  UndefinedBehaviorSanitizer. LeakSanitizer cannot inspect `/proc` in this
  workspace sandbox, so those workspace runs set `ASAN_OPTIONS=detect_leaks=0`;
  the required Actions sanitizer commands retain their normal settings.
- Owned Python compile checks, modified workflow YAML parsing, documentation
  links/anchors and `git diff --check` pass. The existing probe implementation
  changes only by adding the two bindings/declarations; ordinary snapshots and
  terrain budget clocks remain unchanged.

These are logic/static checks. Neither Godot/Windows compilation nor real
counter/hash/wait/worker capability has run for this source. The open PR's
remote head was independently confirmed still at `1cbf609e408911b22e283245d8a58aeb6843edbe`.

Pending exact-build Actions verification and portable artifact audit. The next
task may implement v2 inventory/interval readers and the declared finite sequence
only after capability passes. If counters are unavailable or contradictory,
retain the error and stop that implementation path.

API contracts checked against the pinned Godot `core/os/thread.h`,
`core/crypto/crypto_core.h` and `core/string/ustring.h`, plus Microsoft's
[process-cycle](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryprocesscycletime)
and [thread-cycle](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime)
documentation. Raw cycles remain distinct from elapsed time.
