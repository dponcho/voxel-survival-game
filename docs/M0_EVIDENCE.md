# M0 evidence record

Status: **in_progress**. No cloud build or target result is claimed yet.

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

Pending: first successful complete cold-cache cloud build and its artifact identity.
Target OpenGL launch and HD 620 frame/memory performance are **not_run**.
Hosted Windows headless checks do not certify rendering. A rendered smoke test
is not yet available. The complete benchmark is an M1 deliverable.

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

Next bounded task: repair any cloud build failure, obtain the first verified
portable ZIP and record its evidence here. Do not start M1 in this task.
