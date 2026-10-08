# Architecture

Design baseline: 2026-09-05; gameplay-state requirements clarified 2026-09-26. Status: implementation specification; qualification is tracked in milestone evidence. [GAME_DESIGN.md](GAME_DESIGN.md) owns product scope; [PERFORMANCE.md](PERFORMANCE.md) owns budgets; [TESTING.md](TESTING.md) owns evidence requirements.

## 1. Engine decision

Use **Godot 4.x, Compatibility renderer, Zylann Voxel Tools as a compiled engine module**, plus a small project-owned C++ module for world rules and integration. Use typed GDScript for menus, presentation and orchestration. Do not use C# or ship a managed runtime.

The candidate baseline is the published **Godot 4.7.2 + Voxel Tools 1.7** pairing, observed on 2026-09-05. This is a candidate to compile and qualify in M0, not a claim that this project has tested it. Resolve the corresponding exact Godot source revision and Voxel Tools `v1.7` revision to full commit SHAs before the first engine build; retain those values in `build/dependencies.lock.json`. Never synthesize a full SHA from the short hash shown in a release title. [Upstream release](https://github.com/Zylann/godot_voxel/releases/tag/v1.7).

The module edition has a longer development history; upstream describes the extension edition as less tested. A module export requires custom export templates containing the same modules as the editor. A stock template cannot provide the native voxel classes. This is why the cloud pipeline builds the editor and both Windows templates together. [Voxel Tools editions and exports](https://voxel-tools.readthedocs.io/en/latest/getting_the_module/).

Compatibility uses the OpenGL rendering path. No gameplay feature may depend on RenderingDevice, compute shaders or Forward+. The initial Windows driver path is native OpenGL; ANGLE is a separately qualified Compatibility fallback only if the actual laptop requires it. [Godot renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html).

| Alternative | Decision and reconsideration trigger |
| --- | --- |
| Voxel Tools GDExtension | Reconsider if it passes the same correctness/HD 620 tests and materially reduces build maintenance; convenience alone does not justify switching |
| Project-owned native mesher inside the module | Add if profiling proves stock meshing or upload granularity prevents the required budgets |
| Entirely custom C++ voxel engine under Godot | Last resort after a bounded comparison demonstrates that the module cannot meet a critical gate; preserve world and gameplay interfaces |
| Scripted voxel engine or one node per block | Rejected: inappropriate data representation and hot-loop overhead for this target |
| Smooth SDF / Transvoxel terrain | Outside the block-based product; no benefit sufficient to justify its different geometry and collision costs |

An engine replacement requires a written benchmark comparison, save-format compatibility plan and successful Windows ZIP export. Do not maintain two production backends speculatively.

## 2. Repository and ownership

Place the six design documents at the repository root. The proposed implementation layout is:

| Path | Responsibility |
| --- | --- |
| `game/project.godot`, `game/export_presets.cfg` | Project configuration and checked-in export presets |
| `game/scenes/`, `game/ui/`, `game/scripts/` | Scene composition, interface and high-level orchestration |
| `game/content/`, `game/assets/` | Validated content definitions and original/licensed assets |
| `native/sandbox_world/core/` | Engine-independent generation, commands, persistence model and bounded algorithms |
| `native/sandbox_world/godot/` | Godot registration, Voxel Tools adapters and render integration |
| `native/sandbox_world/config.py`, `SCsub` | Custom Godot module build integration |
| `tests/native/`, `tests/integration/`, `tests/fixtures/` | Executable correctness tests and reference data |
| `benchmarks/scenarios/`, `benchmarks/baselines/` | Versioned workloads and evidence references |
| `build/dependencies.lock.json`, `build/config/` | Exact source/toolchain pins and target build options |
| `build/patches/voxel/` | Minimal, reviewable downstream patches when required |
| `tools/ci/` | Idempotent setup, build, test, export, package and verification commands |
| `.github/workflows/` | Cloud CI, cached engine builds, candidate artifacts and releases |

Generated engine sources, `.godot` import caches, object files, templates and packages are build outputs. They are not hand-maintained game source. All native gameplay changes are included in the engine cache key; a gameplay module change must not accidentally reuse an old executable.

Stage upstream Voxel Tools at `engine-src/modules/voxel`, and the project module at `engine-src/modules/sandbox_world`. Declare the module dependency explicitly and test both editor and template registrations. Upstream requires the `voxel` directory name for its module build. [Module build instructions](https://voxel-tools.readthedocs.io/en/latest/development/).

## 3. Runtime boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| `WorldSession` | World identity, seed/version, lifecycle, authoritative simulation tick | Per-voxel script loops |
| `WorldBackend` | Bounded terrain access, edit admission, snapshots and readiness | Inventory UI or recipe presentation |
| `TerrainAdapter` | Voxel Tools terrain/viewers, mesher integration and native callbacks | A second competing world database |
| `WorldGenerator` | Pure coordinate-based voxel generation | Scene tree, clocks or shared mutable RNG |
| `WorldCommands` | Ordered, validated game-state changes and transaction payloads | Rendering as the source of truth |
| `WorldStore` | Durable transactions, chunk snapshots, migrations and recovery | Main-thread disk waits |
| `SimulationScheduler` | Active entities, fluids, growth and bounded job admission | Unbounded world scans |
| `Diagnostics` | Frame timings, memory, queues, scenario reports and build identity | Automatic uploads of player data |

Proposed application interfaces include `request_region`, `query_readiness`, `try_read_voxel`, `submit_edit`, `poll_completions`, `request_save_barrier` and `get_stats`. These names are project interfaces to implement, not claimed upstream methods. A read reports **ready / missing / out of bounds / error** separately; missing is never interpreted as air.

Use one authoritative voxel store in memory through the terrain backend. Workers may hold bounded immutable snapshots. Do not mirror the whole active world in GDScript dictionaries, nodes or another permanent native array.

## 4. Spatial representation

One voxel is one metre. World coordinates use signed integers; persistence keys include the world identity and integer chunk coordinates. Use mathematical floor division for negative coordinates: voxel -1 maps to chunk -1, local coordinate 15 for a 16-voxel chunk. Casting toward zero is incorrect.

The 1.0 world is X/Z [-8192, 8192), Y [-64, 192). Physics/render transforms use the standard single-precision engine build within those bounds. Do not enable double-precision builds or claim unlimited coordinates. Generation uses sufficiently wide integer intermediates so coordinate hashing cannot overflow signed arithmetic.

| Representation | Baseline |
| --- | --- |
| Data chunk | 16 × 16 × 16 voxels |
| Render chunk | 32 × 32 × 32 voxels, comprising 2 × 2 × 2 data chunks |
| Block type | Unsigned 16-bit ID; zero reserved for air; IDs never silently recycled |
| State | One byte for bounded orientation/variant state where needed |
| Light | One byte: 4-bit skylight and 4-bit local emissive intensity |
| Stateful block metadata | Sparse, versioned records for containers, workstations and plants |
| Mesh neighbourhood | One-voxel halo for face visibility/AO; lighting may request a separately bounded region |

Voxel Tools documents 16³ storage chunks and a choice of 16 or 32 for render block size. Larger render blocks trade fewer draw calls for more expensive edits. Arbitrary render block sizes are not assumed. [VoxelTerrain API](https://voxel-tools.readthedocs.io/en/latest/api/VoxelTerrain/).

Empty and uniform channels remain compressed. Unused channels allocate no dense payload. A fully materialized 16³ chunk at four bytes per voxel has 16 KiB of channel payload; metadata, neighbourhood copies, meshes and allocator overhead are separate budgets.

Start with 96 m visual radius and 128 m data prefetch radius, with integer chunk alignment and a halo. Use one visual viewer and a data-only viewer. Measure the actual union of their requests, including vertical extent and padding. A simple cube bound of 19³ data chunks is 6,859 chunks, or about 107.2 MiB of four-byte payload, before overhead; the resident cap is 8,192 chunks. Do not allocate full-height columns on each horizontal request.

Do not assume `view_distance_vertical_ratio` trims `VoxelTerrain`: its documented support is restricted to a `VoxelLodTerrain` mode. Any anisotropic loading policy for this backend needs explicit native support. [VoxelViewer API](https://voxel-tools.readthedocs.io/en/latest/api/VoxelViewer/).

## 5. Deterministic generation

Define generated voxel content as `G(seed, generator_version, content_hash, integer_position)`. The same inputs produce identical block/state data on Windows and Linux, independent of traversal order, thread count, cancellation or cache history. Visual particles and full physics replay are not promised to be cross-platform deterministic.

Implement a fixed, versioned integer hash/PRNG with explicit unsigned wraparound. Use integer or fixed-point lattice noise for terrain decisions, specified rounding and serialized parameters. Do not let compiler-specific floating-point thresholds decide block IDs. Native generator graphs/noise libraries can be benchmarked, but they do not satisfy cross-platform determinism until golden output tests establish it.

Generation passes:

1. Derive coarse regional climate, landform height and surface classification from coordinates.
2. Fill uniform air/solid runs before evaluating detail.
3. Evaluate cave/detail noise only within relevant altitude ranges.
4. Place resources using feature-specific seeds, independent of incidental RNG call order.
5. Enumerate feature anchors in neighbouring macro cells that can intersect this chunk. Clip their contributions locally; resolve overlaps using stable feature priority and ID.
6. Apply saved edits and state after base generation. A restored edit is never overwritten by a late generator result.

Spawn selection is a bounded deterministic search with a safe fallback. Validate essential resources, standing clearance and access to a refuge-sized area. Generation must not recursively load neighbouring chunks or read live scene state.

Saved worlds pin generator version, content mapping and parameters. Existing worlds retain their generator or undergo an explicit migration with a backup. Updating the engine version alone does not authorize changing world output.

## 6. Streaming, scheduling and edits

The primary lifecycle is: absent → requested → loading/generating → data ready → mesh pending → render ready → eviction candidate. Dirty data is a separate persistence condition. Every request/result carries world-session epoch, coordinate, revision and cancellation token. Reopening a world or reusing a coordinate cannot accept an old result from another session.

Priority order is: safe player movement and nearby edits; visible missing terrain; imminent direction of travel; nearby active simulation; remaining prefetch; distant maintenance. Persistence has reserved admission so sustained streaming cannot indefinitely postpone a save.

Use the Voxel Tools pool for terrain CPU work, with **one terrain worker on the 2C/4T target initially**. Add one disk worker that mostly waits for I/O. Schedule compression and other CPU-heavy work under the same total concurrency budget. Account for Godot's own worker/render/audio threads; four logical CPUs are not four spare cores. A second terrain worker is an experiment requiring sustained target measurements.

Voxel Tools exposes thread-count controls and a main-thread task time budget. These controls help admission but do not interrupt an expensive mesh upload already in progress. [Thread and main-thread budget documentation](https://voxel-tools.readthedocs.io/en/latest/performance/).

| Queue | Initial maximum | Saturation response |
| --- | --- | --- |
| Admitted terrain CPU work | 64 jobs, including active jobs | Drop stale prefetch requests; retain a compact desired-region description |
| Completed CPU mesh payloads | 16 payloads and 32 MiB, whichever binds first | Stop new distant meshing until uploads drain |
| Undurable game transactions | 8 MiB or 2 seconds of oldest pending work | Pause new mutations; maintain rendering and show saving status |
| Lighting work | 65,536 queued cells | Coalesce dirty regions and defer; never lose required invalidations |
| Fluid work | 4,096 active cells | Keep a bounded dirty-region marker; defer remote propagation |

These are project requirements. They are not all stock Voxel Tools settings. M1 must instrument the pinned implementation, identify which internal queues bypass admission, and add minimal native hooks where needed. An unbounded internal queue behind a capped public queue fails this design.

Keep safety data resident around the player, independent of whether a GPU mesh exists. Movement checks a swept readiness volume. If necessary data is missing, halt movement at the last safe boundary and prioritize recovery. Ordinary 6.5 m/s traversal must not routinely hit that boundary; the streaming benchmark checks throughput as well as fps. Teleports and world loads use an explicit loading state until their safety region is ready.

The M1 16³ heavy-route first-boundary experiment adds four fixed preparation
viewers inside the existing data halo; base required geometry and safety stay
unchanged. At most 511 resident regions fit the existing 512 cap. A one-process
pose latch preserves native mesh references during base-viewer handover; all
preparation/submission/retirement work remains accounted. This narrow fixture
policy is not a general-world streaming solution or target qualification. See
[the bounded replay](docs/M1_FRONTIER_BOUNDARY_REPLAY.md).

A second visual-only viewer of an already submitted region retains its current
desired revision, including while an accepted edit replacement is in flight.
First loads, `post_edit` invalidation and collision-viewer combinations retain
their existing scheduling. A cloud-only bounded observer copies resource IDs,
viewer counts and desired/last-submitted revisions without retaining resources
or reading GPU buffers; ordinary callbacks do not invoke it. See
[the concurrent-edit replay](docs/M1_FRONTIER_EDIT_HANDOVER.md).

Edits are validated commands: reach, inventory, collision, bounds, readiness and complexity admission. A successful command assigns a revision, changes voxel/inventory state consistently, marks affected border meshes and lighting, and queues its persistence payload. Coalesce repeated edits to the same chunk. Main-thread reads/edits must not wait behind a long worker-held spatial lock; use short snapshots, retry/try-lock paths or narrowly scoped native adaptation where required.

Never discard unsaved state during eviction. Once its complete transaction is durably journalled, in-memory chunk data may be evicted even if snapshot compaction is pending. Reload reconstructs the snapshot plus all later committed records. Bound mesh destruction as well as creation; releasing hundreds of buffers at once is not free.

## 7. Meshing, rendering and lighting

Start with `VoxelTerrain`, `VoxelMesherBlocky`, shared `VoxelBlockyLibrary` resources, hidden-face removal and frustum culling. **The stock blocky mesher does not do greedy meshing.** Its vertex ambient occlusion is useful, but it is not the game's full sunlight/emissive-light system. [Blocky meshing](https://voxel-tools.readthedocs.io/en/latest/blocky_terrain/).

Keep at most three terrain material families: opaque/emissive, cutout and water. The core block set includes stairs/slabs and bounded water/lava/falling-block behaviour; collision shapes, orientation and fluid/light state must remain data-driven with no node per voxel. Empty surfaces create no draw calls. Prefer opaque geometry for leaves and small plants where it remains attractive; keep cutout coverage bounded. Use a minimal atlas shader, no normal maps or real-time shadows on the target preset, and linear/distance fog. Use ordinary frustum/backface/hidden-face culling first; dynamic occluder baking is not part of the initial implementation.

The project owns a native light field and the shader/mesh attribute path that consumes it. Implement this explicitly in M2/M5; do not assume the upstream mesher automatically reads a custom light channel. Seed skylight from bounded column summaries, propagate at most 15 intensity levels, and propagate removals as well as additions. Persist/reconstruct boundary conditions so load order cannot leave lighting seams. Changing time of day changes a shader multiplier, not every chunk mesh.

If geometry cost fails M1, introduce a native greedy cube-face path. Merge only faces with identical material, orientation, transparency class, tiling semantics and compatible light/AO values. Keep non-cube models on their bounded model path. A large atlas quad needs tile-local repeating coordinates with correct filtering; stretching a single tile across the quad is a visual bug. Test seams and lighting before accepting the optimization.

An upload budget is both time- and byte-limited. A per-frame deadline cannot preempt a driver call. Measure worst-case individual uploads; split oversized work into bounded spatial payloads or revise the mesher before they enter the render thread. If the selected stock backend cannot enforce that policy, the native integration is incomplete. Keep the previous mesh until replacement is ready; revision checks prevent stale replacement. Also measure deferred driver work at frame end.

Arbitrary checkerboard constructions can overwhelm any practical geometry budget. Define and enforce a local exposed-face limit before admitting edits, using the same rules in both game modes. Initial limits are in PERFORMANCE.md. Reject a complexity-increasing edit with a clear message if necessary; never silently delete existing geometry. The supported envelope is tested, and out-of-envelope stress must fail gracefully.

## 8. Collision and simulation

Disable classic terrain collision generation. Use `VoxelBoxMover` or a measured project-native swept AABB implementation for terrain contact and voxel raycasts for targeting. Projectiles use swept traces. This avoids maintaining triangle-mesh terrain colliders. Custom stairs/slabs require matching collision boxes and dedicated tests; visual meshes do not define collision implicitly. [Voxel collision API and behaviour](https://voxel-tools.readthedocs.io/en/latest/blocky_terrain/).

Use a 60 Hz fixed player/movement tick with presentation interpolation. AI decisions run at 5 Hz, active creature movement at a bounded rate compatible with 60 Hz collision stepping, and fluids/growth on scheduled work. Do not catch up unlimited missed ticks in one frame. A bounded catch-up cap reports overload; it cannot hide a performance failure by slowing the simulation clock.

Entities use compact records and a spatial hash. Instantiate presentation nodes only for active nearby actors. Maximum counts, sensing radii and path-search expansions are explicit. Terrain edits invalidate nearby path regions, not a global navigation mesh. Growth/workstation catch-up is a bounded arithmetic update, not one iteration per missed tick.

## 9. Persistence and recovery

Use a project-owned native `WorldStore` backed by SQLite, with one writer and bounded readers. The upstream `VoxelStreamSQLite` is a useful reference for block storage, but its public API does not promise an atomic transaction spanning terrain, inventory and player state. The shipped game needs an explicit `VoxelStream` adapter/transaction coordinator; a separate player JSON file beside an independently saved terrain database is insufficient. [VoxelStreamSQLite API](https://voxel-tools.readthedocs.io/en/latest/api/VoxelStreamSQLite/).

Compile a pinned SQLite implementation once, with deliberate ownership of its linkage. Avoid conflicting duplicate amalgamations between native modules. Use WAL mode with `synchronous=FULL`; perform checkpoints on the disk worker. Verify the actual filesystem/runtime behaviour in crash tests rather than assuming a save call is durable. [SQLite transactions](https://www.sqlite.org/transactional.html), [WAL](https://www.sqlite.org/wal.html).

Logical schema:

| Record | Contents |
| --- | --- |
| `world_meta` | UUID, format version, generator/content identities, bounds, clock and creation metadata |
| `transactions` | Monotonic sequence, simulation tick, complete mutation payload, version and checksum |
| `chunk_snapshots` | Chunk coordinate, incorporated transaction sequence, compressed block/state payload and checksum |
| `state_snapshots` | Player, inventory, entities, containers and progression at an identified sequence |

Journal authoritative after-values and explicit IDs, including all sides of inventory/world changes. Replaying must not call a recipe RNG or generation function to rediscover an outcome. Commit coupled state changes atomically. A block removed and its item awarded are one logical transaction. Snapshots are acceleration data; transactions after their incorporated sequence remain recoverable. Prune journal prefixes only after every affected snapshot and the pruning watermark are committed consistently.

The Java-style core contract uses nine hotbar plus twenty-seven backpack slots, armour/offhand slots, 2×2/3×3 crafting grids and input/fuel/output furnace state. Grid consumption/output, tool durability, death inventory clearing plus item-drop creation, pickup and drop expiry all use the transaction model above. Unloaded crops/furnaces pause; loaded-time item expiry never advances from the system clock. Drop-cap saturation retains bounded authoritative pending contents instead of deleting inventory. The core reference is a behaviour contract, not Minecraft save or protocol compatibility.

Target a durable batch at least once per second in active play. Distinguish visible changes from durable changes in diagnostics. The 2-second/8-MiB pending ceiling pauses new mutations if the writer stalls. Save and Quit waits asynchronously for a barrier covering all accepted commands and the final player state, then closes cleanly. On failure, keep the session recoverable and show the problem rather than claiming success.

Backups use a consistent database snapshot, not a casual copy of the main file while WAL is active. Keep three rotating checkpoints; expose restore in the game. World-format migrations create a backup, validate the result and preserve the original if interrupted. Unsupported future formats open read-only for metadata or are refused; they are never rewritten automatically.

Default saves use a stable `user://` game-data directory independent of build version. Portable-data mode resolves a writable `data/` beside the executable through the application path service; this is game functionality, not Godot editor self-contained mode. Use a per-world lock to prevent two processes writing the same world. Treat disk-full, permissions, corrupt payloads and unavailable paths as tested states.

## 10. Automated cloud build and ZIP delivery

Everything in this section runs in Codex Cloud or GitHub Actions. The six-document package does not contain an implemented workflow; M0 implements and executes this contract.

`build/dependencies.lock.json` must pin full Godot/Voxel commits, project module source hash, patch hashes, compiler/toolchain version, Windows SDK, Python/SCons versions, dependency archive digests, SQLite revision and build flags. GitHub Actions references use full action SHAs. Resolve pins from verified upstream sources; do not use `latest` or a moving branch as a production dependency. Hosted runner images can change, so record the resolved image/tool versions and fail or deliberately refresh the lock when required tools no longer match.

Use a concrete Windows hosted image initially, such as `windows-2022`, with a selected MSVC toolset. Probe availability at M0 and pin the actual toolchain identity. All setup is automated on that runner. Build three x64 targets from exactly the same source bundle: editor, `template_debug`, `template_release`. A Linux editor with the same modules supports Codex Cloud integration work; it is built/cached by a separate Linux job when needed.

Initial build choices: Compatibility/OpenGL enabled, Vulkan and D3D12 disabled, non-.NET, standard precision, release optimization, no architecture-native instruction requirement. Keep LTO off for the bootstrap because full-engine linking can exceed modest runner memory; enable a measured compatible form only after cold builds pass. Prefer a static runtime; otherwise package every legally redistributable non-system DLL and audit transitive imports. No local VC runtime installation is allowed. Qualify the actual laptop's Windows build and installed graphics driver; the hardware specification alone does not establish those versions. [Windows compilation and templates](https://docs.godotengine.org/en/stable/engine_details/development/compiling/compiling_for_windows.html).

The proposed command shape below is **a cloud implementation template, not an executed build**. M0 checks options against the pinned source and supplies dependency flags required by that revision. It rejects unknown options rather than assuming a successful-looking command configured the build correctly.

```powershell
# Run from the staged engine source directory on the cloud Windows runner.
scons platform=windows arch=x86_64 target=editor vulkan=no d3d12=no opengl3=yes lto=none -j2
scons platform=windows arch=x86_64 target=template_debug vulkan=no d3d12=no opengl3=yes lto=none -j2
scons platform=windows arch=x86_64 target=template_release vulkan=no d3d12=no opengl3=yes lto=none -j2
```

The wrapper checks every exit code, inventories output filenames, checks native class registration and stages the results under stable paths. Do not guess that custom binaries have the official template names. Cache only verified bundles under a key that includes **all** source, toolchain, target and configuration inputs. A cache miss automatically builds; it never requires someone to prepare a workstation. Do not restore executables using broad partial cache keys.

Check in the `Windows Portable` export preset with x86_64 architecture, non-embedded PCK and explicit custom debug/release template paths. Set `renderer/rendering_method="gl_compatibility"` under the project's rendering settings. After import, export with the custom editor; the release template alone cannot perform editor imports. [Godot command-line export](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html).

```powershell
# tools/ci/export_windows.ps1 resolves these absolute paths in the runner.
& $EditorPath --headless --path $GamePath --import
if ($LASTEXITCODE -ne 0) { throw 'Import failed' }
& $EditorPath --headless --path $GamePath --export-release 'Windows Portable' $OutputExe
if ($LASTEXITCODE -ne 0) { throw 'Export failed' }
```

The export wrapper creates the output directory first, validates expected files, copies notices/build metadata, audits dependencies, and packages a **Windows distribution ZIP**. `--export-pack` by itself is not a portable Windows game.

| Workflow | Triggers | Required result |
| --- | --- | --- |
| `ci.yml` | Pull request, push | Static/content checks, native tests, matching-editor import and headless integration |
| `engine.yml` | Reusable call on cache miss or native/dependency change | Verified matching editor and export templates; Linux cloud editor as applicable |
| `windows-build.yml` | Every code-bearing PR/push and manual dispatch | Release export, clean extraction, headless Windows self-test, complete ZIP + diagnostics |
| `release.yml` | Authorized version tag | Rerun required gates, attach exact verified ZIP/checksum/build manifest to a GitHub release |
| `cold-build.yml` | Weekly and dependency changes | Clean-cache source-to-ZIP proof with recorded duration and runner image |

Give ordinary jobs read-only repository permissions. Upload candidate artifacts without publishing source or changing repository visibility. The release job alone receives the scoped permission needed for its intended release. PR code never receives release secrets. Pin/check downloads and keep credentials out of packages.

The ZIP root contains `Cairn.exe`, `Cairn.pck`, `BUILD_INFO.json`, `README.txt`, `LICENSES/`, plus any audited runtime files. Symbols belong in a separate diagnostic artifact. The published checksum is calculated after packaging; release attachment uses those same bytes. No installer, editor, Python, Godot download or online bootstrap is included in the player's launch path.

GitHub-hosted machines can validate builds and logic, but their hardware is not this laptop. Their results cannot certify HD 620 frame pacing. [GitHub-hosted runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). The actual executable's automatic performance check supplies that evidence; without it, label target performance **unverified**.

## 11. Principal risks and decision gates

| Risk | Resolution required before expansion |
| --- | --- |
| OpenGL upload/deletion stalls | M1 individual-operation and whole-frame traces; bounded native work if upstream controls are insufficient |
| CPU oversubscription/thermal throttling | M1 one/two-worker comparison and sustained target benchmark |
| Geometry explosion | M1 exposed-face stress, then mesh splitting/greedy path and admission limits |
| Module build drift or missing runtime dependency | M0 clean-cache build, matching classes and DLL audit |
| Inconsistent saves between systems | M3 crash-injected atomic transaction/replay proof |
| False determinism | M2 Windows/Linux golden hashes under reordered and cancelled requests |
| Missing light/queue hooks in upstream API | Explicit native implementation work; never treat an architectural requirement as an existing feature |

Changing an engine pin, save format, generation rule or certified profile invalidates the relevant evidence. Record the decision and rerun its gate before claiming it is resolved.
