"""Actual mesh last-owner lifetime controls and saved-only reconciliation."""
import copy
import hashlib
import json
from pathlib import Path
import re

import shipping_cycles as cycles
import terrain_budget

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'cairn-mesh-retirement-proof-1'
BEFORE_SHA256 = 'e99e6e65f5ccab7eb2990f49fbb5807335b6bf6655a59dcced5ffa684a412f46'
SOURCES = ('m1_mesh_retirement_tests.gd', 'title.gd')
NATIVE = ('godot/retirement_probe.cpp', 'godot/retirement_before.h', 'godot/m1_hooks.h',
          'godot/benchmark_probe.cpp', 'godot/benchmark_probe.h', 'core/operation_metrics.h')
# name, surfaces before/after, refs before, endpoint alive, after alive, postpone, observed calls
CASES = (
    ('rejected-empty',0,None,1,True,False,False,1),
    ('empty',0,None,1,False,False,False,1),
    ('surface-0',2,1,1,True,True,True,1),
    ('surface-1',1,0,1,True,True,True,1),
    ('surface-release',0,None,1,False,False,False,1),
    ('shared-empty',0,0,2,True,True,False,1),
    ('postponed',0,0,1,None,True,True,0),
    ('postponed-release',0,None,1,False,False,False,1),
    ('non-array',None,None,1,False,False,False,1),
    ('null-add',None,None,None,None,False,False,0),
)
require, read, sha, uint = cycles.require, cycles.read, cycles.sha, cycles.uint


def source_metadata(root=ROOT):
    root = Path(root)
    before = (root/'native/sandbox_world/godot/retirement_before.h').read_text(encoding='utf-8')
    body = re.search(r'    void run\(TimeSpreadTaskContext &ctx\) override \{.*?(?=    ~)',before,re.S)
    require(body is not None and hashlib.sha256(body.group().encode()).hexdigest() == BEFORE_SHA256,
            'Frozen rejected retirement body changed')
    return dict(schema='cairn-mesh-retirement-source-1', before_run_sha256=BEFORE_SHA256,
        sources_sha256={n: sha(root/'game/scripts'/n) for n in SOURCES},
        native_sha256={n: sha(root/'native/sandbox_world'/n) for n in NATIVE},
        admission_patch_sha256=sha(root/'build/patches/voxel/m1-admission.json'))


def verify_metadata(build, contents, root=ROOT):
    require(build['mesh_retirement'] == source_metadata(root), 'Retirement source/native identity differs')
    for name in SOURCES:
        stem = 'scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC') and
                ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'], 'Missing retirement bytecode')


def natural(value):
    require(type(value) is int and value >= 0, 'Invalid integer retirement observation')
    return value


def exact_optional(value, expected):
    return type(value) is type(expected) and value == expected


