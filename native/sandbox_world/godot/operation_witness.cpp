#include "operation_witness.h"
#include "benchmark_probe.h"
#include "m1_hooks.h"
#include "../core/observer_ledger.h"
#include "core/io/file_access.h"
#include "core/os/thread.h"
#ifdef WINDOWS_ENABLED
#include <windows.h>
#endif

namespace {
cairn::OperationWitness storage;
String output_path;
bool used = false;
uint64_t wall() { return OS::get_singleton()->get_ticks_usec(); }
String number(uint64_t n) { return String::num_uint64(n); }
cairn::CycleRead read() {
    if (!cairn::operation_control_counter_fault) return cairn::native_observer_read();
    cairn::CycleRead r; r.wall_before_usec = wall();
    if (cairn::operation_control_counter_fault == 1) {
#ifdef WINDOWS_ENABLED
        ULONG64 n = UINT64_MAX;
        const BOOL ok = QueryThreadCycleTime(nullptr,&n);
        const DWORD error = ok ? ERROR_SUCCESS : GetLastError();
        r.value = {true,ok != FALSE,uint32_t(error),uint64_t(n)};
#else
        r.value = {false,false,50,UINT64_MAX};
#endif
    } else r.value = {false,false,50,UINT64_MAX}; // Declared unsupported-call control.
    r.wall_after_usec = wall(); return r;
}
}
namespace cairn {
uint64_t operation_witness_begin(uint64_t start) {
    return operation_witness ? operation_witness->begin(start,operations.active_phase(),
            operations.current_native_frame(),native_observer_thread(),frame_upload_usec,read) : 0;
}
void operation_witness_ending(uint64_t token, uint32_t kind, uint64_t bytes, uint64_t nested) {
    if (!operation_witness) return;
    // This explicitly injected, bounded wall-wait dose is control work. Its
    // elapsed time remains INSIDE the failed operation, ahead of both end reads.
    if (operation_control_dose_usec && operation_control_dose_usec <= 20000)
        OS::get_singleton()->delay_usec(operation_control_dose_usec);
    operation_witness->ending(token,kind,bytes,nested,operation_control_dose_usec,operations.active_phase(),
            operations.current_native_frame(),native_observer_thread(),read);
}
void operation_witness_commit(uint64_t token, uint64_t end, bool phase_maximum) {
    if (operation_witness) operation_witness->commit(token,end,frame_upload_usec,
            operations.current_time_limit(),operations.current_bytes(),operations.current_byte_limit(),wall,phase_maximum);
}
void operation_witness_cancel(uint64_t token) { if (operation_witness) operation_witness->cancel(token); }
bool operation_witness_start(const String &path, bool retain_all) {
    if (!Thread::is_main_thread() || used || path.is_empty() || operation_witness ||
            operation_control_dose_usec || operation_control_counter_fault) return false;
    used = true; output_path = path; storage.active = true; storage.retain_all = retain_all;
    operation_witness = &storage; return true;
}
Dictionary operation_witness_finish(CairnProbe &probe) {
    Dictionary d; d["schema"] = "cairn-operation-witness-1"; d["passed"] = false;
    if (!Thread::is_main_thread() || !operation_witness || !storage.active) return d;
    // Stop all capture before bounded serialization. No operation or worker can
    // mutate this POD storage during its synchronous main-thread close.
    operation_witness = nullptr; storage.active = false;
    d["emit_start"] = probe.cpu_cycle_observation();
    const uint64_t begin = wall();
    auto bytes = operation_header(storage);
    bytes.reserve(storage.HEADER+storage.CAP*storage.RECORD);
    for (uint64_t i=0; i<storage.size; ++i) operation_encode(bytes,storage.records[i]);
    bool io = false, closed = false;
    Ref<FileAccess> file = FileAccess::open(output_path,FileAccess::WRITE);
    if (file.is_valid()) {
        io = file->store_buffer(bytes.data(),bytes.size());
        file->flush(); io = io && file->get_error() == OK;
        file->close(); file.unref(); closed = true;
    }
    const uint64_t end = wall();
    d["emit_end"] = probe.cpu_cycle_observation();
    d["file"] = output_path.get_file(); d["bytes"] = int64_t(bytes.size());
    d["serialization_capacity_bytes"] = int64_t(bytes.capacity());
    d["emit_begin_usec"] = number(begin); d["emit_end_usec"] = number(end);
    d["closed"] = closed; d["io_ok"] = io;
    d["record_count"] = int64_t(storage.size); d["completed"] = number(storage.completed);
    d["selected"] = number(storage.selected); d["overflow"] = number(storage.overflow);
    d["counter_errors"] = number(storage.counter_errors); d["context_errors"] = number(storage.context_errors);
    d["first_failure_id"] = number(storage.first_failure);
    d["fixed_storage_bytes"] = int64_t(sizeof(storage));
    d["record_cap"] = int64_t(storage.CAP); d["output_cap_bytes"] = int64_t(storage.OUTPUT_CAP);
    d["api"] = "QueryThreadCycleTime"; d["thread"] = number(native_observer_thread());
    d["perturbing"] = true; d["qualified"] = false;
    d["selection"] = storage.retain_all ? "control-retain-all" : "phase-and-process-maxima-first-failure-counter-error";
    d["integrity_passed"] = storage.good();
    d["passed"] = io && closed && bytes.size() == storage.HEADER+storage.size*storage.RECORD &&
            bytes.size() <= storage.OUTPUT_CAP;
    return d;
}
}
bool CairnProbe::operation_witness_start(const String &path) {
    if (observer || preparation) return false;
    return cairn::operation_witness_start(path);
}
Dictionary CairnProbe::operation_witness_finish() { return cairn::operation_witness_finish(*this); }
