"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_cascade_sud_nord_v2/package.py   (après build.py)
"""
from pathlib import Path
import base64, io, json, subprocess, sys, zipfile

from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_cascade_sud_nord_v2'
S = R / '.cache/entree_cascade_sud_nord_v2/entree_cascade_sud_nord_v2'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_cascade_sud_nord_v2.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'ECN2_projet_pmdo_0812.zip',
           [(p, 'entree_cascade_sud_nord_v2/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ['eau', 'cascade', 'scintillements']:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'masques/' + p.name) for p in sorted((O / 'masques').glob('*.png'))]
    items += [(O / 'ECN2_entree_cascade_calques.ora', 'ECN2_entree_cascade_calques.ora'), (O / 'manifest.json', 'manifest.json'),
              (O / 'README.md', 'README.md'), (O / 'review/ECN2_scene_t000.png', 'apercu/ECN2_scene_t000.png'),
              (O / 'review/ECN2_scene_animee.webp', 'apercu/ECN2_scene_animee.webp'),
              (O / 'review/ECN2_collisions_marqueurs.png', 'apercu/ECN2_collisions_marqueurs.png')]
    zipdir(O / 'ECN2_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    stack = []
    for p in M['layer_order_bottom_to_top']:
        if p.startswith('animation/'):
            stack.append({'id': Path(p).stem.replace('ECN2_', '').rsplit('_f', 1)[0], 'ticks': M['water']['frame_length_ticks'],
                          'frames': [uri(O / p.replace('fX', f'f{t}')) for t in range(M['water']['phases'])]})
        else:
            stack.append({'id': Path(p).stem.replace('ECN2_', ''), 'ticks': 60, 'frames': [uri(O / p)]})
    brut = Image.open(HERE / 'bruts/decor_magenta.png').convert('RGB'); brut.thumbnail((600, 448)); buf = io.BytesIO(); brut.save(buf, 'PNG')
    data = {'size': M['size_px'], 'loop': M['scene_loop_ticks'], 'stack': stack,
            'brut': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(),
            'collisions': uri(O / 'review/ECN2_collisions_marqueurs.png'),
            'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px']}
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_cascade_sud_nord_v2.html').write_text(page)
    for p in [O / 'ECN2_projet_pmdo_0812.zip', O / 'ECN2_calques_png_8px.zip', R / 'apercu_entree_cascade_sud_nord_v2.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
