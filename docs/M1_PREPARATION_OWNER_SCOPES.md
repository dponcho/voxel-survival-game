# M1 direct preparation owner scopes

October 25, 2026. Implementation, controls and matching candidate verified in
[CI 40216786118](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118);
**no attribution route or laptop run**. M1, diagnostic cost and target performance remain unqualified.
The [adopted design](M1_PREPARATION_DEMAND_DECISION.md#narrow-owner-extension-after-lifetime-capability-passes)
is implemented as `m1-preparation-demand-attribution-1`, inventory
`m1-preparation-demand-inventory-1`, raw version 2 / `CAIRNOB2`.

## Scope and raw contract

| Slot | Real entry | Deliberate limit |
| --- | --- | --- |
| 13 | `CairnFixture::generate_block()` | Whole function, including overlay/compression and return; excludes task scheduling and other worker work. |
| 14 | `CairnMesher::build()` | Whole face guard, stock mesher and bounded split, including every overload return. |
| 15 | `VoxelEngine::process()` | Completion/application/destruction, time-spread/progressive work and viewer synchronization, including the existing frame marker. |
| 16 | `VoxelTerrain::process()` | Quick reload, viewer processing and meshing submission. |

The 40-byte header and 192-byte little-endian record layout remain bounded by
32 MiB wire bytes, eight lanes and depth eight. Old version 1 encoding and its
slots 1–12 remain unchanged; its reader rejects version 2. Only version 2 admits
slots 13–16. Each new native record uses `units=1` for the attempt and the old
`bytes` field as an explicitly versioned **outcome tag**, not bytes: 1 normal,
2 meshing overload. `complete=1` witnesses actual RAII completion. Attempt,
completion, overload and crossing populations are independently reconciled.

All four raw current-thread reads retain unsigned cycles, wall brackets,
availability, success and OS error. Counter/owner/context/cap failure stops new
version 2 admission and retains its prefix; admitted scopes still return.
No sampling, zero replacement, cycle/time conversion or fitted correction.

Main owners use the original main stack and shared boundary OS TID. Inclusive
full, body, bookkeeping and exclusive body remain distinct; nested unions are
charged once. A main section crossing fails. Only preparation (section 0)
admits new native scopes. An admitted worker completes after handover on its
actual executing thread; its original begin/end/submission context and outcome
remain. Crossing demand is separate, without clipping or wall-time splitting.

## Pool and lifetime

The pinned pool's real thread entry installs a unique monotonically assigned
incarnation token and thread-local pool/index/count identity. Registration binds
that token, the actual executing OS TID and a bounded lane on its first admitted
call. A replacement requires real retirement of the previous incarnation.
Unexpected pool/index/count, reused live identity and mismatched completion fail.
The existing pool retains one terrain worker; no pool or worker is added.

A single publication mutex safely acquires bounded strong session references
and closes acquisition/unpublish races. Each scope releases its reference on
return. Disabled function entries perform the atomic dispatch check and no new
counter read, trace lock, allocation, I/O or worker scheduling. Pool bootstrap
only assigns its thread-local identity and monotonic incarnation; it does not
read CPU/wall counters, allocate or acquire the trace lock when disabled.

The distinct opt-in mode orders start observation before allocation, reservation
and publication. It preserves the existing work, operation, resource, readiness,
coverage, edit and writer guards. Normal and failed closure stop submissions,
drain admitted work, join/detach writers, unpublish, copy immutable counts/owners,
witness session destruction, seal/emit/flush/close, explicitly dispose the last
recorder owner, hash, then take the ending shared boundary. An abandoned native
caller unpublishes as failed; it cannot leave a hidden publisher owner.

Persistent pool threads have a drained registration detach witness, **not a pool
join**. Actual retirement is recorded separately when a worker really exits.
Record/vector capacities, the fixed session/owner table and bounded serialization
capacity are reported separately. Weak-reference expiry witnesses requested
object/vector destruction, not allocator/OS page retention. Additional reads,
shared locks and dispatch perturb scheduling; bookkeeping spans do not bound all
of that perturbation. No total engine/worker/GPU/driver or causal cost is inferred.

## Bounded verification

`--preparation-demand-check` calls the real four functions in each matching
editor/release, with an explicitly refused orphan fixture and a real in-tree terrain,
under a five-second native cap and 60-second outer timeout. Its
existing pool executes finite generation, real stock meshing/splitting and a
checkerboard face-guard early return. It exercises actual one-worker replacement,
a gated generation return across handover, nested main scopes, a persistent
worker detach and joined UTF-8 qualification/proxy writes. Separate real-entry
counter/cap/unregistered-owner/main-crossing/write faults retain failed prefixes
and reclaim their owners. Twenty-one saved metadata corruptions must be rejected.

The eleventh native sanitizer suite covers disabled dispatch, real thread entry/
exit identities, legal same-TID reuse, overlap refusal, nested union, crossing,
unsigned/raw failure, saturation/depth, foreign-thread completion, unpublish with
an admitted scope and retained lifetime. Ten new Python cases cover the independent
version 2 reader and required controls. All **213 Python regressions** and the
three affected native ASan/UBSan suites pass locally. Local LeakSanitizer is
unavailable under the executor's `/proc` restrictions; CI retains full sanitizer
settings and all eleven suites.

The initial source `fcb1f2e` is a preflight. Pinned `Node3D::get_global_transform()`
requires `is_inside_tree()`, while the first native control created an orphan
terrain. The corrected fixture supplies an in-tree node, proves its context,
rejects the orphan before publication, then removes/destroys the fixture before
closure. No log is suppressed or acceptance check removed. The initial compile
is retained as preflight evidence, not a qualified candidate. CI `39966730530`
passes compilation/qualification of all three binaries but correctly fails the
editor control on four scene-tree errors before any export or route. The
[self-contained failed preflight](evidence/m1-preparation-owner-preflight-2026-10-23.json)
retains its original report, log, nine raw files / 503,842 bytes, native manifest
and digests. Its 2,620 raw records reconcile structurally, and both owners are
destroyed, but engine-context failure invalidates attribution even though inner
API flags say passed. No error is ignored and no portable candidate is claimed.

Initial source `fcb1f2e9e81f0377aed7edd73d01abb08da7ed81`, native key
`a6ab4888dce3d003e61161ef0456763051ba70ea82b4b801c15d791dbf8f7100`,
[CI 39966730530](https://github.com/dponcho/voxel-survival-game/actions/runs/39966730530).
The cloud static gate now passes all 213 regressions and all eleven full sanitizer
suites. The [live build checkpoint](evidence/m1-preparation-owner-build-checkpoint-2026-10-23.json)
records the pending native compile without restarting it.

Required CI parses the new mode, runs both new controls, rebuilds/requalifies
all three exact-key Windows binaries, exports the portable player, retains all
existing integration/offline checks and replays the downloaded candidate and
saved controls on Windows and Linux. These cloud checks and the candidate are
now verified in the [result](#result).

The earlier fixture correction used native key
`030d60ff7c04bed7fffab28511c1d79f10a251658baf05f98c0e864ba306dd69`.
Source `108c8e136eac84e784f8a9ab2d2b33884bcc7c8e`,
[CI 39982108071](https://github.com/dponcho/voxel-survival-game/actions/runs/39982108071);
[context correction checkpoint](evidence/m1-preparation-owner-context-checkpoint-2026-10-23.json).
That superseded build passed all 213 regressions and eleven full sanitizer
suites before cancellation for the admission corrections below. The new control
also proves orphan rejection
without allocating/publishing a recorder, and rejects twenty-one saved corruptions.

## Admission lock correction

A deterministic native regression reproduces a second preflight defect: the
worker passed the optimistic preparation check, acquired its strong reference,
then waited for the session lock while main changed the section. The original
constructor admitted a section-1 record; the saved reader would reject it, but
admission itself must be correct. The constructor now rechecks section/failure
under the same lock used by handover, before any raw read, registration or
attempt. The regression controls the interleaving with the existing bounded
strong reference and asserts zero reads/attempts/records for the excluded call.
It failed before the correction and passes ASan/UBSan after it.

Native key `ae750bbdd0db95ce09ae5c5e3a423e6584d4af8bd08114254bb390a6c08d4256`
supersedes the unfinished `030d60ff` build. A one-run concurrency setting stops
that superseded native build so the corrected source can start its required
checks immediately; the normal non-cancelling setting will be restored in the
next documentation checkpoint. All pilot inputs remain false; no route is
interrupted or launched. Matching checks were pending at that superseded checkpoint.

The inactive-section regression also holds the publication mutex while another
thread attempts an owner entry. A separate atomic admission flag now makes that
call return without reads, registration, allocation or publication locking.
Handover clears admission under the session lock; admitted scopes still return
and pool retirement tracking stays enabled until unpublish. Both admission-race
variants (handover and first failure) and the locked-publication inactive case
pass ASan/UBSan. The final native key is:
`777879f5d9b2bd461e37dcac74102b5adc370381342d60250fcebed7002c360a`.
This supersedes the short-lived `ae750bbd` build before any controls/route.

Admission-corrected source `2288a01f1b2786fda96775ab5ca1ff0fcbea3954`,
[CI 39998646163](https://github.com/dponcho/voxel-survival-game/actions/runs/39998646163).
The [admission checkpoint](evidence/m1-preparation-admission-checkpoint-2026-10-23.json)
records the reproduced failure, both passing race variants, inactive-entry proof
and cancelled superseded builds. The normal `cancel-in-progress:false` setting
was restored after that replacement started. Its packaging cancellation and
completed exact-key recovery are recorded below.

## Packaging timeout recovery — October 25, 2026

CI `39998646163` completed the static gate, matching native qualification, both
real-entry controls, full integration and both offline extraction tests. Its
35-minute export job expired while compressing separate symbols, before player
publication or independent Windows/Linux candidate audits. It remains cancelled,
not a complete candidate pass. The downloaded evidence archive is 31,014,145
bytes, SHA-256
`cd2200f6ee8fda3d50bcce415297c2ec7debec763cfda4f4706ccd4f4d4cb8a3`.

The run spent 8 minutes 46 seconds downloading the qualified native bundle and
21 minutes 3 seconds in required integration. The export job's orchestration
limit is now 60 minutes, preserving every check, runtime timeout, numerical
gate and disabled pilot input. The exact native key remains `777879f5`; reuse
its qualified bundle, requalify all three binaries, and complete the required
candidate publication and downloaded audits. No new native compilation or route
is needed for this workflow-only correction.

## Result

October 25, 2026. Source `2288a01` and workflow recovery `378de8f` pass
[CI 40216786118](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118).
All 213 Python regressions on each platform, eleven native sanitizer suites,
matching editor/debug/release qualification, both real-entry controls, required
integration/package checks and downloaded Windows/Linux audits pass. The exact
qualified native bundle is reused under key
`777879f5d9b2bd461e37dcac74102b5adc370381342d60250fcebed7002c360a`;
this recovery adds no native, game, save, generator or measurement change.

| Control | Editor | Release |
| --- | ---: | ---: |
| Complete fixture, µs (limit 5,000,000) | 11,411 | 9,229 |
| Raw records / lanes | 1,680 / 4 | 1,182 / 4 |
| Generation attempts / completions | 3 / 3 | 3 / 3 |
| Meshing attempts / completions / overload returns | 4 / 4 / 2 | 4 / 4 / 2 |
| Complete worker scope crossing handover | 1 | 1 |
| Rejected saved semantic corruptions | 21 | 21 |

Both controls call the actual four entries, prove the scene-tree context and
orphan refusal, actual pool replacement and persistent-worker detach, nested
main union, joined UTF-8 writer bytes, failed raw prefixes and session/recorder
destruction. Attempt/completion counts and raw unsigned/error observations
reconcile without clipping or process/thread subtraction. Normal traces retain
the 32 MiB wire cap, eight-lane/depth limits and one terrain worker. Actual
record/vector/session capacities remain separate from allocator/OS retention.

The [self-contained proof](evidence/m1-preparation-owner-cloud-2026-10-25.json)
preserves exact compressed report/raw bytes for both this run and cancelled
CI `39998646163`, their hashes and reproduced control verdicts. The preceding
cancelled run is not converted into a CI pass. The current downloaded candidate
passes 8 identity-bound self-tests, PE dependency checks
and 112 PCK entry hashes; the Linux replay and local
read-only audit reproduce the Windows result without executing an engine.

| Published item | Exact identity |
| --- | --- |
| Exported source | `d6e14a545e31dcd62e74e263442e6849459b5d8c` (PR merge of `378de8f`) |
| [Portable candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118/artifacts/12609121247) | Inner ZIP 30,306,108 bytes; SHA-256 `3b894f209a1b9976fa2b79dfcc60878895d4219c1557eb4b8078e5622b1f48b1` |
| Release executable | SHA-256 `b3d7a391ffb60c0649d7dd4ba1a599da544be6ac89bc567bb5adcd47feec91de` |
| PCK | SHA-256 `cddd23ad15583052f1bafcaf4216b89e426d642806dadb73d006ef475448f5f9` |
| [Export evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118/artifacts/12608656180) | Exact controls, integration reports and Windows independent audit |
| [Native qualification](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118/artifacts/12607338327) | Requalified editor/debug/release; manifest and hashes retained |
| [Linux replay](https://github.com/dponcho/voxel-survival-game/actions/runs/40216786118/artifacts/12608441752) | Same downloaded candidate/evidence result; no engine |

Broader operation evidence retained: 809 µs deletion in `debug-m1-raw` / `H1` / retirement; 865 µs deletion in `release-m1-raw` / `AB-off-2` / retirement.
The existing 16³ H2 edit failures and historical diagnostic/target verdicts also
remain. These controls establish capability and integrity, not shipping cost,
causality, representative preparation demand, target speed or M1 qualification.
All three consumed pilot inputs stay false; no attribution route ran.

## Run boundary and next decision

Required CI has no preparation route input. All three consumed pilot flags stay
false. The new `--preparation-demand-pilot` entry additionally requires a separate
prospective exact-native-key/inventory declaration, one process, at most five
trials, no retry and no positive/shipping continuation. No such declaration or
route process is created by this increment. The independent reader retains the
original complete fixed-work/lifecycle checks and adds version 2 ownership and
destruction; a failed or unavailable attribution never becomes a passing zero.

With controls and matching candidate verified, the next bounded task is to review
their exact proof and prospectively decide whether to declare **at most one
process, warm-up plus four bare trials**, as already specified in the adopted
design. Preserve 32³/one worker, complete 4,320 ticks / 103,680 actor ticks /
288 edits / 72 saves, full height and radii, all deadlines/caps and numerical 1%.
That future decision is separate; no route, laptop action or M2 follows now.


## Replay saved controls without artifacts or an engine

The proof embeds exact report/raw bytes with SHA-256 and bounded zlib/base64
encoding. Replay both verified controls and the preceding cancelled run's
controls from the repository root:

```bash
python - <<'PY'
import base64, hashlib, json, sys, tempfile, zlib
from pathlib import Path
sys.path.insert(0, 'tools/qa')
import preparation_demand as q
p = json.loads(Path('docs/evidence/m1-preparation-owner-cloud-2026-10-25.json').read_text())
for group, build in ((p, p['candidate']['build']),
                     (p['preceding_cancelled_run'], p['preceding_cancelled_run']['build'])):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, item in group['files'].items():
            parts = name.split('/')
            assert len(parts) == 2 and parts[0] in ('editor', 'release')
            assert Path(parts[1]).name == parts[1] and chr(92) not in parts[1]
            data = zlib.decompress(base64.b64decode(item['base64_zlib'], validate=True))
            assert len(data) == item['bytes'] <= 33554432
            assert hashlib.sha256(data).hexdigest() == item['sha256']
            folder = root/('preparation-demand-'+parts[0])
            folder.mkdir(exist_ok=True)
            (folder/parts[1]).write_bytes(data)
        assert q.saved_controls(root, build) == group['controls']
print('All four saved controls and 84 semantic corruptions reproduce; no engine.')
PY
```
