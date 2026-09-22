#!/usr/bin/env python3
"""Paquet natif PMDO pour Reverie Town v1 : .rsground (JSON RogueEssence 0.8.12.0, TexSize 1 = 8 px)
+ feuilles .tile personnalisées uniquement pour les tuiles qui ne sont pas des tuiles natives entières
(objets découpés, et nuit des calques sans feuille *_Night native : objets, eau animée).

Les tuiles natives entières référencent directement les feuilles du jeu (Metano_Town_Base, Metano_Town_Cliffs,
Metano_Town_Objects, Metano_Town_Animation_Tileset, Metano_Town_River_Animation_1..4 et leurs *_Night).
Sortie : exports/reverie_town_v1/paquet_natif/{Data/Ground/*.rsground, Content/Tile/*.tile, manifest.json}.
Aucun test dans le moteur PMDO n'a été effectué ici (moteur absent du bac à sable).
"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from assemble import T, NIGHT_SHEETS, SHEETS, MIRROR_SHEETS  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location('pmdo_cote_build', ROOT / 'source/pmdo_cote/build.py')
_pmdo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pmdo)
TileBank, auto = _pmdo.TileBank, _pmdo.auto  # écrivain .tile natif validé sur les paquets précédents
import carte_ne  # noqa: E402
import carte_no  # noqa: E402

OUT = ROOT / 'exports/reverie_town_v1/paquet_natif'
FRAME_LENGTH = 10  # comme l'eau native de Métano (River_Animation, FrameLength 10)
MIRROR_REFS = {}   # feuille miroir -> {(tx, ty)} référencées par les cartes du paquet (écrites en .tile à la fin)


def rock_fraction(tile):
    a = np.array(tile).astype(int)
    op = a[..., 3] > 0
    if not op.any():
        return 0.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grass = (g >= r) & (g > b + 30)
    return float((op & ~grass).sum() / op.sum())


def obstacles(scene, walkable_override):
    """Tags 1 = bloqué (convention du fichier utilisateur cliffdaytest.rsground), 0 = libre.
    Falaises : tuiles majoritairement rocheuses ; eau/anim : toute tuile ; objets : tuiles couvertes >= 90 %.
    Première passe à affiner dans l'éditeur (escaliers et seuils de porte laissés libres)."""
    blocked = set()
    F = scene.layers['falaises']
    for (c, r) in F.refs[0]:
        tile = F.day[0].crop((c * T, r * T, c * T + T, r * T + T))
        if rock_fraction(tile) > 0.35:
            blocked.add((c, r))
    A = scene.layers['anim']
    for p in range(A.phases):
        blocked |= set(A.refs[p])
    O = scene.layers['objets']
    for (c, r) in O.refs[0]:
        tile = np.array(O.day[0].crop((c * T, r * T, c * T + T, r * T + T)))
        if (tile[..., 3] > 0).mean() >= 0.9:
            blocked.add((c, r))
    blocked -= walkable_override
    return [[{'Bounds': {'X': x * T, 'Y': y * T, 'Width': T, 'Height': T}, 'Tags': 1 if (x, y) in blocked else 0}
             for y in range(scene.h)] for x in range(scene.w)]


def stairs_and_doors(scene):
    """Tuiles rendues franchissables : planches des escaliers (tx 153..161) et seuils de porte (tx 108..111)."""
    free = set()
    F = scene.layers['falaises']
    for (c, r), (sheet, tx, ty) in F.refs[0].items():
        if 153 <= tx <= 161 and ty >= 53:
            free.add((c, r))
        if 107 <= tx <= 112 and ty >= 58:
            free.add((c, r))
    return free


