# Bounded frontier edit handover

Scope: one accepted border edit during the second 16³ +X preparation/base
handover. This public cloud correctness replay does not run the full route,
estimate diagnostic overhead or qualify HD 620. M1 remains blocked.

The horizontal poses are the float32 results of the existing 6.5 m/s, 60 Hz
route at ticks 203 and 204: `31.9917182922363` and `32.1000518798828`.
Z stays 10, camera Y is the settled route clearance `1.65100002288818`, yaw
`-1.57079637050629`, pitch -0.18, far clip/fog 96 m. The existing fixture,
geometry, 96/128 m viewers, four radius-one preparation viewers, native workers,
queues, admission limits and simulation/gameplay requirements are unchanged.
This isolated replay creates those poses; it is not a simulation completion
claim. No save/generator format changes.

Predeclared controls, in order for each of one and two workers:

- Stationary: prepare column 8, accept voxel `(128,6,10)` -> content ID 2,
  dispatch its replacement and keep the camera/base pose before the boundary.
  Both render targets `(7,0,0)` and `(8,0,0)` must acknowledge current revisions.
- Handover: the same single edit and dispatch, then cross to tick-204 pose.
  Hold column 8 for the first process opportunity before retargeting column 9.
  Keep submitted coverage and check the original accepted edit independently
  of any new viewer scheduling. A non-edit supersession is a correctness failure.
- Cancellation before base acquisition, and cancellation during actual
  overlapping ownership: cross with that dispatched edit pending, release all
  viewers and terrain, then completely drain native work and renderer retirement
  before changing worker count. Deferred deletion may let a current submission
  finish first. Otherwise the existing `finish_edit_trace` protocol cancels an
  abandoned pending edit after drain. Record the pre-close counters, exact close
  bracket and terminal source; collection cancellation is not acknowledgement.

The concurrency prerequisite is one pending accepted edit and zero queued
terrain mesh updates after a real process opportunity. No sleep, extra edit,
queue manipulation or acknowledgement deadline extension manufactures it.
The unchanged 200,000 µs edit guard applies. Preparation, edit/transfer and
retirement each close their native phase; saved operation rows retain the
unchanged 750 µs upload/deletion guard separately from correctness. A timing
failure remains a failure even when mesh/reference correctness succeeds.

Bounds: eight cases, 102 saved observations within 160; one edit/two affected
revisions per case; four preparation viewers; existing resident/retirement caps;
20,000 streamed operation rows / 8 MiB; summary 1 MiB. Missing inputs retain
unavailable/null status. Report I/O, incomplete/reordered evidence, stalled
work, missing revisions, lost references, supersession and failed guards must
remain visible. Existing first-boundary and all measurement controls remain.

The supplementary native observer accepts 1..16 distinct `Vector3i` coordinates,
only on the main thread with a live terrain. The replay requests ten: both edit
targets, all old/new preparation cells, and an already submitted empty cell.
It copies viewer counts, desired/submitted revisions and decimal mesh object
identities. No Mesh reference survives the call, no arrays/GPU buffers are read,
and ordinary benchmark/gameplay callbacks do not call it. The last submitted
revision is recorded only after actual visual replacement, including confirmed
empty. Its extra per-block 64-bit field is bounded by the existing resident
limit (4 KiB for 512 blocks); shared instrumentation overhead is still unmeasured.
Null terrain, empty/oversized/malformed/duplicate requests and an absent block
exercise unavailable/null semantics. Missing blocks and revisions cannot pass;
confirmed-empty submissions intentionally have no mesh resource identity.

Final acceptance checks require the original accepted edit revisions to remain
unchanged through transfer, all four old submitted resources to remain owned,
actual viewer references `1 -> 2 -> 1`, unedited resource identities to remain
stable, both current edit targets to acknowledge, and the next preparation column
to submit. Explicit cancellation controls retain pending/current revisions,
outcome source and complete drain without mislabelling collection close as mesh
submission. Preparation/edit-transfer/retirement rows independently reconcile
all sums, maxima, first-tie identities, frame peaks, terminal rows and phase
boundaries. Failed 750 µs guards remain visible. The three new Python regressions
also reject missing/reordered/stalled/failed work, lost references, superseded
or stale revisions, unavailable zeros, I/O loss and hidden operation failures.

## Demonstrated cause before correction

