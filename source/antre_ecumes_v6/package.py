from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_ecumes_v6';dest=O/'antre_ecumes_v6.zip'
files=['apercu_antre_ecumes_v6.html','source/layouts_magenta_v1/palette.py','source/amp_plains_fleurie_v1/inspect_references.py','source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile','source/antre_harmonie_v3/references/altere_pond.rsground','renders/antre_harmonie_v3/manifest.json']
files += [f'source/antre_harmonie_v3/references/chute_native_{p}.png' for p in range(4)]
files += [f'source/antre_harmonie_v3/references/ecume_native_{p}.png' for p in range(3)]
files += [f'renders/antre_harmonie_v3/antre/harmonie_{n}.png' for n in ['02_paroi_fond','03_bordure_gauche','04_bordure_droite','05_rebord_bas']]
files += ['renders/antre_bassin_v4/bruts/bassin_quatre_poses.png','renders/antre_bassin_v4/bruts/cascades_quatre_poses_magenta.png']
files += [f'renders/antre_bassin_v4/antre/bassin4_00_bassin_regenere_{p:02}.png' for p in range(4)]
files += ['source/antre_harmonie_v3/references/Altere_Pond_River.tile','source/antre_harmonie_v3/references/Altere_Pond_River_Animations.tile']
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for name in files:z.write(R/name,name)
print(dest,dest.stat().st_size,'bytes')