def build_map(scene, mode, label):
    asset = f'{scene.slug}_{mode}'.lower()
    banks = {}

    def custom(bank_name, tile, c, r):
        if bank_name not in banks:
            banks[bank_name] = TileBank(bank_name)
        return banks[bank_name].add(tile, c, r)

    layers_json = []
    for li, name in enumerate(scene.order):
        L = scene.layers[name]
        tiles = [[None] * scene.h for _ in range(scene.w)]
        for x in range(scene.w):
            for y in range(scene.h):
                frames = []
                for p in range(L.phases):
                    ref = L.refs[p].get((x, y))
                    if ref is None:
                        frames.append(None)
                        continue
                    sheet, tx, ty = ref
                    img = (L.day if mode == 'jour' else L.night)[p]
                    tile = img.crop((x * T, y * T, x * T + T, y * T + T))
                    native = (x, y) not in L.cut[p] and (mode == 'jour' or sheet in NIGHT_SHEETS)
                    if native:
                        ref_sheet = NIGHT_SHEETS[sheet] if mode == 'nuit' else sheet
                        frames.append({'Sheet': ref_sheet, 'TexLoc': {'X': tx, 'Y': ty}})
                        if ref_sheet in MIRROR_SHEETS:   # feuille miroir (non native) : livrée en .tile à part
                            MIRROR_REFS.setdefault(ref_sheet, set()).add((tx, ty))
                    else:
                        frames.append(custom(f'{scene.slug}_{mode}_{name}'.upper(), tile, x, y))
                frames = [f for f in frames if f is not None]
                if not frames:
                    tiles[x][y] = auto()
                    continue
                if all(f == frames[0] for f in frames):
                    frames = [frames[0]]
                tiles[x][y] = auto(frames, FRAME_LENGTH if len(frames) > 1 else 60)
        layers_json.append({'Name': f'{li:02d} {name}', 'Layer': 0, 'Visible': True, 'Tiles': tiles})

    free = stairs_and_doors(scene)
    obs = obstacles(scene, free)
    # marqueur d'entrée : case libre près du bord sud, au centre (arrivée par le sud -> objectif au nord)
    entry = None
    for y in range(scene.h - 4, scene.h // 2, -1):
        for dx in range(0, scene.w // 2):
            for x in (scene.w // 2 + dx, scene.w // 2 - dx):
                if all(obs[x + i][y + j]['Tags'] == 0 for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    entry = (x, y)
                    break
            if entry:
                break
        if entry:
            break
    marker = {'EntName': 'entrance', 'Direction': 0, 'EntEnabled': True, 'triggerType': 0,
              'Collider': {'X': entry[0] * T - 8, 'Y': entry[1] * T - 8, 'Width': 16, 'Height': 16}}
    obj = {'$type': 'RogueEssence.Ground.GroundMap, RogueEssence', 'TexSize': 1,
           'Name': {'DefaultText': label, 'LocalTexts': {}}, 'Released': False,
           'Comment': 'Reverie Town v1 - tuiles natives Metano (kit falaises). Collisions : premiere passe automatique a affiner.',
           'obstacles': obs,
           'rand': {'$type': 'RogueElements.ReRandom, RogueElements', 'FirstSeed': 0,
                    's': [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
           'Status': {},
           'Background': {'$type': 'RogueEssence.Dungeon.MapBG, RogueEssence', 'MapLoc': {'X': 0, 'Y': 0},
                          'BGAnim': {'AnimIndex': '', 'FrameTime': 1, 'StartFrame': -1, 'EndFrame': -1,
                                     'AnimDir': -1, 'Alpha': 255, 'AnimFlip': 0},
                          'BGMovement': {'X': 0, 'Y': 0}, 'Parallax': '0, 0', 'RepeatX': False, 'RepeatY': False},
           'BlankBG': auto(), 'Layers': layers_json, 'AssetName': asset, 'Music': '', 'EdgeView': 0,
           'NoSwitching': False, 'ViewCenter': None, 'ViewOffset': {'X': 0, 'Y': 0}, 'ActiveChar': None,
           'Decorations': [{'Name': 'Vos decorations', 'Layer': 0, 'Visible': True, 'Anims': []}],
           'Entities': [{'Name': 'Vos objets et personnages', 'Visible': True, 'MapChars': [],
                         'GroundObjects': [], 'Spawners': [], 'Markers': [marker]}]}
    doc = {'Version': '0.8.12.0', 'Object': obj}
    path = OUT / f'Data/Ground/{asset}.rsground'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    for bank in banks.values():
        bank.write(OUT / f'Content/Tile/{bank.name}.tile')
    sheets = sorted({f['Sheet'] for L in layers_json for col in L['Tiles'] for t in col for la in t['Layers'] for f in la['Frames']})
    return {'asset': asset, 'file': f'Data/Ground/{asset}.rsground', 'label': label, 'grid': [scene.w, scene.h],
            'size_px': [scene.w * T, scene.h * T], 'entry_tile': list(entry), 'sheets': sheets,
            'custom_tiles': {b.name: len(b.data) for b in banks.values()},
            'mirror_tiles': {sh: sum(1 for L in layers_json for col in L['Tiles'] for t in col for la in t['Layers']
                                     for f in la['Frames'] if f['Sheet'] == sh) for sh in MIRROR_SHEETS if sh in sheets},
            'blocked_tiles': sum(t['Tags'] == 1 for col in obs for t in col)}


def write_mirror_banks():
    """Feuilles miroir (RVT_Cliffs_Miroir[_Nuit]) : .tile à disposition conservée (TexLoc = (tx, ty) de la feuille
    miroir), ne contenant que les tuiles référencées par les cartes du paquet."""
    out = {}
    for sheet, locs in MIRROR_REFS.items():
        bank = TileBank(sheet, preserve_layout=True)
        src = SHEETS.get(sheet)
        for tx, ty in sorted(locs):
            bank.add(src.crop((tx * T, ty * T, tx * T + T, ty * T + T)), tx, ty)
        bank.write(OUT / f'Content/Tile/{bank.name}.tile')
        out[sheet] = len(bank.data)
    return out


def main():
    manifest = {'native_schema_version': '0.8.12.0', 'tex_size': 1, 'tile_px': T, 'frame_length': FRAME_LENGTH,
                'runtime_tested': False, 'maps': []}
    for mod, label in ((carte_ne, 'Reverie Town - Nord-Est'), (carte_no, 'Reverie Town - Nord-Ouest')):
        scene = mod.build()
        scene.verify()
        for mode in ('jour', 'nuit'):
            info = build_map(scene, mode, f'{label} ({mode})')
            manifest['maps'].append(info)
            print(info['asset'], info['grid'], 'feuilles', len(info['sheets']), 'custom', info['custom_tiles'],
                  'bloquées', info['blocked_tiles'])
    manifest['mirror_tile_sheets'] = write_mirror_banks()
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
