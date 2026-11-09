#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace cairn {
// Main-thread-only, bounded selection over the existing pending vector. No jobs,
// revisions, resource ownership, demand or admission budgets are changed here.
constexpr size_t MESH_PENDING_CAP = 512;
struct MeshCandidate {
    int32_t x = 0, y = 0, z = 0;
    uint32_t flags = 0; // 1 valid, 2 visual owner, 4 loaded, 8 collision owner.
    uint64_t desired = 0, submitted = 0;
};
inline unsigned mesh_class(const MeshCandidate &c) {
    if ((c.flags & 6) == 6 && c.desired != c.submitted) return 0; // Current replacement first.
    if ((c.flags & 6) == 2) return 1; // Never-submitted required visuals.
    return 2;
}
inline double mesh_distance_squared(const MeshCandidate &c, const double *origin, int side) {
    const int32_t coordinates[] = {c.x, c.y, c.z};
    double sum = 0;
    for (unsigned axis = 0; axis < 3; ++axis) {
        const double begin = double(coordinates[axis]) * side;
        const double gap = std::max({begin - origin[axis], origin[axis] - (begin + side), 0.0});
        sum += gap * gap;
    }
    return sum;
}
inline bool mesh_admission_order(const MeshCandidate *pending, size_t count, const double *origin,
        int side, bool priority, uint16_t *order) {
    if (count > MESH_PENDING_CAP || (side != 16 && side != 32)) return false;
    for (unsigned axis = 0; axis < 3; ++axis) if (!std::isfinite(origin[axis])) return false;
    std::array<double, MESH_PENDING_CAP> distances{};
    for (size_t i = 0; i < count; ++i) {
        if (!(pending[i].flags & 1)) return false;
        order[i] = uint16_t(i);
        distances[i] = mesh_distance_squared(pending[i], origin, side);
        if (!std::isfinite(distances[i])) return false;
    }
    if (!priority) return true;
    // Original index breaks ties, retaining FIFO within equal urgency. Sorting
    // fixed indices avoids a heap allocation and never traverses the world map.
    std::sort(order, order + count, [&](uint16_t a, uint16_t b) {
        const unsigned ca = mesh_class(pending[a]), cb = mesh_class(pending[b]);
        if (ca != cb) return ca < cb;
        if (ca == 1 && distances[a] != distances[b]) return distances[a] < distances[b];
        return a < b;
    });
    return true;
}
struct MeshAdmissionRecord {
    uint64_t row = 0, phase = 0, start_usec = 0, end_usec = 0, decision_usec = 0;
    double origin[3]{};
    uint32_t side = 0, count = 0, admitted = 0, jobs_before = 0, jobs_after = 0;
    bool priority = false, valid = false;
    std::array<MeshCandidate, MESH_PENDING_CAP> pending{};
    std::array<uint16_t, MESH_PENDING_CAP> order{}, loads{};
};
class MeshAdmissionTrace {
public:
    static constexpr size_t CAPACITY = 64;
    MeshAdmissionRecord current;
    bool enabled = false;
    uint64_t recorded = 0, popped = 0, dropped = 0;
    size_t high_water = 0, max_pending = 0;
    void reset() {
        head = size = high_water = max_pending = 0;
        recorded = popped = dropped = 0; enabled = true;
    }
    void push() {
        if (!enabled) return;
        current.row = ++recorded;
        max_pending = std::max(max_pending, size_t(current.count));
        if (size == CAPACITY) { ++dropped; return; }
        records[(head + size) % CAPACITY] = current;
        ++size; high_water = std::max(high_water, size);
    }
    const MeshAdmissionRecord *pop() {
        if (size == 0) return nullptr;
        const MeshAdmissionRecord *result = &records[head];
        head = (head + 1) % CAPACITY; --size; ++popped;
        return result;
    }
    size_t queued() const { return size; }
private:
    std::array<MeshAdmissionRecord, CAPACITY> records{};
    size_t head = 0, size = 0;
};
static_assert(sizeof(MeshAdmissionTrace) <= 2 * 1024 * 1024, "Admission telemetry exceeded its fixed 2 MiB envelope");
}
