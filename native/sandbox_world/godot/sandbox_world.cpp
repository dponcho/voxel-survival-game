#include "sandbox_world.h"
#include "../build_identity.gen.h"
#include "../register_types.h"
#include "core/object/class_db.h"
#include "fixture_generator.h"
#include "benchmark_probe.h"
#include "report_sink.h"

void SandboxWorld::_bind_methods() {
    ClassDB::bind_method(D_METHOD("get_build_identity"), &SandboxWorld::get_build_identity);
}

Dictionary SandboxWorld::get_build_identity() const {
    Dictionary result;
    result["engine_inputs"] = CAIRN_ENGINE_INPUTS;
    result["godot_commit"] = CAIRN_GODOT_COMMIT;
    result["voxel_commit"] = CAIRN_VOXEL_COMMIT;
    return result;
}

void initialize_sandbox_world_module(ModuleInitializationLevel p_level) {
    if (p_level == MODULE_INITIALIZATION_LEVEL_SCENE) {
        ClassDB::register_class<SandboxWorld>();
        ClassDB::register_class<CairnFixture>();
        ClassDB::register_class<CairnMesher>();
        ClassDB::register_class<CairnProbe>();
        ClassDB::register_class<CairnReportSink>();
    }
}

void uninitialize_sandbox_world_module(ModuleInitializationLevel p_level) {
    // RefCounted instances own their lifetime; M0 registers no singleton or worker.
}
