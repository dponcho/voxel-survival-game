"""Independent post-boundary publication checks and real controller controls."""
import copy
import json
from pathlib import Path
import re

from shipping_cycles import require, read, sha, uint

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'cairn-preparation-sequence-prefix-1'
CONTROL = 'cairn-preparation-prefix-controls-1'
ABORT = 'Sequence-prefix publication failed'


def natural(value):
    require(type(value) is int and value >= 0, 'Prefix count/time/size is not a nonnegative integer')
    return value


def file_state(state, folder, verify_file):
    require(state['name'] == 'sequence-prefix.json' and state['status'] in ('missing','unavailable','retained'),
            'Prefix file identity/status differs')
    path = Path(folder)/'sequence-prefix.json'
    if state['status'] != 'retained':
        require(state['bytes'] is None and state['sha256'] is None, 'Missing prefix invented bytes/hash')
        if verify_file and state['status'] == 'missing':
            require(not path.is_file(), 'Missing prefix contradicts retained file')
        return
    natural(state['bytes'])
    require(type(state['sha256']) is str and re.fullmatch('[0-9a-f]{64}', state['sha256']),
            'Invalid prefix file hash')
    if verify_file:
        require(path.is_file() and path.stat().st_size == state['bytes'] and sha(path) == state['sha256'],
                'Retained prefix file changed or disappeared')


def publications(folder, batch):
    trials, events = batch['trials'], batch['prefix_publications']
    complete = [t for t in trials if t['complete']]
    require(type(events) is list and len(events) == len(complete) <= 5 and
            trials[:len(complete)] == complete, 'Missing, extra or out-of-order prefix publication')
    failed = False
    for index, (event, trial) in enumerate(zip(events, complete)):
        require(event['schema'] == SCHEMA and natural(event['trial_count']) == index+1 and
                event['id'] == trial['id'] and type(event['passed']) is bool and
                type(event['write_succeeded']) is bool, 'Prefix attempt detached from completed trial')
        require(event['write_succeeded'] is (natural(event['write_error']) == 0),
                'Prefix raw write error was hidden or invented')
        begin, end = natural(event['start_usec']), natural(event['end_usec'])
        require(natural(trial['start_usec']) <= natural(trial['end_usec']) <=
                natural(trial['marker_end_usec']) <= begin <= end, 'Prefix write escaped its post-boundary scope')
        if 'marker_cycles' in trial:
            require(uint(trial['marker_cycles']['end']['reads'][3]['wall_after_usec']) <= begin,
                    'Prefix write overlaps the terminal counter observation')
        if index:
            require(events[index-1]['end_usec'] <= trial['start_usec'], 'Next trial started before prefix publication ended')
        file_state(event['file'], folder, index == len(events)-1)
        require(event['passed'] is (event['write_succeeded'] and event['file']['status'] == 'retained'),
                'Prefix success hid a failed write or unavailable output')
        if not event['passed']:
            failed = True
            require(index == len(events)-1 and len(trials) == index+1,
                    'Continued after prefix publication failure')
            expected = ABORT if trial['valid'] else 'Attribution trial guard failed: '+trial['id']
            require(batch['abort_reason'] == expected, 'Prefix failure lost its first stop reason')
    require(type(batch['batch_publication_valid']) is bool and
            batch['batch_publication_valid'] is (not failed), 'Batch publication verdict differs')
    if not events:
        require(not (Path(folder)/'sequence-prefix.json').is_file(), 'Prefix exists without a publication attempt')
    elif events[-1]['passed']:
        # Earlier overwrites are not claimed as separately retained files. The
        # last successful snapshot must contain the exact completed prefix.
        saved = read(Path(folder)/'sequence-prefix.json')
        require(saved == dict(schema=SCHEMA, trials=complete, no_retry=True),
                'Published prefix changed completed trials or retry policy')
    return dict(passed=not failed, attempts=len(events),
                status='retained_publication_failure' if failed else ('verified' if events else 'not_attempted'),
                last_file=events[-1]['file'] if events else None,
                complete_trial_flags_preserved=True)


