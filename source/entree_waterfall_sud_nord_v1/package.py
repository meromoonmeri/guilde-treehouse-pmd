"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_waterfall_sud_nord_v1/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_waterfall_sud_nord_v1'
S = R / '.cache/entree_waterfall_sud_nord_v1/entree_waterfall_sud_nord'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_waterfall_sud_nord_v1.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'EWN1_projet_pmdo_0812.zip',
           [(p, 'entree_waterfall_sud_nord/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ['eau', 'scintillements']:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'poses_scintillements/' + p.name) for p in sorted((O / 'poses_scintillements').glob('*.png'))]
    items += [(O / 'EWN1_entree_waterfall_calques.ora', 'EWN1_entree_waterfall_calques.ora'), (O / 'manifest.json', 'manifest.json'),
              (O / 'README.md', 'README.md'), (O / 'review/EWN1_scene_t000.png', 'apercu/EWN1_scene_t000.png'),
              (O / 'review/EWN1_scene_animee.webp', 'apercu/EWN1_scene_animee.webp'),
              (O / 'review/EWN1_collisions_marqueurs.png', 'apercu/EWN1_collisions_marqueurs.png')]
    zipdir(O / 'EWN1_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    counts = {'eau': M['water']['phases'], 'scintillements': M['scintillements']['phases']}
    ticks = {'eau': M['water']['frame_length_ticks'], 'scintillements': M['scintillements']['frame_length_ticks']}
    stack = []
    for p in M['layer_order_bottom_to_top']:
        kind = p.split('/')[1] if p.startswith('animation/') else None
        if kind:
            n = counts[kind]
            fmt = (lambda t, p=p: p.replace('fXX', f'f{t:02d}')) if 'fXX' in p else (lambda t, p=p: p.replace('fX', f'f{t}'))
            stack.append({'id': Path(p).stem.replace('EWN1_', '').rsplit('_f', 1)[0], 'ticks': ticks[kind],
                          'frames': [uri(O / fmt(t)) for t in range(n)]})
        else:
            stack.append({'id': Path(p).stem.replace('EWN1_', ''), 'ticks': 60, 'frames': [uri(O / p)]})
    gm = M['canonique']['decor_roche_moyenne']
    data = {'size': M['size_px'], 'loop': M['scene_loop_ticks'], 'stack': stack,
            'surface': 'rgb(%d,%d,%d)' % (gm[0], gm[1], gm[2]),
            'poses': [{'id': f'scintillement {i}', 'uri': uri(O / f'poses_scintillements/EWN1_scintillement_{i}.png')} for i in range(8)],
            'collisions': uri(O / 'review/EWN1_collisions_marqueurs.png'),
            'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px']}
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_waterfall_sud_nord_v1.html').write_text(page)
    for p in [O / 'EWN1_projet_pmdo_0812.zip', O / 'EWN1_calques_png_8px.zip', R / 'apercu_entree_waterfall_sud_nord_v1.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
