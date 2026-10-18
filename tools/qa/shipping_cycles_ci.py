"""One declared release sequence. Audits and saved mutations never run a game."""
import argparse
import contextlib
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/ci'))
from build_support import write_json, run as invoke, extract
from mesh_admission_candidate_audit import pack
from shipping_pilot_ci import candidate_identity as legacy_candidate_identity
from shipping_cycles import (POLICY, VERSION, require, read, sha, verify_metadata, saved_controls,
                             validate_method_controls, reconcile, expected_protocol, work_record)

REPORTS = ROOT/'reports/shipping-cycles-pilot'
INVENTORY_PATH = ROOT/'game/diagnostics/shipping_cycles_inventory.json'


def run_controls(executable, label, game=None):
    name = 'shipping-cycles-controls-'+label
    path = ROOT/'reports'/(name+'.json')
    require(not path.exists(), 'V2 API checks already have evidence; no automatic retry')
    args = [executable, '--headless']
    if game is not None: args += ['--path', game]
    output = invoke(args+['--', '--shipping-cycles-check', '--shipping-cycles-output='+str(path)], name, timeout=60)
    markers = [line.split('CAIRN_SHIPPING_CYCLES_CONTROLS=',1)[1] for line in output.splitlines()
               if 'CAIRN_SHIPPING_CYCLES_CONTROLS=' in line]
    require(len(markers) == 1 and 'SCRIPT ERROR:' not in output and 'ERROR:' not in output,
            'V2 control runner failed or missing')
    require(json.loads(markers[0]) == dict(passed=True, output=str(path)), 'V2 control console/saved result differs')
    build = read(ROOT/'game/build_info.json')
    result = validate_method_controls(read(path), build)
    write_json(ROOT/'reports'/(name+'-validation.json'), result)
    return result


def candidate_identity():
    result = legacy_candidate_identity()
    with zipfile.ZipFile(ROOT/'build/published-player/Cairn-windows-x86_64.zip') as zipped:
        verify_metadata(result['build'], pack(zipped.read('Cairn.pck')), ROOT)
    result.update(policy=POLICY, method=VERSION, cycles_inventory_sha256=sha(INVENTORY_PATH))
    return result


def saved_faults(folder, build):
    labels = ('numeric-counter', 'reversed-boundary', 'missing-shared-section', 'unmeasured-marker-zero',
              'missing-native-witness', 'changed-native-digest', 'changed-native-update-count',
              'missing-final-physics', 'missing-final-callback', 'missing-edit-ack', 'ignored-operation-failure',
              'continued-after-stop', 'forged-control', 'false-qualification')
    rejected = []
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='cairn-cycles-fault-') as td:
            target = Path(td)/'raw'
            shutil.copytree(folder, target)
            pilot = read(target/'shipping-cycles.json')
            t = pilot['trials'][0]
            if label == 'numeric-counter':
                t['cycle_boundaries'][0]['before']['reads'][0]['cycles'] = 9007199254740993
            elif label == 'reversed-boundary': t['cycle_boundaries'][0]['bounds'][0] = str(2**64-1)
            elif label == 'missing-shared-section': t['cycle_boundaries'].pop(2)
            elif label == 'unmeasured-marker-zero': t['cycle']['marker'] = ['0','0']
            elif label in ('missing-native-witness','changed-native-digest','changed-native-update-count'):
                # Every arm has the common native witness, including a bare
                # sequence that stopped before either positive. A forged bare
                # digest/update is undeclared work and must be rejected too.
                path = target/(t['id']+'-cycles.jsonl')
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                if label == 'missing-native-witness': rows.pop()
                elif label == 'changed-native-digest': rows[0]['digest'] = '0'*64
                else: rows[0]['updates'] += 1
                path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                t['dose_sha256'] = sha(path)
            elif label in ('missing-final-physics','missing-final-callback','missing-edit-ack'):
                suffix = {'missing-final-physics':'-poses.csv','missing-final-callback':'-frames.csv',
                          'missing-edit-ack':'-frames.csv.edits.jsonl'}[label]
                path = target/(t['id']+suffix)
                lines = path.read_text(encoding='utf-8-sig').splitlines()
                path.write_text('\n'.join(lines[:-1])+'\n')
            elif label == 'ignored-operation-failure':
                t['phases'][0]['data_apply']['max_usec'] = 751
                t['checks']['operations'] = True
                t['valid'] = True
            elif label == 'continued-after-stop': pilot['trials'].append(copy.deepcopy(t))
            elif label == 'forged-control': pilot['assessment']['controls']['valid'] = True
            elif label == 'false-qualification': pilot['qualified'] = True
            # Re-sign matching redundant snapshots where possible. Semantic
            # validation still rejects lost work, invented zero or altered SHA.
            cp = target/(t['id']+'-complete.json')
            if cp.exists():
                body = read(cp)
                for key in list(body):
                    if key in t: body[key] = t[key]
                write_json(cp, body)
                bp = target/(t['id']+'-boundary.json')
                terminal = read(bp)
                for key in list(terminal):
                    if key in t and key != 'cycle': terminal[key] = t[key]
                terminal['complete_sha256'] = sha(cp)
                write_json(bp, terminal)
            write_json(target/'shipping-cycles.json', pilot)
            try:
                reconcile(target, build, INVENTORY_PATH)
            except (RuntimeError, KeyError, ValueError, TypeError, IndexError):
                rejected.append(label)
            else:
                raise RuntimeError('Saved v2 fault accepted: '+label)
    return dict(passed=True, count=len(rejected), rejected=rejected)


