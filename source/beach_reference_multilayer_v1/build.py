"""Package the audited Beach reference as a simple PMDO multi-layer map.

This variant intentionally does not invent a new composition. It copies the
reference Ground's three native layers and renders them separately so the
player sees the same canonical Beach material as an alternate map asset.
Generated images are not read or imported.
"""
from __future__ import annotations

import base64
import copy
import hashlib
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
REF = ROOT / "source" / "beach_cave_v1" / "references" / "ExplorersOfSkyOrigins"
OUT = ROOT / "renders" / "beach_reference_multilayer_v1"
PACK = ROOT / ".cache" / "beach_reference_multilayer_v1_pack"
ZIP = ROOT / "beach_reference_multilayer_v1_pmdo.zip"
GROUND_NAME = "v50812_beach_reference_multilayer_v1.rsground"
W, H, CELL = 33, 16, 24
SHEETS = ["D01P11A_layer1", "beach_animation", "D01P11A_layer2"]


def read_tile(path: Path) -> dict[tuple[int, int], Image.Image]:
    raw = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", raw)
    assert tile_size == CELL
    bank: dict[tuple[int, int], Image.Image] = {}
    cache: dict[int, Image.Image] = {}
    for i in range(count):
        x, y, offset = struct.unpack_from("<iiq", raw, 8 + i * 16)
        if offset not in cache:
            length = struct.unpack_from("<q", raw, offset)[0]
            cache[offset] = Image.open(io.BytesIO(raw[offset + 8 : offset + 8 + length])).convert("RGBA")
        bank[x, y] = cache[offset]
    return bank


def resolve(frame: dict, banks: dict[str, dict[tuple[int, int], Image.Image]]) -> Image.Image:
    sheet = frame["Sheet"]
    loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
    assert sheet in banks and loc in banks[sheet], (sheet, loc)
    return banks[sheet][loc]


