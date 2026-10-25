"""Replay saved owner controls and bind the no-launch decision to exact source.

Never starts an engine, changes a runtime/inventory, or enables a pilot. The
stop-rule finding is source inspection, not an executed Godot fault fixture.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/ci'))
import pipeline
import preparation_demand as owners
from mesh_admission_candidate_audit import pack, imports

VERSION = 'm1-preparation-owner-launch-review-1'
EVIDENCE = ROOT/'docs/evidence/m1-preparation-owner-cloud-2026-10-25.json'
RUNTIME = 'game/scripts/m1_preparation_demand_runtime.gd'
BASE = 'game/scripts/benchmark.gd'
require = owners.require


def digest(data):
    return hashlib.sha256(data).hexdigest()


def embedded(item):
    count = item['bytes']
    require(type(count) is int and 0 <= count <= owners.CAP, 'Invalid embedded byte bound')
    raw = base64.b64decode(item['base64_zlib'], validate=True)
    decoder = zlib.decompressobj()
    data = decoder.decompress(raw, count+1)
    require(len(data) == count and decoder.eof and not decoder.unconsumed_tail and
            not decoder.unused_data and digest(data) == item['sha256'],
            'Embedded saved file changed, truncated or exceeded its bound')
    return data


def replay(group, build):
    manifest = {}
    with tempfile.TemporaryDirectory(prefix='cairn-owner-review-') as td:
        root = Path(td)
        for name, item in group['files'].items():
            parts = name.split('/')
            require(len(parts) == 2 and parts[0] in ('editor','release') and
                    parts[1] not in ('','.','..') and '\\' not in parts[1] and ':' not in parts[1],
                    'Saved control path escaped its declared binary')
            data = embedded(item)
            folder = root/('preparation-demand-'+parts[0])
            folder.mkdir(exist_ok=True)
            (folder/parts[1]).write_bytes(data)
            manifest[name] = dict(bytes=len(data), sha256=digest(data))
        actual = owners.saved_controls(root, build)
        require(actual == group['controls'], 'Saved owner verdicts or corruption results differ')
        for label in ('editor','release'):
            log = (root/('preparation-demand-'+label)/'process.log').read_text(encoding='utf-8-sig')
            require('CAIRN_PREPARATION_DEMAND=' in log and 'ERROR:' not in log,
                    'Real-entry control log contains an error or lacks its result')
    return dict(files=manifest, file_count=len(manifest),
                bytes=sum(v['bytes'] for v in manifest.values()), controls=actual,
                semantic_corruptions_rejected=sum(len(v['mutations_rejected']) for v in actual.values()))


def candidate(archive, proof, root=ROOT):
    raw = Path(archive).read_bytes()
    expected = proof['candidate']
    require(len(raw) == expected['portable_bytes'] and digest(raw) == expected['portable_sha256'],
            'Review candidate ZIP differs from the verified candidate')
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        require(len(names) == len(set(names)) and zipped.testzip() is None and
                all(n and not n.startswith('/') and '\\' not in n and ':' not in n and
                    '..' not in n.split('/') for n in names), 'Candidate ZIP paths/CRC differ')
        build = json.loads(zipped.read('BUILD_INFO.json'))
        exe, pck = zipped.read('Cairn.exe'), zipped.read('Cairn.pck')
    contents = pack(pck)
    require(build == expected['build'] == json.loads(contents['build_info.json']) and
            digest(exe) == expected['exe_sha256'] == build['engine_binaries']['template_release.exe'] and
            digest(pck) == expected['pck_sha256'] and len(contents) == expected['pck_entries_md5_verified'],
            'Candidate native/PCK/build identity differs')
    owners.verify_metadata(build, contents, root)
    require(pipeline.input_hash(root) == build['native_source_key'] == proof['native']['key'],
            'Reviewed native sources/pins differ from the qualified bundle')
    dlls = imports(exe)
    allowed = set(owners.read(Path(root)/'build/config/windows-system-dlls.json'))
    require(len(dlls) == expected['pe_imports_verified'] and
            all(n in allowed or n.startswith('api-ms-win-crt-') for n in dlls), 'Candidate DLL imports differ')
    return dict(portable_sha256=digest(raw), portable_bytes=len(raw), exe_sha256=digest(exe),
                pck_sha256=digest(pck), pck_entries_md5_verified=len(contents),
                pe_imports_verified=len(dlls), native_key=build['native_source_key'],
                game_commit=build['game_commit'], inventory_sha256=build['preparation_demand']['inventory_sha256'])


def excerpt(source, text):
    require(source.count(text) == 1, 'Reviewed source witness changed; a new review is required')
    start = source.index(text)
    return dict(first_line=source[:start].count('\n')+1,
                last_line=source[:start+len(text)].count('\n')+1, text=text)


def stop_witness(root=ROOT):
    root = Path(root)
    source = (root/RUNTIME).read_text()
    base = (root/BASE).read_text()
    publication = '''\ttrials.append(trial.duplicate(true))
\tif not _write_json("sequence-prefix.json", {"trials": trials, "no_retry": true}): report_io_failed = true
\tif not bool(trial.valid): abort_reason = "Attribution trial guard failed: " + str(trial.id)
\ttrial.clear()
\tif not abort_reason.is_empty(): scenarios.resize(scenario_index + 1)'''
    scheduler = '''\t\t\t_scenario_drained()
\t\t\tscenario_index += 1
\t\t\tif scenario_index >= (2 if mode == "startup" else scenarios.size()):
\t\t\t\t_finish("completed", "Short startup timing check completed; only warmup and N1 ran" if mode == "startup" else "All applicable engine scenarios ran")
\t\t\telse: _start_scenario()'''
    return dict(finding='sequence_prefix_io_does_not_stop_next_trial',
                basis='Source control-flow inspection only; no engine or injected runtime fault executed.',
                preconditions=dict(completed_trial_valid=True, abort_reason='',
                                   scenario_index=0, scheduled_trials=5, sequence_prefix_write=False),
                publication=dict(file=RUNTIME, source_sha256=digest(source.encode()), **excerpt(source,publication)),
                scheduler=dict(file=BASE, source_sha256=digest(base.encode()), **excerpt(base,scheduler)),
                path=['The completed trial is copied before the prefix write.',
                      'Write failure changes report_io_failed; trial.valid and abort_reason remain unchanged.',
                      'No scenario truncation occurs while abort_reason is empty.',
                      'The inherited scheduler increments index 0 to 1 and calls the next _start_scenario().'],
                impact='The next recorder/terrain setup can start after an already detected prefix I/O failure.',
                runtime_reproduction='not_run; required before accepting the correction')


def derive(archive, evidence=EVIDENCE, root=ROOT):
    root, evidence = Path(root), Path(evidence)
    proof = owners.read(evidence)
    require(proof['schema'] == 'cairn-preparation-owner-proof-1' and
            proof['status']['capability_verified'] is True and proof['status']['qualified'] is False and
            proof['ci']['run']['id'] == 40216786118 and proof['ci']['run']['conclusion'] == 'success',
            'The reviewed capability proof or CI result differs')
    required = {'static','windows / native / native-binaries','windows / export-and-test','windows / counter-artifact-recheck'}
    jobs = {j['name']: j for j in proof['ci']['jobs']}
    require(required <= jobs.keys() and all(jobs[n]['conclusion'] == 'success' for n in required),
            'Missing required capability qualification job')
    identity = candidate(archive, proof, root)
    current = replay(proof, proof['candidate']['build'])
    previous = proof['preceding_cancelled_run']
    require(previous['ci_run'] == 39998646163 and previous['conclusion'] == 'cancelled',
            'Cancelled packaging run was reclassified')
    cancelled = replay(previous, previous['build'])
    witness = stop_witness(root)
    return dict(schema=VERSION, reviewed_head='b6b36a4b1186f064d11e5a94140fe3539c6fbf77',
                source_evidence_sha256=digest(evidence.read_bytes()), candidate=identity,
                current_controls=current, cancelled_run_controls=cancelled,
                control_reports_verified=4,
                semantic_corruptions_rejected=current['semantic_corruptions_rejected']+cancelled['semantic_corruptions_rejected'],
                finding=witness, decision=dict(route_authorized=False, declaration_created=False,
                    reason='Correct and verify prefix-publication failure stopping before declaring a route.',
                    next_task='Fix only the new preparation-demand mode and reader; inject prefix-write failure in matching editor/release without a route; verify a new portable PCK with the same exact native bundle.'),
                attribution_route_processes=0, engine_processes=0,
                runtime_or_inventory_changed=False, native_build_required=False,
                historical_pilot_flags=dict(historical_v1_pilot=False,shipping_cycles_pilot=False,shipping_observer_pilot=False),
                measurement_valid=False, shipping_cost_estimate=None, qualified=False,
                target_performance='not_run', laptop_action_required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = derive(args.candidate, args.evidence)
    if args.check:
        require(result == owners.read(args.check), 'Saved launch review differs')
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, controls=4, corruptions_rejected=result['semantic_corruptions_rejected'],
                         route_authorized=False, engine_processes=0, finding=result['finding']['finding'])))


if __name__ == '__main__':
    main()
