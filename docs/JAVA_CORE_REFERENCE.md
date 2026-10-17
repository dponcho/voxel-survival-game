# Java Edition core reference contract

User-approved direction, 2026-09-26: make Cairn as close as practical to Minecraft
**Java Edition** in core mechanics, behaviour, features and appearance. Deliver
core survival/building in 1.0. Automation circuits, enchanting, brewing, additional
dimensions and boss progression are deferred until after 1.0. This supersedes
the earlier list-only crafting, 8+24 inventory, independent stamina/exposure and
mandatory cairn/storm quest design. It is a requirements change, not an assertion
that the current M1 fixture implements these features.

Use project-owned code and original or appropriately licensed textures, models,
audio and interface art. Familiar functional conventions and common materials
are intentional. Cairn has its own name/branding. It does not load Minecraft
worlds, data packs, mods, assets or network protocols.

## Behaviour and appearance required for core 1.0

| Area | Cairn requirement | Acceptance evidence |
| --- | --- | --- |
| Movement/input | Java-style WASD, Space jump, Ctrl sprint, Shift sneak with ledge protection, E inventory, mouse attack/use, hotbar 1–9/wheel, Q drop, F swap hands; remappable | Movement/reach/ledge and input/focus cases against documented reference settings |
| Mining/placement | Hardness, appropriate tool/tier, durability and drops; target outline and break cracks; face/orientation placement, support rules and player/actor occupancy | Boundary edits, denied edits without consumption, tool/drop accounting and visual feedback checks |
| Inventory | Nine hotbar + 27 backpack slots, four armour slots, offhand; ordinary stacks 64, declared exceptions 16 or one; split, shift-transfer, drag and quick selection | Full-inventory, cursor-stack, transfer, stacking and save/reload transaction tests |
| Crafting | Inventory 2×2 and table 3×3 grids; shaped and shapeless recipes; recipe-book search/preview/assistance; basic recipes have no narrative lock | Independent matching/quantity tests; full output slots, cancelled interactions and crash-safe ingredient/output transfer |
| Materials/equipment | Wood → stone → smelted metal → advanced mining tools; pickaxe, axe, shovel, hoe, sword, bow, shield, armour, buckets; explicit harvest/drop tables | All scoped material tiers and food/building recipes reachable from ordinary spawn resources |
| Building set | Grass/dirt/stone, logs/planks/leaves, ores, sand/gravel, glass, lights, stairs/slabs, fences, doors/trapdoors, storage, beds, crafting table/furnace and water/lava | Shape/orientation/support rules, seams, light propagation and construction-envelope admission |
| Smelting/cooking | Furnace input, fuel, output and timed progress; persist state; pause when its area stops ticking | Fuel accounting, output blocking and unload/reload tests without offline production |
| Survival/combat | Health, hunger/saturation, regeneration, armour, attack cooldown/knockback, bow/shield, fall/fire/drowning damage and difficulty; no extra stamina/exposure meters | Explicit versioned numeric rules; damage/food/sprint/cooldown and item accounting cases |
| Spawn/sleep/death | Safe initial spawn; bed respawn with safe fallback; sleep advances to morning when allowed; inventory/equipment drop on death and age only while loaded | Bed removal/obstruction, hazard death, expiry, cap pressure, save/reload and no duplication |
| Farming/creatures | Three crops with tilling/hydration/light rules; feeding/breeding of passive animals; at least two passive and three hostile species with night/light spawning | Bounded active population/pathfinding; growth, breeding and spawn cases; no unloaded-time production |
| Terrain/exploration | Seeded block terrain with recognisable land/soil/stone layering, forests, caves, ores, water and three optional landmark families across four regions | M2 deterministic golden chunks, safe spawn and cross-chunk structures; core resources reachable |
| Fluids/falling blocks | Source/flow levels, bucket placement/removal, water/lava interaction and gravity-driven sand/gravel within explicit finite work limits | Source removal, border/unload, cancellation and saturation convergence tests |
| Free-build mode | Creative-style block catalogue, flight, instant break and no survival item consumption; retain world/edit safety caps | Flight/control and creation/selection tests; independent survival inventory rules |
| Visual language | One-metre cubes, squared trees, crisp original 16×16 pixel tiles, blocky mobs/tools, simple sky/clouds, readable grass/stone layers, hotbar/health/hunger and grid inventory | Rendered gameplay comparisons at 720p, including movement, mining, placement, inventory and night lighting |

Match ordinary interactions closely before inventing additional systems. Before
implementing a subsystem, record the specific Java reference version/behaviour,
numeric settings and any deliberate deviation in its tests/design notes. The
reference contract is a fixed scope of core features, not a promise to chase
every future Minecraft update or duplicate its entire content catalogue.

The input and crafting conventions are grounded in Mojang's
[controls guide](https://www.minecraft.net/en-us/article/minecraft-controls) and
[crafting guide](https://www.minecraft.net/en-us/article/how-craft).
Mojang's [spawn/death guide](https://www.minecraft.net/en-us/article/spawning-and-dying)
describes bed respawning and items remaining at death with loaded-time expiry;
use it as behavioural context, then specify Cairn's bounded transactions and
expiry rules before implementation. These sources describe reference behaviour,
not evidence of implemented Cairn functionality.

## Explicit differences and unchanged constraints

- Single-player, offline, finite 16,384 × 256 × 16,384 world; the existing
  coordinate range, safe world edge, 96 m visual and 128 m data radii remain.
- Native Windows portable ZIP, Godot Compatibility and the same HD 620/RAM target.
  Keep all frame/throughput/memory gates. Existing M1 scenarios retain their
  6.5 m/s stress speed regardless of future reference-tuned player movement.
- Creature counts, active simulation, geometry, lighting, fluids, dropped items
  and queues remain bounded. Behaviour beyond the supported envelope must be
  explicit; never silently omit accepted blocks or destroy overflow inventory.
- Original content and a finite selected block/creature set; exact Minecraft
  assets, branding, worlds and file/network compatibility are outside the product.
- No automation/redstone analogue, enchanting, brewing, additional dimensions,
  bosses, multiplayer or mod loader in core 1.0. Those are later work, not hidden
  completion requirements for M8.

M1 must first resolve the [target-review findings](M1_TARGET_REVIEW.md). M2 then
implements the deterministic editable foundation for this core direction; it
does not absorb all survival, crafting or later feature work into one milestone.
