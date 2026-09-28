#include "benchmark_probe.h"
#include "m1_hooks.h"
#include "modules/voxel/engine/voxel_engine.h"
#include "core/object/class_db.h"
#ifdef WINDOWS_ENABLED
#include <windows.h>
#include <psapi.h>
#endif

void CairnProbe::_bind_methods() {
    ClassDB::bind_method(D_METHOD("snapshot"), &CairnProbe::snapshot);
    ClassDB::bind_method(D_METHOD("machine"), &CairnProbe::machine);
    ClassDB::bind_method(D_METHOD("configure", "workers", "heavy"), &CairnProbe::configure);
    ClassDB::bind_method(D_METHOD("begin_phase", "id", "trace"), &CairnProbe::begin_phase);
    ClassDB::bind_method(D_METHOD("end_phase"), &CairnProbe::end_phase);
    ClassDB::bind_method(D_METHOD("phase_snapshot"), &CairnProbe::phase_snapshot);
    ClassDB::bind_method(D_METHOD("take_operation_frames"), &CairnProbe::take_operation_frames);
    ClassDB::bind_method(D_METHOD("start_edit_trace", "enabled"), &CairnProbe::start_edit_trace);
    ClassDB::bind_method(D_METHOD("tick_edit_trace"), &CairnProbe::tick_edit_trace);
    ClassDB::bind_method(D_METHOD("finish_edit_trace"), &CairnProbe::finish_edit_trace);
    ClassDB::bind_method(D_METHOD("edit_trace_snapshot"), &CairnProbe::edit_trace_snapshot);
    ClassDB::bind_method(D_METHOD("take_edit_events"), &CairnProbe::take_edit_events);
}
void CairnProbe::start_edit_trace(bool enabled) {
    cairn::edit_visibility.reset(enabled);
}
void CairnProbe::tick_edit_trace() {
    cairn::edit_visibility.tick(OS::get_singleton()->get_ticks_usec());
}
void CairnProbe::finish_edit_trace() {
    cairn::edit_visibility.stop(OS::get_singleton()->get_ticks_usec());
}
Dictionary CairnProbe::edit_trace_snapshot() const {
    const auto &s = cairn::edit_visibility;
    Dictionary d;
    d["enabled"] = s.enabled;
    d["accepted"] = int64_t(s.accepted);
    d["submitted"] = int64_t(s.submitted);
    d["superseded"] = int64_t(s.superseded);
    d["cancelled"] = int64_t(s.cancelled);
    d["timeout"] = int64_t(s.timed_out);
    d["unavailable"] = int64_t(s.unavailable);
    d["overflow"] = int64_t(s.overflow);
    d["pending"] = int64_t(s.pending());
    d["pending_high_water"] = int64_t(s.pending_high_water);
    d["queued"] = int64_t(s.queued());
    d["p95_upper_usec"] = int64_t(s.p95_upper_usec());
    d["max_usec"] = int64_t(s.max_usec);
    return d;
}
Array CairnProbe::take_edit_events() {
    Array result;
    cairn::EditEvidence e;
    while (cairn::edit_visibility.pop(e)) {
        Dictionary d;
        d["id"] = int64_t(e.id);
        Array voxel;
        voxel.push_back(e.x); voxel.push_back(e.y); voxel.push_back(e.z);
        d["voxel"] = voxel;
        d["accepted_usec"] = int64_t(e.accepted_usec);
        d["end_usec"] = int64_t(e.end_usec);
        d["latency_usec"] = int64_t(e.end_usec - e.accepted_usec);
        static const char *names[] = {"invalid", "submitted", "superseded", "cancelled", "timeout", "unavailable"};
        d["outcome"] = names[e.outcome];
        Array targets;
        for (unsigned int i = 0; i < e.target_count; ++i) {
            const auto &block = e.targets[i];
            Dictionary target;
            Array coordinate;
            coordinate.push_back(block.x); coordinate.push_back(block.y); coordinate.push_back(block.z);
            target["block"] = coordinate;
            target["revision"] = int64_t(block.revision);
            target["submitted"] = block.submitted;
            targets.push_back(target);
        }
        d["targets"] = targets;
        result.push_back(d);
    }
    return result;
}
static Dictionary operation_totals(const cairn::OperationTotals &s) {
    Dictionary d;
    d["count"] = int64_t(s.count); d["bytes"] = int64_t(s.bytes); d["usec"] = int64_t(s.usec);
    d["max_usec"] = int64_t(s.max_usec); d["max_bytes"] = int64_t(s.max_bytes);
    d["max_start_usec"] = int64_t(s.max_start_usec); d["max_kind"] = s.max_kind;
    return d;
}
void CairnProbe::begin_phase(int64_t id, bool trace) {
    cairn::operations.begin_phase(id, OS::get_singleton()->get_ticks_usec(), trace);
}
Dictionary CairnProbe::phase_snapshot() const {
    const auto &s = cairn::operations;
    Dictionary d;
    d["id"] = int64_t(s.phase); d["upload"] = operation_totals(s.upload);
    d["deletion"] = operation_totals(s.deletion); d["frames"] = int64_t(s.frames);
    d["dropped_frames"] = int64_t(s.dropped); d["tracing"] = s.tracing;
    d["peak_frame_operation_usec"] = int64_t(s.peak_frame_usec);
    d["peak_frame_upload_bytes"] = int64_t(s.peak_frame_upload_bytes);
    return d;
}
Dictionary CairnProbe::end_phase() {
    cairn::operations.end_phase(OS::get_singleton()->get_ticks_usec());
    return phase_snapshot();
}
Array CairnProbe::take_operation_frames() {
    Array frames;
    cairn::OperationFrame frame;
    while (cairn::operations.pop(frame)) {
        Dictionary d;
        d["native_frame"] = int64_t(frame.native_frame); d["phase"] = int64_t(frame.phase);
        d["start_usec"] = int64_t(frame.start_usec); d["end_usec"] = int64_t(frame.end_usec);
        d["phase_boundary"] = frame.phase_boundary;
        d["upload"] = operation_totals(frame.upload); d["deletion"] = operation_totals(frame.deletion);
        frames.push_back(d);
    }
    return frames;
}
void CairnProbe::configure(int workers, bool heavy) {
    auto &engine = zylann::voxel::VoxelEngine::get_singleton();
    if (workers >= 1 && workers <= 2 && workers != engine.get_thread_count()) engine.set_thread_count(workers);
    cairn::byte_budget = heavy ? 1024 * 1024 : 512 * 1024;
    cairn::time_budget = heavy ? 2000 : 1000;
    engine.set_main_thread_time_budget_usec(cairn::time_budget);
}
Dictionary CairnProbe::snapshot() const {
    Dictionary d;
    const auto s = zylann::voxel::VoxelEngine::get_singleton().get_stats();
    d["generation_jobs"] = s.generation_tasks; d["mesh_jobs"] = s.meshing_tasks;
    d["result_jobs"] = cairn::result_tasks; d["main_jobs"] = s.main_thread_tasks;
    d["generated"] = int64_t(cairn::generated.load()); d["meshed"] = int64_t(cairn::meshed.load());
    d["generation_usec"] = int64_t(cairn::generation_usec.load());
    d["meshing_usec"] = int64_t(cairn::meshing_usec.load());
    d["upload_usec"] = int64_t(cairn::upload_usec); d["upload_max_usec"] = int64_t(cairn::upload_max_usec);
    d["upload_bytes"] = int64_t(cairn::upload_bytes); d["uploads"] = int64_t(cairn::uploads);
    d["stale_results"] = int64_t(cairn::stale); d["overloads"] = int64_t(cairn::overloads.load());
    d["deletion_usec"] = int64_t(cairn::deletion_usec); d["deletion_max_usec"] = int64_t(cairn::deletion_max_usec);
    d["retired_meshes"] = cairn::retired_meshes; d["retired_high_water"] = cairn::retired_high_water;
    d["data_apply_usec"] = int64_t(cairn::data_apply_usec);
    d["data_apply_max_usec"] = int64_t(cairn::data_apply_max_usec);
#ifdef WINDOWS_ENABLED
    PROCESS_MEMORY_COUNTERS_EX memory = {};
    memory.cb = sizeof(memory);
    if (GetProcessMemoryInfo(GetCurrentProcess(), reinterpret_cast<PROCESS_MEMORY_COUNTERS *>(&memory), sizeof(memory))) {
        d["private_bytes"] = int64_t(memory.PrivateUsage);
        d["working_set"] = int64_t(memory.WorkingSetSize);
    }
#endif
    return d;
}
Dictionary CairnProbe::machine() const {
    Dictionary d;
#ifdef WINDOWS_ENABLED
    MEMORYSTATUSEX memory = {}; memory.dwLength = sizeof(memory);
    if (GlobalMemoryStatusEx(&memory)) {
        d["installed_ram_bytes"] = int64_t(memory.ullTotalPhys);
        d["available_ram_bytes"] = int64_t(memory.ullAvailPhys);
    }
    SYSTEM_POWER_STATUS power = {};
    if (GetSystemPowerStatus(&power)) d["ac_power"] = int(power.ACLineStatus);
#endif
    return d;
}
