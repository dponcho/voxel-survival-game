#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace cairn {
struct BlockSpan {
    int32_t begin = 0, end = 0; // Half-open block coordinates.
    bool empty() const { return begin >= end; }
};

// Cover the actual world-space interval, not an interval centered on a floored
// block. Clip in floating point before narrowing to block coordinates.
inline bool viewer_block_span(double position, double radius, int32_t block_size,
        BlockSpan bounds, BlockSpan &out) {
    out = {bounds.begin, bounds.begin};
    if (!std::isfinite(position) || !std::isfinite(radius) || radius < 0 ||
            block_size <= 0 || bounds.begin > bounds.end) return false;
    if (radius == 0 || bounds.empty()) return true;
    const double first = std::floor((position - radius) / block_size);
    const double last = std::ceil((position + radius) / block_size);
    out = {int32_t(std::clamp(first, double(bounds.begin), double(bounds.end))),
        int32_t(std::clamp(last, double(bounds.begin), double(bounds.end)))};
    return true;
}

// Every demanded mesh block needs its complete data blocks and one neighbouring
// data block for the mesher's voxel halo. Empty demand must not create a halo.
inline bool meshing_data_span(BlockSpan mesh, int32_t render_to_data,
        BlockSpan bounds, BlockSpan &out) {
    out = {bounds.begin, bounds.begin};
    if (render_to_data <= 0 || mesh.begin > mesh.end || bounds.begin > bounds.end) return false;
    if (mesh.empty() || bounds.empty()) return true;
    const int64_t first = int64_t(mesh.begin) * render_to_data - 1;
    const int64_t last = int64_t(mesh.end) * render_to_data + 1;
    out = {int32_t(std::clamp(first, int64_t(bounds.begin), int64_t(bounds.end))),
        int32_t(std::clamp(last, int64_t(bounds.begin), int64_t(bounds.end)))};
    return true;
}
}
