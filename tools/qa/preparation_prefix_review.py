"""Review the corrected saved candidate and declare a later finite process.

Reads files only. Never executes an engine, rebuilds a candidate or enables CI.
"""
import argparse
import json
from pathlib import Path
import re
import tempfile

import preparation_owner_review as prior
import preparation_demand as owners
import preparation_prefix as prefix

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'm1-preparation-prefix-launch-review-1'
EVIDENCE = ROOT/'docs/evidence/m1-preparation-prefix-cloud-2026-10-25.json'
PROOF_SHA256 = '7ef239d68367dc67cd9885a842cd08138cd5a247ffaff413d24a45bef9801e50'
HEAD = 'f511e7610df0a87ced09d770822b811e909300b6'
SOURCE = '501d3a3d4bf13f69fc33213ca8e809fa44fee83e'
MEASURED_SHA256 = '2bd3ae7c9a51553968e0a883cd1a10adbf26f9d308be4b56b9699a461cde7566'
READER_SHA256 = {'tools/qa/preparation_prefix.py': '22142c6ed662af274b980db6561a37674262dccc711c6a58ee06fca406106909',
                 'tools/qa/preparation_demand.py': '1d31330efaa32d5ff6f620d27a47645fb260f718c19c0499cb1d545c49a6f746'}
require, digest = owners.require, prior.digest


def replay(proof):
    """Decode every nested prefix file before replaying the actual readers."""
    files, manifest = proof['files'], {}
    require(type(files) is dict and 1 <= len(files) <= 256 and
            type(proof['embedded_file_count']) is int and len(files) == proof['embedded_file_count'],
            'Prefix embedded file population differs')
    total = 0
    with tempfile.TemporaryDirectory(prefix='cairn-prefix-review-') as td:
        root = Path(td)
        for name, item in files.items():
            parts = name.split('/')
            require(len(parts) in (2,3) and parts[0] in ('editor','release') and
                    all(p not in ('','.','..') and '\\' not in p and ':' not in p for p in parts) and
                    (len(parts) == 2 or parts[1] == 'before' or re.fullmatch(r'case-[0-6]',parts[1])),
                    'Prefix embedded path escaped its declared control')
            data = prior.embedded(item)
            total += len(data)
            require(total <= owners.CAP, 'Prefix embedded aggregate exceeds bound')
            path = root/('preparation-prefix-'+parts[0])/Path(*parts[1:])
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            manifest[name] = dict(bytes=len(data),sha256=digest(data))
        require(type(proof['embedded_bytes']) is int and total == proof['embedded_bytes'],
                'Prefix embedded byte population differs')
        actual = prefix.saved_controls(root,proof['candidate']['build'])
        require(actual == proof['controls'], 'Saved prefix verdicts or corruptions differ')
        for label in ('editor','release'):
            log = (root/('preparation-prefix-'+label)/'process.log').read_text(encoding='utf-8-sig')
            require('CAIRN_PREPARATION_PREFIX=' in log and 'ERROR:' not in log, 'Prefix process log differs')
    return dict(files=manifest,file_count=len(manifest),bytes=total,controls=actual,
                semantic_corruptions_rejected=sum(len(v['mutations_rejected']) for v in actual.values()))


def verify_proof(proof,root=ROOT):
    require(proof['schema'] == 'cairn-preparation-prefix-proof-1' and proof['implementation_commit'] == SOURCE and
            proof['status'] == dict(capability_verified=True,qualified=False,shipping_cost_estimate=None,
                target_performance='not_run',m1='blocked',laptop_action_required_now=False),
            'Corrected proof identity or qualification differs')
    run = proof['ci']['run']
    require(run['id'] == 40247195315 and run['conclusion'] == 'success' and run['status'] == 'completed' and
            proof['ci']['source_commit'] == SOURCE and proof['ci']['native_source'] == 'cache', 'Corrected CI identity differs')
    required = {'static','windows / native / native-binaries','windows / export-and-test','windows / counter-artifact-recheck'}
    jobs = {j['name']:j for j in proof['ci']['jobs']}
    require(required <= jobs.keys() and all(jobs[k]['conclusion'] == 'success' for k in required),
            'Missing successful corrected-candidate job')
    flags = ('historical_v1_pilot','shipping_cycles_pilot','shipping_observer_pilot')
    require(all(proof['validation'][f] is False for f in flags) and
            proof['validation']['attribution_route_processes'] == 0, 'Consumed pilot or route was enabled')
    build = proof['candidate']['build']
    require(proof['preparation_metadata'] == build['preparation_demand'] == owners.source_metadata(root) and
            proof['exported_game_commit'] == build['game_commit'], 'Reviewed preparation metadata changed')
    manifest = proof['native']['manifest']
    require(manifest['engine_inputs'] == proof['native']['key'] == build['native_source_key'] and
            build['engine_binaries'] == {k:v for k,v in manifest['files'].items() if k.endswith('.exe')},
            'Reviewed native manifest differs')
    identity = {k:manifest[k] for k in ('engine_inputs','godot_commit','voxel_commit')}
    for label in ('editor','debug','release'):
        q = proof['native']['qualification'][label]
        require(q == dict(errors=[],game_commit=build['game_commit'],identity=identity,passed=True),
                'Native qualification changed')
    linux,local = proof['linux_downloaded_replay'],proof['local_downloaded_replay']
    require(linux == local and linux['passed'] is True and linux['qualified'] is False and
            linux['engine_executed'] is False and linux['candidate_audit_reproduced'] is True and
            linux['portable_sha256'] == proof['candidate']['portable_sha256'], 'Saved downloaded replay differs')
    for name,item in proof['prior_proofs'].items():
        require(name in ('m1-preparation-owner-cloud-2026-10-25.json','m1-preparation-owner-launch-review-2026-10-25.json'),
                'Historical proof path differs')
        raw = (Path(root)/'docs/evidence'/name).read_bytes()
        require(len(raw) == item['bytes'] and digest(raw) == item['sha256'], 'Historical proof was rewritten')
    for name,expected in READER_SHA256.items():
        require(digest((Path(root)/name).read_bytes()) == expected, 'Reviewed reader changed')


