"""Independent geometry, saved native replay and complete/failed/null guards.

This first-boundary correctness check is neither a route performance result nor
a qualification policy. The ordinary operation/evaluation tests remain active.
"""
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/m1_frontier_boundary.json'
STAGES = ['prepared', 'crossed-before-engine'] + [f'handover-{i}' for i in range(16)] + ['crossed-settled', 'unprepared-failure-control']


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def cells(pose):
    """Choose cells geometrically, without calling the production planner."""
    px, _, pz = map(Fraction, pose)
    # First column outside the current 96 m demand; pick the two Z cells whose
    # boxes have smallest distance to the route. No frustum-based omission.
    x = math.ceil((px + 96) / 16)
    candidates = list(range(math.floor(pz/16)-2, math.floor(pz/16)+3))
    candidates.sort(key=lambda z: (max(z*16-pz, pz-(z+1)*16, 0), -z))
    z0 = math.floor(pz/16)
    adjacent = next(z for z in candidates if z != z0)
    return [[x, -1, z0], [x, 0, z0], [x, -1, adjacent], [x, 0, adjacent]]


def demand(pose, radius, side=16):
    lo = [max(math.floor((v-radius)/side), b) for v,b in zip(pose, [-256,-1,-256])]
    hi = [min(math.ceil((v+radius)/side), b) for v,b in zip(pose, [256,2,256])]
    return lo, hi


def preparation_bounds(pose):
    lo, hi = demand(pose, 96)
    dlo, dhi = demand(pose, 128)
    targets = cells(pose)
    base_count = math.prod(h-l for l,h in zip(lo,hi))
    extra = sum(not all(l <= v < h for l,v,h in zip(lo,c,hi)) for c in targets)
    require(base_count + extra <= 511, 'Resident mesh envelope exceeds 511')
    # A 16³ preparation region and its actual one-data-cell meshing halo are
    # wholly inside data-only demand. No additional data envelope is permitted.
    for c in targets:
        require(all(l <= max(v-1,blo) and min(v+2,bhi) <= h
                    for l,v,h,blo,bhi in zip(dlo,c,dhi,[-256,-1,-256],[256,2,256])), 'Preparation escaped data halo')
    return base_count + extra


def classification(sample, fog):
    if sample.get('status') != 'measured':
        return 'inconclusive', None, None
    n,c,r,u,e = (sample.get(k) for k in ('checked_regions','candidate_regions','ready_regions','unready_regions','empty_regions'))
    d = sample.get('frontier_distance_m')
    require(all(type(v) in (int,float) and int(v)==v for v in (n,c,r,u,e)), 'Missing native counts')
    require(0 < n <= c <= 1024 and r >= 0 and u >= 0 and r+u==n and 0 <= e <= r, 'Incomplete native counts')
    require(type(d) in (int,float) and math.isfinite(d) and d >= 0, 'Missing native distance')
    require(fog == json.loads(FIXTURE.read_text())['fog'], 'Fog requirement changed')
    f = Fraction(str(d)); t = max(Fraction(0), min(Fraction(1), (f-16)/80))
    transmittance = 1-t*t*(3-2*t)
    result = 'failed' if u and f < 96 else ('inconclusive' if not u and f < 96 else 'passed')
    return result, float(f-96), float(transmittance)


def reconcile_source(root):
    fixture = json.loads(FIXTURE.read_text())
    path = root / fixture['source']['relative_file']
    require(hashlib.sha256(path.read_bytes()).hexdigest() == fixture['source']['file_sha256'], 'Public seed hash mismatch')
    selected = []
    with path.open(newline='') as stream:
        for row in csv.DictReader(stream):
            if int(row['frame']) in fixture['source']['frames']:
                selected.append(row)
    require([int(r['frame']) for r in selected] == fixture['source']['frames'], 'Seed frame sequence mismatch')
    for i,row in enumerate(selected):
        require(row['frontier_mesh_state'] == fixture['source']['states'][i] and row['frontier_block']=='7;0;0', 'Seed state mismatch')
        require(float(row['frontier_distance_m']) == fixture['source']['distances_m'][i], 'Seed distance mismatch')
        pose = fixture['before_camera'] if i==0 else fixture['crossed_camera']
        require([float(row['camera_'+a]) for a in 'xyz'] == pose, 'Seed pose mismatch')
    return {'public_seed_verified': True, 'rows': len(selected), 'sha256': fixture['source']['file_sha256']}


