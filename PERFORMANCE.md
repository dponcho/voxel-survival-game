# Performance contract

Design baseline: 2026-09-05. **No performance result has been measured for this project.** Every number below is a requirement, admission limit or initial engineering allocation. Settings become a certified profile only after the exported Windows build passes on the specified machine.

## 1. Fixed target and meaning of a pass

| Requirement | Value |
| --- | --- |
| CPU | Intel Core i7-7600U, 2 physical cores / 4 logical threads |
| GPU | Intel HD Graphics 620, shared system memory |
| RAM | 8 GB installed, including OS and graphics needs |
| Platform | Native Windows x64, Godot Compatibility |
| Rendering | 1280 × 720, 100% internal render scale |
| Normal gameplay | 60 fps; application frame deadline 16.667 ms |
| Heavy chunk streaming | At least 30 fps; application frame deadline 33.333 ms |

Normal gameplay includes movement through already prepared and normally streaming terrain, mining, building, inventory use, ordinary combat, day/night transitions and automatic saves. Heavy streaming is the defined virgin-terrain sprint and repeated-turn workload in TESTING.md. Classify phases before a run; a slow frame does not retroactively make ordinary gameplay “heavy.”

For an uncapped workload run, require average fps at or above the target **and** p99 frame time within its deadline **and no game-attributable frame beyond the deadline**. Report p50, p95, p99, p99.9, maximum and every deadline miss. An acceptable average or p99 cannot conceal a failed minimum. The normal budget is stricter than a 30-fps floor: gameplay work must fit its 60-fps deadline.

Also run a 60-Hz paced pass to check actual frame pacing and input response. Distinguish CPU work, GPU execution and presentation intervals. Timer noise, OS scheduling and display refresh can affect observations; retain raw measurements. A raw deadline miss needs investigation and a repeat, not silent trimming. If attribution cannot be established, mark the run inconclusive. A cloud benchmark is never target-hardware certification.

Explicit world-opening, teleport and migration screens are not gameplay phases. Label and time them separately. Streaming at ordinary movement speeds may not be hidden by repeatedly entering loading screens, pausing simulation or reducing speed. A protective stop at genuinely missing terrain prevents a fall but is still a streaming-throughput failure in the standard route.

No finite benchmark proves every possible operating-system event or construction will meet a deadline. Release acceptance means the defined supported envelope has passed, with its limits disclosed. The requested targets must not be softened to average-only metrics or hidden resolution reductions.

## 2. HD 620 reference profile

| Setting | Initial reference value |
| --- | --- |
| Render method | `gl_compatibility` |
| Resolution / scale | 1280 × 720 / 1.0 |
| Display pacing | 60-Hz target; uncapped/VSync-off only for workload diagnosis |
| Visual radius | 96 m, six 16-voxel data-chunk widths |
| Data prefetch radius | 128 m plus the measured required halo |
| Data / render block | 16³ / 32³; compare 16³ render blocks in M1 |
| Terrain CPU workers | One on this 4-logical-thread machine |
| Terrain triangle colliders | Disabled; voxel/AABB contact instead |
| Shadows | Disabled |
| Lighting | Simple sky/day factor, native block light, vertex AO; no light node per lamp |
| Anti-aliasing | Off initially; no rendering below 720p |
| Post effects | SSAO, glow, SSR, depth of field, motion blur and volumetric effects off |
| Texture policy | Small shared atlases; nearest-style art with measured mip/padding handling |
| Water | Flat/simple local surfaces, no reflections/refractions or full-screen effects |
| Particles / audio | Pooled and capped |

The reference radius does not shrink during certification. Optional stronger-hardware presets are separate profiles. An emergency profile may sacrifice distance or effects to remain responsive, but its results do not prove this profile passed. Never silently lower 720p, skip gameplay simulation or change fixed tick rates to manufacture a pass.

