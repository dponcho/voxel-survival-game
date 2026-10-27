"""Bounded actual-operation cycle witnesses; no cycle/time conversion or cost verdict."""
import copy
import hashlib
import json
from pathlib import Path
import struct

import shipping_cycles as cycles
import terrain_budget

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'cairn-operation-witness-proof-1'
HEADER, RECORD, CAP, OUTPUT_CAP = 256, 296, 128, 262144
HEADER_KEYS = ('cap','size','attempts','completed','cancelled','selected','overflow','counter_errors',
               'context_errors','first_failure','outside_usec','read_calls','storage_bytes','retain_all','active','depth')
EVENT_KEYS = ('id','parent','completion','phase','frame','thread_begin','thread_end','start','end','bytes',
              'nested','charged_before','charged_after','commit_end','injected_usec','phase_end','frame_end',
              'frame_limit','frame_bytes','frame_byte_limit','kind','flags')
SOURCES = ('m1_operation_witness_tests.gd','title.gd')
NATIVE = ('core/operation_witness.h','core/operation_metrics.h','core/cycle_observation.h',
          'godot/operation_witness.h','godot/operation_witness.cpp','godot/operation_witness_controls.cpp',
          'godot/m1_hooks.h','godot/observer_probe.cpp','godot/benchmark_probe.cpp','godot/benchmark_probe.h')
require, read, sha, uint = cycles.require, cycles.read, cycles.sha, cycles.uint


def source_metadata(root=ROOT):
    root = Path(root)
    return dict(schema='cairn-operation-witness-source-1',
        sources_sha256={n:sha(root/'game/scripts'/n) for n in SOURCES},
        native_sha256={n:sha(root/'native/sandbox_world'/n) for n in NATIVE},
        admission_patch_sha256=sha(root/'build/patches/voxel/m1-admission.json'),
        inventory_sha256=sha(root/'game/diagnostics/operation_witness.json'),
        parent_shipping_inventory_sha256=sha(root/'game/diagnostics/shipping_inventory.json'))


def verify_metadata(build, contents, root=ROOT):
    require(build['operation_witness'] == source_metadata(root), 'Operation witness source/native identity differs')
    require(json.loads(contents['diagnostics/operation_witness.json']) == read(Path(root)/'game/diagnostics/operation_witness.json'),
            'Operation witness inventory differs')
    for name in SOURCES:
        stem = 'scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC') and
                ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'], 'Missing operation witness bytecode')


