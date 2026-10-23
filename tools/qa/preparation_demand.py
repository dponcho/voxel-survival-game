"""Independent CAIRNOB2 ownership, lifecycle and real-entry controls. No route launch."""
import copy
import csv
import json
import math
from pathlib import Path
import struct

import shipping_cycles as cycles
import observer_disposal as disposal
from shipping_diagnostics import trial_evidence as common_trial_evidence

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'm1-preparation-demand-attribution-1'
INVENTORY = 'm1-preparation-demand-inventory-1'
SCHEMA = 'cairn-preparation-demand-controls-1'
CAP, SIZE = 33554432, 192
HEADER, RECORD, STAMP = struct.Struct('<8sIIQQII'), struct.Struct('<QQQIIIIIIQQ'), struct.Struct('<QQQII')
SOURCES = ('m1_preparation_demand_runtime.gd', 'm1_preparation_demand_tests.gd', 'title.gd',
           'm1_full_height_runtime.gd', 'benchmark.gd')
NATIVE = ('core/preparation_observer.h', 'core/observer_ledger.h', 'core/observer_disposal.h',
          'godot/preparation_probe.cpp', 'godot/fixture_generator.cpp', 'godot/observer_probe.cpp',
          'godot/benchmark_probe.h', 'godot/benchmark_probe.cpp', 'godot/report_sink.cpp', 'godot/report_sink.h')
require, read, sha, uint = cycles.require, cycles.read, cycles.sha, cycles.uint


def source_metadata(root):
    root = Path(root)
    return dict(method=VERSION, inventory=INVENTORY, raw_version=2,
                inventory_sha256=sha(root/'game/diagnostics/preparation_demand_inventory.json'),
                sources_sha256={n: sha(root/'game/scripts'/n) for n in SOURCES},
                native_sha256={n: sha(root/'native/sandbox_world'/n) for n in NATIVE},
                patches_sha256=sha(root/'build/patches/voxel/m1-preparation.json'))


def verify_metadata(build, contents, root):
    require(build['preparation_demand'] == source_metadata(root), 'Preparation source/native identity differs')
    require(sha(Path(root)/'game/diagnostics/preparation_demand_inventory.json') ==
            build['preparation_demand']['inventory_sha256'], 'Preparation inventory differs')
    for name in SOURCES:
        stem = 'scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC') and
                ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'], 'Missing preparation bytecode: '+name)
    require(contents['diagnostics/preparation_demand_inventory.json'] ==
            (Path(root)/'game/diagnostics/preparation_demand_inventory.json').read_bytes(), 'Packaged preparation inventory differs')


def decode(data, *, failed_cap=False):
    require(HEADER.size <= len(data) <= CAP, 'Missing/oversized preparation trace')
    magic, version, size, cap, count, failure, lanes = HEADER.unpack_from(data)
    require((magic, version, size) == (b'CAIRNOB2', 2, SIZE) and 0 <= failure <= 7 and
            1 <= lanes <= 8 and len(data) == HEADER.size+count*SIZE and len(data) <= cap <= CAP,
            'Preparation header/population differs')
    require(cap == CAP or (failed_cap and failure == 1 and cap == HEADER.size+SIZE), 'Unexpected preparation cap')
    rows = []
    for offset in range(HEADER.size, len(data), SIZE):
        r = dict(zip(('id','parent','thread','slot','lane','start_section','end_section','submitted_section',
                      'complete','units','bytes'), RECORD.unpack_from(data, offset)))
        require(r['id'] == len(rows)+1 and r['parent'] < r['id'] and r['thread'] > 0 and
                1 <= r['slot'] <= 16 and 1 <= r['lane'] <= lanes and r['complete'] in (0,1) and
                0 <= r['submitted_section'] <= r['start_section'] <= r['end_section'] <= 4,
                'Malformed preparation owner/context')
        r['reads'] = []
        for i in range(4):
            n, before, after, flags, error = STAMP.unpack_from(data, offset+RECORD.size+i*STAMP.size)
            require(flags in (0,1,3) and before <= after and (flags == 3 and error == 0 or n == 0),
                    'Malformed preparation raw flags/error/null')
            r['reads'].append(dict(cycles=n if flags == 3 and error == 0 else None,
                                   wall_before_usec=before, wall_after_usec=after, flags=flags, error=error))
        rows.append(r)
    return dict(cap_bytes=cap, record_count=count, failure_code=failure, lane_count=lanes), rows


