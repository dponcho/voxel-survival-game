# Development handoff

Branch: `codex/m1-engine-proof`. Milestone: **M1 blocked; no target profile qualified**.

Completed bounded startup attribution: six logical initialization/preparation/
warm-up/retirement/N1 groups, first 64 intervals plus one maximum per group,
bounded script/physics/render-signal spans, overlap/outside-stage accounting,
explicit phase crossings and unknown asynchronous renderer origins. The title
offers **Run startup timing check (~20 s + loading)**, two shortened routes in a
fresh process. Normal baseline/matrix durations and all workload/demand/budget,
CSV, world/save and native inputs remain. Read [semantics](M1_STARTUP_ATTRIBUTION.md).

Two exact-build HD 620 short startup repetitions were reviewed October 6.
Both complete without integration failures. The historical 184.252 ms stall
did not recur; smaller early warm-up hitches recur in both, mostly inside the
render-signal bracket. Both shortened prepared N1 routes retain zero deadline
misses. Raw CSV/diagnostic/native accounting, 585 retained timing partitions and
260 interval joins reconcile. No overflow, invalid/dropped spans or unmatched
signals occur. A recurring early rendering/wait delay is observed; background,
driver/shader cause and physical presentation remain unverified. Callback/viewport
times are wall elapsed, not CPU service. Neither the historical stall nor the
smaller repetitions are waived. Detailed target reports remain private.

Latest code: `4df6cc2042f9778350b8ade48b16872c052e7c2a`.
[CI 37225602689](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689)
passed all three jobs on October 4. Eighteen Python regressions, five native
sanitizer suites, matching-editor/evaluator/trace checks, all four profiles, the
short release route, debug/release exports, DLL audit and two fresh offline
extractions pass. The initial JSON verifier type mismatch was corrected and has
a round-trip regression. Six reports complete without integration failures or
startup overflow/invalid/dropped spans; 1,632 retained partitions were independently
checked. Both 16³ profiles retain analytic coverage failures; every headless
renderer-model verdict is inconclusive and OpenGL readback remains unavailable.

[Windows player 11311923130](https://github.com/dponcho/voxel-survival-game/actions/runs/37225602689/artifacts/11311923130)
expires November 3 at 18:53 UTC. Verified build ID:
`b7506f9ca2184ee3d59fa5cb1b8fcdd1914182b2`; portable ZIP SHA-256:
`5d92cdcb885c2243015ae9ef856e4e774f1f6f32271ff999658c1d3d45b40437`.
Native key remains `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
Downloaded archives, checksums, identities, native registrations and smoke reports
match. [Evidence](M1_EVIDENCE.md) retains exact provenance and earlier candidates.

No full target baseline/matrix is requested solely for this reporting increment.
The two requested startup repeats are now reviewed; no further startup run is
requested solely for this review. Startup overhead is unqualified by the later
flat A/B. Failed recorded gates still include analytic H1/H2 coverage
and isolated target upload limits/one terrain subtotal. Unresolved: pacing,
unstable flat A/B, heavy diagnostics cost, allocation/deferred-renderer accounting,
retention, profile comparison and qualification repeats. The truncating desktop
shader model preserves analytic alarms; it does not establish visible pixels.
The short repeats also retain preparation/retirement individual-operation budget
exceedances, outside measured gameplay. Callback wall fractions are not a causal
estimate of added diagnostics cost. Rain remains an M1 proxy defect deferred to
M5. No gate or visual motion review is replaced by an overall pass percentage.

**Single next implementation task:** add a matched heavy-route diagnostic cost
comparison. The existing flat A/B cannot qualify the per-frame H1/H2 frontier
scan. Keep fixtures, routes, actors, edits, resolution, radii, ticks and admission
caps equivalent; bound storage and separately account the switched probe and
shared instrumentation. Missing coverage samples must remain explicitly
unavailable, never a passing zero. Independently verify matched workload, phase
accounting, stability and saved-report reconciliation, then run affected cloud/
export/portable checks. Target overhead and coverage still need actual HD 620
evidence; another full matrix is premature until these measurements are trustworthy.

Read `AGENTS.md`, `PERFORMANCE.md`, `TESTING.md`, `docs/M1_FOG_FRONTIER.md`,
`docs/M1_STARTUP_ATTRIBUTION.md`, `game/scripts/benchmark.gd`,
`game/scripts/benchmark_diagnostics.gd`, `game/scripts/benchmark_frontier.gd`
and the existing operation/evaluation/trace tests.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
