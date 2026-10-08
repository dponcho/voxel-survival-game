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

Final cloud results and independently reconciled candidate identity will be
added after execution. No new target-side action is needed now.