def ownership(rows, lanes, witness):
    require(witness['schema'] == 'cairn-preparation-owners-1' and witness['passed'] is True and
            witness['unpublished'] is True and witness['drained'] is True and
            type(witness['in_flight']) is int and witness['in_flight'] == 0 and
            witness['configured_workers'] == 1 and witness['session_destroyed'] is True and
            type(witness['session_bytes']) is int and 0 < witness['session_bytes'] < 65536,
            'Preparation publisher/drain/destruction unavailable')
    main = uint(witness['main_thread'])
    require(main > 0, 'Missing preparation boundary main identity')
    owners = {}
    identities = set()
    for owner in witness['owners']:
        lane, tid, incarnation = owner['lane'], uint(owner['thread']), uint(owner['incarnation'])
        require(type(lane) is int and 2 <= lane <= lanes and lane not in owners and
                tid > 0 and tid != main and incarnation > 0 and incarnation not in identities and
                owner['pool'] == 'VoxelEngine.general' and owner['worker_index'] == 0 and
                owner['pool_joined'] is False and owner['in_flight'] == 0,
                'Unregistered/duplicate/unexpected terrain worker')
        attached, detached = uint(owner['attached_usec']), uint(owner['detached_usec'])
        retired = None if owner['retired_usec'] is None else uint(owner['retired_usec'])
        require(attached > 0 and attached <= detached and (retired is None or attached <= retired <= detached),
                'Missing terrain registration/retirement/detach')
        for previous in owners.values():
            # The pool has one worker, irrespective of whether Windows reused TID.
            require(previous['retired'] is not None and previous['retired'] <= attached,
                    'Terrain incarnations overlap or replacement lacks real retirement')
        identities.add(incarnation)
        owners[lane] = dict(thread=tid, attached=attached, detached=detached, retired=retired)
    children = {r['id']: [] for r in rows}
    roots = {lane: [] for lane in range(1,lanes+1)}
    for r in rows:
        if r['parent']:
            p = rows[r['parent']-1]
            require(p['thread'] == r['thread'] and p['lane'] == r['lane'], 'Preparation child has false owner')
            children[p['id']].append(r)
        else: roots[r['lane']].append(r)
    totals, population, crossings = [], {s: [] for s in range(13,17)}, []
    writer_lifetimes = []
    for lane, lane_roots in roots.items():
        require(lane_roots, 'Missing preparation lane/root')
        tid = lane_roots[0]['thread']
        previous_wall = previous_cycles = 0
        visited = []
        def stamp(s):
            nonlocal previous_wall, previous_cycles
            require(s['flags'] == 3 and s['error'] == 0 and s['cycles'] is not None and
                    previous_wall <= s['wall_before_usec'] <= s['wall_after_usec'] and
                    previous_cycles <= s['cycles'], 'Preparation raw failure/reversal or overlapping siblings')
            previous_wall, previous_cycles = s['wall_after_usec'], s['cycles']
        def visit(r, depth=0):
            require(depth < 8 and r['complete'] == 1 and r['thread'] == tid, 'Incomplete/deep/changed preparation owner')
            slot = r['slot']
            if lane == 1:
                require(tid == main and slot not in (8,9,10,11,13,14) and
                        r['submitted_section'] == r['start_section'] == r['end_section'], 'Main ownership/section crossing')
            elif lane in owners:
                require(tid == owners[lane]['thread'] and slot in (13,14), 'Terrain lane claimed another owner')
                require(owners[lane]['attached'] <= r['reads'][0]['wall_before_usec'] and
                        r['reads'][3]['wall_after_usec'] <= (owners[lane]['retired'] or owners[lane]['detached']),
                        'Terrain scope outside registered incarnation')
            else:
                require(tid != main and slot in (8,9,10,11), 'Writer lane claimed native/main ownership')
            if slot >= 13:
                require(r['start_section'] == r['submitted_section'] == 0 and r['units'] == 1 and
                        r['bytes'] in ((1,2) if slot == 14 else (1,)), 'Native admission/attempt/outcome differs')
                population[slot].append(r)
                if r['end_section'] != 0: crossings.append(r['id'])
            stamp(r['reads'][0]); stamp(r['reads'][1])
            for child in children[r['id']]: visit(child, depth+1)
            stamp(r['reads'][2]); stamp(r['reads'][3])
            c = [s['cycles'] for s in r['reads']]
            r['full_cycles'], r['body_cycles'] = c[3]-c[0], c[2]-c[1]
            r['bookkeeping_cycles'] = r['full_cycles']-r['body_cycles']
            child_full = sum(child['full_cycles'] for child in children[r['id']])
            require(child_full <= r['body_cycles'], 'Native child exceeds parent body')
            r['exclusive_body_cycles'] = r['body_cycles']-child_full
            visited.append(r)
        for r in lane_roots: visit(r)
        full = sum(r['full_cycles'] for r in lane_roots)
        exclusive = sum(r['exclusive_body_cycles'] for r in visited)
        bookkeeping = sum(r['bookkeeping_cycles'] for r in visited)
        require(full == exclusive+bookkeeping, 'Preparation nested union double-counted')
        if lane > 1 and lane not in owners:
            require(len(lane_roots) == 1 and lane_roots[0]['slot'] == 8 and
                    all(c['slot'] in (9,10,11) for c in children[lane_roots[0]['id']]), 'Writer lifetime missing')
            writer_lifetimes.append(lane_roots[0])
        totals.append(dict(lane=lane, thread=str(tid), root_full_cycles=str(full),
                           exclusive_body_cycles=str(exclusive), bookkeeping_cycles=str(bookkeeping)))
    # A writer may reuse a retired terrain or earlier writer TID, never a live one.
    for a in writer_lifetimes:
        for b in writer_lifetimes:
            if a['id'] >= b['id'] or a['thread'] != b['thread']: continue
            require(a['reads'][3]['wall_after_usec'] <= b['reads'][0]['wall_before_usec'], 'Writer incarnations overlap')
        for o in owners.values():
            if a['thread'] == o['thread']:
                require(o['retired'] is not None and o['retired'] <= a['reads'][0]['wall_before_usec'],
                        'Writer reused live terrain identity')
    require(len(witness['counts']) == 4, 'Missing native attempt populations')
    counts = []
    for slot, c in zip(range(13,17), witness['counts']):
        rs = population[slot]
        require(c['slot'] == slot and uint(c['attempted']) == uint(c['completed']) == len(rs) and
                uint(c['overload']) == sum(r['bytes'] == 2 for r in rs) and
                uint(c['crossing']) == sum(r['end_section'] != 0 for r in rs), 'Native attempt/completion/outcome population differs')
        counts.append(dict(slot=slot, attempted=len(rs), overload=uint(c['overload']), crossing=uint(c['crossing']),
                           inclusive_full_cycles=str(sum(r['full_cycles'] for r in rs)),
                           body_cycles=str(sum(r['body_cycles'] for r in rs)),
                           bookkeeping_cycles=str(sum(r['bookkeeping_cycles'] for r in rs)),
                           exclusive_body_cycles=str(sum(r['exclusive_body_cycles'] for r in rs))))
    return dict(lanes=totals, native=counts, crossing_ids=crossings,
                crossing_policy='Retained complete, separate from preparation; no wall split or clipping')


