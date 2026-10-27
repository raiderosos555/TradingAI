"""Build a REVIEW copy only. Never writes source files or contacts MT5/GitHub.

Requires an empty destination. Further updates must be exported to a new review
directory and diffed, not blindly copied over a checkout. No push is implemented.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def protect(root):
    files = list((root/'trading_ai').glob('*.py'))
    files += list((root/'research/forward_validation').glob('*.py'))
    files += list((root/'research/forward_context').glob('*.py'))
    files += list(root.glob('config*.json'))
    files += [root/'state/runtime/effective-config.json']
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in files if p.is_file()}

def private_values(root):
    values = set()
    for p in root.glob('config*.json'):
        obj=json.loads(p.read_text(encoding='utf-8-sig'))
        for key in ('account_login', 'account_server'):
            if obj.get(key): values.add(str(obj[key]))
        auth=obj.get('runtime',{}).get('authorization_id')
        if auth: values.add(str(auth))
    # The legacy research default was copied from an account balance.
    original=(root/'trading_ai/portfolio_research.py').read_text(encoding='utf-8-sig')
    balance=re.search(r'initial_equity=(\d+\.\d+)',original)
    if balance:
        value=balance.group(1); values.add(value)
        values.add(value.replace('.',','))
        values.add(f'{float(value):,.2f}'.replace(',',' ').replace('.',','))
    return sorted(values, key=len, reverse=True)

def sanitize(text, values, markdown=False):
    for value in values:
        if value.isdigit(): replacement='123456789'
        elif re.fullmatch(r'\d+\.\d+',value): replacement='100000.0'
        elif re.fullmatch(r'[\d ,]+',value): replacement='[PRIVATE AMOUNT OMITTED]'
        elif value.startswith('demo-'): replacement='EXAMPLE-NOT-AUTHORIZED'
        else: replacement='EXAMPLE-DEMO-SERVER'
        text=text.replace(value,replacement)
    text=re.sub(r'(?i)([A-Z]:[\\/]+Users[\\/]+)[^\\/\s\"\x27]+',lambda m:m.group(1)+'EXAMPLE_USER',text)
    text=re.sub(r'(?i)(MetaQuotes[\\/]+Terminal[\\/]+)[a-f0-9]{32}',lambda m:m.group(1)+'EXAMPLE_TERMINAL',text)
    text=re.sub(r'(?i)\bS-1-5-21-(?:\d+-){2,}\d+\b','EXAMPLE-SID',text)
    if markdown:
        # Remove whole paragraphs, never silently fabricate account evidence.
        sensitive=re.compile(r'(?i)(?:\d[\d .,]*\s*(?:PLN|USD|EUR)\b|(?:equity|balance|saldo|kapitał początkow).{0,70}\d|(?:ticket|login|rachunek|account_login)\s*[:=#` ]+\d{6,}|\|\s*\d{8,12}\s*\||DEMO wykonał|pozycje raportowane|przy pierwszym odczycie tej kontynuacji|Przy uruchomieniu była|obecne pozycje FX|Nowe numery transakcji|management-after-recovery\.json)')
        text='\n\n'.join('[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]' if sensitive.search(p) else p for p in re.split(r'\n\s*\n',text))
        text='> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.\n\n'+text
    return text

def build(root, dest, audit):
    if dest.exists() and any(dest.iterdir()): raise SystemExit('Destination must be empty')
    if dest.resolve()==root.resolve() or root.resolve() in dest.resolve().parents:
        raise SystemExit('Export must be separate from the active installation')
    audit.mkdir(parents=True,exist_ok=True); dest.mkdir(parents=True,exist_ok=True)
    before=protect(root); values=private_values(root)
    (audit/'private-deny-values.json').write_text(json.dumps(values),encoding='utf-8')
    excluded=[]; records=[]; sizes={}; large=[]
    allowed={'.py','.ps1','.mq5','.mqh','.md','.patch'}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root); name=rel.as_posix()
        if rel.parts[0]=='publication': continue
        size=p.stat().st_size
        bucket=sizes.setdefault(rel.parts[0],{'files':0,'bytes':0})
        bucket['files']+=1; bucket['bytes']+=size
        if size>5*1024**2: large.append({'path':name,'bytes':size})
        top=rel.parts[0]
        selected=(top in {'trading_ai','tests','tools','mql5','research','docs'} and p.suffix in allowed)
        selected |= top in {'examples','schemas'} and p.suffix=='.json'
        selected |= name in {'.gitignore','pyproject.toml','config.json'}
        selected &= not any(part in {'__pycache__','.git','.venv','validation','inputs'} for part in rel.parts)
        # Frozen code is useful for review; original configs/manifests and evidence are not exported.
        if not selected or size>1024**2 or p.is_symlink():
            if top not in {'.venv','state','exchange','trading_ai_briefing.egg-info'}:
                excluded.append({'path':name,'bytes':size,'reason':'not on text/source allowlist, private evidence, generated, or >1 MiB'})
            continue
        raw=p.read_bytes(); text=raw.decode('utf-8-sig')
        if name=='config.json':
            cfg=json.loads(text); cfg['terminal_path']=''; cfg['engine']['enabled']=False;cfg['collection']['enabled']=False
            text=json.dumps(cfg,indent=2)+'\n'
        text=sanitize(text,values,p.suffix=='.md')
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8',newline='\n')
        records.append({'path':name,'source_sha256':sha(raw),'export_sha256':sha(target.read_bytes()),'changed_for_export':raw!=target.read_bytes()})
    # A synthetic template satisfies test fixtures without retaining actual account or permission.
    cfg=json.loads((root/'config.demo.json').read_text(encoding='utf-8-sig'))
    cfg.update(mode='DRY_RUN',terminal_path='',account_login=0,account_server='',live_enabled=False,live_allowlist=[])
    cfg.pop('runtime',None);cfg.pop('broker_time_offset_seconds',None)
    cfg['risk']['max_positions']=2;cfg['engine']['enabled']=False;cfg['collection']['enabled']=False
    for symbol in cfg['symbols'].values(): symbol['trading_enabled']=False
    (dest/'examples/config.demo.example.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    test=dest/'tests/test_demo_slots.py'
    test.write_text(test.read_text(encoding='utf-8').replace("/'config.demo.json'","/'examples/config.demo.example.json'"),encoding='utf-8')
    test=dest/'tests/test_complete_system.py'
    test.write_text(test.read_text(encoding='utf-8').replace('self.c,self.brief=fixture(self.b.now)', 'self.c,self.brief=fixture(self.b.now)\n        self.c["engine"]["enabled"] = True  # Explicitly enable only this in-memory test fixture.'),encoding='utf-8')
    after=protect(root)
    if before!=after: raise SystemExit('Protected source changed during export; review required')
    inventory={'created_at':datetime.now(timezone.utc).isoformat(),'directories':sizes,'large_files':sorted(large,key=lambda x:-x['bytes']),'excluded':excluded,'mapping':records,'protected_unchanged':before==after,'protected_hashes':before}
    (audit/'inventory-private.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    print(json.dumps({'exported_files':len(records),'large_files':len(large),'protected_unchanged':before==after}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True,type=Path);ap.add_argument('--dest',required=True,type=Path);ap.add_argument('--audit',required=True,type=Path)
    a=ap.parse_args();build(a.source,a.dest,a.audit)
