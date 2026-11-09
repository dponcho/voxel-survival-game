# M1 explicit recorder disposal

October 19, 2026. Implements the bounded capability selected in
[the saved preparation decision](M1_PREPARATION_DEMAND_DECISION.md).
Implementation `d1bb1320f41263ba3c0abd07886ce69e4d95336e` is verified;
[CI 39300074494](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494)
passes 203 Python regressions on both platforms, ten native sanitizer suites,
matching Windows binaries, real disposal controls, required integration/package
checks and downloaded Windows/Linux audits. Native key:
`ec74fbdda9015e0c1ae3bd75594fad2c35e8d89a91d0196ba5436b0007bc581d`.
M1 and optional diagnostic cost remain unqualified. The
[self-contained proof](evidence/m1-observer-disposal-cloud-2026-10-19.json)
retains both original control reports, fourteen raw control files/checksums,
exact candidate identity and reproduced verdicts.

## Capability and boundary

`CairnProbe.observer_dispose()` is a distinct opt-in API with witness schema
`cairn-observer-disposal-1`. It refuses a foreign calling thread, absent recorder,
retained strong owner, open scope, active recorder or missing emission attempt.
Refusal does not seal, wait, clear errors, destroy storage or claim a passing zero.
The main caller must stop publishers and join/detach clients before release.
The API is not a general concurrent reference-reclamation protocol.

After existing `observer_finish()` emits/closes the trace (or retains its honest
failure), the new API copies immutable record/lane/open counts, failure code and
actual vector capacities. With one owner and no open scopes, it releases the
ledger and verifies destruction through an independent weak reference. It then
clears the retained path and emission state before its ending raw observation.
Reported storage covers the ledger object and its record/lane vector capacities;
it does not measure allocator overhead, retained heap pages or OS working set.
Failed or unavailable counters remain raw failures, distinct from destruction.

The former finish API still retains its owner. Its v1/v2 modes, raw wire codec,
inventories, readers, workloads and historical verdicts are preserved. No old
trial is retroactively repaired. A later mode must explicitly detach, finish and
dispose inside its originating final boundary, retaining the full setup, writer,
retirement, emission, file hashing, final boundary and terminal-marker lifecycle.
This increment supplies the capability and controls; it adds no terrain owner
scope or new attribution/cost route. All three pilot inputs stay false.

## Finite controls and acceptance

The hidden `--observer-disposal-check` executes once in each matching Windows
editor/release through the existing prepare/package pipeline. Each native
fixture has a five-second wall cap, two bounded UTF-8 writes (17 / 6 bytes), six
raw spans and two lanes. It retains:

- Actual main-thread/raw-process lifecycle observations around recorder setup,
  writer creation/join, trace emission, release and bounded fault cleanup.
- Rejections while active, while two main scopes are open, while a writer is
  alive, after that writer joins but remains attached, and with another foreign
  strong owner after detach. A separate short joined thread verifies calling-
  thread refusal without touching the recorder or inventing counter values.
- A final-owner destruction witness, readable original trace after destruction,
  zero accepted post-disposal spans, failed post-disposal finish and no second
  destruction witness on repeated disposal.
- Counter failure with injected poisoned output encoded as flagged null; actual
  saturation of a one-record 232-byte fixture; and actual write/open failure
  using an existing file as the parent directory. Failed codes/counts survive
  disposal. A missing write-failure trace stays unavailable, never an empty pass.

The small saturation fixture declares its actual smaller cap. Its dedicated
failure-prefix reader does not relax the old shipping reader's fixed 32 MiB cap.
The normal control trace keeps that original cap, twelve slots and eight-lane/
depth limits. No scope logging, timer, allocation or worker change is added to
ordinary terrain work. No save/generator/content compatibility changes.

The tenth pure native sanitizer suite checks ownership/lifetime, sealed-open
refusal, actual cap failure, emission prerequisite, retained bytes and failed
prefix cleanup. An injected shared-allocation rejection verifies that an absent
allocation cannot manufacture a release witness. It does not induce real OS
memory exhaustion or establish recovery from arbitrary process out-of-memory.
Eight new pure Python cases check exact unsigned observations, refusal/null
semantics, capacities, failed prefixes and preservation of the old codec. The
independent real-report audit also rejects fifteen saved semantic corruptions.

