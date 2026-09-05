# M0 evidence record

Status: **M0 complete — cloud_passed_target_unverified**. The complete
cold-cache source-to-ZIP run passed on 2026-09-05.

The six root specification documents are authoritative and preserved verbatim.
This increment implements the title screen, native module registration, matching
Windows editor/debug/release builds, package checks and candidate artifact workflows.
There is no generation, world persistence or gameplay, and no compatibility format
has been introduced. M1 and later milestones have not started.

## Locked inputs

- Godot 4.7.2: `ed1daf0bf001b61586d9930840f2f1394092c079`.
- Voxel Tools 1.7: `2ac9f5f8a8219bf499314cc0fad54ffc47df908f`.
- LLVM-MinGW UCRT 20250709; Python 3.12.10; SCons 4.9.1.
- Download SHA-256 values are in `build/dependencies.lock.json`.
- Native source, compiler archive, source archives, build flags, patches and CI
  scripts all participate in the engine input/cache identity.

## Acceptance evidence

The workflow retains every executed command's exit code and duration in
`commands.jsonl`, full command logs, compiler/runner identity, all binary hashes,
dependency audit, editor/debug/release self-tests and two offline fresh-extraction
reports. Successful jobs publish `candidate.json` with the ZIP digest, commit,
run URL and whether the engine was built on a cache miss. Symbols are separate.

First cold cloud run: https://github.com/dponcho/voxel-survival-game/actions/runs/33941123135
at source `65cc62df14eb42be656d07be8809f35ed93abe55` (PR merge build
`ae54499a86293accd757fdd7ea7b60d579dd4f03`). Linux and Windows regression
tests passed; all three engine targets compiled; editor import and editor/debug/
release native self-tests passed. Packaging failed because the initial system-DLL
allowlist omitted seven Windows components. No candidate ZIP passed that run.

The audit now explicitly includes those components. Microsoft documents
[Windows API sets](https://learn.microsoft.com/en-us/windows/win32/apiindex/windows-apisets),
[DirectWrite](https://learn.microsoft.com/en-us/windows/win32/api/dwrite/nf-dwrite-dwritecreatefactory),
[Shcore](https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-getdpiformonitor)
and the [Winsock compatibility library](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-2-architecture-2).
Unknown API sets and external C++ runtime DLLs remain rejected.

The complete cached build [33977718075](https://github.com/dponcho/voxel-survival-game/actions/runs/33977718075)
passed editor import, editor/debug/release native self-tests, the x64 DLL audit,
and both firewall-blocked fresh extractions (including a path with spaces and
Unicode). Its game build is `61bc8564721fbd178a9514f355203693b006e647`.
The [portable candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/33977718075/artifacts/9972862442)
contains a 29,833,416-byte player ZIP with SHA-256
`411001105163dd038883288e622c5b951fa0d4cff88faddf0dc5f7a90e7384fd`.
Evidence is retained as artifact `9972869055`; symbols are separate.

On 2026-09-05 the user supplied a screenshot of this exact build running on
Windows. It shows the title screen, `gl_compatibility` renderer and
"Startup check passed. Native modules are ready." This establishes a visible
Windows launch and successful interactive startup check on the user's machine.
The screenshot does not establish hardware identity or frame/memory performance.

The final [cold-cache run 33978065158](https://github.com/dponcho/voxel-survival-game/actions/runs/33978065158)
passed all jobs, with cache restoration explicitly skipped and `cold_cache: true`
in its retained candidate report. It ran from 16:30:13 to 19:44:52 UTC on
2026-09-05 (3 hours 14 minutes 39 seconds). The editor, debug and release source
builds took 4,768.64, 3,315.91 and 3,248.26 seconds respectively; all exited zero.
The compiler logs are retained in the evidence artifact. Actions prints each
target's start, rather than streaming individual compilation lines.

| Final cold-build evidence | Value |
| --- | --- |
| Source branch commit | `d573ff3a897c87da4f03eb55b7870866df566fbc` |
| Tested PR merge/game commit | `6a82cd6dd3912709dbe9eefb7aff6aeab8deba30` |
| Engine input identity | `5632e92829aaa7c7221d9ede9cd77c1b141cf742feb579726bf29abf6e6adf86` |
| [Portable player artifact](https://github.com/dponcho/voxel-survival-game/actions/runs/33978065158/artifacts/9975747665) | `9975747665` |
| Inner player ZIP size | 29,833,421 bytes |
| Inner player ZIP SHA-256 | `15f9debc406b65364fbd25a52a6fb49e2b35db5fa25eaeaae6dbd6828c90eae7` |
| [Evidence artifact](https://github.com/dponcho/voxel-survival-game/actions/runs/33978065158/artifacts/9975754715) | `9975754715` |
| [Separate symbols](https://github.com/dponcho/voxel-survival-game/actions/runs/33978065158/artifacts/9975754178) | `9975754178` |

Linux and Windows packaging regression tests passed. Matching-editor import,
editor/debug/release native self-tests, x64 dependency audit, and both fresh
firewall-blocked extraction tests passed. Both extraction tests used isolated
user data and a PATH without development tools; one used spaces and Unicode.
The resulting executable and PCK are packaged together with dependency notices.
Artifacts are retained for 30 days; a future authorized release must retain the
exact package and evidence under the repository's tag/release process.

HD 620 frame/memory performance remains **not_run**. Hosted Windows headless
checks do not certify rendering. The user screenshot above covers the earlier
cached candidate, not the final cold-build executable. The complete benchmark
is an M1 deliverable.

## Implementation choices

Builds use the upstream-supported LLVM-MinGW static C++ runtime path and the
Windows UCRT. WinRT TTS and AccessKit are disabled in this minimal build because
they require additional SDK downloads; the M0 UI uses built-in Godot controls.
GPU compute is disabled. These choices do not replace later accessibility or
performance requirements. No existing specification requirement is relaxed.

The M0 self-test checks the title scene, actual instantiation and scene lifecycle
of native terrain, blocky mesher and voxel mover, disabled terrain triangle
colliders, one terrain worker, native/pack identity and temporary default data
storage. World/save tests belong to the milestones that introduce those systems.

M0 stops here. The next roadmap task is M1's target-machine engine proof;
it has not been started as part of this task.
