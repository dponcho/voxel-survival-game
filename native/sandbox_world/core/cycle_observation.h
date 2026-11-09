#pragma once
#include <array>
#include <cstdint>
#include <string>

namespace cairn {
// No elapsed/cycle conversion, signed cast, or floating-point storage here.
struct CycleValue {
    bool available = false;
    bool success = false;
    uint32_t error = 0;
    uint64_t cycles = 0; // Meaningful only on a successful call.
};
struct CycleRead {
    CycleValue value;
    uint64_t wall_before_usec = 0, wall_after_usec = 0;
};
struct CycleObservation {
    // Nested order: process low, thread low, thread high, process high.
    std::array<CycleRead, 4> reads;
    const char *status() const {
        for (const auto &r : reads) if (!r.value.available) return "unavailable";
        for (const auto &r : reads) if (!r.value.success || r.value.error) return "failed";
        for (size_t i = 0; i < reads.size(); ++i) {
            if (reads[i].wall_before_usec > reads[i].wall_after_usec ||
                    (i && reads[i - 1].wall_after_usec > reads[i].wall_before_usec)) return "contradictory";
        }
        if (reads[0].value.cycles > reads[3].value.cycles ||
                reads[1].value.cycles > reads[2].value.cycles) return "contradictory";
        return "measured";
    }
};
template <class Process, class CurrentThread, class Clock>
CycleObservation observe_cycles(Process process, CurrentThread thread, Clock clock) {
    CycleObservation result;
    for (size_t i = 0; i < result.reads.size(); ++i) {
        auto &r = result.reads[i];
        r.wall_before_usec = clock();
        r.value = (i == 0 || i == 3) ? process() : thread();
        r.wall_after_usec = clock();
    }
    return result;
}
inline std::string cycle_decimal(uint64_t value) { return std::to_string(value); }
} // namespace cairn
