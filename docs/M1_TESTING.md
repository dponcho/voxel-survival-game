# M1 laptop verification

M1 is an engine experiment: visible voxel terrain, movement, temporary edits and
automatic performance measurements. It does not include survival gameplay or saved
worlds. A startup-check pass alone does not qualify M1.

The September 25 candidate's standalone baseline and four-setting comparison have
now been received and [reviewed](M1_TARGET_REVIEW.md). M1 is not yet qualified.
The October 3 finite-fog 32³/one-worker baseline has also been reviewed. Keep those
reports; no new full baseline is requested solely for the shader-model reporting
update. Follow [NEXT_TASK.md](NEXT_TASK.md) before another comparison or final
qualification repeat. The procedures below remain available when a targeted run
is requested; completion still does not qualify M1.

## Get the candidate

Use the M1 Windows artifact linked in [M1_EVIDENCE.md](M1_EVIDENCE.md) once its
cloud checks have passed. Do not use the earlier M0 executable for these tests.
Download `Cairn-windows-x86_64-<commit>`, extract the download, then extract the
contained `Cairn-windows-x86_64.zip` into a new folder. Keep every extracted file
together, including `Cairn.exe`, `Cairn.pck`, `BUILD_INFO.json` and `LICENSES`.

You do not need Godot, a compiler, a test utility, an account in the game or an
Internet connection to run the extracted candidate.

## First check: a few minutes

1. Open `Cairn.exe`. Confirm that the title says Milestone 1 and note its build ID.
2. Select **Check native modules**. It should report that the native modules are ready.
3. Leave the setting at **32³ render blocks • 1 worker (baseline)** and select
   **Explore the terrain fixture**. After preparation, terrain should be visible.
4. Move with **W, A, S, D** and look with the **mouse**. Check that the ground holds
   you, nearby terrain remains visible, and movement responds normally.
5. Press **Escape** to release the mouse and save a partial report. Use
   **Return to title**. A cancelled exploration is expected and is not a failed
   performance qualification.

If the game crashes, stays blank, falls through loaded ground or cannot finish
preparation, stop here and report the build ID, what happened and any saved report.
Do not spend an hour running comparisons on a visibly broken candidate.

## Short startup reproduction: about 20 seconds plus preparation

The current candidate adds **Run startup timing check (~20 s + loading)** for
investigating the early warm-up hitch. Keep the baseline profile selected. Each
launch starts a fresh game process and runs only shortened warm-up and N1 routes.
The original full baseline and comparison are separate menu choices.

When a targeted reproduction is requested, run the short check twice in succession
and keep both complete report folders, even if the second seems smoother. Note
any interruption or demanding background application you noticed; no task-list
capture or system change is required. The game does not inspect other processes.
Use **Open reports folder** to collect `summary.json`, finalization timing and all
CSV files. No full matrix is requested solely for startup attribution.

These short runs provide timing evidence, not performance qualification. A clean
repeat cannot identify the cause of the historical hitch. See
[startup timing semantics and limits](M1_STARTUP_ATTRIBUTION.md).

## Targeted heavy cost check: about 7 minutes plus preparation

Select **32³ render blocks • 1 worker (baseline)**, then **Compare heavy-route
probe cost (~7 min + loading)**. Keep the foreground game visible on AC power.
The game runs the warm-up and matched H1/H2 off/on/on/off quartets automatically.
Use **Open reports folder** and retain the entire folder, including finalization,
frame/operation CSVs and edit events. Keep failed/inconclusive results too.
This bounded check does not certify M1 or require another full matrix.
Read the [measurement scope](M1_HEAVY_DIAGNOSTIC_AB.md).

## Automatic baseline: about 24 minutes plus preparation

Plug the target laptop into AC power. Use your normal Windows power setting and
close other demanding applications. Keep the game visible and in the foreground;
avoid resizing, minimizing or switching applications during the measured run.
The check fixes the game view at 1280 × 720 and uses the specified viewing distance.

Select the baseline setting and **Run performance check (~24 min)**. The game moves
and runs every workload automatically. No input is needed. It runs warm-up,
settlement/cave/dense terrain proxies, sprinting, turns, rain, border edits,
temporary storage writes, recovery, a paced pass, and a diagnostic overhead A/B
comparison. Preparation screens between fixtures are timed separately.

The text displays the current phase. **Cancel check and save partial report** ends
the run safely if needed. Keep a cancelled or failed report; do not treat it as a
pass or discard an inconvenient slow result.

When it finishes, select **Open reports folder**. Send the entire report folder
as a ZIP, including `summary.json`, `summary.txt`, `report-finalization.json` and
all preparation, measurement and retirement CSV files. The report
contains hardware/build information and measurements; it does not upload anything
automatically. Also mention whether the picture and controls looked normal and
whether another application interrupted the run.

## Compare settings: about 96 minutes plus preparation

Once the baseline launches and completes correctly, select **Compare all four
settings (~96 min)**. This automatically runs 32³/one worker, 16³/one worker,
32³/two workers and 16³/two workers. A new game process starts between settings.
The window may briefly close and reopen. Resolution, fixtures and viewing
distance stay the same.

At the end, **Open reports folder** opens the last result. Move up one folder in
File Explorer to collect the four folders from this comparison. Send all four,
including failed/inconclusive results. You may run a single setting instead using
the title-screen selector, but that alone does not complete the comparison.

## What establishes completion

Codex must review the exact-build reports against the full frame, memory,
streaming and correctness gates in the specification. A message saying that all
scenarios ran means the check finished; it does not mean every gate passed.
Cloud tests cannot reproduce the Intel HD 620 laptop's graphics, power or thermal
behaviour. Unavailable metrics and unreviewed deadline misses remain unverified.

After selecting a qualified setting, the specification calls for three complete
qualification runs, including a fresh launch and a run after sustained use. Review
the first comparison before spending time on these repeats: an engine defect or
failed budget may require a new candidate first. No manual source changes,
development installations or build commands are required from you.
