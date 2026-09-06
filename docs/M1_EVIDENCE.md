# M1 engine experiment evidence

Status: **in_progress**. No M1 Windows candidate or target performance pass is claimed.

Candidate work is in [PR 2](https://github.com/dponcho/voxel-survival-game/pull/2).
[Run 34003770515](https://github.com/dponcho/voxel-survival-game/actions/runs/34003770515)
passed Linux sanitizer fixture checks and Linux/Windows packaging regression
tests, then failed during editor compilation: the project module lacked upstream
Voxel Tools' conditional build definitions. The module build now reads the pinned
upstream configuration so headers share its namespace and feature/class layout.
The correction passed native compilation in
[run 34007283054](https://github.com/dponcho/voxel-survival-game/actions/runs/34007283054).
Its editor, debug and release templates qualified, the game imported, and native
mesher coverage passed. The debug scenario check then exposed an upstream boundary
assertion: the first 16-voxel data chunk of a 32-voxel render region can be outside
the fixed terrain bounds. The check now anchors within the intersection of the
render region and actual data bounds; it still asserts that this data exists.
The fixture size and all specification budgets remain unchanged. The existing
debug scenario is the regression reproducer (396 assertion errors in that run).
This native correction requires a new matching source build; no M1 ZIP has passed.

This increment retains VoxelTerrain, VoxelBoxMover and the pinned stock blocky
mesher. A project mesher subclasses the stock mesher to divide output into bounded
uploads; it does not implement greedy meshing. Exact-match native patches bound
admission and defer mesh uploads/retirement, with per-request revisions rejecting
stale mesh results. The six specification documents remain unchanged.

The temporary fixtures have a finite vertical slab, Y [-16,32), shared by every
comparison. Visual/data radii remain 96/128 metres. This is an engine experiment,
not certification of the complete world's vertical extent. No world format or
durable survival save implementation is introduced.

The menu offers a baseline check, four-profile comparison and fixture exploration.
Full checks run the specified warm-up and N1/N2/H1/H2/N3/R1 proxy sequence, followed
by a paced diagnostic and paired diagnostic overhead samples. Reports distinguish raw frame misses, workload delivery,
native queues, upload timings, memory, rendering counters and unavailable metrics.
Temporary autosave proxies and frame CSV writes share one bounded disk worker.

Additional cloud integration covers actual voxel collision, edits at negative and
positive borders, unload/reload preservation of the temporary edit overlay, and
world cancellation before changing worker counts. These new checks are pending.
The [laptop testing guide](M1_TESTING.md) describes the candidate controls and the
reports needed from the user after cloud validation.

Pending: cloud compilation/integration, package audit, complete native correctness
review, rendered inspection and exact-build target reports. Do not mark M1 passed
until all applicable ROADMAP/PERFORMANCE/TESTING gates have evidence.
