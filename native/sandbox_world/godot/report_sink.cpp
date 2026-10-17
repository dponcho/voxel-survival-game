#include "report_sink.h"
#include "core/io/file_access.h"
#include "core/object/class_db.h"

void CairnReportSink::_bind_methods() {
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
    worker = std::thread([this, path]() {
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
            if (item.snapshot) {
                Ref<FileAccess> file = FileAccess::open(path + ".proxy.tmp", FileAccess::WRITE);
                if (file.is_null()) failed = true;
                else { file->store_string(item.text); file->flush(); if (file->get_error() != OK) failed = true; }
            } else {
                Ref<FileAccess> output = item.edits ? edits : (item.operations ? operations : csv);
                output->store_string(item.text); if (output->get_error() != OK) failed = true;
            }
            ++completed;
        }
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
    queue.push_back({text, snapshot, false, false}); wake.notify_one(); return true;
}
bool CairnReportSink::append_operations(String text) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, false, true, false}); wake.notify_one(); return true;
}
bool CairnReportSink::append_edits(String text) {
    if (text.length() > 65536 || failed.load()) return false;
    std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
    if (!lock.owns_lock() || stopping || queue.size() >= 64) return false;
    queue.push_back({text, false, false, true}); wake.notify_one(); return true;
}
void CairnReportSink::finish() {
    { std::lock_guard<std::mutex> lock(mutex); stopping = true; }
    wake.notify_one();
    if (worker.joinable()) worker.join();
    queue.clear();
}
