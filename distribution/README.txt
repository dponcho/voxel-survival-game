CAIRN - Milestone 1 engine experiment

Extract this ZIP completely, then open Cairn.exe. No installation, account,
network connection, editor, compiler or runtime download is required.
Supported platform: Windows 10/11 x86-64 with an OpenGL 3.3 capable driver.

Run startup check first, then Explore the terrain fixture (WASD and mouse;
Escape ends exploration). No survival gameplay or durable worlds exist yet.

For measurements, use AC power and keep the game visible. Leave the baseline
32-cube render blocks / one worker selected and run the automatic performance
check (about 24 minutes plus preparation). Compare all four settings takes
about 96 minutes. The game runs the workloads without user input.

For the targeted heavy-probe comparison, select Compare heavy-route probe cost
(about 7 minutes plus loading) with the baseline setting. It switches only the
coverage probe; shared instrumentation and safety remain. This is a bounded
cost experiment, not full performance qualification.

Use Open reports folder after the check. Share summary.json, summary.txt and
the frame CSV files for review. The comparison creates four sibling report
folders. Keep failed and cancelled results too. Cancel saves a partial report.
Startup success or completed scenarios do not certify HD 620 performance.

The data pack Cairn.pck must remain next to Cairn.exe.
Diagnostics use the per-user Cairn application-data directory.
Portable save-data mode belongs to a later milestone.

BUILD_INFO.json identifies this exact source and engine build.
LICENSES contains Godot, Voxel Tools and bundled static-runtime notices.
No personal data or diagnostics are uploaded automatically.
