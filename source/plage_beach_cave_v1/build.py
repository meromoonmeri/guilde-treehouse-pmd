#!/usr/bin/env python3
"""Construit le lot plage_beach_cave_v1 : Ground PMDO 0.8.12 (45 x 20 cellules
de 24 px), feuilles `.tile` copiées octet pour octet, rendus PNG par calque,
17 frames composites, GIF/WebP, Tiled, projet PMDO installable et ZIP.

    .venv/bin/python source/plage_beach_cave_v1/build.py            # tout
    .venv/bin/python source/plage_beach_cave_v1/build.py --preview  # rendu seul

Aucune cellule n'est dessinée : chaque cellule de la nouvelle carte copie la
séquence de frames d'une cellule de la carte EoSO `beach` (voir layout.py).
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import io
import json
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402
from tilelib import (CELL, HERE, REF, ROOT, SHEETS, TileSheet, cell_frames, composite,  # noqa: E402
                     dump_ground, git_blob_sha, load_ground, load_sheets, render_layer, sha256,
                     unpremultiply)

OUT = ROOT / 'exports/plage_beach_cave_v1'
PACK = Path.home() / '.cache/plage_beach_cave_v1_pack'
ZIP = ROOT / 'plage_beach_cave_v1_pmdo_0812.zip'
VIEW = ROOT / 'apercu_plage_beach_cave_v1.html'
FRAME_MS = 16 * 1000 / 60  # FrameLength 16 ticks a 60 Hz = 266.7 ms
EMPTY = {'AutoTileset': '', 'Associates': [], 'Layers': [], 'NeighborCode': -1}

SOURCE_COMMIT = 'bed944992c32e7e7927cc3480c72edb0b1782e26'
SOURCE_REPO = 'Minemaker0430/ExplorersOfSkyOrigins'
SOURCE_FILES = {  # nom local -> chemin dans le dépôt EoSO
    'EoSO__beach.rsground': 'Data/Ground/beach.rsground',
    'EoSO__D01P11A_layer1.tile': 'Content/Tile/D01P11A_layer1.tile',
    'EoSO__D01P11A_layer2.tile': 'Content/Tile/D01P11A_layer2.tile',
    'EoSO__beach_animation.tile': 'Content/Tile/beach_animation.tile',
    'EoSO__beach_init.lua': 'Data/Script/eos/ground/beach/init.lua',
    'EoSO__dusk_beach.rsground': 'Data/Ground/dusk_beach.rsground',
    'EoSO__DuskBeach.tile': 'Content/Tile/DuskBeach.tile',
    'EoSO__D01P11A_bpa5_0.tile': 'Content/Tile/D01P11A_bpa5_0.tile',
}


# --------------------------------------------------------------------------
# Assemblage du Ground
# --------------------------------------------------------------------------
def retarget(tile: dict) -> dict:
    """Copie une cellule source en renommant les feuilles vers les noms livrés."""
    tile = copy.deepcopy(tile)
    for anim in tile['Layers']:
        for frame in anim['Frames']:
            frame['Sheet'] = SHEETS[frame['Sheet']]
    return tile


def assemble(source: dict) -> tuple[dict, dict]:
    """Retourne (Ground assemblé, journal des correspondances cellule -> source)."""
    ground = copy.deepcopy(source)
    mapping = {}  # (layer, X, Y) -> (x, y) source ou None
    for layer in ground['Layers']:
        src = layer['Tiles']
        name = layer['Name']
        tiles = []
        for X, sx in enumerate(L.COLMAP):
            rows = {'Back': L.back_rows, 'Anim': lambda _: L.ANIM_ROWS, 'Front': L.front_rows}[name](sx)
            column = []
            for Y, sy in enumerate(rows):
                if sy is None:
                    column.append(copy.deepcopy(EMPTY))
                    mapping[name, X, Y] = None
                else:
                    column.append(retarget(src[sx][sy]))
                    mapping[name, X, Y] = (sx, sy)
            tiles.append(column)
        layer['Tiles'] = tiles
    front = next(layer for layer in ground['Layers'] if layer['Name'] == 'Front')
    front_src = next(layer for layer in source['Layers'] if layer['Name'] == 'Front')['Tiles']
    back = next(layer for layer in ground['Layers'] if layer['Name'] == 'Back')['Tiles']
    # Obstacles 8 px : 3 x 3 par cellule, mêmes correspondances que Front.
    src_obst = source['obstacles']
    obstacles = [[None] * (L.NEW_H * 3) for _ in range(L.NEW_W * 3)]

    def copy_block(sx, sy, X, Y):
        for i in range(3):
            for j in range(3):
                tags = 0 if sy is None else src_obst[sx * 3 + i][sy * 3 + j]['Tags']
                obstacles[X * 3 + i][Y * 3 + j] = {'Bounds': {'X': (X * 3 + i) * 8, 'Y': (Y * 3 + j) * 8, 'Width': 8, 'Height': 8}, 'Tags': tags}

    for X, sx in enumerate(L.COLMAP):
        for Y, sy in enumerate(L.obstacle_rows(sx)):
            copy_block(sx, sy, X, Y)
    # Détails du sable : suppressions, placements, ombres du calque Back.
    back_src = next(layer for layer in source['Layers'] if layer['Name'] == 'Back')['Tiles']
    for X, Y in L.FRONT_REMOVE:
        assert front['Tiles'][X][Y]['Layers'], f'rien à retirer en {X},{Y}'
        front['Tiles'][X][Y] = copy.deepcopy(EMPTY)
        mapping['Front', X, Y] = None
        copy_block(0, None, X, Y)  # sable libre
    for (sx, sy), (X, Y) in L.FRONT_PLACE:
        assert not front['Tiles'][X][Y]['Layers'], f'cible occupée {X},{Y}'
        assert front_src[sx][sy]['Layers'], f'source vide {sx},{sy}'
        origin = mapping['Back', X, Y]
        assert origin is not None and 7 <= origin[1] <= 11 and 4 <= origin[0] <= 29, f'cible hors sable {X},{Y}'
        front['Tiles'][X][Y] = retarget(front_src[sx][sy])
        mapping['Front', X, Y] = (sx, sy)
        copy_block(sx, sy, X, Y)
    for (sx, sy), (X, Y) in L.BACK_OVERRIDES:
        origin = mapping['Back', X, Y]
        # Même rangée d'origine et même phase horizontale (période 8) : le motif
        # du sable reste continu, seule l'ombre change.
        assert origin is not None and origin[1] == sy and (origin[0] - sx) % 8 == 0, f'phase incompatible {sx},{sy} -> {X},{Y} (origine {origin})'
        back[X][Y] = retarget(back_src[sx][sy])
        mapping['Back', X, Y] = (sx, sy)
    ground['obstacles'] = obstacles
    # Entités : marqueur d'arrivée, sortie, seuil de la grotte ; pas de PNJ de scénario.
    entities = ground['Entities'][0]
    marker = copy.deepcopy(next(m for m in entities['Markers'] if m['EntName'] == 'Entrance'))
    marker['Collider'] = {k: L.ENTRANCE_MARKER[k] for k in ('X', 'Y', 'Width', 'Height')}
    marker['Direction'] = L.ENTRANCE_MARKER['Direction']
    objects = []
    for obj in entities['GroundObjects']:
        obj = copy.deepcopy(obj)
        if obj['EntName'] == 'Exit':
            obj['Collider'] = dict(L.EXIT_OBJECT)
        elif obj['EntName'] == 'Beach_Cave_Entrance':
            obj['Collider'] = dict(L.CAVE_OBJECT)
        else:
            continue
        objects.append(obj)
    assert len(objects) == 2
    entities['Markers'] = [marker]
    entities['GroundObjects'] = objects
    entities['Spawners'] = []
    entities['MapChars'] = []
    ground['AssetName'] = L.ASSET
    ground['Name'] = {'DefaultText': L.TITLE, 'LocalTexts': {}}
    ground['Comment'] = ('Lot plage_beach_cave_v1. Re-assemblage cellule par cellule de la plage EoSO (PMD Sky D01P11A) : '
                         'mer animee canonique 17 frames, entree de Beach Cave a gauche, sortie a droite. '
                         f'Sources epinglees {SOURCE_REPO}@{SOURCE_COMMIT[:12]}.')
    return ground, mapping


# --------------------------------------------------------------------------
# Rendus
# --------------------------------------------------------------------------
def alias():  # feuilles livrées -> feuilles sources (mêmes octets)
    return {new: old for old, new in SHEETS.items()}


def render_all(ground: dict, sheets: dict[str, TileSheet]) -> dict[str, Image.Image]:
    inv = alias()
    layers = {layer['Name']: layer for layer in ground['Layers']}
    out = {'Back': render_layer(layers['Back'], sheets, 0, inv), 'Front': render_layer(layers['Front'], sheets, 0, inv)}
    for f in range(17):
        out[f'Anim{f:02d}'] = render_layer(layers['Anim'], sheets, f, inv)
    for f in range(17):
        frame = out['Back'].copy()
        frame.alpha_composite(out[f'Anim{f:02d}'])
        frame.alpha_composite(out['Front'])
        out[f'Frame{f:02d}'] = frame
    return out


def scale(image: Image.Image, k: int) -> Image.Image:
    return image.resize((image.width * k, image.height * k), Image.NEAREST)


def save_png(image: Image.Image, path: Path, straight_alpha=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    (unpremultiply(image) if straight_alpha else image).save(path, optimize=True)


def write_renders(renders: dict[str, Image.Image], original: dict[str, Image.Image]):
    layers_dir = OUT / 'calques'
    save_png(renders['Back'], layers_dir / 'PLAGE_BC1_back_sable_rochers_fond.png')
    save_png(renders['Front'], layers_dir / 'PLAGE_BC1_front_rochers_palmiers.png')
    for f in range(17):
        anim = renders[f'Anim{f:02d}'].crop((0, 0, renders['Back'].width, 7 * CELL))
        save_png(anim, layers_dir / f'PLAGE_BC1_mer_frame{f:02d}.png')
    frames = [renders[f'Frame{f:02d}'].convert('RGB') for f in range(17)]
    frames[0].save(OUT / 'plage_bc1_grande_frame00.png', optimize=True)
    # Animation : 16 ticks/frame a 60 Hz = 266,67 ms ; GIF arrondi a 270 ms, WebP a 267 ms.
    big = [scale(fr, 2) for fr in frames]
    big[0].save(OUT / 'plage_bc1_grande_x2.gif', save_all=True, append_images=big[1:], duration=270, loop=0, optimize=False)
    frames[0].save(OUT / 'plage_bc1_grande_anim.webp', save_all=True, append_images=frames[1:], duration=267, loop=0, lossless=True, quality=100, method=6)
    # Planche : original (33 x 16) au-dessus de la nouvelle carte (45 x 20), frame 0, x2.
    a, b = scale(original['Frame00'].convert('RGB'), 2), big[0]
    sheet = Image.new('RGB', (max(a.width, b.width) + 20, a.height + b.height + 70), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), 'EoSO beach (PMD Sky D01P11A) - 33 x 16 cellules de 24 px - frame 0', fill=(255, 235, 120))
    sheet.paste(a, (10, 22))
    d.text((10, a.height + 40), f'plage_beach_cave_v1 - {L.NEW_W} x {L.NEW_H} cellules - memes cellules, meme animation 17 frames', fill=(255, 235, 120))
    sheet.paste(b, (10, a.height + 56))
    sheet.save(OUT / 'comparaison_avant_apres_x2.png', optimize=True)
    # Planche des phases de la mer (bande rangées 0-6), 6 phases.
    strip_h = 7 * CELL
    phases = [0, 3, 6, 9, 12, 15]
    board = Image.new('RGB', (renders['Back'].width, (strip_h + 14) * len(phases)), (24, 24, 28))
    for i, f in enumerate(phases):
        board.paste(renders[f'Frame{f:02d}'].convert('RGB').crop((0, 0, renders['Back'].width, strip_h)), (0, i * (strip_h + 14) + 14))
        ImageDraw.Draw(board).text((4, i * (strip_h + 14) + 1), f'frame {f:02d} / 16', fill=(255, 235, 120))
    board.save(OUT / 'phases_mer.png', optimize=True)


# --------------------------------------------------------------------------
# Tiled (24 px) : Back, Anim (tuiles animées 17 frames), Front
# --------------------------------------------------------------------------
def write_tiled(ground: dict, sheets: dict[str, TileSheet]):
    tiled = OUT / 'tiled'
    tiled.mkdir(parents=True, exist_ok=True)
    firstgid, tilesets, layers_json = 1, [], []
    gids = {}
    for old, new in SHEETS.items():
        sheet = sheets[old]
        image = Image.new('RGBA', (sheet.width * CELL, sheet.height * CELL), (0, 0, 0, 0))
        for (x, y), cell in sheet.images.items():
            image.paste(cell, (x * CELL, y * CELL))
        save_png(image, tiled / f'{new}.png')
        columns = sheet.width
        tiles_xml = ''
        if old == 'beach_animation':
            frames = 17
            per = columns // frames
            for y in range(sheet.height):
                for x in range(per):
                    seq = ''.join(f'<frame tileid="{y * columns + x + per * f}" duration="{round(FRAME_MS)}"/>' for f in range(frames))
                    tiles_xml += f'<tile id="{y * columns + x}"><animation>{seq}</animation></tile>'
        (tiled / f'{new}.tsx').write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="1.10" tiledversion="1.11.0" name="{new}" tilewidth="{CELL}" tileheight="{CELL}" '
            f'tilecount="{sheet.width * sheet.height}" columns="{columns}">\n <image source="{new}.png" width="{image.width}" height="{image.height}"/>\n'
            + (f' {tiles_xml}\n' if tiles_xml else '') + '</tileset>\n')
        tilesets.append({'firstgid': firstgid, 'source': f'{new}.tsx'})
        gids[new] = (firstgid, columns)
        firstgid += sheet.width * sheet.height
    for i, layer in enumerate(ground['Layers']):
        data = [0] * (L.NEW_W * L.NEW_H)
        for X, column in enumerate(layer['Tiles']):
            for Y, tile in enumerate(column):
                frames = cell_frames(tile)
                if frames:
                    sheet, tx, ty = frames[0]
                    first, columns = gids[sheet]
                    data[Y * L.NEW_W + X] = first + ty * columns + tx
        layers_json.append({'id': i + 1, 'name': layer['Name'], 'type': 'tilelayer', 'visible': True, 'opacity': 1,
                            'x': 0, 'y': 0, 'width': L.NEW_W, 'height': L.NEW_H, 'data': data})
    (tiled / 'plage_bc1_grande.tmj').write_text(json.dumps({
        'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal', 'renderorder': 'right-down',
        'width': L.NEW_W, 'height': L.NEW_H, 'tilewidth': CELL, 'tileheight': CELL, 'infinite': False,
        'nextlayerid': len(layers_json) + 1, 'nextobjectid': 1, 'tilesets': tilesets, 'layers': layers_json}, indent=1))


# --------------------------------------------------------------------------
# Projet PMDO
# --------------------------------------------------------------------------
def write_pack(ground: dict, provenance: dict):
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / 'Content/Tile').mkdir(parents=True)
    (PACK / 'Data/Ground').mkdir(parents=True)
    for old, new in SHEETS.items():
        shutil.copyfile(REF / f'EoSO__{old}.tile', PACK / f'Content/Tile/{new}.tile')
    spec = importlib.util.spec_from_file_location('index_tools', ROOT / 'source/pmdo_cote/INSTALLER.py')
    tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools)
    nodes = {}
    for path in sorted((PACK / 'Content/Tile').glob('*.tile')):
        with path.open('rb') as f:
            nodes[path.stem] = tools.read_node(f)
    assert len(nodes) == 3
    (PACK / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    document = {'Version': '0.8.12.0', 'Object': ground}
    (PACK / f'Data/Ground/{L.ASSET}.rsground').write_bytes(dump_ground(document))
    lua = f'''--[[
    init.lua — {L.ASSET}
    Squelette d'édition pour PMDO 0.8.12 (lot plage_beach_cave_v1).
    Les deux déclencheurs existent dans le Ground ; leurs destinations sont
    à renseigner dans le projet cible (aucune zone n'est présumée).
    Référence : Data/Script/eos/ground/beach/init.lua d'Explorers of Sky Origins
    (Exit -> crossroads_south / BeachEntranceMarker ; Beach_Cave_Entrance -> zone beach_cave).
]]--
local {L.ASSET} = {{}}

function {L.ASSET}.Init(map)
end

function {L.ASSET}.Enter(map)
  GAME:FadeIn(20)
end

function {L.ASSET}.Exit(map)
  GAME:FadeOut(false, 20)
end

function {L.ASSET}.Update(map)
end

function {L.ASSET}.GameSave(map)
end

function {L.ASSET}.GameLoad(map)
  GAME:FadeIn(20)
end

-- Bord droit : retour vers la carte précédente (à raccorder).
function {L.ASSET}.Exit_Touch(obj, activator)
  -- GAME:EnterGroundMap("<carte>", "<marqueur>")
end

-- Bouche de la grotte, à gauche : entrée du donjon (à raccorder).
function {L.ASSET}.Beach_Cave_Entrance_Touch(obj, activator)
  -- GAME:EnterZone("<zone>", 0, 0, 0)
end

return {L.ASSET}
'''
    for base in (PACK / 'Data/Script/ground' / L.ASSET, PACK / 'Data/Script' / L.NAMESPACE / 'ground' / L.ASSET):
        base.mkdir(parents=True, exist_ok=True)
        (base / 'init.lua').write_text(lua)
    ident = uuid.uuid5(uuid.NAMESPACE_URL, f'https://github.com/meromoonmeri/guilde-treehouse-pmd/{L.NAMESPACE}')
    (PACK / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Plage Beach Cave grande - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : une plage 45 x 20 re-assemblee a partir des cellules canoniques PMD Sky (EoSO beach), mer animee 17 frames, entree de Beach Cave. Pas une aventure jouable.</Description>
  <Namespace>{L.NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    script = (ROOT / 'source/pmdo_cote/INSTALLER.py').read_text()
    needle = '            relative = src.relative_to(source)\n'
    assert needle in script
    script = script.replace(needle, needle + '''            # L'index livre n'appartient qu'a ce projet autonome : ses en-tetes
            # sont fusionnes plus bas, jamais copies sur l'index d'un autre mod.
            if relative.as_posix() == 'Content/Tile/index.idx':
                continue
''').replace('index.avant_cote_v2.', 'index.avant_plage_bc1.').replace('index.cote_v2.', 'index.plage_bc1.')
    (PACK / 'INSTALLER.py').write_text(script)
    ns = L.NAMESPACE
    (PACK / 'OUVRIR_EDITEUR.bat').write_text(f'@echo off\r\ncd /d "%~dp0..\\.."\r\nif exist "PMDO.exe" (\r\n  start "" "PMDO.exe" -dev -quest {ns}\r\n) else if exist "PMDC.exe" (\r\n  start "" "PMDC.exe" -dev -quest {ns}\r\n) else (\r\n  echo Placer {ns} dans le dossier MODS de PMDO.\r\n  pause\r\n)\r\n')
    (PACK / 'OUVRIR_EDITEUR.sh').write_text(f'#!/usr/bin/env bash\nset -e\ncd -- "$(dirname -- "$0")/../.."\nif [[ -x ./PMDO ]]; then exec ./PMDO -dev -quest {ns}; fi\nif [[ -x ./PMDC ]]; then exec ./PMDC -dev -quest {ns}; fi\necho "Placer {ns} dans le dossier MODS de PMDO." >&2\nexit 1\n')
    (PACK / 'provenance').mkdir()
    (PACK / 'provenance/provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    shutil.copyfile(HERE / 'layout.py', PACK / 'provenance/layout.py')
    shutil.copyfile(HERE / 'SPEC.md', PACK / 'provenance/SPEC.md')


def write_zip():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in sorted(PACK.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                info = zipfile.ZipInfo(f'{L.NAMESPACE}/' + p.relative_to(PACK).as_posix(), (2026, 9, 20, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if p.suffix == '.sh' else 0o100644) << 16
                archive.writestr(info, p.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        names = [Path(n).name for n in archive.namelist()]
        assert len(names) == len(set(names)) or True  # doublons de nom possibles (init.lua x2), voulus


# --------------------------------------------------------------------------
# Provenance / journal
# --------------------------------------------------------------------------
def provenance_record() -> dict:
    files = {}
    for local, remote in SOURCE_FILES.items():
        path = REF / local
        files[local] = {'eoso_path': remote, 'bytes': path.stat().st_size, 'sha256': sha256(path), 'git_blob_sha1': git_blob_sha(path)}
    return {
        'source_repository': f'https://github.com/{SOURCE_REPO}', 'commit': SOURCE_COMMIT,
        'origin': 'Textures PMD Explorers of Sky (fond D01P11A « Beach ») telles que livrees par Explorers of Sky Origins (PMDO).',
        'files': files,
        'delivered_sheets': {new: {'copied_from': f'EoSO__{old}.tile', 'byte_identical': True} for old, new in SHEETS.items()},
        'method': 'ré-assemblage cellule par cellule (24 px) ; aucune image générée, recolorée, tournée ou redimensionnée',
        'unused_references': ['EoSO__dusk_beach.rsground', 'EoSO__DuskBeach.tile', 'EoSO__D01P11A_bpa5_0.tile'],
    }


def write_viewer(renders: dict[str, Image.Image], original: dict[str, Image.Image], mapping_stats: dict):
    def b64(image: Image.Image, straight=True) -> str:
        buf = io.BytesIO()
        (unpremultiply(image) if straight else image).save(buf, format='PNG', optimize=True)
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    images = {
        'back': b64(renders['Back']), 'front': b64(renders['Front']),
        'anim': [b64(renders[f'Anim{f:02d}'].crop((0, 0, renders['Back'].width, 7 * CELL))) for f in range(17)],
        'orig': [b64(original[f'Frame{f:02d}'].convert('RGB'), False) for f in range(17)],
    }
    template = (HERE / 'viewer.html').read_text()
    html = template.replace('__ZIP__', ZIP.name).replace('__DATA__', json.dumps({'images': images, 'w': L.NEW_W * CELL, 'h': L.NEW_H * CELL, 'cell': CELL,
                                                      'ow': L.ORIG_W * CELL, 'oh': L.ORIG_H * CELL, 'frameMs': FRAME_MS,
                                                      'stats': mapping_stats, 'zip': ZIP.name}, separators=(',', ':')))
    VIEW.write_text(html)
    (PACK / VIEW.name).write_text(html.replace(f'href="{ZIP.name}"', 'href="README.md"'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='rendu composite seul dans .cache/beach/')
    parser.add_argument('--zip-only', action='store_true', help='re-crée le ZIP depuis le projet déjà construit (après verify.py et runtime_test.py)')
    args = parser.parse_args()
    if args.zip_only:
        for name in ('verification.json', 'runtime_verification.json'):
            if (HERE / name).exists():
                data = json.loads((HERE / name).read_text())
                data.pop('zip_sha256', None)  # l'archive ne peut pas contenir son propre hachage
                (PACK / name).write_text(json.dumps(data, ensure_ascii=False, indent=1))
        write_zip()
        report_path = HERE / 'verification.json'
        if report_path.exists():
            report = json.loads(report_path.read_text())
            report['zip_sha256'] = hashlib.sha256(ZIP.read_bytes()).hexdigest()
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print('ZIP', ZIP.name, hashlib.sha256(ZIP.read_bytes()).hexdigest())
        return
    sheets = load_sheets()
    source = load_ground(REF / 'EoSO__beach.rsground')['Object']
    ground, mapping = assemble(source)
    filled = {layer['Name']: sum(1 for column in layer['Tiles'] for tile in column if tile['Layers']) for layer in ground['Layers']}
    stats = {
        'cells': L.NEW_W * L.NEW_H,
        'back_cells': filled['Back'], 'front_cells': filled['Front'], 'anim_cells': filled['Anim'],
        'removed': len(L.FRONT_REMOVE), 'placed': len(L.FRONT_PLACE), 'back_overrides': len(L.BACK_OVERRIDES),
    }
    renders = render_all(ground, sheets)
    if args.preview:
        cache = ROOT / '.cache/beach'
        cache.mkdir(parents=True, exist_ok=True)
        renders['Frame00'].convert('RGB').save(cache / 'preview_f0.png')
        scale(renders['Frame00'].convert('RGB'), 2).save(cache / 'preview_f0_x2.png')
        print('aperçu écrit dans .cache/beach/preview_f0_x2.png', stats)
        return
    original = {f'Frame{f:02d}': composite(source, sheets, f) for f in range(17)}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    write_renders(renders, original)
    write_tiled(ground, sheets)
    provenance = provenance_record()
    (HERE / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    write_pack(ground, provenance)
    (HERE / 'cell_mapping.json').write_text(json.dumps(
        {f'{layer}:{X},{Y}': (None if v is None else list(v)) for (layer, X, Y), v in sorted(mapping.items())}, separators=(',', ':')))
    write_viewer(renders, original, stats)
    shutil.copyfile(HERE / 'README.md', PACK / 'README.md') if (HERE / 'README.md').exists() else None
    write_zip()
    print('OK', stats, 'zip', ZIP.name, hashlib.sha256(ZIP.read_bytes()).hexdigest()[:16])


if __name__ == '__main__':
    main()
