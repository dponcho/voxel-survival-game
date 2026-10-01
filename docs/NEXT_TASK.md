# Development handoff

- Branch: `codex/m1-engine-proof`; runtime/head before this checkpoint:
  `1a03f16747fa01563150b8a03f6cf6a219718312`.
- Milestone: **M1 blocked; target not qualified**. Indexed-upload implementation
  is in verification. [CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
  is running its native Windows rebuild.
- Latest successful [CI 36803692007](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007)
  and [Windows player 11137310682](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11137310682)
  contain the previous lifecycle correction, **not** the indexed optimization.

Implemented this session: preserve source vertex reuse inside the existing
1,024-triangle batches; retain triangle order, attributes, surface/material order
and draw count. Worker-local scratch is bounded to a 384 KiB lookup and 24 KiB
batch arrays. Invalid indices/channel layouts fail admission. Upload/retirement
payload estimates count actual vertices and indices, with conservative tangent
reserve; no renderer buffer readback. Full quad batches estimate 143,360 bytes
instead of 208,896. This proves data-size reduction, not target timing improvement.
No settings, workload, face/queue/time/byte caps, generator or save format changed.

Verified: 12 packaging/cache regressions, Python compile checks and four native
sanitizer suites passed in this CI. The new remap suite checks full batches,
reconstruction, batch resets, malformed indices, bounds and payload accounting.
Changed ordered upstream patch groups matched pinned source. Native source key:
`bb20d80d8e527335a7cb2e9a728c0eb1328812fd0650b66dcc494daea121763b`.

Failed checks this session: none. Pending/unverified: matching editor/debug/release
builds; engine geometry/AO/UV/color/tangent and unchanged-surface-count tests;
exported lifecycle/streaming/edit/collision checks, offline package checks, candidate
hashes and HD 620 timing. Prior target upload/coverage failures and raw deadline
misses remain evidence. Detailed uploaded-report/hardware data remain private.
No local engine compilation or execution occurred.

**Single next task:** finish verification of the indexed-upload candidate,
then obtain one exact-build 32³/one-worker laptop baseline. No laptop action
is needed before the new Windows candidate passes CI.

Acceptance: native engine attributes/winding/face counts and batch surface counts
match the stock mesher; saved CSV/summary reconciliation, all four profiles,
dependency audit and fresh offline extractions pass. Publish the matching candidate
and assess scoped upload/frame costs, edit acknowledgement, coverage and overhead.
Keep unmeasured improvements and unresolved outliers unqualified. Do not request
full comparisons or qualification repeats yet.

Inspect `native/sandbox_world/core/mesh_batch.h`,
`native/sandbox_world/godot/fixture_generator.cpp`,
`native/sandbox_world/godot/m1_hooks.h`,
`build/patches/voxel/m1-admission.json`, `tests/native/test_mesh_batch.cpp`,
`game/scripts/m1_native_tests.gd`, `game/scripts/benchmark.gd`,
`PERFORMANCE.md` section 3 and `docs/M1_OPERATION_DIAGNOSTICS.md`.

Next model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
