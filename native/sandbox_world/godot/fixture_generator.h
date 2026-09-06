#pragma once
#include "modules/voxel/generators/voxel_generator.h"
#include "modules/voxel/meshers/blocky/voxel_mesher_blocky.h"

class CairnFixture : public zylann::voxel::VoxelGenerator {
    GDCLASS(CairnFixture, zylann::voxel::VoxelGenerator);
    int fixture = 0;
protected:
    static void _bind_methods();
public:
    void set_fixture(int value) { fixture = CLAMP(value, 0, 2); }
    int get_fixture() const { return fixture; }
    Result generate_block(VoxelQueryData input) override;
    int get_used_channels_mask() const override;
};

class CairnMesher : public zylann::voxel::VoxelMesherBlocky {
    GDCLASS(CairnMesher, zylann::voxel::VoxelMesherBlocky);
protected:
    static void _bind_methods() {}
public:
    void build(Output &output, const Input &input) override;
};
