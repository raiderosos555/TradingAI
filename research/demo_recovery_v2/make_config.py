"""Create explicit LAB configs, or an uninstalled DEMO proposal. Never start tasks."""
import argparse,hashlib,json,sys
from pathlib import Path
A=Path(__file__).resolve().parent

def build(root,scenario='healthy',mode='LAB',backoff=(.15,.3,.6)):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    source=A/'candidate';state=root/'state';home=root/'supervision'
    state.mkdir(exist_ok=True)
    cfg=dict(schema=1,mode=mode,home=str(home),source=str(source),state=str(state),exchange=str(root/'exchange'),
        engine_config=str(source/'config.demo.json'),python=sys.executable,scenario=scenario,
        backoff_seconds=list(backoff),healthy_seconds=.3,heartbeat_timeout=.4,startup_timeout=3,lifetime=30,
        engine_locks=[str(state/'runtime/engine'),str(state),str(root/'account-lock')],pinned_files={})
    if mode=='DEMO':
        project=A.parents[1];config=project/'config.demo.json';data=json.loads(config.read_text())
        import os
        sys.path.insert(0,str(source));from trading_ai.models import digest
        cfg.update(state=str(project/'state'),exchange=str(project/'exchange'),engine_config=str(config),
            backoff_seconds=[60,120,240],healthy_seconds=300,heartbeat_timeout=180,startup_timeout=900,
            engine_locks=[str(project/'state/runtime/engine'),str(project/'state'),str(Path(os.environ['LOCALAPPDATA'])/'TradingAI/locks'/digest([data['account_login'],data['account_server']]))])
        cfg.pop('scenario');cfg.pop('lifetime')
    files=list(source.glob('trading_ai/*.py'))+[A/'supervisor.py',A/'launcher.py',Path(cfg['engine_config'])]
    if mode=='LAB':files.append(A/'lab_runtime.py')
    cfg['pinned_files']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    path=root/'supervise.json';path.write_text(json.dumps(cfg,indent=2));return path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--scenario',default='healthy');p.add_argument('--demo-proposal',action='store_true');p.add_argument('--real-backoff',action='store_true');a=p.parse_args()
    print(build(a.root,a.scenario,'DEMO' if a.demo_proposal else 'LAB',(60,120,240) if a.real_backoff else (.15,.3,.6)))
