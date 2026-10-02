# Development handoff

- Branch: `codex/m1-engine-proof`; head reviewed:
  `ce87bf3c50486ec04a5edcc7497dff72c60d4041`.
  Runtime implementation: `1a03f16747fa01563150b8a03f6cf6a219718312`.
- Milestone: **M1 blocked; target not qualified**. Indexed-upload candidate:
  cloud checks passed; exact-build laptop baseline reviewed privately.
- Latest successful [CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
  passed all three jobs. [Windows player 11186079360](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11186079360)
  exports game build `25e4501360187b3a6afc56e507ac74f841c788b7`.
  Artifact expires 2026-10-31, 18:52 UTC.

Completed this session: validated the uploaded baseline against the release
artifact's build identity and executable/PCK hashes; reconciled raw frame,
operation, edit, callback/finalization and coverage evidence with its summary.
No integrity errors were found. Accepted edit submission met its latency gate
in this run, with no missing-data movement stops. Saved the detailed review
privately; no runtime code, settings, workloads or formats changed.

Inspected pinned `VoxelTerrain::process_viewers`: it centers visual demand on
the floored mesh-block coordinate. At fractional positions its positive edge
falls short of the fixed world-space viewing distance. Frontier traces identify
unready required blocks outside that requested box. This is an attributable
coverage-admission defect; correction does not by itself qualify coverage.

Failed: conservative H1/H2 mesh coverage and isolated individual upload limits;
one normal phase also exceeded the tracked upload/deletion frame allocation.
Unverified/inconclusive: attribution of raw frame/paced misses, actual exposed
pixels and rendered fog boundary, full diagnostic overhead, deferred renderer
costs, allocation/retention qualification and all-profile target repeats.
Latest CI failures: none. No local engine build or game execution.

**Single next implementation task:** correct native world-space visual demand
bounds and derive its required meshing-data halo. Preserve the established
viewer/demand-difference lifecycle, 96 m visual radius, 128 m data prefetch,
workloads and admission ceilings. No additional laptop run is needed before
implementing and producing this candidate.

Acceptance:

- Geometry/property regressions cover fractional, exact-boundary and negative
  positions for 16/32 render blocks and clipped fixture bounds; every block
  intersecting the required visual envelope is demanded with its data halo.
- Existing geometry, edits, collision, eviction/cancellation and all four cloud
  profiles pass; resident regions/objects and queue/payload limits remain bounded
  under unchanged ceilings. Matching binaries and a portable Windows artifact
  are produced by GitHub Actions.
- Keep frustum corners, exponential-fog limitations and remaining timing failures
  explicit; do not weaken readiness or declare M1 qualified from this partial fix.

Inspect `build/patches/voxel/m1-admission.json`, pinned upstream
`terrain/fixed_lod/voxel_terrain.cpp` (`process_viewers`),
`native/sandbox_world/godot/benchmark_probe.cpp`,
`game/scripts/benchmark_frontier.gd`, `game/scripts/m1_native_tests.gd`,
`game/scripts/benchmark.gd`, `docs/M1_FOG_FRONTIER.md`, `docs/M1_TESTING.md`,
`docs/M1_EVIDENCE.md` and `PERFORMANCE.md` sections 2-6.

Next model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
This is bounded native integration; no specialist escalation is demonstrated.
