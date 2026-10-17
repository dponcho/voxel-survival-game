#include "benchmark_probe.h"
#include "../core/cycle_observation.h"
#include "core/crypto/crypto_core.h"
#include "core/os/os.h"
#include "core/os/thread.h"
#include <cstring>
#ifdef WINDOWS_ENABLED
#include <windows.h>
#endif

namespace {
uint64_t wall() { return OS::get_singleton()->get_ticks_usec(); }
String decimal(uint64_t n) { return String(cairn::cycle_decimal(n).c_str()); }

cairn::CycleValue process_value(bool invalid = false) {
#ifdef WINDOWS_ENABLED
    ULONG64 value = 0;
    const BOOL ok = QueryProcessCycleTime(invalid ? nullptr : GetCurrentProcess(), &value);
    const DWORD error = ok ? ERROR_SUCCESS : GetLastError();
    return {true, ok != FALSE, uint32_t(error), uint64_t(value)};
#else
    return {false, false, 50, 0}; // Explicit unsupported platform, never a zero observation.
#endif
}
cairn::CycleValue thread_value(bool invalid = false) {
#ifdef WINDOWS_ENABLED
    ULONG64 value = 0;
    const BOOL ok = QueryThreadCycleTime(invalid ? nullptr : GetCurrentThread(), &value);
    const DWORD error = ok ? ERROR_SUCCESS : GetLastError();
    return {true, ok != FALSE, uint32_t(error), uint64_t(value)};
#else
    return {false, false, 50, 0};
#endif
}
cairn::CycleObservation observation() {
    return cairn::observe_cycles([] { return process_value(); }, [] { return thread_value(); }, wall);
}
Dictionary value_record(const cairn::CycleValue &v) {
    Dictionary d;
    d["available"] = v.available; d["success"] = v.success; d["error"] = int64_t(v.error);
    d["cycles"] = v.available && v.success && !v.error ? Variant(decimal(v.cycles)) : Variant();
    return d;
}
Dictionary record(const cairn::CycleObservation &o) {
    Dictionary d;
    d["schema"] = "cairn-cpu-cycle-observation-1";
    d["status"] = o.status();
    d["process_api"] = "QueryProcessCycleTime"; d["thread_api"] = "QueryThreadCycleTime";
#ifdef WINDOWS_ENABLED
    d["platform"] = "windows";
    d["thread_id"] = decimal(GetCurrentThreadId());
#else
    d["platform"] = "unsupported"; d["thread_id"] = Variant();
#endif
    Array reads;
    static const char *kinds[] = {"process_lo", "thread_lo", "thread_hi", "process_hi"};
    for (size_t i = 0; i < o.reads.size(); ++i) {
        const auto &r = o.reads[i];
        Dictionary item = value_record(r.value);
        item["kind"] = kinds[i]; item["wall_before_usec"] = decimal(r.wall_before_usec);
        item["wall_after_usec"] = decimal(r.wall_after_usec); reads.push_back(item);
    }
    d["reads"] = reads;
    return d;
}
constexpr uint32_t HASH_UPDATES = 1024;
constexpr uint32_t HASH_BYTES = 4096;
constexpr uint64_t FIXTURE_LIMIT_USEC = 5000000;
struct HashWork {
    cairn::CycleObservation start, end;
    uint32_t updates = 0;
    int error = OK;
    uint8_t digest[32] = {};
    uint64_t deadline = 0;
    bool capped = false;
    uint64_t thread_id = 0;
};
void hash_work(void *data) {
    auto &w = *static_cast<HashWork *>(data);
#ifdef WINDOWS_ENABLED
    w.thread_id = GetCurrentThreadId();
#endif
    w.start = observation();
    if (std::strcmp(w.start.status(), "measured")) { w.end = w.start; return; }
    uint8_t bytes[HASH_BYTES];
    for (size_t i = 0; i < HASH_BYTES; ++i) bytes[i] = uint8_t(i % 251);
    CryptoCore::SHA256Context hash;
    w.error = hash.start();
    while (w.error == OK && w.updates < HASH_UPDATES) {
        if (wall() >= w.deadline) { w.capped = true; break; }
        w.error = hash.update(bytes, sizeof(bytes));
        if (w.error == OK) ++w.updates;
    }
    if (w.error == OK) w.error = hash.finish(w.digest);
    w.end = observation(); // Worker witness is retained before thread exit.
}
Dictionary hash_record(const HashWork &w) {
    Dictionary d;
    // record() normally labels the calling thread; these two observations were
    // captured by the worker itself, so retain its original OS identity on replay.
    Dictionary start = record(w.start), end = record(w.end);
    start["thread_id"] = decimal(w.thread_id); end["thread_id"] = decimal(w.thread_id);
    d["start"] = start; d["end"] = end; d["updates"] = int64_t(w.updates);
    d["bytes_per_update"] = int64_t(HASH_BYTES); d["expected_updates"] = int64_t(HASH_UPDATES);
    d["error"] = w.error; d["capped"] = w.capped;
    d["digest"] = String::hex_encode_buffer(w.digest, sizeof(w.digest));
    return d;
}
} // namespace

