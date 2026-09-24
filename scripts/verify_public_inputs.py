#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys
root=Path(__file__).resolve().parents[1]
dir_=root/'inputs'/'public-patches'
meta=json.loads((dir_/'SOURCE-METADATA.json').read_text(encoding='utf-8'))
errors=[]
for row in meta['patches']:
    p=dir_/row['file']
    if not p.is_file(): errors.append(f"missing {p}"); continue
    b=p.read_bytes()
    if len(b)!=row['bytes']: errors.append(f"byte-count mismatch: {p}")
    if hashlib.sha256(b).hexdigest()!=row['sha256']: errors.append(f"sha256 mismatch: {p}")
    text=b.decode('utf-8')
    if not text.startswith('diff --git ') or '\n--- ' not in text or '\n+++ ' not in text:
        errors.append(f"not a unified diff: {p}")
if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print(f"verified {len(meta['patches'])} preserved public patch snapshots")
