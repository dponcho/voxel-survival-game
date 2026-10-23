#include "report_sink.h"
#include "benchmark_probe.h"
#include "../core/observer_ledger.h"
#include "core/io/file_access.h"
#include "core/object/class_db.h"

namespace {
struct ObserverScope {
    std::shared_ptr<cairn::ObserverLedger> ledger;
    uint64_t token = 0;
    uint32_t lane;
    ObserverScope(std::shared_ptr<cairn::ObserverLedger> value, uint32_t owner, uint32_t slot,
            uint64_t bytes = 0, uint32_t submitted = 5) : ledger(value), lane(owner) {
        if (ledger && ledger->active()) token = ledger->begin(slot,lane,cairn::native_observer_thread(),1,bytes,cairn::native_observer_read,submitted);
    }
    ~ObserverScope() {
        if (ledger && token) ledger->end(token,lane,cairn::native_observer_thread(),cairn::native_observer_read);
    }
};
}
void CairnReportSink::set_observer_probe(Object *object) {
    if (worker.joinable()) { failed = true; return; }
    auto *probe = Object::cast_to<CairnProbe>(object);
    observer = probe ? probe->observer_recorder() : nullptr;
}
Dictionary CairnReportSink::observer_worker_snapshot() const {
    Dictionary d; d["lane"] = int(observer_lane); d["joined"] = !worker.joinable();
    d["completed"] = int64_t(completed.load()); d["failed"] = failed.load();
    d["qualification_count"] = int64_t(observer_qualification.load()); d["proxy_count"] = int64_t(observer_proxy.load());
    d["qualification_bytes"] = int64_t(observer_qualification_bytes.load()); d["proxy_bytes"] = int64_t(observer_proxy_bytes.load());
    return d;
}

void CairnReportSink::_bind_methods() {
    ClassDB::bind_method(D_METHOD("set_observer_probe", "probe"), &CairnReportSink::set_observer_probe);
    ClassDB::bind_method(D_METHOD("observer_worker_snapshot"), &CairnReportSink::observer_worker_snapshot);
    ClassDB::bind_method(D_METHOD("start", "path"), &CairnReportSink::start);
    ClassDB::bind_method(D_METHOD("append", "text", "snapshot"), &CairnReportSink::append);
    ClassDB::bind_method(D_METHOD("append_operations", "text"), &CairnReportSink::append_operations);
    ClassDB::bind_method(D_METHOD("append_edits", "text"), &CairnReportSink::append_edits);
    ClassDB::bind_method(D_METHOD("finish"), &CairnReportSink::finish);
    ClassDB::bind_method(D_METHOD("has_failed"), &CairnReportSink::has_failed);
    ClassDB::bind_method(D_METHOD("get_completed"), &CairnReportSink::get_completed);
}
void CairnReportSink::start(String path) {
    finish(); stopping = false; failed = false; completed = 0;
    observer_qualification = 0; observer_proxy = 0; observer_qualification_bytes = 0; observer_proxy_bytes = 0;
    const auto recorder = observer && observer->active() ? observer : nullptr;
    observer_lane = recorder ? recorder->new_lane() : 0;
    const uint32_t lane = observer_lane;
    worker = std::thread([this, path, recorder, lane]() {
        ObserverScope lifetime(recorder,lane,cairn::WORKER_LIFETIME);
        Ref<FileAccess> csv = FileAccess::open(path, FileAccess::WRITE);
        Ref<FileAccess> operations = FileAccess::open(path + ".operations.csv", FileAccess::WRITE);
        Ref<FileAccess> edits = FileAccess::open(path + ".edits.jsonl", FileAccess::WRITE);
        if (csv.is_null() || operations.is_null() || edits.is_null()) { failed = true; return; }
        for (;;) {
            Write item;
            {
                std::unique_lock<std::mutex> lock(mutex);
                wake.wait(lock, [this]() { return stopping || !queue.empty(); });
                if (queue.empty() && stopping) break;
                item = std::move(queue.front()); queue.pop_front();
            }
            const uint64_t bytes = recorder ? uint64_t(item.text.utf8().length()) : 0;
            ObserverScope write(recorder,lane,item.snapshot ? cairn::WORKER_PROXY : cairn::WORKER_QUALIFICATION,bytes,item.section);
            if (item.snapshot) {
                Ref<FileAccess> file = FileAccess::open(path + ".proxy.tmp", FileAccess::WRITE);
                if (file.is_null()) failed = true;
                else { file->store_string(item.text); file->flush(); if (file->get_error() != OK) failed = true; }
            } else {
                Ref<FileAccess> output = item.edits ? edits : (item.operations ? operations : csv);
                output->store_string(item.text); if (output->get_error() != OK) failed = true;
            }
            if (recorder) {
                if (item.snapshot) { ++observer_proxy; observer_proxy_bytes += bytes; }
                else { ++observer_qualification; observer_qualification_bytes += bytes; }
            }
            ++completed;
        }
        ObserverScope flush(recorder,lane,cairn::WORKER_FLUSH);
        csv->flush();
        if (csv->get_error() != OK) failed = true;
        operations->flush();
        if (operations->get_error() != OK) failed = true;
        edits->flush();
        if (edits->get_error() != OK) failed = true;
    });
}
bool CairnReportSink::append(String text, bool snapshot) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, snapshot, false, false, observer && observer->active() ? observer->context() : 0}); wake.notify_one(); return true;
}
bool CairnReportSink::append_operations(String text) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, false, true, false, observer && observer->active() ? observer->context() : 0}); wake.notify_one(); return true;
}
bool CairnReportSink::append_edits(String text) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, false, false, true, observer && observer->active() ? observer->context() : 0}); wake.notify_one(); return true;
}
void CairnReportSink::finish() {
    { std::lock_guard<std::mutex> lock(mutex); stopping = true; }
    wake.notify_one();
    if (worker.joinable()) worker.join();
    queue.clear();
}
