# Development handoff

- Branch: `codex/m1-engine-proof`; verified implementation:
  `7024be977653ffbe03376cda215323be58cb6835`.
  Head before this documentation update:
  `5232367577b1c351354009674215af09692b37c3` (documentation only).
- Milestone: **M1 blocked; target not qualified**. Fog/frontier instrumentation
  is cloud verified; M2 remains gated.
- Latest successful [CI 36775406042](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042)
  published [Windows player 11131500525](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131500525)
  (expiry 2026-10-30 23:08 UTC). Exported PR merge/build ID:
  `e51d00d0d3e847e4b1c04362df6642eef695c3ad`.

This session completed bounded H1/H2 mesh-frontier evidence: submitted and
confirmed-empty readiness, explicit missing/pending/hidden regions, camera pose,
conservative distance, analytic fog transmittance and available boundary/clearance
values. Schema 5 adds fog-crossing/invalid-input regressions and saved CSV/summary
reconciliation. All 33 ordered Voxel Tools patches matched the pinned source.
All three CI jobs passed: packaging/cache regressions and native sanitizers,
matching editor/debug/release build and qualification, import, native/evaluation
tests, debug/release smoke, all four streaming profiles, dependency audit and
two fresh offline extractions. Settings, thresholds, workloads and save/generator
formats are unchanged. No local engine compilation or game execution ran.

**Failed:** no check failed in this CI run. Coverage gaps before analytic opaque
fog fail the conservative coverage check. The analytic exponential model has no
finite opaque boundary; missing boundary evidence stays inconclusive.
Box/frustum overlap and pre-half-packing transmittance do not prove pixel
visibility or rendered opacity.

**Unverified:** independent candidate download/hash; exact-build HD 620 coverage,
edit latency, diagnostic overhead and pacing; shader/driver precision, allocation
completeness, driver retention and final qualification repeats. No corrected
target baseline from the previous candidate was supplied. Cloud success does
not qualify M1.

**Single next implementation task:** add a bounded H1/H2 diagnostic-overhead
comparison including the frontier probe, after reviewing one corrected exact-build
target baseline. Existing flat-fixture A/B phases cannot qualify heavy-only costs.

Acceptance: compare identical heavy routes/settings/workloads with diagnostics
off/on; include probe, formatting, writer drain and final callback costs; retain
raw misses and unstable/incomplete outcomes; preserve the 1% overhead gate;
cloud integration and Windows packaging pass with a matching candidate. Keep
target qualification unverified until its exact-build HD 620 report is reviewed.

Inspect `docs/M1_FOG_FRONTIER.md`, `docs/M1_EVIDENCE.md`,
`docs/M1_OPERATION_DIAGNOSTICS.md`, `PERFORMANCE.md` sections 6/8,
`TESTING.md` sections 7/8, `game/scripts/benchmark.gd`,
`game/scripts/benchmark_frontier.gd`, `game/scripts/benchmark_evaluation.gd`,
`native/sandbox_world/godot/benchmark_probe.cpp` and
`build/patches/voxel/m1-admission.json`.

Recommended next model: **Sol High**. This is bounded diagnostic integration with
established gates; increase effort only for a substantive attribution or engine
integration problem.
