def can_build(env, platform):
    env.module_add_dependencies("sandbox_world", ["voxel"])
    return True


def configure(env):
    pass