def audit():
    identity = candidate_identity()
    require(identity == read(REPORTS/'candidate-identity.json'), 'V2 pilot candidate changed')
    build = identity['build']
    controls_path = ROOT/'build/downloaded-export-evidence/reports'
    controls = saved_controls(controls_path, build)
    files = list((REPORTS/'raw').glob('*/shipping-cycles.json'))
    require(len(files) == 1, 'Missing or repeated v2 pilot sequence')
    result = reconcile(files[0].parent, build, INVENTORY_PATH)
    reservation = read(REPORTS/'sequence-declared.json')
    require(reservation == declaration(build), 'Prospective finite declaration changed')
    faults = saved_faults(files[0].parent, build) if all(t['complete'] for t in read(files[0])['trials']) else dict(passed=True, count=0, rejected=[], reason='partial sequence retained; complete-trial mutations unavailable')
    value = dict(passed=True, qualified=False, target_performance='not_run', candidate=identity,
                 controls=controls, sequence=result, saved_faults=faults, engine_runs=1, maximum_trials=13)
    write_json(REPORTS/'independent-audit.json', value)
    return value


def declaration(build):
    return dict(policy=POLICY, method=VERSION, build=build, render_block=32, workers=1,
                physics_ticks=4320, ordered_maximum=[list(v) for v in expected_protocol()], maximum_trials=13,
                hash_update_cap=512, tick_wall_cap_usec=50000, automatic_retry=False,
                rule='Stop at first failed guard or unresolved null/positive control. No padding, profile matrix or target action.')


def run():
    require(not REPORTS.exists(), 'V2 sequence already declared; no automatic retry')
    REPORTS.mkdir(parents=True)
    identity = candidate_identity()
    write_json(REPORTS/'candidate-identity.json', identity)
    write_json(REPORTS/'sequence-declared.json', declaration(identity['build']))
    # Both API/method controls must already have passed before the only route
    # launch. This launcher never imports an editor or runs companion routes.
    saved_controls(ROOT/'build/downloaded-export-evidence/reports', identity['build'])
    destination = ROOT/'build/shipping-cycles-player'
    extract(ROOT/'build/published-player/Cairn-windows-x86_64.zip', destination)
    executable = destination/'Cairn.exe'
    command = [str(executable), '--headless', '--', '--shipping-cycles-pilot', '--m1-report-root='+str(REPORTS/'raw')]
    with (REPORTS/'release-sequence.log').open('w', encoding='utf-8') as log:
        finished = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=1500)
    output = (REPORTS/'release-sequence.log').read_text(encoding='utf-8', errors='replace')
    markers = [line.split('CAIRN_SHIPPING_CYCLES=',1)[1] for line in output.splitlines() if 'CAIRN_SHIPPING_CYCLES=' in line]
    require(len(markers) == 1 and 'SCRIPT ERROR:' not in output and 'ERROR:' not in output, 'V2 engine error or missing result; keep partial evidence')
    marker = json.loads(markers[0])
    require(type(marker['expected_exit']) is int and marker['expected_exit'] in (0,1)
            and finished.returncode == marker['expected_exit'], 'Unexpected v2 process exit')
    folder = Path(marker['report_dir']).resolve()
    require(folder.is_relative_to((REPORTS/'raw').resolve()), 'V2 reports escaped declared destination')
    p = read(folder/'shipping-cycles.json')
    require(marker['measurement_valid'] is p['measurement_valid'] and marker['qualified'] is False
            and marker['outcome'] == p['assessment']['outcome'] and marker['trials'] == len(p['trials'])
            and marker['abort_reason'] == p['abort_reason'], 'V2 console/saved outcome differs')
    write_json(REPORTS/'runtime-result.json', marker)
    result = audit()
    print(json.dumps(dict(evidence_integrity=result['sequence']['evidence_integrity'],
                         measurement_valid=result['sequence']['measurement_valid'],
                         cycle_cost=result['sequence']['cycle_cost'], trials=result['sequence']['trials'],
                         abort_reason=result['sequence']['abort_reason'], qualified=False)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    audit() if args.audit_only else run()
