# Cairn

An original native Windows voxel survival sandbox. The authoritative specification
is [GAME_DESIGN.md](GAME_DESIGN.md), with [ARCHITECTURE.md](ARCHITECTURE.md),
[ROADMAP.md](ROADMAP.md), [PERFORMANCE.md](PERFORMANCE.md),
[TESTING.md](TESTING.md) and [AGENTS.md](AGENTS.md).

Only **M0: cloud build foundation** is currently being implemented. The candidate
opens a title screen and offers a startup check; gameplay has not been implemented.
See [the milestone evidence record](docs/M0_EVIDENCE.md) for actual verification status.

## Portable builds

Successful CI runs retain a `Cairn-windows-x86_64-<commit>` artifact containing the
portable ZIP, SHA-256 checksum and build information. Download the artifact, extract
the contained player ZIP, and open `Cairn.exe`. Keep `Cairn.pck` beside it.
There is no player installation, account or first-launch download.

All compiler/tool setup and game execution for development tests run in GitHub
Actions. Source/toolchain hashes are locked in `build/dependencies.lock.json`.
CI automatically builds a matching custom editor and both export templates on a
cache miss. Manual Windows builds and the weekly cold build can bypass the cache.
Only authorized `v*` tags invoke release publication; ordinary builds are artifacts.

The package/evidence and symbols are separate artifacts. Cloud headless success
does not establish OpenGL driver compatibility or HD 620 performance.
