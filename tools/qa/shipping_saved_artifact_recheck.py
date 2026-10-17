"""Independent downloaded Windows evidence recheck. No engine is available or run."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/ci'))
from pipeline import input_hash
import mesh_admission_candidate_audit as main_audit
import shipping_pilot_ci as pilot_audit
from shipping_diagnostics import read, require


def copy_exact(source, destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        require(source.read_bytes() == destination.read_bytes(), 'Downloaded source/config mismatch: '+str(destination))
    else:
        shutil.copy2(source,destination)


def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,list): return [normalize(v) for v in value]
    if isinstance(value,str) and value.startswith(('[Errno 2]', '[WinError 2]')):
        return '[Errno 2] missing-file mutation'
    return value


def run():
    exported = ROOT/'build/downloaded-export-evidence'
    downloaded = ROOT/'build/downloaded-pilot-evidence'
    pilot_base = downloaded/'reports' if (downloaded/'reports').is_dir() else downloaded
    published = ROOT/'build/published-player'
    info = read(published/'BUILD_INFO.json')
    require(info['game_commit'] == os.environ['GITHUB_SHA']
            and info['native_source_key'] == info['engine_inputs'] == input_hash(),
            'Recheck source/native build identity mismatch')
    # Do not overwrite the source inputs with an artifact's self-description.
    require((exported/'build/dependencies.lock.json').read_bytes() ==
            (ROOT/'build/dependencies.lock.json').read_bytes(), 'Downloaded dependency lock mismatch')
    for source in (exported/'build/config').rglob('*'):
        if source.is_file(): copy_exact(source,ROOT/'build/config'/source.relative_to(exported/'build/config'))
    copy_exact(exported/'build/engine-bundle/manifest.json',ROOT/'build/engine-bundle/manifest.json')
    copy_exact(published/'Cairn-windows-x86_64.zip',ROOT/'dist/Cairn-windows-x86_64.zip')
    require(not (ROOT/'reports').exists(), 'Recheck requires a fresh isolated report tree')
    shutil.copytree(exported/'reports',ROOT/'reports')
    expected_main = read(exported/'reports/m1-mesh-admission-independent-audit.json')
    with (ROOT/'reports/cloud-main-recheck.log').open('w',encoding='utf-8') as output:
        with contextlib.redirect_stdout(output): main_audit.audit()
    actual_main = read(ROOT/'reports/m1-mesh-admission-independent-audit.json')
    require(normalize(expected_main) == normalize(actual_main),
            'Downloaded main audit did not reproduce the Windows verdicts/numbers')
    # Keep original downloaded measurements and prior audit immutable.
    source_pilot = pilot_base/'shipping-pilot'
    target_pilot = ROOT/'build/rechecked-pilot'
    require(not target_pilot.exists(), 'Recheck pilot destination already exists')
    shutil.copytree(source_pilot,target_pilot)
    copy_exact(pilot_base/'shipping-method-controls.json',ROOT/'reports/shipping-method-controls.json')
    expected_pilot = read(source_pilot/'independent-audit.json')
    # Verify that the moved editor case is the exact original preflight evidence.
    early = exported/'build/shipping-preflight-raw'
    before = {p.relative_to(early).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in early.rglob('*') if p.is_file()}
    after_root = source_pilot/'editor-bare'
    after = {p.relative_to(after_root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in after_root.rglob('*') if p.is_file()}
    require(before and before == after, 'Original editor preflight files changed during transfer')
    pilot_audit.REPORTS = target_pilot
    with (ROOT/'reports/cloud-pilot-recheck.log').open('w',encoding='utf-8') as output:
        with contextlib.redirect_stdout(output): actual_pilot = pilot_audit.audit()
    require(expected_pilot == actual_pilot, 'Downloaded pilot audit did not reproduce every saved field')
    full = next(p for p in target_pilot.rglob('shipping-pilot.json') if not read(p)['single_mode'])
    raw = read(full)
    controls = raw['assessment']['controls']
    trials = [dict(id=t['id'],group=t['group'],index=t['index'],mode=t['diagnostic_mode'],
                   duration_usec=t['duration_usec'],sections_usec=t['sections_usec'],
                   callback_count=t['callback_count'],marker_usec=t['marker_usec'],dose=t['dose'])
              for t in raw['trials']]
    result = dict(passed=True,qualified=False,engine_executed=False,target_performance='not_run',
        source=os.environ['GITHUB_SHA'],build=info,native_key=actual_main['native_key'],
        portable_sha256=actual_main['portable_sha256'],portable_bytes=actual_main['portable_bytes'],
        pck_entries=actual_main['pck_entries_md5_verified'],pe_imports=actual_main['pe_imports_verified'],
        self_tests=actual_main['self_tests_verified'],method_controls=actual_pilot['method_controls'],
        main_saved_faults=actual_main['saved_mutations']['count']+actual_main['reversal_saved_mutations']['count']+actual_main['full_height_saved_mutations']['count'],
        pilot_saved_faults=actual_pilot['saved_faults']['count'],
        original_editor_files_verified=len(before),pilot_folders=len(actual_pilot['records']),
        trial_count=len(trials),assessment=raw['assessment'],trials=trials,
        note='Downloaded candidate and complete original saved evidence independently reconciled on Linux; no engine or compiler executed.')
    (ROOT/'reports/saved-artifact-recheck.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('CAIRN_SAVED_RECHECK='+json.dumps(result,separators=(',',':')),flush=True)


if __name__=='__main__': run()