def function(source,name):
    match = re.search(r'^func '+re.escape(name)+r'\(.*?(?=^func |\Z)',source,re.M|re.S)
    require(match is not None, 'Missing reviewed function '+name)
    return match.group()


def source_witness(proof,root=ROOT):
    root = Path(root)
    runtime = (root/prior.RUNTIME).read_text(encoding='utf-8')
    base = (root/prior.BASE).read_text(encoding='utf-8')
    frozen_path = 'game/scripts/m1_preparation_prefix_before.gd'
    frozen = (root/frozen_path).read_text(encoding='utf-8')
    for name,text in ((prior.RUNTIME,runtime),(prior.BASE,base),(frozen_path,frozen)):
        require(digest(text.encode()) == proof['preparation_metadata']['sources_sha256'][Path(name).name],
                'Reviewed runtime source changed')
    original = owners.read(root/'docs/evidence/m1-preparation-owner-launch-review-2026-10-25.json')['finding']
    rejected = function(frozen,'_publish_finished_trial').split('\n',1)[1].strip()
    require(rejected == ('\ttrial["complete"] = true\n'+original['publication']['text']).strip(),
            'Frozen rejected publication no longer matches the historical witness')
    finalizer = function(runtime,'_finish_trial').split('\t_publish_finished_trial()\n')[0]
    require(digest(finalizer.encode()) == MEASURED_SHA256 and len(finalizer.encode()) == 7849,
            'Measured finalizer/boundary changed')
    start = function(runtime,'_start_scenario')
    require('\tif not abort_reason.is_empty(): return\n\t_setup_trial()' in start, 'Stopped-entry guard changed')
    publish = function(runtime,'_publish_finished_trial')
    expected = ['trials.append(trial.duplicate(true))','if not bool(trial.valid): abort_reason =',
        'var written: bool = _write_json("sequence-prefix.json"','var write_error: int = json_write_error',
        'var retained: Dictionary = _prefix_file_state()','prefix_publications.append(',
        'if not published:\n\t\treport_io_failed = true',
        'if abort_reason.is_empty(): abort_reason = PREFIX_ABORT','integration_failures.append(PREFIX_ABORT)',
        'trial.clear()','if not abort_reason.is_empty(): scenarios.resize(scenario_index + 1)']
    positions = [publish.index(s) for s in expected]
    require(positions == sorted(positions), 'Post-boundary publication/first failure stopping changed')
    scheduler = original['scheduler']['text']
    require(scheduler in base and '\t_finish_trial()' in function(runtime,'_scenario_drained') and
            '\toutcome = _publication_outcome(outcome)\n' in function(runtime,'_finish_report'),
            'Inherited handover or failed batch outcome changed')
    excerpts = {'start_guard':start,'publication':publish,'scheduler':scheduler,
                'terminal_tail':'\tvar marker_end: Dictionary = probe.cpu_cycle_observation()'+
                    function(runtime,'_finish_trial').split('\tvar marker_end: Dictionary = probe.cpu_cycle_observation()',1)[1].rstrip()}
    return dict(finding='prefix_publication_continuation_gap_closed',
        basis='Saved paired real-engine controls plus exact-source control-flow review; no engine executed in this review.',
        measured_finalizer=dict(bytes=7849,sha256=MEASURED_SHA256,unchanged=True,
            compared_with='c4c599e9947882d84f4c2c1395031044b534c13e',scope='Original _finish_trial body before completed-trial publication'),
        frozen_rejected_source_sha256=digest(frozen.encode()),
        excerpts={k:dict(file=prior.BASE if k=='scheduler' else prior.RUNTIME,
            **prior.excerpt(base if k=='scheduler' else runtime,v)) for k,v in excerpts.items()})


