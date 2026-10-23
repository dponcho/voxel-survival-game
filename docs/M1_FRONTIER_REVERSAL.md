# Bounded H2 camera-reversal comparison

This increment extends the experimental native FIFO/priority comparison to
1,200 fixed 60 Hz ticks (20 seconds), in matching editor/release with one/two
workers. The production H2 route continues outward at 6.5 m/s; its camera turns
around at 15 seconds / tick 900. Motion is never reversed, teleported or stalled
to substitute another workload. The fixture, 24 actors / 256 rain proxies,
80 due border edits, 20 32 KiB proxy saves, resolution, collision/safety and all
world/save semantics remain. Eight new processes supplement all completed
600-tick controls and every earlier check. Ordinary production keeps FIFO.

Native admission and the experimentally verified priority ordering are unchanged:
loaded current replacements first, then missing visuals by closed-box distance,
then remaining FIFO, with original order breaking ties. Loading/retirement keep
FIFO in both cases. Four preparation viewers, resident cap 512, 96 m required
geometry/fog, 128 m data envelope, workers/admission limits and the 100/200 ms,
750 microsecond and 1% guards retain their requirements.

The longer observation adds the four cells affected by edits at x=96/128 in a
separate bounded native call. The original fifteen-cell primary and two-cell
lateral calls remain; no call exceeds the established sixteen-cell API limit.
All eight outbound handovers, exact float32 route/camera/checkpoints/command hash,
current accepted/submitted revisions and actual resource identities are verified.
Eviction after a region leaves 96 m is recorded with its last ready identity and
native missing/hidden state. Missing fields remain null. The observer never keeps
a native resource alive. Loss inside required geometry, changed commands,
unacknowledged edits, non-edit supersession, stale resources or hidden guards
remain failures. The initial missing snapshot before native admission stays null.

Predeclared storage: the same 4,096 rows / 32 MiB per observation and admission
file, exclusive 32/64 KiB row limits, 512 pending candidates, 64 native trace
records / at most 2 MiB fixed storage, existing native operation/frame/edit files,
64 pending / 128 terminal edits, bounded writer/retirement queues and 600-second
command timeout. Overflow or I/O loss fails rather than truncating evidence.
Existing loading/drain limits and gameplay wall limit (2 * duration + 30 seconds)
remain. All preparation/gameplay/retirement rows, terminal intervals, final
callback, acknowledgement, native closure, writer drain and combined report
finalization remain. Overlapping brackets are never added.

The independent reader splits actual saved coverage counts before/after tick 900
without trimming rows. It retains the first raw failure in each window and joins
all sixteen lateral requests to actual native admission and current submission
observations. All eight due-command handovers and full native drain are required.
Functional evidence integrity remains separate from coverage, edit/operation/
diagnostic assessments. A successful bounded result needs continuous priority
coverage through camera reversal within the existing envelope; any remaining
alarm retains its guard and identifies the next measured cause.

Controls predeclare a complete null/no-exposure observation, the exact 899/900
camera transition, continuing outward motion, all 80 edits/20 saves, both sides
of legitimate eviction, missing/reordered/stalled/incomplete/failed workload,
lost revision/resource/ownership, failed operation/evidence/I/O and unavailable
measurements. Saved actual evidence is independently reconciled and mutated.
All older control expectations and false qualification flags remain.

Copying/formatting/sorting/file I/O perturb elapsed timing. This is neither render
throughput nor per-frame CPU/GPU critical-path cost, shared diagnostic overhead,
physical presentation or HD 620 qualification. No replacement assessment policy
is adopted. M1 remains blocked; no new target-side action is needed now.

## Verified October 13 cloud result

