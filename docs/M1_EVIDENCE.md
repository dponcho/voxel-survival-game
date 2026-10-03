# M1 engine experiment evidence

Current milestone status: **blocked; target not qualified**. The original
[five-run laptop review](M1_TARGET_REVIEW.md) and subsequent private exact-build
reviews retain unresolved gates. The candidates below passed cloud checks;
none qualifies M1.

## Current Windows candidate: finite shader-matched fog boundary

Implementation `f1fea7bc56dc7aeef4f372e26baada84bbce7132` configures the actual
Environment with Compatibility depth fog: begin 16 m, opaque end 96 m,
density 1, curve 1 and no height fog. The pinned radial smoothstep equation
matches the conservative frontier distance. Reports record the actual settings;
the existing density field is no longer hardcoded. The analytic boundary is
evaluated before shader half packing and does not prove rendered pixel coverage.
See [fog/frontier semantics](M1_FOG_FRONTIER.md). Visual/data demand remains
96/128 m; resolution, routes, ticks, workloads and resource/time caps remain.

[CI 37160455260](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260)
passed all three jobs on 2026-10-03 UTC. Static job `111312633017` passed
12 packaging/cache regressions, Python compile checks and five native sanitizer
suites. Native job `111312696593` reused the exact native cache and independently
requalified editor/debug/release binaries; compilation was skipped. Export job
`111312843050` passed engine import, actual-Environment fog regressions,
independent smoothstep values and before/at/after-96 m crossings, invalid-input
handling, saved-report reconciliation, geometry, edits, collision,
eviction/cancellation, all four streaming profiles, dependency audit and two
fresh offline extractions. The 20 demand cases and four mesh-only halo checks
still pass. Five smoke exports completed with no integration failures; every
accepted N2/H2 edit submitted, with no cancellations, timeouts or pending edits
at closure. Every report records the configured finite fog profile.

The short cloud 32³ smoke runs pass the conservative H1/H2 coverage check.
Both 16³ profiles still fail it: pending regions reach approximately 95.5 m,
inside the 96 m boundary. Those failures remain recorded and prevent scenario
qualification; green integration tests do not erase them. Prior target upload
failures have no new target evidence resolving them. Hosted render smoke says
`not_run`; exact-build HD 620 rendering/performance, moving-frontier readiness,
full heavy diagnostics overhead, retention and qualification repeats remain
unverified. Frame/pacing attribution and A/B remain inconclusive.
**M1 remains blocked; no profile is qualified.**

