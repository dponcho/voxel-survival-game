#include "benchmark_probe.h"
#include "fixture_generator.h"
#include "report_sink.h"
#include "m1_hooks.h"
#include "../core/preparation_observer.h"
#include "modules/voxel/engine/voxel_engine.h"
#include "modules/voxel/terrain/fixed_lod/voxel_terrain.h"
#include "modules/voxel/storage/voxel_buffer.h"
#include "core/os/os.h"
#include "core/os/thread.h"
#include <thread>

namespace cairn {
uint64_t native_preparation_wall() { return OS::get_singleton()->get_ticks_usec(); }
}
CairnProbe::~CairnProbe() {
    // An abandoned caller cannot leave a publisher or a hidden recorder owner.
    // In-flight scopes own their session until return. This is a failed prefix.
    if (preparation) cairn::unpublish_preparation(preparation,false,0);
}
bool CairnProbe::preparation_start(const String &path) {
    auto &engine = zylann::voxel::VoxelEngine::get_singleton();
    if (!Thread::is_main_thread() || observer || preparation || engine.get_thread_count() != 1) return false;
    const auto before = snapshot();
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs"})
        if (int64_t(before[key]) != 0) return false;
    observer = std::make_shared<cairn::ObserverLedger>(cairn::OBSERVER_CAP,2);
    observer_path = path; observer_emitted = false;
    preparation = std::make_shared<cairn::PreparationSession>(observer,engine.cairn_preparation_pool(),cairn::native_observer_thread());
    if (!cairn::publish_preparation(preparation)) { preparation.reset(); observer.reset(); return false; }
    return true;
}
Dictionary CairnProbe::preparation_finish() {
    Dictionary d; d["schema"] = "cairn-preparation-owners-1"; d["passed"] = false;
    if (!Thread::is_main_thread() || !preparation) return d;
    const auto native = snapshot();
    const int workers = zylann::voxel::VoxelEngine::get_singleton().get_thread_count();
    bool drained = workers == 1;
    for (const char *key : {"generation_jobs","mesh_jobs","result_jobs","main_jobs"})
        drained = drained && int64_t(native[key]) == 0;
    drained = drained && observer->storage().open_spans == 0;
    const bool detached = cairn::unpublish_preparation(preparation,drained,cairn::native_preparation_wall());
    {
        std::lock_guard<std::mutex> lock(preparation->mutex);
        d["main_thread"] = String::num_uint64(preparation->main_thread);
        d["unpublished"] = preparation->unpublished; d["drained"] = preparation->drained;
        d["in_flight"] = int64_t(preparation->in_flight);
        d["configured_workers"] = int64_t(workers);
        d["native_end"] = native;
        Array owners, counts;
        for (uint32_t i = 0; i < preparation->owner_count; ++i) {
            const auto &o = preparation->owners[i]; Dictionary item;
            item["lane"] = int64_t(o.lane); item["thread"] = String::num_uint64(o.thread);
            item["incarnation"] = String::num_uint64(o.incarnation);
            item["attached_usec"] = String::num_uint64(o.attached);
            item["retired_usec"] = o.retired ? Variant(String::num_uint64(o.retired)) : Variant();
            item["detached_usec"] = o.detached ? Variant(String::num_uint64(o.detached)) : Variant();
            item["in_flight"] = int64_t(o.in_flight); item["pool_joined"] = false;
            item["pool"] = "VoxelEngine.general"; item["worker_index"] = int64_t(0);
            owners.push_back(item);
        }
        for (uint32_t i = 0; i < 4; ++i) {
            const auto &c = preparation->counts[i]; Dictionary item;
            item["slot"] = int64_t(i+13); item["attempted"] = String::num_uint64(c.attempted);
            item["completed"] = String::num_uint64(c.completed); item["overload"] = String::num_uint64(c.overload);
            item["crossing"] = String::num_uint64(c.crossing); counts.push_back(item);
        }
        d["owners"] = owners; d["counts"] = counts;
        d["session_bytes"] = int64_t(sizeof(cairn::PreparationSession));
        d["passed"] = detached && observer->failure() == cairn::OBS_OK;
    }
    // Scope-held references can survive only a failed unpublish. Never seal or
    // iterate their records concurrently; retain the failure without emission.
    if (int64_t(d["in_flight"]) == 0) {
        std::weak_ptr<cairn::PreparationSession> witness = preparation;
        preparation.reset();
        d["session_destroyed"] = witness.expired();
        if (!witness.expired()) { observer->fail(cairn::OBS_OPEN); d["passed"] = false; }
    } else d["session_destroyed"] = false;
    return d;
}

