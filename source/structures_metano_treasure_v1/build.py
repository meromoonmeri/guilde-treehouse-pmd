#!/usr/bin/env python3
"""Sprites de structures style Métano Town / Treasure Town + carte village terminée.

Tous les pixels finaux proviennent des ressources canoniques des dépôts de
référence (Palikadude/Halcyon et Minemaker0430/ExplorersOfSkyOrigins), décodées
par `native.py`. Aucune texture générée, aucune recoloration, aucun
rééchantillonnage : on extrait, on détouré (suppression du sol par propagation
depuis les bords) et on réassemble. Le détourage retire uniquement les pixels de
sol connectés au bord ; les pixels des bâtiments sont conservés tels quels.

Ce n'est PAS un test moteur PMDO : collisions, warps et intégration restent à
configurer. Les terrains créés entre le 13 et le 17 septembre sont considérés
validés ; cette livraison ajoute les structures et termine la carte.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

import native

R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parent
REF = S / 'references'
O = R / 'exports' / 'structures_metano_treasure_v1'

CELL = 24  # feuilles Treasure Town / Guilde : tuiles de 24 px

# Boîtes (x0, y0, x1, y1) dans le rendu 1152x504 de treasure_town.rsground.
TREASURE_STRUCTURES = [
    ('kangaskhan_reserve', 'Réserve Kangaskhan', (112, 72, 248, 208)),
    ('kecleon_boutique', 'Boutique Kecleon', (268, 80, 396, 200)),
    ('xatu_expertise', 'Expertise Xatu', (168, 256, 296, 368)),
    ('duskull_banque', 'Banque Duskull', (936, 72, 1064, 196)),
    ('electivire_liaison', 'Liaison Élekable', (896, 256, 1056, 352)),
    ('marowak_dojo', 'Dojo Ossatueur', (704, 292, 804, 372)),
]
GUILD_BOX = (160, 50, 320, 170)


def flood_remove_ground(rgba: np.ndarray, tol: int = 30) -> np.ndarray:
    """Rend transparent le sol connecté au bord ; préserve le bâtiment."""
    a = rgba.astype(int)
    h, w = a.shape[:2]
    rgb = a[:, :, :3]
    seeds = [a[y, x, :3] for (y, x) in
             [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1),
              (0, w // 2), (h - 1, w // 2), (h // 2, 0), (h // 2, w - 1)]]
    ground = np.zeros((h, w), bool)
    for s in seeds:
        ground |= np.abs(rgb - np.array(s)).sum(2) <= tol
    border = np.zeros((h, w), bool)
    border[0, :] = border[-1, :] = True
    border[:, 0] = border[:, -1] = True
    reach = nd.binary_propagation(border & ground, structure=np.ones((3, 3)), mask=ground)
    out = rgba.copy()
    out[reach, 3] = 0
    return out


def trim_to_content(rgba: np.ndarray):
    ys, xs = np.where(rgba[:, :, 3] > 0)
    if len(xs) == 0:
        return rgba
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def pad_to_grid(rgba: np.ndarray, cell: int):
    h, w = rgba.shape[:2]
    nh, nw = ((h + cell - 1) // cell) * cell, ((w + cell - 1) // cell) * cell
    out = np.zeros((nh, nw, 4), rgba.dtype)
    out[:h, :w] = rgba
    return out


def extract_all():
    treasure = native.read_ground(REF / 'treasure_town.rsground')
    tt_sheets = native.sheets_from_tiles([REF / 'TreasureTownEast.tile', REF / 'TreasureTownWest.tile'])
    town, missing = native.render_ground(treasure, tt_sheets)
    assert not missing, missing
    town_a = np.array(town.convert('RGBA'))

    sprites = []
    for ident, label, box in TREASURE_STRUCTURES:
        cut = flood_remove_ground(town_a[box[1]:box[3], box[0]:box[2]])
        cut = pad_to_grid(trim_to_content(cut), CELL)
        sprites.append({'id': ident, 'label': label, 'style': 'Treasure Town', 'cell_px': CELL, 'rgba': cut, 'source_box': list(box)})

    g = native.read_ground(REF / 'guild_outside.rsground')
    day, m1 = native.render_ground(g, {'GuildOutside': native.read_tile(REF / 'GuildOutside.tile')}, layer_filter={0})
    night, m2 = native.render_ground(g, {'GuildOutside': native.read_tile(REF / 'GuildOutsideNight.tile')}, layer_filter={0})
    assert not m1 and not m2, (m1, m2)
    d = flood_remove_ground(np.array(day.convert('RGBA'))[GUILD_BOX[1]:GUILD_BOX[3], GUILD_BOX[0]:GUILD_BOX[2]])
    n_raw = np.array(night.convert('RGBA'))[GUILD_BOX[1]:GUILD_BOX[3], GUILD_BOX[0]:GUILD_BOX[2]]
    alpha_day = d[:, :, 3] > 0
    n = n_raw.copy()
    n[:, :, 3] = np.where(alpha_day, n_raw[:, :, 3], 0)  # géométrie identique : masque du jour
    sprites.append({'id': 'guilde_qg', 'label': 'QG de la Guilde (Wigglytuff)', 'style': 'Guilde / Treasure Town', 'cell_px': CELL, 'rgba': pad_to_grid(trim_to_content(d), CELL), 'source_box': list(GUILD_BOX), 'mode': 'jour'})
    sprites.append({'id': 'guilde_qg_nuit', 'label': 'QG de la Guilde (nuit)', 'style': 'Guilde / Treasure Town', 'cell_px': CELL, 'rgba': pad_to_grid(trim_to_content(n), CELL), 'source_box': list(GUILD_BOX), 'mode': 'nuit'})
    return sprites, town_a


def build():
    O.mkdir(parents=True, exist_ok=True)
    sprites, town_a = extract_all()

    # --- PNG individuels ---
    ind = O / 'individuels'
    ind.mkdir(parents=True, exist_ok=True)
    for s in sprites:
        Image.fromarray(s['rgba']).save(ind / f'StructureTT_{s["id"]}.png')

    # --- Atlas 24 px (grille) pour Tiled / import ---
    cols = 4
    cw = max(s['rgba'].shape[1] for s in sprites)
    ch = max(s['rgba'].shape[0] for s in sprites)
    rows = (len(sprites) + cols - 1) // cols
    atlas = np.zeros((rows * ch, cols * cw, 4), np.uint8)
    rects = {}
    for i, s in enumerate(sprites):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        atlas[cy:cy + s['rgba'].shape[0], cx:cx + s['rgba'].shape[1]] = s['rgba']
        rects[s['id']] = [cx, cy, s['rgba'].shape[1], s['rgba'].shape[0]]
    Image.fromarray(atlas).save(O / 'Structures_TreasureTown_atlas.png')

    # --- Carte village terminée : terrain natif + calque structures ---
    # Terrain reconstruit à partir de tuiles de sol natives 24 px (herbe + chemin).
    grass = town_a[216:240, 96:120]   # bloc herbe natif
    path = town_a[200:224, 432:456]   # bloc chemin de terre natif
    mw, mh = 24, 14  # cellules -> 576 x 336 px
    terrain = np.zeros((mh * CELL, mw * CELL, 4), np.uint8)
    for y in range(mh):
        for x in range(mw):
            terrain[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = path if y in (6, 7) else grass
    struct_layer = np.zeros_like(terrain)

    placements = [
        ('guilde_qg', 9, 0),
        ('kecleon_boutique', 1, 2),
        ('kangaskhan_reserve', 6, 2),
        ('duskull_banque', 16, 2),
        ('xatu_expertise', 2, 9),
        ('electivire_liaison', 15, 9),
        ('marowak_dojo', 10, 9),
    ]
    by_id = {s['id']: s for s in sprites}
    for ident, cx, cy in placements:
        spr = by_id[ident]['rgba']
        h, w = spr.shape[:2]
        px, py = cx * CELL, cy * CELL
        region = struct_layer[py:py + h, px:px + w]
        a = spr[:, :, 3:4] / 255.0
        region[:, :, :3] = (spr[:, :, :3] * a + region[:, :, :3] * (1 - a)).astype(np.uint8)
        region[:, :, 3] = np.maximum(region[:, :, 3], spr[:, :, 3])

    (O / 'map').mkdir(exist_ok=True)
    Image.fromarray(terrain).save(O / 'map/village_00_terrain.png')
    Image.fromarray(struct_layer).save(O / 'map/village_01_structures.png')

    # --- Tiled : petit tileset sol 24px + TMX (terrain en tuiles, structures en objets) ---
    groundset = np.concatenate([grass, path], axis=1)  # 24x48 -> 2 tuiles
    Image.fromarray(groundset).save(O / 'map/village_sol_2tiles.png')
    with open(O / 'map/village_sol.tsx', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<tileset version="1.10" tiledversion="1.10.2" name="village_sol" tilewidth="{CELL}" tileheight="{CELL}" tilecount="2" columns="2">\n'
                f' <image source="village_sol_2tiles.png" width="48" height="24"/>\n</tileset>\n')
    gids = []
    for y in range(mh):
        row = []
        for x in range(mw):
            row.append(2 if y in (6, 7) else 1)  # gid 1 = herbe, 2 = chemin
        gids.append(row)
    csv = ',\n'.join(','.join(map(str, r)) for r in gids)
    objs = []
    for ident, cx, cy in placements:
        s = by_id[ident]
        objs.append(f'  <object id="{len(objs)+1}" name="{ident}" x="{cx*CELL}" y="{cy*CELL}" width="{s["rgba"].shape[1]}" height="{s["rgba"].shape[0]}">\n'
                    f'   <image source="../individuels/StructureTT_{ident}.png" width="{s["rgba"].shape[1]}" height="{s["rgba"].shape[0]}"/>\n  </object>')
    with open(O / 'map/village.tmx', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<map version="1.10" orientation="orthogonal" renderorder="right-down" width="{mw}" height="{mh}" tilewidth="{CELL}" tileheight="{CELL}">\n'
                f' <tileset firstgid="1" source="village_sol.tsx"/>\n'
                f' <layer id="1" name="terrain" width="{mw}" height="{mh}">\n  <data encoding="csv">\n{csv}\n  </data>\n </layer>\n'
                f' <objectgroup id="2" name="structures">\n' + '\n'.join(objs) + '\n </objectgroup>\n</map>\n')
    comp = terrain.copy().astype(np.uint16)
    a = struct_layer[:, :, 3:4].astype(np.uint16) / 255
    comp[:, :, :3] = struct_layer[:, :, :3] * a + comp[:, :, :3] * (1 - a)
    comp[:, :, 3] = 255
    Image.fromarray(comp.astype(np.uint8)).save(O / 'map/village_composite.png')

    provenance = native.provenance()
    (O / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')

    manifest = {
        'grid_px': CELL,
        'method': 'Extraction canonique + détourage par propagation depuis les bords. Aucun pixel généré, recoloré ou rééchantillonné.',
        'terrains_13_17_septembre': 'validés par l’utilisateur ; cette livraison ajoute les structures et termine la carte village.',
        'structures': [{
            'id': s['id'], 'label': s['label'], 'style': s['style'], 'cell_px': s['cell_px'],
            'size_px': [int(s['rgba'].shape[1]), int(s['rgba'].shape[0])],
            'file': f'individuels/StructureTT_{s["id"]}.png',
            'atlas_rect_px': rects[s['id']],
        } for s in sprites],
        'atlas': 'Structures_TreasureTown_atlas.png',
        'map': {
            'size_px': [int(mw * CELL), int(mh * CELL)],
            'layers': ['map/village_00_terrain.png', 'map/village_01_structures.png'],
            'composite': 'map/village_composite.png',
            'placements': [{'id': i, 'cell': [cx, cy]} for i, cx, cy in placements],
        },
        'not_validated': ['Import PMDO réel', 'Collisions / warps / occlusion', 'Appréciation artistique'],
        'credits': 'Ressources natives © leurs auteurs (Palikadude/Halcyon, Minemaker0430/ExplorersOfSkyOrigins).',
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    _viewer(sprites, manifest)
    with zipfile.ZipFile(R / 'exports' / 'structures_metano_treasure_v1_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
    print(f'{len(sprites)} structures extraites ; carte {mw*CELL}x{mh*CELL}px ; atlas {atlas.shape[1]}x{atlas.shape[0]}px.')


def _viewer(sprites, manifest):
    import base64
    def uri(a):
        buf = __import__('io').BytesIO()
        Image.fromarray(a).save(buf, 'png')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    data = [{'id': s['id'], 'label': s['label'], 'style': s['style'],
             'uri': uri(s['rgba']), 'w': s['rgba'].shape[1], 'h': s['rgba'].shape[0]} for s in sprites]
    map_uri = uri(np.array(Image.open(O / 'map/village_composite.png')))
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Structures Métano / Treasure Town</title>
<style>body{{background:#14231e;color:#ecdfba;font:16px system-ui;max-width:1250px;margin:32px auto;padding:16px}}h1{{font-size:34px}}p{{line-height:1.6;color:#c3cfbc}}.grid{{display:flex;flex-wrap:wrap;gap:20px}}article{{background:#20362c;padding:14px;border:1px solid #41604a;border-radius:12px}}canvas{{image-rendering:pixelated;background:repeating-conic-gradient(#2a4035 0% 25%,#30493c 0% 50%) 0/16px 16px}}small{{color:#b2c9ac}}a{{color:#e1c97a}}</style>
<h1>Structures · style Métano Town / Treasure Town</h1>
<p>Sprites extraits pixel-par-pixel des feuilles canoniques <b>Treasure Town</b> et <b>Guilde</b> (tuiles 24 px), détourés par propagation depuis les bords. Aucun pixel généré. Carte village terminée ci-dessous (terrain natif + calque structures).</p>
<div class="grid" id="g"></div>
<h2>Carte village terminée</h2><canvas id="map" style="max-width:100%"></canvas>
<script>const D={json.dumps(data,ensure_ascii=False)};const MAP={json.dumps(map_uri)};
const g=document.getElementById('g');for(const s of D){{const a=document.createElement('article');a.innerHTML='<h3>'+s.label+'</h3><small>'+s.style+' · '+s.w+'×'+s.h+' px</small>';const c=document.createElement('canvas');c.width=s.w;c.height=s.h;c.style.width=s.w*2+'px';c.style.height=s.h*2+'px';const x=c.getContext('2d');const im=new Image();im.onload=()=>x.drawImage(im,0,0);im.src=s.uri;a.append(c);g.append(a)}}
const m=document.getElementById('map');const mi=new Image();mi.onload=()=>{{m.width=mi.width;m.height=mi.height;m.getContext('2d').drawImage(mi,0,0)}};mi.src=MAP;</script></html>'''
    (R / 'apercu_structures_metano_treasure_v1.html').write_text(html)


if __name__ == '__main__':
    build()
