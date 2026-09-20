#!/usr/bin/env python3
"""Vérification indépendante du lot plage_cote_v2 -> verification.json.

    .venv/bin/python source/plage_cote_v2/verify.py [--online]

Relit le projet livré (~/.cache/plage_cote_v2_pack et le ZIP), jamais les
structures en mémoire du build. Ce n'est PAS un test dans le moteur PMDO
(voir runtime_test.py pour le chargement natif réel).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

OUT = ROOT / 'exports/plage_cote_v2'
PACK = Path.home() / '.cache/plage_cote_v2_pack'
ZIP = ROOT / 'plage_cote_v2_pmdo_0812.zip'
INV = {new: old for old, new in SHEETS.items()}
NAMES = ('crique', 'anse')
NAMESPACE = 'plage_cote_v2'


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

    # 2. ZIP et pack
    with zipfile.ZipFile(ZIP) as archive:
        R.check('zip integrity', archive.testzip() is None)
        names = archive.namelist()
        for old, new in SHEETS.items():
            src = (REF / f"EoSO__{old.replace(' ', '_')}.tile").read_bytes()
            R.check(f'sheet {new} pack identical', (PACK / f'Content/Tile/{new}.tile').read_bytes() == src)
            R.check(f'sheet {new} zip identical', archive.read(f'{NAMESPACE}/Content/Tile/{new}.tile') == src)
        grounds_zip = {}
        for name in NAMES:
            asset = L.LAYOUTS[name]['asset']
            p = f'{NAMESPACE}/Data/Ground/{asset}.rsground'
            R.check(f'zip ground {asset}', p in names)
            grounds_zip[name] = archive.read(p)
            R.check(f'zip ground {asset} == pack', grounds_zip[name] == (PACK / f'Data/Ground/{asset}.rsground').read_bytes())
        base = [Path(n).name for n in names if n.endswith(('.tile', '.rsground'))]
        R.check('unique tile/ground basenames', len(base) == len(set(base)), base)
        R.check('zip has installer, Mod.xml, lua, index', all(f'{NAMESPACE}/{p}' in names for p in (
            'INSTALLER.py', 'Mod.xml', 'Content/Tile/index.idx', f'Data/Script/{NAMESPACE}/ground/plage_cv2_crique/init.lua',
            f'Data/Script/{NAMESPACE}/ground/plage_cv2_anse/init.lua', 'OUVRIR_EDITEUR.sh', 'README.md')))

    # 3. structure des Grounds livrés
    docs = {name: json.loads(grounds_zip[name].decode('utf-8-sig')) for name in NAMES}
    R.check('grounds version 0.8.12.0', all(d['Version'] == '0.8.12.0' for d in docs.values()))
    grounds = {name: docs[name]['Object'] for name in NAMES}
    R.check('TexSize 3 (24 px)', all(g['TexSize'] == 3 for g in grounds.values()))
    R.check('asset names', all(grounds[name]['AssetName'] == L.LAYOUTS[name]['asset'] for name in NAMES))
    R.check('single layer each', all(len(g['Layers']) == 1 for g in grounds.values()))
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        layer = g['Layers'][0]
        R.check(f'{name}: dims {W} x {H}', (len(layer['Tiles']), len(layer['Tiles'][0])) == (W, H))
        R.check(f'{name}: columns rectangular', all(len(col) == H for col in layer['Tiles']))
        R.check(f'{name}: pixel dims multiples of 24 and 8', (W * CELL) % 24 == 0 and (H * CELL) % 24 == 0)

    # 4. chaque cellule = séquence exacte d'une cellule source
    source = load_ground(REF / 'EoSO__Brine_Cave_Entrance.rsground')['Object']
    src_layer = source['Layers'][0]
    ref_sheets = load_sheets()
    pack_sheets = {new: TileSheet(PACK / f'Content/Tile/{new}.tile') for new in SHEETS.values()}

    def payload_seq(frames, sheets):
        return tuple(hashlib.sha256(sheets[s].blobs[x, y]).hexdigest() for s, x, y in frames)

    src_sequences = {payload_seq(cell_frames(t), ref_sheets) for col in src_layer['Tiles'] for t in col if cell_frames(t)}
    mapping_all = json.loads((HERE / 'cell_mapping.json').read_text())
    counts = {}
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        layer = g['Layers'][0]
        mapping = {k.split(':', 1)[1]: v for k, v in mapping_all.items() if k.startswith(name + ':')}
        bad_cells, bad_map, bad_sheet = [], [], []
        counts[name] = 0
        for X, col in enumerate(layer['Tiles']):
            for Y, tile in enumerate(col):
                frames_ = cell_frames(tile)
                if not frames_:
                    bad_map.append((name, X, Y))
                    continue
                counts[name] += 1
                if any(s not in pack_sheets or (x, y) not in pack_sheets[s].blobs for s, x, y in frames_):
                    bad_sheet.append((name, X, Y))
                    continue
                if payload_seq(frames_, pack_sheets) not in src_sequences:
                    bad_cells.append((name, X, Y))
                mapped = mapping.get(f'{X},{Y}')
                src_frames = cell_frames(src_layer['Tiles'][mapped[0]][mapped[1]])
                if [(INV[s], x, y) for s, x, y in frames_] != src_frames:
                    bad_map.append((name, X, Y))
        R.check(f'{name}: every frame references a delivered cell', not bad_sheet, bad_sheet[:5])
        R.check(f'{name}: every cell sequence exists in the source (byte-identical payloads)', not bad_cells, bad_cells[:5])
        R.check(f'{name}: cell_mapping.json consistent', not bad_map, bad_map[:5])
    R.check('non-empty cell counts', counts == {'crique': 735, 'anse': 903}, counts)

    # 5. animation canonique de l'eau
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        layer = g['Layers'][0]
        rive = L.rive_y(name)
        R.check(f'{name}: all cells 15 frames, FrameLength 8',
                all(len(t['Layers'][0]['Frames']) == L.FRAMES and t['Layers'][0]['FrameLength'] == 8
                    for col in layer['Tiles'] for t in col if t['Layers']))
        R.check(f'{name}: deep-sea cells really animated (no static water fill)',
                all(len({(f['TexLoc']['X'], f['TexLoc']['Y']) for f in layer['Tiles'][X][Y]['Layers'][0]['Frames']}) > 1
                    for X in range(W) for Y in range(rive + 1, H)))
        frames_imgs = [composite(g, pack_sheets, f) for f in range(L.FRAMES)]
        R.check(f'{name}: 15 distinct composite frames', len({fr.tobytes() for fr in frames_imgs}) == L.FRAMES)
        bands_ok = True
        for Y in range(rive + 1, H):
            band = [fr.crop((0, Y * CELL, W * CELL, (Y + 1) * CELL)).tobytes() for fr in frames_imgs]
            bands_ok &= len(set(band)) > 1
        R.check(f'{name}: every sea row animated (frames differ)', bands_ok)

    # 6. géométrie : rive alignée, coupe de sortie, entités
    for name in NAMES:
        g = grounds[name]
        W, H = L.dims(name)
        mapping = {k.split(':', 1)[1]: v for k, v in mapping_all.items() if k.startswith(name + ':')}
        rive = L.rive_y(name)
        R.check(f'{name}: foam shore aligned on row {rive}', all(mapping[f'{X},{rive}'][1] == 16 for X in range(W)))
        for k in range(2):
            R.check(f'{name}: exit cut cell {k} == source (24,{12 + k})',
                    mapping[f'{W - 1},{12 + k}'] == [24, 12 + k])

    # 7. coutures : paires de voisins absentes de la source, mesurées
    def payload_grid(layer, sheets):
        return {(X, Y): (payload_seq(cell_frames(t), sheets) if cell_frames(t) else None)
                for X, col in enumerate(layer['Tiles']) for Y, t in enumerate(col)}

    src_arr = np.stack([np.asarray(composite(source, ref_sheets, f)) for f in range(L.FRAMES)]).astype(np.float64)
    sg = payload_grid(src_layer, ref_sheets)
    pairs_h = {(sg[x, y], sg[x + 1, y]) for x in range(L.ORIG_W - 1) for y in range(L.ORIG_H)}
    pairs_v = {(sg[x, y], sg[x, y + 1]) for x in range(L.ORIG_W) for y in range(L.ORIG_H - 1)}
    src_h = max(float(np.mean((src_arr[:, Y * CELL:(Y + 1) * CELL, X * CELL + CELL - 1] - src_arr[:, Y * CELL:(Y + 1) * CELL, (X + 1) * CELL]) ** 2))
                for X in range(L.ORIG_W - 1) for Y in range(L.ORIG_H))
    src_v = max(float(np.mean((src_arr[:, Y * CELL + CELL - 1, X * CELL:(X + 1) * CELL] - src_arr[:, (Y + 1) * CELL, X * CELL:(X + 1) * CELL]) ** 2))
                for X in range(L.ORIG_W) for Y in range(L.ORIG_H - 1))
    seam_report = {'method': 'MSE RGBA sur le rendu composite (15 frames), paires de cellules voisines absentes de la carte source, comparées au pire raccord de la source'}
    seam_report['source_max_horizontal'] = round(src_h, 1)
    seam_report['source_max_vertical'] = round(src_v, 1)
    SEA_SKIP_ROWS = set(L.SEA_PHASE_SKIP_ROWS)
    SEA_SKIP_BOUND = 3300.0  # max mesuré de la jonction documentée (rangée 18 : 3236,3)
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        new_arr = np.stack([np.asarray(composite(g, pack_sheets, f)) for f in range(L.FRAMES)]).astype(np.float64)
        ng = payload_grid(g['Layers'][0], pack_sheets)
        junction_prev = {X - 1 for X in L.junction_cols(name)}
        new_h, skip_h = [], []
        for X in range(W - 1):
            for Y in range(H):
                if (ng[X, Y], ng[X + 1, Y]) in pairs_h:
                    continue
                (skip_h if (X in junction_prev and Y in SEA_SKIP_ROWS) else new_h).append((X, Y))
        new_v = [(X, Y) for X in range(W) for Y in range(H - 1) if (ng[X, Y], ng[X, Y + 1]) not in pairs_v]
        hs = [float(np.mean((new_arr[:, Y * CELL:(Y + 1) * CELL, X * CELL + CELL - 1] - new_arr[:, Y * CELL:(Y + 1) * CELL, (X + 1) * CELL]) ** 2)) for X, Y in new_h]
        ss = [float(np.mean((new_arr[:, Y * CELL:(Y + 1) * CELL, X * CELL + CELL - 1] - new_arr[:, Y * CELL:(Y + 1) * CELL, (X + 1) * CELL]) ** 2)) for X, Y in skip_h]
        vs = [float(np.mean((new_arr[:, Y * CELL + CELL - 1, X * CELL:(X + 1) * CELL] - new_arr[:, (Y + 1) * CELL, X * CELL:(X + 1) * CELL]) ** 2)) for X, Y in new_v]
        seam_report[name] = {'new_horizontal_pairs': len(new_h), 'max_horizontal': round(max(hs), 1) if hs else 0.0,
                             'new_vertical_pairs': len(new_v), 'max_vertical': round(max(vs), 1) if vs else 0.0,
                             'documented_sea_phase_skip': {'pairs': len(skip_h), 'max': round(max(ss), 1) if ss else 0.0,
                                                           'values': sorted(set(round(v, 1) for v in ss), reverse=True)},
                             'worst_horizontal': sorted(zip([round(v, 1) for v in hs], new_h), reverse=True)[:5],
                             'worst_vertical': sorted(zip([round(v, 1) for v in vs], new_v), reverse=True)[:5]}
        R.check(f'{name}: new adjacencies no worse than source seams',
                (not hs or max(hs) <= src_h) and (not vs or max(vs) <= src_v), seam_report[name])
        R.check(f'{name}: documented sea phase-skip within measured bound',
                (not ss or max(ss) <= SEA_SKIP_BOUND) and len(skip_h) == len(L.junction_cols(name)) * len(SEA_SKIP_ROWS),
                seam_report[name]['documented_sea_phase_skip'])

    # 8. obstacles, entités, accessibilité
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        obst = g['obstacles']
        R.check(f'{name}: obstacle grid {W * 3} x {H * 3}', len(obst) == W * 3 and all(len(c) == H * 3 for c in obst))
        R.check(f'{name}: obstacle bounds consistent',
                all(cell['Bounds'] == {'X': x * 8, 'Y': y * 8, 'Width': 8, 'Height': 8} and cell['Tags'] in (0, 1)
                    for x, col in enumerate(obst) for y, cell in enumerate(col)))
        free = {(x, y) for x, col in enumerate(obst) for y, cell in enumerate(col) if cell['Tags'] == 0}
        ents = g['Entities'][0]
        R.check(f'{name}: entities 1 marker + Exit + Beach_Cave_Entrance, no spawners',
                len(ents['Markers']) == 1 and {o['EntName'] for o in ents['GroundObjects']} == {'Exit', 'Beach_Cave_Entrance'}
                and not ents['Spawners'] and not ents['MapChars'])
        marker = ents['Markers'][0]
        objs = {o['EntName']: o['Collider'] for o in ents['GroundObjects']}

        def cells_of(c):
            return {(x, y) for x in range(c['X'] // 8, (c['X'] + c['Width'] - 1) // 8 + 1) for y in range(c['Y'] // 8, (c['Y'] + c['Height'] - 1) // 8 + 1)}

        start = cells_of(marker['Collider'])
        R.check(f'{name}: entrance marker on free ground inside map', start <= free and marker['Collider']['X'] + marker['Collider']['Width'] <= W * CELL)
        seen = set(start & free)
        queue = deque(seen)
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in free and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    queue.append((nx, ny))
        R.check(f'{name}: cave trigger reachable from entrance', bool(seen & cells_of(objs['Beach_Cave_Entrance'])))
        R.check(f'{name}: exit trigger reachable and touching the right edge',
                bool(seen & cells_of(objs['Exit'])) and objs['Exit']['X'] + objs['Exit']['Width'] >= W * CELL - 8)
        edge_free = {y for (x, y) in free if x == W * 3 - 1}
        want = set(range(12 * 3, 14 * 3))
        R.check(f'{name}: right edge free only on exit corridor rows {sorted(want)}', edge_free == want, sorted(edge_free))
        R.check(f'{name}: sea fully blocked below the foam shore',
                all((x, y) not in free for X in range(W) for Y in range(L.rive_y(name) + 1, H)
                    for x in range(X * 3, X * 3 + 3) for y in range(Y * 3, Y * 3 + 3)))
        R.check(f'{name}: free cell count grows with the map', len(free) > 948, len(free))

    # 9. index, Mod.xml, installateur
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
    R.check('Mod.xml namespace/version', root.findtext('Namespace') == NAMESPACE and root.findtext('GameVersion') == '0.8.12.0')
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp) / 'mod'
        mod.mkdir()
        (mod / 'Mod.xml').write_text(f'<?xml version="1.0" encoding="utf-8"?><Header><Namespace>{NAMESPACE}</Namespace></Header>')
        installer.install(PACK, mod)
        merged = installer.read_index(mod / 'Content/Tile/index.idx')
        R.check('installer copies grounds, sheet, scripts and merges index',
                all((mod / f'Data/Ground/{L.LAYOUTS[n]["asset"]}.rsground').read_bytes() == grounds_zip[n] for n in NAMES)
                and set(merged) == set(SHEETS.values())
                and (mod / f'Data/Script/{NAMESPACE}/ground/plage_cv2_crique/init.lua').is_file()
                and (mod / f'Data/Script/{NAMESPACE}/ground/plage_cv2_anse/init.lua').is_file())
        try:
            installer.install(PACK, mod)
            rerun = True
        except ValueError:
            rerun = False
        R.check('installer idempotent on identical files', rerun)

    # 10. Tiled
    for name in NAMES:
        W, H = L.dims(name)
        tmj = json.loads((OUT / f'tiled/plage_cv2_{name}.tmj').read_text())
        R.check(f'{name}: tiled map dims', tmj['width'] == W and tmj['height'] == H and tmj['tilewidth'] == CELL
                and all(len(l['data']) == W * H for l in tmj['layers']))
    tsx = (OUT / 'tiled/PLAGE_CV2_BRINE.tsx').read_text()
    R.check('tiled tsx: animated tiles present', tsx.count('<animation>') == L.ORIG_W * L.ORIG_H and 'duration="133"' in tsx)
    R.check('tiled tsx/png present', (OUT / 'tiled/PLAGE_CV2_BRINE.png').is_file())

    # 11. exports = rendu du projet livré
    for name in NAMES:
        g, (W, H) = grounds[name], L.dims(name)
        f0 = composite(g, pack_sheets, 0).convert('RGB')
        R.check(f'{name}: frame00.png == composite',
                Image.open(OUT / name / f'plage_cv2_{name}_frame00.png').convert('RGB').tobytes() == f0.tobytes())
        lay = unpremultiply(render_layer(g['Layers'][0], pack_sheets, 0))
        R.check(f'{name}: layer png', Image.open(OUT / name / f'PLAGE_CV2_{name}_calque.png').convert('RGBA').tobytes() == lay.tobytes())
        gif = Image.open(OUT / name / f'plage_cv2_{name}_x2.gif')
        R.check(f'{name}: gif 15 frames', getattr(gif, 'n_frames', 1) == L.FRAMES, getattr(gif, 'n_frames', 1))
        webp = Image.open(OUT / name / f'plage_cv2_{name}_anim.webp')
        R.check(f'{name}: webp 15 frames', getattr(webp, 'n_frames', 1) == L.FRAMES)

    runtime = json.loads((HERE / 'runtime_verification.json').read_text()) if (HERE / 'runtime_verification.json').exists() else {}
    if runtime:
        R.check('native PMDO 0.8.12 headless load (runtime_test.py)', runtime.get('status') == 'PASS', runtime.get('rows'))
    report = {
        'status': 'PASS' if R.failed == 0 else 'FAIL', 'lot': 'plage_cote_v2', 'zip': ZIP.name, 'zip_sha256': sha256(ZIP),
        'grounds': {name: L.LAYOUTS[name]['asset'] for name in NAMES},
        'grid_cells': {name: list(L.dims(name)) for name in NAMES},
        'pixels': {name: [L.dims(name)[0] * CELL, L.dims(name)[1] * CELL] for name in NAMES},
        'cell_px': CELL, 'source_commit': provenance['commit'], 'seams': seam_report,
        'free_obstacle_cells': {name: sum(1 for col in grounds[name]['obstacles'] for c in col if c['Tags'] == 0) for name in NAMES},
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
