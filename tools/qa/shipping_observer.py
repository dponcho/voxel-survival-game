"""Independent fixed-format observer attribution reader. No engine execution."""
import copy
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import struct

import shipping_cycles as cycles
from shipping_diagnostics import trial_evidence as common_trial_evidence

VERSION = 'm1-shipping-observer-attribution-1'
INVENTORY = 'm1-shipping-observer-inventory-1'
CAP = 33554432
HEADER = struct.Struct('<8sIIQQII')
RECORD = struct.Struct('<QQQIIIIIIQQ')
STAMP = struct.Struct('<QQQII')
SIZE = 192
SLOTS = ('preparation_queries','callback_queries','frontier','callback_output','native_witness',
         'tick_output','report_close','worker_lifetime','worker_qualification','worker_proxy',
         'worker_flush','boundary_snapshot')
SOURCES = ('m1_shipping_observer_runtime.gd','m1_shipping_observer_tests.gd','m1_full_height_runtime.gd','benchmark.gd','title.gd')
require, read, sha = cycles.require, cycles.read, cycles.sha


def decode(data):
    require(HEADER.size <= len(data) <= CAP, 'Missing/oversized observer trace')
    magic, version, size, cap, count, failure, lanes = HEADER.unpack_from(data)
    require((magic,version,size,cap)==(b'CAIRNOB1',1,SIZE,CAP) and 0 <= failure <= 7
            and 1 <= lanes <= 8 and len(data)==HEADER.size+count*SIZE, 'Observer header/population differs')
    records = []
    for offset in range(HEADER.size,len(data),SIZE):
        values = RECORD.unpack_from(data,offset)
        r = dict(zip(('id','parent','thread','slot','lane','start_section','end_section','submitted_section','complete','units','bytes'),values))
        require(r['id']==len(records)+1 and r['parent']<r['id'] and r['thread']>0 and 1<=r['slot']<=12
                and 1<=r['lane']<=lanes and r['complete'] in (0,1)
                and 0<=r['submitted_section']<=r['start_section']<=r['end_section']<=4, 'Observer identity/context malformed')
        r['reads'] = []
        for i in range(4):
            value, before, after, flags, error = STAMP.unpack_from(data,offset+RECORD.size+i*STAMP.size)
            require(0<=flags<=3 and before<=after, 'Observer raw flags/wall malformed')
            good = flags==3 and error==0
            require(good or value==0, 'Failed observer counter has a non-null payload')
            r['reads'].append(dict(cycles=value if good else None, available=bool(flags&1), success=bool(flags&2),
                                   error=error, wall_before_usec=before, wall_after_usec=after))
        records.append(r)
    return dict(cap_bytes=cap,record_count=count,failure_code=failure,lane_count=lanes),records


