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
- Cancellation: cross with that dispatched edit pending, release all viewers
  and terrain, record the actual cancellation and completely drain native work
  and renderer retirement before changing worker count.

The concurrency prerequisite is one pending accepted edit and zero queued
terrain mesh updates after a real process opportunity. No sleep, extra edit,
queue manipulation or acknowledgement deadline extension manufactures it.
The unchanged 200,000 µs edit guard applies. Preparation, edit/transfer and
retirement each close their native phase; saved operation rows retain the
unchanged 750 µs upload/deletion guard separately from correctness. A timing
failure remains a failure even when mesh/reference correctness succeeds.

Bounds: six cases, 92 saved observations within 128; one edit/two affected
revisions per case; four preparation viewers; existing resident/retirement caps;
20,000 streamed operation rows / 8 MiB; summary 1 MiB. Missing inputs retain
unavailable/null status. Report I/O, incomplete/reordered evidence, stalled
work, missing revisions, lost references, supersession and failed guards must
remain visible. Existing first-boundary and all measurement controls remain.

Initial characterization uses the current native bundle before a behaviour
change. It permits recording a submitted or superseded handover event as an
observation and marks supersession `edit_evaluation: failed`; it cannot certify
the handover. Only a demonstrated failure can justify a narrow native fix.
Actual cloud results and independently reconciled candidate identity will be
added after execution. No new target-side action is needed now.
