#pragma once
#include "core/os/os.h"
#include "scene/resources/mesh.h"
#include "../core/operation_metrics.h"
#include "../core/edit_visibility.h"
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
inline void begin_frame() {
    operations.begin_frame(OS::get_singleton()->get_ticks_usec());
    frame_upload_bytes = 0; frame_upload_usec = 0;
}
inline bool admit_upload(uint32_t bytes) {
    if (shutting_down) return true; // Exit is not a gameplay frame; shutdown must drain.
    if (bytes > 256 * 1024) { ++overloads; return false; }
    return frame_upload_bytes + bytes <= byte_budget && frame_upload_usec + 750 <= time_budget;
}
inline void record_upload(uint32_t bytes, uint64_t start) {
    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;
    frame_upload_bytes += bytes; frame_upload_usec += elapsed;
    upload_bytes += bytes; upload_usec += elapsed; ++uploads;
    upload_max_usec = MAX(upload_max_usec, elapsed);
    operations.record_upload(bytes, start, elapsed);
}
inline void record_deletion(uint32_t bytes, uint64_t start, bool surface) {
    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;
    deletion_usec += elapsed; frame_upload_usec += elapsed;
    deletion_max_usec = MAX(deletion_max_usec, elapsed);
    operations.record_deletion(bytes, start, elapsed, surface);
}
}