def natural(v):
    require(type(v) is int and v >= 0, 'Invalid operation witness integer')
    return v


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(type(raw) is bytes and HEADER <= len(raw) <= HEADER+CAP*RECORD, 'Operation witness file cap/length')
    require(raw[:8] == b'CAIRNOP1' and struct.unpack_from('<II',raw,8) == (1,RECORD), 'Operation witness codec')
    h = dict(zip(HEADER_KEYS,struct.unpack_from('<16Q',raw,16)))
    for i,key in enumerate(('counts','maxima','max_ids')):
        h[key] = list(struct.unpack_from('<4Q',raw,144+32*i))
    require(not any(raw[240:HEADER]) and h['cap'] == CAP and h['size'] <= CAP and
            len(raw) == HEADER+h['size']*RECORD, 'Operation witness header/record extent')
    require(0 < h['storage_bytes'] <= 65536 and h['retain_all'] in (0,1) and h['active'] == h['depth'] == 0,
            'Operation witness storage/close state')
    require(h['attempts'] == h['completed']+h['cancelled'] and h['read_calls'] == 4*h['completed']+2*h['cancelled']
            and h['size']+h['overflow'] == h['selected'] <= h['completed'] and sum(h['counts']) == h['completed'],
            'Operation witness count/overflow disagreement')
    rows, ids, completion = [], set(), 0
    for index in range(h['size']):
        offset = HEADER+index*RECORD
        r = dict(zip(EVENT_KEYS,struct.unpack_from('<20Q2I',raw,offset)))
        require(0 < r['id'] <= h['attempts'] and r['id'] not in ids and
                completion < r['completion'] <= h['completed'], 'Operation event identity/completion order')
        ids.add(r['id']); completion = r['completion']
        require(1 <= r['kind'] <= 4 and 0 < r['thread_begin'] == r['thread_end'] and
                r['phase'] == r['phase_end'] and r['frame'] == r['frame_end'] and
                r['parent'] < r['id'] and r['start'] <= r['end'] <= r['commit_end'], 'Operation owner/context/endpoints')
        require(r['frame_limit'] in (1000,2000) and r['frame_byte_limit'] in (524288,1048576) and
                r['injected_usec'] <= 20000, 'Operation budgets/control dose changed')
        reads, wall, previous, counter = [], r['start'], 0, False
        for j in range(4):
            value,before,after,flags,error = struct.unpack_from('<QQQII',raw,offset+168+32*j)
            require(flags in (0,1,3) and wall <= before <= after <= r['end'], 'Counter wall enclosure/flags')
            good = flags == 3 and error == 0
            require(good or value == 0, 'Failed/unavailable wire counter became measured zero')
            counter |= not good or value < previous
            if good: previous = value
            reads.append(dict(cycles=str(value) if good else None,available=bool(flags&1),success=bool(flags&2),
                              error=error,wall_before_usec=str(before),wall_after_usec=str(after)))
            wall = after
        elapsed = r['end']-r['start']
        flags = (1 if elapsed>750 else 0) | (2 if counter else 0) | (8 if r['charged_after']>r['frame_limit'] else 0) | \
                (16 if r['frame_bytes']>r['frame_byte_limit'] else 0) | (32 if r['kind']==1 and r['bytes']>262144 else 0)
        require(r['flags'] == flags, 'Operation guard/counter verdict differs')
        require(r['nested'] <= elapsed and (r['kind'] == 4 or r['nested'] == 0) and
                r['charged_after'] == r['charged_before']+elapsed, 'Operation single/union charge differs')
        # A parent starts before children are charged: end charge equals its
        # original charge plus its inclusive elapsed duration, exactly once.
        r['reads'] = reads; r['elapsed_usec'] = elapsed
        if counter:
            r['status'] = 'unavailable' if any(not v['available'] for v in reads) else 'failed'
            r['body_cycles'] = r['full_cycles'] = r['uncertainty_cycles'] = None
        else:
            values = [int(v['cycles']) for v in reads]
            r['status'] = 'measured'; r['body_cycles'] = str(values[2]-values[1])
            r['full_cycles'] = str(values[3]-values[0]); r['uncertainty_cycles'] = str(int(r['full_cycles'])-int(r['body_cycles']))
        rows.append(r)
    by_id = {r['id']:r for r in rows}
    require(h['counter_errors'] >= sum(bool(r['flags']&2) for r in rows) and h['context_errors'] == 0,
            'Operation counter/context failure count differs')
    require(h['outside_usec'] >= sum(r['commit_end']-r['end'] for r in rows), 'Post-wall bookkeeping hidden')
    if h['retain_all']:
        require(h['selected'] == h['completed'] and [r['completion'] for r in rows] == list(range(1,len(rows)+1)),
                'Retain-all control silently sampled/evicted')
    for k in range(4):
        candidates = [r for r in rows if r['kind'] == k+1]
        key = h['max_ids'][k]
        if not h['counts'][k]:
            require(not candidates and h['maxima'][k] == key == 0, 'Empty operation maximum became observed zero')
        else:
            require(key > 0 and h['counts'][k] >= len(candidates), 'Operation count/maximum missing')
            largest = max(candidates,key=lambda r:r['elapsed_usec']) if candidates else None
            if key in by_id:
                require(largest is not None and largest['id'] == key and largest['elapsed_usec'] == h['maxima'][k],
                        'First-tie operation maximum differs')
            else:
                require(h['overflow'] > 0 and key <= h['attempts'] and
                        (not largest or h['maxima'][k] >= largest['elapsed_usec']), 'Unobserved maximum without overflow')
    failures = [r for r in rows if r['flags']&57]
    if failures:
        require(h['first_failure'] == failures[0]['id'], 'First failure replaced by later maximum')
    else:
        require(h['first_failure'] == 0 or h['overflow'] > 0, 'Invented first failure')
    return h,rows


