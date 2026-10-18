#pragma once
#include "cycle_observation.h"
#include <limits>

namespace cairn {
inline bool parse_cycle_decimal(const std::string &text, uint64_t &value) {
    if (text.empty() || text.size() > 20 || (text.size() > 1 && text[0] == '0')) return false;
    uint64_t n = 0;
    for (char c : text) {
        if (c < '0' || c > '9' || n > (UINT64_MAX - uint64_t(c - '0')) / 10) return false;
        n = n * 10 + uint64_t(c - '0');
    }
    value = n;
    return true;
}
struct CycleDose {
    uint32_t updates = 0;
    bool reached = false, capped = false, counter_failed = false, hash_failed = false;
};
// SHA work, not waiting. Counters/wall and the entire loop are inside the dose
// witness. Hitting either hard cap invalidates even a just-reached request.
template <class Counter, class Clock, class Update>
CycleDose cycle_dose(uint64_t request, uint64_t initial, uint64_t begin,
        Counter counter, Clock clock, Update update) {
    CycleDose result;
    uint64_t previous = initial;
    while (request && !result.reached) {
        const uint64_t now = clock();
        if (now < begin || now - begin >= 50000 || result.updates >= 512) {
            result.capped = true; break;
        }
        if (!update()) { result.hash_failed = true; break; }
        ++result.updates;
        const CycleValue current = counter();
        if (!current.available || !current.success || current.error || current.cycles < previous) {
            result.counter_failed = true; break;
        }
        previous = current.cycles;
        result.reached = current.cycles - initial >= request;
    }
    const uint64_t end = clock();
    result.capped = result.capped || result.updates >= 512 || end < begin || end - begin > 50000;
    return result;
}
} // namespace cairn