Dictionary CairnProbe::cpu_cycle_observation() const { return record(observation()); }

Dictionary CairnProbe::cpu_cycle_capability_smoke() const {
    Dictionary d;
    d["schema"] = "cairn-cpu-cycle-capability-1";
    d["passed"] = false; d["qualified"] = false; d["target_performance"] = "not_run";
    d["scope"] = "counter capability only; no cost/sensitivity/CPU-seconds inference";
    const uint64_t start = wall();
    const uint64_t deadline = start + FIXTURE_LIMIT_USEC;
    d["fixture_start_usec"] = decimal(start); d["fixture_limit_usec"] = decimal(FIXTURE_LIMIT_USEC);
    if (!Thread::is_main_thread()) { d["reason"] = "main thread required"; return d; }
    const auto first = observation(); d["first"] = record(first);
    if (std::strcmp(first.status(), "measured")) {
        d["reason"] = first.status(); d["fixture_end_usec"] = decimal(wall()); return d;
    }
    Array exact;
    for (uint64_t n : {uint64_t(0), uint64_t(9007199254740993ULL), uint64_t(9223372036854775808ULL), UINT64_MAX})
        exact.push_back(decimal(n));
    d["decimal_controls"] = exact;
    d["failed_process_call"] = value_record(process_value(true));
    d["failed_thread_call"] = value_record(thread_value(true));
    // Serialization/failure controls use the same production recorder, including
    // an intentionally poisoned failed output which must serialize as null.
    auto failed = first; failed.reads[0].value = {true, false, 6, UINT64_MAX};
    d["failed_control"] = record(failed);
    auto unavailable = first; unavailable.reads[0].value = {false, false, 50, UINT64_MAX};
    d["unavailable_control"] = record(unavailable);
    auto reversed = first; reversed.reads[3].value.cycles = 0; reversed.reads[0].value.cycles = 1;
    d["reversed_control"] = record(reversed);
    HashWork main; main.deadline = deadline;
    hash_work(&main); d["main_hash"] = hash_record(main);
    d["wait_start"] = record(observation());
    d["wait_requested_usec"] = "20000";
    if (wall() + 20000 < deadline) OS::get_singleton()->delay_usec(20000);
    d["wait_end"] = record(observation());
    d["worker_process_start"] = record(observation());
    HashWork worker; worker.deadline = deadline;
    Thread thread;
    bool joined = false;
    if (wall() < deadline) {
        thread.start(hash_work, &worker);
        if (thread.is_started()) { thread.wait_to_finish(); joined = true; }
    }
    // Crucially, this read follows join and the worker's termination.
    const auto after_join = observation();
    d["worker_joined"] = joined; d["worker_hash"] = hash_record(worker);
    d["worker_process_end"] = record(after_join);
    d["last"] = record(observation());
    const uint64_t end = wall(); d["fixture_end_usec"] = decimal(end);
    d["passed"] = joined && end >= start && end - start <= FIXTURE_LIMIT_USEC &&
            main.updates == HASH_UPDATES && worker.updates == HASH_UPDATES &&
            main.error == OK && worker.error == OK && !main.capped && !worker.capped &&
            std::strcmp(after_join.status(), "measured") == 0;
    // Independent exact-integer QA decides monotonicity and retained worker demand.
    return d;
}
