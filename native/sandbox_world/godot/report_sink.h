#pragma once
#include "core/object/ref_counted.h"
#include "core/string/ustring.h"
#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <atomic>

// One bounded disk worker shared by CSV and temporary autosave proxy writes.
class CairnReportSink : public RefCounted {
    GDCLASS(CairnReportSink, RefCounted);
    struct Write { String text; bool snapshot; bool operations; bool edits; };
    std::thread worker;
    std::mutex mutex;
    std::condition_variable wake;
    std::deque<Write> queue;
    bool stopping = false;
    std::atomic<bool> failed{false};
    std::atomic<uint64_t> completed{0};
protected:
    static void _bind_methods();
public:
    void start(String path);
    bool append(String text, bool snapshot);
    bool append_operations(String text);
    bool append_edits(String text);
    void finish();
    bool has_failed() const { return failed.load(); }
    int64_t get_completed() const { return completed.load(); }
    ~CairnReportSink() { finish(); }
};
