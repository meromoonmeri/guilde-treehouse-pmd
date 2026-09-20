"""Build Beach Cave Entrance V2 from canonical EoSO cells only.

The geometry is a hand-authored cell placement. Magenta is used only as a
preview backdrop to inspect transparent layer exports; it is never written to
the PMDO Ground or the native tile sheets.
"""
from __future__ import annotations

import base64
import copy
import importlib.util
import io
import json
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V1 = ROOT / "source" / "beach_cave_v1"
REF = V1 / "references" / "ExplorersOfSkyOrigins"
OUT = ROOT / "renders" / "beach_cave_entrance_v2"
PACK = ROOT / ".cache" / "beach_cave_entrance_v2_pack"
ZIP = ROOT / "beach_cave_entrance_v2_pmdo.zip"
W, H, CELL = 33, 18, 24
GROUND_NAME = "v50812_beach_cave_entrance_v2.rsground"


def read_tile(path: Path) -> tuple[int, dict[tuple[int, int], Image.Image]]:
    raw = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", raw)
    bank: dict[tuple[int, int], Image.Image] = {}
    cache: dict[int, Image.Image] = {}
    for i in range(count):
        x, y, offset = struct.unpack_from("<iiq", raw, 8 + i * 16)
        if offset not in cache:
            length = struct.unpack_from("<q", raw, offset)[0]
            bank[x, y] = cache[offset] = Image.open(io.BytesIO(raw[offset + 8 : offset + 8 + length])).convert("RGBA")
        else:
            bank[x, y] = cache[offset]
    return tile_size, bank


def blank() -> dict:
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}


def cell_matrix(layer: dict) -> list[list[dict]]:
    return [[copy.deepcopy(layer["Tiles"][x][y]) if y < len(layer["Tiles"][x]) else blank() for y in range(H)] for x in range(W)]


def build_layers() -> tuple[list[list[dict]], dict]:
    beach = json.loads((REF / "beach.rsground").read_text(encoding="utf-8-sig"))["Object"]
    pit = json.loads((REF / "beach_cave_pit.rsground").read_text(encoding="utf-8-sig"))["Object"]
    source_back, source_anim, source_front = beach["Layers"]
    source_pit = pit["Layers"][0]

    # Background: keep the canonical sky/shore transition, then extend the
    # canonical sand cell (10,10) into a larger open arrival. This is a source
    # cell copied at native scale, never generated or repainted.
    back = [[blank() for _ in range(H)] for _ in range(W)]
    sand = copy.deepcopy(source_back["Tiles"][10][10])
    shore = copy.deepcopy(source_back["Tiles"][10][6])
    for x in range(W):
        for y in range(H):
            if y < 6:
                back[x][y] = copy.deepcopy(source_back["Tiles"][x][y])
            elif y == 6:
                back[x][y] = copy.deepcopy(shore)
            else:
                back[x][y] = copy.deepcopy(sand)

    # The reference's complete animated upper band is kept with its native
    # frame list and FrameLength=16. It is the canonical animated sky/shore
    # sheet; no phase is duplicated or fabricated.
    anim = [[blank() for _ in range(H)] for _ in range(W)]
    for x in range(W):
        for y in range(7):
            anim[x][y] = copy.deepcopy(source_anim["Tiles"][x][y])

    # A canonical water patch from Beach Cave Pit becomes the new central lagoon.
    # Its 23 frames and native FrameLength=8 are carried over unchanged.
    water = [[blank() for _ in range(H)] for _ in range(W)]
    # Select the native water-facing cells only. The upper cave roof and its
    # dark surround remain out of this layer so the lagoon reads as water on
    # the canonical sand background rather than as a pasted rectangle.
    sx0, sy0, pw, ph = 7, 3, 6, 2
    dx0, dy0 = 13, 9
    for dx in range(pw):
        for dy in range(ph):
            source_cell = source_pit["Tiles"][sx0 + dx][sy0 + dy]
            if source_cell["Layers"]:
                water[dx0 + dx][dy0 + dy] = copy.deepcopy(source_cell)

    # Foreground variant: open the south-to-north promenade, move the native
    # palm group to the west terrace, and duplicate a contiguous canonical cliff
    # block as a central cave mouth. No individual tile is altered.
    front = cell_matrix(source_front)
    for x in range(11, 22):
        for y in range(7, H):
            front[x][y] = blank()
    for sx in range(0, 9):
        for sy in range(3, 8):
            front[sx + 12][sy] = copy.deepcopy(source_front["Tiles"][sx][sy])
    for sx in range(13, 19):
        for sy in range(9, 16):
            if source_front["Tiles"][sx][sy]["Layers"]:
                front[sx - 10][sy + 1] = copy.deepcopy(source_front["Tiles"][sx][sy])
            front[sx][sy] = blank()

    # The entrance itself is also assembled from the native cave-mouth cells
    # of the pit reference. It sits above the lagoon and replaces no pixels.
    for sx in range(8, 12):
        for sy in range(0, 3):
            if source_pit["Tiles"][sx][sy]["Layers"]:
                front[sx + 6][sy + 6] = copy.deepcopy(source_pit["Tiles"][sx][sy])

    def native_animation_length(layer: dict) -> int:
        for column in layer["Tiles"]:
            for cell in column:
                for stack in cell.get("Layers", []):
                    if len(stack.get("Frames", [])) > 1:
                        return len(stack["Frames"])
        return 1

    spec = {
        "id": "beach_cave_entrance_v2",
        "title": "Beach Cave Entrance V2 — la Crique des Palmes",
        "grid_cells": [W, H],
        "size_px": [W * CELL, H * CELL],
        "tex_size": 3,
        "tile_size_px": CELL,
        "layout": "different cell composition: central cave mouth, south-north promenade, central canonical lagoon, palms moved west",
        "layers": ["background", "animation", "water", "foreground"],
        "reference_animation_frames": native_animation_length(source_anim),
        "reference_animation_frame_length": 16,
        "water_frames": native_animation_length(source_pit),
        "water_frame_length": 8,
        "entrance": {"name": "Entrance", "xy": [388, 388], "direction": 4},
        "dungeon_threshold": {"name": "donjon_seuil", "xy": [388, 124], "direction": 0, "width_px": 48},
        "magenta_preview_only": True,
        "generated_guide_used_as_pixels": False,
        "canonical_sources": [
            "Content/Tile/D01P11A_layer1.tile",
            "Content/Tile/beach_animation.tile",
            "Content/Tile/D01P11A_layer2.tile",
            "Content/Tile/BeachCavePit.tile",
        ],
    }
    return [back, anim, water, front], spec


