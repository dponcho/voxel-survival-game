# Development handoff

Branch: `codex/m1-engine-proof`. Milestone: **M1 blocked; no target profile qualified**.

The authorized October 3 baseline handoff was published. This increment verifies
the exact pinned Godot desktop shader path and adds a separately labelled
conversion-model verdict, actual rendering-driver identity, independent evaluator
regressions, saved-CSV reconciliation and an optional cloud conversion readback.
Raw analytic coverage, CSV columns, fog, radii, settings, workloads and caps remain.
World/save versions and the native source key are unchanged.

Correction: the default desktop `opengl3` Compatibility shader uses a truncating
`float2half` polyfill, not nearest binary16 rounding. Under that confirmed-path
assumption, complete baseline replay retains 352 H1 and 527 H2 alarms at packed
transmittance 0.00048828125. Another eight H1 and nine H2 analytic alarms convert
to opacity one but remain inconclusive because shader arithmetic and clipped
coverage are unverified. The old report lacks exact driver identity. None of
these conservative region alarms establishes visible pixels; none qualifies M1.

Verification in progress: 18 Python regressions, compile checks and diff checks
pass. Native key remains
`11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d`.
The matching-editor/cloud/portable candidate checks are pending; replace this
paragraph with the inspected CI and artifact identities before task completion.
Until then the last inspected player is [11287845333](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287845333).

Failed recorded gates remain analytic H1/H2 coverage and isolated target upload
limits/one terrain subtotal. Unresolved: startup warm-up hitch (184.252 ms),
one near-deadline gameplay interval, physical pacing, unstable flat A/B,
heavy diagnostic overhead, allocation/deferred-renderer accounting, retention,
profile comparison and qualification repeats. Headless or hosted conversion
evidence cannot certify HD 620 terrain rendering or speed.

**Single next implementation task:** add bounded first-use/startup attribution
around the early warm-up hitch. Separate loading/preparation from gameplay;
retain the complete callback interval, native work and diagnostic timing, and
explicitly label unavailable engine/driver/OS attribution. Do not absorb the
hitch into an average, hide it with warm-up, add unbounded samples, or change
terrain demand/caps. Independently test phase boundaries and saved timing
reconciliation, then run the affected cloud/export/portable checks. Reuse the
existing baseline for this reporting task; another full matrix is premature.

Rain remains an M1 proxy defect deferred to M5. `TESTING.md` now requires motion
review for repetition, synchronized resets, popping, flicker and responsiveness,
and measured optimization benefit with preserved behaviour. No pass percentage
overrides a failed gate. Moving-frontier readiness and upload optimization still
need evidence after attribution is trustworthy.

Read `AGENTS.md`, `docs/M1_FOG_FRONTIER.md`, `docs/M1_EVIDENCE.md`, `PERFORMANCE.md`,
`TESTING.md`, `game/scripts/benchmark.gd`, `game/scripts/benchmark_diagnostics.gd`,
`game/scripts/benchmark_trace_tests.gd` and the existing operation phase metrics.

Model: **GPT-6.1 Sol Max** (`gpt-6.1-sol`, effort `max`), the user's default.
