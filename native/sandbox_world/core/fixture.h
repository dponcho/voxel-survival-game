#pragma once
#include <cstdint>

namespace cairn {
// M1 fixtures only: no released world generator or save format.
inline int floor_div(int n, int d) { return n / d - (n % d < 0); }
inline int positive_mod(int n, int d) { return n - floor_div(n, d) * d; }
inline uint16_t full_height_fixture_voxel(int x, int y, int z) {
    // Separate M1 fixture v1, not a change to the older slab or a save generator.
    if (y < -64 || y >= 192) return 0;
    const bool route = positive_mod(x - 8, 48) < 5 || positive_mod(z - 8, 48) < 5;
    const int terrace = positive_mod(floor_div(x, 32) + floor_div(z, 48), 3);
    const int height = route ? 64 : 64 + terrace * 2;
    if (y >= height) return 0;
    // Four vertically separated tunnel levels; the bottom two layers stay solid.
    if (y >= -62 && y < height - 8 && positive_mod(y + 48, 32) < 5 &&
            (positive_mod(x, 32) < 5 || positive_mod(z, 32) < 5)) return 0;
    return y == height - 1 ? 2 : 1;
}
inline uint16_t fixture_voxel(int x, int y, int z, int fixture) {
    if (fixture == 3) return full_height_fixture_voxel(x, y, z);
    if (y < -16 || y >= 32) return 0;
    if (fixture == 0) return y < 0 ? 1 : 0;
    const int terrace = positive_mod(floor_div(x, 32) + floor_div(z, 48), 3);
    // A traversable measured route through representative surrounding terrain.
    const int height = positive_mod(z - 8, 48) < 5 ? 0 : terrace * 2;
    if (y >= height) {
        // Repeated bounded construction fixtures. No per-voxel scene objects.
        if (fixture == 2 && y < height + 8 && positive_mod(x, 64) < 16 &&
                positive_mod(z, 64) < 16 &&
                (positive_mod(x, 4) == 0 || positive_mod(z, 4) == 0 || y == height + 7)) return 2;
        return 0;
    }
    // Intersecting five-metre tunnels and occasional surface openings.
    if (y >= -11 && y <= -6 && (positive_mod(x, 24) < 5 || positive_mod(z, 24) < 5)) return 0;
    if (positive_mod(x, 48) < 4 && positive_mod(z, 48) < 4 && y >= -11) return 0;
    return y >= height - 1 ? 2 : 1;
}
inline int face_delta(bool before, bool after, int solid_neighbors) {
    return before == after ? 0 : (after ? 6 - 2 * solid_neighbors : 2 * solid_neighbors - 6);
}
constexpr int MAX_FACES = 16384;
constexpr int MAX_DATA_JOBS = 48;
constexpr int MAX_MESH_JOBS = 4; // Four <= 6 MiB outputs stay below 32 MiB.
constexpr int TRIANGLES_PER_UPLOAD = 1024;
}
