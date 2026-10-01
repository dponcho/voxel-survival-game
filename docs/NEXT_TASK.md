# Development handoff

- Branch: `codex/m1-engine-proof`; head when prepared:
  `4660a193656ff6164fb9b4262c18f2521af13547`.
  Runtime implementation: `1a03f16747fa01563150b8a03f6cf6a219718312`.
- Milestone: **M1 blocked; target not qualified**. Indexed-upload candidate:
  **cloud_passed_target_unverified**.
- Latest successful [CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
  passed all three jobs. [Windows player 11186079360](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11186079360)
  exports game build `25e4501360187b3a6afc56e507ac74f841c788b7`.
  Artifact expires 2026-10-31, 18:52 UTC.

Completed: indexed vertex reuse within existing 1,024-triangle batches, preserving
triangle order, attributes, materials and draw/surface counts. Invalid indices
and channel layouts fail admission; scratch is bounded to a 384 KiB lookup plus
24 KiB batch arrays per mesh worker. Upload/retirement estimates count actual
vertices/indices with tangent reserve; no renderer readback. Full quad batches
estimate 143,360 rather than 208,896 bytes. This is data-size reduction, not a
target timing result. Settings, workloads, budgets and save/generator formats
are unchanged.

This continuation finished verification: 12 packaging/cache regressions, Python
compile checks and four native sanitizer suites passed; matching editor/debug/
release binaries were built and qualified. Engine attribute/AO/winding and
multi-batch/border/surface-count tests passed. All four profiles, streaming,
collision, edits, eviction/cancellation, dependency audit and fresh offline
extractions passed. Five smoke exports reconciled saved reports; all accepted
N2/H2 edits submitted with zero pending/cancelled/timed-out edits at closure.
Downloaded player/export/native evidence digests, ZIP CRCs, checksums,
manifest hashes and build identities matched. No local engine build or execution.

Failed in this CI: none. Prior target upload/coverage failures and raw deadline
misses remain unresolved evidence. Unverified: this candidate's HD 620 upload/frame
costs, rendered coverage, edit deadlines, full diagnostic overhead, allocation/
retention and final repeats. Uploaded target details remain private.
Native key: `bb20d80d8e527335a7cb2e9a728c0eb1328812fd0650b66dcc494daea121763b`.

**Single next task / implementation gate:** review one exact-build 32³/one-worker
laptop baseline and identify the highest-priority remaining M1 blocker.
Further implementation waits for that evidence; do not request full comparisons
or qualification repeats yet.

Acceptance: matching build identity, complete summary/finalization and CSV/edit
evidence; review scoped upload/frame costs, raw deadline misses, edit submission,
coverage and overhead against unchanged gates. Select one attributable failing
gate for the next bounded fix; retain unverified results as unverified.

Inspect `docs/M1_TESTING.md`, `docs/M1_EVIDENCE.md`,
`docs/M1_OPERATION_DIAGNOSTICS.md`, `PERFORMANCE.md` section 3,
`native/sandbox_world/core/mesh_batch.h`,
`native/sandbox_world/godot/fixture_generator.cpp`,
`native/sandbox_world/godot/m1_hooks.h`, `build/patches/voxel/m1-admission.json`,
`tests/native/test_mesh_batch.cpp` and `game/scripts/m1_native_tests.gd`.

Next model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
