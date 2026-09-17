from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_cascades_v2';dest=O/'antre_cascades_v2.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for name in ['images.png','IMG_4912.jpeg','apercu_antre_cascades_v2.html','source/layouts_magenta_v1/palette.py','renders/arene_aquatique_bois_v1/bruts/arene_pierre_bois_magenta.png']:z.write(R/name,name)
print(dest,dest.stat().st_size,'bytes')