Implementation `51be24a6a45690b536f23c3f3ddccfdabd5fe567` and exported merge/build
`439398d6be1f06f1fd15e7c80daf76bb669ccc8b` share tree
`b1af2634f746ec1e93f8ced3750d4a22cdc45e84`.
[CI 38333317049](https://github.com/dponcho/voxel-survival-game/actions/runs/38333317049)
passed all three jobs on its first attempt: 91 Python regressions, six native
sanitizer suites, matching editor/debug/release qualification, all eight new
processes, every preceding control/replay/runtime/profile check, DLL audit and
two fresh offline extractions. The exact source-built native binaries are reused
under unchanged key
`b45c169f391a4af65b5b4157dc1cc112b7dbd1ddd8b5fb2f85cf529bf694f502`.
No engine or compiler ran locally.

| Engine / workers | FIFO coverage before / after camera turn | FIFO lateral unready observations | Priority coverage before / after | Priority lateral unready | Priority current before 96 m entry |
| --- | --- | --- | --- | --- | --- |
| Editor / 1 | 36 / 0 | 77 | 0 / 0 | 0 | 16 / 16 |
| Editor / 2 | 38 / 0 | 81 | 0 / 0 | 0 | 16 / 16 |
| Release / 1 | 37 / 0 | 79 | 0 / 0 | 0 | 16 / 16 |
| Release / 2 | 36 / 0 | 77 | 0 / 0 | 0 | 16 / 16 |

The camera reverses exactly at tick 900 while outward motion continues to
`[139.99847412109375, 0.0010000000474974513, 10]` (float32). Each pair retains
exact work/configuration/command evidence: 1,200 ticks, 28,800 actor updates,
80 accepted due edits, 20 saves and eight actual `1 -> 2 -> 1` handovers at
ticks 56/204/351/499/647/794/942/1090. All 64 priority lateral witnesses are
currently submitted before entry, including columns 13/14 requested after the
camera turns. FIFO's retained alarms all precede the turn; its post-turn scan
also reports zero. The result does not establish a FIFO camera-turn failure.

Priority submits all original 80 edit identities per run, with no supersession,
cancellation, timeout or unavailable outcomes, and passes the existing edit and
operation guards. Its submitted-edit maximum latencies are
42,094/42,060/42,121/41,974 microseconds; these instrumented cloud observations
do not estimate target performance or causal overhead. FIFO fails the edit
duration guard in all four runs. Editor/two-worker FIFO additionally retains
edit 53 at voxel `[96, 6, 13]`, timed out after 201,272 microseconds with both
current requested revisions 850/851 still unsubmitted. Its terminal report has
79 submitted plus one timeout; the reader preserves that failure. Every run's
operation guard passes. Every priority scenario remains **inconclusive**, solely
under the unchanged diagnostic-cost guard; FIFO scenarios remain failed.

Three previously ready edited cells per run, `[-1, 0, 0]`, `[0, 0, 0]` and
`[1, 0, 0]`, are actually evicted outside 96 m. Last submitted identities and
the subsequent native missing/null observations are retained. The observer does
not retain resources or treat missing as air. Loss inside required geometry and
fabricated non-null missing identities are rejected. Mesh/data peaks remain
511/867, travel retirement high-water two, complete retirement high-water 287,
and overloads zero, with full native drain.

The eight trials reconcile **26,770 native admission records / 28,419,106 bytes,
20,148 observations / 128,681,342 bytes, 24 native phases / 26,826 operation rows
and 23,211 frame rows**. Maximum pending is 460. Each file stays below the
predeclared 4,096-row/32 MiB limits; every callback, phase closure,
acknowledgement, writer drain and combined finalization is retained. Published
download review verifies portable byte round-trip, archive CRC/paths, all 78 PCK
entry MD5s, exact native/build identities, eight native/game/offline self-tests
and 38 PE imports. The independent saved reader rejects all 26 earlier mutations
and twelve new mutations covering incomplete/camera/motion/tail/null/eviction/
checkpoint/operation/I/O/phase/final-callback evidence. Three new Python tests
also use an independent exact float32/integer command oracle and reject 21
modeled faults; the original 600-tick case cannot be replaced by this case.

Ten ordinary folders / 98 scenarios / 284 phases reconcile 37,349 operation rows,
14,321 scenario samples and 94 edits. All 42 preceding heavy work/configuration/
available exact contracts match the durable public baseline. Ordinary production
still uses FIFO, and short 16³ H2 retains edit/diagnostic failures. No ordinary
operation exceedance occurred in this run; earlier measured cloud/target
operation failures remain historical and unwaived. Every prior assessment and
control expectation remains. Headless OpenGL readback is still unavailable.

[Windows player 11783674763](https://github.com/dponcho/voxel-survival-game/actions/runs/38333317049/artifacts/11783674763)
expires `2026-11-12T02:01:01Z`. Portable ZIP: 30,127,996 bytes; SHA-256
`5c49e34a1d041c41f349f52273ceb16c3de8f7662fbd2ea40d63fa0812be36ff`.
See [the public verification record](evidence/m1-frontier-reversal-cloud-2026-10-13.json)
for exact artifacts, saved witnesses, preserved failures and qualification flags.

This verifies the opt-in, traced twenty-second scope. Ordinary priority without
the replay observer/admission trace, full/repeated routes, physical pixels,
HD 620 pacing, per-frame CPU/GPU sensitivity and shared diagnostic overhead remain
unverified. The next bounded check exercises that ordinary untraced path with
matched work and unchanged guards; it does not adopt a broader default policy.
M1 remains blocked, M2 gated; **no new target-side action is needed now**.
