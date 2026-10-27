#pragma once
#include "cycle_observation.h"
#include <algorithm>
#include <array>
#include <type_traits>
#include <vector>

namespace cairn {
// Opt-in main-thread forensic evidence. No allocator, clock or renderer in the
// recorder; the adapter supplies raw same-thread reads and actual wall endpoints.
struct OperationEvent {
    uint64_t id = 0, parent = 0, completion = 0, phase = 0, frame = 0;
    uint64_t thread_begin = 0, thread_end = 0, start = 0, end = 0, bytes = 0;
    uint64_t nested = 0, charged_before = 0, charged_after = 0, commit_end = 0;
    uint64_t injected_usec = 0, phase_end = 0, frame_end = 0;
    uint64_t frame_limit = 0, frame_bytes = 0, frame_byte_limit = 0;
    uint32_t kind = 0, flags = 0; // 1 individual, 2 counter, 4 context, 8 frame time, 16 frame bytes, 32 payload.
    std::array<CycleRead, 4> reads{};
};
struct OperationWitness {
    static constexpr uint64_t CAP = 128, DEPTH = 8, OUTPUT_CAP = 256 * 1024;
    static constexpr uint32_t HEADER = 256, RECORD = 296;
    std::array<OperationEvent, CAP> records{};
    std::array<OperationEvent, DEPTH> stack{};
    uint64_t size = 0, depth = 0, attempts = 0, completed = 0, cancelled = 0;
    uint64_t selected = 0, overflow = 0, counter_errors = 0, context_errors = 0;
    uint64_t first_failure = 0, outside_usec = 0, read_calls = 0;
    std::array<uint64_t, 4> counts{}, maxima{}, max_ids{};
    bool active = false, retain_all = false;