def trace(path, metadata, witness):
    data = Path(path).read_bytes()
    header, rows = decode(data)
    require(metadata['schema'] == 'cairn-observer-ledger-2' and metadata['passed'] is True and
            metadata['closed'] is True and metadata['file'] == Path(path).name and header['failure_code'] == 0 and
            all(type(metadata[k]) is int and metadata[k] == v for k,v in header.items()) and
            type(metadata['trace_bytes']) is int and metadata['trace_bytes'] == len(data), 'Preparation emission differs')
    cycles.sequence([metadata['emit_start'], metadata['emit_end']])
    result = ownership(rows, header['lane_count'], witness)
    return dict(**header, bytes=len(data), sha256=sha(path), ownership=result), rows


def validate(report, folder, build):
    folder = Path(folder)
    require(report['schema'] == SCHEMA and report['build'] == build and report['passed'] is True and
            report['qualified'] is False and report['target_performance'] == 'not_run', 'Preparation controls identity/result differs')
    n = report['native']
    require(report['context_refusal'] == dict(passed=False, qualified=False) and n['terrain_in_tree'] is True and
            not (folder/(n['ledger']['file'][:-4]+'.orphan.bin')).exists(), 'Terrain control did not reject an orphan or prove tree context')
    require(n['passed'] is True and n['qualified'] is False and uint(n['fixture_limit_usec']) == 5000000 and
            0 <= uint(n['fixture_end_usec'])-uint(n['fixture_start_usec']) <= 5000000, 'Preparation control failed or exceeded cap')
    cycles.sequence([n['process_start'], n['ledger']['emit_start'], n['ledger']['emit_end'],
                     n['release']['counter_start'], n['release']['counter_end'], n['process_end']])
    raw, rows = trace(folder/n['ledger']['file'], n['ledger'], n['ownership'])
    require(n['ownership']['main_thread'] == n['process_start']['thread_id'] == n['process_end']['thread_id'],
            'Control main identity detached from direct boundary observations')
    process_upper = cycles.demand(n['process_start'], n['process_end'], 'process')[1]
    require(all(int(lane['root_full_cycles']) <= process_upper for lane in raw['ownership']['lanes']),
            'Direct lane exceeds enclosing process bound')
    require(all(uint(n['process_start']['reads'][3]['wall_after_usec']) <= r['reads'][0]['wall_before_usec'] <=
                r['reads'][3]['wall_after_usec'] <= uint(n['ledger']['emit_start']['reads'][0]['wall_before_usec'])
                for r in rows), 'Control span escaped start or continued after drain/seal')
    disposal.disposal(n['release'], 'disposed')
    require(n['release']['failure_code'] == 0 and n['release']['storage_before']['record_count'] == len(rows), 'Release lost native records')
    counts = raw['ownership']['native']
    require((counts[0]['attempted'], counts[0]['crossing'], counts[1]['attempted'], counts[1]['overload']) ==
            (3,1,4,2) and counts[2]['attempted'] > 0 and counts[3]['attempted'] == 1,
            'Real four entries, overload or handover were not exercised')
    require(len(n['ownership']['owners']) == 2 and n['ownership']['owners'][0]['retired_usec'] is not None and
            n['ownership']['owners'][1]['retired_usec'] is None and
            any(r['parent'] and r['slot'] in (15,16) for r in rows), 'Missing actual replacement, persistent detach or nested main entry')
    for key, expected in (('generated',3), ('meshed',2), ('overloads',2)):
        require(n['ownership']['native_end'][key]-n['native_start'][key] == expected, 'Original native work did not reconcile: '+key)
    w = n['worker']
    require(w == dict(lane=4, joined=True, failed=False, completed=2, qualification_count=1, proxy_count=1,
                      qualification_bytes=20, proxy_bytes=6), 'Real joined/detached writer differs')
    require((folder/(n['ledger']['file']+'.csv')).read_bytes() == b'preparation control\n' and
            (folder/(n['ledger']['file']+'.csv.proxy.tmp')).read_bytes() == b'proxy\n', 'Writer UTF-8 bytes differ')
    writer = [r for r in rows if r['slot'] in (9,10)]
    require(len(writer) == 2 and sum(r['bytes'] for r in writer) == 26 and all(r['lane'] == 4 for r in writer), 'Writer raw population differs')
    expected_faults = [('counter',4,1), ('cap',1,1), ('owner',2,0), ('main_crossing',5,1), ('write',7,None)]
    require(len(n['faults']) == len(expected_faults), 'Missing real-entry fault controls')
    faults = []
    for f,(name,code,count) in zip(n['faults'],expected_faults):
        require(f['name'] == name and f['ledger']['passed'] is False and f['ledger']['failure_code'] == code,
                'Hidden preparation fault verdict')
        disposal.disposal(f['release'], 'disposed')
        require(f['release']['failure_code'] == code and f['ownership']['session_destroyed'] is True and
                f['ownership']['unpublished'] is True and f['ownership']['in_flight'] == 0, 'Fault cleanup lost failure or owner')
        p = folder/f['ledger']['file']
        if code == 7:
            require(f['ledger']['closed'] is False and f['ledger']['trace_bytes'] == 0 and not p.exists(), 'Write failure invented trace')
            faults.append(dict(name=name, failure_code=code, trace_available=False)); continue
        data = p.read_bytes(); h, rs = decode(data, failed_cap=name == 'cap')
        require(h['failure_code'] == code and len(rs) == count and f['ledger']['trace_bytes'] == len(data) and
                f['ledger']['closed'] is True and all(f['ledger'][k] == v for k,v in h.items()),
                'Fault prefix lost or padded')
        if code == 4:
            require(all(s['cycles'] is None and s['flags'] == 1 and s['error'] == 6 for s in rs[0]['reads']), 'Raw counter fault repaired')
        if code == 5: require(rs[0]['start_section'] == 0 and rs[0]['end_section'] == 1, 'Main crossing clipped')
        faults.append(dict(name=name, failure_code=code, bytes=len(data), sha256=sha(p)))
    return dict(passed=True, qualified=False, raw=raw, faults=faults,
                elapsed_usec=uint(n['fixture_end_usec'])-uint(n['fixture_start_usec']), engine_executed=False)


