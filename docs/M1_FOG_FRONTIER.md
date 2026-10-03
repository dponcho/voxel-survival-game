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

The M1 profile now uses Compatibility depth fog: begin 16 m, end 96 m,
density 1 and curve 1, with no height fog. The pinned shader computes
`pow(smoothstep(begin, end, length(vertex)), curve) * density` opacity.
Distance is radial, matching the probe's Euclidean lower bound, rather than
camera Z depth. Opacity reaches 1 at 96 m, providing a finite analytic boundary
without reducing the fixed 96 m visual or 128 m data demand. The fog color still
matches the existing background. Resolution, routes, ticks, workloads and caps
are unchanged. This rendering-setting change requires new target evidence.

The report evaluates transmittance before the shader's `packHalf2x16` opacity
packing; rounding may produce stored opacity 1 earlier. The analytic terminal
boundary is conservative and does not qualify rendered opacity or pixel coverage.
No arbitrary opacity cutoff or new acceptance tolerance is introduced. An unready
required region inside 96 m still fails; coverage at or beyond the opaque boundary
can pass the conservative check. An unobserved boundary beyond the far clip
cannot pass. Invalid inputs remain unavailable/inconclusive. Legacy exponential
fog retains a null boundary, and partial terminal depth opacity cannot manufacture
one. Reports record the actual mode, density, begin/end, curve and height density;
the existing top-level density field now reflects the actual Environment.

The probe rejects scans exceeding 1,024 candidate regions before traversal.
There is no new worker, terrain lock, renderer readback or retained sample array.
The ledger keeps totals, minima and one worst sample; raw rows use the existing
bounded CSV and disk queue. Probe/formatting work belongs to the full callback
timer. Existing flat-fixture A/B phases do not exercise this heavy-only probe, so
they cannot qualify its overhead. Exact-build HD 620 evidence is outstanding.

Regressions cover the actual Environment profile, independent smoothstep values,
fog crossings and the exact 96 m boundary, missing/invalid inputs,
confirmed-empty readiness, negative coordinates/camera reversals, eviction,
scan bounds and actual saved CSV/count/minimum/equation reconciliation. Headless
integration proves these mechanics, not target rendering or performance.

The world-space demand correction covers the fixed 96 m visual and 128 m
data-only envelopes at the actual viewer position, including fractional and
negative positions. Its meshing-data halo covers complete demanded render
blocks and the existing neighbour padding. Independent geometry and all four
cloud profiles verify settled coverage within the clipped M1 fixture and
unchanged caps. These checks do not prove readiness while moving, rendered
opacity or target throughput. The finite analytic boundary leaves genuine
inside-boundary readiness failures observable; target rendering and moving-frontier
qualification remain outstanding.
