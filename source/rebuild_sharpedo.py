"""Seconde scène : falaise côtière naturelle, mer et cycle de vagues adaptés à la référence."""
from pathlib import Path
from PIL import Image
import json
import math
from exterior_animation import export_variant, stars_spec, save_png
from rebuild_falaise import grade, SPECS
from export_bordures_pmd import attach_tileset

R = Path(__file__).resolve().parents[1]
S = R / 'source/sharpedo'
F = R / 'source/falaise'
OUT = R / 'sharpedo'
SIZE = (504, 384)
LAYERS = [
    ('00_ciel', 'Ciel', False),
    ('01_astres', 'Lune fixe et étoiles scintillantes', True),
    ('02_nuages', 'Nuages — six familles de formes', True),
    ('03_mer', 'Mer — profondeur et couleurs', False),
    ('04_vagues', 'Vagues — cycle de référence adapté', True),
    ('05_falaise', 'Falaise et bordures PMD, prairie et chemin', False),
    ('06_decor', 'Décor additionnel — vide', False),
]


def shared(name):
    return Image.open(F / name).convert('RGBA').resize(SIZE, Image.Resampling.NEAREST)


def build():
    terrain = Image.open(S / 'falaise_native.png').convert('RGBA')
    sea = Image.open(S / 'mer_native.png').convert('RGBA')
    waves = Image.open(S / 'vagues_native.png').convert('RGBA')
    wave_cycle = Image.open(S / 'vagues_cycle.png').convert('RGBA')
    frames = math.lcm(SIZE[0], 24, 10)
    clouds = shared('nuages_native.png')
    stars = shared('astres_nuit_native.png')
    definitions = [{'id': key, 'nom': label, 'anime': animated} for key, label, animated in LAYERS]
    rules = json.loads((S / 'regles.json').read_text(encoding='utf-8'))
    manifest = {'version': 3, 'id': 'sharpedo', 'titre': 'Falaise côtière — prairie sur la mer',
                'dimensions': list(SIZE), 'grille_px': 8, 'cellules': [63, 48], 'base_start': 5,
                'animation': {'frames': frames, 'duree_image_ms': 250, 'duree_boucle_ms': frames*250},
                'ambiances': ['jour', 'nuit'], 'calques': definitions, 'regles': rules, 'fichiers': {}}
    star_animation = stars_spec(stars, OUT)
    markers = [{'nom': 'Approche depuis l’est', 'rectangle_px': [464, 148, 40, 64]},
               {'nom': 'Point de vue sur la mer', 'rectangle_px': [172, 140, 32, 32]}]
    for mode in manifest['ambiances']:
        _, _, mul, add, saturation = SPECS[mode]
        body = [shared(f'ciel_{mode}_native.png'), stars if mode == 'nuit' else Image.new('RGBA', SIZE),
                grade(clouds, mul, add, saturation), grade(sea, mul, add, saturation),
                grade(waves, mul, add, saturation), grade(terrain, mul, add, saturation), Image.new('RGBA', SIZE)]
        cycle_path = f'animations/source_vagues_{mode}.png'
        save_png(grade(wave_cycle, mul, add, saturation), OUT / cycle_path)
        specs = {'02_nuages': {'kind': 'scroll', 'period': SIZE[0], 'prefix': 'nuages'},
                 '04_vagues': {'kind': 'frames', 'period': 10, 'prefix': 'vagues',
                               'source_atlas': cycle_path, 'source_frame_size': list(SIZE),
                               'source_columns': 5, 'reference_cycle': True}}
        if mode == 'nuit':
            specs['01_astres'] = star_animation
        manifest['fichiers'][mode] = export_variant(OUT, mode, definitions, body, specs, SIZE, frames, 5, markers)
        attach_tileset(OUT, mode, manifest['fichiers'][mode])
        print('Falaise côtière', mode, '— paroi naturelle, cycle de mer en 10 phases, nuages et étoiles', flush=True)
    (OUT / 'kit.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    build()