def ownership(records, lanes):
    """Exact containment identity per lane; no overlapping process/thread sum."""
    children = {r['id']:[] for r in records}
    roots = {lane:[] for lane in range(1,lanes+1)}
    for r in records:
        if r['parent']:
            p = records[r['parent']-1]
            require(p['lane']==r['lane'] and p['thread']==r['thread'], 'Observer child has a false owner')
            children[p['id']].append(r)
        else:
            roots[r['lane']].append(r)
    totals = []
    for lane, lane_roots in roots.items():
        require(lane_roots, 'Missing observer lane/root')
        identity = lane_roots[0]['thread']
        previous_wall = previous_cycle = 0
        nodes = []
        def stamp(value):
            nonlocal previous_wall, previous_cycle
            require(value['available'] and value['success'] and value['error']==0 and value['cycles'] is not None,
                    'Observer counter unavailable or failed')
            require(previous_wall<=value['wall_before_usec']<=value['wall_after_usec'] and previous_cycle<=value['cycles'],
                    'Observer lane counter/wall reversed or sibling spans overlap')
            previous_wall,previous_cycle = value['wall_after_usec'],value['cycles']
        def visit(r,depth=0):
            require(depth<8 and r['complete']==1 and r['thread']==identity, 'Observer span incomplete/deep or identity changed')
            if lane==1:
                require(r['start_section']==r['end_section']==r['submitted_section'] and r['slot'] not in (8,9,10,11),
                        'Main-thread observer crossed section or claimed writer ownership')
            else:
                require(r['slot'] in (8,9,10,11), 'Worker claimed main-thread observer ownership')
            stamp(r['reads'][0]);stamp(r['reads'][1])
            for child in children[r['id']]: visit(child,depth+1)
            stamp(r['reads'][2]);stamp(r['reads'][3])
            c = [v['cycles'] for v in r['reads']]
            r['full_cycles'],r['body_cycles'] = c[3]-c[0],c[2]-c[1]
            r['bookkeeping_cycles'] = r['full_cycles']-r['body_cycles']
            child_full = sum(ch['full_cycles'] for ch in children[r['id']])
            require(child_full<=r['body_cycles'], 'Child full cost exceeds parent body')
            r['exclusive_body_cycles'] = r['body_cycles']-child_full
            nodes.append(r)
        for r in lane_roots: visit(r)
        full = sum(r['full_cycles'] for r in lane_roots)
        exclusive = sum(r['exclusive_body_cycles'] for r in nodes)
        bookkeeping = sum(r['bookkeeping_cycles'] for r in nodes)
        require(full==exclusive+bookkeeping, 'Observer nesting double counted or lost work')
        if lane>1:
            require(len(lane_roots)==1 and lane_roots[0]['slot']==8
                    and all(ch['slot'] in (9,10,11) for ch in children[lane_roots[0]['id']]),
                    'Writer lifetime missing or has false ownership')
        totals.append(dict(lane=lane,thread_id=str(identity),root_full_cycles=str(full),
                           exclusive_body_cycles=str(exclusive),bookkeeping_cycles=str(bookkeeping)))
    for i,left in enumerate(totals[1:],1):
        require(left['thread_id']!=totals[0]['thread_id'], 'Worker reused the live main-thread identity')
        for j,right in enumerate(totals[1:i],1):
            if left['thread_id']==right['thread_id']:
                a,b=roots[left['lane']][0],roots[right['lane']][0]
                require(b['reads'][3]['wall_after_usec']<=a['reads'][0]['wall_before_usec']
                        or a['reads'][3]['wall_after_usec']<=b['reads'][0]['wall_before_usec'], 'Reused worker identity has overlapping incarnations')
    return totals


def ledger(path, metadata, *, failed=False):
    header,records = decode(Path(path).read_bytes())
    require(all(type(metadata[k]) is int and metadata[k]==v for k,v in header.items()) and type(metadata['trace_bytes']) is int and metadata['trace_bytes']==Path(path).stat().st_size
            and metadata['schema']=='cairn-observer-ledger-1' and metadata['file']==Path(path).name
            and type(metadata['passed']) is bool and type(metadata['closed']) is bool, 'Observer binary/metadata differ')
    if header['failure_code']:
        require(failed and metadata['passed'] is False and metadata['closed'] is True, 'Ignored observer failure')
        return dict(passed=False,records=records,lanes=[],groups=[],**header)
    require(metadata['passed'] is True and metadata['closed'] is True and records, 'Observer failed/empty trace')
    lanes = ownership(records,header['lane_count'])
    groups = {}
    for r in records:
        section = str(r['start_section']) if r['start_section']==r['end_section'] else 'cross_section'
        key = (r['lane'],r['slot'],section)
        g = groups.setdefault(key,dict(lane=r['lane'],slot=SLOTS[r['slot']-1],section=section,calls=0,units=0,bytes=0,
                                       inclusive_full_cycles=0,exclusive_body_cycles=0,bookkeeping_cycles=0))
        g['calls']+=1;g['units']+=r['units'];g['bytes']+=r['bytes']
        for k,rk in (('inclusive_full_cycles','full_cycles'),('exclusive_body_cycles','exclusive_body_cycles'),('bookkeeping_cycles','bookkeeping_cycles')):
            g[k]+=r[rk]
    for g in groups.values():
        for key in ('inclusive_full_cycles','exclusive_body_cycles','bookkeeping_cycles'): g[key]=str(g[key])
        if g['slot'] not in ('worker_qualification','worker_proxy'): g['bytes']=None
    return dict(passed=True,records=records,lanes=lanes,groups=list(groups.values()),**header)


def source_metadata(root):
    root=Path(root)
    return dict(method=VERSION,inventory_sha256=sha(root/'game/diagnostics/shipping_observer_inventory.json'),
        sources_sha256={name:sha(root/'game/scripts'/name) for name in SOURCES},
        native_sha256={name:sha(root/name) for name in ('native/sandbox_world/core/observer_ledger.h',
            'native/sandbox_world/godot/observer_probe.cpp','native/sandbox_world/godot/benchmark_probe.h',
            'native/sandbox_world/godot/benchmark_probe.cpp','native/sandbox_world/godot/report_sink.h',
            'native/sandbox_world/godot/report_sink.cpp')})


