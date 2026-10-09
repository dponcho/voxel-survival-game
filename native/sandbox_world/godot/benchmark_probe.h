#pragma once
#include "core/object/ref_counted.h"
#include "core/math/aabb.h"
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
    void start_edit_trace(bool enabled);
    void tick_edit_trace();
    void finish_edit_trace();
    Dictionary edit_trace_snapshot() const;
    Array take_edit_events();
    Dictionary sample_frontier(Object *terrain, Object *camera, AABB surface_bounds) const;
    Dictionary sample_mesh_blocks(Object *terrain, Array coordinates) const;
    bool set_mesh_admission(Object *terrain, bool priority, Vector3 origin, bool trace);
    void begin_mesh_admission_trace();
    Dictionary mesh_admission_snapshot() const;
    Array take_mesh_admission_frames();
};
