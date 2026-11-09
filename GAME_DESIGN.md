# Game design — Project Cairn

Design baseline: 2026-09-05; product direction revised 2026-09-26 at the user's request. This is a requirements document; implementation and qualification status live in the milestone evidence records. “Project Cairn” is a working codename, not a cleared commercial title.

## 1. Product contract

Build a complete first-person voxel survival sandbox for native Windows x64, closely following **Minecraft Java Edition's core survival and building mechanics, behaviour and visual language**, using project-owned code and original or appropriately licensed content. The player gathers wood, crafts tools, mines stone and ores, builds shelter, survives nights, farms, cooks and explores a persistent block world. Building and exploration remain open-ended.

The user selected core survival/building for 1.0; automation circuits, enchanting, brewing, additional dimensions and boss progression are deferred until after 1.0. [The Java core reference contract](docs/JAVA_CORE_REFERENCE.md) defines required behaviour, verification and explicit differences. Similarity is a product goal; it does not override the hardware, persistence or portable-build requirements below.

The required machine is an Intel Core i7-7600U, 2 physical cores / 4 logical threads, Intel HD Graphics 620, and 8 GB of total system RAM. The acceptance targets are 1280 × 720 at 60 fps in normal gameplay and at least 30 fps during heavy chunk streaming. These are release requirements, not performance claims. [PERFORMANCE.md](PERFORMANCE.md) defines the measurement contract.

All source work, development tools, compilation and automated tests belong in Codex Cloud and GitHub Actions. The player downloads a portable Windows ZIP, extracts it and launches the game. No local editor, SDK, compiler, terminal commands, package manager, redistributable installer or build step is required. The downloadable game includes an automatic benchmark mode; running it uses the same executable as playing.

## 2. Design pillars

1. **An editable world that remains trustworthy.** Mining and building must persist; the player must not fall through missing terrain or lose committed progress.
2. **Familiar survival choices.** Food, light, tools, armour and shelter enable mining and exploration. Hunger supports the familiar sprint/regeneration loop; there is no separate stamina or exposure meter.
3. **Expressive block construction.** Predictable placement, mining, stairs, slabs, doors, storage and beds make building useful. Shelter protects from hostile creatures and supports a home base.
4. **Familiar block visuals at low cost.** Cubic landforms, crisp low-resolution textures, blocky creatures, simple lighting and a readable hotbar/HUD evoke Java Edition while remaining clear at 720p.
5. **Open-ended progression.** A wood/stone/metal tool-and-equipment ladder supports deeper mining and more building options. No mandatory cairn quest or storm expedition gates the sandbox.

Implement familiar mechanics and functional interface conventions deliberately: a nine-slot hotbar, grid crafting, conventional material names and a tool-tier progression are appropriate to the requested direction. Create Cairn's own textures, models, sounds, writing, interface artwork and branding; do not import Minecraft game assets or code. Preserve licences and provenance. The earlier requirement to invent different recipes, inventory layouts and progression solely for differentiation is superseded.

## 3. Version 1.0 scope

The initial product is single-player and offline. The following decisions bound the engineering problem; they are the default design, not additional user requirements.

| Area | Complete 1.0 requirement |
| --- | --- |
| World | Seeded terrain, caves, deposits, plants, landmarks and persistent block edits |
| World dimensions | 16,384 × 256 × 16,384 one-metre voxels; generated only where needed |
| Coordinates | X/Z in [-8192, 8192); Y in [-64, 192); explicit world-edge treatment |
| Regions | Meadow basin, dry escarpment, mistwood and frost upland, with gradual transitions |
| Construction | Mine/place blocks, face-based placement, orientation, stairs/slabs, fences, doors, storage, beds, crafting tables and furnaces |
| Survival | Health, hunger/saturation, armour, fall/fire/drowning damage, hostile nights, beds and respawn; no independent stamina/exposure system |
| Crafting | 2×2 inventory grid, 3×3 crafting table, shaped/shapeless recipes with recipe-book assistance, fuel-based furnace smelting/cooking |
| Progression | Gather wood → wooden/stone tools → smelted metal tools and armour → advanced mining/building; no forced narrative ending |
| Ecology | At least two passive species and three hostile species with distinct readable behaviours |
| Food | Foraging, hunting, cooking, three cultivable crops, tilling/hydration and bounded passive-animal breeding |
| Exploration | Three landmark families, caves and deposits; useful materials and optional discoveries without diagram-locked basic recipes |
| Completion scope | All core survival/building systems work together; optional landmarks and self-directed projects; bosses are post-1.0 |
| Continuing play | Construction, farming, mining and exploration without a mandatory finale |
| Modes | Standard survival and a separate Creative-style free-build world mode with flight, instant breaking and a block catalogue |
| Product shell | Title menu, world creation/selection, pause, settings, remappable controls, credits, save recovery and diagnostics |

The horizontal world is deliberately finite for 1.0. It is not preallocated and is not described as infinite. A distant impassable storm boundary signals its edge; safe movement limits prevent walking into missing space. Deep bedrock and a construction ceiling define vertical limits. Expanding coordinates or adding a floating origin is a later architecture decision.

