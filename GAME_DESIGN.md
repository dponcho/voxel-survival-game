# Game design — Project Cairn

Design baseline: 2026-09-05. Status: specification; the game and its performance are not yet implemented or validated. “Project Cairn” is a working codename, not a cleared commercial title.

## 1. Product contract

Build a complete, original, first-person voxel survival sandbox for native Windows x64. The player explores, mines, builds, grows food, crafts equipment, survives changing weather and hostile wildlife, and establishes a network of inhabited refuges. Completing the progression opens a continuing sandbox rather than ending the world.

The required machine is an Intel Core i7-7600U, 2 physical cores / 4 logical threads, Intel HD Graphics 620, and 8 GB of total system RAM. The acceptance targets are 1280 × 720 at 60 fps in normal gameplay and at least 30 fps during heavy chunk streaming. These are release requirements, not performance claims. [PERFORMANCE.md](PERFORMANCE.md) defines the measurement contract.

All source work, development tools, compilation and automated tests belong in Codex Cloud and GitHub Actions. The player downloads a portable Windows ZIP, extracts it and launches the game. No local editor, SDK, compiler, terminal commands, package manager, redistributable installer or build step is required. The downloadable game includes an automatic benchmark mode; running it uses the same executable as playing.

## 2. Design pillars

1. **An editable world that remains trustworthy.** Mining and building must persist; the player must not fall through missing terrain or lose committed progress.
2. **Preparation makes exploration possible.** Food, light, clothing and shelter enable longer expeditions into unfamiliar terrain.
3. **Useful construction.** A refuge provides warmth, storage, crafting and a dependable return point. Weather gives roofs and enclosed spaces a purpose.
4. **Readable, inexpensive visuals.** Strong silhouettes, restrained textures and spatial audio carry the atmosphere. Visibility and interaction remain clear at 720p.
5. **A complete progression with room to improvise.** Recipes, equipment and discoveries form an achievable loop; building remains freely expressive.

Voxel mining, crafting and survival are genre foundations. All names, creature designs, textures, sounds, writing, interface art, recipes and progression are original or appropriately licensed. Do not reuse Minecraft assets, distinctive enemies, interface layouts, named items or progression sequences.

## 3. Version 1.0 scope

The initial product is single-player and offline. The following decisions bound the engineering problem; they are the default design, not additional user requirements.

| Area | Complete 1.0 requirement |
| --- | --- |
| World | Seeded terrain, caves, deposits, plants, landmarks and persistent block edits |
| World dimensions | 16,384 × 256 × 16,384 one-metre voxels; generated only where needed |
| Coordinates | X/Z in [-8192, 8192); Y in [-64, 192); explicit world-edge treatment |
| Regions | Meadow basin, dry escarpment, mistwood and frost upland, with gradual transitions |
| Construction | Mine/place blocks, face-based placement, rotation where meaningful, doors, storage, beds and workstations |
| Survival | Health, stamina, nourishment, exposure, fall damage, drowning and rest |
| Crafting | Discoverable recipe list, hand crafting and three workstation families |
| Progression | Fieldcraft → fired materials → forged equipment → restored refuges |
| Ecology | At least two passive species and three hostile species with distinct readable behaviours |
| Food | Foraging, hunting, cooking and three cultivable crops |
| Exploration | Three landmark families; recoverable diagrams and materials; player map markers |
| End goal | Restore three ancient survey cairns using regional supplies, then complete a final storm expedition |
| Continuing play | Construction, farming, exploration and optional repeat expeditions after the final goal |
| Modes | Standard survival and a separate free-build world mode using the same engine |
| Product shell | Title menu, world creation/selection, pause, settings, remappable controls, credits, save recovery and diagnostics |

The horizontal world is deliberately finite for 1.0. It is not preallocated and is not described as infinite. A distant impassable storm boundary signals its edge; safe movement limits prevent walking into missing space. Deep bedrock and a construction ceiling define vertical limits. Expanding coordinates or adding a floating origin is a later architecture decision.

