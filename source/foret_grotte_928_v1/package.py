from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2]
O=R/'exports/foret_grotte_928_v1/forest_cave_928'
Z=R/'foret_grotte_928_v1_pack.zip'
files=list(O.glob('Foret928*.png'))+list(O.glob('Foret928*.tsx'))+list(O.glob('*_source.npz'))+list(O.glob('composite*.png'))+list(O.glob('path*.png'))+list(O.glob('access*.png'))
files+= [R/'exports/foret_grotte_928_v1/manifest.json', R/'exports/foret_grotte_928_v1/manifest_nuit.json', R/'exports/foret_grotte_928_v1/README.md']
# add viewer snippet
files.append(R/'apercu_foret_grotte_928_v1.html')
with zipfile.ZipFile(Z,'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in files:
        if f.exists():
            # keep relative path
            try:
                arc=f.relative_to(R)
            except:
                arc=f.name
            z.write(f, arc)
print(f'ZIP {Z} — {len(files)} files, {Z.stat().st_size/1024:.0f} KB')
import subprocess, sys
subprocess.run([sys.executable, str(R/'source/foret_grotte_928_v1/verify.py')], check=True)