# name, completed kinds, payloads, postpone, before/after liveness, surfaces before/after, endpoint alive.
CASES = (
    ('upload-first-failure',[1],[192],False,False,False,None,None,None),
    ('upload-later-maximum',[1],[192],False,False,False,None,None,None),
    ('surface-0',[2],[192],True,True,True,2,1,True),
    ('surface-1',[2],[192],True,True,True,1,0,True),
    ('surface-release',[3],[0],False,True,False,0,None,False),
    ('empty-release',[3],[0],False,True,False,0,None,False),
    ('shared-empty',[3],[0],False,True,True,0,0,True),
    ('postponed',[],[],True,True,True,0,0,None),
    ('resumed',[3],[0],False,True,False,0,None,False),
    ('null-add',[],[],False,False,False,None,None,None),
    ('nested-charge',[3,4],[0,0],False,True,False,0,None,False),
    ('phase-carry-normal',[3],[0],False,True,False,0,None,False),
    ('phase-carry-heavy',[3],[0],False,True,False,0,None,False),
    ('failed-counter',[3],[0],False,True,False,0,None,False),
    ('unavailable-counter',[3],[0],False,True,False,0,None,False),
)


def totals(rows):
    maximum = max(rows,key=lambda r:r['elapsed_usec']) if rows else None
    return dict(count=len(rows),bytes=sum(r['bytes'] for r in rows),usec=sum(r['elapsed_usec'] for r in rows),
        max_usec=maximum['elapsed_usec'] if maximum else 0,max_bytes=maximum['bytes'] if maximum else 0,
        max_start_usec=maximum['start'] if maximum else 0,max_kind=maximum['kind'] if maximum else 0)


