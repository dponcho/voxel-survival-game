#include "report_sink.h"
#include "core/io/file_access.h"
#include "core/object/class_db.h"

void CairnReportSink::_bind_methods() {
    ClassDB::bind_method(D_METHOD("start", "path"), &CairnReportSink::start);
    ClassDB::bind_method(D_METHOD("append", "text", "snapshot"), &CairnReportSink::append);
    ClassDB::bind_method(D_METHOD("finish"), &CairnReportSink::finish);
    ClassDB::bind_method(D_METHOD("has_failed"), &CairnReportSink::has_failed);
    ClassDB::bind_method(D_METHOD("get_completed"), &CairnReportSink::get_completed);
}
void CairnReportSink::start(String path) {
    finish(); stopping = false; failed = false; completed = 0;
    worker = std::thread([this, path]() {
        Ref<FileAccess> csv = FileAccess::open(path, FileAccess::WRITE);
        if (csv.is_null()) { failed = true; return; }
        for (;;) {
            Write item;
            {
                std::unique_lock<std::mutex> lock(mutex);
                wake.wait(lock, [this]() { return stopping || !queue.empty(); });
                if (queue.empty() && stopping) break;
                item = std::move(queue.front()); queue.pop_front();
            }
            if (item.snapshot) {
                Ref<FileAccess> file = FileAccess::open(path + ".proxy.tmp", FileAccess::WRITE);
                if (file.is_null()) failed = true;
                else { file->store_string(item.text); file->flush(); if (file->get_error() != OK) failed = true; }
            } else { csv->store_string(item.text); if (csv->get_error() != OK) failed = true; }
            ++completed;
        }
        csv->flush();
        if (csv->get_error() != OK) failed = true;
    });
}
bool CairnReportSink::append(String text, bool snapshot) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, snapshot}); wake.notify_one(); return true;
}
void CairnReportSink::finish() {
    { std::lock_guard<std::mutex> lock(mutex); stopping = true; }
    wake.notify_one();
    if (worker.joinable()) worker.join();
    queue.clear();
}
