#include "benchmark_probe.h"
#include "m1_hooks.h"
#include "retirement_before.h"
#include "../core/observer_ledger.h"
#include "modules/voxel/terrain/free_mesh_task.h"
#include "core/object/object.h"
#include "core/os/thread.h"

namespace {
struct EndpointWitness {
    ObjectID object;
    uint64_t start = 0, observed = 0, order = 0, thread = 0;
    uint32_t calls = 0, bytes = 0;
    bool surface = false, alive = false;
    int references = -1, surfaces = -1;
};
EndpointWitness *current = nullptr;
uint64_t order = 0;
bool used = false;

bool alive(ObjectID id) { return id.is_valid() && ObjectDB::get_instance(id) != nullptr; }
int references(ObjectID id) {
    auto *object = id.is_valid() ? ObjectDB::get_instance<RefCounted>(id) : nullptr;
    return object ? object->get_reference_count() : -1;
}
int surfaces(ObjectID id) {
    auto *mesh = id.is_valid() ? ObjectDB::get_instance<ArrayMesh>(id) : nullptr;
    return mesh ? mesh->get_surface_count() : -1;
}
void before_endpoint(uint32_t bytes, uint64_t start, bool surface) {
    if (!current || ++current->calls != 1) return;
    current->start = start; current->bytes = bytes; current->surface = surface;
    current->thread = cairn::native_observer_thread();
    current->alive = alive(current->object);
    current->references = references(current->object);
    current->surfaces = surfaces(current->object);
    current->observed = OS::get_singleton()->get_ticks_usec();
    current->order = ++order;
}
struct ObservationScope {
    ObservationScope() { cairn::retirement_control_before_end = before_endpoint; }
    ~ObservationScope() { cairn::retirement_control_before_end = nullptr; current = nullptr; }
};
String number(uint64_t n) { return String::num_uint64(n); }
Variant optional(int value) { return value < 0 ? Variant() : Variant(int64_t(value)); }
Ref<Mesh> empty_array() {
    Ref<ArrayMesh> mesh; mesh.instantiate();
    mesh->get_rid(); // Exercise an allocated empty resource, not only an unallocated wrapper.
    return mesh;
}
Ref<Mesh> two_surfaces() {
    Ref<ArrayMesh> mesh; mesh.instantiate();
    PackedVector3Array vertices;
    vertices.push_back(Vector3(0,0,0)); vertices.push_back(Vector3(1,0,0)); vertices.push_back(Vector3(0,1,0));
    Array arrays; arrays.resize(Mesh::ARRAY_MAX); arrays[Mesh::ARRAY_VERTEX] = vertices;
    mesh->add_surface_from_arrays(Mesh::PRIMITIVE_TRIANGLES,arrays);
    mesh->add_surface_from_arrays(Mesh::PRIMITIVE_TRIANGLES,arrays);
    return mesh;
}
}

