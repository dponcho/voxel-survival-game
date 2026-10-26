"""Reproduce downloaded preparation results without an engine."""
from pathlib import Path
import shutil

import preparation_demand_ci as launch


def run():
    source=launch.ROOT/'build/downloaded-preparation-pilot'
    require=launch.require
    require(not launch.REPORTS.exists(),'Fresh preparation saved replay required')
    shutil.copytree(source,launch.REPORTS)
    expected=launch.read(launch.REPORTS/'independent-audit.json')
    actual=launch.audit()
    require(actual == expected,'Downloaded Windows/Linux preparation audit differs')
    launch.write_json(launch.ROOT/'reports/preparation-demand-downloaded-recheck.json',dict(passed=True,
        engine_executed=False,qualified=False,target_performance='not_run',candidate=actual['candidate'],
        engine_processes=actual['engine_processes'],sequence=actual['sequence'],saved_faults=actual['saved_faults'],
        retained_files=len(actual['files'])))
    print('Preparation raw prefix, ownership, immutable boundaries and failures reproduced; no engine executed.')


if __name__=='__main__':run()
