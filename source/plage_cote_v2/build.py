#!/usr/bin/env python3
"""Construit le lot plage_cote_v2 : deux Grounds PMDO 0.8.12 (« crique »
36 x 23 et « anse » 45 x 25 cellules de 24 px) ré-assemblés cellule par
cellule depuis Brine_Cave_Entrance (EoSO), feuille `.tile` copiée octet pour
octet, mer animée canonique 15 frames, rendus, Tiled, aperçu HTML, projet
PMDO installable et ZIP.

    .venv/bin/python source/plage_cote_v2/build.py            # tout
    .venv/bin/python source/plage_cote_v2/build.py --preview  # rendus seuls
    .venv/bin/python source/plage_cote_v2/build.py --zip-only # re-ZIP après verify/runtime

Aucune cellule n'est dessinée : chaque cellule copie la séquence de frames
d'une cellule de la carte EoSO (voir layout.py). Les images générées du
dossier references/ sont des guides de composition, jamais des tuiles.
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

OUT = ROOT / 'exports/plage_cote_v2'
PACK = Path.home() / '.cache/plage_cote_v2_pack'
ZIP = ROOT / 'plage_cote_v2_pmdo_0812.zip'
VIEW = ROOT / 'apercu_plage_cote_v2.html'
FRAME_MS = 8 * 1000 / 60  # FrameLength 8 ticks à 60 Hz = 133,3 ms
NAMES = ('crique', 'anse')

SOURCE_COMMIT = 'bed944992c32e7e7927cc3480c72edb0b1782e26'
SOURCE_REPO = 'Minemaker0430/ExplorersOfSkyOrigins'
SOURCE_FILES = {
    'EoSO__Brine_Cave_Entrance.rsground': 'Data/Ground/Brine_Cave_Entrance.rsground',
    'EoSO__Brine_Cave_Entrance.tile': 'Content/Tile/Brine Cave Entrance.tile',
}
SHEET_NEW = 'PLAGE_CV2_BRINE'
NAMESPACE = 'plage_cote_v2'


# --------------------------------------------------------------------------
# Assemblage
# --------------------------------------------------------------------------
def retarget(tile: dict) -> dict:
    tile = copy.deepcopy(tile)
    for anim in tile['Layers']:
        for frame in anim['Frames']:
            frame['Sheet'] = SHEETS[frame['Sheet']]
    return tile


def assemble(source: dict, name: str) -> tuple[dict, dict[tuple[int, int], tuple[int, int]]]:
    """Ground assemblé pour le layout `name` + correspondances cellule -> source."""
    spec = L.LAYOUTS[name]
    W, H = L.dims(name)
    mapping = L.source_of(name)
    ground = copy.deepcopy(source)
    layer = ground['Layers'][0]
    src_tiles = layer['Tiles']
    layer['Tiles'] = [[retarget(src_tiles[mapping[X, Y][0]][mapping[X, Y][1]])
                       for Y in range(H)] for X in range(W)]
    # Obstacles 8 px : mêmes correspondances que les cellules (blocs 3 x 3).
    src_obst = source['obstacles']
    obstacles = [[None] * (H * 3) for _ in range(W * 3)]
    for X in range(W):
        for Y in range(H):
            sx, sy = mapping[X, Y]
            for i in range(3):
                for j in range(3):
                    obstacles[X * 3 + i][Y * 3 + j] = {
                        'Bounds': {'X': (X * 3 + i) * 8, 'Y': (Y * 3 + j) * 8, 'Width': 8, 'Height': 8},
                        'Tags': src_obst[sx * 3 + i][sy * 3 + j]['Tags']}
    ground['obstacles'] = obstacles
    ground['Entities'] = L.entities(name)
    ground['AssetName'] = spec['asset']
    ground['Name'] = {'DefaultText': spec['title'], 'LocalTexts': {}}
    ground['Comment'] = (f'Lot plage_cote_v2 ({name}). Re-assemblage cellule par cellule de '
                         f'Brine_Cave_Entrance (PMD Sky) : grotte a gauche, mer animee 15 frames en bas, '
                         f'sortie a droite. Sources epinglees {SOURCE_REPO}@{SOURCE_COMMIT[:12]}.')
    return ground, mapping


# --------------------------------------------------------------------------
# Rendus
# --------------------------------------------------------------------------
def alias():  # feuilles livrées -> feuilles sources (mêmes octets)
    return {new: old for old, new in SHEETS.items()}


def render_all(ground: dict, sheets: dict[str, TileSheet]) -> dict[str, Image.Image]:
    inv = alias()
    out = {'Layer': render_layer(ground['Layers'][0], sheets, 0, inv)}
    for f in range(L.FRAMES):
        out[f'Frame{f:02d}'] = composite(ground, sheets, f, inv)
    return out


def scale(image: Image.Image, k: int) -> Image.Image:
    return image.resize((image.width * k, image.height * k), Image.NEAREST)


def save_png(image: Image.Image, path: Path, straight_alpha=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    (unpremultiply(image) if straight_alpha else image).save(path, optimize=True)


def write_renders(renders: dict[str, dict[str, Image.Image]], source_frames: list[Image.Image]):
    for name in NAMES:
        base = OUT / name
        r = renders[name]
        save_png(r['Layer'], base / f'PLAGE_CV2_{name}_calque.png')
        save_png(r['Frame00'], base / f'plage_cv2_{name}_frame00.png')
        frames = [r[f'Frame{f:02d}'].convert('RGB') for f in range(L.FRAMES)]
        big = [scale(fr, 2) for fr in frames]
        big[0].save(base / f'plage_cv2_{name}_x2.gif', save_all=True, append_images=big[1:],
                    duration=round(FRAME_MS), loop=0, optimize=False)
        frames[0].save(base / f'plage_cv2_{name}_anim.webp', save_all=True, append_images=frames[1:],
                       duration=round(FRAME_MS), loop=0, lossless=True, quality=100, method=6)
    # Planche : source puis les deux layouts, frame 0, x2.
    rows = [(scale(source_frames[0].convert('RGB'), 2), 'EoSO Brine_Cave_Entrance - 27 x 21 cellules de 24 px - frame 0'),
            (scale(renders['crique']['Frame00'].convert('RGB'), 2), 'plage_cote_v2 « crique » - 36 x 23 - memes cellules, mer animee 15 frames'),
            (scale(renders['anse']['Frame00'].convert('RGB'), 2), 'plage_cote_v2 « anse » - 45 x 25 - module [17..26) x2, mer animee 15 frames')]
    width = max(im.width for im, _ in rows) + 20
    height = sum(im.height for im, _ in rows) + 24 * len(rows) + 30
    sheet = Image.new('RGB', (width, height), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    y = 6
    for im, label in rows:
        d.text((10, y), label, fill=(255, 235, 120))
        y += 18
        sheet.paste(im, (10, y))
        y += im.height + 6
    sheet.save(OUT / 'comparaison_avant_apres.png', optimize=True)


# --------------------------------------------------------------------------
# Tiled
# --------------------------------------------------------------------------
def write_tiled(grounds: dict[str, dict], sheets: dict[str, TileSheet]):
    tiled = OUT / 'tiled'
    tiled.mkdir(parents=True, exist_ok=True)
    sheet = sheets['Brine Cave Entrance']
    new = SHEETS['Brine Cave Entrance']
    image = Image.new('RGBA', (sheet.width * CELL, sheet.height * CELL), (0, 0, 0, 0))
    for (x, y), cell in sheet.images.items():
        image.paste(cell, (x * CELL, y * CELL))
    save_png(image, tiled / f'{new}.png')
    columns = sheet.width
    frames_ms = round(FRAME_MS)
    tiles_xml = ''
    for y in range(sheet.height):
        for x in range(L.ORIG_W):
            if (x, y) not in sheet.blobs:
                continue
            seq = ''.join(f'<frame tileid="{y * columns + x + L.ORIG_W * f}" duration="{frames_ms}"/>' for f in range(L.FRAMES))
            tiles_xml += f'<tile id="{y * columns + x}"><animation>{seq}</animation></tile>'
    (tiled / f'{new}.tsx').write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="1.10" tiledversion="1.11.0" name="{new}" '
        f'tilewidth="{CELL}" tileheight="{CELL}" tilecount="{sheet.width * sheet.height}" columns="{columns}">\n'
        f' <image source="{new}.png" width="{image.width}" height="{image.height}"/>\n {tiles_xml}\n</tileset>\n')
    for name in NAMES:
        ground = grounds[name]
        W, H = L.dims(name)
        data = [0] * (W * H)
        for X, column in enumerate(ground['Layers'][0]['Tiles']):
            for Y, tile in enumerate(column):
                frames_ = cell_frames(tile)
                if frames_:
                    _, tx, ty = frames_[0]
                    data[Y * W + X] = 1 + ty * columns + tx
        (tiled / f'plage_cv2_{name}.tmj').write_text(json.dumps({
            'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal',
            'renderorder': 'right-down', 'width': W, 'height': H, 'tilewidth': CELL, 'tileheight': CELL,
            'infinite': False, 'nextlayerid': 2, 'nextobjectid': 1,
            'tilesets': [{'firstgid': 1, 'source': f'{new}.tsx'}],
            'layers': [{'id': 1, 'name': ground['Layers'][0]['Name'], 'type': 'tilelayer', 'visible': True,
                        'opacity': 1, 'x': 0, 'y': 0, 'width': W, 'height': H, 'data': data}]}, indent=1))


# --------------------------------------------------------------------------
# Aperçu HTML
# --------------------------------------------------------------------------
def write_viewer(renders: dict[str, dict[str, Image.Image]]):
    def b64(image: Image.Image, straight=True) -> str:
        buf = io.BytesIO()
        (unpremultiply(image) if straight else image).save(buf, format='PNG', optimize=True)
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

    data = {}
    for name in NAMES:
        W, H = L.dims(name)
        data[name] = {'w': W * CELL, 'h': H * CELL, 'cells': [W, H],
                      'frames': [b64(renders[name][f'Frame{f:02d}'].convert('RGB'), False) for f in range(L.FRAMES)]}
    html = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>plage_cote_v2 — aperçu animé</title>
<style>body{background:#141418;color:#ddd;font-family:system-ui,sans-serif;margin:20px}
h1{font-size:20px;color:#ffeb78}.note{color:#7adc8c;font-size:13px;margin:6px 0 18px}
.blk{margin-bottom:28px}.lbl{font-size:14px;margin-bottom:6px}
canvas{image-rendering:pixelated;border:1px solid #333;max-width:100%}</style></head><body>
<h1>__TITRE__</h1>
<div class="note">guide de provenance : cellules canoniques EoSO Brine_Cave_Entrance (bed94499) —
aperçu recomposé depuis le projet livré ; ni rendu GPU ni validation moteur (voir verification.json).<br>
Images générées du lot = guides de composition uniquement, aucune tuile n'en provient.</div>
<div id="root"></div><script>
const DATA=__DATA__;const MS=133.33;const root=document.getElementById('root');
for(const[name,d]of Object.entries(DATA)){
 const blk=document.createElement('div');blk.className='blk';
 blk.innerHTML='<div class="lbl"><b>'+name+'</b> — '+d.cells[0]+'×'+d.cells[1]+' cellules de 24 px ('+d.w+'×'+d.h+' px)</div>';
 const c=document.createElement('canvas');c.width=d.w;c.height=d.h;blk.appendChild(c);root.appendChild(blk);
 const ctx=c.getContext('2d');const imgs=d.frames.map(s=>{const i=new Image();i.src=s;return i;});let f=0;
 setInterval(()=>{f=(f+1)%imgs.length;ctx.drawImage(imgs[f],0,0);},MS);ctx.drawImage(imgs[0],0,0);
}
</script></body></html>"""
    titre = 'plage_cote_v2 — ' + ' et '.join(
        f"{name} ({L.dims(name)[0]}×{L.dims(name)[1]})" for name in NAMES) + ', mer animée 15 frames'
    html = html.replace('__TITRE__', titre)
    html = html.replace('__DATA__', json.dumps(data, separators=(',', ':')))
    VIEW.write_text(html)
    shutil.copyfile(VIEW, PACK / VIEW.name)


