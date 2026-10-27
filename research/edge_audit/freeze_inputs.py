"""Keep original research artifacts and inputs recoverable, never overwrite evidence."""
import json,shutil,hashlib
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
inventory=json.loads((A/'inputs/inventory.json').read_text())
for item in inventory:
 src=ROOT/item['path'];dst=A/'inputs/frozen-originals'/item['path'];dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(src,dst)
 assert hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256']
extra=[]
for src in (ROOT/'exchange/research/cost-sample-20261022').glob('*.json.gz'):
 dst=A/'inputs/cost-samples'/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(src,dst)
 extra.append({'path':str(dst.relative_to(A)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
(A/'inputs/additional-evidence-hashes.json').write_text(json.dumps(extra,indent=2),encoding='utf-8')
print('Frozen originals:',len(inventory),'cost archives:',len(extra))
