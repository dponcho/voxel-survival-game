#pragma once
#include "core/object/ref_counted.h"
#include "core/variant/dictionary.h"
#include "core/variant/array.h"

class CairnProbe : public RefCounted {
    GDCLASS(CairnProbe, RefCounted);
protected:
    static void _bind_methods();
public:
    Dictionary snapshot() const;
    Dictionary machine() const;
    void configure(int workers, bool heavy);
    void begin_phase(int64_t id, bool trace);
    Dictionary end_phase();
    Dictionary phase_snapshot() const;
    Array take_operation_frames();
};
