#include "../../native/sandbox_world/core/mesh_batch.h"
#include <cassert>
#include <iostream>
#include <vector>

static void reconstruct(cairn::IndexedMeshBatch &batch, const std::vector<int32_t> &source) {
    assert(batch.index_size() == source.size());
    for (uint32_t i = 0; i < source.size(); ++i) {
        assert(batch.index(i) >= 0 && uint32_t(batch.index(i)) < batch.vertices());
        assert(batch.source_vertex(batch.index(i)) == source[i]);
    }
}

int main() {
    cairn::IndexedMeshBatch batch(cairn::MAX_SOURCE_VERTICES);
    std::vector<int32_t> quads;
    for (uint32_t face = 0; face < cairn::MAX_BATCH_INDICES / 6; ++face)
        for (int corner : {0, 1, 2, 0, 2, 3}) quads.push_back(face * 4 + corner);
    assert(batch.build(quads.data(), quads.size()));
    reconstruct(batch, quads);
    assert(batch.vertices() == 2048);
    assert(cairn::mesh_payload_bytes(batch.vertices(), batch.index_size()) == 143360);
    assert(cairn::mesh_payload_bytes(batch.vertices(), batch.index_size()) < uint64_t(quads.size()) * 68);

    // Same source IDs in new order must not retain the preceding local mapping.
    std::vector<int32_t> seam = {5, 1, 5, 5, 2, 1};
    assert(batch.build(seam.data(), seam.size()));
    reconstruct(batch, seam);
    assert(batch.vertices() == 3 && batch.source_vertex(0) == 5);
    const int32_t negative[] = {0, 1, -1};
    const int32_t high[] = {0, 1, int32_t(cairn::MAX_SOURCE_VERTICES)};
    for (const auto *invalid : {negative, high}) {
        assert(!batch.build(invalid, 3));
        assert(batch.vertices() == 0 && batch.index_size() == 0);
        assert(batch.build(seam.data(), seam.size()));
        reconstruct(batch, seam);
    }
    assert(!batch.build(nullptr, 3));
    assert(!batch.build(seam.data(), 2));
    assert(!batch.build(seam.data(), cairn::MAX_BATCH_INDICES + 3));
    assert(batch.build(nullptr, 0) && batch.vertices() == 0);

    std::vector<int32_t> distinct(cairn::MAX_BATCH_INDICES);
    for (uint32_t i = 0; i < distinct.size(); ++i) distinct[i] = cairn::MAX_SOURCE_VERTICES - 1 - i;
    assert(batch.build(distinct.data(), distinct.size()));
    reconstruct(batch, distinct);
    assert(batch.vertices() == cairn::MAX_BATCH_INDICES);
    assert(cairn::mesh_payload_bytes(batch.vertices(), batch.index_size()) <= 256 * 1024);
    cairn::IndexedMeshBatch oversized(cairn::MAX_SOURCE_VERTICES + 1);
    assert(!oversized.build(seam.data(), seam.size()));
    cairn::IndexedMeshBatch empty(0);
    assert(empty.build(nullptr, 0) && !empty.build(seam.data(), seam.size()));
    assert(cairn::mesh_payload_bytes(1, 6) == 88); // Index count is not vertex count.
    std::cout << "Indexed mesh batch checks passed\n";
}
