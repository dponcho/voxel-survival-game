#include "../../native/sandbox_world/core/edit_visibility.h"
#include <cassert>

int main() {
    cairn::EditVisibility trace;
    trace.reset(true);
    trace.begin(0, 0, 0, 1000);
    trace.target({-1, 0, 0, 10}, 1001);
    trace.target({0, 0, 0, 11}, 1002);
    trace.end(1003);
    trace.mesh_submitted({-1, 0, 0, 9}, 2000); // stale completion
    trace.mesh_submitted({-1, 0, 0, 10}, 3000);
    assert(trace.queued() == 0 && trace.pending() == 1);
    trace.mesh_submitted({0, 0, 0, 11}, 4000);
    cairn::EditEvidence event;
    assert(trace.pop(event) && event.outcome == cairn::EDIT_SUBMITTED);
    assert(event.target_count == 2 && event.targets[0].submitted && event.targets[1].submitted);
    assert(event.end_usec - event.accepted_usec == 3000 && trace.max_usec == 3000);

    trace.begin(1, 0, 0, 10000);
    trace.target({-1, 0, 0, 12}, 10001);
    trace.end(10002);
    trace.begin(2, 0, 0, 11000);
    trace.target({-1, 0, 0, 13}, 11001);
    trace.end(11002);
    assert(trace.pop(event) && event.outcome == cairn::EDIT_SUPERSEDED);
    assert(event.targets[0].revision == 12);
    trace.mesh_cancelled({-1, 0, 0, 13}, 12000);
    assert(trace.pop(event) && event.outcome == cairn::EDIT_CANCELLED);

    trace.begin(3, 0, 0, 13000);
    trace.target({-1, 0, 0, 14}, 13001);
    trace.end(13002);
    trace.revision_changed({-1, 0, 0, 15}, 14000); // newer data load, no new edit
    assert(trace.pop(event) && event.outcome == cairn::EDIT_SUPERSEDED);

    trace.begin(-1, 0, 0, 20000);
    trace.target({-1, 0, 0, 16}, 20001);
    trace.end(20002);
    trace.tick(220001);
    assert(trace.pop(event) && event.outcome == cairn::EDIT_TIMEOUT);
    trace.begin(99, 0, 0, 300000);
    trace.end(300001);
    assert(trace.pop(event) && event.outcome == cairn::EDIT_UNAVAILABLE);
    assert(trace.accepted == 6 && trace.submitted == 1 && trace.superseded == 2);
    assert(trace.cancelled == 1 && trace.timed_out == 1 && trace.unavailable == 1);

    trace.reset(true);
    for (int i = 0; i < 65; ++i) {
        trace.begin(i, 0, 0, 1000);
        trace.target({i, 0, 0, uint64_t(i + 1)}, 1000);
        trace.end(1000);
    }
    assert(trace.pending() == 64 && trace.pending_high_water == 64 && trace.overflow == 1);
    trace.stop(2000);
    assert(trace.cancelled == 64 && trace.queued() == 64 && trace.pending() == 0);
}
