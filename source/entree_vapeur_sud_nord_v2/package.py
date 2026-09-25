"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine (V2).
.venv/bin/python source/entree_vapeur_sud_nord_v2/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_vapeur_sud_nord_v2'
S = R / '.cache/entree_vapeur_sud_nord_v2/entree_vapeur_sud_nord_v2'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_vapeur_sud_nord_v2.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'ESN2_projet_pmdo_0812.zip',
           [(p, 'entree_vapeur_sud_nord_v2/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    for sub in ['eau', 'scintillements', 'bulles']:
        items += [(p, f'animation/{sub}/' + p.name) for p in sorted((O / 'animation' / sub).glob('*.png'))]
    items += [(p, 'poses_bulles/' + p.name) for p in sorted((O / 'poses_bulles').glob('*.png'))]
    items += [(O / 'ESN2_entree_vapeur_calques.ora', 'ESN2_entree_vapeur_calques.ora'),
              (O / 'manifest.json', 'manifest.json'), (O / 'README.md', 'README.md'),
              (O / 'review/ESN2_scene_t000.png', 'apercu/ESN2_scene_t000.png'),
              (O / 'review/ESN2_scene_animee.webp', 'apercu/ESN2_scene_animee.webp'),
              (O / 'review/ESN2_collisions_marqueurs.png', 'apercu/ESN2_collisions_marqueurs.png')]
    zipdir(O / 'ESN2_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    data = {
        'size': M['size_px'], 'waterTicks': M['water']['frame_length_ticks'], 'bubbleTicks': M['bubbles']['frame_length_ticks'],
        'loop': M['scene_loop_ticks'], 'surface': 'rgb(%d,%d,%d)' % tuple(M['water']['couleurs']['surface']),
        'water': [uri(O / f'animation/eau/ESN2_00_eau_metano_f{t}.png') for t in range(M['water']['phases'])],
        'sparks': [uri(O / f'animation/scintillements/ESN2_01_scintillements_f{t}.png') for t in range(M['water']['phases'])],
        'bubbles': [uri(O / f'animation/bulles/ESN2_02_bulles_f{t:02d}.png') for t in range(M['bubbles']['phases'])],
        'layers': [{'id': Path(p).stem.replace('ESN2_', ''), 'uri': uri(O / p)} for p in M['layer_order_bottom_to_top'][3:]],
        'poses': [{'id': k, 'uri': uri(O / f'poses_bulles/ESN2_bulle_{k}.png')} for k in M['bubbles']['poses']],
        'collisions': uri(O / 'review/ESN2_collisions_marqueurs.png'),
        'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px'],
    }
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_vapeur_sud_nord_v2.html').write_text(page)
    for p in [O / 'ESN2_projet_pmdo_0812.zip', O / 'ESN2_calques_png_8px.zip', R / 'apercu_entree_vapeur_sud_nord_v2.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
