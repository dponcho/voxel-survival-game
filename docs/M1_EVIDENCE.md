# M1 engine experiment evidence

Status: **cloud_passed_target_unverified** for the candidate from [GitHub run 34036830778](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778). This is not an M1 target-performance pass.

The Windows job (101496360796) built the custom editor and matching debug/release templates. Native qualification, project import and mesher coverage passed; debug and release scenario smoke passed; all four profiles passed along with collision, eviction and cancellation checks. The dependency audit and fresh offline extraction checks also passed.

Build identity: source branch commit `fe5cadc2876fc5a889c72b097373f544f4ed9fff`; exported synthetic merge `4e6c761c26950111ffd6af1bd496c81a6c9ed04b`; native legacy identity `f90df9f55adb77e131cd1f575a50caded0e8fbd17f5b0f96877e7884320197b1`.

The Windows player candidate is [artifact 9992504297](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992504297), available through 2026-10-06. Its enclosing artifact archive SHA-256 is `005138342e079611dee69bf1ae0c88a0eb245685e49b4d85aacb950577b86504`; this identifies the outer archive, not the player ZIP inside it. The accompanying evidence artifact is [9992510088](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992510088).

These results establish the listed cloud build, integration, package and offline checks. Rendered inspection and execution on the target i7-7600U / HD 620 were not performed; no target fps, frame-pacing, memory or visual-quality claim is made. M1 remains target-unverified until the exact candidate has a target-machine report.

The experiment uses the stock blocky mesher with bounded split uploads, not greedy meshing. Every comparison uses the same finite fixture slab Y [-16,32), visual radius 96 m and data radius 128 m. Edits use a bounded temporary session overlay; actor, weather and storage workloads are proxies. No durable save format or complete-world vertical qualification is introduced. The six authoritative specifications remain unchanged.

Follow [the laptop testing guide](M1_TESTING.md) for the visual check, automatic baseline, four-setting comparison and reports to return. Aggregate geometry, full frame/throughput gates, unavailable driver metrics and target memory behaviour still require evidence.

The local follow-up game changes and CI redesign remain pending new validation; this run does not validate those later changes. Preserve the earlier failed run 34003770515 and corrective run 34007283054 as history; the successful evidence above supersedes their pending status for this candidate only.