The user explicitly defers automation circuits, enchanting, brewing, extra dimensions and boss progression until after 1.0. Multiplayer, mod loading, moving voxel vehicles, a fully simulated economy, structural collapse, unlimited creature swarms and general-purpose fluid simulation are also outside 1.0. Deliver core survival/building first; these exclusions do not permit omitting ordinary crafting, furnace cooking, farming, beds or bounded water/lava behaviour.

## 4. Core loop and pacing

| Time scale | Player actions | Reward and pressure |
| --- | --- | --- |
| Seconds | Move, inspect, mine, place, attack, collect | Immediate block/tool feedback; positioning, attack cooldown and hunger matter |
| Minutes | Gather supplies, cook, craft, mine, return | A useful tool or a better shelter; daylight and hostile nights affect choices |
| Sessions | Explore a region, establish a base, investigate a landmark | New materials, building options and routes |
| Long term | Improve equipment, develop farms and undertake larger builds | An ongoing sandbox with optional exploration goals |

The first session introduces logs/planks, a crafting table, basic tools, stone, a furnace, food, light, shelter and a bed. All essentials are obtainable near a validated spawn. Resource availability is deterministic; no required item depends solely on a rare random drop.

A basic first-night shelter should be attainable near spawn. Onboarding supports experimentation and the familiar wood-to-stone-to-metal loop without requiring a quest chain; progression gives practical new capabilities.

## 5. Movement and interaction

Default controls follow Java Edition: WASD movement, mouse look, Space jump, Ctrl sprint, Shift sneak, left click attack/mine, right click use/place/interact, E inventory, 1–9 or mouse wheel hotbar selection, Q drop, F swap hands, Escape pause. Every gameplay binding is remappable; toggle options exist for sprint and crouch. Disable head bob and motion blur by default.

Movement, acceleration, jumping, swimming, reach and sneaking should feel close to Java Edition; verify numeric reference behaviour before implementing and version the resulting settings. Sneaking must prevent ordinary walk-off at a ledge. Collision uses a swept axis-aligned character box against voxel data. The existing M1 6.5 m/s stress route stays unchanged even if the final player movement tuning differs; changes require a separate gameplay regression route and do not soften [PERFORMANCE.md](PERFORMANCE.md). Sprint never outruns the readiness envelope in [ARCHITECTURE.md](ARCHITECTURE.md).

Mining has block-hardness/tool/tier-dependent progress, durability, appropriate drops and crack feedback; it cancels predictably when the target changes. Placement uses a crosshair and targeted-block outline, respects face/orientation, occupancy and reach, and consumes an item only when the corresponding world edit is accepted. Prevent placement through the player or an actor. Bulk construction tools, if added to free-build mode, obey edit and mesh-complexity limits.

Inventory has nine hotbar slots and twenty-seven backpack slots, four armour slots and one offhand slot. Ordinary materials stack to 64; explicitly declared item families may stack to 16; tools and armour are unstackable. Moving, splitting, crafting, dropping and collecting are explicit transactions. A full inventory leaves recoverable items in the world; it must not delete them.

## 6. Survival, crafting and progression

| Stage | Unlocks | New decisions |
| --- | --- | --- |
| Wood and shelter | Planks, sticks, crafting table, basic tools and construction | Gather efficiently and establish a safe first night |
| Stone and heat | Stone tools, furnace, torches and cooked food | Select fuels, mine safely and preserve supplies |
| Metal equipment | Smelted metal tools, armour, buckets and stronger mining capability | Trade durability and protection against resource cost |
| Established sandbox | Advanced materials, expanded farms and varied construction | Choose larger builds and self-directed expeditions |

Crafting uses a 2×2 inventory grid and a 3×3 crafting-table grid, with shaped and shapeless recipes. A searchable recipe book may preview or fill available ingredients into the grid; it does not replace grid matching or bypass ingredient consumption. Basic recipes do not require story diagrams. Furnace input, fuel and output slots support timed smelting/cooking. Validate recipe matching, mirror/translation rules, stack limits, output quantities, unreachable prerequisites and unintended resource-creating cycles.

Health, hunger and saturation govern damage, sprint availability and natural regeneration in the Java-style survival loop. Food has explicit nutrition/saturation values; difficulty defines starvation and hostile pressure. Health damage has visible or audible feedback. No separate stamina, clothing/exposure, disease, thirst, nutrient-by-nutrient model or spoilage system is required for 1.0. Rain/snow provide atmosphere and ordinary block/world effects without adding a competing survival meter.

Death returns the player to a valid bed spawn or the validated world spawn. Carried inventory/equipment drops at the death location as bounded item stacks rather than a permanent recovery chest; loaded simulation time governs expiry, and unloaded drops do not age from the system clock. Clearing inventory and creating drops form one durable transaction; pickup, expiry and hazards cannot duplicate or silently overflow them. If a drop cap is saturated, retain authoritative pending contents with visible backpressure until admission is safe. Bed destruction/obstruction falls back to safe spawn. Loading at a respawn destination is explicit.

