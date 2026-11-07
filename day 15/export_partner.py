#!/usr/bin/env python3
"""Export public challenge source only. Never include .env, access notes or run evidence."""
from pathlib import Path
import sys
import zipfile
root=Path(__file__).resolve().parent
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'exports/day15-partner.zip'
out.parent.mkdir(parents=True,exist_ok=True)
files=[p for p in root.glob('*.py') if p.is_file()]
files += [root/name for name in ('README.md','ATTACKER.md','attack-report.md','defend-report.md','comparison.md','.env.example','.gitignore','.dockerignore','start.sh')]
for folder in ('seed','trusted','deploy','tests','eval'):
    files += [p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts
              and p.suffix in ('.py','.js','.cjs','.md','.yml') or p.is_file() and p.name in ('package.json','attacks.json','Dockerfile')]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):
        if p.is_symlink() or not p.is_file():raise ValueError('unexpected export source')
        rel=p.relative_to(root).as_posix()
        if p.name=='.env' or '.local.' in p.name or rel.startswith(('runs/','logs/')):raise ValueError('private export source')
        z.write(p,rel)
print(str(out))
