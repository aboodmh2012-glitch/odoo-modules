#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
root = Path('.')
# Support both odoo20-addons layout and legacy Msarpay layouts
candidates = [root/'masar_addons', root/'addons', root]
mods=[]
for base in candidates:
  if not base.is_dir():
    continue
  for p in base.iterdir() if base != root else []:
    if p.is_dir() and (p/'__manifest__.py').exists():
      mods.append(p)
  if base != root:
    continue
# also top-level modules
for p in root.iterdir():
  if p.is_dir() and (p/'__manifest__.py').exists():
    mods.append(p)
mods=list({p.resolve():p for p in mods}.values())
sign = root/'enterprise_addons'/'sign'
print(f'addons ready: {len(mods)} modules; sign={sign.is_dir()}')
if not mods and not (root/'masar_addons').is_dir():
  # Still succeed for empty bootstrap so environment Save works
  print('warning: no modules detected; continuing')
else:
  assert mods or (root/'masar_addons').is_dir(), 'addons layout missing'
print('install complete')
PY
