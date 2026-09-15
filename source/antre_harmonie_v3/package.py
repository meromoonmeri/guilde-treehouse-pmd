from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_harmonie_v3';dest=O/'antre_harmonie_v3.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for name in ['apercu_antre_harmonie_v3.html','source/layouts_magenta_v1/palette.py','source/amp_plains_fleurie_v1/inspect_references.py','source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile','source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png','source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_composition.png']:z.write(R/name,name)
print(dest,dest.stat().st_size,'bytes')
