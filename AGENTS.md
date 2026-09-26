# Repository agent instructions

## Mission and authority

Build the complete voxel survival sandbox defined in [GAME_DESIGN.md](GAME_DESIGN.md), following the user-selected Java Edition core survival/building reference in [docs/JAVA_CORE_REFERENCE.md](docs/JAVA_CORE_REFERENCE.md) with original or appropriately licensed content. Work incrementally through [ROADMAP.md](ROADMAP.md). The required deliverable is a native, portable Windows x64 game produced entirely by Codex Cloud and GitHub Actions.

These instructions describe the intended repository. In the initial six-document package, implementation files, workflows and test commands are planned, not present. Inspect the actual checkout before claiming any exist or have run. User instructions take precedence over these project defaults; do not reinterpret a hard requirement merely to pass a test.

## Non-negotiable constraints

- Target: Intel Core i7-7600U, 2C/4T, Intel HD Graphics 620, 8 GB total RAM.
- 1280 × 720 at 60 fps normal gameplay; at least 30 fps under the defined heavy streaming workload. Apply the full frame/throughput contract in [PERFORMANCE.md](PERFORMANCE.md), not average fps alone.
- Godot 4.x Compatibility with a qualified native voxel backend. The initial choice is the Zylann Voxel Tools module and a small project C++ module.
- No local development installation or compilation. The user only downloads, extracts and runs portable builds; automatic diagnostics are part of the game.
- Every runtime dependency must be contained in the ZIP or already part of the supported Windows runtime. No first-launch installer, runtime download or account requirement.
- Deterministic generated world data, bounded resident memory and queues, and durable world/inventory consistency are foundational requirements.
- All game content is original or appropriately licensed. Preserve notices and asset provenance.

## Before implementing a task

1. Read this file, the active milestone and the relevant sections of ARCHITECTURE.md, PERFORMANCE.md and TESTING.md.
2. Inspect repository status, existing changes, dependency lock and available commands. Preserve unrelated work. Search with `rg`/`rg --files` first.
3. State a bounded observable result and its acceptance checks. Choose the smallest complete increment that advances the milestone.
4. Verify unfamiliar Godot/Voxel Tools APIs against the pinned source or its matching documentation. A proposed project interface is not an upstream API.
5. Identify save/generator compatibility and performance implications before changing them. Resolve routine reversible choices autonomously; ask only when a consequential ambiguity remains after useful work.

Do not create a new repository, publish source, change repository visibility or invent a remote/artifact URL to compensate for missing access. Finish the authorized local/cloud-preparable work, then state the exact access needed for the remaining action. Do not ask the user to install tools as a workaround.

## Architecture rules

- Use native C++ for voxel generation, intensive meshing/light/fluid/pathfinding loops, persistence codecs and scheduler controls. Typed GDScript owns orchestration/UI and bounded gameplay glue.
- Never use one scene node, physics body, material instance or script callback per voxel. No full-world scan or synchronous regeneration on the frame thread.
- Preserve 16³ data chunks and the measured render-block choice; do not assume the two sizes are identical.
- Use voxel-data/AABB collision initially; keep classic terrain triangle-collider generation off. Missing data is a distinct state and blocks unsafe movement.
- Bound every job/result queue, temporary payload and retained cache. Account for upstream internal queues and deferred renderer work, not only the outer wrapper.
- Begin with one terrain worker on the target CPU. Additional parallel CPU work needs target evidence; do not create a thread pool per subsystem.
- Main-thread budgets must bound individual operations and total work. A timer cannot preempt an oversized upload or disk flush.
- Keep scene-tree and renderer mutations on their allowed engine threads. Cross-thread messages carry session epoch, coordinate and revision; stale completions are rejected.
- Stock `VoxelMesherBlocky` does not provide greedy meshing or the complete proposed block-light system. Implement and test required native extensions explicitly.
- No compute-shader, Forward+, Vulkan or discrete-GPU assumption may enter the target gameplay path.

## Determinism and saves

- Use versioned seed/coordinate-based generation with explicit integer arithmetic and RNG semantics. Test negative coordinates and Windows/Linux output equality.
- Preserve stable content IDs. Never update a golden hash simply to conceal an accidental world change.
- An accepted edit, inventory change and related progression/state mutation belong to one transaction. Render meshes are disposable derived data.
- No direct player-state JSON write alongside independently committed terrain saves as a substitute for atomic consistency.
- Never discard unjournalled dirty data, overwrite a newer revision with a worker result, or migrate a save without a recoverable original.
- Bound catch-up simulation and protect against clock-dependent offline changes. A slowed simulation must not manufacture a passing fps result.

## Build and dependency discipline

Implement M0 before substantial gameplay. Resolve exact source/toolchain pins and hashes; do not fill lockfiles with placeholders or moving `latest` branches. Build a matching custom editor, Windows debug template and Windows release template containing the same voxel and project modules.

All setup/build/export/package scripts run in cloud environments and are idempotent. Cache misses must build automatically. Cache keys include native module source, dependency revisions, patches, compiler identity and flags. A stale template is a build defect even if export succeeds.

Keep `project.godot` and `export_presets.cfg` in source control. Import/export with the matching editor, audit the final executable/DLL dependencies, and test a fresh extraction. A PCK export alone is not a Windows distribution. Keep symbols separate from the portable player ZIP.

Use least-privilege CI permissions, pin third-party actions and verify downloaded dependencies. Never expose secrets to untrusted PR code or include credentials/user data in packages. Ordinary candidate artifact creation is part of the development task; releases follow the repository's authorized tag/release process.

## Verification and completion

Follow the change-specific checks in TESTING.md. Write tests for meaningful risk: generation seams, stale jobs, save integrity, collision and package correctness. Do not add implementation-mirroring tests or rerun expensive game suites solely for prose changes.

Use release exports for performance. Record exact settings and build identity. Headless/software-rendered/cloud-runner results do not prove HD 620 performance. Keep target results unverified until the actual downloaded executable's report exists. No invented fps, RAM figures, test passes or CI runs.

If a gate fails, isolate and fix the cause before expanding that system. Preserve a useful failing seed or fixture. Do not silently lower resolution, view radius, entity workload, tick rate or acceptance thresholds. An intentional supported-envelope change belongs in the design and requires new evidence.

A task is complete when its intended behaviour works, relevant checks have run or are explicitly blocked, compatibility is preserved, and its Windows candidate is produced when runtime code changed. Update the milestone record and relevant documentation. Report the observable change, artifact, validation and material remaining uncertainty concisely.

## Keep the project focused

Complete the specified single-player core survival/building 1.0 before adding automation circuits, enchanting, brewing, extra dimensions, boss progression, multiplayer, mod loaders, moving voxel machines, unbounded water or advanced rendering. Avoid broad rewrites without a measured reason. Prefer a small tested native change over a growing abstraction layer with no demonstrated use.

Do not delegate to additional agents by default. Use delegation only when the user's request or applicable higher-priority instructions authorize it. Continue useful authorized work until the bounded task is concrete and reviewable.
