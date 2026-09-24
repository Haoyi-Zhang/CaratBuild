#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, os, re, stat, subprocess, sys
root=Path(__file__).resolve().parents[1]
errors=[]; warnings=[]; parsed={'json':0,'csv':0}
for p in sorted((root/'results').rglob('*')) if (root/'results').exists() else []:
    if not p.is_file(): continue
    try:
        if p.suffix=='.json': json.loads(p.read_text(encoding='utf-8')); parsed['json']+=1
        elif p.suffix=='.csv':
            with p.open(newline='',encoding='utf-8') as f: list(csv.reader(f)); parsed['csv']+=1
    except Exception as e: errors.append(f'unparseable result {p.relative_to(root)}: {e}')
for p in root.rglob('*'):
    rel=p.relative_to(root)
    if p.is_symlink(): errors.append(f'symlink not permitted: {rel}')
    if p.is_dir() and p.name in {'.git','__pycache__','.pytest_cache','.mypy_cache'}: errors.append(f'cache/VCS directory: {rel}')
    if p.is_file() and (p.suffix in {'.pyc','.pyo'} or p.name=='.DS_Store'): errors.append(f'generated/cache file: {rel}')
repro=root/'scripts'/'reproduce.sh'
if not repro.is_file(): errors.append('missing scripts/reproduce.sh')
elif not os.access(repro,os.X_OK): errors.append('scripts/reproduce.sh is not executable')
else:
    txt=repro.read_text(encoding='utf-8')
    for i,line in enumerate(txt.splitlines()):
        if re.match(r'^\s*exec\s+',line):
            later=[x for x in txt.splitlines()[i+1:] if x.strip() and not x.lstrip().startswith('#')]
            if later: errors.append('premature exec makes later reproduction checks unreachable')
# Shell syntax and non-empty scientific evidence gates.
if repro.is_file():
    shellcheck = subprocess.run(["bash", "-n", str(repro)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if shellcheck.returncode:
        errors.append("reproduce.sh shell syntax error: " + shellcheck.stdout[-1000:])
scientific=[]
if (root/'results').exists():
    for q in (root/'results').rglob('*'):
        if not q.is_file() or q.suffix not in {'.json','.csv'}:
            continue
        low=q.name.lower()
        if any(x in low for x in ('audit','environment','trial','resource','performance','timing')):
            continue
        scientific.append(str(q.relative_to(root)))
if len(scientific)<5:
    errors.append(f"too few non-audit scientific result files: {len(scientific)}")

# Verify public-input hashes in a subprocess so failures are explicit.
vp=root/'scripts'/'verify_public_inputs.py'
if vp.exists():
    cp=subprocess.run([sys.executable,str(vp)],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if cp.returncode: errors.append('public input verification failed: '+cp.stdout[-1000:])
else: warnings.append('no public-input verifier')
# Search textual artifacts for private absolute paths and unresolved claim placeholders.
private_patterns=[r'/home/[^/\s]+/',r'/Users/[^/\s]+/',r'[A-Za-z]:\\Users\\[^\\\s]+\\']
for p in root.rglob('*'):
    if p.resolve() in {Path(__file__).resolve(), (root/'scripts'/'sanitize_outputs.py').resolve()}: continue
    if not p.is_file() or p.stat().st_size>5_000_000 or p.suffix.lower() in {'.pdf','.png','.jpg','.jpeg','.zip'}: continue
    try: t=p.read_text(encoding='utf-8')
    except Exception: continue
    for pat in private_patterns:
        if re.search(pat,t): errors.append(f'private absolute path in {p.relative_to(root)}'); break
out={'schema_version':1,'status':'PASS' if not errors else 'FAIL','errors':errors,'warnings':warnings,'parsed_results':parsed,'file_count':sum(1 for p in root.rglob('*') if p.is_file())}
(root/'results').mkdir(exist_ok=True)
(root/'results'/'reviewer_audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
if errors: raise SystemExit(1)