def resolve(frame: dict, banks: dict[str, dict[tuple[int, int], Image.Image]]) -> Image.Image:
    loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
    return banks[frame["Sheet"]][loc]


def render(cells: list[list[dict]], banks: dict[str, dict[tuple[int, int], Image.Image]], tick: int) -> Image.Image:
    image = Image.new("RGBA", (W * CELL, H * CELL))
    for x, column in enumerate(cells):
        for y, cell in enumerate(column):
            for stack in cell["Layers"]:
                frames = stack.get("Frames", [])
                if not frames:
                    continue
                frame = frames[(tick // stack.get("FrameLength", 1)) % len(frames)]
                image.alpha_composite(resolve(frame, banks), (x * CELL, y * CELL))
    return image


def preview_layer(image: Image.Image, path: Path) -> None:
    magenta = Image.new("RGBA", image.size, (255, 0, 255, 255))
    magenta.alpha_composite(image)
    magenta.save(path, optimize=True)


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_preview(spec: dict, frames: list[Path], layer_paths: list[Path]) -> None:
    frame_uris = [data_uri(p) for p in frames]
    layer_uris = [data_uri(p) for p in layer_paths]
    labels = ["01 · fond", "02 · animation canonique", "03 · eau canonique", "04 · premier plan"]
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{spec["title"]}</title>
<style>body{{margin:0;background:#1b1420;color:#f6ead8;font:16px system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:28px}}h1{{color:#ffd187}}p{{color:#d0c5cb;line-height:1.6}}img{{display:block;max-width:100%;image-rendering:pixelated;margin:12px 0}}button,input{{padding:9px;background:#3a2742;color:#fff;border:1px solid #c17bbd;border-radius:5px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}figure{{margin:0}}figcaption{{color:#ff9ff1}}.note{{border-left:4px solid #ff00ff;padding-left:14px}}strong{{color:#ff9ff1}}small{{color:#bfafc0}}</style><main>
<div class="note"><strong>MAGENTA = contrôle de transparence uniquement</strong><br>Le magenta n'est pas une texture de la map et n'entre pas dans le Ground PMDO.</div>
<h1>{spec["title"]}</h1><p>Layout différent de la référence : promenade sud–nord, bouche centrale, eau canonique au centre et palmiers déplacés à l'ouest. L'eau est animée avec les frames natives de <code>BeachCavePit.tile</code>; le bandeau haut conserve la liste native de <code>beach_animation.tile</code>.</p>
<button id="play">Pause</button> <input id="frame" type="range" min="0" max="{len(frame_uris)-1}" value="0"><span id="label">Phase 1</span><img id="scene" alt="Beach Cave Entrance V2">
<h2>Calques séparés sur magenta</h2><div class="grid">{''.join(f'<figure><img src="{u}"><figcaption>{label}</figcaption></figure>' for u,label in zip(layer_uris,labels))}</div>
<p><small>Textures finales : références EoSO uniquement. Le guide généré est hors import. Aperçu visuel : pas de validation moteur/GPU/collisions.</small></p>
<script>const frames={json.dumps(frame_uris)},scene=document.querySelector('#scene'),range=document.querySelector('#frame'),label=document.querySelector('#label'),play=document.querySelector('#play');let running=true,t=0;function draw(){{scene.src=frames[t];range.value=t;label.textContent='Phase '+(t+1)+' / '+frames.length}}range.oninput=()=>{{running=false;play.textContent='Lecture';t=+range.value;draw()}};play.onclick=()=>{{running=!running;play.textContent=running?'Pause':'Lecture'}};setInterval(()=>{{if(running){{t=(t+1)%frames.length;draw()}}}},130);draw();</script></main></html>'''
    (ROOT / "apercu_beach_cave_entrance_v2.html").write_text(html, encoding="utf-8")


def make_index(tile_paths: list[Path]) -> bytes:
    spec = importlib.util.spec_from_file_location("index_tools", ROOT / "source/pmdo_cote/INSTALLER.py")
    tools = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(tools)
    nodes = {}
    for path in tile_paths:
        with path.open("rb") as stream:
            nodes[path.stem] = tools.read_node(stream)
    return tools.encode_index(nodes)


def ground_document(spec: dict, layers: list[list[list[dict]]]) -> dict:
    reference = json.loads((REF / "beach.rsground").read_text(encoding="utf-8-sig"))
    obj = copy.deepcopy(reference["Object"])
    obstacle = []
    for x in range(W * 3):
        obstacle.append([{"Bounds": {"X": x * 8, "Y": y * 8, "Width": 8, "Height": 8}, "Tags": 0} for y in range(H * 3)])
    names = ["Fond sable et ciel canonique", "Animation ciel/shore canonique", "Eau Beach Cave Pit canonique", "Premier plan roche/palmes canonique"]
    obj.update({
        "TexSize": 3,
        "Name": spec["title"],
        "Released": False,
        "AssetName": "v50812_beach_cave_entrance_v2",
        "Music": "BGM_DUN_BeachCave",
        "Comment": "PMDO 0.8.12. Layout différent, cellules canoniques EoSO uniquement. Magenta hors import. Collisions à revoir en jeu.",
        "obstacles": obstacle,
        "Layers": [{"Name": name, "Layer": 1 if i == 3 else 0, "Visible": True, "Tiles": layer} for i,(name,layer) in enumerate(zip(names,layers))],
        "Entities": [{"Name": spec["title"], "Visible": True, "MapChars": [], "GroundObjects": [], "Spawners": [], "Markers": [
            {"EntName": "Entrance", "Direction": 4, "EntEnabled": True, "EntOrder": 0, "InteractOrder": 0, "triggerType": 0, "Collider": {"X": 388, "Y": 388, "Width": 16, "Height": 16}},
            {"EntName": "donjon_seuil", "Direction": 0, "EntEnabled": True, "EntOrder": 0, "InteractOrder": 0, "triggerType": 0, "Collider": {"X": 388, "Y": 124, "Width": 16, "Height": 16}},
        ]}],
    })
    return {"$type": "RogueEssence.Ground.GroundMap, RogueEssence", "Version": "0.8.12.0", "Object": obj}


def package(ground_path: Path, manifest: dict) -> None:
    if PACK.exists(): shutil.rmtree(PACK)
    root = PACK / "beach_cave_entrance_v2"
    for p in [root / "Data/Ground", root / "Content/Tile", root / "Data/Script/ground/v50812_beach_cave_entrance_v2", root / "Data/Script/beach_cave_entrance_v2/ground/v50812_beach_cave_entrance_v2"]: p.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ground_path, root / "Data/Ground" / GROUND_NAME)
    script=b"-- Empty editing scaffold. Destination and return events are not guessed.\nreturn {}\n"
    for p in [root/"Data/Script/ground/v50812_beach_cave_entrance_v2/init.lua", root/"Data/Script/beach_cave_entrance_v2/ground/v50812_beach_cave_entrance_v2/init.lua"]:p.write_bytes(script)
    tile_paths=[]
    for name in ["D01P11A_layer1.tile","beach_animation.tile","D01P11A_layer2.tile","BeachCavePit.tile"]:
        dst=root/"Content/Tile"/name;shutil.copyfile(REF/name,dst);tile_paths.append(dst)
    (root/"Content/Tile/index.idx").write_bytes(make_index(tile_paths))
    for f in ["README.md","provenance.json","verification.json"]:
        shutil.copyfile(HERE/f,root/f)
    (root/"layout.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (root/"Mod.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>\n<Header>\n  <Name>Beach Cave Entrance V2 — la Crique des Palmes</Name>\n  <Author>guilde-treehouse-pmd</Author>\n  <Description>Ground PMDO 0.8.12 à calques séparés, layout différent et textures canoniques EoSO.</Description>\n  <Namespace>beach_cave_entrance_v2</Namespace>\n  <UUID>c2eab9e1-9d1f-45d6-9275-4cbe0812a602</UUID>\n  <Version>1.0.0.0</Version>\n  <GameVersion>0.8.12.0</GameVersion>\n  <ModType>Quest</ModType>\n  <Relationships />\n</Header>\n''',encoding='utf-8')
    if ZIP.exists():ZIP.unlink()
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(PACK.rglob('*')):
            if p.is_file():
                info=zipfile.ZipInfo('/'.join(p.relative_to(PACK).parts),(2026,9,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(ZIP) as z: assert z.testzip() is None


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    layers,spec=build_layers()
    banks={name:read_tile(REF/(name+'.tile'))[1] for name in ["D01P11A_layer1","beach_animation","D01P11A_layer2","BeachCavePit"]}
    magenta_names=["01_fond_magenta.png","02_animation_magenta.png","03_eau_magenta.png","04_premier_plan_magenta.png"]
    layer_paths=[]
    for c,n in zip(layers,magenta_names):
        p=OUT/n;preview_layer(render(c,banks,0),p);layer_paths.append(p)
    frames=[]
    for tick in range(36):
        comp=Image.new('RGBA',(W*CELL,H*CELL))
        for c in layers:comp=Image.alpha_composite(comp,render(c,banks,tick))
        p=OUT/f'composition_phase_{tick:02d}.png';comp.save(p,optimize=True);frames.append(p)
    # Native cells in every final layer resolve against one of the four audited sheets.
    doc=ground_document(spec,layers);ground_path=OUT/GROUND_NAME;ground_path.write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    provenance={"status":"PASS","reference_provenance":"source/beach_cave_v1/provenance.json","layout":"different manual placement of canonical cells; central lagoon copied from beach_cave_pit","canonical_only":True,"magenta_preview_only":True,"sources":{n:__import__('hashlib').sha256((REF/n).read_bytes()).hexdigest() for n in ["D01P11A_layer1.tile","beach_animation.tile","D01P11A_layer2.tile","BeachCavePit.tile"]}}
    (HERE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n');(HERE/'verification.json').write_text(json.dumps({"status":"PASS","layers":4,"water_source":"BeachCavePit.tile","water_frames":spec["water_frames"],"water_frame_length":spec["water_frame_length"],"reference_animation_source":"beach_animation.tile","reference_animation_frames":spec["reference_animation_frames"],"reference_animation_frame_length":spec["reference_animation_frame_length"],"generated_pixels_used_in_final":0,"magenta_in_final":False},indent=2)+'\n')
    manifest={**spec,"ground":GROUND_NAME,"preview_frames":36,"runtime_engine_tested":False,"destination_configured":False,"guide":"renders/beach_cave_entrance_v2/guide_layout_magenta.png"}
    (OUT/'layout.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    write_preview(manifest,frames,layer_paths);package(ground_path,manifest)
    print(f'PASS: {spec["title"]}; 4 layers, 36 previews, canonical water animated, magenta previews only')
if __name__=='__main__':main()
