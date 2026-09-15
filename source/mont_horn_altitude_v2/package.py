from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/mont_horn_altitude_v2';dest=O/'mont_horn_altitude_v2.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for p in [R/'apercu_mont_horn_altitude_v2.html',R/'Mt_Horn_entrance_Sky.png',R/'source/layouts_magenta_v1/palette.py']:z.write(p,str(p.relative_to(R)))
 for p in sorted((R/'renders/mont_horn_panorama_v1/bruts').glob('*.png')):z.write(p,str(p.relative_to(R)))
 for n in ['03_falaises_gauches','04_falaises_droites','05_chemin_pierre_grise','06_entree_nord_et_marches']:
  p=R/f'renders/mont_horn_panorama_v1/mont_horn/horn_{n}.png';z.write(p,str(p.relative_to(R)))
print(dest, dest.stat().st_size, 'bytes')
