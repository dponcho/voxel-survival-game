#pragma once
#include "core/os/os.h"
#include "scene/resources/mesh.h"
#include "../core/operation_metrics.h"
#include "../core/edit_visibility.h"
#include "../core/mesh_batch.h"
#include "../core/viewer_demand.h"
#include "../core/mesh_admission.h"
#include "operation_witness.h"
#include "modules/voxel/util/math/box3i.h"
#include <atomic>
#include <cstdint>

namespace cairn {
inline std::atomic<uint64_t> generated{0}, meshed{0}, generation_usec{0}, meshing_usec{0};
inline std::atomic<uint64_t> overloads{0};
inline uint64_t upload_usec = 0, upload_max_usec = 0, upload_bytes = 0, uploads = 0;
inline uint64_t stale = 0, frame_upload_bytes = 0, frame_upload_usec = 0;
inline uint64_t deletion_usec = 0, deletion_max_usec = 0;
inline uint64_t data_apply_usec = 0, data_apply_max_usec = 0;
inline uint64_t next_revision = 0;
inline uint32_t result_tasks = 0;
inline uint32_t retired_meshes = 0, retired_high_water = 0;
inline uint32_t byte_budget = 512 * 1024, time_budget = 1000;
inline bool shutting_down = false;
inline OperationMetrics operations;
inline EditVisibility edit_visibility;
inline MeshAdmissionTrace mesh_admission;
inline zylann::Box3i viewer_demand_box(Vector3 position, Vector3i radius, int block_size,
        const zylann::Box3i &bounds) {
    Vector3i first, last;
    for (int axis = 0; axis < 3; ++axis) {
        BlockSpan span;
        if (!viewer_block_span(position[axis], radius[axis], block_size,
                {bounds.position[axis], bounds.position[axis] + bounds.size[axis]}, span)) {
            ++overloads; return {};
        }
        if (span.empty()) return {};
        first[axis] = span.begin; last[axis] = span.end;
    }
    return zylann::Box3i::from_min_max(first, last);
}
inline zylann::Box3i meshing_data_box(const zylann::Box3i &mesh, int render_to_data,
        const zylann::Box3i &bounds) {
    if (mesh.is_empty()) return {};
    Vector3i first, last;
    for (int axis = 0; axis < 3; ++axis) {
        BlockSpan span;
        if (!meshing_data_span({mesh.position[axis], mesh.position[axis] + mesh.size[axis]},
                render_to_data, {bounds.position[axis], bounds.position[axis] + bounds.size[axis]}, span)) {
            ++overloads; return {};
        }
        if (span.empty()) return {};
        first[axis] = span.begin; last[axis] = span.end;
    }
    return zylann::Box3i::from_min_max(first, last);
}
inline void begin_frame() {
    operations.begin_frame(OS::get_singleton()->get_ticks_usec());
    frame_upload_bytes = 0; frame_upload_usec = 0;
}
inline bool admit_upload(uint32_t bytes) {
    if (shutting_down) return true; // Exit is not a gameplay frame; shutdown must drain.
    if (bytes > 256 * 1024) { ++overloads; return false; }
    return frame_upload_bytes + bytes <= byte_budget && admit_terrain_operation(frame_upload_usec, time_budget);
}
inline void record_upload(uint32_t bytes, uint64_t start, uint64_t witness = 0) {
    if (witness) operation_witness_ending(witness,1,bytes,0);
    const uint64_t end = OS::get_singleton()->get_ticks_usec();
    const uint64_t elapsed = end - start;
    frame_upload_bytes += bytes; frame_upload_usec += elapsed;
    upload_bytes += bytes; upload_usec += elapsed; ++uploads;
    upload_max_usec = MAX(upload_max_usec, elapsed);
    const bool phase_maximum = witness && operations.active_phase() && (!operations.upload.count || elapsed > operations.upload.max_usec);
    operations.record_upload(bytes, start, elapsed);
    if (witness) operation_witness_commit(witness,end,phase_maximum);
}
// The actual ApplyMeshUpdateTask and finite controls share this renderer entry.
template<class MaterialIndices>
inline void upload_surface(uint32_t bytes, Ref<ArrayMesh> &partial, const Array &arrays,
        int material, MaterialIndices &indices) {
    const uint64_t start = OS::get_singleton()->get_ticks_usec();
    const uint64_t witness = operation_witness ? operation_witness_begin(start) : 0;
    if (partial.is_null()) partial.instantiate();
    partial->add_surface_from_arrays(Mesh::PRIMITIVE_TRIANGLES, arrays);
    indices.push_back(material);
    record_upload(bytes,start,witness);
}
// Main-thread, test-only observation. Null in ordinary gameplay. A bounded
// capability fixture observes ObjectDB before the unchanged ending clock read;
// its inspection cost stays inside that fixture's measured operation.
inline void (*retirement_control_before_end)(uint32_t, uint64_t, bool) = nullptr;
inline void record_deletion(uint32_t bytes, uint64_t start, bool surface, uint64_t witness = 0) {
    if (retirement_control_before_end) retirement_control_before_end(bytes, start, surface);
    if (witness) operation_witness_ending(witness,surface ? 2 : 3,bytes,0);
    const uint64_t end = OS::get_singleton()->get_ticks_usec();
    const uint64_t elapsed = end - start;
    deletion_usec += elapsed; frame_upload_usec += elapsed;
    deletion_max_usec = MAX(deletion_max_usec, elapsed);
    const bool phase_maximum = witness && operations.active_phase() && (!operations.deletion.count || elapsed > operations.deletion.max_usec);
    operations.record_deletion(bytes, start, elapsed, surface);
    if (witness) operation_witness_commit(witness,end,phase_maximum);
}
inline void record_data_apply(uint64_t start, uint64_t previous_charged_usec, uint64_t witness = 0) {
    const uint64_t nested = frame_upload_usec - previous_charged_usec;
    if (witness) operation_witness_ending(witness,4,0,nested);
    const uint64_t end = OS::get_singleton()->get_ticks_usec();
    const uint64_t elapsed = end - start;
    if (nested > elapsed) ++overloads;
    const uint64_t bounded_nested = MIN(nested, elapsed);
    data_apply_usec += elapsed; data_apply_max_usec = MAX(data_apply_max_usec, elapsed);
    frame_upload_usec += elapsed - bounded_nested;
    const bool phase_maximum = witness && operations.active_phase() && (!operations.data_apply.count || elapsed > operations.data_apply.max_usec);
    operations.record_data_apply(start, elapsed, bounded_nested);
    if (witness) operation_witness_commit(witness,end,phase_maximum);
}
}
