"""Configuration du générateur d'images pour « Lisière fleurie V1 » (guide de composition uniquement).

Produit dans generateur/refs/ :
  01_reference_native_vast_steppe_x2.png  carte native Halcyon rendue depuis les .tile (x2 plus proche voisin)
  02_planche_modules_x3.png               modules natifs complets (canopée+tronc, rochers, touffes, galets,
                                          fleur 3 poses, corniche/couloir/sortie) sur fond neutre
  03_palette_materiaux.png                nuanciers échantillonnés par matériau, avec hex
  04_schema_<variante>.png                schéma de layout à respecter (aplats codés, pas une texture)
et generateur/config.json (hex par matériau, consignes et prompts par variante).

Les sorties du générateur ne sont JAMAIS livrées comme pixels de carte : elles guident seulement
la position des masses (forêt, prairie, corniche, fleurs, rochers) avant l'assemblage natif.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from modules import REF, T, build_modules, load_sheets  # noqa: E402

OUT = HERE / 'refs'


def top_colors(pixels, n=8):
    p = pixels.astype(np.int64)
    k = p[:, 0] * 65536 + p[:, 1] * 256 + p[:, 2]
    u, c = np.unique(k, return_counts=True)
    order = np.argsort(-c)[:n]
    total = c.sum()
    return [{'hex': f'#{int(u[i]):06x}', 'part': round(float(c[i] / total), 4)} for i in order]


def module_pixels(sheets, m):
    a = sheets[m.sheet][m.sy:m.sy + m.h, m.sx:m.sx + m.w]
    return a[m.mask & (a[..., 3] > 0)][:, :3]


def palettes(sheets, mods):
    cl = sheets['Vast_Steppe_Cliifs']
    band = cl[208:280][cl[208:280, :, 3] > 0][:, :3]
    glow = cl[0:120, 216:296][cl[0:120, 216:296, 3] > 0][:, :3]
    fl = sheets['Vast_Steppe_Flower_Animations']
    return {
        'herbe_prairie': top_colors(sheets['Vast_Steppe_Base'][..., :3].reshape(-1, 3)),
        'canopee_foret': top_colors(module_pixels(sheets, mods['canopee'])),
        'tronc_et_ombre_herbe': top_colors(module_pixels(sheets, mods['tronc'])),
        'corniche_roche': top_colors(band),
        'sortie_lumineuse': top_colors(glow),
        'fleurs': top_colors(fl[fl[..., 3] > 0][:, :3]),
        'rochers_galets': top_colors(np.concatenate([module_pixels(sheets, mods[k]) for k in
                                                     ('rocher_a', 'rocher_b', 'galet_a', 'galet_b')])),
        'touffes': top_colors(np.concatenate([module_pixels(sheets, mods[k]) for k in ('touffe_a', 'touffe_b')])),
    }


def native_render():
    bank = T.SheetBank()
    bank.add_dir(REF)
    img, _ = T.render_ground(T.load_ground(REF / 'vast_steppe_entrance.rsground'), bank)
    return Image.fromarray(img)


def modules_board(sheets, mods):
    bg = (200, 196, 176, 255)
    board = Image.new('RGBA', (420, 230), bg)
    def paste(name, x, y):
        m = mods[name]
        a = sheets[m.sheet][m.sy:m.sy + m.h, m.sx:m.sx + m.w].copy()
        a[~m.mask] = 0
        board.alpha_composite(Image.fromarray(a), (x, y))
    # arbre complet = canopée + tronc au décalage natif
    paste('tronc', 8 + 24, 8 + 48)
    paste('canopee', 8, 8)
    paste('rocher_a', 150, 12); paste('rocher_b', 200, 12)
    paste('touffe_a', 150, 60); paste('touffe_b', 184, 60)
    paste('galet_a', 218, 60); paste('galet_b', 252, 60)
    fl = sheets['Vast_Steppe_Flower_Animations']
    for p in range(3):
        board.alpha_composite(Image.fromarray(fl[:, p * 24:(p + 1) * 24]), (150 + p * 30, 90))
    cl = sheets['Vast_Steppe_Cliifs']
    cor = Image.fromarray(cl[0:280, 120:392]).resize((136, 140), Image.NEAREST)
    board.alpha_composite(cor, (280, 84))
    return board.resize((board.width * 3, board.height * 3), Image.NEAREST)


def palette_board(pal):
    rows = list(pal.items())
    im = Image.new('RGB', (8 * 90 + 200, len(rows) * 46 + 10), (30, 30, 30))
    d = ImageDraw.Draw(im)
    for r, (name, cols) in enumerate(rows):
        y = 8 + r * 46
        d.text((6, y + 14), name, fill=(240, 240, 240))
        for i, c in enumerate(cols):
            x = 200 + i * 90
            d.rectangle([x, y, x + 84, y + 28], fill=c['hex'])
            d.text((x + 2, y + 30), c['hex'], fill=(230, 230, 230))
    return im


# Schémas : aplats codés de la composition demandée (géométrie seulement).
SCHEMA_COLORS = {'foret': (34, 92, 40), 'prairie': (127, 199, 95), 'corniche': (150, 110, 60),
                 'sortie': (222, 230, 150), 'fleurs': (236, 120, 220), 'arrivee': (250, 250, 250)}

VARIANTS = {
    'legere': {
        'size': [768, 896],
        'description': 'Variante légère : proche de l’esprit de l’entrée native (corniche + couloir au nord), '
                       'mais lisière ouest continue et ondulante, anse fleurie, bosquet est, arrivée au sud.',
        'forest': [[(0, 0), (240, 0), (232, 200), (0, 200)],
                   [(500, 0), (768, 0), (768, 200), (500, 200)],
                   [(0, 280), (250, 300), (300, 460), (250, 560), (120, 600), (80, 760), (330, 896), (0, 896)],
                   [(620, 280), (768, 280), (768, 440), (640, 430)],
                   [(560, 896), (768, 700), (768, 896)]],
        'ledge_y': 208, 'passage_x': 312, 'passage_w': 144,
        'flowers': [(130, 700, 60), (380, 540, 40), (360, 320, 30), (440, 820, 36), (560, 430, 30)],
        'arrival_x': 456,
    },
    'spacieuse': {
        'size': [816, 1152],
        'description': 'Variante spacieuse : prairie beaucoup plus ouverte, lisière ouest plus mince et '
                       'échancrée, quelques arbres isolés, grands massifs de fleurs, corniche au nord.',
        'forest': [[(0, 0), (240, 0), (232, 200), (0, 200)],
                   [(520, 0), (816, 0), (816, 200), (520, 200)],
                   [(0, 280), (170, 300), (200, 460), (120, 620), (60, 700), (60, 880), (230, 1000),
                    (300, 1152), (0, 1152)],
                   [(700, 280), (816, 280), (816, 420), (720, 410)],
                   [(640, 1152), (816, 980), (816, 1152)]],
        'ledge_y': 208, 'passage_x': 312, 'passage_w': 144,
        'flowers': [(140, 780, 70), (420, 560, 60), (560, 760, 50), (360, 330, 30), (470, 1060, 50),
                    (650, 520, 40)],
        'arrival_x': 470,
    },
}


def schema(v):
    W, H = v['size']
    im = Image.new('RGB', (W, H), SCHEMA_COLORS['prairie'])
    d = ImageDraw.Draw(im)
    for poly in v['forest']:
        d.polygon(poly, fill=SCHEMA_COLORS['foret'])
    y = v['ledge_y']
    d.rectangle([0, y, W, y + 72], fill=SCHEMA_COLORS['corniche'])
    px, pw = v['passage_x'], v['passage_w']
    d.rectangle([px, y, px + pw, y + 72], fill=SCHEMA_COLORS['prairie'])
    d.rectangle([px + 24, 0, px + pw - 24, 140], fill=SCHEMA_COLORS['sortie'])
    for fx, fy, r in v['flowers']:
        d.ellipse([fx - r, fy - r * 0.7, fx + r, fy + r * 0.7], outline=SCHEMA_COLORS['fleurs'], width=6)
    ax = v['arrival_x']
    d.polygon([(ax - 24, H - 4), (ax + 24, H - 4), (ax, H - 44)], fill=SCHEMA_COLORS['arrivee'])
    return im


PROMPT = (
    'Top-down 3/4 view game map in the exact pixel-art style of Pokemon Mystery Dungeon Explorers of Sky '
    'ground maps, same art as the Halcyon "Vast Steppe" reference image. Follow the colour-block layout sketch '
    'EXACTLY for geometry: dark green = dense forest of round bushy trees (each tree = the reference canopy '
    'with its brown trunk and dark grass shade), light green = open grass meadow, brown band = rocky ledge '
    'crossing the whole width with ONE gap, pale yellow = bright exit glow at the top edge reached by a rocky '
    'corridor, pink ellipses = drifts of small pink flower clumps, white triangle = arrival from the bottom edge. '
    'Use ONLY these materials and colours: {hex}. No path, no water, no buildings, no characters, no text, '
    'no UI, no border frame. Crisp pixels, flat readable shapes, trees may overlap into a continuous forest edge. '
    '{variant}'
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sheets = load_sheets()
    mods = build_modules(sheets)
    nat = native_render()
    nat.resize((1024, 1024), Image.NEAREST).save(OUT / '01_reference_native_vast_steppe_x2.png')
    modules_board(sheets, mods).save(OUT / '02_planche_modules_x3.png')
    pal = palettes(sheets, mods)
    palette_board(pal).save(OUT / '03_palette_materiaux.png')
    hexes = ', '.join(f"{k.replace('_', ' ')} {' '.join(c['hex'] for c in v[:4])}" for k, v in pal.items())
    cfg = {'role': 'guide de composition uniquement ; aucun pixel généré livré',
           'references': ['refs/01_reference_native_vast_steppe_x2.png', 'refs/02_planche_modules_x3.png',
                          'refs/03_palette_materiaux.png'],
           'palette_echantillonnee': pal, 'schema_colors': SCHEMA_COLORS, 'variants': {}}
    for name, v in VARIANTS.items():
        schema(v).save(OUT / f'04_schema_{name}.png')
        cfg['variants'][name] = {k: v[k] for k in ('size', 'description', 'ledge_y', 'passage_x',
                                                    'passage_w', 'arrival_x')}
        cfg['variants'][name]['schema'] = f'refs/04_schema_{name}.png'
        cfg['variants'][name]['prompt'] = PROMPT.format(hex=hexes, variant=v['description'])
    (HERE / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
    print(json.dumps({k: [c['hex'] for c in v[:4]] for k, v in pal.items()}, indent=1))


if __name__ == '__main__':
    main()
