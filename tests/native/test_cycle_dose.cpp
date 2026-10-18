#include "../../native/sandbox_world/core/cycle_dose.h"
#include <cassert>
#include <iostream>
int main() {
    uint64_t n = 17;
    for (const char *s : {"", "01", "-1", "+1", "1.0", "18446744073709551616", "9007199254740993x"})
        assert(!cairn::parse_cycle_decimal(s, n) && n == 17);
    assert(cairn::parse_cycle_decimal("18446744073709551615", n) && n == UINT64_MAX);
    assert(cairn::parse_cycle_decimal("0", n) && n == 0);
    uint64_t wall = 0, cycles = (uint64_t(1) << 63);
    auto read = [&] { cycles += 7; return cairn::CycleValue{true, true, 0, cycles}; };
    int updates = 0;
    auto hash = [&] { ++updates; return true; };
    auto clock = [&] { return ++wall; };
    auto r = cairn::cycle_dose(20, cycles, wall, read, clock, hash);
    assert(r.reached && !r.capped && r.updates == 3 && updates == 3);
    r = cairn::cycle_dose(UINT64_MAX, cycles, wall, read, clock, hash);
    assert(!r.reached && r.capped && r.updates == 512);
    r = cairn::cycle_dose(1, cycles, wall, [] { return cairn::CycleValue{true, false, 6, UINT64_MAX}; }, clock, hash);
    assert(r.counter_failed && !r.reached);
    r = cairn::cycle_dose(1, cycles, wall, [] { return cairn::CycleValue{true, true, 0, 0}; }, clock, hash);
    assert(r.counter_failed);
    r = cairn::cycle_dose(1, cycles, wall, read, clock, [] { return false; });
    assert(r.hash_failed && r.updates == 0);
    r = cairn::cycle_dose(1, cycles, 0, read, [] { return uint64_t(50000); }, hash);
    assert(r.capped && r.updates == 0);
    r = cairn::cycle_dose(0, cycles, wall, read, clock, hash);
    assert(r.updates == 0 && !r.reached && !r.capped);
    std::cout << "Exact requests, SHA-loop demand, failures and hard caps passed\n";
}
