#pragma once
#include "core/object/ref_counted.h"
#include "core/variant/dictionary.h"

class SandboxWorld : public RefCounted {
    GDCLASS(SandboxWorld, RefCounted);

protected:
    static void _bind_methods();

public:
    Dictionary get_build_identity() const;
};
