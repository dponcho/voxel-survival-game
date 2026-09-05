def can_build(env, platform):
    return True


def configure(env):
    env.module_add_dependencies("sandbox_world", ["voxel"])
