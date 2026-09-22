"""CANON1 - four underground maps compiled only from native PMDO bank cells.

Method: the DTEF route (Wall / Secondary / Floor autotiles, 24 px native cells) with
the engine's own neighbour code and variant selection. No generated texture, no
recolour, no rotation, no pixel "bombing": every output cell is a whole tile read
from the pinned ``.tile`` bank, and the manifest records its coordinate so the
verifier re-reads the bank and compares pixels instead of trusting filenames.

    .venv/bin/python source/canon_dtef_v1/build.py                  # all four maps
    .venv/bin/python source/canon_dtef_v1/build.py --maps JC1_entree

Outputs  renders/canon_dtef_v1/{DTEF,cartes,apercus,manifests,PMDO}
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'renders/canon_dtef_v1'
STAGING = ROOT / '.cache/canon_dtef_v1_pmdo'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))

import autotile  # noqa: E402
import layouts  # noqa: E402
import pmdo_ground as pg  # noqa: E402
from native import Bank, TYPES, TYPE_INDEX, TILE, straight  # noqa: E402

THEMES = {'JC1': ('jungle', 'southern_jungle'), 'TC1': ('foret', 'treeshroud_forest_1')}
TICK_MS = 1000 / 60
MODES = ('jour', 'nuit')
LAYERS = ('01_sol_continu', '02_murs_relief', '03_secondaire_base', '04_secondaire_anim')
LAYER_OF = {'wall': '02_murs_relief', 'secondary': '03_secondaire_base', 'floor': '01_sol_continu'}
BASE_TICKS = 60


def seed_of(map_id: str) -> int:
    return int(hashlib.sha256(f'CANON1/{map_id}'.encode()).hexdigest()[:8], 16)


# --------------------------------------------------------------------------- layout
def place(bank: Bank, map_id: str, seed: int):
    """Resolve each cell to (type, variant, mask) with the engine's own rules."""
    g = layouts.grids(map_id)
    plan = {}
    for y in range(layouts.H):
        for x in range(layouts.W):
            for typ in TYPES:
                grid = g[typ]
                if not grid[y][x]:
                    continue
                mask = autotile.neighbor_mask(grid, y, x)
                assert mask in bank.slot, (map_id, x, y, typ, mask)
                count = bank.variant_count.get((TYPE_INDEX[typ], mask), 1)
                variant = autotile.variant_code(autotile.rand_code(x, y, seed), count)
                plan[(x, y, typ)] = (TYPE_INDEX[typ], variant, mask)
    return g, plan


def cell_stack(bank: Bank, key):
    """Engine layers of one placed cell: native base, then each native anim group."""
    t, vi, mask = key
    out = [([bank.base[(t, vi, mask)]], BASE_TICKS)]
    if TYPES[t] == 'secondary':
        for gid, locs in sorted(bank.anim.get((t, vi, mask), {}).items()):
            out.append((locs, bank.duration(gid)))
    return out


# ------------------------------------------------------------------------- render
def render(bank: Bank, plan: dict, size, mode: str, tick: int | None = None):
    layers = {name: Image.new('RGBA', size) for name in LAYERS}
    for (x, y, typ), key in plan.items():
        px = (x * TILE, y * TILE)
        t, vi, mask = key
        layers[LAYER_OF[TYPES[t]]].alpha_composite(bank.tile(bank.base[(t, vi, mask)], mode), px)
        if typ != 'secondary':
            continue
        for gid, locs in sorted(bank.anim.get((t, vi, mask), {}).items()):
            fi = 0 if tick is None else int(tick) % len(locs)
            layers['04_secondaire_anim'].alpha_composite(bank.tile(locs[fi], mode), px)
    return layers


def merge(layers: dict) -> Image.Image:
    out = Image.new('RGBA', layers[LAYERS[0]].size)
    for name in LAYERS:
        out.alpha_composite(layers[name])
    return out


def ora(path: Path, layers: dict):
    size = layers[LAYERS[0]].size
    root = ET.Element('image', w=str(size[0]), h=str(size[1]))
    stack = ET.SubElement(root, 'stack')
    flat = Image.new('RGBA', size)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (name, im) in enumerate(layers.items()):
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            z.writestr(f'data/{i}.png', buf.getvalue())
            ET.SubElement(stack, 'layer', name=name, src=f'data/{i}.png', x='0', y='0',
                          opacity='1.0', visibility='visible', **{'composite-op': 'svg:src-over'})
            flat.alpha_composite(im)
        z.writestr('stack.xml', ET.tostring(root))
        buf = io.BytesIO()
        flat.save(buf, format='PNG')
        z.writestr('mergedimage.png', buf.getvalue())


