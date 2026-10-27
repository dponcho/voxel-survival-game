#include "../../native/sandbox_world/core/observer_ledger.h"
#include <cassert>
#include <iostream>

struct Clock {
    uint64_t ticks = 100, cycles = (uint64_t(1)<<63);
    cairn::CycleRead operator()() { ++ticks; cycles += 101; return {{true,true,0,cycles},ticks,ticks}; }
};
int main() {
    using namespace cairn;
    Clock clock;
    auto read = [&] { return clock(); };
    ObserverLedger l;
    auto p = l.begin(REPORT_CLOSE,1,77,1,0,read);
    auto c = l.begin(CALLBACK_QUERY,1,77,2,11,read);
    l.end(c,1,77,read); l.end(p,1,77,read);
    assert(l.failure()==OBS_OK && l.count()==2);
    assert(l.records()[1].parent==p && l.records()[0].parent==0);
    assert(l.records()[0].reads[1].value.cycles<=l.records()[1].reads[0].value.cycles);
    assert(l.records()[1].reads[3].value.cycles<=l.records()[0].reads[2].value.cycles);
    auto lane=l.new_lane(); Clock worker;
    auto wread=[&] { return worker(); };
    auto w=l.begin(WORKER_LIFETIME,lane,88,1,0,wread);
    l.set_section(1); l.end(w,lane,88,wread);
    assert(l.records().back().start_section==0 && l.records().back().end_section==1);
    auto reused=l.new_lane(); worker.cycles=0; // Same Windows ID may belong to a later incarnation.
    w=l.begin(WORKER_LIFETIME,reused,88,1,0,wread); l.end(w,reused,88,wread);
    l.seal(); assert(l.failure()==OBS_OK);
    auto header=observer_header(l); assert(header.size()==OBSERVER_HEADER);
    std::vector<uint8_t> binary; observer_encode(binary,l.records()[0]);
    assert(binary.size()==OBSERVER_RECORD && binary[0]==1 && binary[24]==REPORT_CLOSE && binary[28]==1);
    assert(binary[71]==128); // Exact >INT64_MAX endpoint is serialized unsigned little endian.
    ObserverLedger cap(OBSERVER_HEADER+OBSERVER_RECORD);
    p=cap.begin(CALLBACK_QUERY,1,77,1,0,read); cap.end(p,1,77,read);
    assert(cap.begin(CALLBACK_QUERY,1,77,1,0,read)==0 && cap.failure()==OBS_CAP);
    cap.seal(); assert(cap.count()==1); // Retain prefix; never overwrite/drop a sample.
    ObserverLedger nesting;
    p=nesting.begin(REPORT_CLOSE,1,77,1,0,read); c=nesting.begin(CALLBACK_QUERY,1,77,1,0,read);
    nesting.end(p,1,77,read); assert(nesting.failure()==OBS_NESTING);
    nesting.end(c,1,77,read); nesting.end(p,1,77,read); nesting.seal();
    ObserverLedger owner;
    p=owner.begin(REPORT_CLOSE,1,77,1,0,read); owner.end(p,1,88,read); assert(owner.failure()==OBS_NESTING);
    ObserverLedger open;
    open.begin(REPORT_CLOSE,1,77,1,0,read); open.seal(); assert(open.failure()==OBS_OPEN && !open.records()[0].complete);
    ObserverLedger failed;
    auto poison=[] { return CycleRead{{true,false,6,UINT64_MAX},10,10}; };
    p=failed.begin(CALLBACK_QUERY,1,77,1,0,poison); failed.end(p,1,77,poison); failed.seal();
    assert(failed.failure()==OBS_COUNTER);
    binary.clear(); observer_encode(binary,failed.records()[0]);
    for (size_t i=64;i<72;++i) assert(binary[i]==0); // Flagged failure serializes a null payload.
    assert(binary[88]==1 && binary[92]==6);
    ObserverLedger reversed;
    p=reversed.begin(REPORT_CLOSE,1,77,1,0,read); clock.cycles=0;
    reversed.end(p,1,77,read); assert(reversed.failure()==OBS_COUNTER);
    ObserverLedger context;
    p=context.begin(REPORT_CLOSE,1,77,1,0,read); context.set_section(1); context.end(p,1,77,read);
    assert(context.failure()==OBS_CONTEXT);
    ObserverLedger invalid_context; invalid_context.set_section(5); assert(invalid_context.failure()==OBS_CONTEXT);
    ObserverLedger invalid_owner;
    assert(invalid_owner.begin(0,1,77,1,0,read)==0 && invalid_owner.failure()==OBS_OWNER);
    std::cout << "Observer spans: ownership, nesting, cap, failed/null endpoints, unsigned encoding, worker incarnations and context controls pass\n";
}
