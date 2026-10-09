#pragma once
#include <array>
#include <cstdint>

namespace cairn {

// Main-thread-only M1 evidence. Mesh submissions are renderer commands, not scanout.
struct EditBlock {
    int32_t x = 0, y = 0, z = 0;
    uint64_t revision = 0;
    bool submitted = false;
    bool same_place(const EditBlock &other) const {
        return x == other.x && y == other.y && z == other.z;
    }
};

struct EditEvidence {
    uint64_t id = 0, accepted_usec = 0, end_usec = 0;
    int32_t x = 0, y = 0, z = 0;
    uint8_t outcome = 0, target_count = 0;
    std::array<EditBlock, 8> targets{};
};

enum EditOutcome : uint8_t { EDIT_SUBMITTED = 1, EDIT_SUPERSEDED = 2,
    EDIT_CANCELLED = 3, EDIT_TIMEOUT = 4, EDIT_UNAVAILABLE = 5 };

class EditVisibility {
public:
    static constexpr unsigned int PENDING_CAP = 64;
    static constexpr unsigned int EVENT_CAP = 128;
    static constexpr uint64_t DEADLINE_USEC = 200000;
    bool enabled = false;
    uint64_t accepted = 0, submitted = 0, superseded = 0, cancelled = 0;
    uint64_t timed_out = 0, unavailable = 0, overflow = 0, max_usec = 0;
    uint32_t pending_high_water = 0;

