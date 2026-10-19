#pragma once
#include "core/object/ref_counted.h"
#include "core/math/aabb.h"
#include "core/variant/dictionary.h"
#include "core/variant/array.h"
#include <memory>
namespace cairn { class ObserverLedger; }

class CairnProbe : public RefCounted {
    GDCLASS(CairnProbe, RefCounted);
    std::shared_ptr<cairn::ObserverLedger> observer;
    String observer_path;
    bool observer_emitted = false;
protected:
    static void _bind_methods();
public:
    bool observer_start(const String &path);
    void observer_section(int section);
    int64_t observer_begin(int slot, int64_t units, int64_t bytes);
    void observer_end(int64_t token);
    Dictionary observer_status() const;
    Dictionary observer_finish();
    Dictionary observer_dispose();
    Dictionary observer_disposal_controls(const String &path);
    Dictionary observer_controls(const String &path);
    std::shared_ptr<cairn::ObserverLedger> observer_recorder() const { return observer; }
    Dictionary cpu_cycle_observation() const;
    Dictionary cpu_cycle_capability_smoke() const;
    Dictionary cpu_cycle_dose(const String &requested_cycles) const;
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
