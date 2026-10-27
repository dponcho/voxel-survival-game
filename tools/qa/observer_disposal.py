"""Independent explicit-disposal capability checks. No route or engine in readers."""
import copy
import json
from pathlib import Path

import shipping_cycles as cycles
import shipping_observer as observer

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'cairn-observer-disposal-controls-1'
DISPOSAL = 'cairn-observer-disposal-1'
SOURCES = ('m1_observer_disposal_tests.gd', 'title.gd')
NATIVE = ('core/observer_disposal.h', 'core/observer_ledger.h', 'godot/observer_disposal.cpp',
          'godot/observer_probe.cpp', 'godot/benchmark_probe.h', 'godot/benchmark_probe.cpp',
          'godot/report_sink.cpp', 'godot/report_sink.h')
require, read, sha = cycles.require, cycles.read, cycles.sha


def source_metadata(root):
    root = Path(root)
    return dict(schema=DISPOSAL,
                sources_sha256={n: sha(root/'game/scripts'/n) for n in SOURCES},
                native_sha256={n: sha(root/'native/sandbox_world'/n) for n in NATIVE})


def verify_metadata(build, contents, root):
    require(build['observer_disposal'] == source_metadata(root), 'Disposal source/native identity differs')
    for name in SOURCES:
        stem = 'scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC')
                and ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'],
                'Missing tokenized disposal source: '+name)


def disposal(value, status):
    require(value['schema'] == DISPOSAL and value['status'] == status and value['qualified'] is False
            and value['disposed'] is (status == 'disposed'), 'Disposal status/destruction witness differs')
    if status == 'wrong_thread':
        require(all(value[k] is None for k in ('storage_before', 'storage_after', 'failure_code',
                'strong_owners', 'counter_start', 'counter_end')), 'Foreign-thread refusal invented observations')
        return
    cycles.sequence([value['counter_start'], value['counter_end']])
    if status == 'absent':
        require(all(value[k] is None for k in ('storage_before', 'storage_after', 'failure_code', 'strong_owners')),
                'Absent recorder invented storage/failure/owner zero')
        return
    storage = value['storage_before']
    require(set(storage) == {'record_count', 'lane_count', 'open_spans', 'record_capacity_bytes',
                            'lane_capacity_bytes', 'object_bytes'}, 'Missing disposal storage witness')
    require(all(type(v) is int and v >= 0 for v in storage.values())
            and 1 <= storage['lane_count'] <= 8 and storage['open_spans'] <= 64
            and 0 < storage['object_bytes'] < 65536 and storage['lane_capacity_bytes'] == 512
            and storage['record_count']*observer.SIZE <= storage['record_capacity_bytes'] <= observer.CAP,
            'Invalid requested object/vector capacities')
    require(type(value['failure_code']) is int and 0 <= value['failure_code'] <= 7
            and type(value['strong_owners']) is int and value['strong_owners'] > 0, 'Missing honest pre-disposal state')
    if status == 'disposed':
        require(value['strong_owners'] == 1 and storage['open_spans'] == 0
                and type(value['storage_after']) is int and value['storage_after'] == 0,
                'Disposed while retained/open or failed to release storage')
    else:
        require(value['storage_after'] is None, 'Refused disposal invented freed storage')
        if status == 'retained_owner': require(value['strong_owners'] > 1, 'Missing retained owner')
        if status == 'open_spans': require(storage['open_spans'] > 0, 'Missing open scope')
        if status == 'active': require(storage['open_spans'] == 0, 'Active refusal hid an open scope')


def failed_prefix(path, metadata, code):
    """One-record fault fixture, including a deliberately smaller saturation cap.

    This reader does not relax the old shipping codec's fixed 32 MiB contract.
    """
    data = Path(path).read_bytes()
    require(len(data) == observer.HEADER.size+observer.SIZE, 'Failed prefix lost or padded')
    magic, version, size, cap, count, failure, lanes = observer.HEADER.unpack_from(data)
    expected_cap = len(data) if code == 1 else observer.CAP
    require((magic, version, size, cap, count, failure, lanes)
            == (b'CAIRNOB1', 1, 192, expected_cap, 1, code, 1), 'Failed prefix header differs')
    require(metadata['schema'] == 'cairn-observer-ledger-1' and metadata['passed'] is False
            and metadata['closed'] is True and metadata['file'] == Path(path).name
            and all(type(metadata[k]) is int and metadata[k] == v for k, v in
                    dict(trace_bytes=len(data), cap_bytes=cap, record_count=1, failure_code=code, lane_count=1).items()),
            'Failed prefix metadata differs')
    record = observer.RECORD.unpack_from(data, observer.HEADER.size)
    require(record[:2] == (1, 0) and record[2] > 0
            and record[3:] == (2, 1, 0, 0, 0, 1, 1, 0), 'Failed fixture owner/population differs')
    previous_wall = previous_cycle = 0
    for i in range(4):
        cycle, before, after, flags, error = observer.STAMP.unpack_from(
            data, observer.HEADER.size+observer.RECORD.size+i*observer.STAMP.size)
        require(previous_wall <= before <= after, 'Failed prefix wall reversal')
        previous_wall = after
        if code == 4:
            require((cycle, flags, error) == (0, 1, 6), 'Failed counter was replaced by a measured zero')
        else:
            require(flags == 3 and error == 0 and previous_cycle <= cycle, 'Cap fixture counter failure/reversal')
            previous_cycle = cycle
    return dict(bytes=len(data), sha256=sha(path), failure_code=code)


