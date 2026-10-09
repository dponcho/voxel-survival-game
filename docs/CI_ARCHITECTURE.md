# Native build and Windows export audit

The native engine is a reusable dependency of the game export. Ordinary GDScript,
scene, asset, project-setting and packaging changes must import/test/export the
game using matching existing binaries. They do not change the native build key.

## Why the previous workflow rebuilt

The previous workflow already attempted an exact engine cache restore, so it did
not deliberately compile on every gameplay change. Its boundaries were too broad:

- It hashed **all of `tools/ci`**, including export, package, audit and test
  orchestration. Changes to those scripts invalidated all three native binaries.
- Marking a PR ready for review, tagged releases, the weekly schedule and the
  default manual build explicitly requested a cold build. A configuration push
  could start both ordinary CI and a second cold workflow.
- The only reusable native output was an Actions cache. The uploaded player ZIP
  and symbols were not a complete editor/debug/release engine bundle. A cache
  miss or branch-scope boundary therefore forced compilation.
- Each hosted runner starts without the previous runner's object files. On a
  native cache miss, SCons rebuilt unchanged third-party translation units too.
- Cancelling ordinary CI on each push could discard an unfinished native build.

The September 6 run [34036830778](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778)
did require a native rebuild: it corrected a debug assertion at a terrain boundary.
It compiled and qualified all three binaries, then passed the M1 integration and
portable-package checks. This was a real native change, separate from the
unnecessary invalidation and forced-build problems above.

## Current responsibilities

| Layer | Inputs and result |
| --- | --- |
| Native identity | `native/**`, `build/patches/**`, dependency lock, Windows compiler flags, `engine_recipe.py` and `build_support.py` |
| Native acquisition | Exact cache, then a qualified artifact with the same key; source build only on a genuine miss or an explicit cold-proof request |
| Native qualification | Checks the embedded identity and required native classes in the editor and both export templates before reuse/publication |
| Game export | Downloads the selected bundle, verifies every file, imports current game content, exports debug/release, runs M1 correctness checks, audits dependencies and tests fresh offline extractions |
| Delivery | Portable Windows x86-64 ZIP, build identity/checksum, separate symbols and test evidence |

`tools/ci/engine_recipe.py` owns compiler setup and compilation. Shared source
acquisition/command helpers live in `build_support.py` and participate in the key.
Export/package logic lives in `pipeline.py`; artifact selection lives in
`native_bundle.py`. Changes to the latter two do not invalidate native code.
The DLL allowlist is an export audit input, not a compiler input.

Git checkout uses LF for implementation text, and identity sorts relative paths
explicitly, so Linux and Windows identify the same native inputs. The original
six specification documents retain their existing byte-preservation attributes.

The engine job publishes a qualified, content-addressed native artifact for up to
90 days independently of game-test success. It includes the matching editor,
debug/release templates, manifest, notices, symbols and pinned dependency-audit
utility. Existing artifacts with more than seven days remaining are reused
instead of duplicating the large bundle on every game build. The audit utility
never enters the portable player ZIP. Cache hits do not install a compiler or
SCons; migration of an older bundle may download the pinned audit utility once.

Ordinary CI, PR readiness and releases now use reuse by default. The cold-proof
workflow is manual-only. Ordinary CI keeps an already running workflow alive
when another commit arrives, allowing the completed native work to be reused.
All actions remain pinned, and workflows use read-only permissions except the
existing authorized tagged-release attachment job.

## Trust and unavoidable misses

An artifact is not accepted on its name alone. Its archive digest, manifest,
native identity and every bundled file are checked. Cross-run reuse accepts
qualified default-branch runs or earlier runs of the same pull request from the
same repository. Main never consumes an untrusted PR's binaries. Corrupt inputs
fail visibly rather than silently falling back to an expensive build.

GitHub [isolates cache scopes and may evict caches](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).
Artifact fallback survives cache eviction while its retention period lasts.
A first native version, an expired/missing bundle, or the first trusted build
after merging a PR-only native version can still require compilation. A checkout
with the same inputs and an available trusted bundle skips compilation. This does
not promise permanent storage or reuse of binaries across trust boundaries.

