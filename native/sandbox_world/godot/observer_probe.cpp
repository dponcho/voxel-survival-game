#include "benchmark_probe.h"
#include "report_sink.h"
#include "../core/observer_ledger.h"
#include "../core/preparation_observer.h"
#include "core/io/file_access.h"
#include "core/os/os.h"
#include "core/os/thread.h"
#ifdef WINDOWS_ENABLED
#include <windows.h>
#endif

namespace cairn {
uint64_t native_observer_thread() {
#ifdef WINDOWS_ENABLED
    return GetCurrentThreadId();
#else
    return 1; // Unsupported reads below are explicit failures, never observations.
#endif
}
CycleRead native_observer_read() {
    CycleRead r; r.wall_before_usec = OS::get_singleton()->get_ticks_usec();
#ifdef WINDOWS_ENABLED
    ULONG64 n = 0; const BOOL ok = QueryThreadCycleTime(GetCurrentThread(), &n);
    const DWORD error = ok ? ERROR_SUCCESS : GetLastError();
    r.value = {true,ok != FALSE,uint32_t(error),uint64_t(n)};
#else
    r.value = {false,false,50,0};
#endif
    r.wall_after_usec = OS::get_singleton()->get_ticks_usec(); return r;
}
}
bool CairnProbe::observer_start(const String &path) {
    if (!Thread::is_main_thread() || preparation || (observer && observer->active())) return false;
    observer = std::make_shared<cairn::ObserverLedger>(); observer_path = path;
    observer_emitted = false;
    return observer->failure() == cairn::OBS_OK;
}
void CairnProbe::observer_section(int section) {
    if (preparation) {
        if (!Thread::is_main_thread()) { observer->fail(cairn::OBS_OWNER); return; }
        std::lock_guard<std::mutex> lock(preparation->mutex);
        observer->set_section(uint32_t(section));
        return;
    }
    if (observer) observer->set_section(uint32_t(section));
}
int64_t CairnProbe::observer_begin(int slot, int64_t units, int64_t bytes) {
    if (!observer || !observer->active()) return 0;
    if (!Thread::is_main_thread() || units < 0 || bytes < 0) { observer->fail(cairn::OBS_OWNER); return 0; }
    return int64_t(observer->begin(uint32_t(slot),1,cairn::native_observer_thread(),uint64_t(units),uint64_t(bytes),cairn::native_observer_read));
}
void CairnProbe::observer_end(int64_t token) {
    if (observer && observer->active()) observer->end(uint64_t(token),1,cairn::native_observer_thread(),cairn::native_observer_read);
}
Dictionary CairnProbe::observer_status() const {
    Dictionary d;
    d["active"] = observer && observer->active();
    d["failure_code"] = int64_t(observer ? observer->failure() : cairn::OBS_OWNER);
    d["record_count"] = int64_t(observer ? observer->count() : 0);
    return d;
}
Dictionary CairnProbe::observer_finish() {
    Dictionary d; d["schema"] = "cairn-observer-ledger-1"; d["passed"] = false; d["closed"] = false;
    if (!observer || !Thread::is_main_thread() || !observer->active() || preparation) return d;
    if (observer->version() == 2) d["schema"] = "cairn-observer-ledger-2";
    observer_emitted = true;
    observer->seal();
    d["emit_start"] = cpu_cycle_observation();
    Ref<FileAccess> file = FileAccess::open(observer_path, FileAccess::WRITE);
    auto bytes = cairn::observer_header(*observer);
    if (observer->version() == 2) {
        bytes.reserve(65536+cairn::OBSERVER_RECORD);
        d["serialization_capacity_bytes"] = int64_t(bytes.capacity());
    }
    uint64_t written = 0;
    auto flush = [&] {
        if (!file.is_null() && file->store_buffer(bytes.data(),bytes.size())) written += bytes.size();
        else observer->fail(cairn::OBS_IO);
        bytes.clear();
    };
    for (const auto &r : observer->records()) {
        cairn::observer_encode(bytes,r);
        if (bytes.size() >= 65536) flush();
    }
    if (!bytes.empty()) flush();
    if (!file.is_null()) {
        file->flush(); if (file->get_error() != OK) observer->fail(cairn::OBS_IO);
        file->close(); d["closed"] = true;
    }
    d["emit_end"] = cpu_cycle_observation();
    d["file"] = observer_path.get_file(); d["trace_bytes"] = int64_t(written);
    d["cap_bytes"] = int64_t(observer->cap()); d["record_count"] = int64_t(observer->count());
    d["lane_count"] = int64_t(observer->number_of_lanes()); d["failure_code"] = int64_t(observer->failure());
    d["passed"] = observer->failure() == cairn::OBS_OK && written == cairn::OBSERVER_HEADER+observer->count()*cairn::OBSERVER_RECORD;
    return d;
}
Dictionary CairnProbe::observer_controls(const String &path) {
    Dictionary d; d["passed"] = false; d["qualified"] = false;
    const uint64_t begin = OS::get_singleton()->get_ticks_usec();
    if (!observer_start(path)) return d;
    const auto process_start = cpu_cycle_observation();
    const auto parent = observer_begin(cairn::REPORT_CLOSE,1,0);
    const auto child = observer_begin(cairn::CALLBACK_QUERY,1,0);
    snapshot(); observer_end(child);
    Ref<CairnReportSink> sink; sink.instantiate(); sink->set_observer_probe(this);
    sink->start(path+".csv");
    const bool qualification = sink->append("observer control\n",false);
    const bool proxy = sink->append("proxy\n",true);
    sink->finish(); observer_end(parent);
    const auto process_end = cpu_cycle_observation();
    observer_section(4);
    const Dictionary ledger = observer_finish();
    d["ledger"] = ledger; d["process_start"] = process_start; d["process_end"] = process_end;
    d["worker_joined"] = true; d["worker_completed"] = sink->get_completed();
    d["elapsed_usec"] = int64_t(OS::get_singleton()->get_ticks_usec()-begin);
    d["passed"] = bool(ledger["passed"]) && qualification && proxy && !sink->has_failed() &&
            sink->get_completed() == 2 && OS::get_singleton()->get_ticks_usec()-begin <= 5000000;
    return d;
}
