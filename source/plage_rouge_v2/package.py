"""Empaquetage du lot plage_rouge_v2_eoso."""
from pathlib import Path
import zipfile, sys

R = Path(__file__).resolve().parents[2]
O = R / 'renders/plage_rouge_v2_eoso'
ZIP = R / 'renders/plage_rouge_v2_eoso_pack.zip'
INCLUS = [('manifest.json', 'manifest.json'), ('README.md', 'README.md'), ('apercu.html', 'apercu.html')]
DOSSIERS = ['couches', 'canonique', 'scene', 'review', 'ora', 'exports']

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
                z.write(p, 'plage_rouge_v2_eoso/' + dst); n += 1
        z.write(R / 'source/plage_rouge_v2/references/provenance.json',
                'plage_rouge_v2_eoso/references/provenance.json'); n += 1
        for d in DOSSIERS:
            for p in sorted((O / d).rglob('*')):
                if p.is_file():
                    z.write(p, 'plage_rouge_v2_eoso/' + str(p.relative_to(O))); n += 1
    print(ZIP, f'{n} fichiers, {ZIP.stat().st_size} octets')

if __name__ == '__main__':
    pack()
