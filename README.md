# Cairn

A native Windows voxel survival sandbox following Java Edition's core survival
and building conventions, with original content. The authoritative specification
is [GAME_DESIGN.md](GAME_DESIGN.md), with [ARCHITECTURE.md](ARCHITECTURE.md),
[ROADMAP.md](ROADMAP.md), [PERFORMANCE.md](PERFORMANCE.md),
[TESTING.md](TESTING.md) and [AGENTS.md](AGENTS.md).

**M1: cloud passed; laptop reports reviewed; qualification blocked.** The
candidate includes temporary terrain fixtures, voxel-box movement and automated
performance comparisons. Survival gameplay and durable worlds are later milestones.
See [the M1 evidence record](docs/M1_EVIDENCE.md), [target review](docs/M1_TARGET_REVIEW.md)
and [laptop testing instructions](docs/M1_TESTING.md). M2 waits for the measurement
and pacing gaps to be resolved. A new comparison run is not requested yet.

The [core reference contract](docs/JAVA_CORE_REFERENCE.md) records the user-selected
Java Edition direction. Core survival/building comes first; automation circuits,
enchanting, brewing, extra dimensions and bosses are deferred until after 1.0.

[Download the cloud-verified M1 Windows candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889930434)
from the [successful reuse-and-export run](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961).
This game-only follow-up reused the qualified native bundle and skipped compilation.
The candidate has target-machine measurements but no qualified profile yet.

## Portable builds

Successful CI runs retain a `Cairn-windows-x86_64-<commit>` artifact containing the
portable ZIP, SHA-256 checksum and build information. Download the artifact, extract
the contained player ZIP, and open `Cairn.exe`. Keep `Cairn.pck` beside it.
There is no player installation, account or first-launch download.

All compiler/tool setup and game execution for development tests run in GitHub
Actions. Source/toolchain hashes are locked in `build/dependencies.lock.json`.
CI restores matching native binaries from an exact cache or qualified artifact.
Game scripts, scenes and assets are exported and tested without changing the native
key. A native source/configuration change or unavailable bundle builds automatically;
an explicit manual cold-proof run can bypass reuse. See the [CI architecture audit](docs/CI_ARCHITECTURE.md)
for invalidation rules, artifact trust and the GDExtension evaluation.
Only authorized `v*` tags invoke release publication; ordinary builds are artifacts.

The package/evidence and symbols are separate artifacts. Cloud headless success
does not establish OpenGL driver compatibility or HD 620 performance.
