#include "../../native/sandbox_world/core/operation_metrics.h"
#include <cassert>
#include <iostream>

int main() {
    cairn::OperationMetrics m;
    m.begin_frame(1);
    m.begin_phase(1, 10, true); // Loading is slower than any later operation.
    m.record_upload(100, 11, 5000);
    m.record_deletion(200, 5011, 4000, true);
    m.end_phase(9011);
    assert(m.upload.max_usec == 5000 && m.deletion.max_usec == 4000);
    cairn::OperationFrame f;
    assert(m.pop(f) && f.phase == 1 && f.phase_boundary);
    assert(f.upload.bytes == 100 && f.deletion.max_kind == 2);
    m.begin_phase(2, 9012, true); // Same native frame; no loading contamination.
    assert(m.upload.count == 0 && m.upload.max_usec == 0 && m.deletion.max_usec == 0);
    m.record_upload(300, 9013, 900); // Over budget although lifetime max is unchanged.
    m.record_upload(400, 9913, 100);
    m.record_deletion(0, 10013, 800, false);
    m.begin_frame(10813);
    assert(m.pop(f) && f.phase == 2 && f.native_frame == 1 && !f.phase_boundary);
    assert(f.upload.count == 2 && f.upload.bytes == 700 && f.upload.usec == 1000);
    assert(f.upload.max_usec == 900 && f.upload.max_bytes == 300 && f.upload.max_start_usec == 9013);
    assert(f.deletion.count == 1 && f.deletion.max_kind == 3 && f.deletion.max_usec == 800);
    assert(m.peak_frame_usec == 1800 && m.peak_frame_upload_bytes == 700);
    m.end_phase(11000);
    assert(m.upload.max_usec == 900 && m.deletion.max_usec == 800);
    assert(m.pop(f) && f.upload.count == 0 && f.deletion.count == 0);
    assert(!m.pop(f));
    m.begin_phase(3, 11001, true); // An idle phase has explicit zero counts.
    m.end_phase(11002);
    assert(m.upload.count == 0 && m.deletion.max_usec == 0);
    assert(m.pop(f) && f.phase == 3);
    m.begin_phase(4, 12000, false); // A/B baseline keeps totals without trace storage.
    m.record_upload(20, 12001, 750);
    m.begin_frame(13000); m.end_phase(14000);
    assert(m.upload.max_usec == 750 && m.frames == 2 && !m.pop(f));
    m.begin_phase(5, 15000, true);
    for (size_t i = 0; i < cairn::OperationMetrics::CAPACITY + 3; ++i) {
        m.record_upload(1, 15001 + i * 2, 1);
        m.begin_frame(15002 + i * 2);
    }
    assert(m.dropped == 3 && m.upload.count == cairn::OperationMetrics::CAPACITY + 3);
    size_t count = 0;
    while (m.pop(f)) ++count;
    assert(count == cairn::OperationMetrics::CAPACITY);
    m.end_phase(16000);
    assert(m.pop(f) && !m.pop(f));
    m.record_upload(10, 16001, 9000); // Closed phases cannot acquire late work.
    assert(m.upload.max_usec == 1);
    std::cout << "M1 operation phase, frame, boundary, baseline and overflow checks passed\n";
}
