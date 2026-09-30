# M1 fog/frontier evidence

Schema 5 adds H1/H2 required-region coverage to the existing bounded frame CSV.
The native probe inspects render regions intersecting the current camera frustum
and the fixture surface envelope Y [-16,7). This covers fixture 1 and H2's
temporary edits. It does not generalize to future generators or world envelopes.

Readiness comes from the pinned Voxel Tools mesh map. Missing, pending and hidden
regions remain unready. A submitted visible mesh or a confirmed-empty result is
ready. Data residency and pending-job counts cannot substitute for mesh readiness.
Old visible meshes remain coverage while replacement revisions are handled by
the separate edit-visibility trace.

The reported distance is a conservative Euclidean lower bound to the closest
unready region's box. Box/frustum overlap does not prove pixel visibility;
occlusion and the actual first exposed surface are unavailable. If all inspected
regions are ready, distance is a far-clip lower bound, not an observed gap.
Each row retains camera position/yaw, region identity/state, counts, probe time,
fog transmittance and available boundary/clearance values. No sample outside H1/H2
is represented as zero; those fields say `not_run`.

The pinned Compatibility shader uses `1 - exp(-distance * density)` for the
current exponential fog. It has no finite fully opaque boundary. Boundary and
clearance remain null/`unavailable`, with the reason retained in the summary.
No arbitrary opacity cutoff or new acceptance tolerance is introduced. An
unready required region before opaque fog fails the conservative coverage check;
complete coverage with an unavailable boundary remains inconclusive. Depth fog
can supply a finite boundary only when its terminal opacity is 1. An unobserved
boundary beyond the far clip cannot pass. Settings and workloads are unchanged.

The probe rejects scans exceeding 1,024 candidate regions before traversal.
There is no new worker, terrain lock, renderer readback or retained sample array.
The ledger keeps totals, minima and one worst sample; raw rows use the existing
bounded CSV and disk queue. Probe/formatting work belongs to the full callback
timer. Existing flat-fixture A/B phases do not exercise this heavy-only probe, so
they cannot qualify its overhead. Exact-build HD 620 evidence is outstanding.

Cloud checks cover fog crossings and the exact boundary, missing/invalid inputs,
confirmed-empty readiness, negative coordinates/camera reversals, eviction,
scan bounds and actual saved CSV/count/minimum/equation reconciliation. Headless
integration proves these mechanics, not target rendering or performance.
