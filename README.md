# Cairn

An original native Windows voxel survival sandbox. The authoritative specification
is [GAME_DESIGN.md](GAME_DESIGN.md), with [ARCHITECTURE.md](ARCHITECTURE.md),
[ROADMAP.md](ROADMAP.md), [PERFORMANCE.md](PERFORMANCE.md),
[TESTING.md](TESTING.md) and [AGENTS.md](AGENTS.md).

**M1: engine experiment; cloud passed, target performance unverified.** The
candidate includes temporary terrain fixtures, voxel-box movement and automated
performance comparisons. Survival gameplay and durable worlds are later milestones.
See [the M1 evidence record](docs/M1_EVIDENCE.md) and [laptop testing instructions](docs/M1_TESTING.md).

[Download the cloud-verified M1 Windows candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992504297)
from the [successful source-to-ZIP run](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778).
Target hardware performance remains unverified.

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
