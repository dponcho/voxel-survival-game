#pragma once
#include "core/os/os.h"
#include "scene/resources/mesh.h"
#include "../core/operation_metrics.h"
#include "../core/edit_visibility.h"
#include "../core/mesh_batch.h"
#include "../core/viewer_demand.h"
#include "../core/mesh_admission.h"
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
inline void record_upload(uint32_t bytes, uint64_t start) {
    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;
    frame_upload_bytes += bytes; frame_upload_usec += elapsed;
    upload_bytes += bytes; upload_usec += elapsed; ++uploads;
    upload_max_usec = MAX(upload_max_usec, elapsed);
    operations.record_upload(bytes, start, elapsed);
}
// Main-thread, test-only observation. Null in ordinary gameplay. A bounded
// capability fixture observes ObjectDB before the unchanged ending clock read;
// its inspection cost stays inside that fixture's measured operation.
inline void (*retirement_control_before_end)(uint32_t, uint64_t, bool) = nullptr;
inline void record_deletion(uint32_t bytes, uint64_t start, bool surface) {
    if (retirement_control_before_end) retirement_control_before_end(bytes, start, surface);
    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;
    deletion_usec += elapsed; frame_upload_usec += elapsed;
    deletion_max_usec = MAX(deletion_max_usec, elapsed);
    operations.record_deletion(bytes, start, elapsed, surface);
}
inline void record_data_apply(uint64_t start, uint64_t previous_charged_usec) {
    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;
    const uint64_t nested = frame_upload_usec - previous_charged_usec;
    if (nested > elapsed) ++overloads;
    const uint64_t bounded_nested = MIN(nested, elapsed);
    data_apply_usec += elapsed; data_apply_max_usec = MAX(data_apply_max_usec, elapsed);
    frame_upload_usec += elapsed - bounded_nested;
    operations.record_data_apply(start, elapsed, bounded_nested);
}
}
