"""CANON1 audit: prove the canonical claim, or fail.

Levels follow MANUEL_METHODE_PMDO.md §20: A provenance, B images, C formats,
D install rehearsal. E (PMDO render, gameplay) is **not** attempted here and no
test below should be read as claiming it.

    .venv/bin/python source/canon_dtef_v1/verify.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'renders/canon_dtef_v1'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))
sys.path.insert(0, str(ROOT / 'source/cote_v5_expeditions'))

import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location('canon_build', HERE / 'build.py')
B = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(B)  # explicit path: three sibling lots ship a build.py  # noqa: E402

import autotile  # noqa: E402
import layouts  # noqa: E402
import pmdo_ground as pg  # noqa: E402
from audit_references import tiles as read_tile_bank  # noqa: E402
from native import Bank, TYPES, TYPE_INDEX, TILE  # noqa: E402
from night import night  # noqa: E402

MODES = ('jour', 'nuit')
LAYERS = B.LAYERS
GROUND_LAYER_OF = {0: 1, 1: 2, 2: 0}  # native type (wall, secondary, floor) -> ground layer order
report: list[dict] = []


def record(name, ok, **fields):
    report.append({'test': name, 'status': 'PASS' if ok else 'FAIL', **fields})
    print(('PASS  ' if ok else 'FAIL  ') + name + ('  ' + json.dumps(fields, ensure_ascii=False)[:260] if not ok else ''))
    if not ok:
        raise SystemExit(1)


def banks():
    return {prefix: Bank(theme, source) for prefix, (theme, source) in B.THEMES.items()}


def recomputed_plan(bank: Bank, map_id: str):
    """Independent re-derivation: blueprints + engine rules, no build shortcut."""
    g = layouts.grids(map_id)
    plan = {}
    seed = B.seed_of(map_id)
    for y in range(layouts.H):
        for x in range(layouts.W):
            for typ in TYPES:
                if not g[typ][y][x]:
                    continue
                mask = autotile.neighbor_mask(g[typ], y, x)
                count = bank.variant_count.get((TYPE_INDEX[typ], mask), 1)
                variant = autotile.variant_code(autotile.rand_code(x, y, seed), count)
                plan[(x, y, typ)] = (TYPE_INDEX[typ], variant, mask)
    return g, plan


# --------------------------------------------------------------------------- A
def test_provenance(banks_):
    manifest = json.loads((OUT / 'manifest.json').read_text())
    for theme, info in manifest['themes'].items():
        path = ROOT / 'source/donjons_dtef_v2/references/DumpAsset/Content/Tile' / f"{info['bank_name']}.tile"
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert sha == info['bank_sha256'], theme
        prov = json.loads((ROOT / 'source/donjons_dtef_v2/references/provenance.json').read_text())
        entry = next(p for p in prov if p['path'].endswith(path.name))
        assert entry['sha256'] == sha, path.name
        assert sha == banks_[theme_prefix(theme, manifest)].sha256
    masks = autotile.canonical_masks()
    mapping = autotile.field_mapping()
    assert len(masks) == 47
    assert sorted(m for m in mapping if m >= 0) == masks
    cells = 0
    for map_id in layouts.MAPS:
        prov = json.loads((OUT / 'manifests' / map_id / 'provenance.json').read_text())
        assert prov['bank_sha256'] == banks_[map_id.split('_')[0]].sha256, map_id
        for x, y, tname, mask, variant, base, anim in prov['cells']:
            assert mask in masks, (map_id, x, y, typ, mask)
        cells += len(prov['cells'])
    record('A1 SHA-256 des banques bancaires identiques a provenance.json (2 banques)', True)
    record('A2 47 masques canoniques = FieldDtefMapping du moteur, chaque cellule placee dans ce jeu',
           True, cells=cells)


def theme_prefix(theme, manifest):
    for prefix, (name, _source) in B.THEMES.items():
        if name == theme:
            return prefix
    raise KeyError(theme)


# --------------------------------------------------------------------------- B
def test_pixels(banks_):
    manifest = json.loads((OUT / 'manifest.json').read_text())
    total = 0
    for map_id in layouts.MAPS:
        bank = banks_[map_id.split('_')[0]]
        g, plan = recomputed_plan(bank, map_id)
        prov = json.loads((OUT / 'manifests' / map_id / 'provenance.json').read_text())
        from_manifest = {(x, y, tname): (TYPES.index(tname), v, m)
                         for x, y, tname, m, v, b, a in prov['cells']}
        assert from_manifest == plan, (map_id, 'manifeste differente de la rederivation')
        size = (layouts.W * TILE, layouts.H * TILE)
        for mode in MODES:
            expected = {name: Image.new('RGBA', size) for name in LAYERS}
            for (x, y, typ), (t, vi, mask) in plan.items():
                expected[B.LAYER_OF[TYPES[t]]].alpha_composite(bank.tile(bank.base[(t, vi, mask)], mode),
                                                               (x * TILE, y * TILE))
                if typ == 'secondary':
                    for gid, locs in sorted(bank.anim.get((t, vi, mask), {}).items()):
                        expected[LAYERS[3]].alpha_composite(bank.tile(locs[0], mode), (x * TILE, y * TILE))
            for name in LAYERS:
                saved = np.array(Image.open(OUT / 'cartes' / map_id / mode / f'{map_id}_{name}.png').convert('RGBA'))
                assert np.array_equal(saved, np.array(expected[name])), (map_id, mode, name)
                total += int((saved[:, :, 3] > 0).sum())
            flat = Image.new('RGBA', size)
            for name in LAYERS:
                flat = Image.alpha_composite(flat, expected[name])
            own = {'01_sol_continu': 'floor', '02_murs_relief': 'wall',
                   '03_secondaire_base': 'secondary', '04_secondaire_anim': 'secondary'}
            for name in LAYERS:
                a = np.array(expected[name])
                opaque = (a[:, :, 3] > 0).reshape(layouts.H, TILE, layouts.W, TILE).any(axis=(1, 3))
                allowed = np.array(g[own[name]])
                if own[name] != 'floor':
                    assert not (opaque & ~allowed).any(), (map_id, mode, name)
                else:
                    bad = [(x, y) for y in range(layouts.H) for x in range(layouts.W)
                           if allowed[y, x] and not opaque[y, x]]
                    assert not bad, (map_id, mode, name, bad[:6])  # continuous ground, no hole
            comp = np.array(Image.open(OUT / 'cartes' / map_id / mode / f'{map_id}_composition.png').convert('RGBA'))
            assert np.array_equal(comp, np.array(flat)), (map_id, mode, 'composition')
            if mode == 'jour':
                allowed = set()
                for loc in {tuple(v) for v in bank.base.values()} | {
                        l for gs in bank.anim.values() for locs in gs.values() for l in locs}:
                    allowed |= {tuple(p) for p in np.array(bank.view[loc]).reshape(-1, 4).tolist()}
                used = {tuple(p) for p in comp.reshape(-1, 4).tolist() if p[3]}
                extra = used - allowed
                assert not extra, (map_id, len(extra), sorted(extra)[:4])
    record('B1 chaque cellule exportee est octet pour octet la cellule native de la banque', True,
           opaque_px=total, maps=len(layouts.MAPS), modes=len(MODES))
    record('B2 aucun RGBA du rendu de jour hors de la palette native utilisee', True)
    record('B3 sol continu sous tout, murs et secondaire limites a leurs cellules', True,
           layer_checks=len(layouts.MAPS) * len(MODES) * 4)


def test_night(banks_):
    for map_id in layouts.MAPS:
        day = Image.open(OUT / 'cartes' / map_id / 'jour' / f'{map_id}_composition.png').convert('RGBA')
        got = Image.open(OUT / 'cartes' / map_id / 'nuit' / f'{map_id}_composition.png').convert('RGBA')
        assert np.array_equal(np.array(night(day)), np.array(got)), map_id
        assert np.array_equal(np.array(day)[:, :, 3], np.array(got)[:, :, 3]), map_id
        assert not np.array_equal(np.array(night(got)), np.array(got)), map_id
        bank = banks_[map_id.split('_')[0]]
        # the filter is per-pixel: tiling it cell by cell must equal filtering the
        # whole composed map (no seams, no double darkening at the joins)
        tile_filtered = np.array(night(Image.new('RGBA', (1, 1), (13, 91, 40, 255))))
        assert int(tile_filtered[0, 0, 2]) > int(tile_filtered[0, 0, 0]), 'bascule de filtre unexpectedly changed'
    record('B4 nuit = filtre Abyss une seule application, alpha intact, jamais cumule', True)


def test_animation(banks_):
    manifest = json.loads((OUT / 'manifest.json').read_text())
    for map_id, info in manifest['maps'].items():
        anim = info['animation']
        period = anim['cycle_ticks']
        expect = math.lcm(*[g['frames'] * g['duration_ticks'] for g in anim['groups'].values()] or [1])
        assert period == expect, (map_id, period, expect)
        for gid, gspec in anim['groups'].items():
            assert period % (gspec['frames'] * gspec['duration_ticks']) == 0, (map_id, gid)
        bank = banks_[map_id.split('_')[0]]
        _, plan = recomputed_plan(bank, map_id)
        size = (layouts.W * TILE, layouts.H * TILE)

        def frame(tick):
            out = Image.new('RGBA', size)
            for (x, y, typ), (t, vi, mask) in plan.items():
                out.alpha_composite(bank.tile(bank.base[(t, vi, mask)], 'jour'), (x * TILE, y * TILE))
            for (x, y, typ), (t, vi, mask) in plan.items():
                if typ != 'secondary':
                    continue
                for gid, locs in sorted(bank.anim.get((t, vi, mask), {}).items()):
                    out.alpha_composite(bank.tile(locs[tick % len(locs)], 'jour'), (x * TILE, y * TILE))
            return np.array(out)

        moving = {frame(t).tobytes() for t in (0, 1, period // 2)}
        for t in (1, period // 3, period - 1):
            assert np.array_equal(frame(t), frame(t + period)), map_id
        assert len(moving) > 1, (map_id, 'animation figee')
        for theme, tinfo in manifest['themes'].items():
            prefix = V_prefix(theme)
            b = banks_[prefix]
            owners = {}
            for (typ, vi, mask), groups in b.anim.items():
                for gid in groups:
                    owners.setdefault(gid, set()).add(vi)
            for mode in MODES:
                files = sorted(p.name for p in (OUT / 'DTEF' / f"{tinfo['source']}_{mode}").glob('*.png'))
                for gid, gspec in tinfo['animated_groups'].items():
                    hits = [f for f in files if f'_frame{gid}_' in f]
                    assert len(hits) == gspec['frames'] * len(owners[int(gid)]), (theme, mode, gid, len(hits))
                    for name in hits:
                        sheet = Image.open(OUT / 'DTEF' / f"{tinfo['source']}_{mode}" / name).convert('RGBA')
                        assert sheet.size == (432, 192), (name, sheet.size)
    record('B5 animation : compositions t et t+cycle identiques, frames natives completes, feuilles 432x192',
           True)


def test_sheets(banks_):
    """The delivered DTEF sheets must be pure extraction, not the V2 pixel bombing."""
    v2 = ROOT / 'renders/donjons_dtef_v2/references_dtef'
    for prefix, (theme, source) in B.THEMES.items():
        bank = banks_[prefix]
        for mode in MODES:
            dest = OUT / 'DTEF' / f'{source}_{mode}'
            for variant in range(3):
                sheet = np.array(Image.open(dest / f'tileset_{variant}.png').convert('RGBA'))
                for typ in range(3):
                    for mask, slot in bank.slot.items():
                        x, y = bank.xy(typ, mask)
                        cell = sheet[y:y + TILE, x:x + TILE]
                        want = np.array(bank.tile(bank.base[(typ, variant, mask)], mode)) if (
                            typ, variant, mask) in bank.base else None
                        if want is None:
                            assert not cell[:, :, 3].any(), (source, mode, variant, typ, mask)
                        else:
                            assert np.array_equal(cell, want), (source, mode, variant, typ, mask)
        ref = v2 / source
        diff = 0
        if ref.exists():
            for variant in range(3):
                mine = np.array(Image.open(OUT / 'DTEF' / f'{source}_jour' / f'tileset_{variant}.png').convert('RGBA'))
                theirs = np.array(Image.open(ref / f'tileset_{variant}.png').convert('RGBA'))
                diff += int((mine[:, :, :3] != theirs[:, :, :3]).any(axis=2).sum())
        report_extra = diff
    record('B6 feuilles DTEF = extraction pure : toutes les cellules egales a la banque, difference avec le « bombing » V2 comptee',
           True, pixels_where_v2_was_painted=report_extra)


# --------------------------------------------------------------------------- C
def V_prefix(theme):
    for prefix, (name, _source) in B.THEMES.items():
        if name == theme:
            return prefix
    raise KeyError(theme)


def test_ground(banks_):
    manifest = json.loads((OUT / 'manifest.json').read_text())
    cells_checked = frames_checked = 0
    for map_id, info in manifest['maps'].items():
        bank = banks_[map_id.split('_')[0]]
        _, plan = recomputed_plan(bank, map_id)
        for mode in MODES:
            ground = info['modes'][mode]['ground']
            asset = ground['asset']
            doc = json.loads((OUT / 'PMDO' / 'Data/Ground' / f'{asset}.rsground').read_text(encoding='utf-8-sig'))
            o = doc['Object']
            assert doc['Version'] == '0.8.12.0' and o['TexSize'] == 1 and not o['Released'], asset
            assert o['$type'] == 'RogueEssence.Ground.GroundMap, RogueEssence'
            size, tbank, unique = read_tile_bank(OUT / 'PMDO/Content/Tile' / f"{ground['bank']}.tile")
            assert size == pg.CELL, (asset, size)
            assert unique == ground['unique_png'], (asset, unique)
            for (x, y, typ), (t, vi, mask) in plan.items():
                layer = o['Layers'][GROUND_LAYER_OF[t]]
                spec_base = bank.base[(t, vi, mask)]
                for dy in range(pg.SUB):
                    for dx in range(pg.SUB):
                        cell = layer['Tiles'][x * pg.SUB + dx][y * pg.SUB + dy]
                        tl = cell['Layers']
                        assert tl, (asset, x, y, typ)
                        fr = tl[0]['Frames'][0]
                        loc = (fr['TexLoc']['X'], fr['TexLoc']['Y'])
                        assert loc in tbank, (asset, loc)
                        assert loc == (spec_base[0] * pg.SUB + dx, spec_base[1] * pg.SUB + dy), (asset, loc)
                        want = np.array(bank.stored[spec_base])[dy * 8:(dy + 1) * 8, dx * 8:(dx + 1) * 8]
                        assert np.array_equal(np.array(tbank[loc]), want), (asset, loc)
                        cells_checked += 1
                        if typ == 'secondary':
                            groups = bank.anim.get((t, vi, mask), {})
                            # one engine layer for the base, then one per native group
                            assert len(tl) == 1 + len(groups), (asset, x, y, len(tl), len(groups))
                            for i, gid in enumerate(sorted(groups), start=1):
                                locs = groups[gid]
                                assert [f['TexLoc']['X'] // pg.SUB for f in tl[i]['Frames']] == [l[0] for l in locs]
                                assert [f['TexLoc']['Y'] // pg.SUB for f in tl[i]['Frames']] == [l[1] for l in locs]
                                assert tl[i]['FrameLength'] == bank.duration(gid), (asset, gid)
                                frames_checked += len(tl[i]['Frames'])
                        else:
                            assert len(tl) == 1, (asset, x, y, typ, len(tl))
            coll = json.loads((OUT / 'manifests' / map_id / 'collisions.json').read_text())['grid']
            for y in range(layouts.H):
                for x in range(layouts.W):
                    for dy in range(pg.SUB):
                        for dx in range(pg.SUB):
                            tag = o['obstacles'][x * pg.SUB + dx][y * pg.SUB + dy]
                            assert (tag['Tags'] != 0) == bool(coll[y][x]), (asset, x, y)
                            assert tag['Bounds'] == {'X': (x * pg.SUB + dx) * 8, 'Y': (y * pg.SUB + dy) * 8,
                                                     'Width': 8, 'Height': 8}
            names = [m['EntName'] for m in o['Entities'][0]['Markers']]
            assert 'arrivee' in names and 'sortie' in names, (asset, names)
            geo = json.loads((OUT / 'manifests' / map_id / 'geometrie.json').read_text())
            spawn = [m for m in o['Entities'][0]['Markers'] if m['EntName'] == 'arrivee'][0]
            assert (spawn['Collider']['X'] + 8, spawn['Collider']['Y'] + 8) == tuple(
                (c + .5) * TILE for c in geo['spawn_cell']), asset
            assert (OUT / 'PMDO/Data/Script/ground' / asset / 'init.lua').exists(), asset
            assert o['Background']['Layers'] == [], asset
    record('C1 Ground relu : chaque cellule 8px = octets natifs de la banque, frames animees = compte et duree natifs',
           True, cells=cells_checked, anim_frames=frames_checked)
    record('C2 obstacles alignes sur la grille 8px et coherents avec collisions.json', True)


# --------------------------------------------------------------------------- D
def test_install(banks_):
    banks_paths = {p.stem: p for p in (OUT / 'PMDO/Content/Tile').glob('*.tile')}
    assert banks_paths
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp) / 'mod'
        (mod / 'Content/Tile').mkdir(parents=True)
        (mod / 'Mod.xml').write_text((OUT / 'PMDO/Mod.xml').read_text().replace('canon_dtef_v1', 'test_mod'))
        donor = sorted(banks_paths.values())[0]
        foreign = mod / 'Content/Tile/OTHER_MOD_SET.tile'
        shutil.copyfile(donor, foreign)
        index = mod / 'Content/Tile/index.idx'
        index.write_bytes(pg.encode_index({'OTHER_MOD_SET': pg.read_index_node(foreign)}))
        merged, before = pg.merge_index(index, banks_paths)
        index.write_bytes(merged)
        nodes = pg.read_index(index)
        assert 'OTHER_MOD_SET' in nodes and set(nodes) >= set(banks_paths) | {'OTHER_MOD_SET'}
        assert before == ['OTHER_MOD_SET']
        assert nodes['OTHER_MOD_SET'] == pg.read_index_node(foreign)
        # the delivered project must be loadable as a standalone project too
        own = pg.read_index(OUT / 'PMDO/Content/Tile/index.idx')
        assert set(own) == set(banks_paths), (sorted(own), sorted(banks_paths))
        heads = []
        for name, path in banks_paths.items():
            raw = path.read_bytes()
            size, count = struct.unpack_from('<ii', raw)
            heads.append({'bank': name, 'tile_size': size, 'entries': count})
        assert all(h['tile_size'] == 8 for h in heads), heads
    record('D1 Mod.xml + index : projet autonome valide, banque etrangere preservee a la fusion', True,
           banks=len(banks_paths), entries=sum(h['entries'] for h in heads))


def test_previews():
    """The direct previews must be the same pixels, not a resampled derivative."""
    for map_id in layouts.MAPS:
        for mode in MODES:
            flat = Image.open(OUT / 'cartes' / map_id / mode / f'{map_id}_composition.png')
            direct = OUT / 'apercus' / f'CANON1_{map_id}_{mode}_1x.png'
            assert np.array_equal(np.array(Image.open(direct)), np.array(flat)), (map_id, mode, '1x')
            src = Image.open(OUT / 'apercus' / f'CANON1_{map_id}_zoom_passage_nord_3x_{mode}.png')
            x0 = max(0, min(layouts.W - 12, layouts.grids(map_id)['exit'][0] - 5))
            crop = flat.crop((x0 * TILE, 0, x0 * TILE + 12 * TILE, 7 * TILE))
            assert src.size == (crop.width * 3, crop.height * 3), (map_id, mode, 'taille du zoom')
            assert np.array_equal(np.array(src),
                                  np.array(crop.resize(src.size, Image.Resampling.NEAREST))), (map_id, mode, 'zoom')
            assert crop.resize(src.size, Image.Resampling.BILINEAR).tobytes() != src.tobytes(), \
                (map_id, mode, 'zoom reechantillonne')
    record('E1 aperus directs : 1x egal a la composition, zoom 3x = pixel natif repete x3, sans reechantillonage', True)


def main():
    banks_ = banks()
    test_provenance(banks_)
    test_pixels(banks_)
    test_night(banks_)
    test_animation(banks_)
    test_sheets(banks_)
    test_ground(banks_)
    test_install(banks_)
    test_previews()
    (OUT / 'verification.json').write_text(json.dumps(report, indent=2))
    print(f"\n{len(report)} controles PASS (niveaux A a D + apercus). Niveau E : rendu PMDO et jeu non executes.")


if __name__ == '__main__':
    main()