def verify_metadata(build,contents,root):
    require(build['shipping_observer']==source_metadata(root), 'Observer source/native inventory identity differs')
    require(contents['diagnostics/shipping_observer_inventory.json']==(Path(root)/'game/diagnostics/shipping_observer_inventory.json').read_bytes(),
            'Published observer inventory differs')
    for name in SOURCES:
        stem='scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC') and ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'],
                'Missing observer tokenized source: '+name)


def validate_controls(report,folder,build):
    require(report['schema']=='cairn-shipping-observer-controls-1' and report['method']==VERSION and report['build']==build
            and report['passed'] is True and report['qualified'] is False and report['fixed_work_dispatch'] is True,
            'Observer matching-binary controls failed')
    native=report['native']; meta=native['ledger']
    actual=ledger(Path(folder)/meta['file'],meta)
    worker=[r for r in actual['records'] if r['slot']==8]
    jobs=[r for r in actual['records'] if r['slot'] in (9,10)]
    require(native['passed'] is True and native['worker_joined'] is True and native['worker_completed']==2
            and 0<=native['elapsed_usec']<=5000000 and len(worker)==1 and sorted(r['slot'] for r in jobs)==[9,10]
            and actual['record_count']==6 and actual['lane_count']==2,
            'Observer native/worker controls missing')
    control_path=Path(folder)/meta['file']
    require(Path(str(control_path)+'.csv').read_bytes()==b'observer control\n'
            and Path(str(control_path)+'.csv.proxy.tmp').read_bytes()==b'proxy\n'
            and {r['slot']:r['bytes'] for r in jobs}=={9:17,10:6}, 'Observer worker UTF-8 payload controls differ')
    cycles.sequence([native['process_start'],native['process_end']])
    process=cycles.demand(native['process_start'],native['process_end'],'process')
    require(process[1]>=worker[0]['full_cycles'], 'Observer process counter lost closed worker demand')
    require(cycles.uint(native['process_start']['reads'][3]['wall_after_usec'])<=worker[0]['reads'][0]['wall_before_usec']
            <=worker[0]['reads'][3]['wall_after_usec']<=cycles.uint(native['process_end']['reads'][0]['wall_before_usec']),
            'Observer control worker escaped its joined process interval')
    require([f['name'] for f in report['faults']]==['invalid-slot','wrong-token','unclosed-span'], 'Observer fault controls missing')
    for f in report['faults']:
        require(f['started'] is True and f['ledger']['failure_code']=={'invalid-slot':2,'wrong-token':3,'unclosed-span':6}[f['name']],
                'Observer failure control changed')
        ledger(Path(folder)/f['ledger']['file'],f['ledger'],failed=True)
    return dict(passed=True,qualified=False,method=VERSION,records=actual['record_count'],native_faults=3,
                closed_worker_cycles=str(worker[0]['full_cycles']))


def expected_protocol():
    return [('warmup',0)]+[('bare',i) for i in range(4)]


def verify_prefix(trials):
    require(1<=len(trials)<=5 and [(t['group'],t['index']) for t in trials]==expected_protocol()[:len(trials)],
            'Observer sequence repeated, padded, reordered or continued')
    for i,t in enumerate(trials):
        require(t['id']=='AB-H2-observer-%s-%d'%(t['group'],t['index']) and t['diagnostic_mode']=='bare'
                and t['dose_enabled'] is False and t['dose']['requested_tick_cycles']==t['dose']['reference_cycles']=='0', 'Observer run enabled shipping/positive work')
        if i<len(trials)-1: require(t['valid'] is True and t['complete'] is True, 'Observer continued after a failed/partial trial')
    require(len(trials)==5 or trials[-1]['valid'] is False, 'Observer stopped early without a failed trial')


def trial_ledger(folder,t):
    path=Path(folder)/(t['id']+'-observers.bin');meta=t['observer']
    if meta.get('failure_code')==7:
        require(t['valid'] is False and meta.get('passed') is False and type(meta.get('closed')) is bool
                and meta.get('schema')=='cairn-observer-ledger-1' and meta.get('file')==path.name
                and meta.get('cap_bytes')==CAP, 'Observer I/O failure was hidden or malformed')
        retained=path.stat().st_size if path.exists() else None
        require((retained is None or 0<=retained<=CAP) and t['observer_sha256']==(sha(path) if path.exists() else ''),
                'Retained observer I/O failure bytes/hash differ')
        return dict(passed=False,evidence_integrity='retained_io_failure',failure_code=7,
                    retained_bytes=retained,declared_written_bytes=meta.get('trace_bytes'),
                    records=[],lanes=[],groups=[],reason='Raw attribution unavailable after declared I/O failure; never a measured zero.')
    require(sha(path)==t['observer_sha256'], 'Observer raw trace hash differs')
    return ledger(path,meta,failed=not t['valid'])


