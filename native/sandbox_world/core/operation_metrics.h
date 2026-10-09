#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace cairn {
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
    OperationTotals upload, deletion;
};

class OperationMetrics {
public:
    static constexpr size_t CAPACITY = 64;
    OperationTotals upload, deletion; // Current phase, never differences of maxima.
    uint64_t phase = 0, dropped = 0, frames = 0;
    uint64_t peak_frame_usec = 0, peak_frame_upload_bytes = 0;
    bool tracing = false;
    uint64_t active_phase() const { return active ? phase : 0; }

    void begin_frame(uint64_t now) {
        seal(now, false);
        ++native_frame;
        if (active) open(now);
    }
    void begin_phase(uint64_t id, uint64_t now, bool trace) {
        end_phase(now);
        phase = id; tracing = trace; active = true;
        upload = {}; deletion = {}; dropped = 0; frames = 0;
        peak_frame_usec = 0; peak_frame_upload_bytes = 0;
        open(now);
    }
    void end_phase(uint64_t now) { seal(now, true); active = false; }
    void record_upload(uint64_t bytes, uint64_t start, uint64_t usec) {
        if (!active) return;
        upload.record(bytes, start, usec, 1); current.upload.record(bytes, start, usec, 1);
    }
    void record_deletion(uint64_t bytes, uint64_t start, uint64_t usec, bool surface) {
        if (!active) return;
        const uint32_t kind = surface ? 2 : 3;
        deletion.record(bytes, start, usec, kind); current.deletion.record(bytes, start, usec, kind);
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
    bool active = false, opened = false;
    void open(uint64_t now) {
        current = {}; current.native_frame = native_frame; current.phase = phase;
        current.start_usec = now; opened = true;
    }
    void seal(uint64_t now, bool boundary) {
        if (!opened) return;
        current.end_usec = now; current.phase_boundary = boundary; opened = false;
        ++frames;
        peak_frame_usec = std::max(peak_frame_usec, current.upload.usec + current.deletion.usec);
        peak_frame_upload_bytes = std::max(peak_frame_upload_bytes, current.upload.bytes);
        if (!tracing) return;
        if (size == CAPACITY) { ++dropped; return; }
        records[(head + size) % CAPACITY] = current; ++size;
    }
};
}
