# M1 engine experiment evidence

Current milestone status: **blocked; target not qualified** after the
[five-run laptop review](M1_TARGET_REVIEW.md) on 2026-09-26. The candidate's
immutable cloud result remains **cloud_passed_target_unverified** from
[GitHub run 36183549961](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961),
completed successfully on 2026-09-25. This is not an M1 target-performance pass.
Run status, completed job logs, artifact metadata and downloaded player/evidence
archives were inspected on 2026-09-25.

## Current Windows candidate

Download [player artifact 10889930434](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889930434),
then extract the contained `Cairn-windows-x86_64.zip` into a fresh folder.
GitHub reports an expiry of **2026-10-25 21:58 UTC**; retention can change.
The artifact includes the portable ZIP, `SHA256SUMS.txt` and `BUILD_INFO.json`.

| Identity | Verified value |
| --- | --- |
| Source branch commit | `68918f2a8ad63325b2be7d4c02ce05fa753aef63` |
| Exported synthetic merge / game build ID | `6874b8809094d22b33e05c60ef61c2e1c333494a` |
| Native source key and actual embedded engine identity | `6adda08d3b832e3e5c40a41fd5b7bcd527bd2d1d6b274cd37b039a2371b61d7f` |
| Godot source | `ed1daf0bf001b61586d9930840f2f1394092c079` |
| Voxel Tools source | `2ac9f5f8a8219bf499314cc0fad54ffc47df908f` |
| Inner portable ZIP SHA-256 | `0dd72b172cade30c7a0a7fb8b005490fac39567ff8afcc0f049c209561b4346b` |
| Inner portable ZIP size | 29,892,003 bytes |
| Outer Actions player archive SHA-256 | `c0c4ee6ab2f15aaf1067ccad281416d6888ad446434966915eda4533530e5c92` |

The downloaded outer archive matched GitHub's digest. The inner ZIP was hashed
independently and matched both `SHA256SUMS.txt` and `reports/candidate.json`.
These are different archives and checksums. The current engine identity is the
new source key above; the historical legacy identity was not used by this build.

Supporting artifacts are [export evidence 10889685801](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889685801),
[separate symbols 10888974332](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888974332)
and [native reuse evidence 10888649212](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888649212).
The export evidence archive SHA-256 is
`d7d2414bcd7cb2b7f9f266721380f74961419a74793943c6ab33267aa4772837`,
also verified after download.

## Executed cloud checks

The follow-up static job `108264637172` passed all 12 packaging/native-reuse
regression tests, Python compile checks and native fixture checks with address
and undefined-behaviour sanitizers on Linux.

Native job `108264737945` restored the exact cache and requalified the custom
editor and both Windows templates. Compiler installation and native compilation
were skipped. It reused native artifact `10888733603` from the successful producer
[run 36180365572](https://github.com/dponcho/voxel-survival-game/actions/runs/36180365572);
the follow-up's native-bundle upload was skipped too.

Windows export job `108264995129` downloaded that same producer artifact and
verified its digest and bundle identity/files. It passed:

- All 12 Windows packaging/native-reuse regression tests.
- Matching-editor import, module self-tests and native split-mesher coverage.
- Debug/release scenario smoke and all four render-block/worker profile
  **cloud integration/correctness checks**.
- Streaming collision, edits, eviction and cancellation integration checks.
- Executable dependency audit and both fresh offline extraction self-tests,
  including paths with spaces/non-ASCII characters and a different working directory.
- Portable player ZIP, separate symbols and evidence publication.

`reports/candidate.json` records `native_bundle_source: cache`,
`cold_cache: false`, `status: cloud_passed_target_unverified` and
`target_performance: not_run`. Both extraction reports have `passed: true`,
no errors and the expected build/native identities.

The producer also passed its static, native qualification and separate export
jobs. Its source commit was `f7a02589601a9339c9bdf54c135f9e3d949c99f3`, exported
as `4aeb6029b602328c439815c99864cc93c167c5c9`. The latest candidate above adds
actual window-size reporting without changing native inputs. It includes the
recent N3 rotation, fixture-fall detection, comparison-launch failure reporting,
fixed 720p window and stronger mesher checks. The current cloud results supersede
their previously pending validation status. See the [CI architecture evidence](CI_ARCHITECTURE.md#acceptance-evidence)
for the exact bundle, reuse proof and remaining fallback-path limitation.

## Scope and remaining target evidence

Hosted Windows rendered smoke was **not run**. The user supplied one standalone
baseline and a complete four-profile comparison from the actual i7-7600U / HD 620.
All five report identities and executable/PCK hashes match this candidate;
1,682,025 CSV rows were independently checked against their summaries. See the
[target review](M1_TARGET_REVIEW.md) and [machine-readable results](evidence/m1-target-2026-09-25-review.json).
Frame-rate capacity, memory and recorded collision/readiness results are promising,
but lifetime native timing contaminates scenario outcomes, diagnostic overhead is
inconclusive and frame-pacing/other required observations remain unresolved.
No profile is qualified and M2 remains gated.

The experiment uses stock blocky meshing with bounded split uploads, not greedy
meshing. Every comparison uses the finite fixture slab Y [-16,32), visual radius
96 m and data radius 128 m. Edits use a bounded temporary session overlay; actor,
weather and storage workloads are proxies. There is no durable save format or
complete-world vertical qualification. The runtime/native inputs are unchanged by
this review. The user's [2026-09-26 Java core requirements](JAVA_CORE_REFERENCE.md)
apply to future implementation and do not retroactively change this candidate.

The next bounded task is the diagnostic attribution/overhead correction described
in the target review. Do not request another four-profile run or the final three
qualification repeats until the corrected evidence path is ready. The
[laptop guide](M1_TESTING.md) remains the procedure for the next exact-build
candidate. A startup-check pass alone does not qualify M1.

## Earlier candidate history

[Run 34036830778](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778)
and Windows job `101496360796` passed the earlier native build, integration and
portable-package checks on September 6. Source commit:
`fe5cadc2876fc5a889c72b097373f544f4ed9fff`; exported synthetic merge:
`4e6c761c26950111ffd6af1bd496c81a6c9ed04b`; legacy native identity:
`f90df9f55adb77e131cd1f575a50caded0e8fbd17f5b0f96877e7884320197b1`.

Its [player artifact 9992504297](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992504297)
had outer archive SHA-256
`005138342e079611dee69bf1ae0c88a0eb245685e49b4d85aacb950577b86504`
and recorded expiry 2026-10-06; availability was not rechecked in this continuation.
Its [evidence artifact 9992510088](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992510088)
and the earlier failed run `34003770515` / corrective run `34007283054` remain
historical provenance. Use the current September 25 candidate for new laptop tests.