def mutations(report, folder, build):
    changes = {
        'invalid-terrain-context': lambda n: n.__setitem__('terrain_in_tree',False),
        'live-publisher': lambda n: n['ownership'].__setitem__('unpublished',False),
        'retained-session': lambda n: n['ownership'].__setitem__('session_destroyed',False),
        'live-scope': lambda n: n['ownership'].__setitem__('in_flight',1),
        'pool-join-invention': lambda n: n['ownership']['owners'][1].__setitem__('pool_joined',True),
        'missing-retirement': lambda n: n['ownership']['owners'][0].__setitem__('retired_usec',None),
        'same-incarnation': lambda n: n['ownership']['owners'][1].__setitem__('incarnation',n['ownership']['owners'][0]['incarnation']),
        'wrong-os-thread': lambda n: n['ownership']['owners'][1].__setitem__('thread',n['ownership']['main_thread']),
        'missing-detach': lambda n: n['ownership']['owners'][1].__setitem__('detached_usec',None),
        'unexpected-worker': lambda n: n['ownership']['owners'][1].__setitem__('worker_index',1),
        'missing-attempt': lambda n: n['ownership']['counts'][1].__setitem__('attempted','3'),
        'double-completion': lambda n: n['ownership']['counts'][0].__setitem__('completed','4'),
        'hidden-overload': lambda n: n['ownership']['counts'][1].__setitem__('overload','0'),
        'clipped-crossing': lambda n: n['ownership']['counts'][0].__setitem__('crossing','0'),
        'changed-native-work': lambda n: n['ownership']['native_end'].__setitem__('generated',n['native_start']['generated']+4),
        'unjoined-writer': lambda n: n['worker'].__setitem__('joined',False),
        'retained-recorder': lambda n: n['release'].__setitem__('strong_owners',2),
        'false-destruction': lambda n: n['release'].__setitem__('disposed',False),
        'hidden-raw-failure': lambda n: n['faults'][0]['ledger'].__setitem__('failure_code',0),
        'qualified-cost': lambda n: n.__setitem__('qualified',True),
        'over-cap-fixture': lambda n: n.__setitem__('fixture_end_usec',str(uint(n['fixture_start_usec'])+5000001)),
    }
    rejected = []
    for name,change in changes.items():
        bad = copy.deepcopy(report); change(bad['native'])
        try: validate(bad, folder, build)
        except (RuntimeError,KeyError,TypeError,ValueError): rejected.append(name)
        else: raise RuntimeError('Preparation corruption accepted: '+name)
    return rejected


