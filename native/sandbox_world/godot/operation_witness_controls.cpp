#include "benchmark_probe.h"
#include "m1_hooks.h"
#include "../core/observer_ledger.h"
#include "modules/voxel/terrain/free_mesh_task.h"
#include "core/object/object.h"
#include "core/os/thread.h"
#include <vector>

namespace {
uint64_t wall() { return OS::get_singleton()->get_ticks_usec(); }
String number(uint64_t n) { return String::num_uint64(n); }
bool alive(ObjectID id) { return id.is_valid() && ObjectDB::get_instance(id) != nullptr; }
Variant surfaces(ObjectID id) {
    auto *mesh = id.is_valid() ? ObjectDB::get_instance<ArrayMesh>(id) : nullptr;
    return mesh ? Variant(mesh->get_surface_count()) : Variant();
}
struct Endpoint {
    ObjectID id; uint64_t calls = 0, observed = 0; bool live = false;
};
Endpoint *endpoint = nullptr;
void before_end(uint32_t, uint64_t, bool) {
    if (!endpoint) return;
    ++endpoint->calls; endpoint->live = alive(endpoint->id); endpoint->observed = wall();
}
Ref<Mesh> empty_mesh() { Ref<ArrayMesh> mesh; mesh.instantiate(); mesh->get_rid(); return mesh; }
Array triangle() {
    PackedVector3Array vertices;
    vertices.push_back(Vector3(0,0,0)); vertices.push_back(Vector3(1,0,0)); vertices.push_back(Vector3(0,1,0));
    Array arrays; arrays.resize(Mesh::ARRAY_MAX); arrays[Mesh::ARRAY_VERTEX] = vertices; return arrays;
}
}
Dictionary CairnProbe::operation_witness_controls(const String &path) {
    Dictionary result; result["schema"] = "cairn-operation-witness-controls-1";
    result["passed"] = false; result["qualified"] = false;
    if (!Thread::is_main_thread() || observer || preparation || cairn::retirement_control_before_end ||
            cairn::operations.active_phase() || cairn::operation_witness) return result;
    const auto initial = snapshot();
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs","retired_meshes"})
        if (int64_t(initial[key]) != 0) return result;
    const uint64_t begin = wall();
    result["fixture_start_usec"] = number(begin); result["fixture_limit_usec"] = "5000000";
    result["process_start"] = cpu_cycle_observation(); result["native_start"] = initial;
    result["thread"] = number(cairn::native_observer_thread());
    // The real cap is used, with every event selected for this overflow control.
    if (!cairn::operation_witness_start(path,true)) return result;
    auto &w = *cairn::operation_witness;
    configure(1,false);
    cairn::retirement_control_before_end = before_end;
    Array cases;
    bool ok = true;
    auto record = [&](const char *name, const char *entry, ObjectID id, bool new_frame,
            uint64_t dose, uint32_t counter_fault, uint64_t injected_charge, auto call) {
        Dictionary r;
        r["name"] = name; r["entry"] = entry; r["object_id"] = number(uint64_t(id));
        r["alive_before"] = alive(id); r["surfaces_before"] = surfaces(id);
        if (new_frame) cairn::begin_frame();
        begin_phase(1000+cases.size(),true);
        if (injected_charge) cairn::frame_upload_usec = injected_charge;
        r["admission_charge_usec"] = number(injected_charge);
        r["charge_before_usec"] = number(cairn::frame_upload_usec);
        r["attempts_before"] = number(w.attempts);
        r["dose_usec"] = number(dose); r["counter_fault"] = counter_fault;
        cairn::operation_control_dose_usec = dose; cairn::operation_control_counter_fault = counter_fault;
        Endpoint observed; observed.id = id; endpoint = &observed;
        r["call_begin_usec"] = number(wall());
        zylann::TimeSpreadTaskContext ctx;
        call(ctx);
        r["call_end_usec"] = number(wall()); endpoint = nullptr;
        cairn::operation_control_dose_usec = 0; cairn::operation_control_counter_fault = 0;
        r["alive_after"] = alive(id); r["surfaces_after"] = surfaces(id);
        r["endpoint_calls"] = number(observed.calls);
        r["endpoint_alive"] = observed.calls ? Variant(observed.live) : Variant();
        r["endpoint_observed_usec"] = observed.calls ? Variant(number(observed.observed)) : Variant();
        r["postpone"] = ctx.postpone;
        r["charge_after_usec"] = number(cairn::frame_upload_usec);
        r["attempts_after"] = number(w.attempts);
        r["phase"] = end_phase(); r["frames"] = take_operation_frames();
        cases.push_back(r);
    };
    using zylann::voxel::FreeMeshTask;
    Ref<ArrayMesh> partial;
    std::vector<int> materials;
    const Array arrays = triangle();
    record("upload-first-failure","cairn::upload_surface",ObjectID(),true,2000,0,0,
        [&](zylann::TimeSpreadTaskContext &) { cairn::upload_surface(192,partial,arrays,7,materials); });
    const uint64_t first_max = w.maxima[0];
    const uint64_t second_dose = first_max+2000;
    ok = ok && first_max > 750 && second_dose <= 20000;
    record("upload-later-maximum","cairn::upload_surface",ObjectID(),true,std::min(second_dose,uint64_t(20000)),0,0,
        [&](zylann::TimeSpreadTaskContext &) { cairn::upload_surface(192,partial,arrays,9,materials); });
    ok = ok && w.maxima[0] > first_max && partial.is_valid() && partial->get_surface_count() == 2 &&
            materials == std::vector<int>({7,9}) && w.first_failure == 1 && w.max_ids[0] == 2;
    result["upload_surface_count"] = partial.is_valid() ? partial->get_surface_count() : -1;
    Array material_order; for (auto i : materials) material_order.push_back(i);
    result["upload_material_order"] = material_order;
    {
        const ObjectID id = partial->get_instance_id();
        auto *task = FreeMeshTask::cairn_control_create(partial); partial.unref();
        for (const char *name : {"surface-0","surface-1","surface-release"})
            record(name,"FreeMeshTask::run",id,true,0,0,0,
                [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
        ZN_DELETE(task); ok = ok && !alive(id);
    }
    auto release = [&](const char *name, bool new_frame, uint32_t fault, bool nested) {
        Ref<Mesh> mesh = empty_mesh(); const ObjectID id = mesh->get_instance_id();
        auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
        record(name,nested ? "completed-task-bracket/FreeMeshTask::run" : "FreeMeshTask::run",id,new_frame,0,fault,0,
            [&](zylann::TimeSpreadTaskContext &ctx) {
                if (nested) {
                    const uint64_t start = wall(), token = cairn::operation_witness_begin(start);
                    const uint64_t previous = cairn::frame_upload_usec;
                    task->run(ctx); cairn::record_data_apply(start,previous,token);
                } else task->run(ctx);
            });
        ZN_DELETE(task); ok = ok && !alive(id);
    };
    release("empty-release",true,0,false);
    {
        Ref<Mesh> external = empty_mesh(); const ObjectID id = external->get_instance_id();
        auto *task = FreeMeshTask::cairn_control_create(external);
        record("shared-empty","FreeMeshTask::run",id,true,0,0,0,
            [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
        ZN_DELETE(task); ok = ok && alive(id);
        external.unref(); result["external_alive_after_release"] = alive(id); ok = ok && !alive(id);
    }
    {
        Ref<Mesh> mesh = empty_mesh(); const ObjectID id = mesh->get_instance_id();
        auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
        record("postponed","FreeMeshTask::run",id,true,0,0,251,
            [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
        ok = ok && alive(id);
        record("resumed","FreeMeshTask::run",id,true,0,0,0,
            [&](zylann::TimeSpreadTaskContext &ctx) { task->run(ctx); });
        ZN_DELETE(task); ok = ok && !alive(id);
    }
    record("null-add","FreeMeshTask::add",ObjectID(),true,0,0,0,
        [&](zylann::TimeSpreadTaskContext &) { FreeMeshTask::add(Ref<Mesh>()); });
    release("nested-charge",true,0,true);
    release("phase-carry-normal",true,0,false);
    configure(1,true);
    release("phase-carry-heavy",false,0,false);
    configure(1,false);
    release("failed-counter",true,1,false);
    release("unavailable-counter",true,2,false);
    // A completed-task queue miss takes no operational charge. It retains the
    // cancelled attempt/read count, not an invented completed zero operation.
    cairn::begin_frame();
    const uint64_t empty_start = wall(), cancelled = cairn::operation_witness_begin(empty_start);
    cairn::operation_witness_cancel(cancelled);
    result["cancelled_charge_usec"] = number(cairn::frame_upload_usec);
    // Deterministically fill the actual 128-record cap and attempt two more
    // real releases. No trace eviction or passing truncation is allowed.
    begin_phase(2000,false);
    const uint64_t filler_begin = w.completed;
    while (w.completed < 130 && wall()-begin <= 5000000) {
        cairn::begin_frame();
        Ref<Mesh> mesh = empty_mesh(); const ObjectID id = mesh->get_instance_id();
        auto *task = FreeMeshTask::cairn_control_create(mesh); mesh.unref();
        zylann::TimeSpreadTaskContext ctx; task->run(ctx); ZN_DELETE(task);
        ok = ok && !ctx.postpone && !alive(id);
    }
    result["filler_count"] = number(w.completed-filler_begin);
    result["filler_phase"] = end_phase();
    result["filler_frames"] = take_operation_frames();
    cairn::retirement_control_before_end = nullptr; endpoint = nullptr;
    result["cases"] = cases;
    result["hooks_cleared"] = !cairn::retirement_control_before_end &&
            !cairn::operation_control_dose_usec && !cairn::operation_control_counter_fault;
    result["witness"] = cairn::operation_witness_finish(*this);
    const Dictionary witness = result["witness"];
    result["native_end"] = snapshot(); const Dictionary last = result["native_end"];
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs","retired_meshes"})
        ok = ok && int64_t(last[key]) == 0;
    for (const char *key : {"generated","meshed","overloads"}) ok = ok && int64_t(last[key]) == int64_t(initial[key]);
    result["process_end"] = cpu_cycle_observation();
    const uint64_t end = wall(); result["fixture_end_usec"] = number(end);
    result["passed"] = ok && bool(result["hooks_cleared"]) && bool(witness["passed"]) &&
            !bool(witness["integrity_passed"]) && w.size == 128 && w.completed == 130 && w.overflow == 2 &&
            w.counter_errors == 2 && !w.context_errors && w.cancelled == 1 && !cairn::operation_witness &&
            cases.size() == 15 && end-begin <= 5000000;
    return result;
}
