"""Retry only unfinished chunks after a demonstrated local serialization bottleneck."""
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
A=Path(__file__).resolve().parent; ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=A/'resolved_collection.json'
if out.exists() or (A/'retries').exists():raise SystemExit('Immutable retry exists')
data=read(A/'collection.json'); cfg=read(A/'retry_config.json')
assert 'finished_host_utc' in data
assert read(A/'codec_validation.json')['decompressed_bytes_identical']
failed=[b for i in data['instruments'] for b in i['blocks'] if b['status'] in ['ERROR','TIMEOUT','API_ERROR']]
assert failed and all(b['status']=='TIMEOUT' for b in failed)
for block in failed:
    phases=[json.loads(line) for line in (A/block['path']/'phases.jsonl').read_text().splitlines()]
    assert any(p['phase']=='TICKS_DONE' and p.get('count') is not None for p in phases), 'Not a proven post-response timeout'
data.update(original_collection_sha256=sha(A/'collection.json'),retry_config_sha256=sha(A/'retry_config.json'),
    retry_worker_sha256=sha(A/'fast_probe.py'),retry_started_host_utc=datetime.now(timezone.utc).isoformat(),prior_attempts=[])
env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/Lib/site-packages'))
began=time.monotonic(); stop=False
for instrument in data['instruments']:
    for index,block in enumerate(instrument['blocks']):
        if block['status'] in ['OBSERVED','EMPTY']:continue
        if stop or time.monotonic()-began>=cfg['max_series_seconds_before_next_chunk']:continue
        data['prior_attempts'].append(dict(alias=instrument['alias'],**block))
        dest=A/'retries'/instrument['alias']/Path(block['path']).name
        dest.mkdir(parents=True)
        lo=datetime.fromtimestamp(block['start_raw_ms']/1000,timezone.utc)
        hi=datetime.fromtimestamp(block['end_raw_ms']/1000,timezone.utc)
        result=dict(start_raw_ms=block['start_raw_ms'],end_raw_ms=block['end_raw_ms'],path=dest.relative_to(A).as_posix())
        with (dest/'stdout.txt').open('w') as so,(dest/'stderr.txt').open('w') as se:
            child=subprocess.Popen([getattr(sys,'_base_executable',sys.executable),str(A/'fast_probe.py'),
                '--out',str(dest),'--alias',instrument['alias'],'--start',lo.isoformat(),'--end',hi.isoformat()],
                env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                code=child.wait(timeout=cfg['timeout_per_chunk_seconds'])
                result.update(status='COMPLETED' if code==0 else 'ERROR',returncode=code)
            except subprocess.TimeoutExpired:
                child.kill();code=child.wait(timeout=5);result.update(status='TIMEOUT',returncode=code)
        result['child_pid']=child.pid
        if result['status']=='COMPLETED':
            coverage=read(dest/'coverage.json');result.update(status=coverage['status'],count=coverage['count'])
        stop=result['status'] not in ['OBSERVED','EMPTY']
        instrument['blocks'][index]=result
        out.write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(instrument['alias'],lo.hour,result['status'],result.get('count'),flush=True)
data['retry_finished_host_utc']=datetime.now(timezone.utc).isoformat()
out.write_text(json.dumps(data,indent=2),encoding='utf-8')
