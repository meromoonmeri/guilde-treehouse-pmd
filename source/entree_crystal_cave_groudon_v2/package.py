"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_crystal_cave_groudon_v2/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, re, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_crystal_cave_groudon_v2'
S = R / '.cache/entree_crystal_cave_groudon_v2/entree_crystal_cave_groudon'
PFX = 'ECC2'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_crystal_cave_groudon_v2.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / f'{PFX}_projet_pmdo_0812.zip',
           [(p, 'entree_crystal_cave_groudon/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, p.relative_to(O).as_posix()) for d in ('calques', 'animation', 'poses', 'review') for p in sorted((O / d).rglob('*')) if p.is_file()]
    items += [(O / f'{PFX}_grotte_cristal_groudon_calques.ora', f'{PFX}_grotte_cristal_groudon_calques.ora'),
              (O / 'manifest.json', 'manifest.json'), (O / 'README.md', 'README.md')]
    zipdir(O / f'{PFX}_calques_png_8px.zip', items)
    uri = lambda p: 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    stack = []
    for L in M['layers']:
        fs = [O / L['file']] if L['phases'] == 1 else [O / L['file'].replace('fNN', f'f{t:02d}') for t in range(L['phases'])]
        stack.append({'id': re.sub(rf'^{PFX}_\d\d_', '', Path(L['file']).stem.replace('_fNN', '')), 'ticks': L['ticks'],
                      'evt': bool(L.get('evenement')), 'frames': [uri(p) for p in fs]})
    data = {'size': M['size_px'], 'stack': stack, 'evtTicks': M['evenement']['duree_ticks']}
    out = R / 'apercu_entree_crystal_cave_groudon_v2.html'
    out.write_text((HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data)))
    for p in [O / f'{PFX}_projet_pmdo_0812.zip', O / f'{PFX}_calques_png_8px.zip', out]:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
