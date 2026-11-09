#pragma once
#include "../core/operation_witness.h"
#include "core/variant/dictionary.h"
#include "core/string/ustring.h"
class CairnProbe;

namespace cairn {
// Main-thread opt-in; the process can arm the recorder once. Inactive hooks make
// no counter calls. Dispatch branches remain shared shipping diagnostic work.
inline OperationWitness *operation_witness = nullptr;
uint64_t operation_witness_begin(uint64_t start);
void operation_witness_ending(uint64_t token, uint32_t kind, uint64_t bytes, uint64_t nested);
void operation_witness_commit(uint64_t token, uint64_t end, bool phase_maximum);
void operation_witness_cancel(uint64_t token);
bool operation_witness_start(const String &path, bool retain_all = false);
Dictionary operation_witness_finish(CairnProbe &probe);
// Bounded controls only, never set by the public start API.
inline uint64_t operation_control_dose_usec = 0;
inline uint32_t operation_control_counter_fault = 0;
}
