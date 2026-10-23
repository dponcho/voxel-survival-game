#include "../../native/sandbox_world/core/observer_disposal.h"
#include <cassert>
#include <iostream>
#include <new>
#include <thread>

template<class T> struct RefusedAllocation {
    using value_type = T;
    RefusedAllocation() = default;
    template<class U> RefusedAllocation(const RefusedAllocation<U> &) {}
    T *allocate(size_t) { throw std::bad_alloc(); }
    void deallocate(T *, size_t) {}
};
int main() {
    using namespace cairn;
    std::shared_ptr<ObserverLedger> owner;
    // Fault-injected factory allocation: absence must not manufacture a release
    // witness or measured zero. This does not simulate OS page exhaustion.
    try { owner = std::allocate_shared<ObserverLedger>(RefusedAllocation<ObserverLedger>{}); }
    catch (const std::bad_alloc &) {}
    auto absent = dispose_observer(owner,false);
    assert(!absent.present && !absent.destroyed && std::string(absent.status)=="absent");
    owner = std::make_shared<ObserverLedger>(OBSERVER_HEADER+2*OBSERVER_RECORD);
    auto storage = owner->storage();
    assert(storage.record_bytes>=2*sizeof(ObserverRecord) && storage.lane_bytes==8*8*sizeof(uint64_t));
    assert(storage.object_bytes==sizeof(ObserverLedger));
    assert(std::string(dispose_observer(owner,false).status)=="active");
    uint64_t cycles=0;
    auto read=[&] { ++cycles; return CycleRead{{true,true,0,cycles},cycles,cycles}; };
    auto token=owner->begin(CALLBACK_QUERY,1,7,1,0,read);
    assert(std::string(dispose_observer(owner,false).status)=="open_spans");
    owner->end(token,1,7,read);
    // A client can remain attached even after its actual worker has joined.
    auto attached=owner;
    std::thread worker([held=owner] { assert(held->active()); });
    worker.join();
    owner->seal();
    assert(std::string(dispose_observer(owner,true).status)=="retained_owner");
    attached.reset();
    assert(std::string(dispose_observer(owner,false).status)=="emission_missing");
    auto bytes=observer_header(*owner); observer_encode(bytes,owner->records()[0]);
    std::weak_ptr<ObserverLedger> weak=owner;
    auto released=dispose_observer(owner,true);
    assert(released.destroyed && released.strong_owners==1 && !owner && weak.expired());
    assert(released.storage.records==1 && released.storage.open_spans==0 && released.failure==OBS_OK);
    assert(bytes.size()==OBSERVER_HEADER+OBSERVER_RECORD && bytes[0]=='C' && bytes[40]==1);
    assert(!dispose_observer(owner,true).destroyed); // Repeated disposal is not another release.
    // A sealed but still-open scope must not be freed as a successful disposal.
    owner=std::make_shared<ObserverLedger>(OBSERVER_HEADER+OBSERVER_RECORD);
    owner->begin(CALLBACK_QUERY,1,7,1,0,read); owner->seal();
    assert(std::string(dispose_observer(owner,true).status)=="open_spans" && owner);
    owner.reset(); // Invalid synthetic fixture cleanup; no disposal witness claimed.
    // Counter/cap/I/O failures retain their code and prefix through destruction.
    for (uint32_t failure : {OBS_COUNTER,OBS_CAP,OBS_IO}) {
        owner=std::make_shared<ObserverLedger>(OBSERVER_HEADER+OBSERVER_RECORD);
        token=owner->begin(CALLBACK_QUERY,1,7,1,0,read); owner->end(token,1,7,read);
        if (failure==OBS_CAP) owner->begin(CALLBACK_QUERY,1,7,1,0,read);
        else owner->fail(failure);
        owner->seal();
        released=dispose_observer(owner,true);
        assert(released.destroyed && released.failure==failure && released.storage.records==1);
    }
    std::cout << "Observer disposal: active/open/foreign rejection, allocation fault, last-owner destruction, retained bytes and failed prefixes pass\n";
}