def render_layer(layer: dict, banks: dict[str, dict[tuple[int, int], Image.Image]], tick: int) -> Image.Image:
    image = Image.new("RGBA", (W * CELL, H * CELL))
    for x, column in enumerate(layer["Tiles"]):
        for y, cell in enumerate(column):
            for stack in cell.get("Layers", []):
                frames = stack.get("Frames", [])
                if not frames:
                    continue
                frame = frames[(tick // stack.get("FrameLength", 1)) % len(frames)]
                image.alpha_composite(resolve(frame, banks), (x * CELL, y * CELL))
    return image


def compose(layers: list[dict], banks: dict[str, dict[tuple[int, int], Image.Image]], tick: int) -> Image.Image:
    scene = Image.new("RGBA", (W * CELL, H * CELL))
    for layer in layers:
        if layer.get("Visible", True):
            scene = Image.alpha_composite(scene, render_layer(layer, banks, tick))
    return scene


def preview_layer(image: Image.Image, path: Path) -> None:
    magenta = Image.new("RGBA", image.size, (255, 0, 255, 255))
    magenta.alpha_composite(image)
    magenta.save(path, optimize=True)


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_preview(manifest: dict, frames: list[Path], layer_paths: list[Path]) -> None:
    frame_uris = [data_uri(p) for p in frames]
    layer_uris = [data_uri(p) for p in layer_paths]
    labels = ["01 · fond canonique", "02 · animation canonique", "03 · premier plan canonique"]
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{manifest["title"]}</title>
<style>body{{margin:0;background:#17131d;color:#f8eddc;font:16px system-ui,sans-serif}}main{{max-width:1050px;margin:auto;padding:28px}}h1{{color:#ffd88e}}p{{color:#d2c6cf;line-height:1.6}}img{{display:block;max-width:100%;image-rendering:pixelated;margin:12px 0}}button,input{{padding:9px;background:#3b2b43;color:white;border:1px solid #c980c1;border-radius:5px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}figure{{margin:0}}figcaption{{color:#ffb4f4}}.note{{border-left:4px solid #ff00ff;padding-left:14px}}</style><main>
<div class="note"><strong>MAGENTA = fond de contrôle uniquement</strong><br>Il n'entre ni dans le Ground ni dans les feuilles .tile.</div>
<h1>{manifest["title"]}</h1><p>La composition est celle de la map Beach référente. La différence est l'organisation PMDO en trois calques séparés, utilisables comme variante de map alternative.</p>
<button id="play">Pause</button> <input id="frame" type="range" min="0" max="{len(frame_uris)-1}" value="0"><span id="label">Phase 1</span><img id="scene" alt="Map Beach référente en plusieurs calques">
<h2>Calques séparés</h2><div class="grid">{''.join(f'<figure><img src="{u}"><figcaption>{label}</figcaption></figure>' for u,label in zip(layer_uris,labels))}</div>
<p><small>Sources finales : Ground beach.rsground et feuilles EoSO natives. Aucun pixel généré, aucun recolorage, aucune rotation, aucun redimensionnement. Pas de validation moteur/GPU/collisions.</small></p>
<script>const frames={json.dumps(frame_uris)},scene=document.querySelector('#scene'),range=document.querySelector('#frame'),label=document.querySelector('#label'),play=document.querySelector('#play');let running=true,t=0;function draw(){{scene.src=frames[t];range.value=t;label.textContent='Phase '+(t+1)+' / '+frames.length}}range.oninput=()=>{{running=false;play.textContent='Lecture';t=+range.value;draw()}};play.onclick=()=>{{running=!running;play.textContent=running?'Pause':'Lecture'}};setInterval(()=>{{if(running){{t=(t+1)%frames.length;draw()}}}},130);draw();</script></main></html>'''
    (ROOT / "apercu_beach_reference_multilayer_v1.html").write_text(html, encoding="utf-8")


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


def marker(name: str, x: int, y: int, direction: int) -> dict:
    return {"EntName": name, "Direction": direction, "EntEnabled": True, "EntOrder": 0, "InteractOrder": 0, "triggerType": 0, "Collider": {"X": x, "Y": y, "Width": 16, "Height": 16}}


def ground_document(reference: dict) -> dict:
    obj = copy.deepcopy(reference["Object"])
    obj.update({
        "Name": "Beach — référence en calques alternatifs",
        "Released": False,
        "AssetName": "v50812_beach_reference_multilayer_v1",
        "Music": "BGM_DUN_BeachCave",
        "Comment": "PMDO 0.8.12. Composition exacte de beach.rsground, exposée en trois calques canoniques. Aucun pixel généré. Destination et collisions à revoir en jeu.",
        "Layers": copy.deepcopy(reference["Object"]["Layers"]),
        "Entities": [{"Name": "Beach — référence en calques alternatifs", "Visible": True, "MapChars": [], "GroundObjects": [], "Spawners": [], "Markers": [marker("Entrance", 244, 364, 4), marker("donjon_seuil", 220, 4, 0)]}],
    })
    return {"$type": "RogueEssence.Ground.GroundMap, RogueEssence", "Version": "0.8.12.0", "Object": obj}


def package(ground_path: Path, manifest: dict) -> None:
    if PACK.exists():
        shutil.rmtree(PACK)
    root = PACK / "beach_reference_multilayer_v1"
    for path in [root / "Data/Ground", root / "Content/Tile", root / "Data/Script/ground/v50812_beach_reference_multilayer_v1", root / "Data/Script/beach_reference_multilayer_v1/ground/v50812_beach_reference_multilayer_v1"]:
        path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ground_path, root / "Data/Ground" / GROUND_NAME)
    script = b"-- Empty editing scaffold. Destination and return events are intentionally not guessed.\nreturn {}\n"
    for path in [root / "Data/Script/ground/v50812_beach_reference_multilayer_v1/init.lua", root / "Data/Script/beach_reference_multilayer_v1/ground/v50812_beach_reference_multilayer_v1/init.lua"]:
        path.write_bytes(script)
    tile_paths = []
    for name in [f"{sheet}.tile" for sheet in SHEETS]:
        dst = root / "Content/Tile" / name
        shutil.copyfile(REF / name, dst)
        tile_paths.append(dst)
    (root / "Content/Tile/index.idx").write_bytes(make_index(tile_paths))
    for filename in ["README.md", "provenance.json", "verification.json"]:
        shutil.copyfile(HERE / filename, root / filename)
    (root / "layout.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (root / "Mod.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>\n<Header>\n  <Name>Beach — référence en calques alternatifs</Name>\n  <Author>guilde-treehouse-pmd</Author>\n  <Description>Composition Beach référente EoSO organisée en trois calques PMDO.</Description>\n  <Namespace>beach_reference_multilayer_v1</Namespace>\n  <UUID>1c795fe2-8156-4f73-a7f4-e9a31d2d6007</UUID>\n  <Version>1.0.0.0</Version>\n  <GameVersion>0.8.12.0</GameVersion>\n  <ModType>Quest</ModType>\n  <Relationships />\n</Header>\n''', encoding="utf-8")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PACK.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo("/".join(path.relative_to(PACK).parts), (2026, 9, 20, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None


def main() -> None:
    reference = json.loads((REF / "beach.rsground").read_text(encoding="utf-8-sig"))
    obj = reference["Object"]
    assert obj["TexSize"] * 8 == CELL
    assert len(obj["Layers"]) == 3
    assert len(obj["Layers"][0]["Tiles"]) == W and len(obj["Layers"][0]["Tiles"][0]) == H
    banks = {sheet: read_tile(REF / f"{sheet}.tile") for sheet in SHEETS}
    used = set()
    for layer in obj["Layers"]:
        for column in layer["Tiles"]:
            for cell in column:
                for stack in cell.get("Layers", []):
                    for frame in stack["Frames"]:
                        used.add(frame["Sheet"])
    assert used == set(SHEETS)
    OUT.mkdir(parents=True, exist_ok=True)
    layer_names = ["01_fond_magenta.png", "02_animation_magenta.png", "03_premier_plan_magenta.png"]
    layer_paths = []
    for layer, filename in zip(obj["Layers"], layer_names):
        path = OUT / filename
        preview_layer(render_layer(layer, banks, 0), path)
        layer_paths.append(path)
    frames = []
    for tick in range(17):
        path = OUT / f"composition_phase_{tick:02d}.png"
        compose(obj["Layers"], banks, tick).save(path, optimize=True)
        frames.append(path)
    ground_path = OUT / GROUND_NAME
    ground_path.write_text(json.dumps(ground_document(reference), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    manifest = {
        "id": "beach_reference_multilayer_v1",
        "title": "Beach — référence en calques alternatifs",
        "ground": GROUND_NAME,
        "grid_cells": [W, H],
        "size_px": [W * CELL, H * CELL],
        "tex_size": 3,
        "tile_size_px": CELL,
        "layers": ["Back canonique", "Anim canonique", "Front canonique"],
        "reference_ground": "source/beach_cave_v1/references/ExplorersOfSkyOrigins/beach.rsground",
        "animation_source": "beach_animation.tile",
        "animation_frames": 17,
        "animation_frame_length": 16,
        "generated_pixels_used_in_final": 0,
        "magenta_preview_only": True,
        "runtime_engine_tested": False,
        "destination_configured": False,
    }
    (OUT / "layout.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_preview(manifest, frames, layer_paths)
    hashes = {f"{sheet}.tile": hashlib.sha256((REF / f"{sheet}.tile").read_bytes()).hexdigest() for sheet in SHEETS}
    (HERE / "provenance.json").write_text(json.dumps({"status": "PASS", "reference": "beach.rsground", "canonical_only": True, "generated_guide_used_as_pixels": False, "sheets": hashes}, ensure_ascii=False, indent=2) + "\n")
    (HERE / "verification.json").write_text(json.dumps({"status": "PASS", "layers": 3, "grid_cells": [W, H], "animation_source": "beach_animation.tile", "animation_frames": 17, "animation_frame_length": 16, "generated_pixels_used_in_final": 0, "magenta_in_final": False, "runtime_engine_tested": False}, indent=2) + "\n")
    package(ground_path, manifest)
    print(f"PASS: {manifest['title']}; exact reference composition in 3 native layers; {len(frames)} animation previews")


if __name__ == "__main__":
    main()