def declaration(identity):
    return dict(schema='cairn-preparation-demand-declaration-1',method=owners.VERSION,
        prospective=True,route_authorized=True,processes=1,maximum_trials=5,automatic_retry=False,
        positive_shipping_continuation=False,process_timeout_seconds=1500,
        native_source_key=identity['native_key'],inventory_sha256=identity['inventory_sha256'],
        candidate=identity,implementation_commit=SOURCE,source_evidence_sha256=PROOF_SHA256,
        reviewed_head=HEAD,review_method=VERSION,
        trials=[dict(group='warmup',index=0)]+[dict(group='bare',index=i) for i in range(4)],
        fixed_work=dict(resolution=[1280,720],render_scale=1,render_block=32,data_chunk=16,terrain_workers=1,
            fixture_y=[-64,192],visual_radius=96,data_radius=128,physics_ticks=4320,actor_ticks=103680,
            accepted_edits=288,proxy_saves=72,route=['+X','-X','+Z']),
        observer_bounds=dict(raw_version=2,magic='CAIRNOB2',trace_bytes=33554432,lanes=8,depth=8),
        preserve_all_existing_gates=True,numerical_cost_limit='strictly below 1%; not qualified by this attribution mode',
        stop_rule='Stop on first work/counter/span/I/O/publication/operation/resource/readiness/coverage/edit failure or trial five. Retain partial and immutable complete evidence. No retry.',
        execution='A later task may launch only this exact downloaded release candidate, once; this review executes no engine.',
        qualification=False,shipping_cost_estimate=None,target_performance='not_run',
        forbidden=['positive or shipping continuation','another profile/process matrix','fitted correction',
            'frame normalization','clipping','process/thread addition or subtraction','cycle/time conversion',
            'laptop action','M2 expansion'])


def verify_declaration(saved,identity):
    require(json.dumps(saved,sort_keys=True,separators=(',',':')) ==
            json.dumps(declaration(identity),sort_keys=True,separators=(',',':')),
            'Prospective declaration changed candidate, scope or stop rule')


def derive(archive,evidence=EVIDENCE,root=ROOT):
    evidence,root = Path(evidence),Path(root)
    require(digest(evidence.read_bytes()) == PROOF_SHA256, 'Reviewed proof bytes changed')
    proof = owners.read(evidence)
    verify_proof(proof,root)
    identity = prior.candidate(archive,proof,root)
    corrected = replay(proof)
    owner = prior.replay(dict(files=proof['owner_files'],controls=proof['owner_controls']),proof['candidate']['build'])
    require(owner['file_count'] == proof['owner_embedded_file_count'] and owner['bytes'] == proof['owner_embedded_bytes'],
            'Saved owner file population differs')
    witness = source_witness(proof,root)
    return dict(schema=VERSION,reviewed_head=HEAD,source_evidence_sha256=PROOF_SHA256,candidate=identity,
        prefix_controls=corrected,owner_controls=owner,control_reports_verified=4,
        embedded_files_verified=corrected['file_count']+owner['file_count'],
        embedded_bytes_verified=corrected['bytes']+owner['bytes'],
        semantic_corruptions_rejected=corrected['semantic_corruptions_rejected']+owner['semantic_corruptions_rejected'],
        finding=witness,prospective_declaration=declaration(identity),
        decision=dict(prefix_gap_closed=True,declaration_created=True,execute_in_this_review=False,
            next_task='Prepare and run only the declared one-process release sequence; independently retain/audit every early stop. No retry or continuation.'),
        retained_broader_operation_failures=proof['retained_broader_operation_failures'],
        attribution_route_processes=0,engine_processes=0,runtime_or_inventory_changed=False,native_build_required=False,
        historical_pilot_flags={k:False for k in ('historical_v1_pilot','shipping_cycles_pilot','shipping_observer_pilot')},
        measurement_valid=False,shipping_cost_estimate=None,qualified=False,target_performance='not_run',laptop_action_required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,default=EVIDENCE)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--declaration-output',type=Path)
    parser.add_argument('--check',type=Path)
    parser.add_argument('--check-declaration',type=Path)
    args = parser.parse_args()
    result = derive(args.candidate,args.evidence)
    if args.check: require(result == owners.read(args.check), 'Saved corrected launch review differs')
    if args.check_declaration: verify_declaration(owners.read(args.check_declaration),result['candidate'])
    for path,value in ((args.output,result),(args.declaration_output,result['prospective_declaration'])):
        if path: path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,controls=4,files=result['embedded_files_verified'],
        corruptions_rejected=result['semantic_corruptions_rejected'],prefix_gap_closed=True,
        prospective_declaration=True,engine_processes=0)))


if __name__ == '__main__': main()