def reconcile(folder, build):
    path = folder / 'summary.json'
    require(0 < path.stat().st_size <= 1048576, 'Missing or oversized replay evidence')
    s = json.loads(path.read_text())
    f = json.loads(FIXTURE.read_text())
    require(s['schema']==1 and s['version']=='m1-forward-four-1' and s['passed'] is True and s['failures']==[], 'Replay failed/incomplete')
    require(s['qualified'] is False and s['target_performance']=='not_run', 'Replay qualified hardware')
    require(s['build']==build, 'Replay build differs from candidate')
    require([c['name'] for c in s['cases']] == f['controls'], 'Missing/reordered replay case')
    rows = 0
    for case in s['cases']:
        enabled = case['name'].startswith('corrected')
        require(case['workers']==int(case['name'][-1]) and case['enabled'] is enabled, 'Worker/policy mismatch')
        require(case['settled'] is True and case['drained'] is True, 'Stalled/undrained replay')
        require(case['begin_usec'] < case['cleanup_begin_usec'] <= case['end_usec'], 'Replay boundary order')
        require(case['released_preparation_viewers']==(4 if enabled else 0), 'Leaked preparation nodes')
        require(case['policy']['viewer_count']==(4 if enabled else 0) and case['policy']['required_visual_radius_m']==96 and case['policy']['data_radius_m']==128, 'Workload envelope changed')
        require([r['stage'] for r in case['rows']]==STAGES, 'Incomplete/reordered native rows')
        previous = case['begin_usec']
        engine = -1
        for i,row in enumerate(case['rows']):
            require(previous <= row['usec'] <= case['cleanup_begin_usec'] and row['engine_frame'] >= engine, 'Native row boundary order')
            previous, engine = row['usec'], row['engine_frame']
            require(row['yaw']==f['yaw'], 'Camera route changed')
            expected_pose = f['before_camera'] if i==0 else ([48.5,f['crossed_camera'][1],10] if i==19 else f['crossed_camera'])
            require(all(abs(a-b)<1e-6 for a,b in zip(row['camera'],expected_pose)), 'Camera pose changed')
            expected_cells = cells(row['base_pose'])
            # The first process advance still holds the preparation column;
            # subsequent advances retarget after the base-viewer handover.
            if i <= 2 or i==19:
                expected_cells = cells([f['before_camera'][0] if i<=2 else f['crossed_camera'][0],0,10])
            require(row['preparation_cells']==(expected_cells if enabled else []), 'Preparation cell/handover mismatch')
            outcome, clearance, transmittance = classification(row['sample'],s['fog'])
            require(row['assessment']['evaluation']==outcome and row['assessment']['status']=='measured', 'Frontier classification mismatch')
            require(abs(row['assessment']['fog_clearance_m']-clearance)<1e-8 and abs(row['assessment']['fog_transmittance']-transmittance)<1e-12, 'Fog arithmetic mismatch')
            sample = row['sample']
            if sample['unready_regions']:
                cell = sample['block']
                lo = [cell[j]*16 for j in range(3)]; hi = [(cell[j]+1)*16 for j in range(3)]
                lo[1] = max(lo[1],-16); hi[1] = min(hi[1],7)
                distance = math.sqrt(sum(max(l-p,p-h,0)**2 for l,p,h in zip(lo,row['camera'],hi)))
                require(abs(sample['frontier_distance_m']-distance)<1e-4, 'Native nearest-region distance differs from independent AABB')
            require(len(row['original_targets_submitted'])==4 and all(type(v) is bool for v in row['original_targets_submitted']), 'Missing target readiness')
            if enabled and i < 19:
                require(all(row['original_targets_submitted']) and outcome=='passed', 'Corrected submitted coverage lost')
            if not enabled and i==1:
                require(outcome=='failed' and sample['block']==f['target'] and sample['mesh_state']=='missing' and row['original_targets_submitted']==[False]*4, 'Baseline failure not reproduced')
                require(abs(sample['frontier_distance_m']-f['source']['distances_m'][1])<1e-5, 'Baseline alarm distance changed')
            if i==19:
                require(outcome=='failed', 'Genuine unprepared failure suppressed')
            if i==18:
                require(outcome=='passed' and all(row['original_targets_submitted']), 'Base demand did not eventually submit')
            require(row['terrain']['resident_mesh']<=512 and row['terrain']['resident_data']<=8192 and row['native']['retired_meshes']<=768 and row['native']['overloads']==0, 'Native bounds exceeded')
            rows += 1
        require(case['peaks']['resident_mesh']<=512 and case['peaks']['resident_data']<=8192 and case['peaks']['retired_meshes']<=768 and case['peaks']['overloads']==0, 'Transient bounds exceeded')
        require(all(case['final_native'][key]==0 for key in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes')), 'Retirement incomplete')
    missing = s['missing_input']
    require(missing['status']=='unavailable' and missing['evaluation']=='inconclusive' and all(missing[k] is None for k in ('fog_clearance_m','fog_boundary_m','fog_transmittance')), 'Unavailable measurement became passing zero')
    require(rows <= s['row_cap']==128, 'Replay row cap exceeded')
    return {'passed': True, 'cases': len(s['cases']), 'native_rows': rows, 'baseline_missing_reproduced': True,
            'corrected_first_boundary_submitted': True, 'unprepared_failure_retained': True, 'qualified': False,
            'scope': 'first 16³ boundary only; cloud correctness, not complete route or hardware performance'}