def validate(report, folder, build):
    folder = Path(folder)
    require(report['schema'] == SCHEMA and report['build'] == build and report['passed'] is True
            and report['qualified'] is False and report['target_performance'] == 'not_run', 'Disposal control identity/result differs')
    n = report['native']
    require(n['started'] is True and n['passed'] is True and n['qualified'] is False, 'Native disposal control failed')
    start, end = cycles.uint(n['fixture_start_usec']), cycles.uint(n['fixture_end_usec'])
    require(cycles.uint(n['fixture_limit_usec']) == 5000000 and 0 <= end-start <= 5000000, 'Disposal fixture escaped finite wall cap')
    expected = [('absent', 'absent'), ('active', 'active'), ('open', 'open_spans'), ('live', 'retained_owner'),
                ('attached', 'retained_owner'), ('foreign', 'retained_owner'), ('release', 'disposed'), ('repeat', 'absent')]
    for name, status in expected: disposal(n[name], status)
    disposal(n['wrong_thread'], 'wrong_thread')
    meta = n['ledger']
    path = folder/meta['file']
    raw = observer.ledger(path, meta)
    require(raw['record_count'] == 6 and raw['lane_count'] == 2 and type(n['readback_bytes']) is int
            and n['readback_bytes'] == path.stat().st_size and type(n['post_begin']) is int
            and n['post_begin'] == 0 and n['post_finish']['passed'] is False and n['post_finish']['closed'] is False,
            'Lost post-destruction trace or accepted post-disposal recording')
    require((folder/(meta['file']+'.csv')).read_bytes() == b'disposal control\n'
            and (folder/(meta['file']+'.csv.proxy.tmp')).read_bytes() == b'proxy\n', 'Real disposal worker payload differs')
    w = n['worker']
    jobs = [r for r in raw['records'] if r['slot'] in (9, 10)]
    require(w['joined'] is True and w['failed'] is False
            and all(type(w[k]) is int for k in ('lane', 'completed', 'qualification_count', 'proxy_count',
                                                'qualification_bytes', 'proxy_bytes'))
            and n['live_worker']['joined'] is False and n['live']['strong_owners'] >= 3
            and n['attached']['strong_owners'] == n['foreign']['strong_owners'] == 2
            and w == dict(lane=2, joined=True, failed=False, completed=2, qualification_count=1,
                          proxy_count=1, qualification_bytes=17, proxy_bytes=6)
            and {r['slot']: r['bytes'] for r in jobs} == {9: 17, 10: 6}, 'Live/joined/retained worker evidence differs')
    for name in ('attached', 'foreign', 'release'):
        require(n[name]['storage_before']['record_count'] == 6
                and n[name]['storage_before']['lane_count'] == 2 and n[name]['failure_code'] == 0,
                'Disposal lost immutable recorder metadata')
    require(n['attached']['storage_before'] == n['foreign']['storage_before'] == n['release']['storage_before'],
            'Refused disposal changed the sealed recorder')
    observations = [n['process_start']]
    for name in ('absent', 'active', 'open', 'live'):
        observations += [n[name]['counter_start'], n[name]['counter_end']]
    observations += [meta['emit_start'], meta['emit_end']]
    for name in ('attached', 'foreign', 'release', 'repeat'):
        observations += [n[name]['counter_start'], n[name]['counter_end']]
    require([f['name'] for f in n['faults']] == ['counter', 'cap', 'write'], 'Missing/reordered disposal failure controls')
    faults = []
    for f, code in zip(n['faults'], (4, 1, 7)):
        m, release = f['ledger'], f['release']
        disposal(release, 'disposed')
        require(m['passed'] is False and m['failure_code'] == release['failure_code'] == code
                and release['storage_before']['record_count'] == 1, 'Disposal erased failed state/prefix')
        if code == 7:
            require(m['closed'] is False and m['trace_bytes'] == 0 and not (folder/m['file']).exists(),
                    'Write failure fabricated a readable/closed trace')
            prefix = dict(bytes=None, sha256=None, failure_code=code, trace='unavailable')
        else: prefix = failed_prefix(folder/m['file'], m, code)
        faults.append(dict(name=f['name'], **prefix))
        observations += [m['emit_start'], m['emit_end'], release['counter_start'], release['counter_end']]
    observations += [n['process_end']]
    cycles.sequence(observations)
    require(start <= cycles.uint(observations[0]['reads'][0]['wall_before_usec'])
            and cycles.uint(observations[-1]['reads'][3]['wall_after_usec']) <= end, 'Fixture counter lifecycle escaped wall enclosure')
    worker = next(r for r in raw['records'] if r['slot'] == 8)
    require(cycles.uint(n['process_start']['reads'][3]['wall_after_usec']) <= worker['reads'][0]['wall_before_usec']
            <= worker['reads'][3]['wall_after_usec'] <= cycles.uint(n['process_end']['reads'][0]['wall_before_usec'])
            and cycles.demand(n['process_start'], n['process_end'], 'process')[1] >= worker['full_cycles'],
            'Complete process bounds lost joined worker demand')
    return dict(passed=True, qualified=False, target_performance='not_run', schema=SCHEMA,
                fixture_usec=end-start, records=6, lanes=2, worker_joined=True,
                recorder_destroyed=True, storage_before=n['release']['storage_before'],
                retained_trace_sha256=sha(path), failure_prefixes=faults,
                complete_process_cycles=list(map(str, cycles.demand(n['process_start'], n['process_end'], 'process'))),
                disposal_thread_cycles=list(map(str, cycles.demand(n['release']['counter_start'], n['release']['counter_end'], 'thread'))))


