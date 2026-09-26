"""Vérifie puis produit les archives PMDO/PNG et l’aperçu autonome.
Lancer après build.py : .venv/bin/python source/entree_grotte_cascade_sud_nord_v1/package.py
"""
from pathlib import Path
import base64
import json
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'renders/entree_grotte_cascade_sud_nord_v1'
STAGE = ROOT / '.cache/entree_grotte_cascade_sud_nord_v1/entree_grotte_cascade_sud_nord'
PREFIX = 'EGC1'


def zip_files(path, items):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, dest in items:
            archive.write(source, dest)


def data_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(Path(path).read_bytes()).decode('ascii')


def main():
    subprocess.run([sys.executable, '-m', 'unittest',
                    'source.entree_grotte_cascade_sud_nord_v1.test_build', '-v'],
                   cwd=ROOT, check=True)
    manifest = json.loads((OUT / 'manifest.json').read_text())
    render_readme = OUT / 'README.md'
    if not render_readme.exists():
        render_readme.write_text((HERE / 'README_PACK.md').read_text())
    stage_files = [(p, 'entree_grotte_cascade_sud_nord/' + p.relative_to(STAGE).as_posix())
                   for p in sorted(STAGE.rglob('*')) if p.is_file()]
    project_zip = OUT / 'EGC1_projet_pmdo_0812.zip'
    zip_files(project_zip, stage_files)

    png_items = []
    png_items += [(p, 'calques/' + p.name) for p in sorted((OUT / 'calques').glob('*.png'))]
    png_items += [(p, 'animation/eau/' + p.name)
                  for p in sorted((OUT / 'animation/eau').glob('*.png'))]
    png_items += [(OUT / f'{PREFIX}_entree_grotte_cascade_calques.ora',
                   f'{PREFIX}_entree_grotte_cascade_calques.ora')]
    for filename in ['manifest.json', 'README.md']:
        png_items.append((OUT / filename, filename))
    for filename in [f'{PREFIX}_scene_phase00.png', f'{PREFIX}_scene_x2.png',
                     f'{PREFIX}_scene_animee.webp', f'{PREFIX}_collisions_marqueurs.png',
                     f'{PREFIX}_viewport_arrivee.png']:
        png_items.append((OUT / 'review' / filename, 'apercu/' + filename))
    png_zip = OUT / 'EGC1_calques_png_8px.zip'
    zip_files(png_zip, png_items)

    def layer_uri(layer_name):
        return data_uri(OUT / 'calques' / f'{PREFIX}_{layer_name}.png')
    water_paths = [OUT / 'animation/eau' / f'{PREFIX}_01_eau_caverne_f{i:02d}.png'
                   for i in range(manifest['water']['cycle_frames'])]
    stack = [
        {'id': '00 Sol complet', 'ticks': 60, 'frames': [layer_uri('00_sol_complet')]},
        {'id': '01 Eau caverne — palette-cycling', 'ticks': manifest['water']['frame_length_ticks'],
         'frames': [data_uri(p) for p in water_paths]},
        {'id': '02 Parois rocheuses', 'ticks': 60, 'frames': [layer_uri('02_parois_rocheuses')]},
        {'id': '03 Chemin sud → nord', 'ticks': 60, 'frames': [layer_uri('03_chemin')]},
        {'id': '04 Voûte et seuil nord', 'ticks': 60, 'frames': [layer_uri('04_voute_et_seuil_nord')]},
    ]
    data = {'size': manifest['size_px'], 'loop': manifest['scene_loop_ticks'], 'stack': stack,
            'collisions': data_uri(OUT / 'review' / f'{PREFIX}_collisions_marqueurs.png'),
            'entry': manifest['access']['entry_px'], 'threshold': manifest['access']['threshold_px'],
            'waterTicks': manifest['water']['frame_length_ticks'],
            'waterFrames': manifest['water']['cycle_frames']}
    html = (HERE / 'viewer_template.html').read_text().replace('__DATA__', json.dumps(data, ensure_ascii=False))
    (ROOT / 'apercu_entree_grotte_cascade_sud_nord_v1.html').write_text(html)
    for path in [project_zip, png_zip, ROOT / 'apercu_entree_grotte_cascade_sud_nord_v1.html']:
        print(f'{path.relative_to(ROOT)}: {path.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
