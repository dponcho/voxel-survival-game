# Development handoff

- Branch: `codex/m1-engine-proof`.
- Verified implementation commit: `1c9b7c638bb6154ce78c06f50831a7eda1db737e`.
  The subsequent evidence/handoff commit is documentation-only.
- Milestone: M1; cloud correction passed, target blocked/not qualified. M2 is gated.
- Latest successful CI: [36287728890](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890).
- [Windows artifact 10921940219](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921940219),
  exported build `404af829964d341524f6c7ae29b4aebdac683b2a`.

Published the approved diagnostic-overhead implementation to existing public
PR #2. Schema 3 measures callback formatting/flush/UI work, the final callback,
scenario writer drain and separate final-summary work. Both A/B modes retain
bounded histogram/block evidence. Conservative evaluation rejects unstable
repeats, drift, incomplete workloads and threshold-crossing ranges.

First CI [36287222011](https://github.com/dponcho/voxel-survival-game/actions/runs/36287222011)
failed 32³/two-worker report integrity after a transient sink submission rejection
at closure. Evidence `10920778828` was retained and reviewed. Fixed final-batch
submission with bounded between-frame retries outside gameplay and regressions
for transient/permanent rejection and writer failure. No native, save/generator,
workload or threshold changes. Unrelated local `HANDOFF.md` remains unpublished.

Verified: 12 Linux and 12 Windows packaging/cache tests, native sanitizer suites,
matching editor/templates, GDScript import, accounting/A-B/queue regressions,
debug/release smoke and CSV reconciliation, all four integration profiles,
streaming/collision/edits/eviction/cancellation, dependency audit and two fresh
offline extractions. No follow-up CI check failed. No local compilation or game
tests ran. The player archive was not independently downloaded/hashed locally.

Unverified: exact-build HD 620 overhead, edit visibility, pacing/driver attribution,
allocation completeness and retention/repeats. Earlier target reports failed
qualification. Shared baseline counters and unavailable deferred costs mean a
switched A/B pass alone cannot establish <1% total overhead. Review one corrected
target baseline before another four-profile comparison or final repeats.

Native key: `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803`.
Both runs reused the exact cache and native artifact `10920566667`; compilation
was skipped. Keep normal reuse enabled; do not rebuild for documentation/scripts.

Next implementation task: add bounded edit-to-visible latency evidence for the
existing N2/H2 border-edit workloads. Associate accepted edits with all affected
current mesh revisions, distinguish renderer submission from unavailable physical
presentation, and retain superseded/cancelled/timeout outcomes without false zeroes.
Acceptance: bounded tracking; cloud regressions for border meshes and stale results;
unchanged workloads/thresholds; matching Windows candidate; exact-build target
measurements before claiming the edit-visibility gate passed. Preserve save and
generator compatibility. This remains M1 work.

Inspect `AGENTS.md`, `TESTING.md` sections 7–8, `PERFORMANCE.md`,
`docs/M1_TARGET_REVIEW.md`, `docs/M1_OPERATION_DIAGNOSTICS.md`,
`game/scripts/benchmark.gd`, `benchmark_trace_tests.gd` (same script directory),
`native/sandbox_world/godot/m1_hooks.h`, `benchmark_probe.cpp`, `fixture_generator.cpp`
(same native directory), and `build/patches/voxel/m1-admission.json`.

Recommended next model: **Sol Extra High** for bounded instrumentation across
edit revisions, native meshing and rendered-frame evidence. No architectural
redesign or Astra escalation is currently justified.
