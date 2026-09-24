"""ZIP de livraison."""
from pathlib import Path
import zipfile
R = Path(__file__).resolve().parents[2]
O = R / 'renders/sommet_sky_nuit_v1'
assert (O / 'verification.json').exists(), 'lancer verify.py avant'
with zipfile.ZipFile(O / 'SOMMET_SKY_NUIT_calques.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted((O / 'sommet_nuit').rglob('*')):
        if p.is_file():
            z.write(p, f'sommet_nuit/{p.relative_to(O / "sommet_nuit")}')
    for name in ('README.md', 'manifest.json', 'verification.json', 'PLANCHE_VISTA_NE_PAS_IMPORTER.png',
                 'controle_bande_prairie_jour.png'):
        z.write(O / name, name)
print('ZIP OK')