Voxel Tools provides minimum/ratio/margin thread controls and `voxel/threads/main/time_budget_ms`. Initially use a combination yielding one terrain worker on four logical CPUs, verify it through runtime stats, and set the main-thread budget to 1.0 ms. The heavy preset may admit up to 2.0 ms. Verify actual counts and work: these controls do not bound one non-preemptible operation. [Voxel Tools performance controls](https://voxel-tools.readthedocs.io/en/latest/performance/).

## 3. Frame and worker allocations

All values are initial **engineering budgets**, not measured costs. CPU and GPU stages overlap; adding their times is not a valid estimate of fps. The whole-frame gate remains authoritative.

| Main-thread category | Normal allocation | Heavy allocation |
| --- | ---: | ---: |
| Player contact, input and authoritative commands | 1.2 ms | 1.5 ms |
| Active simulation and scheduler | 0.8 ms | 1.0 ms |
| Terrain upload/apply/destruction | 1.0 ms | 2.0 ms |
| Render culling/submission | 3.0 ms | 4.0 ms |
| Engine, interface, audio bookkeeping | 1.5 ms | 2.0 ms |
| Unallocated main-thread reserve | 2.5 ms | 3.5 ms |
| **Main-thread work target** | **10.0 ms** | **14.0 ms** |
| **GPU work target** | **12.0 ms** | **22.0 ms** |
| **Application deadline** | **16.667 ms** | **33.333 ms** |

Retain reserve for driver behaviour, thermal throttling and unmodelled work. Do not allocate every fraction of the theoretical frame to features before measuring the exported build.

One terrain worker has a target average service utilization below 70% during ordinary travel. Record service time and arrival rate for generation and meshing separately. Sustained queue growth is a failure even when immediate fps remains good. No frame-thread waits on a worker, file flush, large allocation or bulk spatial write lock are allowed in gameplay.

Initial terrain-work rules:

- Check both elapsed time and admitted bytes before starting work; normal 1.0 ms, heavy 2.0 ms.
- Initial maximum individual mesh upload payload: 256 KiB. Qualify a single operation at no more than 0.75 ms on target; reduce/split it if that bound fails.
- Initial total new upload payload per frame: 512 KiB normal, 1 MiB heavy, still subordinate to the time budget.
- Limit resource destruction using the same main-thread allowance and account for work deferred inside the renderer.
- Do not assume changing a budget property splits a large stock mesh. Missing subdivision/admission hooks are native implementation work.

Pushing work to a thread does not remove its CPU, memory-bandwidth or power cost. The GPU and CPU share both system memory bandwidth and the laptop's power/thermal constraints. Benchmark their sustained combination, not isolated peak throughput.

## 4. Geometry and active-work envelope

| Counter | Normal scenario | Heavy / enforced ceiling |
| --- | ---: | ---: |
| Submitted triangles, all scene passes | 250,000 | 450,000 |
| Draw calls, including actors/interface | 250 | 400 |
| Resident data chunks | Within demand | 8,192 |
| Resident render regions | Within demand | 512 |
| Resident render objects after payload splitting | Within demand | 768 |
| Terrain material families | 3 | 3 |
| Fully active creatures | 12 | 24 |
| Fully active dropped-item stacks | 64 | 128 |
| Visible particles | 128 | 256 |
| Simultaneous audio voices | 16 | 24 |
| AI path nodes expanded per frame, shared total | 512 | 1,024 |
| Light cells processed per frame, shared total | 2,048 | 4,096 |
| Fluid cells processed per update at 10 Hz | 128 | 256 |

CPU-time budgets override cell/count budgets when a cell is more expensive than expected. Deferred work remains represented by bounded dirty-region state, so reaching a cap neither loses updates nor allocates another unbounded queue.

Use 48 m for full creature simulation and a 64 m wake/persistence transition band initially. New spawning cannot exceed the active cap. Inert stateful blocks update on demand; they are not individual frame callbacks. Limit a mining/placement command to its validated area, and coalesce edit bursts before remeshing.

Initial construction guard: at most **16,384 exposed cube faces per 32³ render region**, plus equivalent measured cost for custom models. Track the aggregate view envelope as well; a local cap alone does not ensure the total triangle/draw budget. Maintain conservative region summaries and check every maximum-radius observation window affected by an edit, not only the player's current view. Start with 200,000 terrain triangles per such window, reserving the remaining normal allowance for actors and other geometry; generated terrain must satisfy the same envelope. Admission predicts affected border regions and draw-resource counts. Refuse an edit that exceeds the supported construction envelope rather than accepting it and omitting geometry. Dense permitted construction must still pass the normal frame gate; heavy allowances cover transient streaming work. If this starting cap is too high, reduce it before certification or improve the mesher; do not silently reinterpret existing worlds.

The stock mesher is a baseline without greedy merging. Greedy meshing is an optimization to implement and test if needed, not a property assumed in these numbers. [Upstream blocky mesher](https://voxel-tools.readthedocs.io/en/latest/blocky_terrain/).

## 5. RAM and graphics-memory budgets

GB installed on a spec sheet is not equivalent to available game memory. Use MiB/GiB in reports. Count engine overhead, snapshots, driver resources and staging copies as well as raw voxel data.

| CPU-side tracked allocation | Initial cap |
| --- | ---: |
| Engine, imported assets, UI and audio | 256 MiB |
| Voxel payload and chunk metadata | 192 MiB |
| Retained CPU mesh buffers | 128 MiB |
| Entities, block metadata, simulation | 64 MiB |
| In-flight jobs and temporary buffers | 64 MiB |
| Storage caches and transaction buffers | 64 MiB |
| Native allocator/other reserve | 256 MiB |
| **Tracked CPU total** | **1,024 MiB** |

| Process/resource gate | Normal | Peak including heavy streaming |
| --- | ---: | ---: |
| Process private committed bytes | ≤1.5 GiB | ≤2.0 GiB |
| Process working set | ≤1.25 GiB | ≤1.5 GiB |
| GPU resources attributed to game | ≤256 MiB target | ≤384 MiB ceiling |
| Packaged game ZIP | ≤250 MiB target | ≤500 MiB release ceiling |

Private bytes, working set and GPU/shared-memory counters overlap differently by driver. Report them separately; do not sum working set and private bytes as independent allocations. Track resource payload estimates when exact driver attribution is unavailable and label the estimate. A low voxel payload count alone does not establish a low-RAM game.

The 8,192-chunk cap at 16 KiB dense channel payload is 128 MiB before metadata. Uniform compression should lower ordinary use; the budget must survive non-uniform edited terrain. Queue/payload caps from ARCHITECTURE.md are part of the 64 MiB in-flight allocation, not additional allowances.

A 30-minute outward journey must plateau in RAM as old chunks unload; revisiting regions must not grow duplicate cache entries. After five world open/close cycles, quiescent tracked allocations return within 10% or 32 MiB of their initial baseline, whichever is larger. Investigate process/driver retention separately. No persistent positive growth trend or paging-driven hitching passes solely because a short test stayed below 2 GiB.

## 6. Throughput, latency and persistence

| Requirement | Initial acceptance threshold |
| --- | --- |
| Nearby mine/place visual acknowledgement | p95 ≤100 ms; maximum 200 ms under the defined edit workload |
| Required movement data | Ready ahead of the player's swept path; zero emergency stops on standard benchmark routes |
| Continuous 6.5 m/s virgin-terrain sprint | No unbounded backlog; visual frontier stays behind fog boundary |
| Direction reversal | No stale mesh, collision gap or runaway queue after repeated 180° turns |
| Backlog recovery after movement stops | Return to steady state within 5 seconds in the standard route |
| Durable save batching | At least once per second normally; pause mutations at 2 seconds/8 MiB of pending work |
| Save and Quit | Target ≤5 seconds for benchmark worlds, with visible progress; no false success on timeout |
| First playable new world | Target ≤20 seconds after launch/import-free startup on the actual drive |
| Existing-world load | Target ≤10 seconds for benchmark worlds |

The save/load/latency thresholds are additional engineering goals. They do not replace the hard gameplay frame requirements. Record the user's drive type and free space when available; the supplied CPU/RAM specification does not identify disk performance. Do not certify only an empty world or a warmed disk cache.

## 7. Degradation order and failure handling

First stop admitting distant speculative work. Then cancel stale jobs, coalesce repeated edits, delay cosmetic particles and distant nonessential updates, and drain bounded queues. Keep safety data, save durability and input responsive. Never allocate indefinitely in an attempt to catch up.

If rendering or workload budgets still fail, optimize the identified cost or reduce the supported content envelope through an explicit design change. Do not change resolution, the certified visual radius, gameplay speed or simulation correctness inside a run. A protective pause or reduced-distance emergency mode is labelled as recovery, not a passing performance result.

## 8. Qualification procedure

Use release exports without an editor, debugger or diagnostic instrumentation that materially changes cost. Lightweight metrics remain enabled; measure their overhead. Run on AC power with the normal intended Windows power profile, after thermal warm-up. Record OS build, renderer/driver identity, available RAM, power state, monitor refresh and detected hardware; do not require the user to install diagnostic utilities. Memory channel configuration is unknown unless measured and should not be assumed.

The built-in check performs a 3-minute warm-up followed by the scenario suite in TESTING.md. Certification uses three complete runs, including one after a fresh process launch and one following sustained gameplay. Preserve raw results, worst runs and settings. First-use shaders, new content and a cold-start path receive separate coverage; warm-up is not permission to hide repeatable first-encounter stutters.

Changing the engine/driver path, mesher, worker count, rendering settings, world generator or content envelope invalidates the relevant baseline. Gameplay/UI changes run their affected scenarios. Work above these budgets returns to optimization before more content is layered on.
