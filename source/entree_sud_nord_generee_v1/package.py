"""Tests -> ZIP projet PMDO + ZIP calques PNG -> aperçu autonome racine.
.venv/bin/python source/entree_sud_nord_generee_v1/package.py   (après build.py)
"""
from pathlib import Path
import base64, json, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_vapeur_sud_nord_v1'
S = R / '.cache/entree_vapeur_sud_nord_v1/entree_vapeur_sud_nord'


def zipdir(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in items:
            z.write(src, arc)


def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.entree_sud_nord_generee_v1.test_build'], cwd=R, check=True)
    M = json.loads((O / 'manifest.json').read_text())
    zipdir(O / 'ESN1_projet_pmdo_0812.zip',
           [(p, 'entree_vapeur_sud_nord/' + p.relative_to(S).as_posix()) for p in sorted(S.rglob('*')) if p.is_file()])
    items = [(p, 'calques/' + p.name) for p in sorted((O / 'calques').glob('*.png'))]
    items += [(p, 'animation/eau/' + p.name) for p in sorted((O / 'animation/eau').iterdir())]
    items += [(O / 'ESN1_entree_vapeur_calques.ora', 'ESN1_entree_vapeur_calques.ora'),
              (O / 'manifest.json', 'manifest.json'), (O / 'README.md', 'README.md'),
              (O / 'review/ESN1_scene_phase00.png', 'apercu/ESN1_scene_phase00.png'),
              (O / 'review/ESN1_collisions_marqueurs.png', 'apercu/ESN1_collisions_marqueurs.png')]
    zipdir(O / 'ESN1_calques_png_8px.zip', items)

    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    data = {
        'size': M['size_px'], 'ms': M['water']['ms_per_frame'],
        'water': [uri(O / f'animation/eau/ESN1_00_eau_f{t:02d}.png') for t in range(M['water']['frames'])],
        'layers': [{'id': Path(p).stem.replace('ESN1_', ''), 'uri': uri(O / p)} for p in M['layer_order_bottom_to_top'][1:]],
        'collisions': uri(O / 'review/ESN1_collisions_marqueurs.png'),
        'entry': M['access']['entry_px'], 'threshold': M['access']['threshold_px'],
    }
    page = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_entree_vapeur_sud_nord_v1.html').write_text(page)
    for p in [O / 'ESN1_projet_pmdo_0812.zip', O / 'ESN1_calques_png_8px.zip', R / 'apercu_entree_vapeur_sud_nord_v1.html']:
        print(p.relative_to(R), round(p.stat().st_size / 1e6, 2), 'Mo')


if __name__ == '__main__':
    main()