    template<class Read>
    uint64_t begin(uint64_t start, uint64_t phase, uint64_t frame, uint64_t thread,
            uint64_t charged, Read read) {
        if (!active) return 0;
        if (depth == DEPTH) { ++context_errors; return 0; }
        const auto first = read(); ++read_calls;
        auto &r = stack[depth]; r = {};
        r.id = ++attempts; r.parent = depth ? stack[depth-1].id : 0;
        r.start = start; r.phase = phase; r.frame = frame;
        r.thread_begin = thread; r.charged_before = charged; r.reads[0] = first;
        ++depth;
        r.reads[1] = read(); ++read_calls;
        return r.id;
    }
    OperationEvent *pending(uint64_t token) {
        if (!token) return nullptr;
        if (!active || !depth || stack[depth-1].id != token) { ++context_errors; return nullptr; }
        return &stack[depth-1];
    }
    template<class Read>
    void ending(uint64_t token, uint32_t kind, uint64_t bytes, uint64_t nested,
            uint64_t dose, uint64_t phase, uint64_t frame, uint64_t thread, Read read) {
        if (auto *r = pending(token)) {
            r->reads[2] = read(); ++read_calls;
            r->kind = kind; r->bytes = bytes; r->nested = nested; r->injected_usec = dose;
            r->phase_end = phase; r->frame_end = frame; r->thread_end = thread;
            r->reads[3] = read(); ++read_calls;
        }
    }
    static uint32_t faults(const OperationEvent &r) {
        uint32_t result = r.end < r.start || !r.thread_begin || r.thread_begin != r.thread_end ||
                r.phase != r.phase_end || r.frame != r.frame_end || r.kind < 1 || r.kind > 4 ? 4 : 0;
        uint64_t wall = r.start, cycles = 0;
        for (const auto &read : r.reads) {
            const auto &v = read.value;
            if (!v.available || !v.success || v.error || v.cycles < cycles) result |= 2;
            if (read.wall_before_usec < wall || read.wall_after_usec < read.wall_before_usec ||
                    read.wall_after_usec > r.end) result |= 4;
            wall = read.wall_after_usec;
            if (v.available && v.success && !v.error) cycles = v.cycles;
        }
        return result | (r.end >= r.start && r.end-r.start > 750 ? 1 : 0) |
                (r.charged_after > r.frame_limit ? 8 : 0) | (r.frame_bytes > r.frame_byte_limit ? 16 : 0) |
                (r.kind == 1 && r.bytes > 256*1024 ? 32 : 0);
    }
    // Called AFTER the unchanged operational ending clock and single charging.
    // Its outside-bracket cost is explicitly retained, never treated as free.
    template<class Clock>
    void commit(uint64_t token, uint64_t end, uint64_t charged, uint64_t limit,
            uint64_t bytes, uint64_t byte_limit, Clock clock, bool phase_maximum = false) {
        auto *p = pending(token); if (!p) return;
        auto &r = *p; r.end = end; r.charged_after = charged;
        r.frame_limit = limit; r.frame_bytes = bytes; r.frame_byte_limit = byte_limit;
        r.completion = ++completed; r.flags = faults(r);
        counter_errors += bool(r.flags & 2); context_errors += bool(r.flags & 4);
        const bool first = !first_failure && (r.flags & 57);
        if (first) first_failure = r.id;
        bool maximum = false;
        if (r.kind >= 1 && r.kind <= 4) {
            const auto k = r.kind-1; const auto elapsed = r.end >= r.start ? r.end-r.start : 0;
            maximum = !counts[k]++ || elapsed > maxima[k]; // First tie wins.
            if (maximum) { maxima[k] = elapsed; max_ids[k] = r.id; }
        }
        const bool keep = retain_all || first || maximum || phase_maximum || (r.flags & 6);
        uint64_t index = CAP;
        if (keep) {
            ++selected;
            if (size == CAP) ++overflow;
            else { index = size++; records[index] = r; }
        }
        --depth;
        const uint64_t finish = clock();
        if (finish < end) ++context_errors;
        else outside_usec += finish-end;
        if (index < CAP) records[index].commit_end = finish;
    }
    void cancel(uint64_t token) {
        if (auto *r = pending(token)) {
            for (size_t i=0; i<2; ++i)
                if (!r->reads[i].value.available || !r->reads[i].value.success || r->reads[i].value.error) ++counter_errors;
            --depth; ++cancelled;
        }
    }
    bool good() const { return !active && !depth && !overflow && !counter_errors && !context_errors; }
};
static_assert(std::is_trivially_copyable<OperationEvent>::value, "Witness events must remain POD");
static_assert(std::is_standard_layout<OperationEvent>::value, "Witness events must remain standard layout");
static_assert(sizeof(OperationWitness) <= 64 * 1024, "Bound retained POD storage");
inline void operation_u32(std::vector<uint8_t> &out, uint32_t n) {
    for (unsigned i=0; i<4; ++i) out.push_back(uint8_t(n>>(8*i)));
}
inline void operation_u64(std::vector<uint8_t> &out, uint64_t n) {
    for (unsigned i=0; i<8; ++i) out.push_back(uint8_t(n>>(8*i)));
}
inline std::vector<uint8_t> operation_header(const OperationWitness &w) {
    std::vector<uint8_t> out{'C','A','I','R','N','O','P','1'};
    operation_u32(out,1); operation_u32(out,w.RECORD);
    for (uint64_t n : {w.CAP, w.size, w.attempts, w.completed, w.cancelled, w.selected, w.overflow,
            w.counter_errors, w.context_errors, w.first_failure, w.outside_usec, w.read_calls,
            uint64_t(sizeof(w)), uint64_t(w.retain_all), uint64_t(w.active), w.depth}) operation_u64(out,n);
    for (const auto &values : {w.counts,w.maxima,w.max_ids}) for (auto n : values) operation_u64(out,n);
    out.resize(w.HEADER,0); return out;
}
inline void operation_encode(std::vector<uint8_t> &out, const OperationEvent &r) {
    for (auto n : {r.id,r.parent,r.completion,r.phase,r.frame,r.thread_begin,r.thread_end,r.start,r.end,
            r.bytes,r.nested,r.charged_before,r.charged_after,r.commit_end,r.injected_usec,r.phase_end,r.frame_end,
            r.frame_limit,r.frame_bytes,r.frame_byte_limit})
        operation_u64(out,n);
    operation_u32(out,r.kind); operation_u32(out,r.flags);
    for (const auto &v : r.reads) {
        const bool good = v.value.available && v.value.success && !v.value.error;
        operation_u64(out,good ? v.value.cycles : 0); // Flagged null, not a measured zero.
        operation_u64(out,v.wall_before_usec); operation_u64(out,v.wall_after_usec);
        operation_u32(out,(v.value.available?1:0)|(v.value.success?2:0)); operation_u32(out,v.value.error);
    }
}
} // namespace cairn
