"""Review the exact operation-witness candidate and saved evidence; never run an engine."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import mesh_admission_candidate_audit as audit
import mesh_retirement as lifetime
import mesh_retirement_review as archive
import operation_witness as witness
from preparation_owner_review import embedded
from shipping_saved_artifact_recheck import normalize

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT/'docs/evidence/m1-operation-witness-cloud-2026-11-09.json'
PROOF_SHA256 = '6941f781a5f51d1cbebfbaa207e90612969009df7ff533ea66749b2b2c9bc4a1'
SOURCE = 'e8ae2a9ea38d0169c28e6ce7b6f692c9d4407d6a'
TREE = '278661dadad5561672682253b4de49f88dfd280e'
GAME = '75f8b0a9e2fcbfd61d830f420a20e91c9f49ccd2'
KEY = 'ff3a84944e7120b6d6be80e78f7f70438906e57059400289f65339a1d4d9a540'
VERSION = 'm1-operation-witness-saved-review-1'
ARTIFACTS = dict(player=13705042193, export=13704598026, qualification=13702447617, linux=13705935580)
SOURCE_FILES = tuple('native/sandbox_world/'+n for n in witness.NATIVE) + tuple(
    'game/scripts/'+n for n in witness.SOURCES) + (
    'game/diagnostics/operation_witness.json', 'build/patches/voxel/m1-admission.json',
    'tools/qa/operation_witness.py', 'tools/qa/mesh_retirement_review.py',
    'tests/integration/test_mesh_retirement_review.py', 'tests/integration/test_operation_witness.py',
    'tests/native/test_operation_witness.cpp', '.github/workflows/ci.yml',
    '.github/workflows/windows-build.yml', '.github/workflows/engine.yml',
    'tools/ci/pipeline.py', 'tools/qa/mesh_admission_candidate_audit.py', 'tools/qa/cpu_cycle_saved_recheck.py')
require, read, digest = witness.require, witness.read, witness.digest


def verify_proof(p):
    require(p['schema'] == 'cairn-operation-witness-cloud-1' and p['status'] == dict(
        capability_verified=True, qualified=False, target_performance='not_run', m1='blocked',
        laptop_action_required_now=False), 'Operation proof status changed')
    run = p['ci']['run']
    require(run['id'] == 42681602647 and run['status'] == 'completed' and run['conclusion'] == 'success'
            and p['source_commit'] == p['ci']['source_commit'] == SOURCE and p['source_tree'] == TREE
            and p['exported_game_commit'] == p['ci']['checkout_commit'] == GAME, 'CI/source identity changed')
    jobs = {j['name']: j for j in p['ci']['jobs']}
    required = ('static', 'plan', 'windows / native / native-binaries', 'windows / export-and-test',
                'windows / counter-artifact-recheck')
    require(len(jobs) == len(p['ci']['jobs']) and all(jobs[n]['conclusion'] == 'success' for n in required)
            and all(j['conclusion'] == 'skipped' for n, j in jobs.items() if n not in required),
            'Required CI verdict or disabled process changed')
    v = p['validation']
    require(v == dict(python_regressions_per_platform=303, native_sanitizer_suites=12, cases_per_binary=15,
        semantic_faults_per_binary=20, attribution_route_processes=0, automatic_retry=False,
        unchanged_native_key=True, save_generator_compatibility_changed=False), 'Capability validation changed')
    b, n = p['build'], p['native']
    require(b['game_commit'] == GAME and b['native_source_key'] == b['engine_inputs'] == n['key'] ==
            n['manifest']['engine_inputs'] == KEY and b['target_performance'] == 'not_run', 'Native/build identity changed')
    require(b['engine_binaries'] == {k: v for k, v in n['manifest']['files'].items() if k.endswith('.exe')},
            'Matching template hashes changed')
    identity = {k: n['manifest'][k] for k in ('engine_inputs', 'godot_commit', 'voxel_commit')}
    require(set(n['qualification']) == {'editor', 'debug', 'release'} and all(q == dict(
        errors=[], game_commit=GAME, identity=identity, passed=True) for q in n['qualification'].values()),
        'Native qualification changed')
    require(n['selection'] == dict(source='artifact', key=KEY, artifact_id=12768368615, artifact_run_id=40560322527)
            and n['restore'] == dict(artifact_id=12768368615, run_id=40560322527,
                digest='sha256:ce721ac4f22e39109b3b64e8f52d42e88e754d8b5571ea21ee8ec1fd59333f50'),
            'Exact native reuse changed')
    require(all(r['enabled'] is False for r in p['consumed_requests'].values()) and
            p['permanent_consumed_reservation']['branch'] ==
            'codex/reserved-preparation-demand-17cf4e05bfa024aa93c3fcc8b5aebb061db69acf5aca7789e5dfa52d6757daad'
            and p['permanent_consumed_reservation']['commit'] == '8ab1624e0a74f153b6189afa837fb24f6688d8c9',
            'Consumed process enabled or reservation changed')
    failed = p['original_windows_failure']
    require((failed['run'], failed['job'], failed['conclusion'], failed['failed_subtest']) ==
            (40560322527, 122455768783, 'failure', 'backslash'), 'Original failed preflight reclassified')
    require(p['complete_windows_linux_local_audits_equal'] is True, 'Original complete audits disagree')


def embedded_manifest(p):
    result = {}
    def visit(value, path):
        if isinstance(value, dict):
            if 'base64_zlib' in value:
                data = embedded(value)
                result[path] = dict(bytes=len(data), sha256=digest(data))
            else:
                for key, item in value.items(): visit(item, path+'/'+key)
        elif isinstance(value, list):
            for i, item in enumerate(value): visit(item, path+'/'+str(i))
    visit(p, '')
    require(len(result) == 50, 'Embedded proof population changed')
    return result


def source_files(p, root):
    root = Path(root)
    require(set(p['source_files']) == set(SOURCE_FILES), 'Reviewed source population changed')
    for name, item in p['source_files'].items():
        require(embedded(item) == (root/name).read_bytes(), 'Reviewed operation source changed: '+name)


def verify_sources(p, root=ROOT):
    root = Path(root)
    source_files(p, root)
    require(audit.input_hash(root) == KEY and witness.source_metadata(root) == p['build']['operation_witness'],
            'Reviewed native/source key changed')
    for name, expected in p['consumed_requests'].items():
        require(read(root/'build'/name) == expected, 'Consumed request changed')
    return verify_history(p, root)


def verify_history(p, root=ROOT):
    root = Path(root)
    history = {}
    for name, expected in p['prior_proofs'].items():
        require(name in ('m1-mesh-retirement-cloud-2026-10-26.json',
                        'm1-mesh-retirement-saved-review-2026-10-27.json') and
                lifetime.sha(root/'docs/evidence'/name) == expected, 'Historical proof changed')
        history[name] = expected
    require(len(history) == 2, 'Historical proof omitted')
    old = read(root/'docs/evidence/m1-mesh-retirement-saved-review-2026-10-27.json')
    retained = old['retained_prefix']
    require(retained['failure']['elapsed_usec'] == 819 and retained['failure']['limit_usec'] == 750 and
            retained['valid_bare_trials'] == 1 and retained['complete_bare_quartet'] is False and
            retained['shipping_cost_estimate'] is None, 'Consumed failed prefix reclassified')
    return dict(proof_hashes=history, consumed_prefix_failure=retained['failure'], valid_bare_trials=1,
                complete_bare_quartet=False, previous_broader_failures=old['broader_operation_failures'])


def ordered(source, *tokens):
    positions = [source.index(token) for token in tokens]
    require(positions == sorted(set(positions)), 'Operational source endpoint/charge order changed')


def source_contract(p):
    def text(name): return embedded(p['source_files'][name]).decode('utf-8')
    hooks = text('native/sandbox_world/godot/m1_hooks.h')
    upload = archive.body(hooks, 'inline void upload_surface(')
    ordered(upload, 'const uint64_t start', 'operation_witness_begin(start)',
            'partial->add_surface_from_arrays', 'record_upload(bytes,start,witness)')
    for marker, charging in (('inline void record_upload(', 'frame_upload_usec += elapsed;'),
                             ('inline void record_deletion(', 'frame_upload_usec += elapsed;'),
                             ('inline void record_data_apply(', 'frame_upload_usec += elapsed - bounded_nested;')):
        body = archive.body(hooks, marker)
        ordered(body, 'operation_witness_ending(', 'const uint64_t end = OS::get_singleton()->get_ticks_usec();',
                charging, 'operation_witness_commit(')
    deletion = archive.body(hooks, 'inline void record_deletion(')
    ordered(deletion, 'retirement_control_before_end(bytes, start, surface)', 'operation_witness_ending(')
    patch = json.loads(text('build/patches/voxel/m1-admission.json'))
    free = next(v['replacement'] for v in patch if v['path'] == 'terrain/free_mesh_task.h')
    body = archive.body(free, 'void run(TimeSpreadTaskContext &ctx)')
    ref, charge = 'Ref<ArrayMesh> array = _mesh;', 'cairn::record_deletion(bytes, start, surface, witness);'
    def depth(token):
        before = body[:body.index(token)]
        return before.count('{')-before.count('}')
    require(depth(ref) == 1 and depth(charge) == 0, 'Last owner outlives ending reads')
    ordered(body, 'const uint64_t start', 'operation_witness_begin(start)', ref, '_mesh.unref();', charge)
    core = text('native/sandbox_world/core/operation_witness.h')
    require('sizeof(OperationWitness) <= 64 * 1024' in core and
            'CAP = 128, DEPTH = 8, OUTPUT_CAP = 256 * 1024' in core and
            'elapsed > maxima[k]' in core and 'retain_all || first || maximum || phase_maximum' in core,
            'Fixed bounds or first-tie selection changed')
    adapter = text('native/sandbox_world/godot/operation_witness.cpp')
    close = archive.body(adapter, 'Dictionary operation_witness_finish(CairnProbe &probe)')
    ordered(close, 'operation_witness = nullptr', 'd["emit_start"]', 'FileAccess::open(',
            'file->flush()', 'file->close(); file.unref();', 'd["emit_end"]')
    gd = text('game/scripts/m1_operation_witness_tests.gd')
    ordered(gd, 'var writer_start:', 'var writer_begin:', 'var text:', 'file.store_string(text)',
            'file.flush()', 'file.close()', 'var writer_end:', 'var writer_finish:')
    return dict(upload_order='start, begin reads, actual surface upload, ending reads, wall end, charge, commit',
        deletion_order='start, begin reads, last local owner scope exit, non-owning witness, ending reads, wall end, charge, commit',
        corrected_local_scope_depth=1, ending_reads_scope_depth=0, fixed_record_cap=128,
        retained_storage_cap_bytes=65536, serialized_process_cap_bytes=262144,
        writer_order='capture disabled, process start, serialize/open/write/flush/close/release, process end',
        terminal_receipt_own_write_included=False, complete_wall_cpu_demand='unavailable',
        inactive_dispatch_cost='unqualified', renderer_deferred='unverified')


def controls(p):
    with tempfile.TemporaryDirectory(prefix='cairn-operation-review-controls-') as td:
        folder = Path(td)
        for group, prefix, names in (
            ('controls', 'operation-witness-', {'controls.json', 'controls.json.events', 'controls.json.writer.json', 'validation.json'}),
            ('lifetime_controls', 'mesh-retirement-', {'controls.json', 'validation.json'})):
            require(set(p[group]) == {'editor', 'release'}, 'Control binary population changed')
            for label, item in p[group].items():
                require(set(item['files']) == names, 'Control file population changed')
                target = folder/(prefix+label); target.mkdir()
                for name, data in item['files'].items(): (target/name).write_bytes(embedded(data))
        current = witness.saved_controls(folder, p['build'])
        previous = lifetime.saved_controls(folder, p['build'])
    require(current == p['local_saved_controls'] and previous == p['local_lifetime_controls'] and
            all(v == p['controls'][k]['result'] for k, v in current.items()) and
            all(v == p['lifetime_controls'][k]['result'] for k, v in previous.items()), 'Replayed controls differ')
    return dict(operation=current, lifetime=previous, operation_cases=sum(len(v['cases']) for v in current.values()),
        lifetime_cases=sum(len(v['cases']) for v in previous.values()),
        semantic_faults_rejected=sum(len(v['mutations_rejected']) for v in (*current.values(), *previous.values())))


def compare_audits(actual, windows, linux, p):
    require(normalize(actual) == normalize(windows) == normalize(linux) ==
            normalize(json.loads(embedded(p['windows_independent_audit']))) and
            actual['operation_witness_controls'] == p['local_saved_controls'] and
            actual['mesh_retirement_controls'] == p['local_lifetime_controls'] and
            actual['ordinary'] == p['retained_broader_operation_results'], 'Complete candidate audits differ')
    return dict(complete_audits_match=True, pck_entries=actual['pck_entries_md5_verified'],
        pe_imports=actual['pe_imports_verified'], self_tests=actual['self_tests_verified'], ordinary=actual['ordinary'])


def broader_failures(reports, p):
    operations, edits = [], []
    for path in sorted(Path(reports).rglob('summary.json')):
        s = read(path); folder = path.relative_to(reports).parts[0]
        for phase in s.get('operation_phases', []):
            for kind in ('upload', 'deletion'):
                if phase[kind]['max_usec'] > 750:
                    operations.append(dict(folder=folder, scenario=phase['scenario'], phase=phase['phase'], kind=kind,
                        max_usec=phase[kind]['max_usec'], configuration=s['configuration'], operation=phase[kind]))
        for scenario in s.get('scenarios', []):
            edit = scenario.get('edit_visibility', {})
            if edit.get('p95_upper_usec', 0) > 100000 or edit.get('max_usec', 0) > 200000:
                edits.append(dict(folder=folder, id=scenario['id'], coverage=scenario['fog_frontier'].get('exposed_samples'),
                    reasons=scenario['reasons'], evaluation=scenario['evaluation'], qualified=scenario['qualified'],
                    edit_visibility=edit))
    primary = {(e['folder'], e['id']) for e in p['edit_failures']}
    ordinary_edits = [e for e in edits if (e['folder'], e['id']) in primary]
    comparison_edits = [e for e in edits if (e['folder'], e['id']) not in primary]
    require(operations == p['broader_failures'] and ordinary_edits == p['edit_failures'], 'Broader failures changed')
    for name, item in p['broader_failure_sources'].items():
        require((Path(reports)/name).read_bytes() == embedded(item), 'Original broader report bytes changed')
    return dict(operations=operations, edits=ordinary_edits, comparison_baseline_edits=comparison_edits,
                event_specific_cpu_witnesses_available=False,
                historical_failures_waived=False, shipping_cost='unqualified', target_performance='not_run')


def derive(player_artifact, export_artifact, qualification_artifact, linux_artifact, evidence=PROOF, root=ROOT):
    require(lifetime.sha(evidence) == PROOF_SHA256, 'Frozen operation proof changed')
    p = read(evidence); verify_proof(p)
    blobs, history, source, cases = embedded_manifest(p), verify_sources(p, root), source_contract(p), controls(p)
    with tempfile.TemporaryDirectory(prefix='cairn-operation-saved-review-') as td:
        stage = Path(td); identities = {}
        paths = dict(player=player_artifact, export=export_artifact, qualification=qualification_artifact, linux=linux_artifact)
        targets = dict(player='build/published-player', export='build/downloaded-export-evidence',
                       qualification='build/native-qualification-evidence', linux='linux')
        for label, path in paths.items():
            metadata = [a for a in p['ci']['artifacts'] if a['id'] == ARTIFACTS[label]]
            require(len(metadata) == 1 and metadata[0]['workflow_run']['id'] == 42681602647 and
                    metadata[0]['workflow_run']['head_sha'] == SOURCE and metadata[0]['name'].endswith(GAME),
                    'Artifact/source identity differs')
            identities[label] = dict(id=ARTIFACTS[label], **archive.extract_artifact(path, metadata[0], stage/targets[label]))
        published = stage/targets['player']; exported = stage/targets['export']; qualified = stage/targets['qualification']
        contents = archive.portable(published/'Cairn-windows-x86_64.zip', p['candidate'], p['build'])
        witness.verify_metadata(p['build'], contents, root); lifetime.verify_metadata(p['build'], contents, root)
        require(read(published/'BUILD_INFO.json') == p['build'] and
                read(qualified/'build/engine-bundle/manifest.json') == p['native']['manifest'] and
                read(qualified/'reports/native-selection.json') == p['native']['selection'] and
                read(qualified/'reports/native-restore.json') == p['native']['restore'] and
                all(read(qualified/'reports'/('qualification-'+k+'.json')) == v
                    for k, v in p['native']['qualification'].items()), 'Downloaded native/build evidence changed')
        windows_file = exported/'reports/m1-mesh-admission-independent-audit.json'
        linux_file = stage/'linux/counter-candidate-recheck.log'
        replay_file = stage/'linux/cpu-cycle-downloaded-recheck.json'
        require(windows_file.read_bytes() == embedded(p['windows_independent_audit']) and
                linux_file.read_bytes() == embedded(p['linux_complete_audit_log']) and
                replay_file.read_bytes() == embedded(p['linux_replay']), 'Original platform audit bytes changed')
        markers = [json.loads(line.split('CAIRN_INDEPENDENT_AUDIT=', 1)[1])
                   for line in linux_file.read_text(encoding='utf-8-sig').splitlines() if 'CAIRN_INDEPENDENT_AUDIT=' in line]
        require(len(markers) == 1, 'Linux complete audit missing or repeated')
        # Replay the existing saved-only entry point in a fresh process/tree.
        # This also avoids imported modules retaining an earlier ROOT default.
        for name in ('game', 'native', 'tools', 'docs', 'tests/fixtures', 'build/config', 'build/patches'):
            shutil.copytree(Path(root)/name, stage/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(Path(root)/'build/dependencies.lock.json', stage/'build/dependencies.lock.json')
        log = stage/'local-replay.log'
        with log.open('w', encoding='utf-8') as output:
            result = subprocess.run([sys.executable, str(stage/'tools/qa/cpu_cycle_saved_recheck.py')],
                cwd=stage, stdout=output, stderr=subprocess.STDOUT, timeout=300, check=False)
        require(result.returncode == 0, 'Fresh saved-only audit failed: '+log.read_text(encoding='utf-8')[-4000:])
        actual = read(stage/'reports/m1-mesh-admission-independent-audit.json')
        agreement = compare_audits(actual, read(windows_file), markers[0], p)
        replay = read(replay_file)
        require(replay == read(stage/'reports/cpu-cycle-downloaded-recheck.json') and replay['passed'] is True and
                replay['qualified'] is False and replay['engine_executed'] is False and
                replay['candidate_audit_reproduced'] is True, 'Complete Linux/local replay summaries differ')
        failures = broader_failures(stage/'reports', p)
    return dict(schema=VERSION, reader_sha256=lifetime.sha(Path(__file__)), proof_sha256=PROOF_SHA256,
        source_commit=SOURCE, source_tree=TREE, game_commit=GAME, native_key=KEY, candidate=p['candidate'],
        embedded_files=blobs, artifact_archives=identities, source_contract=source, controls=cases,
        audit_agreement=agreement, linux_local_replay=replay, retained_failures=failures, history=history,
        engine_processes_executed=0, runtime_changed=False, native_key_changed=False, qualified=False,
        target_performance='not_run', shipping_cost_estimate=None,
        decision=dict(capability_accepted=True, representative_event_attribution='not_observed',
            next_task='Implement a bounded one-shot operation-witness controller and saved route reader, with finite stop/write-failure controls and a matching portable candidate; leave its launch request disabled.',
            basis='Controls establish the recorder capability. Existing representative failures have no event CPU witnesses, and the current reader/writer are fixture-specific; they cannot validate a real route.',
            observation_preconditions='Prospective exact-candidate/workload declaration and verified failure/overflow/counter/I/O stopping, finite caps and no retry.',
            inconclusive_policy='Stop and choose an explicit bounded implementation/policy decision; do not add another observer family automatically.',
            preparation_owner_expansion='deferred; no new causal owner established', new_process_declared=False,
            consumed_process_retry=False, laptop_action=False, threshold_changes=False, inventory_or_codec_changed=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('player-artifact', 'export-artifact', 'qualification-artifact', 'linux-artifact'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = derive(args.player_artifact, args.export_artifact, args.qualification_artifact, args.linux_artifact)
    if args.check: require(result == read(args.check), 'Committed operation-witness review differs')
    if args.output: args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, engine_processes=0, operation_cases=result['controls']['operation_cases'],
        lifetime_cases=result['controls']['lifetime_cases'], semantic_faults=result['controls']['semantic_faults_rejected'],
        complete_audits_match=True, qualified=False, new_process_declared=False)))


if __name__ == '__main__': main()