## 7. World systems

Terrain uses large readable landforms, small native detail passes, sparse caves and structured deposits. Regional transitions and landmark placement are coordinate-based; visiting locations in a different order must not change their content. Landmarks may span chunks, so ownership and overlap are determined before generation, not by whichever worker finishes first.

Day/night changes sky colour and a global lighting factor. Regional weather is a scheduled state machine, not a volumetric simulation. Rain and snow effects remain near the camera. Sky visibility, light-based hostile spawning and sleep-to-morning behaviour use bounded, cached queries invalidated by nearby edits; they do not scan all buildings every frame.

Water and lava use **bounded local block-fluid rules** with source/flow levels, buckets, gravity, swimming/drowning and explicit interactions. Aim for familiar Java behaviour inside the supported active envelope. Natural bodies may start as static sources in M2, but final local propagation/removal and water/lava contact must be defined and tested in M5. Unloaded fluid does not simulate. Bound active cells, pending work and propagation; saturation defers represented work without losing updates. Disclose departures from the reference at the envelope boundary. Sand/gravel-style falling blocks also require bounded work and safe entity admission.

Crops, furnace progress, entities and storage persist when unloaded. Core crop/furnace activity pauses outside the supported loaded ticking area and resumes from saved state; it does not manufacture offline production. Closing the game pauses world time. Any later subsystem with catch-up must bound it explicitly and must not depend on system-clock manipulation.

## 8. Creatures and combat

Use project-authored blocky creatures with familiar core roles: passive farm animals that can be fed/bred, a close-range night threat, a ranged threat and a cave threat. Retain at least two passive and three hostile species. Night/light, distance, despawn and persistence rules are explicit; visual/audio cues make each behaviour readable.

Combat follows the Java-style attack-cooldown, reach, knockback, armour and damage-feedback loop; include basic melee, a bow/projectiles and shield blocking. There is no separate dodge/stamina resource. Essential encounters must work with the active-creature budget: 12 fully active creatures normally, 24 at the heavy-scenario ceiling. Distant creatures persist as compact state, sleep or are deterministically respawned according to explicit rules. They do not retain a live physics body or pathfinder everywhere in the world.

Navigation is local and voxel-aware. Creatures have constrained movement abilities and can disengage when no bounded path is available. No world-scale navigation-mesh rebake follows a terrain edit. Projectiles use swept traces and bounded lifetimes; dropped items merge into stacks and have a density cap.

## 9. Visual and audio direction

Aim close to Java Edition's familiar block appearance: one-metre cubic terrain, readable grass/dirt/stone layers, squared trees, pixel-textured tools, blocky creatures, crisp nearest-filtered materials and simple sky/clouds. Use original 16 × 16 material tiles with safe atlas padding/mip handling, limited custom models for plants/stairs/slabs and the specified lighting path. HUD composition includes a centred crosshair, nine-slot hotbar, health/hunger/armour feedback and slot-based inventory/grid crafting; all artwork, typography treatment, sounds and branding are project-authored. Compare rendered reference behaviours at 720p before declaring visual similarity complete.

The HD 620 preset uses 720p at native render scale, 96 m visual distance, 128 m data prefetch distance, no real-time shadows, no screen-space post effects and no full-screen transparency effects. See [PERFORMANCE.md](PERFORMANCE.md) for exact limits. Fog conceals the visual boundary but never substitutes for valid collision data.

Audio provides weather, footsteps, tool feedback, creature warnings and quiet environmental cues. Limit simultaneous voices and prioritize nearby critical sounds. Captions or visual cues accompany survival-critical audio. Interface text remains readable at 720p with adjustable scale and symbols that do not rely on colour alone.

## 10. Saving and the portable player experience

The distribution contains the executable, its data pack, build information, instructions and notices. Saves default to a stable per-user game directory, so extracting a new version does not overwrite worlds. An explicit portable-data mode can keep saves beside the executable when that directory is writable. Neither mode requires installation.

Offer automatic saves, Save and Quit, world backups, recovery from a previous checkpoint and a clear incompatible-version message. Never silently open an old world with a different terrain generator. An interrupted write can lose only work after the last durable transaction, not corrupt previously committed play.

The main menu includes **Run performance check** and **Open diagnostics folder**. The check creates a disposable world, drives repeatable scenarios and writes a report without external programs. It never modifies a player's world or uploads data automatically. This is the only optional hardware-feedback action beyond downloading and running the game.

## 11. Definition of a complete game

Version 1.0 requires every scoped core survival/building system to function together in a persistent world. A new player must be able to complete the wood/stone/metal progression, establish a farm/base, survive, die/recover, save/reload and continue freely without debug tools. A mandatory quest finale, boss or extra dimension is not required. Temporary art is replaced, sounds and licences are accounted for, recipes and tutorials are complete, and no essential feature is a placeholder.

Completion also requires the target performance gates, save-integrity tests, clean-machine portable launch and repeatable cloud builds. A pleasant terrain demo is an engine milestone; it is not the completed survival sandbox. [ROADMAP.md](ROADMAP.md) gives the required progression from one to the other.
