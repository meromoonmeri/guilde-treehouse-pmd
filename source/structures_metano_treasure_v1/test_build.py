#!/usr/bin/env python3
"""Tests du lot structures_metano_treasure_v1.

Vérifie, par re-extraction indépendante, que chaque sprite livré est constitué
uniquement de pixels canoniques (identiques au rendu de la map de référence),
que la géométrie nuit == géométrie jour, que l'atlas et la carte sont alignés sur
la grille 24 px et recomposables, et que les fichiers de référence sont intacts
(hash identiques à provenance.json).
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import native

R = Path(__file__).resolve().parents[2]
O = R / 'exports' / 'structures_metano_treasure_v1'
CELL = 24


def main():
    failures = []
    sprites, town_a = build.extract_all()
    by_id = {s['id']: s for s in sprites}
    manifest = json.loads((O / 'manifest.json').read_text())
    prov = json.loads((O / 'provenance.json').read_text())

    # 1. Références intactes : hash = provenance.json
    for name, meta in prov.items():
        p = native.REF / name
        if native.sha256(p) != meta['sha256']:
            failures.append(f'reférence modifiée {name}')

    # 2. Sprites : pixels canoniques + alpha + grille
    for s in sprites:
        png = np.array(Image.open(O / 'individuels' / f'StructureTT_{s["id"]}.png').convert('RGBA'))
        src = s['rgba']
        if png.shape != src.shape or not np.array_equal(png, src):
            failures.append(f'{s["id"]} PNG != re-extraction')
        if png.shape[0] % CELL or png.shape[1] % CELL:
            failures.append(f'{s["id"]} non aligné 24px')
        if (png[:, :, 3] > 0).sum() == 0:
            failures.append(f'{s["id"]} vide')
        # Pixels opaques identiques au rendu source (canonique)
        m = by_id[s['id']]['rgba']
        if not np.array_equal(png, m):
            failures.append(f'{s["id"]} pixels non canoniques')

    # 3. Nuit == géométrie jour
    d = np.array(Image.open(O / 'individuels/StructureTT_guilde_qg.png'))
    n = np.array(Image.open(O / 'individuels/StructureTT_guilde_qg_nuit.png'))
    if not np.array_equal(d[:, :, 3] > 0, n[:, :, 3] > 0):
        failures.append('guilde nuit géométrie != jour')

    # 4. Atlas : contient chaque sprite à son rectangle
    atlas = np.array(Image.open(O / 'Structures_TreasureTown_atlas.png').convert('RGBA'))
    if atlas.shape[0] % CELL or atlas.shape[1] % CELL:
        failures.append('atlas non aligné 24px')
    for s in manifest['structures']:
        x, y, w, h = s['atlas_rect_px']
        sub = atlas[y:y + h, x:x + w]
        png = np.array(Image.open(O / s['file']).convert('RGBA'))
        if not np.array_equal(sub, png):
            failures.append(f'atlas rectangle != {s["id"]}')

    # 5. Carte : dims, recomposition, TMX/TSX
    ter = np.array(Image.open(O / 'map/village_00_terrain.png').convert('RGBA'))
    st = np.array(Image.open(O / 'map/village_01_structures.png').convert('RGBA'))
    comp = np.array(Image.open(O / 'map/village_composite.png').convert('RGBA'))
    for a in (ter, st, comp):
        if a.shape[0] % CELL or a.shape[1] % CELL:
            failures.append('carte non alignée 24px')
    a = st[:, :, 3:4].astype(np.uint16) / 255
    rec = np.dstack([(st[:, :, :3] * a + ter[:, :, :3] * (1 - a)).astype(np.uint8), np.full(st.shape[:2], 255, np.uint8)])
    if not np.array_equal(rec, comp):
        failures.append('composite != terrain+structures')

    mw, mh = manifest['map']['size_px'][0] // CELL, manifest['map']['size_px'][1] // CELL
    root = ET.parse(O / 'map/village.tmx').getroot()
    if (int(root.get('width')), int(root.get('height'))) != (mw, mh):
        failures.append('tmx dims != manifest')
    data = root.find('.//layer/data').text.strip()
    ncells = len([t for t in data.replace('\n', ',').split(',') if t.strip()])
    if ncells != mw * mh:
        failures.append(f'tmx csv {ncells} != {mw*mh}')
    for obj in root.findall('.//object'):
        img = obj.find('image')
        rel = (O / 'map' / img.get('source')).resolve()
        if not rel.exists():
            failures.append(f'tmx objet manquant {img.get("source")}')
    ET.parse(O / 'map/village_sol.tsx')

    print('FAILURES:' if failures else 'OK', len(failures))
    for f in failures:
        print(' -', f)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