# --------------------------------------------------------------------------
# Projet PMDO
# --------------------------------------------------------------------------
def write_pack(grounds: dict[str, dict], provenance: dict):
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / 'Content/Tile').mkdir(parents=True)
    (PACK / 'Data/Ground').mkdir(parents=True)
    for old, new in SHEETS.items():
        shutil.copyfile(REF / f"EoSO__{old.replace(' ', '_')}.tile", PACK / f'Content/Tile/{new}.tile')
    spec = importlib.util.spec_from_file_location('index_tools', ROOT / 'source/pmdo_cote/INSTALLER.py')
    tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools)
    nodes = {}
    for path in sorted((PACK / 'Content/Tile').glob('*.tile')):
        with path.open('rb') as f:
            nodes[path.stem] = tools.read_node(f)
    assert len(nodes) == 1
    (PACK / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    for name in NAMES:
        asset = L.LAYOUTS[name]['asset']
        (PACK / f'Data/Ground/{asset}.rsground').write_bytes(dump_ground({'Version': '0.8.12.0', 'Object': grounds[name]}))
        lua = f'''--[[
    init.lua — {asset}
    Squelette d'édition pour PMDO 0.8.12 (lot plage_cote_v2, layout « {name} »).
    Les deux déclencheurs existent dans le Ground ; leurs destinations sont
    à renseigner dans le projet cible (aucune zone n'est présumée).
    Référence : Data/Script/eos/ground/beach/init.lua d'Explorers of Sky Origins
    (Exit -> crossroads_south ; Beach_Cave_Entrance -> zone beach_cave).
]]--
local {asset} = {{}}

function {asset}.Init(map)
end

function {asset}.Enter(map)
  GAME:FadeIn(20)
end

function {asset}.Exit(map)
  GAME:FadeOut(false, 20)
end

function {asset}.Update(map)
end

function {asset}.GameSave(map)
end

function {asset}.GameLoad(map)
  GAME:FadeIn(20)
end

-- Bord droit : retour vers la carte précédente (à raccorder).
function {asset}.Exit_Touch(obj, activator)
  -- GAME:EnterGroundMap("<carte>", "<marqueur>")
end

-- Bouche de la grotte, à gauche : entrée du donjon (à raccorder).
function {asset}.Beach_Cave_Entrance_Touch(obj, activator)
  -- GAME:EnterZone("<zone>", 0, 0, 0)
end

return {asset}
'''
        for base in (PACK / 'Data/Script/ground' / asset, PACK / 'Data/Script' / NAMESPACE / 'ground' / asset):
            base.mkdir(parents=True, exist_ok=True)
            (base / 'init.lua').write_text(lua)
    ident = uuid.uuid5(uuid.NAMESPACE_URL, f'https://github.com/meromoonmeri/guilde-treehouse-pmd/{NAMESPACE}')
    (PACK / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Plage cote v2 - crique et anse, mer en bas (Atelier 0.8.12)</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : deux layouts (36 x 23 et 45 x 25) re-assembles a partir des cellules canoniques de Brine_Cave_Entrance (PMD Sky, EoSO), mer animee 15 frames en bas, grotte a gauche. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
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
''').replace('index.avant_cote_v2.', 'index.avant_cv2.').replace('index.cote_v2.', 'index.cv2.')
    (PACK / 'INSTALLER.py').write_text(script)
    ns = NAMESPACE
    bat = '@echo off\r\ncd /d "%~dp0..\\.."\r\nif exist "PMDO.exe" (\r\n  start "" "PMDO.exe" -dev -quest {ns}\r\n) else if exist "PMDC.exe" (\r\n  start "" "PMDC.exe" -dev -quest {ns}\r\n) else (\r\n  echo Placer {ns} dans le dossier MODS de PMDO.\r\n  pause\r\n)\r\n'
    (PACK / 'OUVRIR_EDITEUR.bat').write_text(bat)
    (PACK / 'OUVRIR_EDITEUR.sh').write_text(f'#!/usr/bin/env bash\nset -e\ncd -- "$(dirname -- "$0")/../.."\nif [[ -x ./PMDO ]]; then exec ./PMDO -dev -quest {ns}; fi\nif [[ -x ./PMDC ]]; then exec ./PMDC -dev -quest {ns}; fi\necho "Placer {ns} dans le dossier MODS de PMDO." >&2\nexit 1\n')
    (PACK / 'provenance').mkdir()
    (PACK / 'provenance/provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    for f in ('layout.py', 'SPEC.md', 'ANALYSE.md'):
        shutil.copyfile(HERE / f, PACK / 'provenance' / f)
    if (HERE / 'README.md').exists():
        shutil.copyfile(HERE / 'README.md', PACK / 'README.md')


def write_zip():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in sorted(PACK.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                info = zipfile.ZipInfo(f'{NAMESPACE}/' + p.relative_to(PACK).as_posix(), (2026, 9, 20, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if p.suffix == '.sh' else 0o100644) << 16
                archive.writestr(info, p.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None


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
        'origin': ('Textures PMD Explorers of Sky (cave cotiere Brine_Cave_Entrance : grotte a gauche, mer en bas) '
                   'telles que livrees par Explorers of Sky Origins (PMDO). La mer de la plage D01P11A n\'existe '
                   'qu\'en haut de carte : la placer en bas exigerait une rotation, interdite — d\'ou ce choix de source.'),
        'files': files,
        'delivered_sheets': {new: {'copied_from': f'EoSO__{old}.tile', 'byte_identical': True} for old, new in SHEETS.items()},
        'method': 'ré-assemblage cellule par cellule (24 px, flipbooks 15 frames entiers) ; aucune image générée, recolorée, tournée ou redimensionnée',
        'composition_guides': ['references/candidats_mer_autre_cote.png', 'references/guide_composition_L1.png', 'references/guide_composition_L2.png'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='rendus composites seuls dans .cache/plage_cote_v2/')
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
    source = load_ground(REF / 'EoSO__Brine_Cave_Entrance.rsground')['Object']
    grounds, mappings, renders = {}, {}, {}
    for name in NAMES:
        grounds[name], mappings[name] = assemble(source, name)
        renders[name] = render_all(grounds[name], sheets)
        filled = sum(1 for col in grounds[name]['Layers'][0]['Tiles'] for t in col if t['Layers'])
        print(f'{name}: {L.dims(name)} cellules, {filled} cellules remplies, '
              f'mer animée rangées {L.rive_y(name) + 1}..{L.dims(name)[1] - 1}')
    if args.preview:
        cache = ROOT / '.cache/plage_cote_v2'
        cache.mkdir(parents=True, exist_ok=True)
        for name in NAMES:
            renders[name]['Frame00'].convert('RGB').save(cache / f'{name}_f0.png')
        print('aperçus écrits dans .cache/plage_cote_v2/')
        return
    source_frames = [composite(source, sheets, f) for f in range(L.FRAMES)]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    write_renders(renders, source_frames)
    write_tiled(grounds, sheets)
    provenance = provenance_record()
    (HERE / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    write_pack(grounds, provenance)
    (HERE / 'cell_mapping.json').write_text(json.dumps(
        {f'{name}:{X},{Y}': list(v) for name in NAMES for (X, Y), v in sorted(mappings[name].items())},
        separators=(',', ':')))
    write_viewer(renders)
    write_zip()
    stats = {name: {'dims': L.dims(name), 'cells': L.dims(name)[0] * L.dims(name)[1]} for name in NAMES}
    print('OK', json.dumps(stats), 'zip', ZIP.name, hashlib.sha256(ZIP.read_bytes()).hexdigest()[:16])


if __name__ == '__main__':
    main()