def observer_evidence(folder,t):
    folder=Path(folder);path=folder/(t['id']+'-observers.bin')
    a=trial_ledger(folder,t)
    if not a['passed']: return {k:v for k,v in a.items() if k!='records'}
    rows=a['records']; main=[r for r in rows if r['lane']==1]
    if t['cycle']:
        require(all(int(lane['root_full_cycles'])<=cycles.natural(t['cycle']['complete'][1]) for lane in a['lanes']),
                'Observed thread lane exceeds enclosing process demand')
    for r in rows:
        require(t['start_usec']<=r['reads'][0]['wall_before_usec']<=r['reads'][3]['wall_after_usec']<=t['end_usec'],
                'Observer span outside complete trial')
    emission=t['observer']
    cycles.raw_observation(emission['emit_start']);cycles.raw_observation(emission['emit_end'])
    try:
        cycles.sequence([emission['emit_start'],emission['emit_end']])
        emit_process=cycles.demand(emission['emit_start'],emission['emit_end'],'process')
        emit_thread=cycles.demand(emission['emit_start'],emission['emit_end'],'thread')
    except RuntimeError:
        require(t['valid'] is False,'Observer emission counter failure ignored')
        return dict(passed=False,record_count=a['record_count'],lanes=a['lanes'],groups=a['groups'],
                    emission_process_cycles=[],emission_thread_cycles=[],reason='Retained unavailable/failed emission counters')
    if t['cycle']:
        cycles.sequence([emission['emit_end'],t['cycle_boundaries'][-1]['before']])
    require(max(r['reads'][3]['wall_after_usec'] for r in rows)<=cycles.uint(emission['emit_start']['reads'][0]['wall_before_usec']),
            'Observer records continued after drain/seal')
    if t['complete']:
        counts={slot:[r for r in main if r['slot']==slot] for slot in range(1,13)}
        callbacks=t['callback_count']
        require(len(counts[5])==sum(r['units'] for r in counts[5])==4320 and len(counts[6])==4323
                and sum(r['units'] for r in counts[6])==4320 and len(counts[12])==4 and counts[1], 'Observer fixed tick/boundary cadence differs')
        require([r['start_section'] for r in counts[6] if r['units']==0]==[2,3,4]
                and all(r['units'] in (0,1) and r['bytes']==0 for r in main), 'Observer handover units or reserved bytes differ')
        require([r['start_section'] for r in counts[12]]==[0,1,2,3], 'Observer boundary section ownership differs')
        for r,b in zip(counts[12],t['cycle_boundaries'][1:5]):
            require(cycles.uint(b['before']['reads'][3]['wall_after_usec'])<=r['reads'][0]['wall_before_usec']
                    <=r['reads'][3]['wall_after_usec']<=cycles.uint(b['after']['reads'][0]['wall_before_usec']),
                    'Observer boundary snapshot detached from shared bracket')
            if b['before']['status']==b['after']['status']=='measured':
                require(str(r['thread'])==b['before']['thread_id']==b['after']['thread_id']
                        and cycles.uint(b['before']['reads'][2]['cycles'])<=r['reads'][0]['cycles']
                        <=r['reads'][3]['cycles']<=cycles.uint(b['after']['reads'][1]['cycles']),
                        'Observer snapshot counter values detached from shared thread reads')
        require(all(len(counts[k])==sum(r['units'] for r in counts[k])==callbacks for k in (2,3,4)),
                'Observer callback cadence differs')
        with (folder/(t['id']+'-frames.csv')).open(encoding='utf-8-sig',newline='') as f: frames=list(csv.DictReader(f))
        require(len(frames)==callbacks, 'Observer callback population changed')
        for i,(r,frame) in enumerate(zip(counts[4],frames)):
            end=int(frames[i+1]['entry_usec']) if i+1<len(frames) else t['callback_last_end_usec']
            require(int(frame['entry_usec'])<=r['reads'][0]['wall_before_usec']<=r['reads'][3]['wall_after_usec']<=end,
                    'Observer callback detached from its real frame')
            children=[c for c in (counts[2][i],counts[3][i]) if c['parent']==r['id']]
            require(len(children)==2, 'Observer query/frontier has false callback owner')
        work=[json.loads(line) for line in (folder/(t['id']+'-cycles.jsonl')).read_text(encoding='utf-8-sig').splitlines()]
        for r,w in zip(counts[5],work):
            require(r['reads'][1]['wall_after_usec']<=cycles.uint(w['wall_start_usec'])<=cycles.uint(w['wall_end_usec'])<=r['reads'][2]['wall_before_usec'],
                    'Observer native witness detached from real physics work')
            require(str(r['thread'])==w['start']['thread_id']==w['end']['thread_id']
                    and r['reads'][1]['cycles']<=cycles.uint(w['start']['reads'][1]['cycles'])
                    <=cycles.uint(w['start']['reads'][2]['cycles'])<=cycles.uint(w['end']['reads'][1]['cycles'])
                    <=cycles.uint(w['end']['reads'][2]['cycles'])<=r['reads'][2]['cycles'],
                    'Observer native counter values detached from original per-tick witness')
    workers=t['observer_writers']
    require([w['file'] for w in workers]==[t['id']+suffix+'-frames.csv' for suffix in ('-preparation','','-retirement')]
            and {w['worker']['lane'] for w in workers}=={2,3,4} and a['lane_count']==4, 'Observer writer phases/lanes missing, repeated or escaped')
    writer_roots={r['lane']:r for r in rows if r['slot']==8}
    for proof in workers:
        info=proof['worker'];lane=info['lane'];root=writer_roots[lane]
        jobs=[r for r in rows if r['lane']==lane and r['slot'] in (9,10)]
        qualification=[r for r in jobs if r['slot']==9];proxy=[r for r in jobs if r['slot']==10]
        require(info['joined'] is True and info['failed'] is False and info['completed']==len(jobs)
                and info['qualification_count']==len(qualification) and info['proxy_count']==len(proxy)
                and info['qualification_bytes']==sum(r['bytes'] for r in qualification)
                and info['proxy_bytes']==sum(r['bytes'] for r in proxy), 'Observer worker counts/bytes/closure differ')
        files=[folder/(proof['file']+suffix) for suffix in ('','.operations.csv','.edits.jsonl')]
        require(sum(p.stat().st_size for p in files)==info['qualification_bytes'], 'Observer writer payload bytes differ from original files')
        require(len(proxy)==(72 if proof['file']==t['id']+'-frames.csv' else 0), 'Observer lost/changed operational proxy work')
        cycles.sequence([proof['process_start'],proof['process_end']])
        process=cycles.demand(proof['process_start'],proof['process_end'],'process')
        require(cycles.uint(proof['process_start']['reads'][3]['wall_after_usec'])<=root['reads'][0]['wall_before_usec']
                <=root['reads'][3]['wall_after_usec']<=cycles.uint(proof['process_end']['reads'][0]['wall_before_usec'])
                and process[1]>=root['full_cycles'], 'Observer process/closure lost worker incarnation')
    return dict(passed=True,record_count=a['record_count'],trace_bytes=path.stat().st_size,lanes=a['lanes'],groups=a['groups'],
                emission_process_cycles=list(map(str,emit_process)),emission_thread_cycles=list(map(str,emit_thread)),
                scope='Perturbing attribution only; no thread/process addition, fitted subtraction or shipping-cost estimate.')


