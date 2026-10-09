#include "benchmark_probe.h"
#include "m1_hooks.h"
#include "modules/voxel/engine/voxel_engine.h"
#include "modules/voxel/terrain/fixed_lod/voxel_terrain.h"
#include "scene/3d/camera_3d.h"
#include "core/object/class_db.h"
#include "core/os/thread.h"
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
    ClassDB::bind_method(D_METHOD("sample_frontier", "terrain", "camera", "surface_bounds"), &CairnProbe::sample_frontier);
    ClassDB::bind_method(D_METHOD("sample_mesh_blocks", "terrain", "coordinates"), &CairnProbe::sample_mesh_blocks);
    ClassDB::bind_method(D_METHOD("set_mesh_admission", "terrain", "priority", "origin", "trace"), &CairnProbe::set_mesh_admission);
    ClassDB::bind_method(D_METHOD("begin_mesh_admission_trace"), &CairnProbe::begin_mesh_admission_trace);
    ClassDB::bind_method(D_METHOD("mesh_admission_snapshot"), &CairnProbe::mesh_admission_snapshot);
    ClassDB::bind_method(D_METHOD("take_mesh_admission_frames"), &CairnProbe::take_mesh_admission_frames);
}

bool CairnProbe::set_mesh_admission(Object *object, bool priority, Vector3 origin, bool trace) {
    auto *terrain = Object::cast_to<zylann::voxel::VoxelTerrain>(object);
    if (!Thread::is_main_thread() || terrain == nullptr || !terrain->is_inside_tree() ||
            terrain->get_global_transform() != Transform3D() || !origin.is_finite() ||
            terrain->get_mesh_block_size() != 16 || terrain->get_generate_collisions()) return false;
    terrain->set_cairn_mesh_admission(priority, origin, trace);
    return true;
}
void CairnProbe::begin_mesh_admission_trace() { cairn::mesh_admission.reset(); }
Dictionary CairnProbe::mesh_admission_snapshot() const {
    const auto &s = cairn::mesh_admission;
    Dictionary d;
    d["enabled"] = s.enabled; d["recorded"] = int64_t(s.recorded); d["popped"] = int64_t(s.popped);
    d["dropped"] = int64_t(s.dropped); d["queued"] = int64_t(s.queued());
    d["high_water"] = int64_t(s.high_water); d["max_pending"] = int64_t(s.max_pending);
    d["record_cap"] = int64_t(s.CAPACITY); d["pending_cap"] = int64_t(cairn::MESH_PENDING_CAP);
    d["fixed_storage_bytes"] = int64_t(sizeof(s));
    return d;
}
Array CairnProbe::take_mesh_admission_frames() {
    Array result;
    while (const auto *r = cairn::mesh_admission.pop()) {
        Dictionary d;
        d["row"] = int64_t(r->row); d["phase"] = int64_t(r->phase);
        d["start_usec"] = int64_t(r->start_usec); d["end_usec"] = int64_t(r->end_usec);
        d["decision_usec"] = int64_t(r->decision_usec);
        Array origin; for (double value : r->origin) origin.push_back(value);
        d["origin"] = origin; d["side"] = int(r->side); d["priority"] = r->priority; d["valid"] = r->valid;
        d["pending_count"] = int(r->count); d["admitted"] = int(r->admitted);
        d["jobs_before"] = int(r->jobs_before); d["jobs_after"] = int(r->jobs_after);
        Array pending, order, loads;
        if (r->valid) for (size_t i = 0; i < r->count; ++i) {
            const auto &c = r->pending[i];
            Array item;
            item.push_back(c.x); item.push_back(c.y); item.push_back(c.z); item.push_back(int(c.flags));
            item.push_back(c.desired ? Variant(String::num_uint64(c.desired)) : Variant());
            item.push_back(c.submitted ? Variant(String::num_uint64(c.submitted)) : Variant());
            pending.push_back(item); order.push_back(int(r->order[i]));
        }
        for (size_t i = 0; i < r->admitted && i < cairn::MESH_PENDING_CAP; ++i) loads.push_back(int(r->loads[i]));
        d["pending"] = r->valid ? Variant(pending) : Variant();
        d["order"] = r->valid ? Variant(order) : Variant();
        d["loads"] = r->valid ? Variant(loads) : Variant();
        result.push_back(d);
    }
    return result;
}

Dictionary CairnProbe::sample_mesh_blocks(Object *terrain_object, Array coordinates) const {
    Dictionary d;
    d["status"] = "unavailable";
    d["reason"] = "requires a live fixture terrain, main thread and 1..16 distinct Vector3i coordinates";
    d["blocks"] = Variant();
    d["probe_usec"] = Variant();
    auto *terrain = Object::cast_to<zylann::voxel::VoxelTerrain>(terrain_object);
    if (!Thread::is_main_thread() || terrain == nullptr || !terrain->is_inside_tree() ||
            coordinates.size() < 1 || coordinates.size() > 16) return d;
    for (int i = 0; i < coordinates.size(); ++i) {
        if (coordinates[i].get_type() != Variant::VECTOR3I) return d;
        for (int j = 0; j < i; ++j) if (coordinates[i] == coordinates[j]) return d;
    }
    const uint64_t start = OS::get_singleton()->get_ticks_usec();
    Array blocks;
    for (int i = 0; i < coordinates.size(); ++i) {
        const Vector3i coordinate = coordinates[i];
        Dictionary block = terrain->get_cairn_mesh_observation(coordinate);
        Array position;
        position.push_back(coordinate.x); position.push_back(coordinate.y); position.push_back(coordinate.z);
        block["block"] = position;
        blocks.push_back(block);
    }
    d["status"] = "measured";
    d["reason"] = "";
    d["blocks"] = blocks;
    d["probe_usec"] = int64_t(OS::get_singleton()->get_ticks_usec() - start);
    return d;
}