Do not add multiplayer, mod loading, electrical logic, moving voxel vehicles, a fully simulated economy, structural collapse, unlimited creature swarms or general-purpose fluid simulation to 1.0. None is required to finish the defined survival game. Reconsider them only after the complete product passes its existing budgets.

## 4. Core loop and pacing

| Time scale | Player actions | Reward and pressure |
| --- | --- | --- |
| Seconds | Move, inspect, mine, place, attack, dodge, collect | Immediate feedback; positioning and stamina matter |
| Minutes | Choose a route, gather supplies, cook, craft, return | A useful upgrade or a better shelter; daylight and weather constrain travel |
| Sessions | Explore a region, establish a refuge, investigate a landmark | New diagrams, materials and routes |
| Long term | Connect regional knowledge and restore survey cairns | Final expedition, then an unrestricted continuing world |

The first session introduces collecting, a basic tool, food, a roof, a fire and a sleeping place. All essentials are obtainable near a validated spawn. Resource availability is deterministic; no required item depends solely on a rare random drop.

The opening refuge should be attainable in roughly 15–25 minutes. This is a tuning hypothesis, not a promised playtime. The final progression should require multiple meaningful expeditions, not repeated collection of the same resource at increasing quantities.

## 5. Movement and interaction

Default controls: WASD movement, mouse look, Space jump, Shift sprint, Ctrl crouch, left click primary action, right click use/place, E interact, Tab inventory, M map, Escape pause. Every gameplay binding is remappable; toggle options exist for sprint and crouch. Disable head bob and motion blur by default.

Starting movement values: 4.5 m/s walk, 6.5 m/s sprint, 2 m/s crouch, approximately one-block jump, and 5 m interaction reach. Collision uses a swept axis-aligned character box against voxel data. Sprint never outruns the readiness envelope used in [ARCHITECTURE.md](ARCHITECTURE.md).

Mining has tool-dependent progress and cancels predictably when its target changes. Placement displays a valid/invalid preview, respects occupancy and reach, and consumes an item only when the corresponding world edit is accepted. Prevent placement through the player or an actor. Bulk construction tools, if added to free-build mode, obey edit and mesh-complexity limits.

Inventory has eight quick slots and twenty-four backpack slots. Start with a stack limit of 64 for ordinary materials; tools and special equipment are unstackable. Moving, splitting, crafting, dropping and collecting are explicit transactions. A full inventory leaves recoverable items in the world; it must not delete them.

## 6. Survival, crafting and progression

| Stage | Unlocks | New decisions |
| --- | --- | --- |
| Fieldcraft | Hand tools, fibre bindings, simple shelter, camp cooking | Carry capacity, safe routes and food preparation |
| Fired materials | Kiln, vessels, insulated construction, preserved food | Fuel use and a dependable home base |
| Forged equipment | Forge, durable tools, clothing fittings and mining support | Longer expeditions and deeper deposits |
| Restored refuges | Survey instruments and region-specific improvements | Plan a chain of safe returns and prepare for severe weather |

Recipes are selected from a searchable list rather than arranged on a shape-matching grid. A recipe shows ingredients, workstation, outputs and why it is locked. The journal records discoveries without requiring an external wiki. Recipe validation rejects impossible prerequisites, unintended cycles that create free resources, missing inputs and unreachable progression.

Nourishment supports stamina recovery. Exposure combines regional weather, clothing and shelter; it changes slowly enough to communicate and respond. Hunger alone does not produce a sudden unexplained death. Health damage always has a visible or audible cause. No disease, thirst, nutrient-by-nutrient model or inventory spoilage is required for 1.0.

Death returns the player to a valid bed or the validated starting refuge. A marked recovery cache contains the backpack contents. Essential journal progress persists. Cache contents are saved with the inventory transaction; recovery cannot duplicate items. If the world is not ready at the destination, show a loading transition before resuming play.

## 7. World systems

Terrain uses large readable landforms, small native detail passes, sparse caves and structured deposits. Regional transitions and landmark placement are coordinate-based; visiting locations in a different order must not change their content. Landmarks may span chunks, so ownership and overlap are determined before generation, not by whichever worker finishes first.

