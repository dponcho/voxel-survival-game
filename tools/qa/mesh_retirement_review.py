"""Review the exact lifetime candidate and retained failed prefix, without an engine."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import tempfile
import zipfile

import mesh_admission_candidate_audit as audit
import mesh_retirement as retirement
import preparation_failed_prefix_review as prefix
from preparation_owner_review import embedded
from shipping_saved_artifact_recheck import normalize

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT/'docs/evidence/m1-mesh-retirement-cloud-2026-10-26.json'
PROOF_SHA256 = 'e4f35957fb05f5356c21b8c4c5fe52ae68a3440bb1c3e10eb92772c25a1ad329'
PREFIX = ROOT/'docs/evidence/m1-preparation-failed-prefix-review-2026-10-26.json'
PREFIX_SHA256 = 'd35a4417b953648d9d78643ac195b2ebd2807cf64542c13f4b63bd8277947707'
VERSION = 'm1-mesh-retirement-saved-review-1'
require, read = retirement.require, retirement.read


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_proof(p):
    require(p['schema'] == 'cairn-mesh-retirement-cloud-1' and p['status'] == dict(
        capability_verified=True, qualified=False, target_performance='not_run', m1='blocked',
        laptop_action_required_now=False), 'Lifetime proof status changed')
    run = p['ci']['run']
    require(run['id'] == 40440351282 and run['status'] == 'completed' and run['conclusion'] == 'success'
            and run['run_attempt'] == 1 and run['head_sha'] == p['source_commit'] ==
            '2489baaa0f2686634a1bec15b7977608372b6c35', 'Lifetime CI/source changed')
    jobs = {j['name']: j for j in p['ci']['jobs']}
    required = ('static', 'windows / native / native-binaries', 'windows / export-and-test',
                'windows / counter-artifact-recheck')
    require(all(jobs[n]['conclusion'] == 'success' for n in required) and
            all(j['conclusion'] == 'skipped' for n, j in jobs.items() if 'pilot' in n or
                n in ('preparation-demand', 'preparation-recheck')), 'CI verdict or consumed route changed')
    require(p['validation']['attribution_route_processes'] == 0 and
            p['validation']['automatic_retry'] is False and
            all(v['enabled'] is False for v in p['consumed_requests'].values()),
            'Consumed request enabled or route declared')
    require(p['permanent_consumed_reservation']['commit'] ==
            '8ab1624e0a74f153b6189afa837fb24f6688d8c9', 'Consumed reservation changed')
    b, n = p['build'], p['native']
    require(p['exported_game_commit'] == b['game_commit'] ==
            '856537ab2ca7a6c58b8168cfe975fb7c7994c302' and
            n['key'] == b['native_source_key'] == n['manifest']['engine_inputs'],
            'Candidate native/source identity changed')
    require(b['engine_binaries'] == {k: v for k, v in n['manifest']['files'].items() if k.endswith('.exe')},
            'Matching template hashes changed')
    identity = {k: n['manifest'][k] for k in ('engine_inputs', 'godot_commit', 'voxel_commit')}
    require(set(n['qualification']) == {'editor', 'debug', 'release'} and
            all(q == dict(errors=[], game_commit=b['game_commit'], identity=identity, passed=True)
                for q in n['qualification'].values()), 'Native qualification changed')
    require(p['prior_proofs'][PREFIX.name] == PREFIX_SHA256 and
            p['prior_proofs'][prefix.EVIDENCE.name] == prefix.PROOF_SHA256, 'Historical proof binding changed')


def source_files(p, root):
    expected = ('build/patches/voxel/m1-admission.json', 'native/sandbox_world/godot/retirement_probe.cpp',
                'native/sandbox_world/godot/retirement_before.h', 'native/sandbox_world/godot/m1_hooks.h',
                'tools/qa/mesh_retirement.py', 'game/scripts/m1_mesh_retirement_tests.gd')
    require(set(p['source_files']) == set(expected), 'Source witness paths changed')
    for name, item in p['source_files'].items():
        require(embedded(item) == (Path(root)/name).read_bytes(), 'Reviewed lifetime source changed')


def verify_sources(p, root=ROOT):
    # Current-source identity is a CLI acceptance check, separate from archived
    # CI-verdict tests. A future native correction must not keep this old key.
    require(audit.input_hash(root) == p['native']['key'], 'Current native sources differ from reviewed candidate')
    require(prefix.launch.plan() is False and prefix.launch.recheck_plan() is False, 'Consumed request enabled')
    source_files(p, root)
    for name, expected in p['prior_proofs'].items():
        require(Path(name).name == name and name.endswith('.json') and
                digest((Path(root)/'docs/evidence'/name).read_bytes()) == expected,
                'Retained history changed')


def portable(path, expected, build):
    path = Path(path)
    require(path.stat().st_size == expected['portable_bytes'] and
            retirement.sha(path) == expected['portable_sha256'], 'Exact portable candidate changed')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(z.testzip() is None and len(names) == len(set(names)) and
                all(n and not n.startswith('/') and not any(v in ('..', '') for v in n.rstrip('/').split('/'))
                    and ':' not in n and '\\' not in n for n in names), 'Portable archive paths/CRC differ')
        require(json.loads(z.read('BUILD_INFO.json')) == build, 'Portable build identity differs')
        exe, pck = z.read('Cairn.exe'), z.read('Cairn.pck')
    contents = audit.pack(pck)
    require(json.loads(contents['build_info.json']) == build and digest(exe) == expected['exe_sha256'] ==
            build['engine_binaries']['template_release.exe'] and digest(pck) == expected['pck_sha256'] and
            len(contents) == expected['pck_entries_md5_verified'], 'PCK/native identity differs')
    dlls = audit.imports(exe)
    allowed = set(read(ROOT/'build/config/windows-system-dlls.json'))
    require(len(dlls) == expected['pe_imports_verified'] and
            all(n in allowed or n.startswith('api-ms-win-crt-') for n in dlls), 'PE imports differ')
    return contents


def extract_artifact(path, metadata, destination):
    path, destination = Path(path), Path(destination)
    require(path.stat().st_size == metadata['size_in_bytes'] and
            'sha256:'+retirement.sha(path) == metadata['digest'], 'Downloaded artifact bytes changed')
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        require(0 < len(items) <= 4096 and len({i.filename for i in items}) == len(items) and
                sum(i.file_size for i in items) <= 512*1024*1024 and z.testzip() is None,
                'Artifact population/expanded bound/CRC differs')
        for item in items:
            parts = item.filename.rstrip('/').split('/')
            require(all(v not in ('', '.', '..') and ':' not in v and '\\' not in v for v in parts)
                    and not stat.S_ISLNK(item.external_attr >> 16), 'Artifact path escaped')
        z.extractall(destination)
    return dict(bytes=path.stat().st_size, sha256=retirement.sha(path), members=len(items),
                expanded_bytes=sum(i.file_size for i in items))


def controls(p):
    with tempfile.TemporaryDirectory(prefix='cairn-retirement-controls-') as td:
        folder = Path(td)
        for label in ('editor', 'release'):
            target = folder/('mesh-retirement-'+label)
            target.mkdir()
            for name, key in (('controls.json', 'report'), ('validation.json', 'validation')):
                (target/name).write_bytes(embedded(p['controls'][label][key]))
        result = retirement.saved_controls(folder, p['build'])
    require(result == p['local_saved_controls'] and all(result[k] == p['controls'][k]['result']
            for k in result), 'Replayed lifetime verdicts differ')
    return result


def body(source, marker):
    source = re.sub(r'//[^\n]*|/\*.*?\*/', '', source, flags=re.S)
    first = source.index('{', source.index(marker))
    depth = 1
    for end in range(first+1, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if not depth:
            return source[first+1:end]
    raise RuntimeError('Unclosed reviewed function')


def lifetime_source(p, old):
    patch = json.loads(embedded(p['source_files']['build/patches/voxel/m1-admission.json']))
    current = next(v['replacement'] for v in patch if v['path'] == 'terrain/free_mesh_task.h')
    frozen = old['source_witness']['free_mesh_task']
    prefix.retained_release_order(frozen)
    current, frozen = [body(s, 'void run(TimeSpreadTaskContext &ctx)') for s in (current, frozen)]
    ref, end = 'Ref<ArrayMesh> array = _mesh;', 'cairn::record_deletion(bytes, start, surface);'
    def depth(text, token):
        before = text[:text.index(token)]
        return before.count('{')-before.count('}')
    require(current.count(ref) == current.count(end) == frozen.count(ref) == frozen.count(end) == 1 and
            depth(current, ref) == 1 and depth(current, end) == depth(frozen, ref) == depth(frozen, end) == 0 and
            current.index('const uint64_t start') < current.index(ref) < current.index('_mesh.unref();') <
            current.index(end), 'Local owner still outlives deletion bracket')
    hooks = embedded(p['source_files']['native/sandbox_world/godot/m1_hooks.h']).decode()
    hook = body(hooks, 'inline void record_deletion(')
    require(hook.index('retirement_control_before_end(bytes, start, surface)') <
            hook.index('const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;') <
            hook.index('frame_upload_usec += elapsed;'), 'Witness/ending-clock/charge order changed')
    native = embedded(p['source_files']['native/sandbox_world/godot/retirement_probe.cpp']).decode()
    observation = body(native, 'void before_endpoint(')
    require('Ref<' not in observation and 'current->alive = alive(current->object);' in observation and
            'ObjectDB::get_instance(id)' in native, 'Witness acquired an owner or lost ObjectDB observation')
    before = embedded(p['source_files']['native/sandbox_world/godot/retirement_before.h']).decode()
    frozen_run = re.search(r'    void run\(TimeSpreadTaskContext &ctx\) override \{.*?(?=    ~)', before, re.S)
    require(frozen_run is not None and digest(frozen_run.group().encode()) == retirement.BEFORE_SHA256,
            'Frozen rejected lifetime body changed')
    return dict(corrected_local_scope_depth=1, ending_clock_scope_depth=0, frozen_local_scope_depth=0,
        frozen_run_sha256=retirement.BEFORE_SHA256,
        corrected_run_sha256=digest(current.encode()), source_order='scope exit, non-owning witness, ending clock, charge',
        synchronous_lifetime_gap_closed=True, renderer_deferred='unverified')


def gaps(boundaries, records):
    result = prefix.inner_main(boundaries, records)
    require(result['partition_available'], 'Crossing preparation roots make gap topology unavailable')
    lo, hi = map(int, result['endpoints'])
    wall_lo, wall_hi = result['wall_enclosure_usec']
    roots = [r for r in records if r['lane'] == 1 and not r['parent'] and
             wall_lo <= r['reads'][0]['wall_before_usec'] <= r['reads'][3]['wall_after_usec'] <= wall_hi]
    previous, slot, groups = lo, 'inner-start', {}
    for row in roots:
        begin = row['reads'][0]['cycles']
        key = str(slot)+'->'+str(row['slot'])
        g = groups.setdefault(key, dict(count=0, cycles=0, largest_cycles=0))
        g['count'] += 1; g['cycles'] += begin-previous
        g['largest_cycles'] = max(g['largest_cycles'], begin-previous)
        previous, slot = row['reads'][3]['cycles'], row['slot']
    groups[str(slot)+'->inner-end'] = dict(count=1, cycles=hi-previous, largest_cycles=hi-previous)
    require(sum(g['cycles'] for g in groups.values()) == int(result['gap_cycles']), 'Gap topology lost demand')
    return dict(partition=result, predecessor_successor={k: dict(count=v['count'], cycles=str(v['cycles']),
        largest_cycles=str(v['largest_cycles'])) for k, v in sorted(groups.items())},
        causal_owner=None, scope='Adjacent raw endpoints on the same thread; no process subtraction or owner inference.')


def failed_prefix(artifact, player, old):
    original = read(prefix.EVIDENCE)
    require(retirement.sha(prefix.EVIDENCE) == prefix.PROOF_SHA256, 'Original consumed proof changed')
    files = prefix.archive_files(artifact, original['original_archive'])
    with tempfile.TemporaryDirectory(prefix='cairn-retirement-prefix-') as td:
        folder = Path(td)
        for name, raw in files.items():
            path = folder/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        restored = prefix.recovery.restore_sources(folder)
        require(prefix.launch.files(folder) == original['audited_files'], 'Original audited file population changed')
        raw = next((folder/'raw').iterdir())
        batch = read(raw/'preparation-demand-attribution.json')
        portable(player, original['candidate'], batch['build'])
        sequence = prefix.launch.prep.reconcile(raw, batch['build'], ROOT/'game/diagnostics/preparation_demand_inventory.json')
        require(sequence == original['sequence'], 'Retained failed sequence changed')
        topology = []
        for t, expected in zip(batch['trials'], old['trials']):
            ledger = prefix.launch.prep.trial_ledger(raw, t)
            require(ledger['passed'] and t['id'] == expected['id'] and t['valid'] is expected['valid'],
                    'Retained prefix trial identity changed')
            item = gaps(t['cycle_boundaries'], ledger['records'])
            require(item['partition'] == expected['inner_main'], 'Original inner partition changed')
            topology.append(dict(id=t['id'], valid=t['valid'], **item))
            if not t['valid']:
                require(prefix.failed_event(t, ledger['records']) == old['failure'], 'Original 819 us failure changed')
    require(len(topology) == 3 and [t['valid'] for t in topology] == [True, True, False] and
            old['valid_bare_trials'] == 1 and old['complete_bare_quartet'] is False,
            'Failed prefix became a complete control quartet')
    return dict(archive_files=len(files), audited_files=len(original['audited_files']), recovered_source_files=restored,
        sequence=sequence, trials=topology, failure=old['failure'], valid_bare_trials=1, complete_bare_quartet=False,
        shipping_cost_estimate=None, retrospective_qualification=False)


def compare_audits(actual, windows, linux, proof):
    require(normalize(actual) == normalize(windows) == normalize(linux) and
            actual['mesh_retirement_controls'] == proof['local_saved_controls'],
            'Complete Windows/Linux/local candidate audits differ')
    return dict(complete_audits_match=True, portable_sha256=actual['portable_sha256'],
        pck_entries=actual['pck_entries_md5_verified'], pe_imports=actual['pe_imports_verified'],
        self_tests=actual['self_tests_verified'], ordinary=actual['ordinary'])


def derive(player_artifact, export_artifact, qualification_artifact, linux_artifact, old_artifact, old_player,
           evidence=PROOF, previous=PREFIX):
    require(retirement.sha(evidence) == PROOF_SHA256 and retirement.sha(previous) == PREFIX_SHA256,
            'Frozen lifetime/prefix proof changed')
    p, old = read(evidence), read(previous)
    verify_proof(p)
    verify_sources(p)
    c = controls(p)
    source = lifetime_source(p, old)
    retained = failed_prefix(old_artifact, old_player, old)
    with tempfile.TemporaryDirectory(prefix='cairn-retirement-candidate-') as td:
        stage = Path(td); identities = {}
        names = ((player_artifact, 'Cairn-windows-x86_64-', 'build/published-player'),
                 (export_artifact, 'Cairn-evidence-', 'downloaded'),
                 (qualification_artifact, 'Cairn-native-evidence-', 'build/native-qualification-evidence'),
                 (linux_artifact, 'Cairn-counter-saved-recheck-', 'linux'))
        for path, start, target in names:
            meta = [a for a in p['ci']['artifacts'] if a['name'].startswith(start)]
            require(len(meta) == 1, 'Artifact identity is ambiguous')
            identities[start] = extract_artifact(path, meta[0], stage/target)
        published = stage/'build/published-player'
        contents = portable(published/'Cairn-windows-x86_64.zip', p['candidate'], p['build'])
        retirement.verify_metadata(p['build'], contents, ROOT)
        require(read(published/'BUILD_INFO.json') == p['build'], 'Published build changed')
        windows_path = stage/'downloaded/reports/m1-mesh-admission-independent-audit.json'
        require(retirement.sha(windows_path) == p['windows_independent_audit_sha256'], 'Original Windows audit changed')
        windows = read(windows_path)
        replay = read(stage/'linux/cpu-cycle-downloaded-recheck.json')
        require(replay == p['linux_downloaded_replay'] and replay['engine_executed'] is False and
                replay['candidate_audit_reproduced'] is True, 'Linux saved replay changed')
        lines = (stage/'linux/counter-candidate-recheck.log').read_text(encoding='utf-8-sig').splitlines()
        markers = [json.loads(s.split('CAIRN_INDEPENDENT_AUDIT=', 1)[1]) for s in lines if 'CAIRN_INDEPENDENT_AUDIT=' in s]
        require(len(markers) == 1, 'Linux complete audit marker missing or repeated')
        for name in ('game', 'native', 'docs', 'build/config', 'build/patches'):
            shutil.copytree(ROOT/name, stage/name)
        shutil.copy2(ROOT/'build/dependencies.lock.json', stage/'build/dependencies.lock.json')
        shutil.copytree(stage/'downloaded/reports', stage/'reports')
        shutil.copytree(stage/'downloaded/build/engine-bundle', stage/'build/engine-bundle')
        (stage/'dist').mkdir(); shutil.copy2(published/'Cairn-windows-x86_64.zip', stage/'dist/Cairn-windows-x86_64.zip')
        old_root = audit.ROOT
        try:
            audit.ROOT = stage
            with (stage/'local-replay.log').open('w', encoding='utf-8') as output, contextlib.redirect_stdout(output):
                audit.audit()
        finally:
            audit.ROOT = old_root
        actual = read(stage/'reports/m1-mesh-admission-independent-audit.json')
        agreement = compare_audits(actual, windows, markers[0], p)
        observed = []
        for path in sorted((stage/'reports').rglob('summary.json')):
            for phase in read(path).get('operation_phases', []):
                reasons = prefix.terrain_budget.reasons(phase)
                if reasons:
                    observed.append(dict(report=path.relative_to(stage/'reports').as_posix(),
                        scenario=phase.get('scenario'), phase=phase['phase'], reasons=reasons,
                        upload=phase['upload'], deletion=phase['deletion'], data_apply=phase.get('data_apply'),
                        terrain_time_overruns=phase.get('terrain_time_overruns')))
        require(observed == p['retained_broader_operation_failures'], 'Broader operation failures changed')
    return dict(schema=VERSION, reader_sha256=retirement.sha(Path(__file__)), proof_sha256=PROOF_SHA256,
        previous_review_sha256=PREFIX_SHA256, candidate=p['candidate'], native_key=p['native']['key'],
        game_commit=p['build']['game_commit'], artifact_archives=identities, lifetime_source=source,
        controls=c, audit_agreement=agreement, retained_prefix=retained, broader_operation_failures=observed,
        engine_processes_executed=0, runtime_changed=False, native_key_changed=False, qualified=False,
        target_performance='not_run', shipping_cost_estimate=None,
        decision=dict(next_task='Bounded event-specific cycle witnesses for the existing synchronous terrain-operation guards.',
            basis='The kind-3 lifetime prerequisite is closed. Kind-1/2 overruns still stop otherwise complete trials; their event-specific CPU demand is unavailable. Gap adjacency is not causal ownership.',
            preparation_owner_expansion='deferred; 15->1 topology does not identify an intervening engine/renderer/allocator owner',
            new_process_declared=False, consumed_process_retry=False, laptop_action=False,
            threshold_changes=False, inventory_or_codec_changed_by_review=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('player-artifact', 'export-artifact', 'qualification-artifact', 'linux-artifact', 'old-artifact', 'old-player'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = derive(args.player_artifact, args.export_artifact, args.qualification_artifact,
                    args.linux_artifact, args.old_artifact, args.old_player)
    if args.check:
        require(result == read(args.check), 'Committed lifetime review differs')
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, engine_processes=0,
        cases=sum(len(v['cases']) for v in result['controls'].values()),
        semantic_faults=sum(len(v['mutations_rejected']) for v in result['controls'].values()),
        complete_audits_match=True, retained_failure_usec=result['retained_prefix']['failure']['elapsed_usec'],
        qualified=False)))


if __name__ == '__main__':
    main()
