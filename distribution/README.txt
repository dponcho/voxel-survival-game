CAIRN - Milestone 1 engine experiment

Extract this ZIP completely, then open Cairn.exe. No installation, account,
network connection, editor, compiler or runtime download is required.
Supported platform: Windows 10/11 x86-64 with an OpenGL 3.3 capable driver.

Run startup check first, then Explore the terrain fixture (WASD and mouse;
Escape ends exploration). No survival gameplay or durable worlds exist yet.

For a requested focused diagnostic pilot, use AC power and keep the game visible.
Choose Run focused shipping diagnostic pilot (about 12-18 minutes plus loading).
It fixes 32-cube render blocks / one worker, performs one null and one known-positive
control quartet and stops if sensitivity is inconclusive. A shipping comparison
is appended only with usable controls. No full profile matrix is requested by
default. The game runs the complete route/workloads without user input.

For the targeted heavy-probe comparison, select Compare heavy-route probe cost
(about 7 minutes plus loading) with the baseline setting. It switches only the
coverage probe; shared instrumentation and safety remain. This is a bounded
cost experiment, not full performance qualification.

Use Open reports folder after the check. Share summary.json, summary.txt and
the complete report folder for review. The focused pilot includes shipping-pilot.json,
per-trial boundary/complete reports, physics/frame/edit evidence and finalization.
Legacy profile comparisons create four sibling report folders. Keep failed and
cancelled results too. Cancel saves a partial report.
Startup success or completed scenarios do not certify HD 620 performance.

The data pack Cairn.pck must remain next to Cairn.exe.
Diagnostics use the per-user Cairn application-data directory.
Portable save-data mode belongs to a later milestone.

BUILD_INFO.json identifies this exact source and engine build.
LICENSES contains Godot, Voxel Tools and bundled static-runtime notices.
No personal data or diagnostics are uploaded automatically.