Day/night changes sky colour and a global lighting factor. Regional weather is a scheduled state machine, not a volumetric simulation. Rain and snow effects remain near the camera. Roof/exposure checks are cached and invalidated by nearby edits; they do not scan all buildings every frame.

Water is a **bounded local system**. Natural bodies are static source regions; player edits can request local settling within an active region under the fluid-work budget. Unloaded water does not simulate. Limit propagation radius and active cells; exhausting the budget defers work rather than expanding without bound. Communicate finite flow rules through play. The engine prototype may start with static water, but the final local behaviour must be defined and tested before calling the water system complete.

Crops, furnaces and storage persist when unloaded. Growth and crafting use the saved simulation clock, with bounded catch-up calculations when loaded. Closing the game pauses world time. This avoids unbounded offline simulation and system-clock manipulation affecting progression.

## 8. Creatures and combat

Use a small set of original creatures. Suggested roles: a cautious grazing animal, a scavenging animal, a territorial pack hunter, a cave ambusher and a slow armoured defender. Working names and appearances are assigned during the content milestone.

Combat uses telegraphed attacks, spacing, stamina and a brief recovery window. Essential encounters must work with the active-creature budget: 12 fully active creatures normally, 24 at the heavy-scenario ceiling. Distant creatures persist as compact state, sleep or are deterministically respawned according to explicit rules. They do not retain a live physics body or pathfinder everywhere in the world.

Navigation is local and voxel-aware. Creatures have constrained movement abilities and can disengage when no bounded path is available. No world-scale navigation-mesh rebake follows a terrain edit. Projectiles use swept traces and bounded lifetimes; dropped items merge into stacks and have a density cap.

## 9. Visual and audio direction

Use a restrained natural palette with distinct warm refuge lighting and cool exposed terrain. Terrain mostly consists of cubes; selected plants and furnishings use economical custom models. Begin with original 16 × 16 material tiles and shared material atlases. Flat water, a simple sky, inexpensive fog and limited particles are sufficient.

The HD 620 preset uses 720p at native render scale, 96 m visual distance, 128 m data prefetch distance, no real-time shadows, no screen-space post effects and no full-screen transparency effects. See [PERFORMANCE.md](PERFORMANCE.md) for exact limits. Fog conceals the visual boundary but never substitutes for valid collision data.

Audio provides weather, footsteps, tool feedback, creature warnings and quiet environmental cues. Limit simultaneous voices and prioritize nearby critical sounds. Captions or visual cues accompany survival-critical audio. Interface text remains readable at 720p with adjustable scale and symbols that do not rely on colour alone.

## 10. Saving and the portable player experience

The distribution contains the executable, its data pack, build information, instructions and notices. Saves default to a stable per-user game directory, so extracting a new version does not overwrite worlds. An explicit portable-data mode can keep saves beside the executable when that directory is writable. Neither mode requires installation.

Offer automatic saves, Save and Quit, world backups, recovery from a previous checkpoint and a clear incompatible-version message. Never silently open an old world with a different terrain generator. An interrupted write can lose only work after the last durable transaction, not corrupt previously committed play.

The main menu includes **Run performance check** and **Open diagnostics folder**. The check creates a disposable world, drives repeatable scenarios and writes a report without external programs. It never modifies a player's world or uploads data automatically. This is the only optional hardware-feedback action beyond downloading and running the game.

## 11. Definition of a complete game

Version 1.0 requires every scoped system to function together in a persistent world, a new player to reach the final expedition without debug tools, and the same world to remain playable afterward. Temporary art is replaced, sounds and licences are accounted for, recipes and tutorials are complete, and no essential feature is a placeholder.

Completion also requires the target performance gates, save-integrity tests, clean-machine portable launch and repeatable cloud builds. A pleasant terrain demo is an engine milestone; it is not the completed survival sandbox. [ROADMAP.md](ROADMAP.md) gives the required progression from one to the other.
