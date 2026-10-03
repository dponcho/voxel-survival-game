# Development handoff

- Branch: `codex/m1-engine-proof`; head when prepared / verified implementation: `f1fea7bc56dc7aeef4f372e26baada84bbce7132`. The handoff commit is documentation-only.
- Milestone: **M1 blocked; no target profile qualified**. Finite shader-matched fog and correctness regressions passed cloud verification; portable candidate produced.
- Latest successful [CI 37160455260](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260) completed on 2026-10-03 UTC; all three jobs passed.
- [Windows player 11287845333](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287845333): extract the contained portable ZIP. Expiry: 2026-11-02 at 23:10 UTC.
- Game build ID: `c1a71cdf77fe4ee9810eff3573f93460c9c2cc0a`; native key: `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.

Completed this session: configured the actual Environment with Compatibility radial depth fog, begin 16 m / opaque end 96 m, density 1, curve 1 and no height fog. Reports now record actual settings, including the formerly hardcoded density. Added independent smoothstep, exact-boundary, actual-Environment and saved-report regressions. Inside-boundary pending meshes still fail; disabled, invalid and unavailable inputs remain inconclusive. Updated fog semantics and current artifact links. Demand remains 96/128 m; resolution, routes, ticks, workloads and caps remain.

Verified: 12 packaging/cache regressions, Python compile checks, five native sanitizer suites; exact native cache reused and matching editor/debug/release binaries independently requalified. Engine fog/geometry/edit/collision/eviction/cancellation checks, all four streaming profiles, 20 demand cases and four mesh-only halo checks passed. Five smoke exports completed without integration failures; all accepted N2/H2 edits submitted without cancellation, timeout or pending edits at closure. Saved-report reconciliation, dependency audit and two fresh offline extractions passed. Downloaded checksums/CRCs, build identities and native hashes matched. No local engine installation, compilation or execution.

Failed checks: both 16³ cloud smoke profiles retain H1/H2 conservative coverage failures from pending regions just inside 96 m. Short 32³ cloud coverage checks pass; this does not establish target coverage. Prior target individual upload/time-budget failures remain unresolved. No CI test failed. Unverified: this candidate's HD 620 rendering/performance, moving-frontier readiness, full heavy diagnostics overhead, retention and qualification repeats; hosted render smoke was not run. Frame/pacing attribution and A/B remain inconclusive.

**Single next implementation task:** isolate the next failing M1 gate from this exact-build 32³/one-worker laptop baseline and implement one bounded correction. Prerequisite: user runs startup/exploration, then **Run performance check (~24 min)** and supplies the complete report folder plus visual observations. Review that baseline before another full matrix; do not choose an upload/frontier fix from obsolete target measurements.

Acceptance: verify build identity and reconcile raw CSV/operation/fog evidence; confirm the reported 96 m boundary and retain genuine readiness failures. Attribute the selected failure before changing code. Preserve required workload, demand and caps; add a meaningful regression for the correction and pass affected cloud/portable checks. Separate correctness, failed gates and unverified target qualification.

Inspect `docs/M1_TESTING.md`, `docs/M1_EVIDENCE.md`, `docs/M1_FOG_FRONTIER.md`, `docs/M1_OPERATION_DIAGNOSTICS.md`, `game/scripts/benchmark.gd`, `game/scripts/benchmark_frontier.gd`, `game/scripts/benchmark_trace_tests.gd`, `native/sandbox_world/godot/m1_hooks.h`, `native/sandbox_world/core/mesh_batch.h` and `PERFORMANCE.md` sections 2 and 6.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default. No demonstrated specialist escalation is needed.