def validate(report, build, raw):
    require(report['schema'] == SCHEMA and report['build'] == build and report['passed'] is True and
            report['qualified'] is False and report['target_performance'] == 'not_run' and report['route_executed'] is False,
            'Operation fixture identity/qualification differs')
    require(report['trace_sha256'] == digest(raw), 'Operation trace digest differs')
    n = report['native']; w = n['witness']; h,events = decode(raw)
    require(n['schema'] == 'cairn-operation-witness-controls-1' and n['passed'] is True and n['qualified'] is False and
            n['hooks_cleared'] is True and n['external_alive_after_release'] is False and
            natural(n['upload_surface_count']) == 2 and n['upload_material_order'] == [7,9], 'Actual operation control failed')
    begin,end,thread = uint(n['fixture_start_usec']),uint(n['fixture_end_usec']),uint(n['thread'])
    require(0 < begin <= end <= begin+5000000 and n['fixture_limit_usec'] == '5000000', 'Operation fixture cap')
    cycles.sequence([n['process_start'],n['process_end']])
    require(thread > 0 and n['thread'] == n['process_start']['thread_id'] == n['process_end']['thread_id'] and
            begin <= uint(n['process_start']['reads'][0]['wall_before_usec']) and
            uint(n['process_end']['reads'][3]['wall_after_usec']) <= end, 'Operation fixture process/thread enclosure')
    require(w['schema'] == 'cairn-operation-witness-1' and w['passed'] is True and w['closed'] is True and
            w['io_ok'] is True and w['integrity_passed'] is False and w['qualified'] is False and w['perturbing'] is True and
            w['selection'] == 'control-retain-all' and w['api'] == 'QueryThreadCycleTime' and w['thread'] == n['thread'],
            'Operation writer/integrity verdict changed')
    require(natural(w['bytes']) == len(raw) and natural(w['record_cap']) == CAP and natural(w['output_cap_bytes']) == OUTPUT_CAP and
            len(raw) <= natural(w['serialization_capacity_bytes']) <= OUTPUT_CAP and
            natural(w['fixed_storage_bytes']) == h['storage_bytes'] and natural(w['record_count']) == h['size'], 'Witness bounds differ')
    for key in ('completed','selected','overflow','counter_errors','context_errors'):
        require(uint(w[key]) == h[key], 'Witness summary/raw count differs: '+key)
    require(uint(w['first_failure_id']) == h['first_failure'] == 1 and h['retain_all'] == 1 and h['size'] == 128 and
            h['attempts'] == 131 and h['completed'] == h['selected'] == 130 and h['cancelled'] == 1 and
            h['overflow'] == 2 and h['counter_errors'] == 2 and h['context_errors'] == 0, 'Expected failed cap/counter control changed')
    cycles.sequence([w['emit_start'],w['emit_end']])
    require(w['emit_start']['thread_id'] == w['emit_end']['thread_id'] == n['thread'] and
            uint(n['process_start']['reads'][3]['wall_after_usec']) <= uint(w['emit_start']['reads'][0]['wall_before_usec']) <=
            uint(w['emit_start']['reads'][3]['wall_after_usec']) <= uint(w['emit_begin_usec']) <= uint(w['emit_end_usec']) <=
            uint(w['emit_end']['reads'][0]['wall_before_usec']) <= uint(w['emit_end']['reads'][3]['wall_after_usec']) <=
            uint(n['process_end']['reads'][0]['wall_before_usec']), 'Complete witness close not enclosed')
    rows = n['cases']; require(len(rows) == len(CASES) and [r['name'] for r in rows] == [c[0] for c in CASES], 'Missing/reordered operation cases')
    state, results, observed, previous_end = {}, [], set(), begin
    for i,(row,expected) in enumerate(zip(rows,CASES)):
        name,kinds,payloads,postpone,live_before,live_after,surface_before,surface_after,endpoint_alive = expected
        start,stop = uint(row['call_begin_usec']),uint(row['call_end_usec'])
        require(previous_end <= start <= stop <= uint(w['emit_begin_usec']), 'Operation case clocks reordered')
        previous_end = stop
        phase = row['phase']; require(natural(phase['id']) == 1000+i and phase['tracing'] is True, 'Operation phase identity/trace')
        own = [e for e in events if e['phase'] == 1000+i]
        before,after = uint(row['attempts_before']),uint(row['attempts_after'])
        require(after-before == len(kinds) and {e['id'] for e in own} == set(range(before+1,after+1)) and
                [e['kind'] for e in own] == kinds and [e['bytes'] for e in own] == payloads, 'Actual entry kind/payload/attempt differs')
        observed.update(e['id'] for e in own)
        for e in own:
            require(e['thread_begin'] == thread and start <= e['start'] <= e['end'] <= e['commit_end'] <= stop and
                    e['injected_usec'] == uint(row['dose_usec']), 'Case/event thread/clock/dose differs')
            expected_status = ('measured','failed','unavailable')[natural(row['counter_fault'])]
            require(e['status'] == expected_status, 'Failed/unavailable counter became passing zero')
            if row['counter_fault']:
                require(all(not v['success'] and v['cycles'] is None and v['error'] > 0 for v in e['reads']) and
                        all(v['available'] == (row['counter_fault']==1) for v in e['reads']), 'Counter fault provenance changed')
        expected_entry = 'cairn::upload_surface' if i<2 else ('FreeMeshTask::add' if name=='null-add' else
                         ('completed-task-bracket/FreeMeshTask::run' if name=='nested-charge' else 'FreeMeshTask::run'))
        require(row['entry'] == expected_entry and type(row['postpone']) is bool and row['postpone'] == postpone and
                type(row['alive_before']) is bool and row['alive_before'] == live_before and type(row['alive_after']) is bool and
                row['alive_after'] == live_after and type(row['surfaces_before']) is type(surface_before) and
                row['surfaces_before'] == surface_before and type(row['surfaces_after']) is type(surface_after) and
                row['surfaces_after'] == surface_after, 'Lifetime, sharing or postponement changed')
        calls = int(endpoint_alive is not None)
        require(uint(row['endpoint_calls']) == calls and type(row['endpoint_alive']) is type(endpoint_alive) and
                row['endpoint_alive'] == endpoint_alive, 'Destruction endpoint/liveness changed')
        if calls:
            deletion = next(e for e in own if e['kind'] in (2,3))
            require(deletion['start'] <= uint(row['endpoint_observed_usec']) <= int(deletion['reads'][2]['wall_before_usec']),
                    'Destruction witness after ending counter/clock')
        else: require(row['endpoint_observed_usec'] is None, 'Invented endpoint on refused/null/upload work')
        for label,ks in (('upload',(1,)),('deletion',(2,3)),('data_apply',(4,))):
            require(phase[label] == totals([e for e in own if e['kind'] in ks]), 'Operation phase maximum/totals differ')
        nested = sum(e['nested'] for e in own)
        require(phase['data_apply_nested_usec'] == nested, 'Nested operation charge differs')
        charge_before,charge_after = uint(row['charge_before_usec']),uint(row['charge_after_usec'])
        require(charge_after == charge_before+sum(e['elapsed_usec'] for e in own)-nested and
                uint(row['admission_charge_usec']) == (251 if name=='postponed' else 0), 'Single/union charging differs')
        if name=='postponed': require(charge_before == charge_after == 251, 'Admission refusal charged work')
        elif name!='phase-carry-heavy': require(charge_before == 0, 'Unexpected frame carry')
        check = terrain_budget.reconcile_rows(row['frames'],phase,state)
        require(len(row['frames']) == 1 and all(e['frame']==row['frames'][0]['native_frame'] for e in own), 'Native frame identity differs')
        results.append(dict(name=name,events=[e['id'] for e in own],operation_guard=check['outcome'],reasons=check['reasons']))
    ids = [uint(row['object_id']) for row in rows]
    require(ids[0] == ids[1] == ids[9] == 0 and all(ids[i] > 0 for i in range(2,15) if i!=9) and
            ids[2] == ids[3] == ids[4] and ids[7] == ids[8], 'Actual mesh owner identity differs')
    first,later = events[0],events[1]
    require(first['id']==1 and later['id']==2 and first['kind']==later['kind']==1 and first['elapsed_usec']>750 and
            uint(rows[0]['dose_usec'])==2000 and uint(rows[1]['dose_usec'])==first['elapsed_usec']+2000 and
            later['elapsed_usec']>first['elapsed_usec'] and h['max_ids'][0]==2 and h['maxima'][0]==later['elapsed_usec'] and
            results[0]['operation_guard']==results[1]['operation_guard']=='failed', 'Injected first failure/later maximum relabelled')
    parent = next(e for e in events if e['phase']==1010 and e['kind']==4)
    child = next(e for e in events if e['phase']==1010 and e['kind']==3)
    require(child['parent']==parent['id'] and parent['parent']==0 and parent['start']<=child['start']<=child['end']<=parent['end'] and
            parent['nested']==child['elapsed_usec'], 'Nested actual-entry parent/union differs')
    a,b = rows[11],rows[12]
    require(a['frames'][0]['native_frame']==b['frames'][0]['native_frame'] and
            uint(b['charge_before_usec'])==uint(a['charge_after_usec']) and b['frames'][0]['frame_time_limit_usec']==1000 and
            b['frames'][0]['frame_upload_limit_bytes']==524288, 'Normal-to-heavy transition reset the current frame budget')
    require(uint(n['cancelled_charge_usec'])==0 and natural(n['filler_phase']['id'])==2000 and n['filler_frames']==[] and
            n['filler_phase']['tracing'] is False and uint(n['filler_count'])==130-len(observed) and
            n['filler_phase']['deletion']['count']==uint(n['filler_count']) and n['filler_phase']['deletion']['bytes']==0 and
            n['filler_phase']['upload']['count']==n['filler_phase']['data_apply']['count']==0, 'Overflow/cancelled actual-entry control differs')
    filler = [e for e in events if e['id'] not in observed]
    require(all(e['phase']==2000 and e['kind']==3 and e['bytes']==e['nested']==e['injected_usec']==0 and
                e['thread_begin']==thread and e['parent']==0 for e in filler), 'Overflow filler was not an actual release')
    for key in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes'):
        require(n['native_start'][key]==n['native_end'][key]==0, 'Control did not drain native resources')
    for key in ('generated','meshed','overloads'):
        require(n['native_start'][key]==n['native_end'][key], 'Unrelated native work changed')
    require(n['native_end']['uploads']-n['native_start']['uploads']==2 and
            n['native_end']['upload_bytes']-n['native_start']['upload_bytes']==384, 'Actual upload resource work missing')
    return dict(passed=True,qualified=False,operation_guards_valid=False,witness_integrity_valid=False,
        first_failure_id=1,upload_first_tie_maximum_id=2,retained_events=h['size'],completed_events=h['completed'],
        overflow=h['overflow'],counter_errors=h['counter_errors'],storage_bytes=h['storage_bytes'],trace_bytes=len(raw),
        cases=results,failed_counter_nulls_preserved=True,corrected_last_owner_inside_end_reads=True,
        renderer_deferred='unverified',cpu_wall_cause='unavailable',shipping_cost='unqualified',
        events=[dict(id=e['id'],kind=e['kind'],phase=e['phase'],frame=e['frame'],thread=str(e['thread_begin']),
                     elapsed_usec=e['elapsed_usec'],status=e['status'],body_cycles=e['body_cycles'],
                     full_cycles=e['full_cycles'],uncertainty_cycles=e['uncertainty_cycles']) for e in events[:14]],
        complete_process_cycles=list(map(str,cycles.demand(n['process_start'],n['process_end'],'process'))))


