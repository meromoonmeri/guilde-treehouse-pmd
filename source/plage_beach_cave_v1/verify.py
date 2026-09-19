#!/usr/bin/env python3
"""Vérification indépendante du lot plage_beach_cave_v1 -> verification.json.

    .venv/bin/python source/plage_beach_cave_v1/verify.py [--online]

Relit le projet livré (~/.cache/plage_beach_cave_v1_pack et le ZIP), jamais
les structures en mémoire du build. Ce n'est PAS un test dans le moteur PMDO.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402
from tilelib import (CELL, HERE, REF, ROOT, SHEETS, TileSheet, cell_frames, composite, load_ground,  # noqa: E402
                     load_sheets, render_layer, sha256, git_blob_sha, unpremultiply)

OUT = ROOT / 'exports/plage_beach_cave_v1'
PACK = Path.home() / '.cache/plage_beach_cave_v1_pack'
ZIP = ROOT / 'plage_beach_cave_v1_pmdo_0812.zip'
INV = {new: old for old, new in SHEETS.items()}


class Report:
    def __init__(self):
        self.checks = []
        self.failed = 0

    def check(self, name, ok, detail=None):
        self.checks.append({'check': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
        if not ok:
            self.failed += 1
            print('FAIL', name, detail)
        return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online', action='store_true', help='compare aussi les blobs Git avec l arbre GitHub du commit épinglé')
    args = parser.parse_args()
    R = Report()
    provenance = json.loads((HERE / 'provenance.json').read_text())

    # 1. références : hachages
    for name, meta in provenance['files'].items():
        path = REF / name
        R.check(f'reference {name} sha256', path.is_file() and sha256(path) == meta['sha256'], meta['sha256'][:16])
        R.check(f'reference {name} git blob', git_blob_sha(path) == meta['git_blob_sha1'], meta['git_blob_sha1'][:12])
    if args.online:
        tree = json.loads(subprocess.run(['gh', 'api', f"repos/Minemaker0430/ExplorersOfSkyOrigins/git/trees/{provenance['commit']}?recursive=1"],
                                         capture_output=True, text=True, check=True).stdout)
        remote = {t['path']: t['sha'] for t in tree['tree']}
        for name, meta in provenance['files'].items():
            R.check(f'github blob {name}', remote.get(meta['eoso_path']) == meta['git_blob_sha1'], remote.get(meta['eoso_path']))

    # 2. feuilles livrées = feuilles sources, octet pour octet (pack et ZIP)
    with zipfile.ZipFile(ZIP) as archive:
        R.check('zip integrity', archive.testzip() is None)
        names = archive.namelist()
        for old, new in SHEETS.items():
            src = (REF / f'EoSO__{old}.tile').read_bytes()
            R.check(f'sheet {new} pack identical', (PACK / f'Content/Tile/{new}.tile').read_bytes() == src)
            R.check(f'sheet {new} zip identical', archive.read(f'{L.NAMESPACE}/Content/Tile/{new}.tile') == src)
        R.check('zip ground present', f'{L.NAMESPACE}/Data/Ground/{L.ASSET}.rsground' in names)
        ground_zip = archive.read(f'{L.NAMESPACE}/Data/Ground/{L.ASSET}.rsground')
        R.check('zip ground == pack ground', ground_zip == (PACK / f'Data/Ground/{L.ASSET}.rsground').read_bytes())
        base = [Path(n).name for n in names if n.endswith(('.tile', '.rsground'))]
        R.check('unique tile/ground basenames', len(base) == len(set(base)), base)
        R.check('zip has installer, Mod.xml, lua, index', all(f'{L.NAMESPACE}/{p}' in names for p in (
            'INSTALLER.py', 'Mod.xml', 'Content/Tile/index.idx', f'Data/Script/{L.NAMESPACE}/ground/{L.ASSET}/init.lua', 'OUVRIR_EDITEUR.sh', 'README.md')))

    # 3. Ground livré : structure
    document = json.loads(ground_zip.decode('utf-8-sig'))
    R.check('ground version 0.8.12.0', document['Version'] == '0.8.12.0')
    g = document['Object']
    R.check('TexSize 3 (24 px)', g['TexSize'] == 3)
    R.check('asset name', g['AssetName'] == L.ASSET)
    layers = {layer['Name']: layer for layer in g['Layers']}
    R.check('layers Back/Anim/Front in order', [layer['Name'] for layer in g['Layers']] == ['Back', 'Anim', 'Front'])
    dims = {(len(layer['Tiles']), len(layer['Tiles'][0])) for layer in g['Layers']}
    R.check('all layers 45 x 20', dims == {(L.NEW_W, L.NEW_H)}, sorted(dims))
    R.check('columns rectangular', all(len(col) == L.NEW_H for layer in g['Layers'] for col in layer['Tiles']))
    R.check('pixel dims multiples of 24 and 8', (L.NEW_W * CELL) % 24 == 0 and (L.NEW_H * CELL) % 24 == 0)

    # 4. chaque cellule = séquence exacte d'une cellule source (même calque)
    source = load_ground(REF / 'EoSO__beach.rsground')['Object']
    src_layers = {layer['Name']: layer for layer in source['Layers']}
    ref_sheets = load_sheets()
    pack_sheets = {new: TileSheet(PACK / f'Content/Tile/{new}.tile') for new in SHEETS.values()}
    mapping = json.loads((HERE / 'cell_mapping.json').read_text())

    def payload_seq(frames, sheets):
        return tuple(hashlib.sha256(sheets[s].blobs[x, y]).hexdigest() for s, x, y in frames)

    src_sequences = {name: set() for name in src_layers}
    for name, layer in src_layers.items():
        for col in layer['Tiles']:
            for tile in col:
                frames = cell_frames(tile)
                if frames:
                    src_sequences[name].add(payload_seq(frames, ref_sheets))
    bad_cells, bad_map, bad_sheet, counts = [], [], [], {}
    for name, layer in layers.items():
        counts[name] = 0
        for X, col in enumerate(layer['Tiles']):
            for Y, tile in enumerate(col):
                frames = cell_frames(tile)
                mapped = mapping.get(f'{name}:{X},{Y}')
                if not frames:
                    if mapped is not None and cell_frames(src_layers[name]['Tiles'][mapped[0]][mapped[1]]):
                        bad_map.append((name, X, Y))
                    continue
                counts[name] += 1
                if any(s not in pack_sheets or (x, y) not in pack_sheets[s].blobs for s, x, y in frames):
                    bad_sheet.append((name, X, Y))
                    continue
                seq = payload_seq(frames, pack_sheets)
                if seq not in src_sequences[name]:
                    bad_cells.append((name, X, Y))
                if mapped is None:
                    bad_map.append((name, X, Y))
                else:
                    src_frames = cell_frames(src_layers[name]['Tiles'][mapped[0]][mapped[1]])
                    if [(INV[s], x, y) for s, x, y in frames] != src_frames:
                        bad_map.append((name, X, Y))
    R.check('every frame references an existing delivered cell', not bad_sheet, bad_sheet[:5])
    R.check('every cell sequence exists in the source layer (byte-identical payloads)', not bad_cells, bad_cells[:5])
    R.check('cell_mapping.json consistent with delivered ground', not bad_map, bad_map[:5])
    R.check('non-empty cell counts', counts == {'Back': 900, 'Anim': 315, 'Front': 407}, counts)

    # 5. animation de la mer préservée
    anim_cells = [tile for col in layers['Anim']['Tiles'] for tile in col if tile['Layers']]
    R.check('anim cells: 17 frames, FrameLength 16', all(len(t['Layers'][0]['Frames']) == 17 and t['Layers'][0]['FrameLength'] == 16 for t in anim_cells))
    R.check('anim cells occupy rows 0-6 of every column', all(bool(layers['Anim']['Tiles'][X][Y]['Layers']) == (Y < 7) for X in range(L.NEW_W) for Y in range(L.NEW_H)))
    def static_count(layer, sheets):
        return sum(1 for col in layer['Tiles'] for t in col if t['Layers']
                   and len({hashlib.sha256(sheets[f['Sheet']].blobs[f['TexLoc']['X'], f['TexLoc']['Y']]).digest() for f in t['Layers'][0]['Frames']}) == 1)
    static_cells, static_src = static_count(layers['Anim'], pack_sheets), static_count(src_layers['Anim'], ref_sheets)
    # cellules immobiles d'origine (mer lointaine rangées 0-2 + rochers cuits dans la bande) + 12 colonnes x 3 rangées lointaines insérées
    R.check('static-across-frames anim cells = original + inserted far-sea cells', static_cells == static_src + 12 * 3, [static_cells, static_src])
    animated_mid = all(len({hashlib.sha256(pack_sheets[f['Sheet']].blobs[f['TexLoc']['X'], f['TexLoc']['Y']]).digest() for f in layers['Anim']['Tiles'][X][Y]['Layers'][0]['Frames']}) > 1
                       for X in range(9, 37) for Y in range(3, 7))
    R.check('open-sea cells rows 3-6 really animated (no static water fill)', animated_mid)
    frames = [composite(g, pack_sheets, f) for f in range(17)]
    R.check('17 distinct composite frames', len({fr.tobytes() for fr in frames}) == 17)
    for y in range(3, 7):
        band = [fr.crop((0, y * CELL, L.NEW_W * CELL, (y + 1) * CELL)).tobytes() for fr in frames]
        R.check(f'row {y} animated (frames differ)', len(set(band)) > 1)

    # 6. exports = rendu du projet livré
    R.check('frame00.png == composite', Image.open(OUT / 'plage_bc1_grande_frame00.png').convert('RGB').tobytes() == frames[0].convert('RGB').tobytes())
    back_png = Image.open(OUT / 'calques/PLAGE_BC1_back_sable_rochers_fond.png').convert('RGBA')
    R.check('back layer png', back_png.tobytes() == unpremultiply(render_layer(layers['Back'], pack_sheets, 0)).tobytes())
    front_png = Image.open(OUT / 'calques/PLAGE_BC1_front_rochers_palmiers.png').convert('RGBA')
    R.check('front layer png', front_png.tobytes() == unpremultiply(render_layer(layers['Front'], pack_sheets, 0)).tobytes())
    ok = True
    for f in range(17):
        strip = Image.open(OUT / f'calques/PLAGE_BC1_mer_frame{f:02d}.png').convert('RGBA')
        expected = unpremultiply(render_layer(layers['Anim'], pack_sheets, f)).crop((0, 0, L.NEW_W * CELL, 7 * CELL))
        ok &= strip.tobytes() == expected.tobytes()
    R.check('17 sea strips png', ok)
    gif = Image.open(OUT / 'plage_bc1_grande_x2.gif')
    R.check('gif 17 frames', getattr(gif, 'n_frames', 1) == 17, getattr(gif, 'n_frames', 1))
    webp = Image.open(OUT / 'plage_bc1_grande_anim.webp')
    R.check('webp 17 frames', getattr(webp, 'n_frames', 1) == 17)

    # 7. raccords : paires de cellules voisines absentes de l'original, mesurées
    def payload_grid(layer, sheets):
        grid = {}
        for X, col in enumerate(layer['Tiles']):
            for Y, tile in enumerate(col):
                frames_ = cell_frames(tile)
                grid[X, Y] = payload_seq(frames_, sheets) if frames_ else None
        return grid

    def hseam(arr, X, Y):  # cellule (X,Y) | (X+1,Y), RGBA prémultiplié, toutes frames
        return float(np.mean((arr[:, Y * CELL:(Y + 1) * CELL, X * CELL + CELL - 1] - arr[:, Y * CELL:(Y + 1) * CELL, (X + 1) * CELL]) ** 2))

    def vseam(arr, X, Y):  # cellule (X,Y) / (X,Y+1)
        return float(np.mean((arr[:, Y * CELL + CELL - 1, X * CELL:(X + 1) * CELL] - arr[:, (Y + 1) * CELL, X * CELL:(X + 1) * CELL]) ** 2))

    seam_report = {'method': 'MSE RGBA sur le rendu du calque seul (17 frames), paires de cellules voisines absentes de la carte d origine, comparées au pire raccord du même calque dans la carte d origine'}
    for name in ('Back', 'Anim', 'Front'):
        n_frames = 17 if name == 'Anim' else 1
        src_arr = np.stack([np.asarray(render_layer(src_layers[name], ref_sheets, f)) for f in range(n_frames)]).astype(np.float64)
        new_arr = np.stack([np.asarray(render_layer(layers[name], pack_sheets, f)) for f in range(n_frames)]).astype(np.float64)
        src_h = max(hseam(src_arr, X, Y) for X in range(L.ORIG_W - 1) for Y in range(L.ORIG_H))
        src_v = max(vseam(src_arr, X, Y) for X in range(L.ORIG_W) for Y in range(L.ORIG_H - 1))
        sg, ng = payload_grid(src_layers[name], ref_sheets), payload_grid(layers[name], pack_sheets)
        pairs_h = {(sg[x, y], sg[x + 1, y]) for x in range(L.ORIG_W - 1) for y in range(L.ORIG_H)}
        pairs_v = {(sg[x, y], sg[x, y + 1]) for x in range(L.ORIG_W) for y in range(L.ORIG_H - 1)}
        new_h = [(X, Y) for X in range(L.NEW_W - 1) for Y in range(L.NEW_H) if (ng[X, Y], ng[X + 1, Y]) not in pairs_h]
        new_v = [(X, Y) for X in range(L.NEW_W) for Y in range(L.NEW_H - 1) if (ng[X, Y], ng[X, Y + 1]) not in pairs_v]
        hs = [hseam(new_arr, X, Y) for X, Y in new_h]
        vs = [vseam(new_arr, X, Y) for X, Y in new_v]
        seam_report[name] = {'original_max_horizontal': round(src_h, 1), 'original_max_vertical': round(src_v, 1),
                             'new_horizontal_pairs': len(new_h), 'max_horizontal': round(max(hs), 1) if hs else 0.0,
                             'new_vertical_pairs': len(new_v), 'max_vertical': round(max(vs), 1) if vs else 0.0,
                             'worst_horizontal': sorted(zip([round(v, 1) for v in hs], new_h), reverse=True)[:5],
                             'worst_vertical': sorted(zip([round(v, 1) for v in vs], new_v), reverse=True)[:5]}
        R.check(f'{name}: new adjacencies no worse than original seams',
                (not hs or max(hs) <= src_h) and (not vs or max(vs) <= src_v), seam_report[name])

    # 8. obstacles et accessibilité
    obst = g['obstacles']
    R.check('obstacle grid 135 x 60', len(obst) == L.NEW_W * 3 and all(len(c) == L.NEW_H * 3 for c in obst))
    R.check('obstacle bounds consistent', all(cell['Bounds'] == {'X': x * 8, 'Y': y * 8, 'Width': 8, 'Height': 8} and cell['Tags'] in (0, 1)
                                              for x, col in enumerate(obst) for y, cell in enumerate(col)))
    free = {(x, y) for x, col in enumerate(obst) for y, cell in enumerate(col) if cell['Tags'] == 0}
    ents = g['Entities'][0]
    marker = next(m for m in ents['Markers'] if m['EntName'] == 'Entrance')['Collider']
    objs = {o['EntName']: o['Collider'] for o in ents['GroundObjects']}
    R.check('entities: Entrance, Exit, Beach_Cave_Entrance', set(objs) == {'Exit', 'Beach_Cave_Entrance'} and len(ents['Markers']) == 1 and not ents['Spawners'])

    def cells_of(c):
        return {(x, y) for x in range(c['X'] // 8, (c['X'] + c['Width'] - 1) // 8 + 1) for y in range(c['Y'] // 8, (c['Y'] + c['Height'] - 1) // 8 + 1)}

    def reachable(start_cells):
        seen = set(c for c in start_cells if c in free)
        queue = deque(seen)
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in free and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    queue.append((nx, ny))
        return seen

    start = cells_of(marker)
    R.check('entrance marker on free ground inside map', start <= free and marker['X'] + marker['Width'] <= L.NEW_W * CELL)
    region = reachable(start)
    R.check('cave trigger reachable from entrance', bool(region & cells_of(objs['Beach_Cave_Entrance'])))
    R.check('exit trigger reachable and touching the right edge', bool(region & cells_of(objs['Exit'])) and objs['Exit']['X'] + objs['Exit']['Width'] >= L.NEW_W * CELL - 8)
    edge_free = {y for (x, y) in free if x == L.NEW_W * 3 - 1}
    # couloir d'origine : rangées 8 px 22-29 (y 176-239) ; avec 4 rangées de 24 px insérées : 22-41 (y 176-335)
    R.check('right edge free corridor rows 22-41 (8 px) only', edge_free == set(range(22, 42)), sorted(edge_free))
    sand_free = all((x, y) in free for X in range(6, 41) for Y in range(8, 14) for x in range(X * 3, X * 3 + 3) for y in range(Y * 3, Y * 3 + 3)
                    if not layers['Front']['Tiles'][X][Y]['Layers'])
    R.check('inserted sand rows walkable where no Front detail', sand_free)
    R.check('free cell count grows with the map', len(free) > 948, len(free))

    # 9. index, Mod.xml, installateur (dans un mod temporaire)
    spec = importlib.util.spec_from_file_location('installer', PACK / 'INSTALLER.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    nodes = installer.read_index(PACK / 'Content/Tile/index.idx')
    heads = {}
    for path in (PACK / 'Content/Tile').glob('*.tile'):
        with path.open('rb') as f:
            heads[path.stem] = installer.read_node(f)
    R.check('index.idx == tile headers', nodes == heads and set(nodes) == set(SHEETS.values()))
    root = ET.parse(PACK / 'Mod.xml').getroot()
    R.check('Mod.xml namespace/version', root.findtext('Namespace') == L.NAMESPACE and root.findtext('GameVersion') == '0.8.12.0')
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp) / 'mod'
        mod.mkdir()
        (mod / 'Mod.xml').write_text(f'<?xml version="1.0" encoding="utf-8"?><Header><Namespace>{L.NAMESPACE}</Namespace></Header>')
        installer.install(PACK, mod)
        merged = installer.read_index(mod / 'Content/Tile/index.idx')
        R.check('installer copies ground, sheets, scripts and merges index',
                (mod / f'Data/Ground/{L.ASSET}.rsground').read_bytes() == ground_zip and set(merged) == set(SHEETS.values())
                and (mod / f'Data/Script/{L.NAMESPACE}/ground/{L.ASSET}/init.lua').is_file())
        try:
            installer.install(PACK, mod)
            rerun = True
        except ValueError:
            rerun = False
        R.check('installer idempotent on identical files', rerun)

    # 10. Tiled
    tmj = json.loads((OUT / 'tiled/plage_bc1_grande.tmj').read_text())
    R.check('tiled map dims', tmj['width'] == L.NEW_W and tmj['height'] == L.NEW_H and tmj['tilewidth'] == CELL and all(len(l['data']) == L.NEW_W * L.NEW_H for l in tmj['layers']))
    R.check('tiled tsx present', all((OUT / 'tiled' / t['source']).is_file() for t in tmj['tilesets']))

    runtime = json.loads((HERE / 'runtime_verification.json').read_text()) if (HERE / 'runtime_verification.json').exists() else {}
    if runtime:
        R.check('native PMDO 0.8.12 headless load (runtime_test.py)', runtime.get('status') == 'PASS' and runtime.get('asset') == L.ASSET, runtime.get('rows'))
    report = {
        'status': 'PASS' if R.failed == 0 else 'FAIL', 'lot': 'plage_beach_cave_v1', 'zip': ZIP.name, 'zip_sha256': sha256(ZIP),
        'ground': f'{L.ASSET}.rsground', 'ground_sha256': hashlib.sha256(ground_zip).hexdigest(),
        'grid_cells': [L.NEW_W, L.NEW_H], 'pixels': [L.NEW_W * CELL, L.NEW_H * CELL], 'cell_px': CELL,
        'source_commit': provenance['commit'], 'seams': seam_report, 'free_obstacle_cells': len(free),
        'native_runtime_tested': runtime.get('status') == 'PASS', 'native_runtime': runtime or None,
        'editor_tested': False, 'gpu_render_tested': False,
        'checks': R.checks, 'failed': R.failed,
    }
    (HERE / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    (PACK / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(report['status'], f"{len(R.checks)} checks, {R.failed} failed;", json.dumps(seam_report)[:400])
    sys.exit(1 if R.failed else 0)


if __name__ == '__main__':
    main()