namespace {
std::atomic<bool> control_waiting{false}, control_release{false}, control_timed_out{false};
uint64_t control_deadline = 0;
void crossing_gate(uint32_t slot) {
    if (slot != cairn::PREPARATION_GENERATION) return;
    control_waiting = true;
    while (!control_release && cairn::native_preparation_wall() < control_deadline) std::this_thread::yield();
    if (!control_release) control_timed_out = true;
}
void main_crossing_gate(uint32_t) { cairn::preparation_published->ledger->set_section(1); }
cairn::CycleRead failed_read() {
    auto r = cairn::native_observer_read(); r.value = {true,false,6,UINT64_MAX}; return r;
}
struct ControlTask : zylann::IThreadedTask {
    Ref<CairnFixture> fixture;
    Ref<CairnMesher> mesher;
    bool mesh;
    std::atomic<bool> *applied;
    ControlTask(Ref<CairnFixture> f, Ref<CairnMesher> m, bool build, std::atomic<bool> &done) :
            fixture(f), mesher(m), mesh(build), applied(&done) {}
    void run(zylann::ThreadedTaskContext &) override {
        zylann::voxel::VoxelBuffer voxels(zylann::voxel::VoxelBuffer::ALLOCATOR_DEFAULT);
        voxels.create(18,18,18);
        fixture->generate_block({voxels,Vector3i(0,-8,0),0});
        if (!mesh) return;
        zylann::voxel::VoxelMesher::Output output;
        mesher->build(output,{voxels}); // Real stock mesher, then real bounded splitting.
        zylann::voxel::VoxelBuffer checker(zylann::voxel::VoxelBuffer::ALLOCATOR_DEFAULT);
        checker.create(34,34,34);
        for (int z=1;z<33;++z) for (int x=1;x<33;++x) for (int y=1;y<33;++y)
            if ((x+y+z)%2 == 0) checker.set_voxel(1,x,y,z,zylann::voxel::VoxelBuffer::CHANNEL_TYPE);
        zylann::voxel::VoxelMesher::Output rejected;
        mesher->build(rejected,{checker}); // Real face guard early return.
    }
    void apply_result() override { *applied = true; }
};
}
Dictionary CairnProbe::preparation_controls(const String &path, Object *mesher_object, Object *terrain_object) {
    Dictionary d; d["passed"] = false; d["qualified"] = false;
    if (!Thread::is_main_thread()) return d;
    auto *terrain = Object::cast_to<zylann::voxel::VoxelTerrain>(terrain_object);
    if (!terrain || !terrain->is_inside_tree()) return d;
    d["terrain_in_tree"] = terrain->is_inside_tree();
    const uint64_t start = cairn::native_preparation_wall();
    control_deadline = start+5000000;
    d["fixture_start_usec"] = String::num_uint64(start); d["process_start"] = cpu_cycle_observation();
    configure(1,false);
    auto &engine = zylann::voxel::VoxelEngine::get_singleton();
    Ref<CairnFixture> fixture; fixture.instantiate();
    Ref<CairnMesher> mesher = Object::cast_to<CairnMesher>(mesher_object);
    if (mesher.is_null()) return d;
    d["native_start"] = snapshot();
    if (!preparation_start(path)) return d;
    std::atomic<bool> applied{false};
    auto wait = [&] {
        while (!applied && cairn::native_preparation_wall() < control_deadline) {
            engine.process(); std::this_thread::yield();
        }
        const bool done = applied.load();
        if (!done) engine.wait_and_clear_all_tasks(false);
        return done;
    };
    auto run = [&] {
        applied = false;
        engine.push_async_task(ZN_NEW(ControlTask(fixture,mesher,true,applied)));
        return wait();
    };
    // The script supplies a real in-tree terrain with processing disabled and
    // no viewers. Its transform/world context is valid, without route work.
    // Main scopes nest under the existing main stack.
    const auto parent = observer_begin(cairn::CALLBACK_QUERY,1,0);
    terrain->cairn_preparation_control_process();
    const bool first = run();
    observer_end(parent);
    engine.set_thread_count(1); // Real old worker exit/join and new entry, still one worker.
    const bool second = run();
    control_waiting = false; control_release = false; control_timed_out = false;
    preparation->control_gate = crossing_gate;
    applied = false;
    engine.push_async_task(ZN_NEW(ControlTask(fixture,mesher,false,applied)));
    while (!control_waiting && cairn::native_preparation_wall() < control_deadline) std::this_thread::yield();
    const bool crossing = control_waiting;
    observer_section(1); control_release = true;
    const bool third = wait();
    preparation->control_gate = nullptr;
    terrain->cairn_preparation_control_process(); // Admission is off after preparation.
    terrain->get_parent()->remove_child(terrain);
    memdelete(terrain);
    Ref<CairnReportSink> sink; sink.instantiate(); sink->set_observer_probe(this);
    sink->start(path+".csv");
    const bool queued = sink->append("preparation control\n",false) && sink->append("proxy\n",true);
    sink->finish(); d["worker"] = sink->observer_worker_snapshot(); sink->set_observer_probe(nullptr); sink.unref();
    observer_section(4);
    d["ownership"] = preparation_finish(); d["ledger"] = observer_finish(); d["release"] = observer_dispose();
    Array faults;
    for (int fault=0; fault<5; ++fault) {
        const char *names[] = {"counter","cap","owner","main_crossing","write"};
        Ref<CairnProbe> p; p.instantiate();
        if (!p->preparation_start(fault == 4 ? path+"/missing.bin" : path+"-"+names[fault])) break;
        if (fault == 0) p->preparation->reader = failed_read;
        if (fault == 1) {
            p->observer = std::make_shared<cairn::ObserverLedger>(cairn::OBSERVER_HEADER+cairn::OBSERVER_RECORD,2);
            p->preparation->ledger = p->observer;
        }
        if (fault == 3) p->preparation->control_gate = main_crossing_gate;
        if (fault == 2) {
            zylann::voxel::VoxelBuffer v(zylann::voxel::VoxelBuffer::ALLOCATOR_DEFAULT); v.create(2,2,2); fixture->generate_block({v,Vector3i(),0});
        } else engine.process();
        if (fault == 1) engine.process();
        Dictionary f; f["name"] = names[fault]; f["ownership"] = p->preparation_finish();
        f["ledger"] = p->observer_finish(); f["release"] = p->observer_dispose(); faults.push_back(f);
    }
    d["faults"] = faults;
    fixture.unref(); mesher.unref();
    d["process_end"] = cpu_cycle_observation();
    const auto end = cairn::native_preparation_wall();
    d["fixture_end_usec"] = String::num_uint64(end); d["fixture_limit_usec"] = "5000000";
    const Dictionary ledger = d["ledger"], release = d["release"];
    d["passed"] = first && second && third && crossing && !control_timed_out && queued &&
            bool(ledger["passed"]) && bool(release["disposed"]) && end <= control_deadline;
    return d;
}
