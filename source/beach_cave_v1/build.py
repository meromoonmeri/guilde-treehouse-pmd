"""Repackage the canonical EoSO Beach Cave pit as a PMDO 0.8.12 Ground.

The requested artistic constraint is absolute here: the final Ground keeps the
reference composition and every native 24px BeachCavePit payload. The generated
composition image is never read. No tile is cropped, recolored, rotated,
resampled or synthesized.
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
REF = HERE / "references" / "ExplorersOfSkyOrigins"
OUT = ROOT / "renders" / "beach_cave_v1"
PACK = ROOT / ".cache" / "beach_cave_anse_des_marees_pack"
ZIP = ROOT / "beach_cave_anse_des_marees_pmdo.zip"
GROUND_NAME = "v50812_beach_cave_anse_des_marees.rsground"


def read_tile(path: Path) -> tuple[int, dict[tuple[int, int], Image.Image]]:
    raw = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", raw)
    bank: dict[tuple[int, int], Image.Image] = {}
    cache: dict[int, Image.Image] = {}
    for i in range(count):
        x, y, offset = struct.unpack_from("<iiq", raw, 8 + i * 16)
        if offset not in cache:
            length = struct.unpack_from("<q", raw, offset)[0]
            cache[offset] = Image.open(io.BytesIO(raw[offset + 8 : offset + 8 + length])).convert("RGBA")
        bank[x, y] = cache[offset]
    return tile_size, bank


def resolve_frame(frame: dict, bank: dict[tuple[int, int], Image.Image]) -> Image.Image:
    loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
    if frame["Sheet"] != "BeachCavePit" or loc not in bank:
        raise AssertionError(f"non-canonical or unresolved frame: {frame}")
    return bank[loc]


def compose(obj: dict, bank: dict[tuple[int, int], Image.Image], tick: int) -> Image.Image:
    cell = obj["TexSize"] * 8
    width = len(obj["Layers"][0]["Tiles"]) * cell
    height = len(obj["Layers"][0]["Tiles"][0]) * cell
    scene = Image.new("RGBA", (width, height))
    for layer in obj["Layers"]:
        layer_image = Image.new("RGBA", scene.size)
        for x, column in enumerate(layer["Tiles"]):
            for y, tile in enumerate(column):
                for stack in tile.get("Layers", []):
                    frames = stack.get("Frames", [])
                    if not frames:
                        continue
                    duration = stack.get("FrameLength", 1)
                    frame = frames[(tick // duration) % len(frames)]
                    layer_image.alpha_composite(resolve_frame(frame, bank), (x * cell, y * cell))
        if layer.get("Visible", True):
            scene = Image.alpha_composite(scene, layer_image)
    return scene


def marker(name: str, x: int, y: int, direction: int) -> dict:
    return {
        "EntName": name,
        "Direction": direction,
        "EntEnabled": True,
        "EntOrder": 0,
        "InteractOrder": 0,
        "triggerType": 0,
        "Collider": {"X": x, "Y": y, "Width": 16, "Height": 16},
    }


def ground_document(reference: dict) -> dict:
    obj = copy.deepcopy(reference["Object"])
    obj.update({
        "TexSize": 3,
        "Name": "Beach Cave — l’Anse des Marées",
        "Released": False,
        "AssetName": "v50812_beach_cave_anse_des_marees",
        "Music": "BGM_DUN_BeachCave",
        "Comment": (
            "PMDO 0.8.12. Exact EoSO Beach Cave native composition and 24px cells. "
            "No generated pixels are imported. Destination and collisions require in-engine review."
        ),
        # The reference's single Terrain layer is kept intact; inventing a split
        # would alter draw order and no longer be a canonical reconstruction.
        "Layers": copy.deepcopy(reference["Object"]["Layers"]),
        # Remove the reference scenario's Koffing, relic and partner entities.
        "Entities": [{
            "Name": "Beach Cave — l’Anse des Marées",
            "Visible": True,
            "MapChars": [],
            "GroundObjects": [],
            "Spawners": [],
            "Markers": [
                marker("Entrance", 244, 364, 4),
                marker("donjon_seuil", 220, 4, 0),
            ],
        }],
    })
    return {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "Version": "0.8.12.0",
        "Object": obj,
    }


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_preview(layout: dict, frames: list[Path]) -> None:
    uris = [data_uri(path) for path in frames]
    html = f'''<!doctype html>
<html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{layout["title"]}</title>
<style>body{{margin:0;background:#111827;color:#f4ead5;font:16px system-ui,sans-serif}}main{{max-width:980px;margin:auto;padding:28px}}h1{{color:#f5cf88}}p{{line-height:1.6;color:#c8d2d0}}img{{display:block;max-width:100%;image-rendering:pixelated;background:#202b38;margin:14px 0}}button,input{{padding:9px;background:#253746;color:#fff;border:1px solid #668c94;border-radius:5px}}.note{{border-left:4px solid #d99668;padding-left:14px}}strong{{color:#f2c876}}small{{color:#a9b8ba}}</style>
<main><div class="note"><strong>Map référente canonique — pixels inchangés</strong><br>Cette livraison ne découpe pas le guide généré. Elle réutilise directement le Ground et les cellules 24 px de Beach Cave Pit.</div>
<h1>{layout["title"]}</h1><p>Composition canonique : parois rouges, bassin central, plage claire et ouverture nord. L'aperçu ne valide ni le rendu GPU ni les collisions en jeu.</p>
<button id="play">Pause</button> <input id="frame" type="range" min="0" max="{len(uris)-1}" value="0"><span id="label">Phase 1</span><img id="scene" alt="Beach Cave canonique">
<p><small>Source finale : `references/ExplorersOfSkyOrigins/BeachCavePit.tile` + `beach_cave_pit.rsground`, commit audité dans provenance.json. Pas de recoloration, rotation, agrandissement ni pixels générés.</small></p>
<script>const frames={json.dumps(uris)},scene=document.querySelector('#scene'),range=document.querySelector('#frame'),label=document.querySelector('#label'),play=document.querySelector('#play');let running=true,t=0;function draw(){{scene.src=frames[t];range.value=t;label.textContent='Phase '+(t+1)+' / '+frames.length}}range.oninput=()=>{{running=false;play.textContent='Lecture';t=+range.value;draw()}};play.onclick=()=>{{running=!running;play.textContent=running?'Pause':'Lecture'}};setInterval(()=>{{if(running){{t=(t+1)%frames.length;draw()}}}},130);draw();</script></main></html>'''
    (ROOT / "apercu_beach_cave_anse_des_marees.html").write_text(html, encoding="utf-8")


def make_index(tile_path: Path) -> bytes:
    spec = importlib.util.spec_from_file_location("index_tools", ROOT / "source/pmdo_cote/INSTALLER.py")
    tools = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(tools)
    with tile_path.open("rb") as stream:
        return tools.encode_index({tile_path.stem: tools.read_node(stream)})


def package(ground_path: Path, manifest: dict) -> None:
    if PACK.exists():
        shutil.rmtree(PACK)
    root = PACK / "beach_cave_anse_des_marees"
    (root / "Data/Ground").mkdir(parents=True)
    (root / "Data/Script/ground/v50812_beach_cave_anse_des_marees").mkdir(parents=True)
    (root / "Data/Script/beach_cave_anse_des_marees/ground/v50812_beach_cave_anse_des_marees").mkdir(parents=True)
    (root / "Content/Tile").mkdir(parents=True)
    shutil.copyfile(ground_path, root / "Data/Ground" / GROUND_NAME)
    script = b"-- Empty editing scaffold. Destination and return events are intentionally not guessed.\nreturn {}\n"
    for path in [
        root / "Data/Script/ground/v50812_beach_cave_anse_des_marees/init.lua",
        root / "Data/Script/beach_cave_anse_des_marees/ground/v50812_beach_cave_anse_des_marees/init.lua",
    ]:
        path.write_bytes(script)
    tile = REF / "BeachCavePit.tile"
    shutil.copyfile(tile, root / "Content/Tile/BeachCavePit.tile")
    (root / "Content/Tile/index.idx").write_bytes(make_index(root / "Content/Tile/BeachCavePit.tile"))
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for filename in ("provenance.json", "verification.json", "layout.json", "README.md"):
        source = HERE / filename if filename != "layout.json" else OUT / filename
        (root / filename).write_bytes(source.read_bytes())
    (root / "Mod.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Beach Cave — l’Anse des Marées</Name>
  <Author>guilde-treehouse-pmd</Author>
  <Description>Ground PMDO 0.8.12 reconstruit avec les textures canoniques de Explorers of Sky Origins.</Description>
  <Namespace>beach_cave_anse_des_marees</Namespace>
  <UUID>4e3b7a2e-9f4d-4d1c-a7b5-8f3f1c5c0812</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''', encoding="utf-8")
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
        assert any(name.endswith(".rsground") for name in archive.namelist())


def main() -> None:
    layout_module = importlib.util.spec_from_file_location("beach_layout", HERE / "layout.py")
    layout = importlib.util.module_from_spec(layout_module)
    assert layout_module.loader is not None
    layout_module.loader.exec_module(layout)
    layout.main()
    spec = json.loads((OUT / "layout.json").read_text())
    reference = json.loads((REF / "beach_cave_pit.rsground").read_text(encoding="utf-8-sig"))
    tile_size, bank = read_tile(REF / "BeachCavePit.tile")
    assert reference["Object"]["TexSize"] * 8 == tile_size == 24
    frames = []
    for tick in range(24):
        image = compose(reference["Object"], bank, tick)
        path = OUT / f"composition_phase_{tick:02d}.png"
        image.save(path, optimize=True)
        frames.append(path)
    # First frame must be byte-identical to the audited source reconstruction.
    audited = HERE / "audit" / "beach_cave_pit_composition.png"
    assert Image.open(frames[0]).convert("RGBA").tobytes() == Image.open(audited).convert("RGBA").tobytes()
    shutil.copyfile(frames[0], OUT / "01_terrain_canonique.png")
    write_preview(spec, frames)
    ground = ground_document(reference)
    ground_path = OUT / GROUND_NAME
    ground_path.write_text(json.dumps(ground, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    manifest = {
        "id": spec["id"],
        "title": spec["title"],
        "target": "PMDO 0.8.12",
        "ground": GROUND_NAME,
        "size_px": spec["size_px"],
        "TexSize": 3,
        "tile_size_px": 24,
        "layers": ["Terrain canonique Beach Cave Pit"],
        "canonical_source": "source/beach_cave_v1/references/ExplorersOfSkyOrigins/BeachCavePit.tile",
        "canonical_map_source": "source/beach_cave_v1/references/ExplorersOfSkyOrigins/beach_cave_pit.rsground",
        "generated_guide": "renders/beach_cave_v1/guide_composition_generated.png",
        "generated_guide_used_as_pixels": False,
        "native_only": True,
        "frame_preview_count": len(frames),
        "runtime_engine_tested": False,
        "destination_configured": False,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    package(ground_path, manifest)
    print(f"PASS: {spec['title']} — exact canonical composition, {len(frames)} native phases, pack={ZIP.name}")


if __name__ == "__main__":
    main()
