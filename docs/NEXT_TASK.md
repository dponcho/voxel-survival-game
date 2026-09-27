# Development handoff

- Branch: `codex/m1-engine-proof`.
- Current HEAD: `d1cffbe107e3afd333b33f132c6de8d7ecfb3e75`.
- Session implementation is **uncommitted and unpublished** in the working tree.
- Milestone: M1, blocked/not qualified; M2 remains gated.
- Latest successful CI: [36280383637](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637).
- Latest verified [Windows artifact 10920027865](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920027865),
  exported build `b65ba3e409ba7a80da282b5297783533de2f6fc6`.
  This artifact predates and does **not** validate this session's changes.

Implemented locally: complete callback timing through CSV formatting/submission
and live UI; previous-callback CSV attribution with final-callback reconciliation;
measurement writer drain before retirement; separate final report/hash/write/UI
timing; bounded timing blocks and A/B histograms in both modes. A/B evaluation
now checks both repeats, within-phase drift, workload completeness, evidence loss,
apparent speedups and threshold-crossing ranges. Added deterministic accounting/
classification tests and actual CSV reconciliation to existing cloud test routes.
Updated measurement documentation. Preserved native inputs, thresholds, workload,
generator/save behavior and unrelated local `HANDOFF.md`.

Verification: `git diff --check` passed. No local compilation, game execution or
test suite ran. New GDScript import, regressions, debug/release smoke, integration
and Windows packaging remain **unverified**, not failed. M1's earlier target
reports failed qualification; exact-build overhead, edit visibility, pacing/driver
attribution, allocation completeness and retention/repeats remain unverified.

Publication is explicitly approved by the user for existing public PR #2.
This supersedes the initial automatic approval rejection. Publication and cloud
verification are proceeding; the final handoff will record verified identities.

Next task: finish cloud validation
of this diagnostic-overhead increment and fix any concrete failures before adding
features. Acceptance: import and accounting/A-B regressions pass; debug/release
smoke reconciles actual CSV/summary totals; existing integration/package checks
pass; publish a matching portable Windows candidate. Preserve all workloads and
thresholds. Claim neither <1% total overhead nor M1 qualification without exact-
build target evidence; shared baseline/deferred costs remain explicitly limited.

Reuse native key
`3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803`;
qualified artifact `10920566667` from the successful run above was rechecked as
unexpired. Keep normal reuse enabled. No native rebuild is justified by these
script changes.

Inspect `AGENTS.md`, `TESTING.md` section 8, `docs/M1_OPERATION_DIAGNOSTICS.md`,
`game/scripts/benchmark.gd`, `benchmark_diagnostics.gd`,
`benchmark_evaluation.gd`, `benchmark_diagnostic_tests.gd`,
`benchmark_trace_tests.gd`, `m1_native_tests.gd` (all under `game/scripts/`),
and `.github/workflows/windows-build.yml`.

Recommended next model: **Sol High** for cloud validation and isolated fixes to
the implemented design. Use **Sol Extra High** if concrete timing/integration
failures require deeper investigation; no Astra escalation is currently justified.
