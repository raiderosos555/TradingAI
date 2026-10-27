import hashlib,json,shutil,difflib
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
snapshot=A/'source_snapshot'
if snapshot.exists():raise SystemExit('Snapshot exists')
snapshot.mkdir();manifest={}
for p in sorted((ROOT/'trading_ai').glob('*.py')):
    d=snapshot/'trading_ai'/p.name;d.parent.mkdir(exist_ok=True);shutil.copyfile(p,d)
    manifest[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['config.json','config.demo.json','state/runtime/effective-config.json']:
    p=ROOT/name;manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    d=snapshot/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
(A/'protected-before.json').write_text(json.dumps(manifest,indent=2))
candidate=A/'candidate';shutil.copytree(snapshot,candidate)
p=candidate/'trading_ai/runtime.py';before=p.read_text()
old="    atomic_write(root / f'{role}-status.json', canonical({'at': utcnow().isoformat(), 'pid': os.getpid(), **data}))"
new="""    # Status is telemetry, not the durable trading journal. A Windows reader
    # may temporarily deny replacement; that must not terminate error handling.
    content = canonical({'at': utcnow().isoformat(), 'pid': os.getpid(), **data})
    for attempt in range(3):
        try:
            atomic_write(root / f'{role}-status.json', content)
            return True
        except OSError:
            if attempt < 2:
                time.sleep(.05 * (attempt + 1))
            else:
                logging.getLogger('runtime.' + role).exception('Status publication failed; trading journal unchanged')
    return False"""
assert before.count(old)==1
after=before.replace(old,new)
old2="    a = p.parse_args(); run(a.config, a.state, a.exchange, a.role, a.once)"
new2="""    a = p.parse_args()
    try:
        run(a.config, a.state, a.exchange, a.role, a.once)
    except BaseException:
        logging.getLogger('runtime.' + a.role).exception('Unhandled runtime termination')
        raise"""
assert after.count(old2)==1;after=after.replace(old2,new2);p.write_text(after,encoding='utf-8')
(A/'runtime-candidate.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/trading_ai/runtime.py',tofile='b/trading_ai/runtime.py')),encoding='utf-8')
print('Snapshot + uninstalled candidate ready')