def mutations(report, folder, build):
    changes = {
        'false-destruction': lambda r: r['native']['release'].__setitem__('disposed', False),
        'retained-at-release': lambda r: r['native']['release'].__setitem__('strong_owners', 2),
        'open-at-release': lambda r: r['native']['release']['storage_before'].__setitem__('open_spans', 1),
        'invented-freed-storage': lambda r: r['native']['attached'].__setitem__('storage_after', 0),
        'absent-zero': lambda r: r['native']['absent'].__setitem__('failure_code', 0),
        'thread-refusal-zero': lambda r: r['native']['wrong_thread'].__setitem__('counter_start', 0),
        'counter-failure': lambda r: r['native']['release']['counter_end']['reads'][1].__setitem__('success', False),
        'rounded-counter': lambda r: r['native']['release']['counter_end']['reads'][1].__setitem__('cycles', 9007199254740993),
        'worker-not-joined': lambda r: r['native']['worker'].__setitem__('joined', False),
        'no-live-owner': lambda r: r['native']['live'].__setitem__('strong_owners', 1),
        'lost-prefix': lambda r: r['native']['faults'][0]['ledger'].__setitem__('record_count', 0),
        'hidden-io-failure': lambda r: r['native']['faults'][2]['ledger'].__setitem__('passed', True),
        'post-disposal-write': lambda r: r['native'].__setitem__('post_begin', 1),
        'fixture-over-cap': lambda r: r['native'].__setitem__('fixture_end_usec', str(int(r['native']['fixture_start_usec'])+5000001)),
        'qualified-capability': lambda r: r.__setitem__('qualified', True),
    }
    rejected = []
    for name, change in changes.items():
        value = copy.deepcopy(report); change(value)
        try: validate(value, folder, build)
        except (RuntimeError, KeyError, TypeError, ValueError): rejected.append(name)
        else: raise RuntimeError('Disposal corruption accepted: '+name)
    return rejected


def run_controls(executable, label, game=None):
    from build_support import run, write_json
    name = 'observer-disposal-controls-'+label
    path = ROOT/'reports'/(name+'.json')
    require(not path.exists(), 'Disposal control already has evidence; no retry')
    args = [executable, '--headless']+(['--path', game] if game is not None else [])
    output = run(args+['--', '--observer-disposal-check', '--observer-disposal-output='+str(path)], name, timeout=60)
    markers = [line.split('CAIRN_OBSERVER_DISPOSAL=', 1)[1] for line in output.splitlines() if 'CAIRN_OBSERVER_DISPOSAL=' in line]
    require(len(markers) == 1 and 'SCRIPT ERROR:' not in output and 'ERROR:' not in output
            and json.loads(markers[0]) == dict(passed=True, output=str(path)), 'Disposal runner failed')
    report, build = read(path), read(ROOT/'game/build_info.json')
    result = validate(report, path.parent, build)
    result['saved_faults_rejected'] = mutations(report, path.parent, build)
    write_json(path.with_name(name+'-validation.json'), result)
    return result


def saved_controls(folder, build):
    folder = Path(folder); results = {}
    for label in ('editor', 'release'):
        name = 'observer-disposal-controls-'+label
        report = read(folder/(name+'.json'))
        result = validate(report, folder, build)
        result['saved_faults_rejected'] = mutations(report, folder, build)
        require(result == read(folder/(name+'-validation.json')), 'Saved disposal audit differs')
        results[label] = result
    return results
