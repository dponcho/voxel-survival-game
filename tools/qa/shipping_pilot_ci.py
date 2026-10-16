"""Cloud-only matching-editor/export pilot and independent published-file audit.

No engine installation/build/download takes place on a player's computer.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/ci'))
from pipeline import verify_bundle, extract, digest
from m1_integration import check
from mesh_admission_candidate_audit import pack
from shipping_diagnostics import (reconcile, evaluate, compare_method, read, require, floating)

REPORTS = ROOT/'reports/shipping-pilot'
INVENTORY_PATH = ROOT/'game/diagnostics/shipping_inventory.json'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def candidate_identity():
    published = ROOT/'build/published-player'
    archive = published/'Cairn-windows-x86_64.zip'
    info = read(published/'BUILD_INFO.json')
    expected = (published/'SHA256SUMS.txt').read_text().split()[0]
    require(digest(archive) == expected, 'Published pilot player ZIP SHA mismatch')
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        require(len(names) == len(set(names)) and zipped.testzip() is None
                and all(not Path(n).is_absolute() and '..' not in Path(n).parts and ':' not in n and '\\' not in n for n in names),
                'Published pilot ZIP paths/duplicates/CRC failed')
        require(json.loads(zipped.read('BUILD_INFO.json')) == info, 'Published pilot build identity differs')
        executable = zipped.read('Cairn.exe')
        packed = zipped.read('Cairn.pck')
    contents = pack(packed)
    require(contents['diagnostics/shipping_inventory.json'] == INVENTORY_PATH.read_bytes()
            and info['shipping_inventory_sha256'] == digest(INVENTORY_PATH), 'Published inventory mismatch')
    for name in ('m1_shipping_method.gd', 'm1_shipping_runtime.gd', 'm1_full_height_runtime.gd',
                 'benchmark.gd', 'title.gd'):
        # Godot exports tokenized GDScript, not source-format .gd bytes. The
        # committed source hashes are identity, not a token decompilation claim.
        stem = 'scripts/'+name[:-3]
        require(info['shipping_sources_sha256'][name] == digest(ROOT/'game/scripts'/name)
                and contents[stem+'.gdc'].startswith(b'GDSC')
                and ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'],
                'Published tokenized runtime/source identity mismatch: '+name)
    require(json.loads(contents['build_info.json']) == info
            and hashlib.sha256(executable).hexdigest() == info['engine_binaries']['template_release.exe'],
            'Published pilot PCK/native-template identity differs')
    return dict(build=info, archive_sha256=expected,
         executable_sha256=hashlib.sha256(executable).hexdigest(), pack_sha256=hashlib.sha256(packed).hexdigest(),
         inventory_sha256=digest(INVENTORY_PATH), pck_entries=len(contents), qualified=False)


def published_identity():
    identity = candidate_identity()
    save(REPORTS/'candidate-identity.json', identity)
    destination = ROOT/'build/shipping-pilot-player'
    extract(ROOT/'build/published-player/Cairn-windows-x86_64.zip', destination)
    exes = list(destination.rglob('Cairn.exe'))
    require(len(exes) == 1, 'Published pilot must have one portable executable')
    info = identity['build']
    return exes[0], info


def saved_mutations(folder, build):
    """Reject saved-file losses/forgeries; neither reruns nor edits original evidence."""
    labels = ('missing-final-physics', 'missing-final-callback', 'missing-edit-ack',
              'missing-native-closure', 'missing-writer-drain', 'wrong-mode-inventory',
              'operation-overrun', 'io-failure', 'retirement-not-drained', 'truncated-complete-boundary',
              'false-qualification', 'changed-positive-digest')
    rejected = []
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='cairn-shipping-fault-') as td:
            target = Path(td)/'report'
            shutil.copytree(folder, target)
            pilot = read(target/'shipping-pilot.json')
            t = pilot['trials'][0]
            if label in ('missing-final-physics', 'missing-final-callback', 'missing-edit-ack'):
                suffix = {'missing-final-physics':'-poses.csv', 'missing-final-callback':'-frames.csv',
                          'missing-edit-ack':'-frames.csv.edits.jsonl'}[label]
                path = target/(t['id']+suffix)
                lines = path.read_text(encoding='utf-8-sig').splitlines()
                path.write_text('\n'.join(lines[:-1])+'\n', encoding='utf-8')
            elif label == 'changed-positive-digest':
                positive = next(v for v in pilot['trials'] if v['dose_enabled'])
                path = target/(positive['id']+'-poses.csv')
                lines = path.read_text(encoding='utf-8-sig').splitlines()
                values = lines[1].split(',')
                values[-1] = '0'*64
                lines[1] = ','.join(values)
                path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
                # Re-sign so the independent digest/work check, not just SHA, rejects.
                positive['pose_sha256'] = digest(path)
                cp = target/(positive['id']+'-complete.json')
                complete = read(cp)
                complete['pose_sha256'] = positive['pose_sha256']
                save(cp, complete)
                bp = target/(positive['id']+'-boundary.json')
                boundary = read(bp)
                boundary['complete_sha256'] = digest(cp)
                save(bp, boundary)
            else:
                if label == 'missing-native-closure': t['closures'].pop()
                elif label == 'missing-writer-drain': t['writer_drains'].pop()
                elif label == 'wrong-mode-inventory': t['renderer_queries'] = True
                elif label == 'operation-overrun': t['phases'][0]['data_apply']['max_usec'] = 751
                elif label == 'io-failure': t['io_failed'] = True
                elif label == 'retirement-not-drained': t['native_final']['retired_meshes'] = 1
                elif label == 'truncated-complete-boundary': t['end_usec'] -= 1
                elif label == 'false-qualification': pilot['qualified'] = True
                # Keep redundant reports in agreement so semantic guards are exercised.
                cp = target/(t['id']+'-complete.json')
                complete = read(cp)
                for key in complete:
                    if key in t: complete[key] = t[key]
                save(cp, complete)
                bp = target/(t['id']+'-boundary.json')
                boundary = read(bp)
                for key in boundary:
                    if key in t: boundary[key] = t[key]
                boundary['complete_sha256'] = digest(cp)
                save(bp, boundary)
            save(target/'shipping-pilot.json', pilot)
            try:
                reconcile(target, build, INVENTORY_PATH)
            except (RuntimeError, KeyError, ValueError, IndexError):
                rejected.append(label)
            else:
                raise RuntimeError('Saved shipping fault accepted: '+label)
    return dict(passed=True, rejected=rejected, count=len(rejected))


def audit():
    identity = read(REPORTS/'candidate-identity.json')
    require(identity == candidate_identity(), 'Saved pilot candidate record differs from downloaded ZIP/PCK')
    build = identity['build']
    records = []
    for path in sorted(REPORTS.rglob('shipping-pilot.json')):
        result = reconcile(path.parent, build, INVENTORY_PATH)
        records.append(dict(folder=path.parent.relative_to(REPORTS).as_posix(), **result))
    require(len(records) == 7, 'Missing editor/release modes or finite release pilot')
    controls = read(ROOT/'reports/shipping-method-controls.json')
    require(controls['passed'] is True and controls['fixed_work_dispatch'] is True
            and len(controls['cases']) == 24 and not controls['qualified'], 'Missing adopted method controls')
    for item in controls['cases']:
        compare_method(item['assessment'], evaluate(item['trials']))
    full = next(path.parent for path in REPORTS.rglob('shipping-pilot.json')
                if not read(path)['single_mode'])
    faults = saved_mutations(full, build)
    result = dict(passed=True, qualified=False, target_performance='not_run', build=build,
                  candidate=identity, method_controls=len(controls['cases']), saved_faults=faults, records=records)
    save(REPORTS/'independent-audit.json', result)
    print(json.dumps(dict(passed=True, qualified=False, reports=len(records), faults=faults['count'],
                          pilot=next(r['assessment'] for r in records if r['trials'] > 1))), flush=True)
    return result


def run():
    REPORTS.mkdir(parents=True, exist_ok=True)
    verify_bundle()
    executable, info = published_identity()
    save(ROOT/'game/build_info.json', info)
    editor = ROOT/'build/engine-bundle/editor.exe'
    # Source imports are generated output; all runtime checks use matching binaries.
    from build_support import run as invoke
    imported = invoke([editor, '--headless', '--path', ROOT/'game', '--import'], 'shipping-editor-import', timeout=300)
    require('SCRIPT ERROR:' not in imported and 'ERROR:' not in imported, 'Shipping editor import failed')
    check([editor, '--headless', '--path', ROOT/'game', '--script', 'res://scripts/m1_shipping_method_tests.gd'],
          'shipping-method-controls', 'CAIRN_SHIPPING_METHOD=', 60)
    for suffix, command in [('editor', [editor, '--headless', '--path', ROOT/'game']),
                            ('release', [executable, '--headless'])]:
        for mode in ('bare', 'shipping', 'forensic'):
            raw = REPORTS/(suffix+'-'+mode)
            check(command+['--', '--shipping-pilot-check', '--shipping-pilot-case='+mode,
                           '--m1-report-root='+str(raw)], 'shipping-'+suffix+'-'+mode, 'CAIRN_SHIPPING_PILOT=', 360)
    check([executable, '--headless', '--', '--shipping-pilot-check',
           '--m1-report-root='+str(REPORTS/'release-pilot')],
          'shipping-release-pilot', 'CAIRN_SHIPPING_PILOT=', 1500)
    audit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    audit() if args.audit_only else run()