def reconcile(folder,build,inventory_path):
    folder=Path(folder);p=read(folder/'observer-attribution.json');s=read(folder/'summary.json')
    require(p['version']==VERSION and p['policy']==cycles.POLICY and p['build']==s['build']==build
            and p['inventory']==read(inventory_path) and p['inventory']['version']==INVENTORY
            and p['inventory_sha256']==sha(inventory_path) and p['max_trials']==5
            and p['qualified'] is False and p['target_performance']=='not_run' and p['measurement_valid'] is False
            and s['qualified'] is False and s['benchmark_mode']=='observer-attribution', 'Observer batch identity/qualification changed')
    trials=p['trials'];verify_prefix(trials)
    assessment=dict(method=VERSION,qualified=False,outcome='inconclusive',controls=dict(valid=False),shipping_cost_estimate=None,abort_reason=p['abort_reason'])
    require(p['assessment']==assessment and p['abort_reason'] and s['shipping_diagnostic_qualification']==assessment,
            'Observer attribution forged a cost/qualification verdict')
    records=[]
    for t in trials:
        name=t['id']
        if not t['complete']:
            require(read(folder/(name+'-partial.json'))==t and t['valid'] is False and t['abort_reason'], 'Observer partial trial forged')
            cycles.dose_evidence(folder,t,partial=True)
            a=trial_ledger(folder,t)
            records.append(dict(id=name,complete=False,attribution_valid=False,observer_failure=a['failure_code']))
            continue
        complete=read(folder/(name+'-complete.json'));terminal=read(folder/(name+'-boundary.json'))
        require(all(t.get(k)==v for k,v in complete.items()) and terminal['complete_sha256']==sha(folder/(name+'-complete.json'))
                and all(t.get(k)==v for k,v in terminal.items() if k not in ('complete_sha256','cycle')), 'Observer saved lifecycle differs')
        expected=cycles.retained_partition(t['cycle_boundaries'])
        require(terminal['cycle']==expected, 'Observer shared CPU boundary differs')
        marker=t['marker_cycles'];cycles.raw_observation(marker['start']);cycles.raw_observation(marker['end'])
        try:
            cycles.sequence([marker['start'],marker['end']])
            marker_bounds=list(map(str,cycles.demand(marker['start'],marker['end'],'process')))
        except RuntimeError:
            require(t['valid'] is False and t['checks']['marker'] is False,'Observer marker counter failure ignored')
            marker_bounds=[]
        require(t['end_usec']<=t['marker_start_usec']<=t['marker_end_usec'] and
                cycles.uint(marker['start']['reads'][3]['wall_after_usec'])<=t['marker_start_usec']
                and t['marker_end_usec']<=cycles.uint(marker['end']['reads'][0]['wall_before_usec']), 'Observer marker outside measured bounds')
        if expected: expected['marker']=marker_bounds
        require(t['cycle']==expected, 'Observer complete partition/marker changed')
        dose=cycles.dose_evidence(folder,t)
        a=observer_evidence(folder,t)
        checks=cycles.derive_checks(t)
        require(t['pre_boundary_checks']==checks, 'Observer original work guard flags differ')
        checks.update(cycles=bool(expected),dose=dose['witness_valid'],marker=bool(marker_bounds),observers=a['passed'])
        require(t['checks']==checks and t['valid'] is all(checks.values()), 'Observer guard failure was hidden')
        shared={}
        if all(v for k,v in checks.items() if k not in ('operations','cycles','dose','marker','observers')):
            view=copy.deepcopy(t);view['checks']={k:v for k,v in checks.items() if k not in ('cycles','dose','marker','observers')}
            view['valid']=view['checks']['operations'];view['dose']=dict(actual_usec=0,hash_updates=0,ticks=0,requested_tick_usec=0)
            shared=common_trial_evidence(folder,view,sha(inventory_path),method_version=VERSION,verify_saved_boundary=False)
        records.append(dict(id=name,complete=True,attribution_valid=t['valid'],observer=a,checks=checks,common=shared))
    require(p['trial_guards_valid'] is all(t['valid'] for t in trials) and s['scenarios']==[t['report'] for t in trials if t['complete']]
            and s['operation_phases']==[phase for t in trials for phase in t['phases']], 'Observer batch guard/lifecycle changed')
    if len(trials)==5:
        require(cycles.rational_json(p['descriptive_cycle_null'])==cycles.envelope(trials[1:5]), 'Observer descriptive CPU null changed')
        expected_elapsed=cycles.elapsed_envelope(trials[1:5]);actual_elapsed=p['elapsed_descriptive']['bare']
        require(actual_elapsed.get('valid') is bool(expected_elapsed), 'Observer elapsed descriptive validity changed')
        if expected_elapsed:
            require(all(math.isclose(actual_elapsed[k],float(v),rel_tol=1e-10,abs_tol=1e-12) for k,v in expected_elapsed.items()),
                    'Observer elapsed descriptive envelope changed')
    else:
        require(p['descriptive_cycle_null']=={} and p['elapsed_descriptive']=={}, 'Observer incomplete prefix invented a null envelope')
    integrity='verified' if all(t['complete'] for t in trials) and all(r.get('observer',{}).get('evidence_integrity')!='retained_io_failure' for r in records) else 'retained_partial'
    return dict(passed=True,evidence_integrity=integrity,
                attribution_valid=all(t['valid'] for t in trials),measurement_valid=False,cycle_cost='inconclusive',
                shipping_cost_estimate=None,qualified=False,target_performance='not_run',trials=len(trials),records=records)