def validate_controls(report, folder, build):
    folder = Path(folder)
    require(report['schema'] == CONTROL and report['build'] == build and report['passed'] is True and
            report['qualified'] is False and report['target_performance'] == 'not_run' and
            report['synthetic_completions'] is True and report['route_executed'] is False and
            report['fixture_limit_usec'] == 5000000 and natural(report['fixture_usec']) <= 5000000,
            'Prefix controller fixture identity/scope/cap differs')
    before = report['before']
    require(before['index'] == 0 and before['valid_trial'] is True and before['fail_prefix'] is True and
            before['fixture_io_ok'] is True and before['immutable_preserved'] is True and
            before['setup_calls'] == 1 and before['finish_calls'] == 0 and before['abort_reason'] == '' and
            before['injected_open_error'] > 0 and before['observer_active'] is False and
            len(before['trials']) == 1 and before['trials'][0]['valid'] is True,
            'Rejected prefix continuation was not reproduced')
    for key in ('generated','meshed','generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes'):
        require(before['native_before'][key] == before['native_after'][key], 'Rejected fixture created terrain work')
    require(len(before['immutable_files']) == 2 and
            all(Path(n).name == n and '\\' not in n and
                sha(folder/'before'/n) == value and read(folder/'before'/n) == before['trials'][0]
                for n,value in before['immutable_files'].items()), 'Rejected fixture rewrote immutable files')
    expected = [(0,True,False),(0,True,True),(2,True,True),(4,True,True),
                (0,False,False),(4,True,False),(0,False,True)]
    require(len(report['cases']) == len(expected), 'Missing prefix controller cases')
    results = []
    for index,(case,parameters) in enumerate(zip(report['cases'],expected)):
        position, valid, failure = parameters
        require((case['index'],case['valid_trial'],case['fail_prefix']) == parameters and
                case['fixture_io_ok'] is True and case['immutable_preserved'] is True and
                len(case['trials']) == position+1 and len(case['prefix_publications']) == position+1,
                'Prefix fixture setup or population differs')
        location = folder/('case-'+str(index))
        result = publications(location,case)
        stopped = failure or not valid or position == 4
        require(case['setup_calls'] == int(not stopped) and case['finish_calls'] == int(stopped) and
                case['observer_active'] is False and
                case['stopped_entry_checked'] is (failure or not valid) and
                case['final_outcome'] == ('failed' if failure else ('completed' if stopped else '')),
                'Controller started setup after stopping or forged its outcome')
        require((type(case['injected_open_error']) is int and case['injected_open_error'] > 0) if failure
                else case['injected_open_error'] == 0, 'Missing real failed FileAccess open')
        if failure:
            require(case['prefix_publications'][-1]['write_error'] == case['injected_open_error'],
                    'Controller raw open error detached from actual publication')
        require(case['batch_publication_valid'] is (not failure) and
                case['trials'][-1]['valid'] is valid and all(t['checks']['io'] and not t['io_failed'] for t in case['trials']),
                'Late batch failure rewrote an immutable trial observation')
        for key in ('generated','meshed','generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes'):
            require(case['native_before'][key] == case['native_after'][key], 'Controller created native terrain work')
        require(len(case['immutable_files']) == 2*len(case['trials']), 'Missing immutable fixture snapshots')
        for name, expected_hash in case['immutable_files'].items():
            require(Path(name).name == name and '\\' not in name and sha(location/name) == expected_hash,
                    'Completed fixture file was rewritten or escaped')
            trial = next(t for t in case['trials'] if name.startswith(t['id']+'-'))
            require(read(location/name) == trial, 'Immutable fixture snapshot differs from original trial')
        results.append(dict(index=position, trial_valid=valid, prefix_failed=failure,
            setup_calls=case['setup_calls'], finish_calls=case['finish_calls'],
            immutable_files=len(case['immutable_files']), publication=result))
    return dict(passed=True, qualified=False, engine_executed=False, fixture_usec=report['fixture_usec'],
                rejected_tail_setup_calls=1, cases=results)


def mutations(report, folder, build):
    changes = {
        'lost-before-failure': lambda r: r['before'].__setitem__('setup_calls',0),
        'continued-setup': lambda r: r['cases'][1].__setitem__('setup_calls',1),
        'missing-finish': lambda r: r['cases'][1].__setitem__('finish_calls',0),
        'rewritten-trial-io': lambda r: r['cases'][1]['trials'][0].__setitem__('io_failed',True),
        'hidden-batch-failure': lambda r: r['cases'][1].__setitem__('batch_publication_valid',True),
        'hidden-write-error': lambda r: r['cases'][1]['prefix_publications'][0].__setitem__('write_error',0),
        'invented-missing-zero': lambda r: r['cases'][1]['prefix_publications'][0]['file'].__setitem__('bytes',0),
        'lost-raw-open-error': lambda r: r['cases'][1].__setitem__('injected_open_error',0),
        'late-start-before-publication': lambda r: r['cases'][2]['trials'][1].__setitem__('start_usec',0),
        'lost-last-trial-failure': lambda r: r['cases'][3].__setitem__('final_outcome','completed'),
        'over-cap': lambda r: r.__setitem__('fixture_usec',5000001),
        'real-route-invention': lambda r: r.__setitem__('synthetic_completions',False),
    }
    rejected = []
    for name,change in changes.items():
        bad = copy.deepcopy(report); change(bad)
        try: validate_controls(bad,folder,build)
        except (RuntimeError,KeyError,ValueError,TypeError,StopIteration): rejected.append(name)
        else: raise RuntimeError('Prefix controller corruption accepted: '+name)
    return rejected


def run_controls(exe, label, game=None):
    from build_support import REPORTS, run, write_json
    folder = REPORTS/('preparation-prefix-'+label)
    folder.mkdir(parents=True,exist_ok=True)
    output = folder/'controls.json'
    require(not output.exists(), 'Prefix controller already ran; no automatic retry')
    args = [exe,'--headless']+(['--path',game] if game is not None else [])
    log = run(args+['--','--preparation-prefix-check','--preparation-prefix-output='+str(output)],
              'preparation-prefix-'+label,timeout=60)
    require('ERROR:' not in log and 'CAIRN_PREPARATION_PREFIX=' in log, 'Prefix controller log failed')
    report = read(output)
    result = validate_controls(report,folder,read(ROOT/'game/build_info.json'))
    result['mutations_rejected'] = mutations(report,folder,report['build'])
    write_json(folder/'validation.json',result)
    return result


def saved_controls(reports, build):
    results = {}
    for label in ('editor','release'):
        folder = Path(reports)/('preparation-prefix-'+label)
        report = read(folder/'controls.json')
        result = validate_controls(report,folder,build)
        result['mutations_rejected'] = mutations(report,folder,build)
        require(result == read(folder/'validation.json'), 'Saved prefix controller result differs')
        results[label] = result
    return results
