# Development handoff

- Branch: `codex/m1-engine-proof`; implementation/head before this docs update:
  `5ce757dfdce039dea5cfbe1f4ceff76635a272d8`.
- Milestone: **M1 blocked; target not qualified**. This increment is
  **cloud_passed_target_unverified**; M2 remains gated.
- Latest successful [CI 36803692007](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007)
  published [Windows player 11137310682](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11137310682).
  Exported build: `f3eb4ce72dd659f96df6d5e4804331c1fd4e1642`.

**Completed this session:** initialized player/viewer/camera pose at fixture
preparation and measurement start; stopped route commands at scenario end while
pending edits retain their existing 200 ms acknowledgement window. Final
acknowledgement frames, deadlines, native costs and latency stay measured;
writer drain/retirement follow settlement. Genuine timeout, broken-tracker
failure and immediate user cancellation remain distinct. Invalid GPU query
values remain in CSV, are counted, and cannot contaminate the valid-sample peak.
Recorded the user's GPT-6.1 Sol Max default in `AGENTS.md`.

All three CI jobs passed: 12 packaging/cache regressions, Python compile checks,
three native sanitizer suites, exact native reuse/requalification, matching
editor import and lifecycle/GPU regressions, debug/release smoke, four-profile
streaming/collision/edit/eviction/cancellation checks, dependency audit and two
offline fresh extractions. All five smoke exports reconciled saved CSV/summary
evidence and submitted every N2/H2 accepted edit with zero cancellations,
timeouts or pending edits. Independently downloaded player/evidence hashes and
ZIP CRCs matched; the contained player checksum/build identity matched. No local
engine compilation or execution occurred. Workloads, settings, formats and
thresholds were preserved.

**Failed in the supplied prior target baseline:** individual uploads and some
frame-operation allowances, conservative heavy mesh coverage, and recorded raw
dense/warm-up deadline misses. These outcomes remain evidence, not fixed claims.
No CI check failed this session.

**Unverified/inconclusive:** corrected exact-build HD 620 lifecycle/edit latency,
GPU timing validity, diagnostic overhead (especially heavy frontier sampling),
upload/OS/driver attribution, pacing, rendered visibility/fog, allocation
completeness/retention and qualification repeats. Detailed uploaded-report and
hardware data remain private. Request at most one corrected baseline before
any full comparison or qualification repeats.

**Single highest-priority next implementation task:** one bounded upload-cost
experiment retaining indexed vertex reuse within the existing surface batches.
Source currently duplicates indexed triangle vertices; reducing batch size
blindly also increases draw calls. Preserve the accepted architecture.

Acceptance: stock triangle coverage/winding/AO/UV/color/tangents match; draw-call
and face envelopes, bounded buffers/queues, routes and thresholds stay intact.
Payload accounting includes actual vertex/index data. Matching cloud native
tests, debug/release export and offline package checks pass. Produce a new
Windows candidate; compare scoped target upload/frame costs without claiming
an unmeasured improvement or suppressing smaller-payload outliers.

Inspect `PERFORMANCE.md` section 3, `TESTING.md` sections 7/8,
`native/sandbox_world/godot/fixture_generator.cpp`,
`native/sandbox_world/core/fixture.h`,
`build/patches/voxel/m1-admission.json`,
`native/sandbox_world/godot/m1_hooks.h`,
`game/scripts/m1_native_tests.gd`, `game/scripts/benchmark.gd`,
`game/scripts/benchmark_lifecycle_tests.gd` and
`game/scripts/benchmark_trace_tests.gd`.

Recommended next model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the
user's project default. No specialist escalation is currently justified.