# -------------------------------------------------------------------- DTEF sheets
def export_sheets(bank: Bank, mode: str, dest: Path):
    """432x192 sheets: one per variant, plus one per animated group frame."""
    written = []
    for variant in range(3):
        bank.sheet(variant, mode).save(dest / f'tileset_{variant}.png')
        written.append(f'tileset_{variant}.png')
    for typ, vi, gid in sorted({(t, vi, gid) for (t, vi, mask), gs in bank.anim.items() for gid in gs}):
        _, _, count, dur = bank.groups[gid]
        for fi in range(count):
            name = f'tileset_{vi}_frame{gid}_{fi}.{dur}.png'
            bank.sheet(vi, mode, gid=gid, frame=fi).save(dest / name)
            written.append(name)
    return written


# ------------------------------------------------------------------ ground export
def ground_export(bank: Bank, plan: dict, g: dict, map_id: str, mode: str, asset: str, staging: Path):
    """PMDO Ground, TexSize=1: one native 24 px cell = nine 8 px cells, bytes intact."""
    SUB, stored = pg.SUB, bank.stored
    bank_obj = pg.TileBank(f'CANON1_{map_id}_{mode}_T'.upper())
    registered: set[tuple[int, int]] = set()

    def register(loc):
        if loc not in registered:
            bank_obj.add_tile(loc, stored[loc])
            registered.add(loc)

    gw, gh = layouts.W * SUB, layouts.H * SUB
    cells = {name: [[None] * gh for _ in range(gw)] for name in LAYERS[:3]}
    for (x, y, typ), key in plan.items():
        stack = cell_stack(bank, key)
        for locs, _dur in stack:
            for loc in locs:
                register(loc)
        layer_name = LAYER_OF[TYPES[key[0]]]
        for dy in range(SUB):
            for dx in range(SUB):
                # one 24 px native frame -> nine 8 px ground cells, no pixel touched
                cell_layers = []
                for locs, dur in stack:
                    frames = [{'Sheet': bank_obj.name,
                               'TexLoc': {'X': loc[0] * SUB + dx, 'Y': loc[1] * SUB + dy}} for loc in locs]
                    cell_layers.append((frames, dur))
                cells[layer_name][x * SUB + dx][y * SUB + dy] = cell_layers
    obstacles = [[0] * gh for _ in range(gw)]
    for y in range(layouts.H):
        for x in range(layouts.W):
            blocked = 1 if (g['wall'][y][x] or g['secondary'][y][x]) else 0
            for dy in range(SUB):
                for dx in range(SUB):
                    obstacles[x * SUB + dx][y * SUB + dy] = blocked
    sx, sy = g['spawn']
    ex, ey = g['exit']
    reserved = [(x, y) for y in range(layouts.H) for x in range(layouts.W) if g['reserved'][y][x]]
    if reserved:
        rx0 = min(x for x, _ in reserved)
        rx1 = max(x for x, _ in reserved) + 1
        ry0 = min(y for _, y in reserved)
        ry1 = max(y for _, y in reserved) + 1
    else:
        rx0 = rx1 = ry0 = ry1 = 0
    markers = [pg.marker('arrivee', (sx + .5) * TILE, (sy + .5) * TILE),
               pg.marker('sortie', (ex + .5) * TILE, (ey + .5) * TILE)]
    if reserved:
        markers.append(pg.marker('zone_reservee_structures', (rx0 + rx1) / 2 * TILE, (ry0 + ry1) / 2 * TILE,
                                 (rx1 - rx0) * TILE, (ry1 - ry0) * TILE))
    layers = [pg.ground_layer('01 Sol continu - cellules natives', cells[LAYERS[0]], 0),
              pg.ground_layer('02 Murs et reliefs - cellules natives', cells[LAYERS[1]], 0),
              pg.ground_layer('03 Secondaire natif - base puis cycle natif', cells[LAYERS[2]], 1)]
    doc = pg.ground_doc(asset, f'Canonia {map_id} - {mode}',
                        'CANON1 : cellules natives DTEF (banque PMDO epinglee), une tuile = 9 cellules '
                        '8px sans modification de pixel. Collisions derivees du layout. Marqueurs = '
                        'reperes editeur, pas des warps installes. Nuit = filtre Abyss applique une fois.',
                        layers, obstacles, markers)
    pg.save(staging / f'Data/Ground/{asset}.rsground',
            json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode())
    pg.save(staging / f'Data/Script/ground/{asset}/init.lua',
            b"-- CANON1 : le cycle provient des frames natives des tuiles ; aucun script requis.\nreturn {}\n")
    info = bank_obj.write(staging / 'Content/Tile' / f'{bank_obj.name}.tile')
    info.update(asset=asset, grid=[gw, gh], size_px=[gw * pg.CELL, gh * pg.CELL],
                placed_cells=len(plan), native_tiles_registered=len(registered),
                markers=[{'name': m['EntName'], **m['Collider']} for m in markers])
    return info


