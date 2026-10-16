"""Independent v2 terrain ledger: inclusive task spans, exclusive frame charging.

The old upload/deletion columns remain readable as partial historical evidence.
Native-frame cumulative counters survive phase boundaries; phase resets never
grant another 1/2 ms allowance. Renderer-deferred work remains unavailable.
"""
import csv
import json
from pathlib import Path


def require(value, message):
    if not value:
        raise RuntimeError(message)


def reasons(phase):
    result = [f'Individual {kind} exceeded 0.75 ms' for kind in ('upload', 'deletion')
              if phase[kind]['max_usec'] > 750]
    if phase.get('dropped_frames', 0): result.append('Native operation trace dropped frames')
    if phase.get('terrain_accounting_version') == 2:
        if phase['data_apply']['max_usec'] > 750: result.append('Individual data application exceeded 0.75 ms')
        if phase['terrain_time_overruns']: result.append('Cumulative terrain frame time exceeded its 1/2 ms budget')
        if phase['terrain_upload_overruns']: result.append('Cumulative frame upload payload exceeded its budget')
        if phase['peak_single_upload_bytes'] > 262144: result.append('Individual upload payload exceeded 256 KiB')
    return result


def flatten(row):
    if 'data_apply' not in row: return row
    result = {k:v for k,v in row.items() if type(v) is not dict}
    for kind in ('upload','deletion','data_apply'):
        result.update({kind+'_'+k:v for k,v in row[kind].items()})
    return result


def reconcile_rows(rows, phase, state=None):
    if phase.get('terrain_accounting_version') != 2:
        return dict(outcome='inconclusive', reason='legacy partial upload/deletion accounting')
    require(rows and len(rows) == phase['frames'] and phase['dropped_frames'] == 0,
            'Incomplete terrain frame ledger')
    state = {} if state is None else state
    rows = [flatten(r) for r in rows]
    for row in rows:
        keys = ('data_apply_count','data_apply_usec','data_apply_max_usec','data_apply_max_start_usec',
                'data_apply_nested_usec','frame_terrain_usec','frame_upload_bytes_total',
                'frame_time_limit_usec','frame_upload_limit_bytes','frame_single_upload_bytes')
        require(all(type(row.get(k)) in (int,float) and int(row[k]) == row[k] and row[k] >= 0 for k in keys),
                'Missing/invalid complete terrain evidence')
        require(row['frame_time_limit_usec'] in (1000,2000)
                and row['frame_upload_limit_bytes'] in (524288,1048576), 'Terrain budget changed')
        require(row['data_apply_nested_usec'] <= row['data_apply_usec'], 'Nested terrain time exceeds its parent')
        if row['data_apply_count']:
            require(row['start_usec'] <= row['data_apply_max_start_usec']
                    <= row['end_usec']-row['data_apply_max_usec']
                    and row['data_apply_max_usec'] <= row['data_apply_usec'], 'Data application outside frame segment')
        else:
            require(not any(row[k] for k in keys[:5]), 'Empty data application became nonzero')
        work = row['upload_usec']+row['deletion_usec']+row['data_apply_usec']-row['data_apply_nested_usec']
        previous = state.get(row['native_frame'])
        used, payload = (previous['frame_terrain_usec'],previous['frame_upload_bytes_total']) if previous else (0,0)
        require(row['frame_terrain_usec'] >= used+work
                and row['frame_upload_bytes_total'] >= payload+row['upload_bytes'], 'Native-frame budget reset across a phase')
        if previous and previous['end_usec'] == row['start_usec']:
            require(row['frame_terrain_usec'] == used+work
                    and row['frame_upload_bytes_total'] == payload+row['upload_bytes'], 'Nested terrain work double-counted')
        require(row['frame_single_upload_bytes'] >= row['upload_max_bytes'], 'Largest payload lost behind a slower upload')
        if previous:
            require(row['frame_time_limit_usec'] <= previous['frame_time_limit_usec']
                    and row['frame_upload_limit_bytes'] <= previous['frame_upload_limit_bytes'], 'Same-frame allowance increased')
        state[row['native_frame']] = row
    data = phase['data_apply']
    for key in ('count','usec'):
        require(data[key] == sum(r['data_apply_'+key] for r in rows), 'Data application phase sum mismatch')
    candidates = [r for r in rows if r['data_apply_count']]
    largest = max(candidates or rows,key=lambda r:r['data_apply_max_usec'])
    for key in ('max_usec','max_start_usec'):
        require(data[key] == largest['data_apply_'+key], 'Data application first-tie maximum mismatch')
    require(data['bytes'] == data['max_bytes'] == 0 and data['max_kind'] == (4 if candidates else 0), 'Data application kind/payload changed')
    require(phase['data_apply_nested_usec'] == sum(r['data_apply_nested_usec'] for r in rows), 'Nested terrain sum mismatch')
    checks = {
        'peak_frame_terrain_usec': max(r['frame_terrain_usec'] for r in rows),
        'peak_single_upload_bytes': max(r['frame_single_upload_bytes'] for r in rows),
        'terrain_time_overruns': sum(r['frame_terrain_usec'] > r['frame_time_limit_usec'] for r in rows),
        'terrain_upload_overruns': sum(r['frame_upload_bytes_total'] > r['frame_upload_limit_bytes'] for r in rows),
    }
    require(all(phase[k] == v for k,v in checks.items()), 'Terrain budget assessment mismatch')
    if 'native_start' in phase:
        require(phase['native_end']['data_apply_usec']-phase['native_start']['data_apply_usec'] == data['usec'],
                'Data application phase/lifetime mismatch')
    return dict(outcome='failed' if reasons(phase) else 'passed', reasons=reasons(phase),
                scope='synchronous terrain work; renderer-deferred costs unverified')


def reconcile_folder(folder, saved=None):
    folder = Path(folder)
    saved = saved or json.loads((folder/'summary.json').read_text(encoding='utf-8-sig'))
    state, result = {}, []
    for phase in saved['operation_phases']:
        if not phase['tracing']:
            result.append(dict(phase=phase['phase'],outcome='inconclusive',reason='trace disabled; totals only'))
            continue
        path = folder/phase['raw_operations']
        require(0 < path.stat().st_size <= 67108864, 'Missing/oversized terrain ledger')
        with path.open(encoding='utf-8-sig',newline='') as stream:
            rows = [{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
        rows = [r for r in rows if r['phase'] == phase['id']]
        result.append(dict(phase=phase['phase'],**reconcile_rows(rows,phase,state)))
    return dict(qualified=False, phases=result, renderer_deferred='unverified')
