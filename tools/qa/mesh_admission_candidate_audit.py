"""Independent downloaded portable/native/evidence audit; never starts an engine."""
import copy,csv,hashlib,io,json,math,shutil,struct,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/ci'))
from pipeline import input_hash
from mesh_admission import compare,reconcile
from frontier_travel import reconcile as travel
from endpoint_precision import reconcile_saved as endpoint
from fixed_work import reconcile_saved as fixed,reconcile_runtime as fixed_runtime
from cpu_dose import reconcile_saved as cpu,reconcile_runtime as cpu_runtime,scope as cpu_scope
from frame_slack import reconcile_saved as frame,reconcile_runtime as frame_runtime,scope as frame_scope
from route_calibration import validate_controls,reconcile_folder
from diagnostic_method_validation import validate as method
from frontier_boundary import reconcile as boundary
from frontier_edit import reconcile as edit

def require(ok,message):
    if not ok:raise RuntimeError(message)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def pack(data):
    magic,version,major,minor,patch,flags=struct.unpack_from('<6I',data)
    require((magic,major,minor,patch)==(0x43504447,4,7,2) and version in (2,3,4) and not flags&1,'PCK identity/encryption')
    base=struct.unpack_from('<Q',data,24)[0]
    cursor=struct.unpack_from('<Q',data,32)[0] if version in (3,4) else 96
    count=struct.unpack_from('<I',data,cursor)[0];cursor+=4;result={}
    require(0<count<10000,'PCK entry bound')
    for _ in range(count):
        size=struct.unpack_from('<I',data,cursor)[0];cursor+=4
        require(size<8192,'PCK path bound')
        name=data[cursor:cursor+size].rstrip(b'\0').decode();cursor+=size
        offset,length=struct.unpack_from('<QQ',data,cursor);cursor+=16
        digest=data[cursor:cursor+16];cursor+=16
        ef=struct.unpack_from('<I',data,cursor)[0];cursor+=4
        require(ef==0 and name not in result and base+offset+length<=len(data),'PCK entry scope')
        content=data[base+offset:base+offset+length]
        require(hashlib.md5(content).digest()==digest,'PCK MD5 '+name)
        result[name]=content
    return result
