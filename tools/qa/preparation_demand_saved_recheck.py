"""Reproduce downloaded preparation results without an engine."""
from pathlib import Path
import base64
import hashlib
import shutil

import preparation_demand_ci as launch

RECOVERY=launch.ROOT/'docs/evidence/m1-preparation-source-snapshot-recovery-2026-10-25.json'


def restore_sources(folder,recovery=RECOVERY):
    """Restore only hash-bound public source snapshots omitted by upload."""
    folder=Path(folder);preflight=launch.read(folder/'preflight.json');restored=[]
    for name,expected in preflight['source_sha256'].items():
        launch.require(name in launch.SNAPSHOTS,'Unexpected source snapshot path')
        path=folder/'source'/name
        if path.is_file():continue
        launch.require(name in ('.github/workflows/ci.yml','.github/workflows/preparation-demand.yml'),
                       'Missing snapshot cannot be recovered as measured data')
        record=launch.read(recovery)
        launch.require(record['artifact_id'] == 12623918109 and record['ci_run'] == 40259410841 and
            record['source_commit'] == preflight['context']['source_commit'],'Recovery source/run differs')
        item=record['files'][name]
        launch.require(type(item['bytes']) is int and 0 < item['bytes'] <= 16384 and item['sha256'] == expected,
                       'Recovery byte bound or original digest differs')
        data=base64.b64decode(item['base64'],validate=True)
        launch.require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == expected,
                       'Recovered source differs from immutable preflight')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        restored.append(dict(path='source/'+name,bytes=len(data),sha256=expected,source_commit=record['source_commit']))
    return restored


def run():
    source=launch.ROOT/'build/downloaded-preparation-pilot'
    require=launch.require
    require(not launch.REPORTS.exists(),'Fresh preparation saved replay required')
    shutil.copytree(source,launch.REPORTS)
    expected=launch.read(launch.REPORTS/'independent-audit.json')
    recovered=restore_sources(launch.REPORTS)
    actual=launch.audit()
    require(actual == expected,'Downloaded Windows/Linux preparation audit differs')
    launch.write_json(launch.ROOT/'reports/preparation-demand-downloaded-recheck.json',dict(passed=True,
        engine_executed=False,qualified=False,target_performance='not_run',candidate=actual['candidate'],
        engine_processes=actual['engine_processes'],sequence=actual['sequence'],saved_faults=actual['saved_faults'],
        retained_files=len(actual['files']),source_snapshot_recovery=recovered))
    print('Preparation raw prefix, ownership, immutable boundaries and failures reproduced; no engine executed.')


if __name__=='__main__':run()
