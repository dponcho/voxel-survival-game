#include "../../native/sandbox_world/core/operation_witness.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace cairn;
    uint64_t now = 10, cycles = UINT64_C(9223372036854775808);
    auto read = [&] { CycleRead r{{true,true,0,cycles++},now++,now++}; return r; };
    auto clock = [&] { return now++; };
    OperationWitness w; w.active = true;
    auto event = [&](uint64_t elapsed, uint32_t kind = 1, uint64_t payload = 192) {
        const auto start = now++;
        auto token = w.begin(start,1,7,33,0,read);
        w.ending(token,kind,payload,0,0,1,7,33,read);
        now = std::max(now,start+elapsed);
        w.commit(token,now,elapsed,1000,payload,524288,clock); return token;
    };
    const auto first = event(751), second = event(900), tie = event(900);
    assert(w.first_failure == first && w.max_ids[0] == second && tie != second);
    assert(w.size == 2 && w.completed == 3 && w.selected == 2);
    const auto &r = w.records[1];
    assert(r.reads[0].value.cycles <= r.reads[1].value.cycles &&
            r.reads[1].value.cycles <= r.reads[2].value.cycles &&
            r.reads[2].value.cycles <= r.reads[3].value.cycles);
    auto bad = r; bad.thread_end = 44; assert(OperationWitness::faults(bad) & 4);
    bad = r; bad.reads[2].value = {true,false,6,UINT64_MAX};
    assert(OperationWitness::faults(bad) & 2);
    std::vector<uint8_t> encoded; operation_encode(encoded,bad);
    assert(encoded.size() == w.RECORD);
    for (size_t i=0; i<8; ++i) assert(encoded[168+2*32+i] == 0); // Failed wire counter is flagged null.
    bad = r; bad.reads[3].wall_after_usec = bad.end+1; assert(OperationWitness::faults(bad) & 4);
    bad = r; bad.frame_limit = 750; assert(OperationWitness::faults(bad) & 8);
    bad = r; bad.bytes = 262145; assert(OperationWitness::faults(bad) & 32);
    const auto parent = w.begin(now++,2,8,33,0,read);
    const auto child = w.begin(now++,2,8,33,0,read);
    w.ending(child,3,0,0,0,2,8,33,read); w.commit(child,now,10,1000,0,524288,clock);
    w.ending(parent,4,0,10,0,2,8,33,read); w.commit(parent,now,20,1000,0,524288,clock);
    assert(w.records[2].parent == parent && w.records[3].id == parent);
    auto cancelled = w.begin(now++,2,8,33,0,read); w.cancel(cancelled);
    assert(w.cancelled == 1 && !w.depth && w.attempts == w.completed+w.cancelled);
    w.retain_all = true;
    while (w.completed < 140) event(1000);
    assert(w.size == 128 && w.overflow > 0 && w.records[0].id == first && w.records[1].id == second);
    w.active = false; assert(!w.good());
    assert(operation_header(w).size() == w.HEADER && sizeof(w) <= 65536);
    OperationWitness ordinary;
    assert(ordinary.begin(0,0,0,0,0,read) == 0 && ordinary.read_calls == 0);
    std::cout << "Bounded operation witnesses, first failure/tie, nested, null counter and overflow passed\n";
}
