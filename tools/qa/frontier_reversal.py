"""Bounded H2 camera-reversal reader; production continues outward at 6.5 m/s.

Uses the independent complete travel/native selection oracles with an explicit
1200-tick case. Ordinary and existing 600-tick expectations remain unchanged.
"""
from mesh_admission import compare as admission_compare, reconcile as admission_reconcile


def reconcile(folder, build, workers=1, priority=False):
    return admission_reconcile(folder,build,workers,priority,reversal=True)


def compare(fifo_folder, priority_folder, build, workers):
    result = admission_compare(fifo_folder,priority_folder,build,workers,reversal=True)
    result['scope'] = '1200 fixed H2 ticks; camera reversal at tick 900; outward motion unchanged'
    result['camera_reversal_tick'] = 900
    priority = result['priority']['travel']
    result['current_edit_closure_complete'] = priority['edits']['submitted'] == 80
    result['edit_duration_guard_passed'] = not priority['edit_latency_failed']
    result['operation_guards_passed'] = not priority['failed_operation_phases']
    return result
