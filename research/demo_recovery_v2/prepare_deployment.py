"""Create an uninstalled, pinned release and deployment config. No task changes."""
import hashlib,json,os,shutil,sys
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1];release=A/'release';out=A/'deployment'
if release.exists():raise SystemExit('Release exists; preserve it and create a new version for changes')
release.mkdir();out.mkdir(exist_ok=True)
shutil.copytree(A/'candidate/trading_ai',release/'trading_ai',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(A/'candidate/config.json',release/'config.json')
for name in ['supervisor.py','launcher.py']:shutil.copyfile(A/name,release/name)
sys.path.insert(0,str(A));from make_config import build
path=build(out,mode='DEMO');cfg=json.loads(path.read_text())
cfg.update(source=str(release),home=str(ROOT/'state/recovery-v2'))
files=list(release.rglob('*.py'))+[release/'config.json',Path(cfg['engine_config'])]
cfg['pinned_files']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
path.write_text(json.dumps(cfg,indent=2))
(out/'release-manifest.json').write_text(json.dumps({str(p.relative_to(release)):hashlib.sha256(p.read_bytes()).hexdigest() for p in release.rglob('*') if p.is_file()},indent=2))
print('Prepared release and DEMO proposal only; no initialization, task, or engine change.')
