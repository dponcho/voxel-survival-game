#include "../../native/sandbox_world/core/mesh_admission.h"
#include "../../native/sandbox_world/core/operation_metrics.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <random>
#include <vector>

using namespace cairn;
static double geometric_oracle(const MeshCandidate &c, const double *eye) {
    // Independent closed-box clamp; compare exact squared distances here.
    const int32_t coordinates[] = {c.x, c.y, c.z};
    double sum = 0;
    for (int a = 0; a < 3; ++a) {
        const double lo = int64_t(coordinates[a]) * 16, hi = lo + 16;
        const double nearest = eye[a] < lo ? lo : (eye[a] > hi ? hi : eye[a]);
        sum += (nearest-eye[a]) * (nearest-eye[a]);
    }
    return sum;
}
int main() {
    OperationMetrics phases;
    assert(phases.active_phase() == 0);
    phases.begin_phase(1,100,true); assert(phases.active_phase() == 1);
    phases.end_phase(200); assert(phases.active_phase() == 0 && phases.phase == 1);
    phases.begin_phase(2,300,true); assert(phases.active_phase() == 2);
    phases.end_phase(400); assert(phases.active_phase() == 0 && phases.phase == 2);
    const double eye[] = {16.6083488464355, 1.65100002288818, 10};
    std::array<MeshCandidate, MESH_PENDING_CAP> candidates{};
    std::array<uint16_t, MESH_PENDING_CAP> order{};
    std::mt19937 rng(6109);
    for (unsigned trial = 0; trial < 100; ++trial) {
        for (size_t i = 0; i < candidates.size(); ++i) {
            auto &c = candidates[i];
            c.x = int(rng()%31)-15; c.y = int(rng()%3)-1; c.z = int(rng()%31)-15;
            c.flags = 3 | (i%11==0 ? 4 : 0); c.desired = i+1; c.submitted = i%11==0 ? i : 0;
        }
        assert(mesh_admission_order(candidates.data(), candidates.size(), eye, 16, true, order.data()));
        std::vector<unsigned> seen(candidates.size());
        for (size_t j = 0; j < order.size(); ++j) {
            const size_t chosen = order[j]; assert(chosen < seen.size() && !seen[chosen]++);
            assert(mesh_distance_squared(candidates[chosen],eye,16)==geometric_oracle(candidates[chosen],eye));
            // Exhaustive independent minimum among all remaining requests.
            for (size_t i = 0; i < candidates.size(); ++i) if (!seen[i]) {
                const bool ce = candidates[chosen].flags & 4, ie = candidates[i].flags & 4;
                assert(ce || !ie);
                if (ce == ie) {
                    const double cd = ce ? 0 : geometric_oracle(candidates[chosen],eye);
                    const double id = ie ? 0 : geometric_oracle(candidates[i],eye);
                    assert(cd < id || (cd == id && chosen < i));
                }
            }
        }
        assert(mesh_admission_order(candidates.data(), candidates.size(), eye,16,false,order.data()));
        for (size_t i = 0; i < order.size(); ++i) assert(order[i]==i);
    }
    for (auto &c : candidates) c = {7,0,-1,3,1,0};
    assert(mesh_admission_order(candidates.data(),512,eye,16,true,order.data()));
    for (size_t i=0;i<512;++i) assert(order[i]==i); // Exact ties preserve original order.
    assert(!mesh_admission_order(candidates.data(),513,eye,16,true,order.data()));
    assert(mesh_admission_order(candidates.data(),0,eye,16,true,order.data()));
    assert(!mesh_admission_order(candidates.data(),1,eye,0,true,order.data()));
    candidates[0].flags=0;
    assert(!mesh_admission_order(candidates.data(),1,eye,16,true,order.data()));
    candidates[0].flags=3;
    double invalid[] = {std::numeric_limits<double>::quiet_NaN(),0,0};
    assert(!mesh_admission_order(candidates.data(),1,invalid,16,true,order.data()));
    invalid[0]=std::numeric_limits<double>::infinity();
    assert(!mesh_admission_order(candidates.data(),1,invalid,16,true,order.data()));
    invalid[0]=1e300;
    assert(!mesh_admission_order(candidates.data(),1,invalid,16,true,order.data()));
    // Static storage: no new worker/heap queue; overflow stays a failed measurement.
    static MeshAdmissionTrace trace;
    trace.reset(); trace.current.count=512; trace.current.valid=true;
    for (unsigned i=0;i<65;++i) trace.push();
    assert(trace.queued()==64 && trace.high_water==64 && trace.dropped==1 && trace.max_pending==512);
    for (unsigned i=1;i<=64;++i) {const auto *r=trace.pop();assert(r && r->row==i);}
    assert(!trace.pop() && trace.recorded==65 && trace.popped==64);
    trace.reset();assert(trace.queued()==0 && trace.recorded==0 && trace.dropped==0);
    std::cout << "Bounded pending selection, independent geometric minima, FIFO ties and trace overflow verified\n";
}
