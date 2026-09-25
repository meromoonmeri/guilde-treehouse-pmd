"""ZIPs V17 : pack complet + pack plat PNG to Tileset 8px."""
from pathlib import Path
import zipfile

R = Path(__file__).resolve().parents[2]
O = R / 'renders/glace_aurore_canonique_v1'

def main():
    z1 = R / 'renders/glace_aurore_canonique_v1_pack.zip'
    with zipfile.ZipFile(z1, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, 'glace_aurore_canonique_v1/' + str(p.relative_to(O)))
        z.write(R / 'apercu_glace_aurore_canonique_v1.html',
                'glace_aurore_canonique_v1/apercu_glace_aurore_canonique_v1.html')
    z2 = R / 'GLACE_V17_png_import_8px.zip'
    with zipfile.ZipFile(z2, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('GLACE_V17_*.png')) + sorted(O.rglob('GLACE_V17_*.tsx')):
            z.write(p, p.name)  # noms deja uniques (map incluse)
        z.write(O / 'README.md', 'LISEZMOI_IMPORT.txt')
    print(z1.name, z1.stat().st_size, '|', z2.name, z2.stat().st_size)

if __name__ == '__main__':
    main()
