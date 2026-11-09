# Saved preparation-prefix review

October 26, 2026. **Review complete. Next: correct the empty-ArrayMesh release
lifetime inside the existing deletion timer, with real destruction controls.**
No new process is declared. The consumed three-trial result remains failed;
the measured 819 µs surface-removal overrun is unchanged.

## Verified evidence

The [derived review](evidence/m1-preparation-failed-prefix-review-2026-10-26.json)
binds the [original process record](evidence/m1-preparation-demand-cloud-2026-10-25.json),
SHA-256 `adf7012ca93db9a235f58e6b1346e5d15e79fa61b5cbc3de6aec4bb5340a2a08`.
The original 8,164,605-byte archive, all 65 transferred files, both explicitly
recovered workflow snapshots and the complete 66-entry audit manifest verify.
The exact frozen portable ZIP, executable, PCK, native key and inventory verify;
the four prior controls and original preflight review reproduce. The original
sequence audit and eight semantic corruption rejections reproduce, and the
retained Windows/Linux/local replay reports agree. No measured file is changed.

This review ran **zero engines**. Native key `777879f5`, exported game
`73fad4ab0ed4da9d66fb071c7be15596a9f0e705`, declaration `17cf4e05` and permanent
assignment commit `8ab1624e0a74f153b6189afa837fb24f6688d8c9` remain unchanged.
Both preparation requests and all three older consumed pilot inputs stay false.
Original CI `40259410841` remains failed on its first Linux transfer replay;
successful saved-only CI `40389612694` does not rewrite that history.

Warmup-0 and bare-0 are complete and valid. Bare-1 is complete but invalid:
only its operation check fails. Each retains 4,320 ticks, 103,680 actor ticks,
288 accepted/submitted edits and 72 saves. All three observer sessions and
recorders are destroyed, all prefix publications reconcile, and 144,055 raw
spans remain. These observer lifetime witnesses do not prove terrain mesh
destruction was wholly inside its operation timer.

## The measured failure

| Observation | Retained value |
| --- | --- |
| Trial / phase | `AB-H2-preparation-bare-1` / retirement |
| Operation | Kind 2: surface-removal path |
| Monotonic bracket | 233,134,609–233,135,428 µs |
| Elapsed / individual limit | **819 / 750 µs**, excess 69 µs |
| Associated payload | 112,280 accounted bytes |
| Retirement aggregate | 871 operations, 73,913,840 accounted bytes, 6,824 µs |
| Event-specific thread CPU / OS / driver cause | Unavailable |

`OperationTotals::record()` updates elapsed maximum, payload, start and kind
together, retaining the first tie. The payload therefore belongs to this
slowest recorded deletion; it is not an unrelated largest-payload statistic.
It is the project's vertex/index payload accounting, not measured driver or
allocator memory.

The clock starts before the local reference conversion, surface queries and
payload calculation. It ends after `ArrayMesh::surface_remove()` returns.
Thus 819 µs measures that whole synchronous path; it does not isolate only the
RenderingServer call. Pinned Godot source also shows cache clearing, AABB
recomputation and notifications inside `surface_remove()`.

Raw per-operation tracing is disabled in this declared mode. No captured main
span overlaps this particular event, and the four direct preparation scopes
admit only section 0, whereas the failure is in the lifecycle tail. Their CPU
cycles cannot explain or replace this wall-time observation. There is no
evidence to call it OS noise, a GPU stall, a payload-size bottleneck or an
observer-caused overrun. The 750 µs guard remains failed.

## What the direct preparation owners establish

All three preparations record the same native work: 5,104 generated blocks,
392 meshed blocks, 659 uploads and 73,972,640 upload bytes, with no stale result
or overload. Callback/native-frame populations differ: 777 / 824 / 778. Equal
work counters do not prove equal engine scheduling or observer-free demand.

The following is an exact partition of the safe inner preparation window on
the **main thread**. Consecutive raw endpoints directly define the gaps;
nested children are already inside their root. Each row's root union plus gaps
equals its inner demand. Shared-boundary uncertainty and the prepared snapshot
remain outside this inner window. No process-minus-thread arithmetic is used.

| Trial | Inner main demand, cycles | Captured root union, cycles | Uncaptured gaps, cycles |
| --- | ---: | ---: | ---: |
| warmup-0 | 2,465,694,982 | 236,106,468 | 2,229,588,514 |
| bare-0 | 2,579,764,228 | 222,681,834 | 2,357,082,394 |
| bare-1, invalid trial | 2,425,919,186 | 207,262,530 | 2,218,656,656 |

The newly captured main owners do not account for most main preparation demand.
The remaining gaps have no specific engine/renderer/allocator owner in these
records. Native generator/mesher and main engine/terrain scopes remain useful
direct observations within their declared scope:

| Trial | Generation full cycles, terrain worker | Meshing full cycles, terrain worker | VoxelEngine full cycles, main | VoxelTerrain full cycles, main |
| --- | ---: | ---: | ---: | ---: |
| warmup-0 | 633,602,074 | 792,080,608 | 148,240,828 | 52,629,982 |
| bare-0 | 540,715,192 | 756,163,388 | 135,760,860 | 50,556,704 |
| bare-1, invalid trial | 538,942,850 | 747,032,512 | 129,087,600 | 47,380,494 |