Native source changes require a new exact key and matching editor/debug/release.
All existing required native, integration, export, self-test, dependency and fresh
offline extraction checks remain. The published ZIP, PCK/native source identity,
both saved controls and their corruptions are rechecked after download on Windows
and Linux. No automatic control retry or route continuation is selected.

## Result and next gate

| Actual control | Editor | Release |
| --- | ---: | ---: |
| Complete fixture, µs (limit 5,000,000) | 3,930 | 3,163 |
| Normal spans / lanes | 6 / 2 | 6 / 2 |
| Requested ledger/vector bytes before release | 33,555,256 | 33,555,256 |
| Destruction witness / owned storage after release | true / 0 | true / 0 |
| Saved semantic corruptions rejected | 15 | 15 |

Each normal trace remains readable at 1,192 bytes after destruction. Counter and
cap failures retain their 232-byte prefixes and codes 4 / 1. The actual write
failure retains code 7 with its missing trace explicitly unavailable. Refusals
preserve state. Storage comprises 33,554,304 record-capacity bytes, 512 lane-
capacity bytes and a 440-byte object; this does not measure OS memory reclamation.

Both controls and their corruptions reproduce exactly on Windows, the downloaded
Linux audit and the local saved reader. Existing counter/method/observer controls,
required integration, eight self-tests, offline extractions, dependency checks
and 107 PCK entry hashes pass. The native build took 122 minutes 21 seconds and
is cached under the exact key. No attribution or shipping-cost route ran.
The broader suite retains a **905 µs deletion** overrun; the preceding
1,332 / 756 µs and all historical failures remain. This does not qualify complete
observer cost, stable preparation demand, target speed or M1.

| Published item | Exact identity |
| --- | --- |
| Exported source | `fe1cecec824fb6ce973ee278126d382f4a81dcf5` (PR merge of `d1bb132`) |
| [Portable candidate](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494/artifacts/12220471264) | Inner ZIP 30,260,192 bytes; SHA-256 `42ec54470844b27af1ec4d32a675a0f644ebdc13e6e8efa30c84caf0c852619e` |
| Release executable | SHA-256 `61af76f7542be3d7747052ed3f6c5e52bc2b5978bb339f2f165efee63aa53a69` |
| PCK | SHA-256 `158a6fff1978aa8b5cb82a8deb393069e992eacbc52b379d58511d736c8c29ff` |
| [Matching native bundle](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494/artifacts/12219326396) | Editor/debug/release qualified independently; all three hashes are in the proof |
| [Export evidence](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494/artifacts/12220746352) | Raw controls and Windows independent audit |
| [Linux replay](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494/artifacts/12220187625) | Identical downloaded verdicts; no engine executed |

Next implement the four already specified preparation owner scopes under distinct
method/inventory/raw version, with this disposal boundary, meaningful controls
and a matching candidate only. Any later finite route needs its own prospective
declaration. Numerical 1%, work/settings and limits remain unchanged; all three
pilot inputs stay false. No laptop test or M2 expansion. Use GPT-6.1 Sol Max.

## Replay the committed controls without artifacts or an engine

The proof embeds all fourteen tiny raw files as exact hex. From the repository root:

```bash
python - <<'PY'
import hashlib, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, 'tools/qa')
import observer_disposal as q
p = json.loads(Path('docs/evidence/m1-observer-disposal-cloud-2026-10-19.json').read_text())
with tempfile.TemporaryDirectory() as td:
    folder = Path(td)
    for name, item in p['raw_files'].items():
        assert Path(name).name == name and '\\' not in name
        data = bytes.fromhex(item['hex'])
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
        (folder/name).write_bytes(data)
    for label, report in p['control_reports'].items():
        actual = q.validate(report, folder, p['candidate']['build'])
        actual['saved_faults_rejected'] = q.mutations(report, folder, p['candidate']['build'])
        assert actual == p['controls'][label]
print('Both native controls and all saved corruptions reproduce; no engine.')
PY
```
