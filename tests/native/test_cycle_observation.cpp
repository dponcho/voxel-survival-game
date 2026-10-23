#include "../../native/sandbox_world/core/cycle_observation.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {
    using namespace cairn;
    uint64_t tick = 0, process = UINT64_MAX - 8, thread = (uint64_t(1) << 63);
    int process_calls = 0, thread_calls = 0;
    auto o = observe_cycles([&] { ++process_calls; return CycleValue{true, true, 0, ++process}; },
            [&] { ++thread_calls; return CycleValue{true, true, 0, ++thread}; }, [&] { return ++tick; });
    assert(process_calls == 2 && thread_calls == 2 && tick == 8);
    assert(!std::strcmp(o.status(), "measured"));
    assert(o.reads[0].value.cycles == UINT64_MAX - 7 && o.reads[3].value.cycles == UINT64_MAX - 6);
    assert(cycle_decimal(UINT64_MAX) == "18446744073709551615");
    assert(cycle_decimal(uint64_t(1) << 63) == "9223372036854775808");
    assert(cycle_decimal(9007199254740993ULL) == "9007199254740993");
    assert(cycle_decimal(0) == "0");
    for (size_t i = 0; i < 4; ++i) {
        auto v = o; v.reads[i].value.success = false; v.reads[i].value.error = 6;
        assert(!std::strcmp(v.status(), "failed"));
        v = o; v.reads[i].value.available = false;
        assert(!std::strcmp(v.status(), "unavailable"));
        v = o; v.reads[i].wall_before_usec = v.reads[i].wall_after_usec + 1;
        assert(!std::strcmp(v.status(), "contradictory"));
    }
    auto v = o; v.reads[3].value.cycles = 1;
    assert(!std::strcmp(v.status(), "contradictory"));
    v = o; v.reads[2].value.cycles = 1;
    assert(!std::strcmp(v.status(), "contradictory"));
    v = o; v.reads[1].wall_before_usec = 0;
    assert(!std::strcmp(v.status(), "contradictory"));
    v = observe_cycles([] { return CycleValue{true, false, 5, UINT64_MAX}; },
            [] { return CycleValue{true, true, 0, 0}; }, [&] { return ++tick; });
    assert(!std::strcmp(v.status(), "failed") && v.reads[0].value.error == 5);
    std::cout << "Cycle counter nesting, unsigned decimal, failed/unavailable/reversed controls passed\n";
}
