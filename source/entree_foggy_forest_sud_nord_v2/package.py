"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_foggy_forest_sud_nord_v2/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, re, subprocess, sys, zipfile

from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_foggy_forest_sud_nord_v2'
S = R / '.cache/entree_foggy_forest_sud_nord_v2/entree_foggy_forest_sans_tentes'
PFX = 'EFF2'
ANIMS = ['eau', 'scintillements', 'brume']
REVIEW = ['scene_t000.png', 'scene_animee.webp', 'collisions_marqueurs.png', 'planche_poses.png']


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_foggy_forest_sud_nord_v2.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / f'{PFX}_projet_pmdo_0812.zip',
           [(p, 'entree_foggy_forest_sans_tentes/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ANIMS:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'poses/' + p.name) for p in sorted((O / 'poses').glob('*.png'))]
    items += [(p, 'masques/' + p.name) for p in sorted((O / 'masques').glob('*.png'))]
    items += [(O / f'{PFX}_entree_foggy_forest_sans_tentes_calques.ora', f'{PFX}_entree_foggy_forest_sans_tentes_calques.ora'),
              (O / 'manifest.json', 'manifest.json'), (O / 'README.md', 'README.md')]
    items += [(O / 'review' / f'{PFX}_{n}', f'apercu/{PFX}_{n}') for n in REVIEW]
    zipdir(O / f'{PFX}_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    stack = []
    for L in M['layers']:
        name = re.sub(rf'^{PFX}_\d\d_', '', Path(L['file']).stem.replace('_fNN', ''))
        frames = [O / L['file']] if L['phases'] == 1 else [O / L['file'].replace('fNN', f'f{t:02d}') for t in range(L['phases'])]
        stack.append({'id': name, 'ticks': L['ticks'], 'frames': [uri(p) for p in frames]})
    poses = []
    for kind, n in (('brume', 8),):
        for i in range(n):
            p = O / f'poses/{PFX}_{kind}_{i}.png'; w, h = Image.open(p).size
            poses.append({'id': f'{kind} {i}', 'uri': uri(p), 'w': w, 'h': h})
    data = {'size': M['size_px'], 'loop': M['scene_loop_ticks'], 'stack': stack, 'surface': 'rgb(90,150,100)', 'poses': poses,
            'collisions': uri(O / f'review/{PFX}_collisions_marqueurs.png'),
            'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px']}
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_foggy_forest_sud_nord_v2.html').write_text(page)
    for p in [O / f'{PFX}_projet_pmdo_0812.zip', O / f'{PFX}_calques_png_8px.zip', R / 'apercu_entree_foggy_forest_sud_nord_v2.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
