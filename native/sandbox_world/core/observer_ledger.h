#pragma once
#include "cycle_observation.h"
#include <atomic>
#include <limits>
#include <mutex>
#include <vector>

namespace cairn {
// A separate perturbing observer. No operational timer or cycle/time conversion.
// The fixed binary format is explicitly little endian, independent of ABI layout.
constexpr uint64_t OBSERVER_CAP = 32 * 1024 * 1024;
constexpr uint32_t OBSERVER_HEADER = 40, OBSERVER_RECORD = 192, OBSERVER_SLOTS = 12;
enum ObserverSlot : uint32_t {
    PREPARATION_QUERY = 1, CALLBACK_QUERY, FRONTIER, CALLBACK_OUTPUT,
    NATIVE_WITNESS, TICK_OUTPUT, REPORT_CLOSE, WORKER_LIFETIME,
    WORKER_QUALIFICATION, WORKER_PROXY, WORKER_FLUSH, BOUNDARY_QUERY
};
enum ObserverError : uint32_t {
    OBS_OK = 0, OBS_CAP, OBS_OWNER, OBS_NESTING, OBS_COUNTER, OBS_CONTEXT, OBS_OPEN, OBS_IO
};
struct ObserverRecord {
    uint64_t id = 0, parent = 0, thread = 0;
    uint32_t slot = 0, lane = 0, start_section = 0, end_section = 0, submitted_section = 0, complete = 0;
    uint64_t units = 0, bytes = 0;
    // Begin API entry/exit, end API entry/exit. Body excludes the enclosed API
    // bookkeeping; full includes it. Return dispatch remains disclosed overhead.
    std::array<CycleRead, 4> reads{};
};
class ObserverLedger {
    struct Lane { uint64_t thread = 0, last_wall = 0, last_cycles = 0; std::vector<uint64_t> stack; };
    mutable std::mutex mutex;
    std::array<Lane, 8> lanes{};
    std::vector<ObserverRecord> entries;
    uint64_t capacity;
    uint32_t lane_count = 1;
    std::atomic<uint32_t> section{0}, error{OBS_OK};
    std::atomic<bool> sealed{false};
    void check(Lane &owner, const CycleRead &r) {
        if (!r.value.available || !r.value.success || r.value.error || r.wall_before_usec < owner.last_wall ||
                r.wall_after_usec < r.wall_before_usec || r.value.cycles < owner.last_cycles) fail(OBS_COUNTER);
        owner.last_wall = r.wall_after_usec;
        if (r.value.available && r.value.success && !r.value.error) owner.last_cycles = r.value.cycles;
    }
public:
    explicit ObserverLedger(uint64_t cap = OBSERVER_CAP) : capacity(cap) {
        if (cap < OBSERVER_HEADER || cap > OBSERVER_CAP) { fail(OBS_CAP); capacity = OBSERVER_HEADER; }
        entries.reserve((capacity-OBSERVER_HEADER)/OBSERVER_RECORD);
        for (auto &lane : lanes) lane.stack.reserve(8);
    }
    void fail(uint32_t reason) { uint32_t expected = OBS_OK; error.compare_exchange_strong(expected, reason); }
    uint32_t failure() const { return error.load(); }
    bool active() const { return !sealed.load(); }
    uint32_t context() const { return section.load(); }
    uint32_t new_lane() {
        std::lock_guard<std::mutex> lock(mutex);
        if (sealed || lane_count == lanes.size()) { fail(OBS_OWNER); return 0; }
        return ++lane_count;
    }
    void set_section(uint32_t value) {
        if (sealed || value > 4 || value < section.load()) { fail(OBS_CONTEXT); return; }
        section = value;
    }
    template<class Read>
    uint64_t begin(uint32_t slot, uint32_t lane, uint64_t thread, uint64_t units,
            uint64_t bytes, Read read, uint32_t submitted = 5) {
        const auto first = read();
        std::lock_guard<std::mutex> lock(mutex);
        if (sealed || !lane || lane > lane_count || !thread || !slot || slot > OBSERVER_SLOTS) {
            fail(OBS_OWNER); return 0;
        }
        auto &owner = lanes[lane-1];
        if ((owner.thread && owner.thread != thread) || owner.stack.size() >= 8) { fail(OBS_OWNER); return 0; }
        if (OBSERVER_HEADER+(entries.size()+1)*OBSERVER_RECORD > capacity) { fail(OBS_CAP); return 0; }
        owner.thread = thread;
        ObserverRecord entry;
        entry.id = entries.size()+1; entry.parent = owner.stack.empty() ? 0 : owner.stack.back();
        entry.thread = thread; entry.slot = slot; entry.lane = lane;
        entry.start_section = entry.end_section = section.load();
        entry.submitted_section = submitted == 5 ? entry.start_section : submitted;
        if (entry.submitted_section > entry.start_section) fail(OBS_CONTEXT);
        entry.units = units; entry.bytes = bytes; entry.reads[0] = first;
        entries.push_back(entry); owner.stack.push_back(entry.id);
        entries.back().reads[1] = read();
        check(owner,first); check(owner,entries.back().reads[1]);
        return entry.id;
    }
    template<class Read>
    void end(uint64_t id, uint32_t lane, uint64_t thread, Read read) {
        const auto first = read();
        std::lock_guard<std::mutex> lock(mutex);
        if (sealed || !id || id > entries.size() || !lane || lane > lane_count) { fail(OBS_NESTING); return; }
        auto &owner = lanes[lane-1]; auto &entry = entries[id-1];
        if (owner.thread != thread || entry.thread != thread || entry.lane != lane ||
                owner.stack.empty() || owner.stack.back() != id || entry.complete) { fail(OBS_NESTING); return; }
        entry.reads[2] = first; owner.stack.pop_back();
        entry.end_section = section.load(); entry.complete = 1;
        entry.reads[3] = read();
        check(owner,first); check(owner,entry.reads[3]);
        uint64_t previous_wall = 0, previous_cycles = 0;
        for (const auto &r : entry.reads) {
            if (!r.value.available || !r.value.success || r.value.error ||
                    r.wall_before_usec < previous_wall || r.wall_after_usec < r.wall_before_usec ||
                    r.value.cycles < previous_cycles) fail(OBS_COUNTER);
            previous_wall = r.wall_after_usec; previous_cycles = r.value.cycles;
        }
        if (entry.end_section < entry.start_section || (lane == 1 && entry.end_section != entry.start_section)) fail(OBS_CONTEXT);
    }
    void seal() {
        std::lock_guard<std::mutex> lock(mutex);
        for (const auto &lane : lanes) if (!lane.stack.empty()) fail(OBS_OPEN);
        sealed = true;
    }
    uint64_t count() const { std::lock_guard<std::mutex> lock(mutex); return entries.size(); }
    uint32_t number_of_lanes() const { std::lock_guard<std::mutex> lock(mutex); return lane_count; }
    uint64_t cap() const { return capacity; }
    // Only after seal/join: records remain available even on honest failure.
    const std::vector<ObserverRecord> &records() const { return entries; }
};
inline void observer_u32(std::vector<uint8_t> &out, uint32_t n) { for (unsigned i=0;i<4;++i) out.push_back(uint8_t(n>>(8*i))); }
inline void observer_u64(std::vector<uint8_t> &out, uint64_t n) { for (unsigned i=0;i<8;++i) out.push_back(uint8_t(n>>(8*i))); }
inline std::vector<uint8_t> observer_header(const ObserverLedger &ledger) {
    std::vector<uint8_t> out{'C','A','I','R','N','O','B','1'};
    observer_u32(out,1); observer_u32(out,OBSERVER_RECORD); observer_u64(out,ledger.cap());
    observer_u64(out,ledger.count()); observer_u32(out,ledger.failure()); observer_u32(out,ledger.number_of_lanes());
    return out;
}
inline void observer_encode(std::vector<uint8_t> &out, const ObserverRecord &r) {
    observer_u64(out,r.id); observer_u64(out,r.parent); observer_u64(out,r.thread);
    for (uint32_t v : {r.slot,r.lane,r.start_section,r.end_section,r.submitted_section,r.complete}) observer_u32(out,v);
    observer_u64(out,r.units); observer_u64(out,r.bytes);
    for (const auto &v : r.reads) {
        const bool good = v.value.available && v.value.success && !v.value.error;
        observer_u64(out,good ? v.value.cycles : 0); // Flagged null, never a measured zero.
        observer_u64(out,v.wall_before_usec); observer_u64(out,v.wall_after_usec);
        observer_u32(out,(v.value.available?1:0)|(v.value.success?2:0)); observer_u32(out,v.value.error);
    }
}
// Implemented only by the Godot adapter. Core tests inject their own readers.
CycleRead native_observer_read();
uint64_t native_observer_thread();
} // namespace cairn
