# M1 laptop verification

M1 is an engine experiment: visible voxel terrain, movement, temporary edits and
automatic performance measurements. It does not include survival gameplay or saved
worlds. A startup-check pass alone does not qualify M1.

The September 25 candidate's standalone baseline and four-setting comparison have
now been received and [reviewed](M1_TARGET_REVIEW.md). M1 is not yet qualified.
Keep those reports; another full comparison or final qualification repeat should
wait for the diagnostic attribution/overhead correction and its new candidate.
The procedure below remains applicable when that candidate is ready.

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
2. Select **Run startup check**. It should report that the native modules are ready.
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
as a ZIP, including `summary.json`, `summary.txt` and the frame CSV files. The report
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
