"""Offline staged-file and entire local object-database publication gate.

Findings contain rule/path/line, never matched secret text. This is a conservative
heuristic scanner, not a proof of absence of secrets. Review remains required.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

RULES={
 'private-key':r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'github-token':r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'cloud-key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'service-token':r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|xox[baprs]-[A-Za-z0-9-]{20,}|AIza[A-Za-z0-9_-]{30,})\b',
 'jwt':r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
 'credential-in-url':r'''https?://[^\s/@:"']+:[^\s/@"']+@''',
 'literal-credential':r'''(?i)["']?(?:password|passwd|api_key|client_secret|access_token|refresh_token|private_key)["']?\s*[:=]\s*["'][^"'\r\n]{4,}["']''',
 'windows-user':r'(?i)[A-Z]:[\\/]+Users[\\/]+(?!EXAMPLE_USER\b|Public\b|Default\b)[^\\/\s"\x27]+',
 'windows-sid':r'\bS-1-5-21-(?:\d+-){2,}\d+\b',
 'terminal-identity':r'(?i)MetaQuotes[\\/]+Terminal[\\/]+[a-f0-9]{32}',
 'personal-email':r'\b[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com\b|example\.(?:com|org)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
}
FORBIDDEN_PARTS={'state','exchange','.venv','__pycache__','node_modules','.env','cache','tmp'}
FORBIDDEN_SUFFIXES={'.sqlite','.sqlite3','.db','.zip','.gz','.7z','.csv','.jsonl','.ex5','.exe','.dll','.pyd','.pem','.key','.pfx','.log','.tmp','.xml','.snapshot'}

def scan_content(name,data,deny=()):
    findings=[]
    if len(data)>1024**2: findings.append({'path':name,'rule':'file-over-1-MiB'})
    if b'\0' in data: return findings+[{'path':name,'rule':'binary-file'}]
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:return findings+[{'path':name,'rule':'non-UTF8'}]
    for rule,pattern in RULES.items():
        for match in re.finditer(pattern,text):
            findings.append({'path':name,'rule':rule,'line':text.count('\n',0,match.start())+1})
    for value in deny:
        if value and value in text: findings.append({'path':name,'rule':'private-local-deny-value'})
    return findings

def scan_path(name):
    p=Path(name)
    if (set(p.parts)&FORBIDDEN_PARTS or p.suffix.lower() in FORBIDDEN_SUFFIXES
        or p.name.startswith('.env') or p.name in {'config.local.json','config.demo.json'}
        or any(x in p.name.lower() for x in ('credentials','secrets'))):
        return [{'path':name,'rule':'forbidden-path'}]
    return []

def git(*args):
    return subprocess.check_output(['git',*args],stderr=subprocess.PIPE)

def batch_objects(ids):
    ids=sorted(set(ids))
    if not ids:return {}
    proc=subprocess.run(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),capture_output=True,check=True)
    result={};offset=0
    for expected in ids:
        end=proc.stdout.index(b'\n',offset);oid,kind,size=proc.stdout[offset:end].split();start=end+1
        result[expected]=proc.stdout[start:start+int(size)];offset=start+int(size)+1
    return result

def run(staged=False,history=False,deny=()):
    findings=[];files=[];objects=0;commits=0;staged_entries=[];object_entries=[]
    if staged:
        entries=git('ls-files','--stage','-z').split(b'\0')
        for entry in filter(None,entries):
            head,path=entry.split(b'\t',1); mode,oid,stage=head.split();name=path.decode('utf-8')
            files.append(name);findings+=scan_path(name)
            if mode!=b'100644' and mode!=b'100755':findings.append({'path':name,'rule':'non-regular-file'})
            staged_entries.append((name,oid.decode()))
    if history:
        # Includes unreachable objects, not only commits reachable from HEAD.
        entries=git('cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype)').decode().splitlines()
        for entry in entries:
            oid,kind=entry.split();objects+=1
            if kind=='commit':commits+=1
            if kind in {'blob','commit','tag'}:object_entries.append((oid,kind))
            elif kind=='tree':
                for line in git('ls-tree','-rz',oid).split(b'\0'):
                    if line:findings+=scan_path(line.split(b'\t',1)[1].decode())
    contents=batch_objects([oid for _,oid in staged_entries]+[oid for oid,_ in object_entries])
    checked=set()
    for name,oid in staged_entries:
        findings+=scan_content(name,contents[oid],deny);checked.add(oid)
    for oid,kind in object_entries:
        if oid not in checked:findings+=scan_content('object:'+oid,contents[oid],deny)
    return {'status':'PASS' if not findings else 'BLOCKED','files':len(files),'objects':objects,'commits':commits,'findings':findings,'limitations':'Heuristic rules and local deny-list; no guarantee against novel/encoded secrets. Manual review and private remote remain necessary.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--staged',action='store_true');ap.add_argument('--history',action='store_true');ap.add_argument('--deny',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();deny=json.loads(a.deny.read_text(encoding='utf-8')) if a.deny else []
    report=run(a.staged,a.history,deny)
    if a.output:a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
