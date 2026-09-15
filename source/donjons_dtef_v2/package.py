from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_dtef_v2';dest=O/'PMDO_DTEF_10_biomes_v2.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file() and p!=dest:z.write(p,str(p.relative_to(O)))
 for p in sorted(Path(__file__).parent.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
print('Pack:',dest.stat().st_size,'bytes')
