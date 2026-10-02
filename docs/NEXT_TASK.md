# Development handoff

- Branch: `codex/m1-engine-proof`; head when prepared: `f1a476f87225cb5e36ebfe54670d142c0e73ff53`.
- Verified implementation: `c1ad85b55359a3e013ef43d017223116617a0bca`.
- Milestone: **M1 blocked; target not qualified**. World-space demand and meshing-data halo correction passed cloud verification; portable candidate produced.
- Latest successful [CI 37024767302](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302) completed on 2026-10-02 UTC; all three jobs passed.
- [Windows player 11242141810](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242141810): extract the contained portable ZIP. Expiry: 2026-11-01 at 17:25 UTC.
- Game build ID: `77be48ed0ac431da50f7fd9d267873feee403123`; native key: `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.

Completed: native demand covers the actual viewer position at fixed 96 m visual and 128 m data-only radii. Meshing data covers every demanded render block plus its existing neighbour halo. Clipping precedes coordinate narrowing; empty demand creates no halo. Consolidated two overlapping patch pairs with identical emitted code and verified repeat application against pinned source. Existing reference/cancellation lifecycle, budgets, settings and formats remain.

Verified: 12 packaging/cache regressions, Python compile checks and five native sanitizer suites; fresh matching editor/debug/release builds and qualification; native geometry, collision, edits, eviction/cancellation and all four profiles. Engine logs contain 20 passing demand cases, including fractional, negative, exact-boundary and clipped-corner positions, plus four mesh-only halo checks. The fractional pose requires 507 regions at 16³ or 98 at 32³ in the clipped M1 fixture, within unchanged caps. Five smoke exports completed with no integration failures; every accepted N2/H2 edit submitted. Dependency audit and two fresh offline extractions passed. Downloaded archive checksums/CRCs, build identities and native binary hashes matched. No local engine installation, compilation or execution.

Failed checks: prior target heavy-coverage and individual upload/time-budget checks have no new target evidence resolving them. Current CI has no failures. Unverified: this candidate's HD 620 rendering/performance and moving-frontier readiness. Prior frame/pacing attribution and A/B remain inconclusive; full heavy diagnostics overhead, allocation/retention and qualification repeats remain unverified. Exponential fog is unchanged and has no finite analytic opaque boundary. Settled cloud coverage does not qualify M1.

**Single next implementation task:** implement a finite, shader-matched M1 fog boundary at 96 m. Keep genuine inside-boundary missing/pending mesh failures observable. Do this before requesting another laptop baseline or full matrix.

Acceptance: pinned Compatibility shader reaches terminal opacity 1 at the recorded boundary; before/at/after-boundary tests and saved CSV reconciliation agree; invalid/unavailable inputs remain inconclusive; inside-boundary unready meshes still fail. Preserve 96/128 m demand, resolution, routes, ticks, workloads and resource/time caps. All four cloud profiles and portable checks pass with the matching native cache; produce a new candidate. Rendered target proof remains unverified until its report exists.

Inspect `game/scripts/benchmark.gd`, `game/scripts/benchmark_frontier.gd`, `game/scripts/benchmark_frontier_tests.gd`, `game/scripts/benchmark_trace_tests.gd`, `game/scripts/m1_streaming_tests.gd`, `docs/M1_FOG_FRONTIER.md`, `docs/M1_EVIDENCE.md` and `PERFORMANCE.md` sections 2 and 6.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default; this bounded GDScript/fog integration does not require specialist escalation.
