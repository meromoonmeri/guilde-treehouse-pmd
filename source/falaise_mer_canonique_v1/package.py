"""ZIP de livraison: scene, calques, ORA, animation, manifeste, controles, doc."""
from pathlib import Path
import zipfile
R = Path(__file__).resolve().parents[2]
O = R / 'renders/falaise_mer_canonique_v1'
assert (O / 'verification.json').exists(), 'lancer verify.py avant le package'
with zipfile.ZipFile(O / 'CAP_CANONIQUE_FACE_MER_calques.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted((O / 'cap_cascade').glob('*')):
        z.write(p, f'cap_cascade/{p.name}')
    for name in ('README.md', 'manifest.json', 'verification.json', 'PLANCHE_COUPES_2X_NE_PAS_IMPORTER.png'):
        z.write(O / name, name)
print('ZIP OK')
