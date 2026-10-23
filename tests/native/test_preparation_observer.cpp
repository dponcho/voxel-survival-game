#include "../../native/sandbox_world/core/preparation_observer.h"
#include "../../native/sandbox_world/core/observer_disposal.h"
#include <cassert>
#include <chrono>
#include <iostream>
#include <thread>
using namespace cairn;
namespace cairn {
thread_local uint64_t test_thread = 1, test_wall = 100, test_cycles = uint64_t(1)<<63;
std::atomic<uint64_t> calls{0};
CycleRead native_observer_read() { ++calls; return {{true,true,0,++test_cycles},++test_wall,test_wall}; }
uint64_t native_observer_thread() { return test_thread; }
uint64_t native_preparation_wall() { return test_wall; }
}
int main() {
    int pool;
    const auto before = calls.load();
    { PreparationScope disabled(PREPARATION_ENGINE); }
    assert(calls == before && !preparation_published);
    auto make = [&](uint64_t cap=OBSERVER_CAP) {
        return std::make_shared<PreparationSession>(std::make_shared<ObserverLedger>(cap,2),&pool,1);
    };
    auto s = make(); assert(publish_preparation(s) && !publish_preparation(s));
    auto parent = s->ledger->begin(CALLBACK_QUERY,1,1,1,0,native_observer_read);
    { PreparationScope engine(PREPARATION_ENGINE); { PreparationScope terrain(PREPARATION_TERRAIN); } }
    s->ledger->end(parent,1,1,native_observer_read);
    assert(s->ledger->records()[1].parent==parent && s->ledger->records()[2].parent==2);
    // An actual thread entry/exit identity, then legal same-OS-TID reuse with
    // reset counters. Distinct lanes and incarnation tokens prevent aliasing.
    for (int i=0;i<2;++i) {
        std::thread t([&] {
            test_thread=2; test_wall=200+i*100;
            PreparationPoolLifetime lifetime(&pool,0);
            { PreparationScope g(PREPARATION_GENERATION); }
            { PreparationScope m(PREPARATION_MESHING); m.overload(); }
        }); t.join();
    }
    assert(s->owner_count==2 && s->owners[0].retired && s->owners[1].retired);
    assert(s->owners[0].incarnation != s->owners[1].incarnation);
    assert(s->counts[0].attempted==2 && s->counts[1].overload==2);
    assert(unpublish_preparation(s,true,500));
    auto ledger=s->ledger; s.reset(); ledger->seal();
    assert(ledger->failure()==OBS_OK && observer_header(*ledger)[7]=='2');
    assert(dispose_observer(ledger,true).destroyed);
    // Retain an admitted worker through handover; later functions are excluded.
    s=make(); assert(publish_preparation(s));
    std::atomic<bool> entered{false}, release{false};
    std::thread cross([&] {
        test_thread=2; PreparationPoolLifetime lifetime(&pool,0);
        { PreparationScope g(PREPARATION_GENERATION); entered=true; while(!release) std::this_thread::yield(); }
        { PreparationScope excluded(PREPARATION_MESHING); }
    });
    while(!entered) std::this_thread::yield();
    s->ledger->set_section(1); release=true; cross.join();
    assert(s->counts[0].crossing==1 && s->counts[1].attempted==0);
    assert(unpublish_preparation(s,true,600)); s->ledger->seal(); assert(s->ledger->failure()==OBS_OK);
    // Force the admission race: a worker has acquired its strong reference
    // after the optimistic context check, but cannot take the session lock.
    // Handover while holding that lock must exclude the call without reads.
    for (int fault=0; fault<2; ++fault) {
        s=make(); assert(publish_preparation(s));
        const auto reads_before_race=calls.load();
        std::unique_lock<std::mutex> handover(s->mutex);
        std::thread raced([&] {
            test_thread=2; PreparationPoolLifetime lifetime(&pool,0);
            { PreparationScope excluded(PREPARATION_GENERATION); }
        });
        const auto race_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(s.use_count()<3 && std::chrono::steady_clock::now()<race_deadline) std::this_thread::yield();
        assert(s.use_count()==3);
        if (fault==0) s->ledger->set_section(1);
        else s->ledger->fail(OBS_COUNTER);
        handover.unlock(); raced.join();
        assert(calls==reads_before_race && s->ledger->count()==0 && s->counts[0].attempted==0 && s->owner_count==0);
        assert(s->ledger->failure()==(fault==0 ? OBS_OK : OBS_COUNTER) && unpublish_preparation(s,true,600));
    }
    // Main section crossings and unregistered workers fail honestly.
    s=make(); assert(publish_preparation(s));
    { PreparationScope m(PREPARATION_ENGINE); s->ledger->set_section(1); }
    assert(s->ledger->failure()==OBS_CONTEXT); unpublish_preparation(s,true,600);
    s=make(); assert(publish_preparation(s));
    { PreparationScope wrong(PREPARATION_GENERATION); }
    assert(s->ledger->failure()==OBS_OWNER && s->counts[0].attempted==1); unpublish_preparation(s,true,600);
    s=make(); assert(publish_preparation(s));
    std::thread overlap([&] {
        test_thread=2; preparation_pool_enter(&pool,0); { PreparationScope g(PREPARATION_GENERATION); }
        preparation_pool_enter(&pool,0); { PreparationScope reused(PREPARATION_GENERATION); }
        preparation_thread={};
    }); overlap.join();
    assert(s->ledger->failure()==OBS_OWNER); unpublish_preparation(s,true,600);
    // Unpublish with an admitted scope retains lifetime; cannot claim disposal.
    s=make(); assert(publish_preparation(s));
    {
        PreparationScope live(PREPARATION_ENGINE);
        assert(!unpublish_preparation(s,true,600));
        assert(s->ledger->failure()==OBS_OPEN && s->in_flight==1);
    }
    assert(s->in_flight==0 && s->counts[2].completed==1);
    s=make(OBSERVER_HEADER+OBSERVER_RECORD); assert(publish_preparation(s));
    { PreparationScope m(PREPARATION_ENGINE); }
    { PreparationScope m(PREPARATION_ENGINE); }
    auto at_failure=calls.load();
    { PreparationScope stopped(PREPARATION_ENGINE); }
    assert(calls==at_failure && s->ledger->failure()==OBS_CAP && s->ledger->count()==1);
    unpublish_preparation(s,true,600); s->ledger->seal();
    s=make(); assert(publish_preparation(s));
    s->reader=[] { auto r=native_observer_read(); r.value={true,false,6,UINT64_MAX}; return r; };
    { PreparationScope counter(PREPARATION_ENGINE); }
    assert(s->ledger->failure()==OBS_COUNTER && s->ledger->records()[0].complete);
    std::vector<uint8_t> raw; observer_encode(raw,s->ledger->records()[0]);
    assert(raw[88]==1 && raw[92]==6); // Exact failed call stays flagged null.
    unpublish_preparation(s,true,600);
    s=make(); assert(publish_preparation(s));
    std::array<uint64_t,8> depth{};
    for (auto &id:depth) id=s->ledger->begin(CALLBACK_QUERY,1,1,1,0,native_observer_read);
    { PreparationScope ninth(PREPARATION_ENGINE); }
    assert(s->ledger->failure()==OBS_OWNER && s->ledger->count()==8);
    for (int i=7;i>=0;--i) s->ledger->end(depth[i],1,1,native_observer_read);
    unpublish_preparation(s,true,600);
    s=make(); assert(publish_preparation(s));
    auto foreign=std::make_unique<PreparationScope>(PREPARATION_ENGINE);
    std::thread moved([&] { test_thread=2; foreign.reset(); }); moved.join();
    assert(s->ledger->failure()==OBS_NESTING && s->ledger->storage().open_spans==1);
    unpublish_preparation(s,false,600);
    // Old version remains byte-compatible and rejects new slots.
    ObserverLedger old; assert(!old.begin(13,1,1,1,0,native_observer_read));
    assert(old.failure()==OBS_OWNER && observer_header(old)[7]=='1');
    std::cout << "Preparation ownership: real thread incarnation, nesting, crossing, prefix and lifetime controls pass\n";
}