def imports(data):
    pe=struct.unpack_from('<I',data,60)[0]
    require(data[:2]==b'MZ' and data[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',data,pe+4)[0]==0x8664,'x64 PE')
    count,size=struct.unpack_from('<H',data,pe+6)[0],struct.unpack_from('<H',data,pe+20)[0]
    optional=pe+24
    require(struct.unpack_from('<H',data,optional)[0]==0x20b,'PE32+')
    base=struct.unpack_from('<Q',data,optional+24)[0];headers=struct.unpack_from('<I',data,optional+60)[0]
    sections=[]
    for i in range(count):
        vs,va,sz,ptr=struct.unpack_from('<4I',data,optional+size+40*i+8)
        sections.append((va,max(vs,sz),ptr))
    def off(rva):
        if rva<headers:return rva
        for va,sz,ptr in sections:
            if va<=rva<va+sz:return ptr+rva-va
        raise RuntimeError('Unmapped import RVA')
    def name(rva):
        start=off(rva);end=data.index(b'\0',start,start+1024)
        return data[start:end].decode('ascii').lower()
    result=set()
    for directory,width in ((1,20),(13,32)):
        rva,size=struct.unpack_from('<II',data,optional+112+directory*8)
        if not rva:continue
        start=off(rva)
        for p in range(start,start+size,width):
            v=struct.unpack_from('<'+str(width//4)+'I',data,p)
            if not any(v):break
            result.add(name(v[3] if directory==1 else v[1] if v[0]&1 else v[1]-base))
    return sorted(result)

def ordinary_record(folder,s):
    heavy=[]
    for p in s['scenarios']:
        if p['workload'] in ('H1','H2'):
            keys=('id','workload','simulation_ticks','actor_ticks','accepted_proxy_edits','rejected_proxy_edits','proxy_autosaves','frontier_enabled')
            item={k:p[k] for k in keys}
            for k in ('workload_contract','workload_evidence'):
                if k in p:item[k]=p[k]
            heavy.append(item)
    return dict(folder=folder,configuration=s['configuration'],heavy=heavy)

def ordinary(reports):
    records=[];details=[];phases=operation_rows=frames=events=scenarios=0;exceedances=[]
    for path in sorted(reports.rglob('summary.json')):
        s=read(path)
        if 'scenarios' not in s or s.get('benchmark_mode')=='travel-replay':continue
        require(s['completed'] and not s['qualified'] and not s['integration_failures'],'Incomplete ordinary report')
        cpu_scope(s['cpu_dose_sensitivity'],not_run=True);frame_scope(s['frame_slack_sensitivity'],not_run=True)
        folder=path.parent;relative=path.relative_to(reports).parts[0]
        records.append(ordinary_record(relative,s));scenarios+=len(s['scenarios']);phases+=len(s['operation_phases'])
        groups={p['id']:[] for p in s['operation_phases']}
        for name in {p['raw_operations'] for p in s['operation_phases'] if p['tracing']}:
            previous=-1
            with (folder/name).open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f);require(len(reader.fieldnames)==18,'Operation schema')
                for v in reader:
                    r={k:int(n) for k,n in v.items()};operation_rows+=1
                    require(r['phase'] in groups and previous<=r['start_usec']<=r['end_usec'],'Native order/clock')
                    previous=r['end_usec'];groups[r['phase']].append(r)
        for p in s['operation_phases']:
            rows=groups[p['id']]
            if not p['tracing']:continue
            require(rows and len(rows)==p['frames'] and p['dropped_frames']==0,'Incomplete native phase')
            require(all(r['phase_boundary']==int(i==len(rows)-1) for i,r in enumerate(rows)),'Native terminal boundary')
            for kind in ('upload','deletion'):
                for key in ('count','bytes','usec'):
                    require(p[kind][key]==sum(r[kind+'_'+key] for r in rows),'Operation aggregate')
                candidates=[r for r in rows if r[kind+'_count']]
                largest=max(candidates or rows,key=lambda r:r[kind+'_max_usec'])
                for key in ('max_usec','max_bytes','max_start_usec'):
                    require(p[kind][key]==largest[kind+'_'+key],'Operation first-tie maximum')
                require(p['native_end'][kind+'_usec']-p['native_start'][kind+'_usec']==p[kind]['usec'],'Lifetime phase delta')
                if p[kind]['max_usec']>750:exceedances.append(dict(folder=relative,scenario=p['scenario'],phase=p['phase'],kind=kind,max_usec=p[kind]['max_usec']))
        for p in s['scenarios']:
            a=p['diagnostic_accounting'];frames+=p['samples']
            require(a['callbacks']==p['samples'] and not a['overflow'] and not a['invalid_partition'],'Callback count/partition')
            require(a['switched_usec']+a['shared_usec']==a['callback_usec']<=a['elapsed_usec']
                    and a['end_usec']-a['start_usec']==a['elapsed_usec']
                    and a['finalization_usec']==a['end_usec']-a['last_callback_end_usec']
                    and 0<=a['writer_drain_usec']<=a['finalization_usec'],'Complete duration/finalization')
            counts={k:a['last_'+k] for k in ('callback_usec','shared_usec','switched_usec')};rows=0;intervals=0;previous=None
            if not p['id'].startswith('AB-off-'):
                with (folder/p['raw_frames']).open(encoding='utf-8-sig',newline='') as f:
                    for row in csv.DictReader(f):
                        rows+=1;now=int(row['callback_usec']);span=round(float(row['interval_ms'])*1000);intervals+=span
                        require(int(row['frame'])==rows and int(row['diagnostic_frame'])==rows-1,'Saved callback order')
                        require(previous is None or abs(now-previous-span)<=1,'Saved interval gap');previous=now
                        for key,column in (('callback_usec','diagnostic_usec'),('shared_usec','diagnostic_shared_usec'),('switched_usec','diagnostic_switched_usec')):
                            counts[key]+=int(row[column])
                require(rows==p['samples'] and all(counts[k]==a[k] for k in counts) and abs(intervals-p['wall_seconds']*1e6)<=1,'Saved terminal callback reconciliation')
            ep=folder/p['edit_visibility_events']
            if ep.is_file():events+=sum(1 for _ in ep.open(encoding='utf-8'))
            require(p['qualified'] is False,'Qualified ordinary scenario')
            if p['workload'] in ('H1','H2'):
                details.append(dict(folder=relative,id=p['id'],coverage=p['fog_frontier'].get('exposed_samples'),reasons=p['reasons'],evaluation=p['evaluation'],qualified=p['qualified']))
        f=read(folder/'report-finalization.json')
        require(f['end_usec']-f['start_usec']==f['elapsed_usec']>=0,'Combined report finalization')
        if s['benchmark_mode']=='calibration':reconcile_folder(folder)
    return records,dict(folders=len(records),scenarios=scenarios,native_phases=phases,operation_rows=operation_rows,
        scenario_samples=frames,edit_events=events,heavy_contracts_checked=sum(len(r['heavy']) for r in records),heavy=details,
        retained_operation_exceedances=exceedances)

def mutations(folder,info,workers):
    faults=('missing','truncated','reorder','origin','invalid','inexact','desired-null','loaded-null','duplicate','permutation',
            'cap','preparation-priority','phase','clock','overflow','io','finalization','revision-join',
            'incomplete','contract','stalled','actors','edits','resource','guard','failed')
    results={}
    for fault in faults:
        with tempfile.TemporaryDirectory(prefix='cairn-admission-mutation-') as tmp:
            d=Path(tmp);shutil.copytree(folder,d,dirs_exist_ok=True)
            path=d/'mesh-admission.jsonl';m=read(d/'mesh-admission-summary.json');values=[json.loads(s) for s in path.read_text().splitlines()]
            r=next(v for v in values if v['phase']==2 and len(v['pending'])>=2 and v['admitted'])
            if fault=='missing':path.unlink()
            elif fault=='truncated':path.write_text(''.join(json.dumps(v)+'\n' for v in values[:-1]))
            else:
                if fault=='reorder':values[0],values[1]=values[1],values[0]
                if fault=='origin':r['origin']=None
                if fault=='invalid':r['valid']=False
                if fault=='inexact':r['pending'][0][4]=int(r['pending'][0][4])
                if fault=='desired-null':r['pending'][0][4]=None
                if fault=='loaded-null':r['pending'][0][3]|=4;r['pending'][0][5]=None
                if fault=='duplicate':r['pending'][1]=copy.deepcopy(r['pending'][0])
                if fault=='permutation':r['order'][0],r['order'][1]=r['order'][1],r['order'][0]
                if fault=='cap':r['loads'][0]=4
                if fault=='preparation-priority':next(v for v in values if v['phase']==1)['priority']=True
                if fault=='phase':r['phase']=3
                if fault=='clock':r['start_usec']=r['end_usec']=m['trace_finalization_end_usec']+1
                if fault=='overflow':m['snapshot']['dropped']=1
                if fault=='finalization':m['trace_finalization_begin_usec']=m['trace_finalization_end_usec']+1
                if fault=='revision-join':
                    target=next(v for v in values if v['phase']==2 and any(p[:3]==[7,0,-1] and i in v['order'][:v['admitted']] for i,p in enumerate(v['pending'])))
                    next(p for p in target['pending'] if p[:3]==[7,0,-1])[4]='9007199254740993'
                path.write_text(''.join(json.dumps(v)+'\n' for v in values));m['bytes']=path.stat().st_size
                if fault=='io':m['bytes']+=1
            if fault in ('incomplete','contract'):
                p=d/'summary.json';s=read(p)
                if fault=='incomplete':s['completed']=False
                else:s['scenarios'][0]['workload_contract']['actors']=23
                p.write_text(json.dumps(s))
            if fault in ('stalled','actors','edits','resource'):
                p=d/'travel-observations.jsonl';rows=[json.loads(v) for v in p.read_text().splitlines()]
                v=next(v for v in rows if v['stage']=='physics' and v['tick']==60)
                if fault=='stalled':v['player'][0]-=0.1
                if fault=='actors':v['actors']-=24
                if fault=='edits':v['edit_attempt']={}
                if fault=='resource':v['meshes']['blocks'][0]['mesh_id']='1'
                p.write_text(''.join(json.dumps(v)+'\n' for v in rows));t=read(d/'travel-summary.json');t['bytes']=p.stat().st_size;(d/'travel-summary.json').write_text(json.dumps(t))
            if fault=='guard':
                p=d/'travel-summary.json';t=read(p);t['phase_guards'][0]['failures']=['fabricated guard'];p.write_text(json.dumps(t))
            if fault=='failed':m['passed']=False
            (d/'mesh-admission-summary.json').write_text(json.dumps(m))
            try:reconcile(d,info,workers,True)
            except (RuntimeError,ValueError,TypeError,KeyError,OSError) as e:results[fault]=str(e)
            else:raise RuntimeError('Saved mutation accepted: '+fault)
    return dict(passed=True,count=len(results),all_rejected=True,reasons=results)

def audit():
    reports=ROOT/'reports';published=ROOT/'build/published-player'
    raw=(published/'Cairn-windows-x86_64.zip').read_bytes()
    require(raw==(ROOT/'dist/Cairn-windows-x86_64.zip').read_bytes(),'Published portable roundtrip differs')
    require(sha(raw)==(published/'SHA256SUMS.txt').read_text().split()[0],'Published checksum')
    z=zipfile.ZipFile(io.BytesIO(raw));names=z.namelist()
    require(z.testzip() is None and len(names)==len(set(names)) and all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names),'Portable CRC/paths')
    info=read(published/'BUILD_INFO.json');require(info==json.loads(z.read('BUILD_INFO.json')),'Published identity')
    entries=pack(z.read('Cairn.pck'));embedded=[json.loads(v) for k,v in entries.items() if k.endswith('build_info.json') or k.endswith('BUILD_INFO.json')]
    require(embedded==[info],'PCK identity')
    require(any('m1_frontier_admission_runtime.' in k for k in entries),'New runtime missing')
    manifest=read(ROOT/'build/engine-bundle/manifest.json')
    require(manifest==read(ROOT/'build/native-qualification-evidence/build/engine-bundle/manifest.json'),'Native qualification manifest')
    require(manifest['engine_inputs']==input_hash()==info['native_source_key']==info['engine_inputs'],'Native source key')
    binaries={k:v for k,v in manifest['files'].items() if k.endswith('.exe')}
    require(info['engine_binaries']==binaries and sha(z.read('Cairn.exe'))==binaries['template_release.exe'],'Matching native template')
    identity={k:manifest[k] for k in ('engine_inputs','godot_commit','voxel_commit')}
    tests=[ROOT/'build/native-qualification-evidence/reports'/('qualification-'+k+'.json') for k in ('editor','debug','release')]
    tests += [reports/(k+'-self-test.json') for k in ('editor','debug','release')]+[reports/('extracted-offline-'+str(i)+'.json') for i in range(2)]
    for p in tests:
        t=read(p);require(t['passed'] is True and t['errors']==[] and t['identity']==identity and t['game_commit']==info['game_commit'],'Self-test identity '+str(p))
    dlls=imports(z.read('Cairn.exe'));require(read(reports/'dependency-audit.json')=={'cairn.exe':dlls},'Independent PE imports')
    allowed=set(read(ROOT/'build/config/windows-system-dlls.json'));require(all(n in allowed or n.startswith('api-ms-win-crt-') for n in dlls),'Unbundled DLL')
    prior={}
    for label,reader in (('endpoint-precision',endpoint),('fixed-work',fixed),('cpu-dose',cpu),('frame-slack',frame)):
        v=reader(reports/('m1-'+label+'-controls.json'),reports/('m1-'+label+'-raw'))
        require(v==read(reports/('m1-'+label+'-validation.json')),'Saved controls '+label)
        prior[label]=v
    validate_controls(read(reports/'m1-route-calibration-controls.json'));method(read(reports/'m1-diagnostic-method-controls.json'))
    for label in ('editor','release'):
        for name,reader in (('cpu-dose',cpu_runtime),('frame-slack',frame_runtime)):
            v=reader(reports/('m1-'+name+'-'+label+'-raw'),info)
            require(v==read(reports/('m1-'+name+'-'+label+'-validation.json')),'Runtime '+name)
            prior[name+'-'+label]=v
        for name,reader in (('frontier-boundary',boundary),('frontier-edit',edit)):
            v=reader(reports/('m1-'+name+'-'+label+'-raw'),info)
            require(v==read(reports/('m1-'+name+'-'+label+'-validation.json')),'Replay '+name)
            prior[name+'-'+label]=v
    trials={};legacy={}
    for label in ('editor','release'):
        for workers in (1,2):
            name='m1-mesh-admission-'+label+'-'+str(workers);folders=[]
            for mode in ('fifo','priority'):
                files=list((reports/(name+'-'+mode+'-raw')).glob('*/mesh-admission-summary.json'));require(len(files)==1,'Missing admission trial')
                folders.append(files[0].parent)
            v=compare(*folders,info,workers);require(v==read(reports/(name+'-validation.json')),'Saved comparison')
            trials[name]=v
            name='m1-frontier-travel-'+label+'-'+str(workers)
            p=list((reports/(name+'-raw')).glob('*/travel-summary.json'));require(len(p)==1,'Missing prior continuous replay')
            v=travel(p[0].parent,info,workers);require(v==read(reports/(name+'-validation.json')),'Saved continuous replay')
            legacy[name]=v
    current,ordinary_result=ordinary(reports)
    baseline_path=ROOT/'docs/evidence/m1-frontier-travel-contracts-2026-10-09.json'
    if baseline_path.exists():baseline=read(baseline_path)
    else:
        baseline=[]
        previous=ROOT/'build/previous-evidence/reports'
        for p in sorted(previous.rglob('summary.json')):
            s=read(p)
            if 'scenarios' in s and s.get('benchmark_mode')!='travel-replay':baseline.append(ordinary_record(p.relative_to(previous).parts[0],s))
    require(current==baseline and len(current)==10 and ordinary_result['heavy_contracts_checked']==42,'Ordinary fixed-work/contracts changed')
    (reports/'m1-ordinary-contract-baseline.json').write_text(json.dumps(baseline,indent=2))
    print('CAIRN_ORDINARY_BASELINE='+json.dumps(baseline,separators=(',',':')),flush=True)
    folder=next((reports/'m1-mesh-admission-release-1-priority-raw').glob('*/mesh-admission-summary.json')).parent
    mutation=mutations(folder,info,1)
    result=dict(passed=True,qualified=False,target_performance='not_run',build=info,native_key=manifest['engine_inputs'],
        portable_sha256=sha(raw),portable_bytes=len(raw),exe_sha256=sha(z.read('Cairn.exe')),pck_sha256=sha(z.read('Cairn.pck')),
        pck_entries_md5_verified=len(entries),pe_imports_verified=len(dlls),self_tests_verified=len(tests),published_download_roundtrip=True,
        native_manifest=manifest,admission=trials,prior_continuous=legacy,ordinary=ordinary_result,prior_controls=prior,saved_mutations=mutation,
        target_action_required_now=False,engine_run_locally=False,executor_recovery='independent read-only audit executed in Actions after workspace disconnect')
    (reports/'m1-mesh-admission-independent-audit.json').write_text(json.dumps(result,indent=2))
    print('CAIRN_INDEPENDENT_AUDIT='+json.dumps(result,separators=(',',':')),flush=True)

if __name__=='__main__':audit()
