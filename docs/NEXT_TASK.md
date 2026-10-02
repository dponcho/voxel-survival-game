# Development handoff

- Branch: `codex/m1-engine-proof`; implementation/head when prepared:
  `c1ad85b55359a3e013ef43d017223116617a0bca`.
- Milestone: **M1 blocked; target not qualified**. World-space demand fix
  implemented; cloud engine verification and new Windows artifact are pending.
- Active [CI 37024767302](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302):
  static job `110896469348` passed; native job `110896642681` is rebuilding
  editor/debug/release binaries. Native key:
  `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
- Latest fully successful [CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
  and [Windows player 11186079360](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11186079360)
  remain the previous indexed-upload candidate, not this implementation.

Completed: cover render and data-only demand from actual viewer position and
fixed world-space radii; derive meshing-data bounds from demanded render blocks
plus the existing neighbour halo. Clipping precedes coordinate narrowing;
intermediates are widened and empty demand creates no halo. The existing
viewer/reference/difference lifecycle, settings, budgets and formats remain.
Consolidated two overlapping patch pairs with identical emitted runtime code
and verified repeat application against pinned source.

Twelve packaging/cache regressions, Python compile checks and all five native
sanitizer suites passed, including the independent demand/halo geometry oracle.
Engine regressions now check full 96 m visual and 128 m data-only demand,
fractional/negative/exact-boundary positions, clipped world corners and fresh
mesh-only halo loading in all four profiles. These engine checks have not run yet.
No local engine installation, compilation or execution.

Current CI failures: none observed. Unverified: native build/qualification,
engine import and integration, export/offline audit and new artifact. Existing
private target coverage/upload failures remain unresolved by target evidence;
raw frame/pacing attribution, full diagnostics overhead and retention/repeats
remain inconclusive or unverified. Do not declare M1 qualified from this fix.

**Active task to finish:** complete CI 37024767302, repair any concrete failure,
verify the resulting portable player/evidence identities, then update this
handoff with final status and the single next implementation task. Do not start
a duplicate native build while this run is healthy.

Acceptance: matching binaries qualify; geometry, edits, collision,
eviction/cancellation and all four profiles pass under unchanged caps;
Windows packaging and fresh offline extractions pass; exact artifact is verified.

Inspect `native/sandbox_world/core/viewer_demand.h`,
`native/sandbox_world/godot/m1_hooks.h`, `build/patches/voxel/m1-admission.json`,
`tests/native/test_viewer_demand.cpp`, `game/scripts/m1_streaming_tests.gd`,
`docs/M1_FOG_FRONTIER.md`, `docs/M1_EVIDENCE.md` and `PERFORMANCE.md` sections 2-6.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
