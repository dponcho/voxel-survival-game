#pragma once
#include "fixture.h"
#include <array>
#include <cstdint>
#include <vector>

namespace cairn {
constexpr uint32_t MAX_BATCH_INDICES = TRIANGLES_PER_UPLOAD * 3;
constexpr uint32_t MAX_SOURCE_INDICES = MAX_FACES * 6;
constexpr uint32_t MAX_SOURCE_VERTICES = MAX_SOURCE_INDICES;

// Conservative complete M1 vertex layout (including tangent reserve), plus
// every actual 32-bit index. This is input payload, not driver allocation.
constexpr uint64_t mesh_payload_bytes(uint32_t vertices, uint32_t indices) {
    return uint64_t(vertices) * 64 + uint64_t(indices) * sizeof(int32_t);
}
static_assert(mesh_payload_bytes(MAX_BATCH_INDICES, MAX_BATCH_INDICES) <= 256 * 1024);

// Worker-local remap. Source IDs, rather than positions, preserve AO, normals,
// UV seams and material-specific attributes. Reset only vertices touched by
// the previous batch; never clear the entire source lookup for every upload.
class IndexedMeshBatch {
public:
    explicit IndexedMeshBatch(uint32_t source_vertices) :
            valid(source_vertices <= MAX_SOURCE_VERTICES),
            lookup(valid ? source_vertices : 0, -1) {}

    bool build(const int32_t *source_indices, uint32_t count) {
        clear();
        if (!valid || count > MAX_BATCH_INDICES || count % 3 != 0 ||
                (count > 0 && source_indices == nullptr)) return false;
        for (uint32_t i = 0; i < count; ++i) {
            const int32_t source = source_indices[i];
            if (source < 0 || uint32_t(source) >= lookup.size()) {
                clear();
                return false;
            }
            int32_t &local = lookup[source];
            if (local < 0) {
                local = int32_t(vertex_count++);
                sources[local] = source;
            }
            indices[i] = local;
        }
        index_count = count;
        return true;
    }
    uint32_t vertices() const { return vertex_count; }
    uint32_t index_size() const { return index_count; }
    int32_t source_vertex(uint32_t local) const { return sources[local]; }
    int32_t index(uint32_t corner) const { return indices[corner]; }

private:
    void clear() {
        for (uint32_t i = 0; i < vertex_count; ++i) lookup[sources[i]] = -1;
        vertex_count = index_count = 0;
    }
    bool valid;
    std::vector<int32_t> lookup;
    std::array<int32_t, MAX_BATCH_INDICES> sources;
    std::array<int32_t, MAX_BATCH_INDICES> indices;
    uint32_t vertex_count = 0, index_count = 0;
};
} // namespace cairn