`build/native-cache-migration.json` maps exactly one unchanged native source key
to the verified September 6 embedded engine identity. It preserves that binary
identity rather than relabelling an executable. Any native input change disables
the mapping. `BUILD_INFO.json` records both the current native source key and the
actual embedded engine identity. Migration is useful only if the old cache still
exists; the old player artifact cannot substitute for the complete engine bundle.

## GDExtension evaluation

Voxel Tools supports a GDExtension edition that can run with official Godot
binaries. The pinned Voxel Tools 1.7 source includes its extension build entry
point and Windows x86-64 debug/release library configuration. Its published
extension release targets Godot 4.5 or newer. This makes official Godot 4.7.2 plus
a voxel extension a viable experiment, not an already qualified Cairn backend.
See [Voxel Tools releases](https://github.com/Zylann/godot_voxel/releases/tag/v1.7),
[edition guidance](https://voxel-tools.readthedocs.io/en/latest/getting_the_module/)
and [Godot's extension overview](https://docs.godotengine.org/en/stable/tutorials/scripting/gdextension/what_is_gdextension.html).

Cairn currently compiles project classes into Godot and subclasses Voxel Tools'
C++ generator/mesher types. Its M1 patches reach internal scheduling, mesh upload,
mesh retirement, request revisions and voxel write locks. An unmodified prebuilt
extension does not contain those patches, and the public script API does not
replace them. Simply switching binaries would remove the tested safeguards.

A migration would port Cairn's native classes to extension-compatible bindings
and carry the required hooks in a patched Voxel Tools extension, preferably a
single extension build with explicit C++ ownership. Godot itself could then remain
an official prebuilt dependency. Pin and hash the official editor/templates,
godot-cpp API and extension toolchain; retain debug and release DLLs in exports.
Test registration, generation, boundary edits, collision/readiness, cancellation,
queue/payload limits and clean exit, then repeat the same four-profile target
comparison and fresh offline ZIP checks. Upstream describes its extension edition
as less tested. No extension migration, renderer change, save-format change or
target-performance certification is part of this CI correction.

## Acceptance evidence

Cloud validation passed in producer run
[36180365572](https://github.com/dponcho/voxel-survival-game/actions/runs/36180365572)
and game-only follow-up run
[36183549961](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961).
Both runs passed all 12 regression tests on Linux and Windows, including native-key
invalidation and reuse logic, and the Linux sanitizer native fixture.

The producer's native job `108221080856` encountered actual exact and legacy cache
misses, compiled and qualified the matching editor/debug/release binaries, saved
the exact cache and published the qualified native bundle before the separate
export job `108262732907` passed. The follow-up native job `108264737945` hit the
exact cache and passed qualification; compiler installation, native compilation,
cache save and bundle publication were skipped. Its export job `108264995129`
downloaded the same producer artifact
[10888733603](https://github.com/dponcho/voxel-survival-game/actions/runs/36180365572/artifacts/10888733603),
verified its SHA-256 and passed all export/package checks.

The native source key and actual embedded `engine_inputs` identity are both
`6adda08d3b832e3e5c40a41fd5b7bcd527bd2d1d6b274cd37b039a2371b61d7f`;
these runs did not use the legacy migration identity. The native artifact archive
SHA-256 is `891e85323d95c1c7204c854237ab982c082fb3095cbaefbd64b8b5f2b91673f3`,
with recorded expiry `2026-12-24T19:33:03Z`.

These runs establish exact-cache native reuse and a real cross-run export download
of the qualified artifact. They did not exercise native acquisition's artifact
fallback after an exact-cache miss; that selection path has mocked regression
coverage only. See [M1_EVIDENCE.md](M1_EVIDENCE.md) for the player candidate and
package evidence. The [five supplied laptop runs](M1_TARGET_REVIEW.md) match that
candidate but leave qualification blocked on measurement and pacing issues.
Native reuse is cloud-verified; no target profile is certified.
