from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_trois_v2';OLD=R/'renders/waterfall_lake_fidele_v1';m=json.loads((OLD/'manifest.json').read_text());dest=O/'waterfall_lake_trois_v2.zip'
files={R/m['source'],OLD/'manifest.json',OLD/'sprites/matiere_cascade_gba.png',R/'source/cote_v4_abyss/night.py',R/'source/layouts_magenta_v1/palette.py',R/'apercu_waterfall_lake_trois_v2.html'}
for n in m['static']:files.add(OLD/f'jour/lake_jour_{n}.png')
for n in m['animated']:
 for p in range(24):files.add(OLD/f'jour/lake_jour_{n}_{p:02}.png')
for n in m['static']:
 if n!='01_eau_profondeurs_originales':files.add(OLD/f'nuit/lake_nuit_{n}.png')
for n in ['07_cascade_descendante','08_ecume_impact']:
 for p in range(24):files.add(OLD/f'nuit/lake_nuit_{n}_{p:02}.png')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for p in sorted(files):z.write(p,str(p.relative_to(R)))
print(dest,dest.stat().st_size,'bytes')
