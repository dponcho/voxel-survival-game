"""Exact control clocks, independent row expansion and adversarial saved evidence."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from fixed_work import LABELS, VERSION, assess, dose_for, observation, reconcile_control_phase, equal, scope, validate
from route_calibration import assess as legacy_assess, compare
from test_endpoint_precision import fixture as precision_fixture


def fixture(folder,label,index,workload='H1'):
    p=precision_fixture(folder,label,index,workload)
    declared,dose=dose_for(label,index)
    a=p['diagnostic_accounting'];c=p['precision_clock'];l=p['route_calibration']
    end=a['last_callback_end_usec']+2+1055+dose+(450000 if label=='window-drift' and index==3 else 0)
    a.update(end_usec=end,elapsed_usec=end-a['start_usec'],finalization_usec=end-a['last_callback_end_usec'])
    c['phases'][2]=dict(phase='retirement',begin_usec=end,end_usec=end+2000)
    c['dose_end_usec']=c['dose_begin_usec']+dose if index in (1,2) else None
    l['closure_dose']=dict(requested_usec=declared if index in (1,2) else 0,
        start_usec=(p['measurement_end_usec']-1 if label=='dose-overlap' and index==1 else c['dose_begin_usec']) if index in (1,2) and declared else None,
        end_usec=c['dose_end_usec'] if index in (1,2) and declared else None,elapsed_usec=dose)
    p['fixed_work_boundaries']=dict(native_phase_closed_usec=c['native_phase_close_usec'],writer_drain_begin_usec=c['writer_drain_begin_usec'],writer_drain_end_usec=c['writer_drain_end_usec'])
    p['edit_acknowledgement']=dict(start_usec=c['ack_begin_usec'] or 0,end_usec=p['measurement_end_usec'])
    p['edit_visibility']=dict(accepted=120 if workload=='H2' else 0)
    if label=='incomplete' and index==1:p['completed']=False
    if label=='phase-invalid' and index==1:p['fixed_work_boundaries']['native_phase_closed_usec']=c['writer_drain_end_usec']+1
    if label=='missing-window' and index==1:del a['elapsed_usec']
    return p


def phases(folder,label,workload='H1'):
    out=[fixture(folder,label,i,workload) for i in range(4)]
    if label=='missing':out.pop()
    if label=='reordered':out.reverse()
    return out


class FixedWorkTests(unittest.TestCase):
    def test_predeclared_boundaries_and_all_guard_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for workload in ('H1','H2'):
                for label in LABELS:
                    p=phases(folder,label,workload);declared,_=dose_for(label,0)
                    result=assess(p,workload,io_failed=label=='io-failed',declared=declared)
                    expected='null_observed' if label=='null' else ('sensitivity_observed' if label in ('below','at','above','endpoint','ack-duration','count-mask','count-drift') else 'inconclusive')
                    self.assertEqual(result['status'],expected,(workload,label,result))
                    if label=='at':self.assertEqual(result['duration_effect']['lower_fraction'],.01)
                    if label=='below':self.assertEqual(result['duration_effect']['classification'],'below_limit')
                    if label=='threshold-overlap':self.assertEqual(result['duration_effect']['classification'],'inconclusive')

    def test_count_cancellation_is_visible_without_changing_duration_estimand(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=phases(Path(tmp),'count-mask');r=assess(p,'H1')
            self.assertEqual(r['status'],'sensitivity_observed')
            self.assertGreater(r['duration_effect']['lower_fraction'],.01)
            for pair in r['count_duration_decomposition']:
                self.assertGreater(pair['callback_count_added_fraction'],.01)
                self.assertLess(pair['time_per_callback_added_fraction'],.01)
            self.assertEqual(legacy_assess(p,'H1')[0],'inconclusive')
            # Exact identity includes changed final callback cost (five microseconds).
            a,b=p[0]['diagnostic_accounting'],p[1]['diagnostic_accounting']
            self.assertEqual(b['elapsed_usec']-a['elapsed_usec'],599995)
            self.assertEqual(Fraction(b['elapsed_usec'],a['elapsed_usec'])/Fraction(b['callbacks'],a['callbacks']),
                             Fraction(b['elapsed_usec'],b['callbacks'])/Fraction(a['elapsed_usec'],a['callbacks']))

    def test_terminal_uncertainty_uses_complete_trial_units_and_retains_ack_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('endpoint','ack-duration'):
                p=phases(Path(tmp),label);r=assess(p,'H1');pair=r['same_mode_pairs'][0]
                self.assertEqual(pair['terminal_interval_delta_usec'],500)
                self.assertEqual(pair['ack_marker_delta_usec'],0 if label=='endpoint' else 500)
                self.assertEqual(pair['endpoint_uncertainty_usec'],500)
                self.assertLess(pair['endpoint_uncertainty_fraction'],.00002)
                self.assertEqual(len(r['observations']),4)
                self.assertEqual(sum(o['terminal_callbacks'] for o in r['observations']),16)
                self.assertEqual(legacy_assess(p,'H1')[0],'inconclusive')

    def test_missing_measurements_are_null_and_failed_workload_keeps_raw_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('unavailable','phase-invalid','missing-window'):
                r=assess(phases(Path(tmp),label),'H1')
                self.assertEqual(r['duration_effect'],dict(classification='unavailable',added_fraction=None))
                self.assertTrue(any(o['status']=='unavailable' and o['elapsed_usec'] is None for o in r['observations']))
            r=assess(phases(Path(tmp),'failed-operation'),'H1')
            self.assertEqual(r['status'],'inconclusive')
            self.assertEqual(r['duration_effect']['classification'],'above_limit')

    def test_exact_arithmetic_phase_boundaries_and_all_raw_rows_reconcile(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for workload in ('H1','H2'):
                for label in LABELS:
                    for index in range(4):
                        p=fixture(folder,label,index,workload)
                        raw=reconcile_control_phase(folder,p,label,index,workload)
                        self.assertEqual(raw['rows'],p['samples'])

    def test_bad_counts_costs_clocks_ack_and_guard_values_never_become_passing_zeros(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=fixture(Path(tmp),'above',1)
            for path,key,value in [('diagnostic_accounting','elapsed_usec',None),('diagnostic_accounting','callbacks',0),
                                   ('diagnostic_accounting','elapsed_usec',float('nan')),('diagnostic_accounting','last_callback_usec',-1),
                                   ('fixed_work_boundaries','writer_drain_begin_usec',0),('edit_acknowledgement','start_usec',None),
                                   ('edit_acknowledgement','end_usec',0)]:
                p=copy.deepcopy(original);p[path][key]=value
                self.assertEqual(observation(p)['status'],'unavailable',(path,key,value))
            p=copy.deepcopy(original);p['route_calibration']['bins'][6]['callback_usec']=0
            self.assertEqual(observation(p)['elapsed_usec'],None)

    def test_saved_effect_integer_null_and_qualification_mutations_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=assess(phases(Path(tmp),'above'),'H1')
            for mutate in [lambda q:q.__setitem__('qualified',True),lambda q:q['duration_effect'].__setitem__('classification','below_limit'),
                           lambda q:q['observations'][0].__setitem__('elapsed_usec',0),lambda q:q['same_mode_pairs'][0].__setitem__('endpoint_uncertainty_fraction',None)]:
                bad=copy.deepcopy(r);mutate(bad)
                with self.assertRaises(ValueError):equal(bad,r)

    def test_lost_final_raw_row_and_changed_report_closure_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=fixture(folder,'at',1)
            file=folder/p['raw_frames'];lines=file.read_text().splitlines();file.write_text('\n'.join(lines[:-1])+'\n')
            with self.assertRaises(ValueError):reconcile_control_phase(folder,p,'at',1,'H1')
            p=fixture(folder,'at',1);p['diagnostic_accounting']['end_usec']+=1
            with self.assertRaises(ValueError):reconcile_control_phase(folder,p,'at',1,'H1')

    def test_instability_remains_inconclusive_and_short_io_controls_do_not_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for label in ('window-drift','route-drift'):
                self.assertEqual(assess(phases(folder,label),'H1')['status'],'inconclusive')
            p=phases(folder,'above')
            self.assertEqual(assess(p,'H1',short=True)['status'],'inconclusive')
            self.assertEqual(assess(p,'H1',io_failed=True)['status'],'inconclusive')


if __name__=='__main__':unittest.main()
