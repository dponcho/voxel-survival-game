#pragma once
#include "observer_ledger.h"
#include <memory>

namespace cairn {
struct ObserverDisposal {
    const char *status = "absent";
    bool present = false, destroyed = false;
    uint64_t strong_owners = 0;
    uint32_t failure = OBS_OK;
    ObserverStorage storage;
};
// Main-owner operation only. Stop publishers and join/detach clients first.
// No waiting, implicit sealing, error clearing or evidence emission here.
inline ObserverDisposal dispose_observer(std::shared_ptr<ObserverLedger> &owner, bool emitted) {
    ObserverDisposal result;
    if (!owner) return result;
    result.present = true; result.strong_owners = owner.use_count();
    result.storage = owner->storage(); result.failure = owner->failure();
    if (result.strong_owners != 1) result.status = "retained_owner";
    else if (result.storage.open_spans) result.status = "open_spans";
    else if (owner->active()) result.status = "active";
    else if (!emitted) result.status = "emission_missing";
    else {
        // The weak witness owns only the shared control block, never the ledger
        // or its vectors. reset() runs their destructors before expired().
        std::weak_ptr<ObserverLedger> witness = owner;
        owner.reset();
        result.destroyed = witness.expired();
        result.status = result.destroyed ? "disposed" : "retained_owner";
    }
    return result;
}
}