def validate(report, build):
    require(report['schema'] == SCHEMA and report['build'] == build and report['passed'] is True and
            report['qualified'] is False and report['target_performance'] == 'not_run' and
            report['route_executed'] is False, 'Retirement fixture identity/qualification differs')
    n = report['native']
    require(n['schema'] == 'cairn-mesh-retirement-controls-1' and n['passed'] is True and
            n['qualified'] is False and n['status'] == 'complete' and natural(n['wire_case_cap']) == 10 and
            n['endpoint_hook_cleared'] is True, 'Retirement native control failed or retained its hook')
    begin, end = uint(n['fixture_start_usec']), uint(n['fixture_end_usec'])
    require(0 < begin <= end <= begin+5000000 and n['fixture_limit_usec'] == '5000000',
            'Retirement fixture escaped its cap')
    cycles.sequence([n['process_start'], n['process_end']])
    require(uint(n['thread']) > 0 and n['thread'] == n['process_start']['thread_id'] == n['process_end']['thread_id']
            and begin <= uint(n['process_start']['reads'][0]['wall_before_usec'])
            and uint(n['process_end']['reads'][3]['wall_after_usec']) <= end, 'Retirement thread/counter enclosure differs')
    rows = n['cases']
    require(type(rows) is list and len(rows) == 10 and [r['name'] for r in rows] == [c[0] for c in CASES],
            'Retirement cases missing, repeated or reordered')
    ids = [uint(r['object_id']) for r in rows]
    require(all(ids[i] > 0 for i in range(9)) and ids[9] == 0 and ids[2] == ids[3] == ids[4]
            and ids[6] == ids[7] and len({ids[i] for i in (0,1,2,5,6,8)}) == 6,
            'Retirement object identity/lifetime differs')
    require(n['external_alive_before_release'] is True and n['external_alive_after_release'] is False and
            uint(rows[5]['call_end_usec']) <= uint(n['external_release_begin_usec']) <=
            uint(n['external_release_end_usec']) <= uint(rows[6]['call_begin_usec']), 'External owner was falsely freed or unbounded')
    previous_order = 0
    previous_time = uint(n['process_start']['reads'][3]['wall_after_usec'])
    previous_frame = None
    results = []
    for i, (row, expected) in enumerate(zip(rows, CASES)):
        name, before_surfaces, after_surfaces, before_refs, endpoint_alive, after_alive, postpone, calls = expected
        begin_order, end_order = uint(row['call_begin_order']), uint(row['call_end_order'])
        call_begin, call_end = uint(row['call_begin_usec']), uint(row['call_end_usec'])
        require(previous_order < begin_order < end_order and previous_time <= call_begin <= call_end <= end,
                'Retirement call chronology differs')
        previous_order, previous_time = end_order, call_end
        entry = 'frozen-before-run' if i == 0 else ('FreeMeshTask::add' if i == 9 else 'FreeMeshTask::run')
        require(row['entry'] == entry and row['object_alive_before_call'] is (i != 9) and
                row['mesh_rid_valid_before_call'] is (True if i != 9 else None) and
                exact_optional(row['references_before_call'],before_refs) and exact_optional(row['surfaces_before_call'],before_surfaces) and
                row['postpone'] is postpone and row['object_alive_after_call'] is after_alive and
                exact_optional(row['surfaces_after_call'],after_surfaces) and
                exact_optional(row['references_after_call'],1 if after_alive else None), 'Retirement ownership/postponement differs')
        require(type(row['endpoint_calls']) is int and row['endpoint_calls'] == calls and
                row['endpoint_object_alive'] is endpoint_alive, 'Actual endpoint destruction observation differs')
        phase, frames = row['phase'], row['frames']
        require(natural(phase['id']) == 100+i and phase['tracing'] is True and natural(phase['frames']) == 1 and
                natural(phase['dropped_frames']) == 0 and len(frames) == 1, 'Retirement operation frame missing')
        frame = frames[0]
        require(frame['phase'] == phase['id'] and frame['phase_boundary'] is True and
                frame['start_usec'] <= call_begin <= call_end <= frame['end_usec'] and
                frame['frame_time_limit_usec'] == 1000 and frame['frame_upload_limit_bytes'] == 524288 and
                (previous_frame is None or frame['native_frame'] == previous_frame+1), 'Retirement frame budget/identity differs')
        previous_frame = frame['native_frame']
        for kind in ('upload','data_apply'):
            require(all(type(v) is int and v == 0 for v in phase[kind].values()) and
                    phase[kind] == frame[kind], 'Retirement fixture invented other terrain work')
        deletion = phase['deletion']
        for value in deletion.values(): natural(value)
        require(deletion == frame['deletion'] and natural(deletion['count']) == calls,
                'Retirement deletion count/phase differs')
        injected = 251 if name == 'postponed' else 0
        require(type(row['injected_admission_charge_usec']) is int and
                row['injected_admission_charge_usec'] == row['charge_before_usec'] == injected and
                row['charge_after_usec'] == injected+natural(deletion['usec']) and
                frame['frame_terrain_usec'] == deletion['usec'], 'Retirement elapsed charge lost or double-counted')
        if calls:
            surface = name in ('surface-0','surface-1')
            payload = 192 if surface else 0  # Three actual vertices, conservative 64-byte payload, no indices.
            require(deletion['max_kind'] == (2 if surface else 3) and
                    deletion['bytes'] == deletion['max_bytes'] == payload and
                    deletion['max_usec'] == deletion['usec'] and row['endpoint_payload_bytes'] == payload and
                    row['endpoint_surface'] is surface, 'Retirement kind/payload/maximum differs')
            operation_begin = natural(deletion['max_start_usec'])
            operation_end = operation_begin+deletion['usec']
            require(uint(row['endpoint_operation_start_usec']) == operation_begin and
                    call_begin <= operation_begin <= uint(row['endpoint_observed_usec']) <= operation_end <= call_end and
                    begin_order < uint(row['endpoint_order']) < end_order and row['endpoint_thread'] == n['thread'],
                    'Destruction witness is outside the actual measured bracket')
            require(exact_optional(row['endpoint_references'],1 if endpoint_alive else None) and
                    exact_optional(row['endpoint_surfaces'],after_surfaces if endpoint_alive and i != 0 else (0 if i == 0 else None)),
                    'Endpoint retained owner/surfaces differ')
        else:
            require(all(type(v) is int and v == 0 for v in deletion.values()) and
                    all(row[k] is None for k in ('endpoint_references','endpoint_surfaces','endpoint_observed_usec',
                        'endpoint_order','endpoint_thread','endpoint_operation_start_usec','endpoint_payload_bytes','endpoint_surface')),
                    'Refused/null work invented a measured endpoint')
        audit = terrain_budget.reconcile_rows(frames,phase)
        results.append(dict(name=name, entry=entry, object_id=row['object_id'],
            endpoint_object_alive=endpoint_alive, elapsed_usec=deletion['usec'], kind=deletion['max_kind'],
            operation_guard=audit['outcome'], operation_reasons=audit['reasons']))
    require(previous_time <= uint(n['process_end']['reads'][0]['wall_before_usec']), 'Fixture counters lost the final call')
    for key in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes'):
        require(n['native_start'][key] == n['native_end'][key] == 0, 'Retirement fixture retained native work')
    for key in ('generated','meshed','uploads','upload_bytes','overloads'):
        require(n['native_start'][key] == n['native_end'][key], 'Retirement fixture ran terrain work')
    return dict(passed=True, qualified=False, target_performance='not_run', schema=SCHEMA,
        fixture_usec=end-begin, cases=results, rejected_lifetime_reproduced=True,
        corrected_object_absent_before_ending_clock=True, shared_owner_preserved=True,
        endpoint_hook_cleared=True, renderer_deferred='unverified',
        operation_guards_valid=all(r['operation_guard']=='passed' for r in results),
        complete_process_cycles=list(map(str,cycles.demand(n['process_start'],n['process_end'],'process'))))


