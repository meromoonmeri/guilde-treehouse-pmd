"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_cascade_sud_nord_v1/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_cascade_sud_nord_v1'
S = R / '.cache/entree_cascade_sud_nord_v1/entree_cascade_sud_nord'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_cascade_sud_nord_v1.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'ECN1_projet_pmdo_0812.zip',
           [(p, 'entree_cascade_sud_nord/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ['cascade', 'scintillements']:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'masques/' + p.name) for p in sorted((O / 'masques').glob('*.png'))]
    items += [(p, 'provenance/' + p.name) for p in sorted((O / 'provenance').glob('*.npz'))]
    items += [(O / 'ECN1_entree_cascade_calques.ora', 'ECN1_entree_cascade_calques.ora'), (O / 'manifest.json', 'manifest.json'),
              (O / 'README.md', 'README.md'), (O / 'review/ECN1_scene_t000.png', 'apercu/ECN1_scene_t000.png'),
              (O / 'review/ECN1_scene_animee.webp', 'apercu/ECN1_scene_animee.webp'),
              (O / 'review/ECN1_collisions_marqueurs.png', 'apercu/ECN1_collisions_marqueurs.png'),
              (O / 'review/ECN1_sources_cadres.png', 'apercu/ECN1_sources_cadres.png')]
    zipdir(O / 'ECN1_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    stack = []
    for p in M['layer_order_bottom_to_top']:
        if p.startswith('animation/'):
            stack.append({'id': Path(p).stem.replace('ECN1_', '').rsplit('_f', 1)[0], 'ticks': M['cascade']['frame_length_ticks'],
                          'frames': [uri(O / p.replace('fX', f'f{t}')) for t in range(M['cascade']['phases'])]})
        else:
            stack.append({'id': Path(p).stem.replace('ECN1_', ''), 'ticks': 60, 'frames': [uri(O / p)]})
    data = {'size': M['size_px'], 'loop': M['scene_loop_ticks'], 'stack': stack,
            'sources': uri(O / 'review/ECN1_sources_cadres.png'),
            'collisions': uri(O / 'review/ECN1_collisions_marqueurs.png'),
            'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px']}
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_cascade_sud_nord_v1.html').write_text(page)
    for p in [O / 'ECN1_projet_pmdo_0812.zip', O / 'ECN1_calques_png_8px.zip', R / 'apercu_entree_cascade_sud_nord_v1.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