    void reset(bool active) {
        enabled = active; next_id = 0; current = -1; pending_count = 0;
        head = 0; event_count = 0; accepted = submitted = superseded = cancelled = 0;
        timed_out = unavailable = overflow = max_usec = 0; pending_high_water = 0;
        for (auto &slot : slots) slot.used = false;
        latency_bins.fill(0);
    }
    void begin(int32_t x, int32_t y, int32_t z, uint64_t now) {
        if (!enabled) return;
        ++accepted;
        current = -1;
        for (unsigned int i = 0; i < PENDING_CAP; ++i)
            if (slots[i].used && slots[i].e.x == x && slots[i].e.y == y && slots[i].e.z == z)
                finish(i, EDIT_SUPERSEDED, now);
        for (unsigned int i = 0; i < PENDING_CAP; ++i) if (!slots[i].used) {
            slots[i].used = true;
            slots[i].e = {};
            slots[i].e.id = ++next_id;
            slots[i].e.x = x; slots[i].e.y = y; slots[i].e.z = z;
            slots[i].e.accepted_usec = now;
            current = int(i);
            ++pending_count;
            if (pending_count > pending_high_water) pending_high_water = pending_count;
            return;
        }
        ++overflow;
    }
    void target(EditBlock target, uint64_t now) {
        if (!enabled || current < 0) return;
        // A newer revision makes the earlier visual state unobservable.
        for (unsigned int i = 0; i < PENDING_CAP; ++i) {
            if (!slots[i].used || int(i) == current) continue;
            const auto &old = slots[i].e;
            for (unsigned int j = 0; j < old.target_count; ++j) {
                if (old.targets[j].same_place(target) && old.targets[j].revision != target.revision) {
                    finish(i, EDIT_SUPERSEDED, now);
                    break;
                }
            }
        }
        auto &e = slots[current].e;
        for (unsigned int i = 0; i < e.target_count; ++i) {
            if (e.targets[i].same_place(target)) return;
        }
        if (e.target_count == e.targets.size()) { ++overflow; finish(current, EDIT_UNAVAILABLE, now); return; }
        e.targets[e.target_count++] = target;
    }
    void end(uint64_t now) {
        if (current >= 0 && slots[current].used && slots[current].e.target_count == 0)
            finish(current, EDIT_UNAVAILABLE, now);
        current = -1;
    }
    void revision_changed(EditBlock target, uint64_t now) {
        if (!enabled) return;
        for (unsigned int i = 0; i < PENDING_CAP; ++i) {
            if (!slots[i].used || int(i) == current) continue;
            const auto &e = slots[i].e;
            for (unsigned int j = 0; j < e.target_count; ++j) {
                if (e.targets[j].same_place(target) && e.targets[j].revision != target.revision) {
                    finish(i, EDIT_SUPERSEDED, now);
                    break;
                }
            }
        }
    }
    void mesh_submitted(EditBlock target, uint64_t now) {
        if (!enabled) return;
        for (unsigned int i = 0; i < PENDING_CAP; ++i) {
            if (!slots[i].used) continue;
            auto &e = slots[i].e;
            for (unsigned int j = 0; j < e.target_count; ++j) {
                auto &block = e.targets[j];
                if (block.same_place(target) && block.revision == target.revision) block.submitted = true;
            }
            bool complete = e.target_count > 0;
            for (unsigned int j = 0; j < e.target_count; ++j) complete &= e.targets[j].submitted;
            if (complete) finish(i, EDIT_SUBMITTED, now);
        }
    }
    void mesh_cancelled(EditBlock target, uint64_t now) {
        if (!enabled) return;
        for (unsigned int i = 0; i < PENDING_CAP; ++i) {
            if (!slots[i].used) continue;
            const auto &e = slots[i].e;
            for (unsigned int j = 0; j < e.target_count; ++j) {
                if (e.targets[j].same_place(target) &&
                        (target.revision == 0 || e.targets[j].revision == target.revision)) {
                    finish(i, EDIT_CANCELLED, now);
                    break;
                }
            }
        }
    }
    void tick(uint64_t now) {
        if (!enabled) return;
        for (unsigned int i = 0; i < PENDING_CAP; ++i)
            if (slots[i].used && now - slots[i].e.accepted_usec > DEADLINE_USEC)
                finish(i, EDIT_TIMEOUT, now);
    }
    void stop(uint64_t now) {
        if (!enabled) return;
        for (unsigned int i = 0; i < PENDING_CAP; ++i)
            if (slots[i].used) finish(i, EDIT_CANCELLED, now);
        current = -1; enabled = false;
    }
    bool pop(EditEvidence &out) {
        if (event_count == 0) return false;
        out = events[head];
        head = (head + 1) % EVENT_CAP;
        --event_count;
        return true;
    }
    uint32_t pending() const { return pending_count; }
    uint32_t queued() const { return event_count; }
    uint64_t p95_upper_usec() const {
        if (submitted == 0) return 0;
        uint64_t remaining = (submitted * 95 + 99) / 100;
        for (unsigned int i = 0; i < latency_bins.size(); ++i) {
            if (remaining <= latency_bins[i])
                return i + 1 == latency_bins.size() ? max_usec : uint64_t(i + 1) * 1000;
            remaining -= latency_bins[i];
        }
        return max_usec;
    }
private:
    struct Slot { bool used = false; EditEvidence e; };
    std::array<Slot, PENDING_CAP> slots{};
    std::array<EditEvidence, EVENT_CAP> events{};
    std::array<uint32_t, 1001> latency_bins{};
    uint64_t next_id = 0;
    int current = -1;
    uint32_t pending_count = 0, head = 0, event_count = 0;
    void finish(unsigned int index, EditOutcome outcome, uint64_t now) {
        auto &slot = slots[index];
        if (!slot.used) return;
        slot.e.outcome = outcome;
        slot.e.end_usec = now;
        if (outcome == EDIT_SUBMITTED) {
            ++submitted;
            const uint64_t elapsed = now - slot.e.accepted_usec;
            if (elapsed > max_usec) max_usec = elapsed;
            ++latency_bins[elapsed / 1000 < latency_bins.size() ? elapsed / 1000 : latency_bins.size() - 1];
        } else if (outcome == EDIT_SUPERSEDED) ++superseded;
        else if (outcome == EDIT_CANCELLED) ++cancelled;
        else if (outcome == EDIT_TIMEOUT) ++timed_out;
        else ++unavailable;
        if (event_count < EVENT_CAP) {
            events[(head + event_count) % EVENT_CAP] = slot.e;
            ++event_count;
        } else ++overflow;
        slot.used = false;
        --pending_count;
    }
};

} // namespace cairn
