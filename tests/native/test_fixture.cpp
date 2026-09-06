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
    assert(cairn::TRIANGLES_PER_UPLOAD * 3 * 64 <= 256 * 1024);
    std::cout << "M1 fixture coordinate, admission and upload-bound checks passed\n";
}
