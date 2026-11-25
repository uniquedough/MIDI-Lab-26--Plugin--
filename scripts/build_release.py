#!/usr/bin/env python3
"""Create a reproducible plugin ZIP, suitable for GitHub release attachment."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'plugin.json').read_text())
version = manifest['version']
out_dir = root / 'dist'
out_dir.mkdir(exist_ok=True)
out = out_dir / f'midi-lab-plugin-v{version}.zip'
exclude = {'.git', '.venv', 'venv', 'dist', '__pycache__', '.pytest_cache'}
with ZipFile(out, 'w', ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or any(part in exclude for part in p.relative_to(root).parts) or p.suffix in ('.pyc', '.pyo'):
            continue
        z.write(p, 'midi-lab/' + str(p.relative_to(root)))
print(out)
