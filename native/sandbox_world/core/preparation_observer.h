#pragma once
#include "observer_ledger.h"
#include <memory>

namespace cairn {
// Identity is installed at the real pool thread entry, including threads which
// predate publication. It never owns a session. No counter, allocation or lock.
struct PreparationThread { const void *pool = nullptr; uint64_t incarnation = 0; uint32_t index = 0, workers = 0; };
inline thread_local PreparationThread preparation_thread;
inline std::atomic<uint64_t> preparation_incarnation{0};
struct PreparationOwner {
    uint64_t incarnation = 0, thread = 0, attached = 0, retired = 0, detached = 0;
    uint32_t lane = 0, in_flight = 0;
};
struct PreparationCounts { uint64_t attempted = 0, completed = 0, overload = 0, crossing = 0; };
class PreparationSession {
public:
    std::shared_ptr<ObserverLedger> ledger;
    const void *pool;
    const uint64_t main_thread;
    std::mutex mutex;
    std::array<PreparationOwner, 7> owners{};
    std::array<PreparationCounts, 4> counts{};
    uint32_t owner_count = 0, in_flight = 0;
    bool unpublished = false, drained = false;
    void (*control_gate)(uint32_t) = nullptr; // Bounded API controls only; null in the route.
    CycleRead (*reader)() = native_observer_read;
    explicit PreparationSession(std::shared_ptr<ObserverLedger> recorder, const void *p, uint64_t main) :
            ledger(std::move(recorder)), pool(p), main_thread(main) {}
    uint32_t lane(uint64_t thread, uint64_t wall) {
        const auto &identity = preparation_thread;
        if (!pool || identity.pool != pool || !identity.incarnation || identity.index != 0 || identity.workers != 1 || thread == main_thread) {
            ledger->fail(OBS_OWNER); return 0;
        }
        for (uint32_t i = 0; i < owner_count; ++i) {
            auto &o = owners[i];
            if (o.incarnation == identity.incarnation) {
                if (o.thread != thread || o.retired || o.detached) { ledger->fail(OBS_OWNER); return 0; }
                return o.lane;
            }
            // One terrain worker: a replacement is legal only after real exit.
            if (!o.retired || (o.thread == thread && o.retired > wall)) { ledger->fail(OBS_OWNER); return 0; }
        }
        if (owner_count == owners.size()) { ledger->fail(OBS_OWNER); return 0; }
        const auto index = ledger->new_lane();
        if (!index) return 0;
        auto &o = owners[owner_count++];
        o = {identity.incarnation, thread, wall, 0, 0, index, 0};
        return index;
    }
};
// Fast disabled dispatch; publication mutex closes acquire/unpublish races.
// Only one prospective session, never a per-system pool or profiler.
inline std::atomic<bool> preparation_enabled{false};
inline std::mutex preparation_publish_mutex;
inline std::shared_ptr<PreparationSession> preparation_published;
inline bool publish_preparation(const std::shared_ptr<PreparationSession> &session) {
    std::lock_guard<std::mutex> lock(preparation_publish_mutex);
    if (preparation_published || !session || session->ledger->version() != 2) return false;
    preparation_published = session;
    preparation_enabled.store(true, std::memory_order_release);
    return true;
}
inline bool unpublish_preparation(const std::shared_ptr<PreparationSession> &session, bool drained, uint64_t wall) {
    std::lock_guard<std::mutex> publish_lock(preparation_publish_mutex);
    if (preparation_published != session || !session) return false;
    preparation_enabled.store(false, std::memory_order_release);
    preparation_published.reset();
    std::lock_guard<std::mutex> lock(session->mutex);
    session->unpublished = true; session->drained = drained && session->in_flight == 0;
    if (!session->drained) session->ledger->fail(OBS_OPEN);
    for (uint32_t i = 0; i < session->owner_count; ++i) {
        auto &o = session->owners[i];
        if (o.in_flight) session->ledger->fail(OBS_OPEN);
        else o.detached = wall;
    }
    return session->drained;
}
inline void preparation_pool_enter(const void *pool, uint32_t index, uint32_t workers = 1) {
    preparation_thread = {pool, preparation_incarnation.fetch_add(1)+1, index, workers};
}
inline void preparation_pool_exit(uint64_t thread, uint64_t wall) {
    if (preparation_enabled.load(std::memory_order_acquire)) {
        std::lock_guard<std::mutex> publish_lock(preparation_publish_mutex);
        if (preparation_published && preparation_thread.pool == preparation_published->pool) {
            auto &s = *preparation_published;
            std::lock_guard<std::mutex> lock(s.mutex);
            for (uint32_t i = 0; i < s.owner_count; ++i) {
                auto &o = s.owners[i];
                if (o.incarnation != preparation_thread.incarnation) continue;
                if (o.thread != thread || o.retired || o.in_flight) s.ledger->fail(OBS_OWNER);
                o.retired = wall;
            }
        }
    }
    preparation_thread = {};
}
class PreparationScope {
    std::shared_ptr<PreparationSession> session;
    uint64_t token = 0, thread = 0;
    uint32_t slot = 0, lane = 0, outcome = 1;
    CycleRead (*read)();
    uint64_t (*current_thread)();
public:
    explicit PreparationScope(uint32_t owner, CycleRead (*reader)() = native_observer_read,
            uint64_t (*thread_reader)() = native_observer_thread) : slot(owner), read(reader), current_thread(thread_reader) {
        if (!preparation_enabled.load(std::memory_order_acquire)) return;
        std::lock_guard<std::mutex> publish_lock(preparation_publish_mutex);
        if (!preparation_published || preparation_published->ledger->context() != 0 ||
                preparation_published->ledger->failure() != OBS_OK) return;
        session = preparation_published;
        std::lock_guard<std::mutex> lock(session->mutex);
        thread = thread_reader();
        if (reader == native_observer_read) read = session->reader;
        if (slot < 13 || slot > 16) { session->ledger->fail(OBS_OWNER); session.reset(); return; }
        ++session->counts[slot-13].attempted;
        const auto first = read();
        if (slot >= PREPARATION_ENGINE) {
            if (thread != session->main_thread || preparation_thread.pool) session->ledger->fail(OBS_OWNER);
            else lane = 1;
        } else {
            // The first raw entry stamp also brackets registration. It is not
            // used as an inferred thread total or a wall-time cycle split.
            lane = session->lane(thread, first.wall_before_usec);
        }
        if (!lane || session->ledger->failure() != OBS_OK) { session.reset(); return; }
        bool used = false;
        token = session->ledger->begin(slot,lane,thread,1,0,[&] {
            if (!used) { used = true; return first; }
            return read();
        },0);
        if (token) {
            ++session->in_flight;
            for (auto &o : session->owners) if (o.lane == lane) ++o.in_flight;
        } else session.reset();
    }
    PreparationScope(const PreparationScope &) = delete;
    PreparationScope &operator=(const PreparationScope &) = delete;
    void overload() { outcome = 2; }
    void control_entry() { if (session && token && session->control_gate) session->control_gate(slot); }
    ~PreparationScope() {
        if (!session || !token) return;
        std::lock_guard<std::mutex> lock(session->mutex);
        session->ledger->end(token,lane,current_thread(),read,outcome);
        auto &c = session->counts[slot-13];
        ++c.completed; if (outcome == 2) ++c.overload;
        if (session->ledger->context() != 0) ++c.crossing;
        --session->in_flight;
        for (auto &o : session->owners) if (o.lane == lane) --o.in_flight;
    }
};
uint64_t native_preparation_wall();
struct PreparationPoolLifetime {
    PreparationPoolLifetime(const void *pool, uint32_t index, uint32_t workers = 1) { preparation_pool_enter(pool,index,workers); }
    ~PreparationPoolLifetime() {
        if (preparation_enabled.load(std::memory_order_acquire))
            preparation_pool_exit(native_observer_thread(),native_preparation_wall());
        else preparation_thread = {};
    }
};
} // namespace cairn
