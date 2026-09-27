# Development handoff

- Branch: `codex/m1-engine-proof`.
- Implementation commit: `3685dd472e5ffd3429ba5d35b7ee63c949b374e5`.
- Milestone: M1; target remains blocked/not qualified. M2 is gated.
- Latest successful CI: [36280383637](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637).
- Corrected [Windows artifact 10920027865](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920027865);
  exported build `b65ba3e409ba7a80da282b5297783533de2f6fc6`.
  Subsequent handoff/evidence commits are documentation-only.

Completed implementation: phase-local upload/deletion maxima without subtracting
lifetime maxima; bounded native frame records and streamed operation evidence;
separate preparation/gameplay/diagnostic/retirement phases; explicit completion
versus qualification; native regression tests and real CSV reconciliation in the
existing smoke route. Linux sanitizer regressions, 12 Linux/Windows packaging/cache
tests, matching editor/templates, debug/release smoke and trace reconciliation,
all four correctness profiles, streaming/collision/edits/eviction/cancellation,
dependency audit and fresh offline extractions passed. Lifetime counters,
thresholds, workloads and save/generator behavior are preserved. No M2 work was done.

Native key: `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803`.
Qualified native artifact: `10920566667` from the same run; its exact cache was
saved. Keep normal reuse enabled; do not rebuild for docs or script-only fixes.

Blockers: the previous target reports failed qualification and their A/B overhead
comparison was inconclusive. Corrected exact-build target measurements, edit
visibility, pacing/driver attribution, allocation completeness and retention/
qualification repeats remain unverified. No automated check in the new run
failed. The exact corrected build has not been tested on HD 620. Preserve old
evidence and all acceptance thresholds.

Next implementation task: complete end-to-end diagnostic-overhead accounting and
the bounded A/B comparison. Include currently omitted report/UI work, retain
equivalent required evidence, and make unstable comparisons explicitly inconclusive.
Acceptance: cloud regression coverage for measurement boundaries and A/B outcomes;
unchanged simulation/workload and thresholds; matching Windows candidate; exact-
build target evidence before claiming less than 1% overhead or M1 qualification.

Inspect `AGENTS.md`, `TESTING.md` section 8, `PERFORMANCE.md`,
`docs/M1_TARGET_REVIEW.md`, `docs/M1_OPERATION_DIAGNOSTICS.md`,
`game/scripts/benchmark.gd`, `game/scripts/benchmark_evaluation.gd`,
`game/scripts/benchmark_trace_tests.gd`, and
`native/sandbox_world/godot/report_sink.cpp`.

Recommended next model: **Sol Extra High**. This is bounded performance
instrumentation and cross-component timing work; no architectural redesign or
Astra escalation is currently justified. Reassess after concrete failures.