Dictionary CairnProbe::sample_frontier(Object *terrain_object, Object *camera_object, AABB surface_bounds) const {
    const uint64_t start = OS::get_singleton()->get_ticks_usec();
    Dictionary d;
    d["status"] = "unavailable";
    d["reason"] = "invalid terrain, camera or surface bounds";
    auto *terrain = Object::cast_to<zylann::voxel::VoxelTerrain>(terrain_object);
    auto *camera = Object::cast_to<Camera3D>(camera_object);
    if (terrain == nullptr || camera == nullptr || !terrain->is_inside_tree() || !camera->is_inside_tree() ||
            !surface_bounds.position.is_finite() || !surface_bounds.size.is_finite() ||
            surface_bounds.size.x <= 0 || surface_bounds.size.y <= 0 || surface_bounds.size.z <= 0) return d;
    if (terrain->get_global_transform() != Transform3D() || !terrain->is_visible_in_tree()) {
        d["reason"] = "frontier probe requires visible, untransformed fixture terrain";
        return d;
    }
    const auto terrain_box = terrain->get_bounds();
    surface_bounds = surface_bounds.intersection(AABB(Vector3(terrain_box.position), Vector3(terrain_box.size)));
    const Transform3D pose = camera->get_camera_transform();
    const Vector<Plane> planes = camera->get_frustum();
    Vector3 endpoints[8];
    if (!pose.origin.is_finite() || planes.size() != 6 ||
            !camera->get_camera_projection().get_endpoints(pose, endpoints)) {
        d["reason"] = "invalid camera frustum";
        return d;
    }
    AABB query(endpoints[0], Vector3());
    for (int i = 0; i < 8; ++i) {
        if (!endpoints[i].is_finite()) return d;
        query.expand_to(endpoints[i]);
    }
    query = query.intersection(surface_bounds);
    if (query.size.x <= 0 || query.size.y <= 0 || query.size.z <= 0) {
        d["reason"] = "no fixture surface region in frustum";
        return d;
    }
    const int size = terrain->get_mesh_block_size();
    const Vector3 end = query.position + query.size;
    const Vector3i first(int(Math::floor(query.position.x / size)), int(Math::floor(query.position.y / size)), int(Math::floor(query.position.z / size)));
    const Vector3i last(int(Math::ceil(end.x / size)), int(Math::ceil(end.y / size)), int(Math::ceil(end.z / size)));
    const int64_t candidates = int64_t(last.x - first.x) * (last.y - first.y) * (last.z - first.z);
    // Hard bound before traversal; never truncate a scan and report it complete.
    if (candidates <= 0 || candidates > 1024) {
        d["reason"] = "frontier scan exceeds 1024 candidate regions";
        return d;
    }
    int checked = 0, ready = 0, empty = 0, unready = 0;
    double nearest = 0;
    int nearest_state = 0;
    Vector3i nearest_block;
    for (int z = first.z; z < last.z; ++z) for (int x = first.x; x < last.x; ++x) for (int y = first.y; y < last.y; ++y) {
        const Vector3i coordinate(x, y, z);
        const AABB box = AABB(Vector3(coordinate * size), Vector3(size, size, size)).intersection(surface_bounds);
        const Vector3 center = box.position + box.size * 0.5;
        const Vector3 half = box.size * 0.5;
        bool outside = false;
        for (int i = 0; i < planes.size(); ++i) {
            const Plane &p = planes[i];
            const double radius = Math::abs(p.normal.x) * half.x + Math::abs(p.normal.y) * half.y + Math::abs(p.normal.z) * half.z;
            if (p.distance_to(center) > radius) { outside = true; break; }
        }
        if (outside) continue;
        ++checked;
        const int state = terrain->get_cairn_mesh_state(coordinate);
        if (state >= 3) { ++ready; if (state == 4) ++empty; continue; }
        const Vector3 closest(CLAMP(pose.origin.x, box.position.x, box.position.x + box.size.x),
                CLAMP(pose.origin.y, box.position.y, box.position.y + box.size.y),
                CLAMP(pose.origin.z, box.position.z, box.position.z + box.size.z));
        const double distance = pose.origin.distance_to(closest);
        if (unready == 0 || distance < nearest) { nearest = distance; nearest_block = coordinate; nearest_state = state; }
        ++unready;
    }
    if (checked == 0) { d["reason"] = "no required regions sampled"; return d; }
    d["status"] = "measured";
    d["reason"] = "";
    d["candidate_regions"] = candidates;
    d["checked_regions"] = checked;
    d["ready_regions"] = ready;
    d["empty_regions"] = empty;
    d["unready_regions"] = unready;
    d["camera_far_m"] = camera->get_far();
    d["frontier_distance_m"] = unready > 0 ? nearest : double(camera->get_far());
    d["frontier_kind"] = unready > 0 ? "unready_region_lower_bound" : "far_clip_lower_bound";
    if (unready > 0) {
        Array block; block.push_back(nearest_block.x); block.push_back(nearest_block.y); block.push_back(nearest_block.z);
        d["block"] = block;
        static const char *states[] = {"missing", "pending", "hidden"};
        d["mesh_state"] = states[nearest_state];
    }
    d["probe_usec"] = int64_t(OS::get_singleton()->get_ticks_usec() - start);
    return d;
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
