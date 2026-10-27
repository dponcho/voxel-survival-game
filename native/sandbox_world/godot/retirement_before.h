// Frozen rejected production lifetime, for the bounded native control only.
#ifndef CAIRN_FROZEN_FREE_MESH_TASK_H
#define CAIRN_FROZEN_FREE_MESH_TASK_H
#include "../engine/voxel_engine.h"
#include "../util/godot/direct_mesh_instance.h"
#include "modules/sandbox_world/godot/m1_hooks.h"
namespace zylann::voxel {
// Release a bounded surface per operation, under the same upload/delete allowance.
// The M1 single-viewer slab has <=507 mesh blocks. New viewer demand waits above
// 128 retirees, leaving capacity for a complete old scene plus four mesh results.
class CairnBeforeFreeMeshTask : public ITimeSpreadTask {
public:
    static CairnBeforeFreeMeshTask *cairn_control_create(Ref<Mesh> mesh) { return ZN_NEW(CairnBeforeFreeMeshTask(mesh)); }
    static void add(Ref<Mesh> mesh) {
        if (mesh.is_null()) return;
        CairnBeforeFreeMeshTask *task = ZN_NEW(CairnBeforeFreeMeshTask(mesh));
        VoxelEngine::get_singleton().push_main_thread_time_spread_task(task);
    }
    static void try_add_and_destroy(zylann::godot::DirectMeshInstance &mi) {
        if (mi.get_mesh_ptr() != nullptr) add(mi.get_mesh());
        mi.destroy();
    }
    void run(TimeSpreadTaskContext &ctx) override {
        if (!cairn::admit_upload(0)) { ctx.postpone = true; return; }
        const uint64_t start = OS::get_singleton()->get_ticks_usec();
        Ref<ArrayMesh> array = _mesh;
        const bool surface = array.is_valid() && array->get_surface_count() > 0;
        const int last_surface = surface ? array->get_surface_count() - 1 : 0;
        const uint32_t bytes = surface ? cairn::mesh_payload_bytes(
                array->surface_get_array_len(last_surface), array->surface_get_array_index_len(last_surface)) : 0;
        if (surface) {
            array->surface_remove(array->get_surface_count() - 1);
            ctx.postpone = true;
        } else { _mesh.unref(); }
        cairn::record_deletion(bytes, start, surface);
    }
    ~CairnBeforeFreeMeshTask() { --cairn::retired_meshes; }
private:
    explicit CairnBeforeFreeMeshTask(Ref<Mesh> mesh) : _mesh(mesh) {
        ++cairn::retired_meshes;
        cairn::retired_high_water = MAX(cairn::retired_high_water, cairn::retired_meshes);
        if (cairn::retired_meshes > 768) ++cairn::overloads;
    }
    Ref<Mesh> _mesh;
};
}
#endif