# ------------------------------------------------------------------------- previews
def labelled(im: Image.Image, text: str) -> Image.Image:
    out = im.convert('RGBA')
    d = ImageDraw.Draw(out)
    d.rectangle((0, 0, out.width, 15), fill=(16, 16, 22, 235))
    d.text((5, 3), text, fill=(238, 238, 238, 255))
    return out


def board(items, cols, gap=8):
    w = max(i.width for i, _ in items)
    h = max(i.height for i, _ in items)
    rows = math.ceil(len(items) / cols)
    cv = Image.new('RGBA', (cols * w + gap * (cols + 1), rows * (h + 16) + gap * (rows + 1)), (14, 14, 20, 255))
    for idx, (im, name) in enumerate(items):
        x = gap + (idx % cols) * (w + gap)
        y = gap + (idx // cols) * (h + 16 + gap)
        cv.alpha_composite(labelled(im, name), (x, y))
    return cv


# ---------------------------------------------------------------------------- main
def main(maps: list[str]):
    for sub in ('DTEF', 'cartes', 'apercus', 'manifests', 'PMDO'):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True, exist_ok=True)
    banks = {prefix: Bank(theme, source) for prefix, (theme, source) in THEMES.items()}
    manifest = {'method': 'cellules natives DTEF uniquement - aucun pixel genere',
                'tile_px': TILE, 'ground_cell_px': pg.CELL, 'grid_cells': [layouts.W, layouts.H],
                'size_px': [layouts.W * TILE, layouts.H * TILE], 'runtime_validated': False,
                'night': 'filtre Abyss source/cote_v4_abyss/night.py, une seule application par cellule',
                'themes': {}, 'maps': {}}
    for prefix, bank in banks.items():
        theme, source = THEMES[prefix]
        entry = {'source': source, 'bank_name': bank.sheet_name, 'bank_sha256': bank.sha256,
                 'bank_tiles': len(bank.stored),
                 'animated_groups': {str(g): {'frames': v[2], 'duration_ticks': v[3]}
                                      for g, v in sorted(bank.groups.items())}}
        for mode in MODES:
            dest = OUT / 'DTEF' / f'{source}_{mode}'
            dest.mkdir(parents=True, exist_ok=True)
            files = export_sheets(bank, mode, dest)
            entry[mode] = {'sheets': len(files)}
        manifest['themes'][theme] = entry
    for map_id in maps:
        prefix = map_id.split('_')[0]
        bank, (theme, source) = banks[prefix], THEMES[prefix]
        seed = seed_of(map_id)
        g, plan = place(bank, map_id, seed)
        info = layouts.check(map_id)
        size = (layouts.W * TILE, layouts.H * TILE)
        maps_manifest = {'map': map_id, 'theme': theme, 'source': source, 'bank_sha256': bank.sha256,
                         'seed': seed, 'geometry': info, 'cells': len(plan), 'modes': {}}
        for mode in MODES:
            directory = OUT / 'cartes' / map_id / mode
            directory.mkdir(parents=True, exist_ok=True)
            layers = render(bank, plan, size, mode)
            for name, im in layers.items():
                im.save(directory / f'{map_id}_{name}.png')
            merge(layers).save(directory / f'{map_id}_composition.png')
            ora(directory / f'{map_id}_{mode}.ora', layers)
            maps_manifest['modes'][mode] = {'ground': ground_export(bank, plan, g, map_id, mode,
                                                                    f'canon1_{map_id}_{mode}', STAGING)}
        (OUT / 'manifests' / map_id).mkdir(parents=True, exist_ok=True)
        (OUT / 'manifests' / map_id / 'provenance.json').write_text(json.dumps({
            'map': map_id, 'cell_px': TILE, 'theme': theme, 'source': source,
            'bank_sha256': bank.sha256, 'seed': seed,
            'masks_used': dict(Counter(k[2] for k in plan.values())),
            'variants_used': dict(Counter(k[1] for k in plan.values())),
            'cells': [[x, y, TYPES[t], mask, vi, list(bank.base[(t, vi, mask)]),
                       {str(gid): [list(l) for l in locs] for gid, locs in bank.anim.get((t, vi, mask), {}).items()}]
                      for (x, y, typ), (t, vi, mask) in sorted(plan.items())]}, indent=2))
        (OUT / 'manifests' / map_id / 'geometrie.json').write_text(json.dumps({
            'map': map_id, 'label': g['blueprint']['label'], 'grid': [layouts.W, layouts.H],
            'size_px': list(size), 'spawn_cell': list(g['spawn']), 'exit_cell': list(g['exit']),
            'connections': g['blueprint']['connections'],
            'reserved_cells': [[x, y] for y in range(layouts.H) for x in range(layouts.W) if g['reserved'][y][x]],
            'legend': {'#': 'mur', '.': 'sol', '~': 'secondaire natif', 'R': 'reserve vide',
                       'S': 'arrivee', 'X': 'sortie'},
            'rows': g['rows']}, indent=2))
        collisions = [[1 if (g['wall'][y][x] or g['secondary'][y][x]) else 0 for x in range(layouts.W)]
                      for y in range(layouts.H)]
        (OUT / 'manifests' / map_id / 'collisions.json').write_text(json.dumps({
            'derivation': 'layout : mur et secondaire bloquants, sol libre ; non valide en jeu',
            'grid': collisions}, indent=2))
        day = Image.open(OUT / 'cartes' / map_id / 'jour' / f'{map_id}_composition.png')
        night_im = Image.open(OUT / 'cartes' / map_id / 'nuit' / f'{map_id}_composition.png')
        ex = g['exit'][0]
        box = (max(0, min(layouts.W - 12, ex - 5)) * TILE, 0,
               max(0, min(layouts.W - 12, ex - 5)) * TILE + 12 * TILE, 7 * TILE)
        for im, name in [(day, 'jour'), (night_im, 'nuit')]:
            im.save(OUT / 'apercus' / f'CANON1_{map_id}_{name}_1x.png')
            # 3x control strip on the north passage: nearest neighbour only, so a
            # pixel here is still one bank pixel, just readable by eye.
            im.crop(box).resize((12 * TILE * 3, 7 * TILE * 3), Image.Resampling.NEAREST).save(
                OUT / 'apercus' / f'CANON1_{map_id}_zoom_passage_nord_3x_{name}.png')
        groups = sorted({gid for (t, vi, mask), gs in bank.anim.items() for gid in gs})
        periods = [bank.groups[gid][2] * bank.groups[gid][3] for gid in groups] or [1]
        period = math.lcm(*periods)
        samples = 32
        frames, durs = [], []
        for i in range(samples):
            tick = int(i * period / samples)
            frames.append(merge(render(bank, plan, size, 'jour', tick=tick)).resize(
                (size[0] * 2 // 3, size[1] * 2 // 3), Image.Resampling.NEAREST))
            durs.append(round(period / samples * TICK_MS))
        if frames:
            frames[0].save(OUT / 'apercus' / f'CANON1_{map_id}_cycle.webp', save_all=True,
                           append_images=frames[1:], duration=durs, loop=0, lossless=True)
        maps_manifest['animation'] = {'cycle_ticks': period, 'cycle_ms': round(period * TICK_MS, 1),
                                      'preview_samples': samples,
                                      'groups': {str(gid): {'frames': bank.groups[gid][2],
                                                             'duration_ticks': bank.groups[gid][3]}
                                                 for gid in groups}}
        manifest['maps'][map_id] = maps_manifest
    for doc in ('README_import.md', 'README.md'):
        shutil.copyfile(HERE / doc, OUT / doc)
    (OUT / 'layouts').mkdir(exist_ok=True)
    for txt in sorted((HERE / 'layouts').glob('*.txt')):
        shutil.copyfile(txt, OUT / 'layouts' / txt.name)
    pg.write_mod_xml(STAGING / 'Mod.xml', 'canon_dtef_v1')
    shutil.copyfile(ROOT / 'source/pmdo_cote/INSTALLER.py', STAGING / 'INSTALLER.py')
    banks = {p.stem: p for p in (STAGING / 'Content/Tile').glob('*.tile')}
    (STAGING / 'Content/Tile/index.idx').write_bytes(pg.encode_index(
        {name: pg.read_index_node(path) for name, path in sorted(banks.items())}))
    shutil.copytree(STAGING, OUT / 'PMDO', dirs_exist_ok=True)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    items = [(Image.open(OUT / 'apercus' / f'CANON1_{m}_{mode}_1x.png'),
              f'{m} - {THEMES[m.split("_")[0]][0]} - {mode}') for mode in MODES for m in maps]
    board(items, 2).save(OUT / 'apercus' / 'CANON1_collection_1x.png')
    print('CANON1 :', ', '.join(maps))
    for map_id in maps:
        print(' ', map_id, manifest['maps'][map_id]['cells'], 'cellules,',
              manifest['maps'][map_id]['modes']['jour']['ground']['unique_png'], 'tuiles 8px uniques')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--maps', nargs='*', default=layouts.MAPS)
    main(parser.parse_args().maps)
