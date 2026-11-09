"""Independent downloaded v2 artifact audit; zero engine launches."""
import contextlib
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/ci'))
from build_support import write_json
from shipping_cycles import require, read
from shipping_cycles_ci import audit


def run():
    source = ROOT/'build/downloaded-cycles-pilot'
    require(not (ROOT/'reports').exists(), 'Fresh v2 saved recheck required')
    destination = ROOT/'reports/shipping-cycles-pilot'
    shutil.copytree(source, destination)
    with (ROOT/'reports/cycles-saved-recheck.log').open('w', encoding='utf-8') as log:
        with contextlib.redirect_stdout(log): actual = audit()
    require(actual == read(source/'independent-audit.json'), 'Downloaded Windows/Linux v2 audit differs')
    write_json(ROOT/'reports/shipping-cycles-downloaded-recheck.json', dict(passed=True, engine_executed=False,
        qualified=False, target_performance='not_run', candidate=actual['candidate'],
        sequence=actual['sequence'], saved_faults=actual['saved_faults'], controls=actual['controls']))
    print('Downloaded v2 sequence, exact counters, stop rule and saved faults rechecked without an engine.')


if __name__ == '__main__': run()
