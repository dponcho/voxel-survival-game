#include "../../native/sandbox_world/core/viewer_demand.h"
#include <cassert>
#include <iostream>
#include <limits>

using cairn::BlockSpan;

static void geometry_oracle(double position, double radius, int side, BlockSpan bounds) {
    BlockSpan demand;
    assert(cairn::viewer_block_span(position, radius, side, bounds, demand));
    assert(bounds.begin <= demand.begin && demand.end <= bounds.end);
    // Independent oracle: test each candidate cell's geometric intersection.
    for (int cell = bounds.begin; cell < bounds.end; ++cell) {
        const bool intersects = radius > 0 && double(cell + 1) * side > position - radius &&
            double(cell) * side < position + radius;
        assert(intersects == (demand.begin <= cell && cell < demand.end));
    }
    BlockSpan data;
    const int factor = side / 16;
    const BlockSpan data_bounds = {-32, 32};
    assert(cairn::meshing_data_span(demand, factor, data_bounds, data));
    for (int cell = data_bounds.begin; cell < data_bounds.end; ++cell) {
        bool needed = false;
        for (int mesh = demand.begin; mesh < demand.end; ++mesh)
            needed |= cell >= mesh * factor - 1 && cell < (mesh + 1) * factor + 1;
        assert(needed == (data.begin <= cell && cell < data.end));
    }
}

int main() {
    for (int side : {16, 32}) {
        for (double radius : {0.0, 1.0, 48.0, 96.0, 128.0})
            for (int step = -4096; step <= 4096; ++step)
                geometry_oracle(double(step) / 16, radius, side, {-16, 16});
        // World/slab edges, wholly out-of-bounds viewers and very large finite
        // positions exercise clipping without out-of-range float-to-int casts.
        for (double position : {-1e300, -512.125, -256.125, -16.125, -0.125, 0.0,
                10.125, 31.875, 32.0, 32.125, 255.875, 512.125, 1e300})
            for (double radius : {1.0, 96.0, 128.0})
                geometry_oracle(position, radius, side, {-16, 16});
        BlockSpan x, y, data_x;
        assert(cairn::viewer_block_span(10.125, 96, side, {-256, 256}, x));
        assert(cairn::viewer_block_span(2, 96, side, {-1, 32 / side}, y));
        const int64_t regions = int64_t(x.end - x.begin) * (x.end - x.begin) * (y.end - y.begin);
        assert(regions == (side == 16 ? 507 : 98));
        assert(regions <= 512 && regions + 128 + 4 <= 768);
        assert(cairn::viewer_block_span(10.125, 128, 16, {-512, 512}, data_x));
        assert(int64_t(data_x.end - data_x.begin) * (data_x.end - data_x.begin) * 3 <= 8192);
    }
    BlockSpan out;
    assert(cairn::viewer_block_span(10.125, 96, 32, {-128, 128}, out));
    assert(out.begin == -3 && out.end == 4); // Regression: block +3 was never requested.
    assert(cairn::viewer_block_span(-0.125, 96, 32, {-128, 128}, out));
    assert(out.begin == -4 && out.end == 3);
    assert(cairn::viewer_block_span(32, 96, 32, {-128, 128}, out));
    assert(out.begin == -2 && out.end == 4); // Exact edge does not request an extra touching cell.
    for (double invalid : {std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()}) {
        assert(!cairn::viewer_block_span(invalid, 96, 32, {-16, 16}, out) && out.empty());
        assert(!cairn::viewer_block_span(0, invalid, 32, {-16, 16}, out) && out.empty());
    }
    assert(!cairn::viewer_block_span(0, -1, 32, {-16, 16}, out));
    assert(!cairn::viewer_block_span(0, 96, 0, {-16, 16}, out));
    assert(!cairn::viewer_block_span(0, 96, 32, {16, -16}, out));
    assert(!cairn::meshing_data_span({-3, 4}, 0, {-32, 32}, out));
    assert(!cairn::meshing_data_span({4, -3}, 2, {-32, 32}, out));
    assert(cairn::meshing_data_span({0, 0}, 2, {-32, 32}, out) && out.empty());
    assert(cairn::meshing_data_span({INT32_MIN, INT32_MAX}, INT32_MAX,
        {INT32_MIN, INT32_MAX}, out));
    assert(out.begin == INT32_MIN && out.end == INT32_MAX);
    std::cout << "World-space viewer demand and meshing halo checks passed\n";
}