def mutations(report,build,raw):
    def event(blob,index,key,value):
        i = EVENT_KEYS.index(key); fmt,offset = ('<Q',8*i) if i<20 else ('<I',160+4*(i-20))
        struct.pack_into(fmt,blob,HEADER+index*RECORD+offset,value)
    changes = {
        'false-thread':lambda r,b:event(b,0,'thread_end',0),
        'wrong-upload-kind':lambda r,b:event(b,0,'kind',3),
        'wrong-upload-payload':lambda r,b:event(b,0,'bytes',193),
        'endpoint-outside-wall':lambda r,b:struct.pack_into('<Q',b,HEADER+168+16,0),
        'first-failure-replaced-by-maximum':lambda r,b:struct.pack_into('<Q',b,16+8*9,2),
        'maximum-replaced-by-first-failure':lambda r,b:struct.pack_into('<Q',b,208,1),
        'hidden-overflow':lambda r,b:struct.pack_into('<Q',b,16+8*6,0),
        'passing-truncation':lambda r,b:r['native']['witness'].__setitem__('integrity_passed',True),
        'passing-injected-guard':lambda r,b:r['native']['cases'][0]['phase']['upload'].__setitem__('max_usec',750),
        'wrong-case-thread':lambda r,b:r['native'].__setitem__('thread','0'),
        'false-destruction':lambda r,b:r['native']['cases'][4].__setitem__('endpoint_alive',True),
        'destroyed-shared-owner':lambda r,b:r['native']['cases'][6].__setitem__('alive_after',False),
        'phase-carry-reset':lambda r,b:r['native']['cases'][12].__setitem__('charge_before_usec','0'),
        'double-parent-charge':lambda r,b:r['native']['cases'][10].__setitem__('charge_after_usec',str(uint(r['native']['cases'][10]['charge_after_usec'])+1)),
        'missing-refusal':lambda r,b:r['native']['cases'][7].__setitem__('postpone',False),
        'hidden-counter-error':lambda r,b:struct.pack_into('<Q',b,16+8*7,0),
        'invented-cancelled-operation':lambda r,b:struct.pack_into('<Q',b,16+8*4,0),
        'unbounded-storage':lambda r,b:struct.pack_into('<Q',b,16+8*12,65537),
        'unclosed-writer':lambda r,b:r['native']['witness'].__setitem__('closed',False),
        'qualified-control':lambda r,b:r.__setitem__('qualified',True),
    }
    rejected = []
    for name,change in changes.items():
        bad,blob = copy.deepcopy(report),bytearray(raw); change(bad,blob)
        bad['trace_sha256'] = digest(blob) # Re-sign raw mutations; exercise semantic readers.
        try: validate(bad,build,bytes(blob))
        except (RuntimeError,KeyError,TypeError,ValueError,IndexError): rejected.append(name)
        else: raise RuntimeError('Operation witness corruption accepted: '+name)
    return rejected


