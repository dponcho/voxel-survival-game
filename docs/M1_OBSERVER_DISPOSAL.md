# M1 explicit recorder disposal

October 19, 2026. Implements the bounded capability selected in
[the saved preparation decision](M1_PREPARATION_DEMAND_DECISION.md).
Implementation `d1bb1320f41263ba3c0abd07886ce69e4d95336e` is published;
[CI 39300074494](https://github.com/dponcho/voxel-survival-game/actions/runs/39300074494)
has passed all 203 Python regressions and ten native sanitizer suites and is
building the matching Windows binaries. Native key:
`ec74fbdda9015e0c1ae3bd75594fad2c35e8d89a91d0196ba5436b0007bc581d`.
No new Windows result is claimed at this checkpoint. M1 and optional diagnostic
cost remain unqualified. Continue this existing run rather than rebuilding merely
to resume verification.

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

Pending cloud verification and portable publication. Local focused/native checks
pass; this executor's LeakSanitizer cannot inspect its process filesystem, so its
local ASan/UBSan run disables only leak detection. CI retains full sanitizer
settings. The full pure regression suite and cloud results are recorded on
completion, along with exact source/native/artifact hashes.

A successful capability check will establish explicit recorder reclamation,
not complete observer cost, stable preparation demand, target speed or M1.
The previously specified four owner scopes remain deferred until an explicit next
implementation/probe decision. Numerical 1%, operational limits, complete
work/settings and all consumed pilot results remain unchanged. No laptop test
is requested at this stage. Continue with GPT-6.1 Sol Max.
