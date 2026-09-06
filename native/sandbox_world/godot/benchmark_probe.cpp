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