def run_controls(exe, label, game=None):
    from build_support import REPORTS, run, write_json
    folder = REPORTS/('preparation-demand-'+label); folder.mkdir(parents=True,exist_ok=True)
    output = folder/'controls.json'
    require(not output.exists(), 'Preparation controls already ran; no automatic retry')
    args = [exe,'--headless']
    if game is not None: args += ['--path',game]
    args += ['--','--preparation-demand-check','--preparation-demand-output='+str(output)]
    log = run(args,'preparation-demand-'+label,timeout=60)
    require('CAIRN_PREPARATION_DEMAND=' in log and 'SCRIPT ERROR:' not in log and 'ERROR:' not in log,
            'Preparation real-entry API control log failed')
    report = read(output); build = read(ROOT/'game/build_info.json')
    result = validate(report,folder,build); result['mutations_rejected'] = mutations(report,folder,build)
    write_json(folder/'validation.json',result)
    return result


def saved_controls(reports, build):
    results = {}
    for label in ('editor','release'):
        folder = Path(reports)/('preparation-demand-'+label)
        report = read(folder/'controls.json')
        result = validate(report,folder,build); result['mutations_rejected'] = mutations(report,folder,build)
        require(result == read(folder/'validation.json'), 'Saved preparation controls differ: '+label)
        results[label] = result
    return results


def verify_prefix(trials):
    expected = [('warmup',0)]+[('bare',i) for i in range(4)]
    require(1 <= len(trials) <= 5 and [(t['group'],t['index']) for t in trials] == expected[:len(trials)],
            'Preparation prefix repeated, padded, reordered or continued')
    for index,t in enumerate(trials):
        require(t['id'] == 'AB-H2-preparation-%s-%d'%(t['group'],t['index']) and
                t['diagnostic_mode'] == 'bare' and t['dose_enabled'] is False and
                t['dose']['requested_tick_cycles'] == t['dose']['reference_cycles'] == '0',
                'Preparation mode enabled positive/shipping work')
        if index < len(trials)-1: require(t['valid'] is True and t['complete'] is True, 'Continued after a failed preparation trial')
    require(len(trials) == 5 or trials[-1]['valid'] is False, 'Early preparation stop without failure')


