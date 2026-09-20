"""Empaquetage du lot plage_rouge_v1 : ZIP rendu + sources reproductibles.
A executer APRES build.py et test_build.py (le ZIP s'abstient des caches)."""
from pathlib import Path
import zipfile, json, sys

R = Path(__file__).resolve().parents[2]
O = R / 'renders/plage_rouge_v1'
ZIP = R / 'renders/plage_rouge_v1_pack.zip'

INCLUS = [
    ('manifest.json', 'manifest.json'),
    ('README.md', 'README.md'),
]
DOSSIERS = ['couches', 'scene', 'sprites_pack', 'review', 'ora', 'exports', 'bruts']

def pack():
    if not (O / 'manifest.json').exists():
        sys.exit('manifest absent : lancer build.py d abord')
    if ZIP.exists():
        ZIP.unlink()
    n = 0
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, dst in INCLUS:
            p = O / src
            if p.exists():
                z.write(p, 'plage_rouge_v1/' + dst); n += 1
        for d in DOSSIERS:
            for p in sorted((O / d).rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:
                    z.write(p, 'plage_rouge_v1/' + str(p.relative_to(O))); n += 1
    print(ZIP, f'{n} fichiers, {ZIP.stat().st_size} octets')

if __name__ == '__main__':
    pack()
