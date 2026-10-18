#pragma once
#include "core/object/ref_counted.h"
#include "core/string/ustring.h"
#include "core/variant/dictionary.h"
#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <atomic>
#include <memory>
namespace cairn { class ObserverLedger; }

// One bounded disk worker shared by CSV and temporary autosave proxy writes.
class CairnReportSink : public RefCounted {
    GDCLASS(CairnReportSink, RefCounted);
    struct Write { String text; bool snapshot; bool operations; bool edits; uint32_t section = 0; };
    std::shared_ptr<cairn::ObserverLedger> observer;
    uint32_t observer_lane = 0;
    std::atomic<uint64_t> observer_qualification{0}, observer_proxy{0}, observer_qualification_bytes{0}, observer_proxy_bytes{0};
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
    void set_observer_probe(Object *probe);
    Dictionary observer_worker_snapshot() const;
    void start(String path);
    bool append(String text, bool snapshot);
    bool append_operations(String text);
    bool append_edits(String text);
    void finish();
    bool has_failed() const { return failed.load(); }
    int64_t get_completed() const { return completed.load(); }
    ~CairnReportSink() { finish(); }
};
