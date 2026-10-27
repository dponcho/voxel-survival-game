#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace cairn {
inline bool admit_terrain_operation(uint64_t charged_usec, uint64_t budget_usec) {
    return budget_usec >= 750 && charged_usec <= budget_usec - 750;
}
// Main-thread-only telemetry. No clocks, allocations or renderer calls here.
struct OperationTotals {
    uint64_t count = 0, bytes = 0, usec = 0, max_usec = 0;
    uint64_t max_bytes = 0, max_start_usec = 0;
    uint32_t max_kind = 0; // 1 upload, 2 surface removal, 3 mesh reference release.
    void record(uint64_t payload, uint64_t start, uint64_t elapsed, uint32_t kind) {
        ++count; bytes += payload; usec += elapsed;
        if (count == 1 || elapsed > max_usec) {
            max_usec = elapsed; max_bytes = payload; max_start_usec = start; max_kind = kind;
        }
    }
};

struct OperationFrame {
    uint64_t native_frame = 0, phase = 0, start_usec = 0, end_usec = 0;
    bool phase_boundary = false;
    OperationTotals upload, deletion, data_apply;
    uint64_t data_apply_nested_usec = 0;
    uint64_t frame_terrain_usec = 0, frame_upload_bytes = 0, frame_single_upload_bytes = 0;
    uint64_t frame_time_limit_usec = 1000, frame_upload_limit_bytes = 512 * 1024;
};

class OperationMetrics {
public:
    static constexpr size_t CAPACITY = 64;
    OperationTotals upload, deletion, data_apply; // Current phase, never differences of maxima.
    uint64_t phase = 0, dropped = 0, frames = 0;
    uint64_t peak_frame_usec = 0, peak_frame_upload_bytes = 0;
    bool tracing = false;
    uint64_t data_apply_nested_usec = 0, peak_frame_terrain_usec = 0, peak_single_upload_bytes = 0;
    uint64_t terrain_time_overruns = 0, terrain_upload_overruns = 0;
    void configure(uint64_t usec, uint64_t bytes) { time_limit = usec; byte_limit = bytes; }
    uint64_t active_phase() const { return active ? phase : 0; }
    uint64_t current_native_frame() const { return native_frame; }
    uint64_t current_time_limit() const { return frame_time_limit ? frame_time_limit : time_limit; }
    uint64_t current_byte_limit() const { return frame_byte_limit ? frame_byte_limit : byte_limit; }
    uint64_t current_bytes() const { return frame_bytes; }

    void begin_frame(uint64_t now) {
        seal(now, false);
        ++native_frame;
        frame_usec = frame_bytes = frame_single_bytes = frame_time_limit = frame_byte_limit = 0;
        if (active) open(now);
    }
    void begin_phase(uint64_t id, uint64_t now, bool trace) {
        end_phase(now);
        phase = id; tracing = trace; active = true;
        upload = {}; deletion = {}; data_apply = {}; dropped = 0; frames = 0;
        peak_frame_usec = 0; peak_frame_upload_bytes = 0;
        data_apply_nested_usec = peak_frame_terrain_usec = peak_single_upload_bytes = 0;
        terrain_time_overruns = terrain_upload_overruns = 0;
        open(now);
    }
    void end_phase(uint64_t now) { seal(now, true); active = false; }
    void record_upload(uint64_t bytes, uint64_t start, uint64_t usec) {
        note_work(usec, bytes);
        frame_single_bytes = std::max(frame_single_bytes, bytes);
        if (!active) return;
        upload.record(bytes, start, usec, 1); current.upload.record(bytes, start, usec, 1);
    }
    void record_deletion(uint64_t bytes, uint64_t start, uint64_t usec, bool surface) {
        note_work(usec, 0);
        if (!active) return;
        const uint32_t kind = surface ? 2 : 3;
        deletion.record(bytes, start, usec, kind); current.deletion.record(bytes, start, usec, kind);
    }
    void record_data_apply(uint64_t start, uint64_t usec, uint64_t nested) {
        // The completed-task bracket includes any upload/deletion hooks it calls.
        // Those children are already charged: only the exclusive remainder is new.
        nested = std::min(nested, usec);
        note_work(usec - nested, 0);
        if (!active) return;
        data_apply.record(0, start, usec, 4); current.data_apply.record(0, start, usec, 4);
        data_apply_nested_usec += nested; current.data_apply_nested_usec += nested;
    }
    bool pop(OperationFrame &out) {
        if (size == 0) return false;
        out = records[head]; head = (head + 1) % CAPACITY; --size;
        return true;
    }
private:
    std::array<OperationFrame, CAPACITY> records{};
    OperationFrame current;
    size_t head = 0, size = 0;
    uint64_t native_frame = 0;
    uint64_t time_limit = 1000, byte_limit = 512 * 1024;
    uint64_t frame_usec = 0, frame_bytes = 0, frame_single_bytes = 0;
    uint64_t frame_time_limit = 0, frame_byte_limit = 0;
    bool active = false, opened = false;
    void note_work(uint64_t usec, uint64_t bytes) {
        frame_usec += usec; frame_bytes += bytes;
        frame_time_limit = frame_time_limit ? std::min(frame_time_limit, time_limit) : time_limit;
        frame_byte_limit = frame_byte_limit ? std::min(frame_byte_limit, byte_limit) : byte_limit;
    }
    void open(uint64_t now) {
        current = {}; current.native_frame = native_frame; current.phase = phase;
        current.start_usec = now; opened = true;
    }
    void seal(uint64_t now, bool boundary) {
        if (!opened) return;
        current.end_usec = now; current.phase_boundary = boundary; opened = false;
        current.frame_terrain_usec = frame_usec; current.frame_upload_bytes = frame_bytes;
        current.frame_single_upload_bytes = frame_single_bytes;
        current.frame_time_limit_usec = frame_time_limit ? frame_time_limit : time_limit;
        current.frame_upload_limit_bytes = frame_byte_limit ? frame_byte_limit : byte_limit;
        peak_frame_terrain_usec = std::max(peak_frame_terrain_usec, frame_usec);
        peak_single_upload_bytes = std::max(peak_single_upload_bytes, frame_single_bytes);
        terrain_time_overruns += frame_usec > current.frame_time_limit_usec;
        terrain_upload_overruns += frame_bytes > current.frame_upload_limit_bytes;
        ++frames;
        peak_frame_usec = std::max(peak_frame_usec, current.upload.usec + current.deletion.usec);
        peak_frame_upload_bytes = std::max(peak_frame_upload_bytes, current.upload.bytes);
        if (!tracing) return;
        if (size == CAPACITY) { ++dropped; return; }
        records[(head + size) % CAPACITY] = current; ++size;
    }
};
}
