#include "../../native/sandbox_world/core/fixture.h"
#include <cassert>
#include <iostream>

int main() {
    for (int n : {-17, -16, -1, 0, 15, 16, 8191}) {
        const int chunk = cairn::floor_div(n, 16), local = cairn::positive_mod(n, 16);
        assert(local >= 0 && local < 16 && chunk * 16 + local == n);
    }
    assert(cairn::floor_div(-1,16) == -1);
    assert(cairn::fixture_voxel(-1,-1,-1,0) == 1);
    assert(cairn::fixture_voxel(-1,0,-1,0) == 0);
    assert(cairn::fixture_voxel(0,-8,10,1) == 0);
    for (int neighbors = 0; neighbors <= 6; ++neighbors) {
        // An isolated added cube contributes six faces, with each occupied neighbor
        // hiding one old and one new face. Removal must undo it exactly.
        assert(cairn::face_delta(false,true,neighbors) == 6 - 2*neighbors);
        assert(cairn::face_delta(true,false,neighbors) + cairn::face_delta(false,true,neighbors) == 0);
    }
    // Out-of-envelope checkerboards must be rejected before mesh allocation.
    const int checker_faces = 16 * 32 * 32 * 6;
    assert(checker_faces > cairn::MAX_FACES);
    assert(cairn::TRIANGLES_PER_UPLOAD * 3 * 68 <= 256 * 1024);
    // Cover a complete period of terraces, tunnels and dense construction at
    // negative coordinates. Reserve the worst-case six faces for every one of
    // the 64 allowed temporary edits, even if all affect the same render region.
    const int directions[6][3] = {{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    for (int fixture = 0; fixture < 3; ++fixture) {
        int maximum_faces = 0;
        for (int origin_z = -576; origin_z < 0; origin_z += 32)
            for (int origin_x = -192; origin_x < 0; origin_x += 32)
                for (int origin_y : {-32, 0}) {
                    int faces = 0;
                    for (int z = origin_z; z < origin_z + 32; ++z)
                        for (int x = origin_x; x < origin_x + 32; ++x)
                            for (int y = origin_y; y < origin_y + 32; ++y) {
                                if (cairn::fixture_voxel(x,y,z,fixture) == 0) continue;
                                for (const auto &side : directions)
                                    if (cairn::fixture_voxel(x+side[0],y+side[1],z+side[2],fixture) == 0) ++faces;
                            }
                    if (faces > maximum_faces) maximum_faces = faces;
                    assert(faces + 64 * 6 <= cairn::MAX_FACES);
                }
        std::cout << "Fixture " << fixture << " maximum region faces: " << maximum_faces << '\n';
    }
    std::cout << "M1 fixture coordinate, admission and upload-bound checks passed\n";
}