These are inclusive raw cycle observations. Main and worker columns are not
added to the process total or subtracted from it. All generation/meshing calls
complete, with no overload or section crossing. Main engine/terrain call counts
are respectively 776/777, 823/822 and 777/776; no per-callback normalization is
applied. The failed trial's retained observations do not make it a valid control.

Only **one valid bare trial** exists. Warm-up is not a substitute for missing
bare trials, and the invalid bare-1 cannot fill the quartet. No comparative null,
causal preparation-cost verdict, shipping-cost estimate or below-1% result can
be derived from this prefix.

## Separate source finding: last mesh owner outlives its deletion timer

The exact candidate's `m1-admission.json` replaces `terrain/free_mesh_task.h`
with a `FreeMeshTask::run()` that has this order:

```cpp
Ref<ArrayMesh> array = _mesh;
// Surface queries/removal, or:
// } else { _mesh.unref(); }
cairn::record_deletion(bytes, start, surface);
// The local array Ref is destroyed when run() leaves its scope.
```

On the empty **ArrayMesh** path, `array` is an additional owning reference.
Dropping `_mesh` cannot destroy the object while `array` still owns it. If there
is no external owner, final destruction occurs when that local reference dies,
**after** `record_deletion()` has ended and charged the operation. With an
external owner, the local reference release still occurs later; destruction
must not be falsely claimed. Non-ArrayMesh conversion follows a different path.

The [pinned source witness](evidence/m1-retirement-call-source-2026-10-26.json)
retains exact commits, full-file hashes, Git blob identities and relevant lines:

- Godot `Ref<T>` copy/conversion takes a reference; `~Ref()` calls `unref()`,
  which deletes the object only when the last reference is released.
- `ArrayMesh::~ArrayMesh()` invokes `RenderingServer::free_rid()` for its mesh.
- The patched completed-task `record_data_apply()` bracket covers the general
  pool's completed tasks. The time-spread runner that executes `FreeMeshTask`
  is a subsequent call, so that parent bracket does not close this gap.

The whole-trial process boundaries still include the synchronous work. What is
incomplete is the individual deletion/terrain charge, not the retained complete
process interval. A time-spread scheduler budget does not establish a passing
individual 750 µs destruction measurement. Renderer-deferred work remains
unverified independently.

This is a **source-level lifetime defect**, not an executed engine destruction
fixture. It concerns the kind-3 empty/reference-release path. The measured
819 µs failure is kind 2, so this finding neither explains it nor rescues it.
The old artifact and all historical measurements retain their original verdicts.

## Finite decision and next acceptance checks

**Correct this lifetime/accounting gap before another attribution declaration.**
This is smaller and better supported than a speculative mesh split, payload
reduction, new owner expansion or another route run. The correction alone does
not establish that the distinct 819 µs surface-removal overrun is solved.

1. Ensure all operation-local/task-owned references are released inside the
   existing monotonic deletion bracket. An inner lexical scope or a safe
   non-owning access may implement this; prove the chosen lifetime. Preserve
   external shared ownership and the one-surface/postponement behavior.
2. Exercise the actual production path with bounded native/engine controls:
   empty and surfaced ArrayMesh, retained external owner, applicable
   non-ArrayMesh/null handling, postponement and real last-owner destruction.
   Freeze a rejected-lifetime control that shows destruction after the old
   endpoint; the corrected control must place destruction before the measured
   endpoint. Report honest unavailable/failed evidence and reject forged order,
   destruction, charge, kind and ownership claims in the saved reader.
3. Keep the 750 µs individual limit, 1/2 ms native-frame budgets, nested union
   charging, phase carry, resource caps, complete lifecycle and all original
   work/edit/readiness/coverage gates. Count the synchronous destructor work
   once. Do not turn renderer-deferred work into a measured zero or move it
   outside the declared trial.
4. Produce new matching editor/debug/release binaries and a portable candidate,
   retaining required correctness/package checks and downloaded Windows/Linux
   audits. Use only finite capability controls in that increment; do not rerun
   any consumed pilot, create an attribution declaration or ask for a laptop run.
   Preserve method/inventory/codecs and every old failed artifact.

M1 remains blocked. A later process would need a separate review and prospective
decision after this prerequisite; this review creates neither a retry nor an
automatic continuation. Use **GPT-6.1 Sol Max** for the bounded correction.

## Reproduction and checks

In Codex Cloud, with the original raw artifact ZIP and the frozen inner player
ZIP already downloaded:

```bash
python tools/qa/preparation_failed_prefix_review.py \
  --artifact /path/to/preparation-result-40259410841.zip \
  --candidate /path/to/Cairn-windows-x86_64.zip \
  --check docs/evidence/m1-preparation-failed-prefix-review-2026-10-26.json
python -m unittest discover -s tests/integration -p 'test_preparation*.py' -v
```

All **75 affected Python regressions pass**, including eight new archive,
ownership, exact-union, crossing, failed-event and source-binding cases.
Compile checks and whitespace checks pass. The saved review verifies all
66 audit entries and reproduces the original audit/eight corruption rejections.
No engine/native suite, candidate build, export or laptop test ran in this
review-only increment. Save/generator compatibility and runtime bytes are unchanged.