Download [Windows player 11287845333](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287845333)
and extract its contained portable ZIP. Expiry: 2026-11-02 at 23:10 UTC.
[Export evidence 11287477678](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287477678),
[native evidence 11286619792](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11286619792)
and [symbols 11287422754](https://github.com/dponcho/voxel-survival-game/actions/runs/37160455260/artifacts/11287422754)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `f1fea7bc56dc7aeef4f372e26baada84bbce7132` |
| Exported synthetic merge / game build ID | `c1a71cdf77fe4ee9810eff3573f93460c9c2cc0a` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `bcdeb9f91c476505be7ed785faa8ccd4b66951984bd459e41817ce998ee56058` |
| Contained portable ZIP SHA-256 | `0eb379163e88441d0380b48ede68ecb5510037d2d4a6f80bad387feecfd4d130` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. The synthetic merge includes the implementation
commit. No local engine installation, compilation or execution ran.
Review one exact-build 32³/one-worker laptop baseline before another full matrix
or selecting the next bounded correction. [Laptop instructions](M1_TESTING.md)
and [development handoff](NEXT_TASK.md) describe that prerequisite.
Detailed uploaded target measurements remain private.

## Previous Windows candidate: world-space demand and meshing halo

Implementation `c1ad85b55359a3e013ef43d017223116617a0bca` covers the full fixed
96 m visual and 128 m data-only envelopes from the actual viewer position.
It replaces a block-snapped demand box that could omit required edge regions.
Meshing data follows every demanded render block plus its existing neighbouring
data-block halo. Bounds are clipped before coordinate narrowing; widened
intermediates and empty-demand handling avoid invalid or phantom requests.
The existing viewer/reference/difference lifecycle, settings, budgets and
save/generator formats remain. Two overlapping patch pairs were consolidated
with identical emitted code; repeat application against pinned source is stable.

[CI 37024767302](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302)
passed all three jobs on 2026-10-02 UTC. Static job `110896469348` passed
12 packaging/cache regressions, Python compile checks and five native sanitizer
suites, including an independent geometric demand/halo oracle. Native job
`110896642681` freshly built and qualified matching editor/debug/release binaries.
Export job `110946829805` passed import/export, native geometry, collision,
border edits, eviction/cancellation, all four profiles, dependency audit and two
fresh offline extractions.

The engine log contains 20 passing world-space demand cases across 32/1, 16/1,
32/2 and 16/2: fractional and negative positions, an exact block boundary and a
clipped world corner. Required and resident render counts match the independent
block-intersection oracle. The fractional pose requires 507 regions at 16³
or 98 at 32³ in the clipped M1 slab, within the unchanged 512-region cap.
Four fresh mesh-only checks prove the full clipped meshing-data halo loads
without a wider data-only viewer hiding omissions. Resident data and retirement
remain within existing caps. Five smoke exports completed with no integration
failures; all accepted N2/H2 edits submitted, with zero cancellations, timeouts
or pending edits at closure. Saved-report reconciliation passed.

Download [Windows player 11242141810](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242141810)
and extract its contained portable ZIP. GitHub reports expiry on 2026-11-01
at 17:25 UTC. [Export evidence 11242421606](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242421606),
[native evidence 11242440353](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242440353)
and [symbols 11242116942](https://github.com/dponcho/voxel-survival-game/actions/runs/37024767302/artifacts/11242116942)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `c1ad85b55359a3e013ef43d017223116617a0bca` |
| Exported synthetic merge / game build ID | `77be48ed0ac431da50f7fd9d267873feee403123` |
| Native source key | `11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d` |
| Outer player archive SHA-256 | `4f2627ef0be796e70e2bf1a9bc00a2bb7138d9d3191469354af3eb3c6c83b484` |
| Contained portable ZIP SHA-256 | `0151f42967f371384fb7c77d5763489b001fe77a91720bc9ab4d3ed11c99c374` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. The synthetic merge includes the implementation
commit. No local engine installation, compilation or execution ran.

These are settled demand and cloud correctness checks, not rendered HD 620
coverage or performance qualification. Exponential fog is unchanged; its analytic
model has no finite opaque boundary. Moving-frontier readiness, prior target
upload failures, frame/pacing attribution, full diagnostic overhead, retention
and qualification repeats remained unresolved. The finite-boundary candidate
above supersedes this build. Detailed uploaded target measurements remain private.

## Previous Windows candidate: indexed upload batches

Implementation `1a03f16747fa01563150b8a03f6cf6a219718312` preserves source vertex
reuse within the existing 1,024-triangle upload batches. Triangle order,
normals, UVs, color/AO, tangents, materials and surface/draw counts are retained.
The worker-local remap is bounded; malformed indices or channel layouts fail
admission. Upload and retirement estimates now use actual vertex and index counts,
with conservative tangent reserve and no renderer buffer readback.
A full quad batch estimates 143,360 bytes instead of 208,896 (about 31% less).
This is an input-payload reduction, not a measured target timing improvement.
[Measurement semantics](M1_OPERATION_DIAGNOSTICS.md) describe its limits.
Workloads, settings, budgets and save/generator formats are unchanged.

[CI 36893428789](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789)
passed all three jobs on 2026-10-01 UTC. Static job `110474396180` passed
12 packaging/cache regressions, Python compile checks and four native sanitizer
suites, including remap reconstruction, resets, malformed indices and bounds.
Native job `110474542921` built and independently qualified the matching
editor/debug/release binaries after an exact native-cache miss.
Export job `110528071000` passed native geometry/attribute/winding and
unchanged-surface-count regressions, import/export, debug/release smoke,
all four streaming profiles, collision/edit/eviction/cancellation checks,
dependency audit and two fresh offline extractions.
All five smoke exports completed with no integration failures; every N2/H2
accepted edit submitted, with zero cancellations, timeouts or pending edits at
closure. Saved-report reconciliation passed. No CI check in this run failed.

Download [Windows player 11186079360](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11186079360)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-31
at 18:52 UTC. [Export evidence 11185869587](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185869587),
[native evidence 11185868553](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185868553)
and [symbols 11185219665](https://github.com/dponcho/voxel-survival-game/actions/runs/36893428789/artifacts/11185219665)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `1a03f16747fa01563150b8a03f6cf6a219718312` |
| Exported synthetic merge / game build ID | `25e4501360187b3a6afc56e507ac74f841c788b7` |
| Native source key | `bb20d80d8e527335a7cb2e9a728c0eb1328812fd0650b66dcc494daea121763b` |
| Outer player archive SHA-256 | `c62f2e9217158957a470134a26dff5c678c6e76ce574f42a098987f4d6cf7ea4` |
| Contained portable ZIP SHA-256 | `374fa1830097c6f19894b1e9271b2dd1311ff14b9adf9001eaf9e1e2b92fd4fa` |

Completed logs and downloaded player/export/native evidence were inspected.
Archive digests, ZIP CRCs, contained checksums, build identities and native
manifest binary hashes matched. No local engine compilation or execution ran.
Cloud/headless checks do not establish rendered HD 620 performance.
The exact-build 32³/one-worker laptop baseline was reviewed privately on
2026-10-02 UTC. Build identity and raw evidence reconciled; accepted edit
submission met its latency gate in that run, with no missing-data movement
stops. Conservative heavy-streaming coverage and isolated upload limits still
failed. Frame/pacing attribution, rendered fog coverage, full diagnostic
overhead, allocation/retention and qualification repeats remain unresolved.
**M1 remains blocked; target not qualified.** That review motivated the
world-space demand correction above. Detailed uploaded measurements remain private.

## Previous Windows candidate: lifecycle correction

Implementation `5ce757dfdce039dea5cfbe1f4ceff76635a272d8` initializes fixture
camera/viewer pose before measurement and allows final accepted N2/H2 edits
their existing bounded acknowledgement window. Those final frames/native costs
stay measured; route commands stop at the original endpoint. Genuine timeouts
and explicit cancellation remain observable. Invalid GPU query values stay in
raw CSV, with validity counts and a separately scoped valid-sample peak.
[Measurement semantics](M1_OPERATION_DIAGNOSTICS.md) describe the limits.
Settings, workloads, formats and thresholds are unchanged.

[CI 36803692007](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007)
passed all three jobs. Static job `110183343579` passed 12 packaging/cache
regressions, Python compile checks and three native sanitizer suites. Native
job `110183424337` reused and requalified the matching binaries. Export job
`110183626534` passed import, native/evaluation/diagnostic/lifecycle tests,
debug/release smoke, all four streaming profiles, dependency audit and two
fresh offline extractions. All five smoke exports reconciled saved evidence;
every N2/H2 accepted edit submitted, with zero cancellations, timeouts or pending
edits at closure. Cloud timings do not establish HD 620 performance.

Download [Windows player 11137310682](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11137310682)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-31
at 02:06 UTC. [Export evidence 11136737690](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11136737690)
and [symbols 11136633094](https://github.com/dponcho/voxel-survival-game/actions/runs/36803692007/artifacts/11136633094)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `5ce757dfdce039dea5cfbe1f4ceff76635a272d8` |
| Exported synthetic merge / game build ID | `f3eb4ce72dd659f96df6d5e4804331c1fd4e1642` |
| Native source key | `81d54daaa9ffc8907de4e024c6f999f60b00dec21c21883608df1a49fc487f3e` |
| Outer player archive SHA-256 | `f56bbe77e7bdf5dd69b78343cf6a93321c76bb306ea85b473596c55030b34511` |
| Contained portable ZIP SHA-256 | `f9d4e963bbfdfe07d2939d25239f152518bbe8b8d17d69231c61ccd67dfb1769` |

Completed logs and downloaded player/evidence archives were inspected. Digests,
ZIP CRCs, the contained checksum and build identity matched. No local engine
compilation or game execution ran. Exact-build target performance remains
unverified; **M1 remains blocked**, and these fixes do not certify it.

## Previous Windows candidate: fog/frontier evidence

Implementation commit `7024be977653ffbe03376cda215323be58cb6835` on
`codex/m1-engine-proof` adds bounded [H1/H2 fog/frontier evidence](M1_FOG_FRONTIER.md):
mesh readiness, camera pose, conservative frontier distance and analytic fog
transmittance. Schema 5 retains missing boundaries/samples and reconciles saved
CSV rows with summary counts/minima. Settings, workloads, acceptance thresholds
and save/generator formats are unchanged.

[CI 36775406042](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042)
passed all three jobs. Static job `110091931750` passed the 12 packaging/cache
regressions, Python compile checks and three native sanitizer suites. Native job
`110092054562` built and qualified matching editor/debug/release binaries.
Windows export job `110137002347` verified native identity, passed Windows
packaging regressions, import, native/evaluation/helper tests, debug/release
smoke with saved-report reconciliation, all four streaming profiles, dependency
audit and two fresh offline extractions. All 33 ordered Voxel Tools patch entries
matched the pinned source. No check in this run failed.

Download [Windows player 11131500525](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131500525)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-30 at
23:08 UTC. [Export evidence 11131505658](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131505658)
and [symbols 11131026214](https://github.com/dponcho/voxel-survival-game/actions/runs/36775406042/artifacts/11131026214)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `7024be977653ffbe03376cda215323be58cb6835` |
| Exported synthetic merge / game build ID | `e51d00d0d3e847e4b1c04362df6642eef695c3ad` |
| Native source key | `81d54daaa9ffc8907de4e024c6f999f60b00dec21c21883608df1a49fc487f3e` |
| GitHub-reported outer player archive SHA-256 | `01ab158d2a8ce8ea2fe207c32a04a17903d292aeaf9e0d6ae0dc5df2318b94bd` |

Completed logs and artifact metadata were inspected. The archive was not
independently downloaded/hashed or executed locally. No local engine compilation
or game execution ran. Exact-build HD 620 coverage, edit latency, full diagnostic
overhead and pacing, shader/driver precision, allocation completeness, retention
and qualification repeats remain unverified. No corrected target baseline was
supplied; **M1 remains blocked**.

The exponential model has no finite analytic opaque boundary. The shader's
half-precision packing can round opacity; analytic transmittance and conservative
box/frustum overlap do not establish rendered-opacity boundaries or pixel
visibility. Unavailable boundary evidence remains inconclusive.

## Previous Windows candidate: edit visibility evidence

Implementation commit `525a079c414aa1c7c2ff531018b447d2b538ce8d` on
`codex/m1-engine-proof` adds bounded N2/H2 edit-to-mesh-submission evidence and
border/stale-result regressions. Save and generator formats, benchmark workloads
and thresholds are unchanged. Ordered patch entries matched the pinned Voxel
Tools source; local compilation/game execution did not run under the cloud build
rule.

[CI 36364646208](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208)
passed all three jobs. Static checks passed packaging/cache regressions, Python
compile checks and native fixture, operation and edit-visibility sanitizer tests.
The native job built and qualified the matching editor, Windows debug and release
templates. The export job verified their exact native identity, passed Windows
packaging regressions, native mesher and benchmark integration checks, debug and
release smoke, all four streaming profiles including border edits, dependency
audit and two fresh offline extractions. No check in this run failed.

Download [Windows player artifact 10950256937](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10950256937)
and extract its contained portable ZIP. GitHub reports expiry on 2026-10-28 at
03:21 UTC. [Export evidence 10949963015](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10949963015)
and [symbols 10949808351](https://github.com/dponcho/voxel-survival-game/actions/runs/36364646208/artifacts/10949808351)
are separate.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `525a079c414aa1c7c2ff531018b447d2b538ce8d` |
| Exported synthetic merge / game build ID | `3aa0b73091de21d860f3aaf12bc0fe26d654628c` |
| Native source key | `26d6169a6b9c2c8417a241ecae4ec3fee6829cfb9b4859edc39404b482320a1d` |
| GitHub-reported outer player archive SHA-256 | `2dcbb82c801507b079b7a36bd6e4dcc3520d8b74a22d3e7d2428aec7127baa59` |

The logs and artifact metadata were inspected. The player archive was not
independently downloaded/hashed or executed locally. Exact-build HD 620 edit
latency, diagnostic overhead, pacing/driver attribution, allocation completeness,
retention and qualification repeats remain unverified; M1 stays blocked.

## Previous Windows candidate: diagnostic-overhead accounting

[CI 36287728890](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890)
completed successfully on 2026-09-27 UTC (September 26 locally).
Download [Windows player artifact 10921940219](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921940219)
and extract the contained portable ZIP. GitHub reports expiry on 2026-10-27
at 02:17 UTC. Symbols are separate from the player distribution.

| Identity | Verified value |
| --- | --- |
| Implementation branch commit | `1c9b7c638bb6154ce78c06f50831a7eda1db737e` |
| Exported synthetic merge / game build ID | `404af829964d341524f6c7ae29b4aebdac683b2a` |
| Native source key | `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803` |
| GitHub-reported outer player archive SHA-256 | `e6ae070fbbf6000ad7f479891b421e39f3e5dedada12a0ff90dca3e86551cbac` |

The user approved publication to existing public PR #2. Schema 3 now accounts
for callback formatting, CSV submission and UI work, preserves the final callback,
drains each measurement writer before retirement, and separately times final
summary assembly/hash/write/UI work. Both A/B modes retain bounded histograms and
five-second timing blocks. Conservative evaluation rejects unstable repeats in
either mode, within-phase drift, incomplete workloads and ranges crossing 1%.
[Measurement semantics and limits](M1_OPERATION_DIAGNOSTICS.md) remain explicit:
wall time is not CPU service time, overlapping costs are not added, shared native
counters remain enabled, and switched A/B success cannot certify total overhead.

Static job `108531574512` passed 12 packaging/cache regressions, Python compile
checks and both native sanitizer suites. Native job `108531629036` used the exact
cache, requalified editor/debug/release and skipped compiler installation/build.
It reused qualified native artifact `10920566667`; no new native source was built.
Windows job `108531756571` passed 12 Windows regressions, import, native/evaluation
and queue-rejection tests, debug/release smoke with actual CSV reconciliation,
all four correctness profiles, streaming/collision/edit/eviction/cancellation,
dependency audit and two fresh offline extractions. No check in this run failed.

[Export evidence 10921845799](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921845799)
and [symbols 10921516464](https://github.com/dponcho/voxel-survival-game/actions/runs/36287728890/artifacts/10921516464)
are retained. Completed logs and artifact metadata were inspected; the new player
archive was not independently downloaded/hashed or executed locally.

Initial validation [36287222011](https://github.com/dponcho/voxel-survival-game/actions/runs/36287222011)
failed 32³/two-worker report integrity after earlier checks passed.
[Preserved evidence 10920778828](https://github.com/dponcho/voxel-survival-game/actions/runs/36287222011/artifacts/10920778828)
was downloaded and reviewed: incomplete output began after N1; no script error
was logged. Source review identified one-shot final-batch submission despite
transient native queue rejection. The follow-up adds bounded between-frame retries
outside gameplay and regressions for transient rejection, permanent blockage and
writer failure. The corrected full run passed; the original failure is preserved.

No native inputs, save/generator behavior, simulation workload or acceptance
threshold changed. Exact-build HD 620 overhead, edit visibility, pacing/driver
attribution, allocation and retention/qualification evidence remain unverified.
M2 remains gated. Review one corrected baseline before another full comparison
or final repeats. The [handoff](NEXT_TASK.md) names the next bounded implementation.

## September 26 candidate: phase-local attribution correction

[CI run 36280383637](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637)
completed successfully on 2026-09-27 at 01:29 UTC (September 26 locally).
Download [Windows player artifact 10920027865](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920027865)
and extract its contained portable ZIP. The artifact contains the ZIP, checksum
file and build identity. GitHub reports expiry on 2026-10-27 at 01:29 UTC.

| Identity | Value verified from CI logs/artifact metadata |
| --- | --- |
| Implementation branch commit | `3685dd472e5ffd3429ba5d35b7ee63c949b374e5` |
| Exported synthetic merge / game build ID | `b65ba3e409ba7a80da282b5297783533de2f6fc6` |
| Native source key | `3909c871bcac301ba2e0d91cd32b53b99555b9d9a30f2e3b62421b842145d803` |
| GitHub-reported outer player archive SHA-256 | `acf8f7b1c32a00c8a33ab38a5dc9f50ad9f5a428a0d08e91c0fba192c71c76b8` |

The source pins, compiler and flags are unchanged. The native instrumentation
changed the source key, so the ordinary reuse-enabled workflow built matching
editor/debug/release binaries after an exact cache/artifact miss. Native job
`108511005497` qualified them, saved the exact cache and published
[native artifact 10920566667](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920566667)
before game export. No manual cold build or redundant CI run was launched.

Static job `108510956501` passed all 12 packaging/cache regressions, Python
compile checks, the existing native fixture checks and the new phase/frame
regressions with address/undefined-behaviour sanitizers. Windows job `108525026003`
verified native identity/digests, passed all 12 Windows regressions, matching-editor
import and native/evaluation tests, debug/release smoke, all four correctness
profiles, streaming/collision/edit/eviction/cancellation, dependency audit and two
fresh offline extractions. Every smoke report checks actual operation CSV totals,
maxima, timestamps and phase isolation against phase/lifetime counters.

[Export evidence 10920157662](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10920157662)
and [separate symbols 10919853233](https://github.com/dponcho/voxel-survival-game/actions/runs/36280383637/artifacts/10919853233)
are retained. This session inspected completed logs and artifact metadata; it did
not independently download/hash the new archives or run the game locally.

The [correction](M1_OPERATION_DIAGNOSTICS.md) adds phase-local upload/deletion
maxima, bounded per-frame operation evidence and explicit completion versus
qualification. Lifetime counters, thresholds, workload, generator and saves are
unchanged. No current cloud check failed. Corrected exact-build HD 620 results,
end-to-end overhead, edit visibility, pacing/driver attribution, allocation and
retention/qualification evidence remain unverified. M2 remains gated. The
[handoff](NEXT_TASK.md) names the next bounded implementation task.

## September 25 reviewed candidate

The previous candidate's immutable cloud result was **cloud_passed_target_unverified** from
[GitHub run 36183549961](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961),
completed successfully on 2026-09-25. This is not an M1 target-performance pass.
Run status, completed job logs, artifact metadata and downloaded player/evidence
archives were inspected on 2026-09-25.

Download [player artifact 10889930434](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889930434),
then extract the contained `Cairn-windows-x86_64.zip` into a fresh folder.
GitHub reports an expiry of **2026-10-25 21:58 UTC**; retention can change.
The artifact includes the portable ZIP, `SHA256SUMS.txt` and `BUILD_INFO.json`.

| Identity | Verified value |
| --- | --- |
| Source branch commit | `68918f2a8ad63325b2be7d4c02ce05fa753aef63` |
| Exported synthetic merge / game build ID | `6874b8809094d22b33e05c60ef61c2e1c333494a` |
| Native source key and actual embedded engine identity | `6adda08d3b832e3e5c40a41fd5b7bcd527bd2d1d6b274cd37b039a2371b61d7f` |
| Godot source | `ed1daf0bf001b61586d9930840f2f1394092c079` |
| Voxel Tools source | `2ac9f5f8a8219bf499314cc0fad54ffc47df908f` |
| Inner portable ZIP SHA-256 | `0dd72b172cade30c7a0a7fb8b005490fac39567ff8afcc0f049c209561b4346b` |
| Inner portable ZIP size | 29,892,003 bytes |
| Outer Actions player archive SHA-256 | `c0c4ee6ab2f15aaf1067ccad281416d6888ad446434966915eda4533530e5c92` |

The downloaded outer archive matched GitHub's digest. The inner ZIP was hashed
independently and matched both `SHA256SUMS.txt` and `reports/candidate.json`.
These are different archives and checksums. The current engine identity is the
new source key above; the historical legacy identity was not used by this build.

Supporting artifacts are [export evidence 10889685801](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10889685801),
[separate symbols 10888974332](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888974332)
and [native reuse evidence 10888649212](https://github.com/dponcho/voxel-survival-game/actions/runs/36183549961/artifacts/10888649212).
The export evidence archive SHA-256 is
`d7d2414bcd7cb2b7f9f266721380f74961419a74793943c6ab33267aa4772837`,
also verified after download.

## September 25 executed cloud checks

The follow-up static job `108264637172` passed all 12 packaging/native-reuse
regression tests, Python compile checks and native fixture checks with address
and undefined-behaviour sanitizers on Linux.

Native job `108264737945` restored the exact cache and requalified the custom
editor and both Windows templates. Compiler installation and native compilation
were skipped. It reused native artifact `10888733603` from the successful producer
[run 36180365572](https://github.com/dponcho/voxel-survival-game/actions/runs/36180365572);
the follow-up's native-bundle upload was skipped too.

Windows export job `108264995129` downloaded that same producer artifact and
verified its digest and bundle identity/files. It passed:

- All 12 Windows packaging/native-reuse regression tests.
- Matching-editor import, module self-tests and native split-mesher coverage.
- Debug/release scenario smoke and all four render-block/worker profile
  **cloud integration/correctness checks**.
- Streaming collision, edits, eviction and cancellation integration checks.
- Executable dependency audit and both fresh offline extraction self-tests,
  including paths with spaces/non-ASCII characters and a different working directory.
- Portable player ZIP, separate symbols and evidence publication.

`reports/candidate.json` records `native_bundle_source: cache`,
`cold_cache: false`, `status: cloud_passed_target_unverified` and
`target_performance: not_run`. Both extraction reports have `passed: true`,
no errors and the expected build/native identities.

The producer also passed its static, native qualification and separate export
jobs. Its source commit was `f7a02589601a9339c9bdf54c135f9e3d949c99f3`, exported
as `4aeb6029b602328c439815c99864cc93c167c5c9`. The latest candidate above adds
actual window-size reporting without changing native inputs. It includes the
recent N3 rotation, fixture-fall detection, comparison-launch failure reporting,
fixed 720p window and stronger mesher checks. The current cloud results supersede
their previously pending validation status. See the [CI architecture evidence](CI_ARCHITECTURE.md#acceptance-evidence)
for the exact bundle, reuse proof and remaining fallback-path limitation.

## September 25 target evidence and remaining scope

Hosted Windows rendered smoke was **not run**. The user supplied one standalone
baseline and a complete four-profile comparison from the actual i7-7600U / HD 620.
All five report identities and executable/PCK hashes match the September 25 candidate;
1,682,025 CSV rows were independently checked against their summaries. See the
[target review](M1_TARGET_REVIEW.md) and [machine-readable results](evidence/m1-target-2026-09-25-review.json).
Frame-rate capacity, memory and recorded collision/readiness results are promising,
but lifetime native timing contaminates scenario outcomes, diagnostic overhead is
inconclusive and frame-pacing/other required observations remain unresolved.
No profile is qualified and M2 remains gated.

The experiment uses stock blocky meshing with bounded split uploads, not greedy
meshing. Every comparison uses the finite fixture slab Y [-16,32), visual radius
96 m and data radius 128 m. Edits use a bounded temporary session overlay; actor,
weather and storage workloads are proxies. There is no durable save format or
complete-world vertical qualification. That report review did not change runtime
inputs. The user's [2026-09-26 Java core requirements](JAVA_CORE_REFERENCE.md)
apply to future implementation and do not retroactively change the reviewed candidate.

The attribution correction above addresses one part of the target review.
The schema 3 overhead correction above now has cloud evidence; exact-build target overhead remains unverified.
Do not request another four-profile run or the final three
qualification repeats until the corrected evidence path is ready. The
[laptop guide](M1_TESTING.md) remains the procedure for the next exact-build
candidate. A startup-check pass alone does not qualify M1.

## Earlier candidate history

[Run 34036830778](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778)
and Windows job `101496360796` passed the earlier native build, integration and
portable-package checks on September 6. Source commit:
`fe5cadc2876fc5a889c72b097373f544f4ed9fff`; exported synthetic merge:
`4e6c761c26950111ffd6af1bd496c81a6c9ed04b`; legacy native identity:
`f90df9f55adb77e131cd1f575a50caded0e8fbd17f5b0f96877e7884320197b1`.

Its [player artifact 9992504297](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992504297)
had outer archive SHA-256
`005138342e079611dee69bf1ae0c88a0eb245685e49b4d85aacb950577b86504`
and recorded expiry 2026-10-06; availability was not rechecked in this continuation.
Its [evidence artifact 9992510088](https://github.com/dponcho/voxel-survival-game/actions/runs/34036830778/artifacts/9992510088)
and the earlier failed run `34003770515` / corrective run `34007283054` remain
historical provenance. Use the corrected candidate above for subsequent
instrumentation checks; review remaining measurement gaps before qualification repeats.
