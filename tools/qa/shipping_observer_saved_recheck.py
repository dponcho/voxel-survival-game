"""Reproduce downloaded Windows attribution evidence on Linux; no engine."""
import contextlib
from pathlib import Path
import shutil

from shipping_observer_ci import ROOT,audit
from shipping_observer import require,read
import sys
sys.path.insert(0,str(ROOT/'tools/ci'))
from build_support import write_json


def run():
    source=ROOT/'build/downloaded-observer-pilot'
    require(not (ROOT/'reports').exists(),'Fresh observer recheck required')
    shutil.copytree(source,ROOT/'reports/shipping-observer-pilot')
    with (ROOT/'reports/observer-saved-recheck.log').open('w',encoding='utf-8') as log:
        with contextlib.redirect_stdout(log):actual=audit()
    require(actual==read(source/'independent-audit.json'),'Windows/Linux observer audit differs')
    write_json(ROOT/'reports/shipping-observer-downloaded-recheck.json',dict(passed=True,engine_executed=False,qualified=False,
        target_performance='not_run',candidate=actual['candidate'],controls=actual['controls'],sequence=actual['sequence'],saved_faults=actual['saved_faults']))
    print('Observer raw spans, nesting, closed workers, work/operation guards and corruption controls reproduced without an engine.')


if __name__=='__main__':run()
