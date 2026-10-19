#include "benchmark_probe.h"
#include "report_sink.h"
#include "../core/observer_disposal.h"
#include "core/io/file_access.h"
#include "core/os/os.h"
#include "core/os/thread.h"

Dictionary CairnProbe::observer_dispose() {
    Dictionary d;
    d["schema"] = "cairn-observer-disposal-1"; d["disposed"] = false;
    d["qualified"] = false; d["status"] = "wrong_thread";
    d["storage_before"] = Variant(); d["storage_after"] = Variant();
    d["failure_code"] = Variant(); d["strong_owners"] = Variant();
    d["counter_start"] = Variant(); d["counter_end"] = Variant();
    if (!Thread::is_main_thread()) return d;
    d["counter_start"] = cpu_cycle_observation();
    const auto result = cairn::dispose_observer(observer, observer_emitted);
    if (result.destroyed) { observer_path = String(); observer_emitted = false; }
    d["counter_end"] = cpu_cycle_observation();
    d["status"] = result.status; d["disposed"] = result.destroyed;
    if (result.present) {
        Dictionary storage;
        storage["record_count"] = int64_t(result.storage.records);
        storage["lane_count"] = int64_t(result.storage.lanes);
        storage["open_spans"] = int64_t(result.storage.open_spans);
        storage["record_capacity_bytes"] = int64_t(result.storage.record_bytes);
        storage["lane_capacity_bytes"] = int64_t(result.storage.lane_bytes);
        storage["object_bytes"] = int64_t(result.storage.object_bytes);
        d["storage_before"] = storage;
        d["failure_code"] = int64_t(result.failure);
        d["strong_owners"] = int64_t(result.strong_owners);
        // Requested object/vector storage only. No OS working-set assertion.
        if (result.destroyed) d["storage_after"] = int64_t(0);
    }
    return d;
}

Dictionary CairnProbe::observer_disposal_controls(const String &path) {
    Dictionary d; d["passed"] = false; d["qualified"] = false;
    const uint64_t begin = OS::get_singleton()->get_ticks_usec();
    d["fixture_start_usec"] = String::num_uint64(begin);
    d["process_start"] = cpu_cycle_observation();
    d["absent"] = observer_dispose();
    Dictionary wrong_thread;
    std::thread rejected([&] { wrong_thread = observer_dispose(); });
    rejected.join();
    d["wrong_thread"] = wrong_thread;
    const bool started = observer_start(path);
    d["started"] = started;
    if (!started) return d;
    d["active"] = observer_dispose();
    const auto parent = observer_begin(cairn::REPORT_CLOSE,1,0);
    const auto child = observer_begin(cairn::CALLBACK_QUERY,1,0);
    d["open"] = observer_dispose();
    snapshot(); observer_end(child);
    Ref<CairnReportSink> sink; sink.instantiate(); sink->set_observer_probe(this);
    sink->start(path+".csv");
    const bool qualification = sink->append("disposal control\n",false);
    const bool proxy = sink->append("proxy\n",true);
    d["live_worker"] = sink->observer_worker_snapshot();
    d["live"] = observer_dispose();
    sink->finish(); observer_end(parent);
    const bool writer_ok = !sink->has_failed() && sink->get_completed() == 2;
    d["worker"] = sink->observer_worker_snapshot();
    observer_section(4);
    const Dictionary ledger = observer_finish();
    d["ledger"] = ledger;
    d["attached"] = observer_dispose();
    sink->set_observer_probe(nullptr);
    sink.unref();
    auto foreign_owner = observer_recorder();
    d["foreign"] = observer_dispose();
    foreign_owner.reset();
    const Dictionary released = observer_dispose();
    d["release"] = released;
    d["post_begin"] = observer_begin(cairn::CALLBACK_QUERY,1,0);
    d["post_finish"] = observer_finish();
    d["repeat"] = observer_dispose();
    Ref<FileAccess> readback = FileAccess::open(path,FileAccess::READ);
    d["readback_bytes"] = readback.is_valid() ? int64_t(readback->get_length()) : int64_t(-1);
    if (readback.is_valid()) readback->close();
    readback.unref();
    Array faults;
    for (int fault = 0; fault < 3; ++fault) {
        Ref<CairnProbe> probe; probe.instantiate();
        const String name = fault == 0 ? "counter" : (fault == 1 ? "cap" : "write");
        probe->observer_path = fault == 2 ? path+"/missing.bin" : path+"-"+name;
        probe->observer = std::make_shared<cairn::ObserverLedger>(fault == 1 ?
                cairn::OBSERVER_HEADER+cairn::OBSERVER_RECORD : cairn::OBSERVER_CAP);
        auto read = [fault] {
            auto r = cairn::native_observer_read();
            if (fault == 0) r.value = {true,false,6,UINT64_MAX}; // Injected failed output, encoded null.
            return r;
        };
        const auto token = probe->observer->begin(cairn::CALLBACK_QUERY,1,cairn::native_observer_thread(),1,0,read);
        probe->observer->end(token,1,cairn::native_observer_thread(),read);
        if (fault == 1) probe->observer->begin(cairn::CALLBACK_QUERY,1,cairn::native_observer_thread(),1,0,read);
        Dictionary item; item["name"] = name; item["ledger"] = probe->observer_finish();
        item["release"] = probe->observer_dispose();
        faults.push_back(item);
    }
    d["faults"] = faults;
    d["process_end"] = cpu_cycle_observation();
    d["fixture_end_usec"] = String::num_uint64(OS::get_singleton()->get_ticks_usec());
    d["fixture_limit_usec"] = "5000000";
    d["passed"] = bool(released["disposed"]) && bool(ledger["passed"]) && qualification && proxy &&
            writer_ok &&
            OS::get_singleton()->get_ticks_usec()-begin <= 5000000;
    return d;
}
