#pragma once
#include "core/object/ref_counted.h"
#include "core/variant/dictionary.h"

class CairnProbe : public RefCounted {
    GDCLASS(CairnProbe, RefCounted);
protected:
    static void _bind_methods();
public:
    Dictionary snapshot() const;
    Dictionary machine() const;
    void configure(int workers, bool heavy);
};