def validate_files(folder,build):
    folder = Path(folder); output = folder/'controls.json'
    report,raw,receipt = read(output),(folder/'controls.json.events').read_bytes(),read(folder/'controls.json.writer.json')
    result = validate(report,build,raw); result['mutations_rejected'] = mutations(report,build,raw)
    require(receipt['schema']=='cairn-operation-witness-writer-1' and receipt['passed'] is True and
            receipt['terminal_receipt_write_included'] is False and natural(receipt['proof_bytes'])==output.stat().st_size and
            receipt['proof_sha256']==sha(output) and natural(receipt['trace_and_proof_bytes'])==len(raw)+output.stat().st_size and
            sum((folder/name).stat().st_size for name in ('controls.json','controls.json.events','controls.json.writer.json'))<=OUTPUT_CAP,
            'Complete process serialized evidence cap/proof writer differs')
    cycles.sequence([receipt['start'],receipt['end']])
    require(uint(report['native']['fixture_end_usec'])<=uint(receipt['start']['reads'][0]['wall_before_usec'])<=
            uint(receipt['start']['reads'][3]['wall_after_usec'])<=uint(receipt['begin_usec'])<=uint(receipt['end_usec'])<=
            uint(receipt['end']['reads'][0]['wall_before_usec']) and
            receipt['start']['thread_id']==receipt['end']['thread_id']==report['native']['thread'], 'Proof writer enclosure differs')
    result['serialized_process_evidence_bytes'] = sum((folder/name).stat().st_size for name in
        ('controls.json','controls.json.events','controls.json.writer.json'))
    result['proof_writer_process_cycles'] = list(map(str,cycles.demand(receipt['start'],receipt['end'],'process')))
    return result


def run_controls(exe,label,game=None):
    from build_support import REPORTS,run,write_json
    folder = REPORTS/('operation-witness-'+label); folder.mkdir(parents=True,exist_ok=True)
    output = folder/'controls.json'
    require(not output.exists(), 'Operation witness controls already ran; no automatic retry')
    args = [exe,'--headless']+(['--path',game] if game is not None else [])
    log = run(args+['--','--operation-witness-check','--operation-witness-output='+str(output)],'operation-witness-'+label,timeout=60)
    markers = [json.loads(line.split('CAIRN_OPERATION_WITNESS=',1)[1]) for line in log.splitlines() if 'CAIRN_OPERATION_WITNESS=' in line]
    require(markers==[dict(passed=True,output=str(output))] and 'SCRIPT ERROR:' not in log and 'ERROR:' not in log,
            'Operation actual-entry control failed')
    result = validate_files(folder,read(ROOT/'game/build_info.json'))
    write_json(folder/'validation.json',result); return result


def saved_controls(reports,build):
    results = {}
    for label in ('editor','release'):
        folder = Path(reports)/('operation-witness-'+label)
        result = validate_files(folder,build)
        require(result==read(folder/'validation.json'), 'Saved operation witness controls differ: '+label)
        results[label] = result
    return results