[CI 37818620545](https://github.com/dponcho/voxel-survival-game/actions/runs/37818620545),
implementation `d9bf55f9426b0159ed74073c5ee6c2ace0433907`, exported build
`418ff629f46a26e7a16517eb32f6c4c1f18c2fed`, used the unchanged previous native key.
Static and native jobs passed; the export/integration job remains a recorded
failure and produced no approved player artifact. Downloaded
[evidence 11568886138](https://github.com/dponcho/voxel-survival-game/actions/runs/37818620545/artifacts/11568886138)
is 15,044,478 bytes, SHA-256
`c72dbc77ab4d8eacbd7d4966e74872d6d6ce720ed055d70c13139cd880da62fd`.
Independent ZIP/digest/CRC and saved-report review reconciles all six editor
cases, 92 observations and 18 phases/2,826 operation rows (866,388 bytes;
raw SHA-256 `aa88210ca3ea67694b1b48e3a8aafcec4dcf23001bae974ca0d8f5de7dd25b07`).
Both stationary edits submit; both handovers and both cancellation requests
supersede the sole accepted edit despite no second edit and intact old coverage.
All concurrency prerequisites hold; no native operation guard fails in this
characterization. The new fixture also had a queue-snapshot ordering mistake
(snapshot before event pop), retained in its failed report and corrected.
Release characterization did not run after the editor failure.

Pinned upstream `view_mesh_block` always schedules, even for a second visual
owner of an already loaded block. The existing project scheduler then advances
its desired revision, supersedes the pending edit and rejects its old result.
The narrow correction skips this redundant scheduling only for a visual-only
addition with an already loaded block and more than one visual owner. Initial
loads, actual `post_edit` scheduling and other viewer/collision combinations
keep their existing paths; confirmed-empty blocks remain valid without geometry.
No edit acknowledgement or operation guard changes. Pinned patch matches and
Godot main-thread/object-ID APIs were checked without a local engine/compiler.

## Build and reader corrections

[CI 37821509437](https://github.com/dponcho/voxel-survival-game/actions/runs/37821509437),
implementation `d235c06d99f891c5e646ca14662c776d1f3413be`, built the matching
editor/debug/release templates from source and passed native qualification.
Its new native key is
`25581a8d31f5a500c585135069db3a143ac7edc69d984601768910f10ce53348`.
The export job stopped at two Python fixture errors: Windows text-mode newline
conversion changed the recorded operation byte count. The fixture now writes
exact UTF-8/LF bytes. The saved reader also accepts Godot's sorted Dictionary
keys, checks the maximum operation's complete span inside its frame, and verifies
the single submitted edit's exact latency histogram bucket. Drain sampling
retains both transient retirement counts and the native high-water counter.
None changes a timing threshold or native workload.

[CI 37838495804](https://github.com/dponcho/voxel-survival-game/actions/runs/37838495804),
implementation `e419ea1d6b275f09f7cd476c664eaf84443058e8`, passed static/native
and Windows Python checks. Integration stopped after the real editor CPU probe:
its existing reader hardcoded the previous native key. Both CPU/frame readers now
use the exact externally supplied export identity, retain pinned engine/module
revisions, and reject stale or malformed identities. Historical reads without an
export identity retain the previous exact key. All old control expectations and
qualification flags remain. Neither failed run is an approved player candidate.

## Verified cloud result

[CI 37838887842](https://github.com/dponcho/voxel-survival-game/actions/runs/37838887842)
completed successfully `2026-10-08T20:38:07Z`, implementation
`df57421ee9814fb367f603f64a545f385f852fe3`. All three jobs passed: 76 Python
regressions, five native sanitizer suites, matching editor/debug/release checks,
both actual replays, all previous controls/runtime/profile/smoke checks, DLL audit
and two fresh offline extractions. The new binaries were built from source in
37821509437 and reused only after exact manifest/file checks and fresh native
qualification. No engine was installed, compiled or run locally.

Independent downloaded reconciliation verifies sixteen cases, 204 stage rows,
2,200 native block observations, and all 48 phases/7,446 operation rows. Both
worker counts and both executables retain current accepted revisions, the actual
old-column `1 -> 2 -> 1` viewer references, unedited resource identities and
submitted next-column meshes. Stationary/handover cases acknowledge both current
targets. Cancellation before acquisition cancels at explicit collection close
after native/node drain (41,060..47,968 µs); in all overlap cases a current native
submission wins deferred deletion. Those are different recorded outcomes, not
interchangeable acknowledgements. All twelve submissions take 13,569..13,893 µs.

All 48 replay operation guards pass without changing 750 µs: maximum upload/
deletion is 175/514 µs in editor and 116/488 µs in release. Resident mesh/data
peaks remain 511/867, retirement high-water 287, overloads zero; complete drain
is verified. Per-executable summaries are 457,491/457,396 bytes under 1 MiB;
operation files are 1,142,457/1,142,345 bytes under 8 MiB. Every final phase row,
exact sum/maximum/tie identity, clock bracket, latency bucket and null control
reconciles; no terminal evidence is trimmed.

All earlier control expectations reconcile, including 16 method/26 route,
28 endpoint/168,596 rows, 44 fixed-work/176 phases/264,852 rows, 54 CPU/
216 phases/327,444 rows and 30 frame/120 phases/3,856 rows. Real CPU/frame probes
retain 256/512 callbacks and 16 closing anchors. The earlier first-boundary
replay retains eight cases/160 observations. Ten ordinary folders/98 scenarios/
284 phases reconcile with 37,351 operation rows, 12,873 frame rows and 94 edits.
All 42 heavy scenario work-unit records and available route/actor/edit/storage
contracts match the previous candidate; ordinary CPU/frame doses stay `not_run`.
Both 16³ one-second H1/H2 smokes retain zero exposed samples. H2 still fails the
existing edit-latency and diagnostic-cost guards; shortened calibration stays
inconclusive. The ordinary 32³/two-worker `AB-off-2` retirement retains an
841 µs deletion, exceeding 750 µs. Hosted OpenGL readback is unavailable. No full-route, HD 620 or
instrumentation-overhead qualification follows.

[Windows player 11577910752](https://github.com/dponcho/voxel-survival-game/actions/runs/37838887842/artifacts/11577910752)
expires `2026-11-07T20:37:34Z`. Exact exported merge/build:
`f0131627e5928c36fe310d27790605562cc895a1`; implementation/build tree:
`648547042d45c1359e5e0ecef863048515e2da29`. Portable ZIP SHA-256:
`29aab174e747eced9fc1b9ea800f08f2a1a4d6b9d050f255c4a24883444062a1`;
30,104,208 bytes. Downloaded archive sizes/digests/CRCs, PE imports, all 72 PCK
entry MD5s/build identities, native manifests/templates and eight self-tests
independently verify. Read
[the exact public record](evidence/m1-frontier-edit-cloud-2026-10-08.json).

M1 stays blocked, no target profile is qualified, and the recorded target H2
upload failure remains separate. Next: bounded continuous travel across several
preparation columns with the production H2 actor/edit/storage schedule. The
isolated single-edit replay does not establish that interaction or full-route
coverage. **No new target-side action is needed now.**