def trial_ledger(folder,t):
    path=Path(folder)/(t['id']+'-observers.bin'); meta=t['observer']
    require(meta.get('schema') == 'cairn-observer-ledger-2' and meta.get('file') == path.name and
            meta.get('cap_bytes') == CAP, 'Preparation raw identity missing')
    if meta.get('failure_code') == 7:
        require(t['valid'] is False and meta.get('passed') is False and
                t['observer_sha256'] == (sha(path) if path.exists() else ''), 'Hidden preparation I/O failure')
        require(not path.exists() or path.stat().st_size <= CAP, 'Oversized failed preparation prefix')
        return dict(passed=False,failure_code=7,retained_bytes=path.stat().st_size if path.exists() else None,
                    reason='Raw attribution unavailable after I/O failure; no measured zero')
    require(sha(path) == t['observer_sha256'], 'Preparation raw hash differs')
    header,rows=decode(path.read_bytes())
    require(all(meta[k] == v for k,v in header.items()) and meta['trace_bytes'] == path.stat().st_size,
            'Preparation raw metadata differs')
    if header['failure_code']:
        require(t['valid'] is False and meta['passed'] is False and meta['closed'] is True, 'Hidden failed preparation prefix')
        return dict(passed=False,**header,reason='Retained failed prefix; owner demand unavailable')
    a,rows=trace(path,meta,t['preparation_owners'])
    disposal.disposal(t['observer_disposal'],'disposed')
    require(t['observer_disposal']['failure_code'] == 0 and
            t['observer_disposal']['storage_before']['record_count'] == len(rows), 'Preparation recorder release differs')
    cycles.sequence([meta['emit_end'],t['observer_disposal']['counter_start'],t['observer_disposal']['counter_end'],
                     t['cycle_boundaries'][-1]['before']])
    require(t['observer_disposal']['storage_before']['open_spans'] == 0 and
            meta['serialization_capacity_bytes'] >= 65536+SIZE and meta['serialization_capacity_bytes'] < 131072,
            'Preparation cleanup/serialization storage unavailable')
    groups={}
    for r in rows:
        section=str(r['start_section']) if r['start_section'] == r['end_section'] else 'cross_section'
        g=groups.setdefault((r['lane'],r['slot'],section),dict(lane=r['lane'],slot=r['slot'],section=section,
            calls=0,inclusive_full_cycles=0,exclusive_body_cycles=0,bookkeeping_cycles=0))
        g['calls']+=1
        for key,rkey in [('inclusive_full_cycles','full_cycles'),('exclusive_body_cycles','exclusive_body_cycles'),('bookkeeping_cycles','bookkeeping_cycles')]:
            g[key]+=r[rkey]
    for g in groups.values():
        for key in ('inclusive_full_cycles','exclusive_body_cycles','bookkeeping_cycles'): g[key]=str(g[key])
    return dict(passed=True,records=rows,lanes=a['ownership']['lanes'],groups=list(groups.values()),
                ownership=a['ownership'],**header)


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
                and all(r['units'] in (0,1) and r['bytes']==0 for r in main if r['slot']<=12), 'Observer handover units or reserved bytes differ')
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
            and len({w['worker']['lane'] for w in workers})==3
            and {w['worker']['lane'] for w in workers}.isdisjoint({o['lane'] for o in t['preparation_owners']['owners']})
            and a['lane_count']==1+len(t['preparation_owners']['owners'])+3, 'Observer writer phases/lanes missing, repeated or escaped')
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
                native_owners=a['ownership'],scope='Perturbing preparation attribution only; no thread/process addition, fitted subtraction or shipping-cost estimate.')


def reconcile(folder,build,inventory_path):
    folder=Path(folder);p=read(folder/'preparation-demand-attribution.json');s=read(folder/'summary.json')
    require(p['version']==VERSION and p['policy']==cycles.POLICY and p['build']==s['build']==build
            and p['inventory']==read(inventory_path) and p['inventory']['version']==INVENTORY
            and p['inventory_sha256']==sha(inventory_path) and p['max_trials']==5
            and p['qualified'] is False and p['target_performance']=='not_run' and p['measurement_valid'] is False
            and s['qualified'] is False and s['benchmark_mode']=='preparation-demand-attribution', 'Observer batch identity/qualification changed')
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