def mutations(report, build):
    changes = {
        'false-corrected-destruction': lambda r: r['native']['cases'][1].__setitem__('endpoint_object_alive',True),
        'hidden-rejected-lifetime': lambda r: r['native']['cases'][0].__setitem__('endpoint_object_alive',False),
        'false-shared-release': lambda r: r['native']['cases'][5].__setitem__('endpoint_object_alive',False),
        'endpoint-after-clock': lambda r: r['native']['cases'][1].__setitem__('endpoint_observed_usec',str(int(r['native']['cases'][1]['call_end_usec'])+1)),
        'endpoint-after-return': lambda r: r['native']['cases'][1].__setitem__('endpoint_order',r['native']['cases'][1]['call_end_order']),
        'false-owner-thread': lambda r: r['native']['cases'][1].__setitem__('endpoint_thread','0'),
        'double-charged-release': lambda r: r['native']['cases'][1].__setitem__('charge_after_usec',r['native']['cases'][1]['charge_after_usec']+1),
        'wrong-release-kind': lambda r: r['native']['cases'][1]['phase']['deletion'].__setitem__('max_kind',2),
        'missing-native-frame': lambda r: r['native']['cases'][1].__setitem__('frames',[]),
        'invented-null-endpoint': lambda r: r['native']['cases'][9].__setitem__('endpoint_calls',1),
        'destroyed-before-postpone': lambda r: r['native']['cases'][6].__setitem__('object_alive_after_call',False),
        'different-surface-owner': lambda r: r['native']['cases'][3].__setitem__('object_id',r['native']['cases'][1]['object_id']),
        'retained-control-hook': lambda r: r['native'].__setitem__('endpoint_hook_cleared',False),
        'unallocated-mesh-resource': lambda r: r['native']['cases'][1].__setitem__('mesh_rid_valid_before_call',False),
        'fixture-over-cap': lambda r: r['native'].__setitem__('fixture_end_usec',str(int(r['native']['fixture_start_usec'])+5000001)),
        'failed-counter': lambda r: r['native']['process_end']['reads'][1].__setitem__('success',False),
        'qualified-control': lambda r: r.__setitem__('qualified',True),
    }
    rejected = []
    for name, change in changes.items():
        bad = copy.deepcopy(report); change(bad)
        try: validate(bad,build)
        except (RuntimeError,KeyError,TypeError,ValueError,IndexError): rejected.append(name)
        else: raise RuntimeError('Mesh retirement corruption accepted: '+name)
    return rejected


def run_controls(exe,label,game=None):
    from build_support import REPORTS,run,write_json
    folder = REPORTS/('mesh-retirement-'+label); folder.mkdir(parents=True,exist_ok=True)
    output = folder/'controls.json'
    require(not output.exists(), 'Mesh retirement controls already ran; no automatic retry')
    args = [exe,'--headless']+(['--path',game] if game is not None else [])
    log = run(args+['--','--mesh-retirement-check','--mesh-retirement-output='+str(output)],'mesh-retirement-'+label,timeout=60)
    markers = [json.loads(line.split('CAIRN_MESH_RETIREMENT=',1)[1]) for line in log.splitlines() if 'CAIRN_MESH_RETIREMENT=' in line]
    require(markers == [dict(passed=True,output=str(output))] and 'SCRIPT ERROR:' not in log and 'ERROR:' not in log,
            'Mesh retirement actual-entry control failed')
    report, build = read(output), read(ROOT/'game/build_info.json')
    result = validate(report,build); result['mutations_rejected'] = mutations(report,build)
    write_json(folder/'validation.json',result)
    return result


def saved_controls(reports,build):
    results = {}
    for label in ('editor','release'):
        folder = Path(reports)/('mesh-retirement-'+label)
        report = read(folder/'controls.json')
        result = validate(report,build); result['mutations_rejected'] = mutations(report,build)
        require(result == read(folder/'validation.json'), 'Saved mesh retirement controls differ: '+label)
        results[label] = result
    return results