Dictionary CairnProbe::retirement_controls() {
    Dictionary result;
    result["schema"] = "cairn-mesh-retirement-controls-1";
    result["passed"] = false; result["qualified"] = false; result["status"] = "unavailable";
    // The endpoint hook is never armed by ordinary gameplay or another fixture.
    if (!Thread::is_main_thread() || used || observer || preparation ||
            cairn::retirement_control_before_end || cairn::operations.active_phase() != 0) return result;
    const Dictionary initial = snapshot();
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs","retired_meshes"})
        if (int64_t(initial[key]) != 0) return result;
    used = true;
    const uint64_t begin = OS::get_singleton()->get_ticks_usec();
    result["fixture_start_usec"] = number(begin); result["fixture_limit_usec"] = "5000000";
    result["process_start"] = cpu_cycle_observation();
    result["thread"] = number(cairn::native_observer_thread()); result["native_start"] = initial;
    result["wire_case_cap"] = 10;
    configure(1,false);
    Array cases;
    bool ok = true;
    {
        ObservationScope observation;
        auto record = [&](const char *name, const char *entry, ObjectID id, uint32_t injected,
                bool expected_endpoint_alive, bool expected_after_alive, bool expected_postpone,
                uint32_t expected_calls, auto call) {
            Dictionary row;
            row["name"] = name; row["entry"] = entry; row["object_id"] = number(uint64_t(id));
            row["object_alive_before_call"] = alive(id);
            row["references_before_call"] = optional(references(id));
            row["surfaces_before_call"] = optional(surfaces(id));
            auto *resource = id.is_valid() ? ObjectDB::get_instance<Mesh>(id) : nullptr;
            row["mesh_rid_valid_before_call"] = resource ? Variant(resource->get_rid().is_valid()) : Variant();
            ok = ok && (!resource || bool(row["mesh_rid_valid_before_call"]));
            row["injected_admission_charge_usec"] = int64_t(injected);
            // Each attempt is a new native frame. The one declared injected
            // admission precondition is not fabricated elapsed work.
            cairn::begin_frame();
            begin_phase(100+cases.size(),true);
            cairn::frame_upload_usec = injected;
            row["charge_before_usec"] = int64_t(cairn::frame_upload_usec);
            EndpointWitness witness; witness.object = id; current = &witness;
            row["call_begin_order"] = number(++order);
            row["call_begin_usec"] = number(OS::get_singleton()->get_ticks_usec());
            zylann::TimeSpreadTaskContext context;
            call(context);
            row["call_end_usec"] = number(OS::get_singleton()->get_ticks_usec());
            row["call_end_order"] = number(++order);
            current = nullptr;
            row["object_alive_after_call"] = alive(id);
            row["references_after_call"] = optional(references(id));
            row["surfaces_after_call"] = optional(surfaces(id));
            row["postpone"] = context.postpone;
            row["endpoint_calls"] = int64_t(witness.calls);
            row["endpoint_object_alive"] = witness.calls ? Variant(witness.alive) : Variant();
            row["endpoint_references"] = optional(witness.references);
            row["endpoint_surfaces"] = optional(witness.surfaces);
            row["endpoint_observed_usec"] = witness.calls ? Variant(number(witness.observed)) : Variant();
            row["endpoint_order"] = witness.calls ? Variant(number(witness.order)) : Variant();
            row["endpoint_thread"] = witness.calls ? Variant(number(witness.thread)) : Variant();
            row["endpoint_operation_start_usec"] = witness.calls ? Variant(number(witness.start)) : Variant();
            row["endpoint_payload_bytes"] = witness.calls ? Variant(int64_t(witness.bytes)) : Variant();
            row["endpoint_surface"] = witness.calls ? Variant(witness.surface) : Variant();
            row["charge_after_usec"] = int64_t(cairn::frame_upload_usec);
            row["phase"] = end_phase(); row["frames"] = take_operation_frames();
            ok = ok && witness.calls == expected_calls && context.postpone == expected_postpone &&
                    alive(id) == expected_after_alive && (!expected_calls || witness.alive == expected_endpoint_alive);
            cases.push_back(row);
        };
        using zylann::voxel::FreeMeshTask;
        using zylann::voxel::CairnBeforeFreeMeshTask;
        {
            Ref<Mesh> mesh = empty_array(); const ObjectID id = mesh->get_instance_id();
            auto *task = CairnBeforeFreeMeshTask::cairn_control_create(mesh); mesh.unref();
            record("rejected-empty","frozen-before-run",id,0,true,false,false,1,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            ZN_DELETE(task);
        }
        {
            Ref<Mesh> mesh = empty_array(); const ObjectID id = mesh->get_instance_id();
            auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
            record("empty","FreeMeshTask::run",id,0,false,false,false,1,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            ZN_DELETE(task);
        }
        {
            Ref<Mesh> mesh = two_surfaces(); const ObjectID id = mesh->get_instance_id();
            ok = ok && surfaces(id) == 2;
            auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
            for (int index=0; index<3; ++index) {
                const char *name = index == 0 ? "surface-0" : (index == 1 ? "surface-1" : "surface-release");
                record(name,"FreeMeshTask::run",id,0,index<2,index<2,index<2,1,
                    [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            }
            ZN_DELETE(task);
        }
        {
            Ref<Mesh> external = empty_array(); const ObjectID id = external->get_instance_id();
            auto *task = FreeMeshTask::cairn_control_create(external);
            record("shared-empty","FreeMeshTask::run",id,0,true,true,false,1,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            ZN_DELETE(task);
            result["external_alive_before_release"] = alive(id);
            result["external_release_begin_usec"] = number(OS::get_singleton()->get_ticks_usec());
            external.unref();
            result["external_release_end_usec"] = number(OS::get_singleton()->get_ticks_usec());
            result["external_alive_after_release"] = alive(id); ok = ok && !alive(id);
        }
        {
            Ref<Mesh> mesh = empty_array(); const ObjectID id = mesh->get_instance_id();
            auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
            record("postponed","FreeMeshTask::run",id,251,false,true,true,0,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            record("postponed-release","FreeMeshTask::run",id,0,false,false,false,1,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            ZN_DELETE(task);
        }
        {
            Ref<PlaceholderMesh> other; other.instantiate();
            const ObjectID id = other->get_instance_id();
            auto *task = FreeMeshTask::cairn_control_create(other); other.unref();
            record("non-array","FreeMeshTask::run",id,0,false,false,false,1,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
            ZN_DELETE(task);
        }
        record("null-add","FreeMeshTask::add",ObjectID(),0,false,false,false,0,
            [&](zylann::TimeSpreadTaskContext &) { FreeMeshTask::add(Ref<Mesh>()); });
    }
    result["cases"] = cases;
    result["endpoint_hook_cleared"] = cairn::retirement_control_before_end == nullptr && current == nullptr;
    result["native_end"] = snapshot();
    const Dictionary last = result["native_end"];
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs","retired_meshes"})
        ok = ok && int64_t(last[key]) == 0;
    for (const char *key : {"generated","meshed","uploads","upload_bytes","overloads"})
        ok = ok && int64_t(last[key]) == int64_t(initial[key]);
    result["process_end"] = cpu_cycle_observation();
    const uint64_t end = OS::get_singleton()->get_ticks_usec();
    result["fixture_end_usec"] = number(end);
    result["status"] = "complete";
    result["passed"] = ok && bool(result["endpoint_hook_cleared"]) && cases.size() == 10 && end-begin <= 5000000;
    return result;
}
