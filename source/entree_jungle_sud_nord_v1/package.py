"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_jungle_sud_nord_v1/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_jungle_sud_nord_v1'
S = R / '.cache/entree_jungle_sud_nord_v1/entree_jungle_sud_nord'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_jungle_sud_nord_v1.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'EJN1_projet_pmdo_0812.zip',
           [(p, 'entree_jungle_sud_nord/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ['eau', 'scintillements', 'papillons']:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'poses_papillons/' + p.name) for p in sorted((O / 'poses_papillons').glob('*.png'))]
    items += [(O / 'EJN1_entree_jungle_calques.ora', 'EJN1_entree_jungle_calques.ora'), (O / 'manifest.json', 'manifest.json'),
              (O / 'README.md', 'README.md'), (O / 'review/EJN1_scene_t000.png', 'apercu/EJN1_scene_t000.png'),
              (O / 'review/EJN1_scene_animee.webp', 'apercu/EJN1_scene_animee.webp'),
              (O / 'review/EJN1_collisions_marqueurs.png', 'apercu/EJN1_collisions_marqueurs.png')]
    zipdir(O / 'EJN1_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    counts = {'eau': M['water']['phases'], 'scintillements': M['water']['phases'], 'papillons': M['butterflies']['phases']}
    ticks = {'eau': 10, 'scintillements': 10, 'papillons': M['butterflies']['frame_length_ticks']}
    stack = []
    for p in M['layer_order_bottom_to_top']:
        kind = p.split('/')[1] if p.startswith('animation/') else None
        if kind:
            fmt = (lambda t: p.replace('fXX', f'f{t:02d}')) if 'fXX' in p else (lambda t: p.replace('fX', f'f{t}'))
            stack.append({'id': Path(p).stem.replace('EJN1_', '').rsplit('_f', 1)[0], 'ticks': ticks[kind],
                          'frames': [uri(O / fmt(t)) for t in range(counts[kind])]})
        else:
            stack.append({'id': Path(p).stem.replace('EJN1_', ''), 'ticks': 60, 'frames': [uri(O / p)]})
    data = {'size': M['size_px'], 'loop': M['scene_loop_ticks'], 'stack': stack,
            'surface': 'rgb(48,136,64)',
            'poses': [{'id': f'{c} {i}', 'uri': uri(O / f'poses_papillons/EJN1_papillon_{c}_{i}.png')} for c in ('jaune', 'bleu') for i in range(6)],
            'collisions': uri(O / 'review/EJN1_collisions_marqueurs.png'),
            'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px']}
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_jungle_sud_nord_v1.html').write_text(page)
    for p in [O / 'EJN1_projet_pmdo_0812.zip', O / 'EJN1_calques_png_8px.zip', R / 'apercu_entree_jungle_sud_nord_v1.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
