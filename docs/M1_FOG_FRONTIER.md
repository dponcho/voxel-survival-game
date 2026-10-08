# M1 fog/frontier evidence

October 8: the first public 16³ H1/H2 boundary is corrected by four fixed
preparation viewers, not a readiness/fog change. Matching editor/release replay
reproduces the baseline missing alarm and verifies submitted coverage through
base handover; an unprepared gap still fails. Ordinary short cloud H1/H2 smokes
have zero exposed samples for both worker counts. This does not certify full
routes, H2 operations, pixels or HD 620. See
[the bounded replay and exact candidate](M1_FRONTIER_BOUNDARY_REPLAY.md).

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
are unchanged. The October 3 exact-build baseline supplies new recorded timing
evidence for that fog setting; rendered pixel coverage remains unverified.

The original report evaluates transmittance before the shader's `packHalf2x16`
opacity packing. The analytic terminal boundary is conservative and does not
qualify rendered opacity or pixel coverage.
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

## Separately reported shader conversion model

`fog_frontier.renderer_model` adds a conversion-only verdict; the raw CSV,
analytic verdict, scenario gates and schema 5 remain unchanged. Reports now
record the actual rendering driver, platform and display backend. Only the exact
Godot pin, desktop Windows/Linux `opengl3` Compatibility path and the exact M1
fog settings are supported. Missing context, ANGLE, GLES, Web, headless rendering,
changed settings and invalid samples remain unavailable/inconclusive.

Source verification changed the earlier nearest-rounding inference. At pinned
Godot `ed1daf0bf001b61586d9930840f2f1394092c079`,
[scene.glsl](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/shaders/scene.glsl)
packs and unpacks fog before blending. Desktop
[Config](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/storage/config.h)
defaults `polyfill_half2float` to true;
[shader_gles3.cpp](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/shader_gles3.cpp)
selects `USE_HALF2FLOAT`. The
[stdlib_inc.glsl](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/shaders/stdlib_inc.glsl)
conversion drops float32 mantissa bits, without rounding, and flushes small
values. `config.cpp` disables this polyfill for ANGLE and Web; their conversion
is outside this model. Ordinary IEEE nearest binary16 conversion is not a valid
oracle for the default desktop shader path.

An independent arithmetic-floor oracle replayed all 113,890 saved baseline H1/H2
rows. H1 has 360 analytic alarms: 352 retain packed alpha `0x3bff`
(transmittance 0.00048828125) and eight convert to alpha one. H2 has 536 alarms:
527 retain `0x3bff` and nine convert to one. The latter 17 remain inconclusive:
conversion alone cannot certify float32 shader arithmetic or inside-boundary
coverage. The older report did not record the actual rendering driver, so this
replay assumes the confirmed desktop path; it does not certify target rendering.
These are conservative region alarms, not observed exposed pixels.

The ledger retains counts and one worst model sample. It never promotes an
inside-boundary sample to passed or marks pixel visibility qualified. Evaluator
tests use independent binary16 encodings, midpoint/cutoff cases and unsupported
contexts. Cloud smoke reconstructs both summaries from the unchanged frame CSV.
An optional 8×8 canvas readback tests the same shared shader conversion by
encoding half bits as two color bytes. This isolates packing, not terrain fog,
HD 620 rendering or performance; startup OpenGL unavailability is explicit and
script/shader failures block CI. Its result is retained separately in candidate
metadata. No renderer readback is added to gameplay. The reporting increment
does not change world/save versions, native inputs, fog, radii, caps or workloads;
heavy diagnostic overhead still needs measurement.

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

The separate schema 6 [matched heavy comparison](M1_HEAVY_DIAGNOSTIC_AB.md)
now exercises this exact scan on H1/H2 routes. Its off mode dispatches no scan;
coverage is explicitly unavailable, not a passing zero. Its cost scope does not
qualify shared diagnostic instrumentation or replace existing analytic alarms.
