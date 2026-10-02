#include "fixture_generator.h"
#include "m1_hooks.h"
#include "../core/fixture.h"
#include "../core/mesh_batch.h"
#include "modules/voxel/storage/voxel_buffer.h"
#include "modules/voxel/terrain/fixed_lod/voxel_terrain.h"
#include "core/os/os.h"

void CairnFixture::_bind_methods() {
    ClassDB::bind_method(D_METHOD("set_fixture", "value"), &CairnFixture::set_fixture);
    ClassDB::bind_method(D_METHOD("get_fixture"), &CairnFixture::get_fixture);
    ClassDB::bind_method(D_METHOD("try_edit", "terrain", "position", "value"), &CairnFixture::try_edit);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "fixture"), "set_fixture", "get_fixture");
}
bool CairnFixture::try_edit(Object *object, Vector3i position, int value) {
    auto *terrain = Object::cast_to<zylann::voxel::VoxelTerrain>(object);
    if (terrain == nullptr || terrain->get_generator().ptr() != this || value < 0 || value > 2) return false;
    std::unique_lock<std::mutex> lock(edits_mutex, std::try_to_lock);
    if (!lock.owns_lock()) return false;
    unsigned int index = 0;
    while (index < edit_count && edits[index].position != position) ++index;
    if (index == edits.size()) return false;
    if (!terrain->get_storage().try_set_voxel(value, position, zylann::voxel::VoxelBuffer::CHANNEL_TYPE)) return false;
    edits[index] = {position, uint16_t(value)};
    if (index == edit_count) ++edit_count;
    lock.unlock();
    cairn::edit_visibility.begin(position.x, position.y, position.z, OS::get_singleton()->get_ticks_usec());
    terrain->post_edit_voxel(position);
    cairn::edit_visibility.end(OS::get_singleton()->get_ticks_usec());
    return true;
}
int CairnFixture::get_used_channels_mask() const { return 1 << zylann::voxel::VoxelBuffer::CHANNEL_TYPE; }
CairnFixture::Result CairnFixture::generate_block(VoxelQueryData input) {
    const uint64_t start = OS::get_singleton()->get_ticks_usec();
    auto &buffer = input.voxel_buffer;
    const Vector3i size = buffer.get_size();
    for (int z = 0; z < size.z; ++z) for (int x = 0; x < size.x; ++x) for (int y = 0; y < size.y; ++y) {
        const Vector3i p = input.origin_in_voxels + Vector3i(x, y, z);
        buffer.set_voxel(cairn::fixture_voxel(p.x, p.y, p.z, fixture), x, y, z,
                zylann::voxel::VoxelBuffer::CHANNEL_TYPE);
    }
    // Bounded session-only overlay survives fixture eviction; no durable save format.
    {
        std::lock_guard<std::mutex> lock(edits_mutex);
        for (unsigned int i = 0; i < edit_count; ++i) {
            const Vector3i local = edits[i].position - input.origin_in_voxels;
            if (local.x >= 0 && local.y >= 0 && local.z >= 0 && local.x < size.x && local.y < size.y && local.z < size.z)
                buffer.set_voxel(edits[i].value, local.x, local.y, local.z, zylann::voxel::VoxelBuffer::CHANNEL_TYPE);
        }
    }
    buffer.compress_uniform_channels();
    cairn::generation_usec.fetch_add(OS::get_singleton()->get_ticks_usec() - start);
    cairn::generated.fetch_add(1);
    return Result();
}

void CairnMesher::build(Output &output, const Input &input) {
    const uint64_t start = OS::get_singleton()->get_ticks_usec();
    // Refuse the whole unsupported fixture before allocating unbounded geometry.
    // The harness observes overloads and stops with a failed result.
    const auto &voxels = input.voxels;
    const Vector3i size = voxels.get_size();
    int faces = 0;
    const Vector3i sides[] = { Vector3i(1,0,0), Vector3i(-1,0,0), Vector3i(0,1,0),
        Vector3i(0,-1,0), Vector3i(0,0,1), Vector3i(0,0,-1) };
    for (int z = 1; z < size.z - 1; ++z) for (int x = 1; x < size.x - 1; ++x)
        for (int y = 1; y < size.y - 1; ++y) {
            const Vector3i p(x,y,z);
            if (voxels.get_voxel(p, zylann::voxel::VoxelBuffer::CHANNEL_TYPE) == 0) continue;
            for (const Vector3i &side : sides) if (voxels.get_voxel(p + side,
                    zylann::voxel::VoxelBuffer::CHANNEL_TYPE) == 0) ++faces;
        }
    if (faces > cairn::MAX_FACES) { ++cairn::overloads; return; }
    VoxelMesherBlocky::build(output, input);
    zylann::StdVector<Output::Surface> split;
    // Preserve the stock cube mesher, winding, colors, AO, UVs and tangent data.
    // Keep the same triangle batches/draw count, retaining stock vertex reuse.
    uint64_t total_indices = 0, total_vertices = 0;
    for (const auto &surface : output.surfaces) {
        const Array &a = surface.arrays;
        const PackedVector3Array vertices = a[Mesh::ARRAY_VERTEX];
        const PackedVector3Array normals = a[Mesh::ARRAY_NORMAL];
        const PackedVector2Array uvs = a[Mesh::ARRAY_TEX_UV];
        const PackedColorArray colors = a[Mesh::ARRAY_COLOR];
        const PackedFloat32Array tangents = a[Mesh::ARRAY_TANGENT];
        const PackedInt32Array indices = a[Mesh::ARRAY_INDEX];
        total_indices += indices.size();
        total_vertices += vertices.size();
        if (total_indices > cairn::MAX_SOURCE_INDICES || total_vertices > cairn::MAX_SOURCE_VERTICES ||
                indices.size() % 3 != 0 || normals.size() != vertices.size() ||
                uvs.size() != vertices.size() || colors.size() != vertices.size() ||
                (!tangents.is_empty() && tangents.size() != vertices.size() * 4)) {
            ++cairn::overloads;
            output.surfaces.clear();
            return;
        }
        cairn::IndexedMeshBatch batch(vertices.size());
        for (int begin = 0; begin < indices.size(); begin += cairn::TRIANGLES_PER_UPLOAD * 3) {
            const int count = MIN(cairn::TRIANGLES_PER_UPLOAD * 3, indices.size() - begin);
            if (!batch.build(indices.ptr() + begin, count)) {
                ++cairn::overloads;
                output.surfaces.clear();
                return;
            }
            const int unique_count = batch.vertices();
            PackedVector3Array v, n; PackedVector2Array uv; PackedColorArray col; PackedFloat32Array tan;
            PackedInt32Array remapped;
            remapped.resize(count);
            for (int i = 0; i < count; ++i) remapped.set(i, batch.index(i));
            v.resize(unique_count); n.resize(unique_count); uv.resize(unique_count); col.resize(unique_count);
            if (!tangents.is_empty()) tan.resize(unique_count * 4);
            for (int i = 0; i < unique_count; ++i) {
                const int source = batch.source_vertex(i);
                v.set(i, vertices[source]);
                n.set(i, normals[source]);
                uv.set(i, uvs[source]);
                col.set(i, colors[source]);
                if (!tangents.is_empty()) for (int j = 0; j < 4; ++j) tan.set(i * 4 + j, tangents[source * 4 + j]);
            }
            Array arrays; arrays.resize(Mesh::ARRAY_MAX);
            arrays[Mesh::ARRAY_VERTEX] = v; arrays[Mesh::ARRAY_NORMAL] = n;
            arrays[Mesh::ARRAY_TEX_UV] = uv; arrays[Mesh::ARRAY_COLOR] = col;
            arrays[Mesh::ARRAY_INDEX] = remapped;
            if (!tan.is_empty()) arrays[Mesh::ARRAY_TANGENT] = tan;
            split.push_back({ arrays, surface.material_index });
        }
    }
    output.surfaces = std::move(split);
    cairn::meshing_usec.fetch_add(OS::get_singleton()->get_ticks_usec() - start);
    cairn::meshed.fetch_add(1);
}
