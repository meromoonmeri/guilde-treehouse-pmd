#!/usr/bin/env python3
"""Build one forest map with the magenta-composition workflow.

The generated magenta image is used only to lock the composition and to prove
that the chroma-key step was performed.  The five final layers are rebuilt
from the documented canonical V3 source pixels; no generated pixel is copied
into the PMDO terrain.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V3_ROOT = ROOT / "exports/zones_south_north_v3"
V3 = V3_ROOT / "forest_cave"
OUT = ROOT / "exports/forest_cave_magenta_v1_pmdo"
GUIDE_SOURCE = HERE / "generation/forest_cave_magenta_v2.png"
GRID = 8
WIDTH, HEIGHT = 512, 640
ASSET = "forest_magenta_v1"
NAMESPACE = "forest_magenta_v1"
VERSION = "0.8.12.0"

# Reuse the already audited PMDO binary primitives.  Importing this module is
# safe: its build entry point is guarded and does not write the old pack.
sys.path.insert(0, str(ROOT))
from source.zones_south_north_v3.pmdo_build import (  # noqa: E402
    TileBank,
    build_tile_layer,
    cell_animation,
    collision_cells,
    ground_layer,
    obstacle_grid,
    patch_installer,
    write_index,
)


SOURCE_LAYERS = {
    name: V3 / filename
    for name, filename in {
        "01_soil": "SouthNorthV3_forest_cave_01_soil.png",
        "02_path": "SouthNorthV3_forest_cave_02_continuous_earth_path.png",
        "03_north_canopy": "SouthNorthV3_forest_cave_03_north_canopy.png",
        "04_cliff": "SouthNorthV3_forest_cave_04_white_cliff.png",
        "05_cave": "SouthNorthV3_forest_cave_05_cave_opening.png",
        "06_trunks": "SouthNorthV3_forest_cave_06_tree_trunks.png",
        "07_canopies": "SouthNorthV3_forest_cave_07_tree_canopies.png",
        "08_stones": "SouthNorthV3_forest_cave_08_stones.png",
        "09_bushes": "SouthNorthV3_forest_cave_09_cliff_foot_bushes.png",
    }.items()
}
SOURCE_PROVENANCE = {
    name: V3 / filename
    for name, filename in {
        "01_soil": "01_soil_source.npz",
        "02_path": "02_continuous_earth_path_source.npz",
        "03_north_canopy": "03_north_canopy_source.npz",
        "04_cliff": "04_white_cliff_source.npz",
        "05_cave": "05_cave_opening_source.npz",
        "06_trunks": "06_tree_trunks_source.npz",
        "07_canopies": "07_tree_canopies_source.npz",
        "08_stones": "08_stones_source.npz",
        "09_bushes": "09_cliff_foot_bushes_source.npz",
    }.items()
}


def read_source(name: str) -> Image.Image:
    image = Image.open(SOURCE_LAYERS[name]).convert("RGBA")
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"source {name} has invalid size {image.size}")
    return image


def over(*images: Image.Image) -> Image.Image:
    result = Image.new("RGBA", (WIDTH, HEIGHT))
    for image in images:
        result.alpha_composite(image)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_magenta_guide(destination: Path) -> dict:
    if not GUIDE_SOURCE.is_file():
        raise FileNotFoundError(GUIDE_SOURCE)
    raw = Image.open(GUIDE_SOURCE).convert("RGBA")
    # Generated guides are normalized with nearest-neighbor only.  This is a
    # guide operation, never an operation on the canonical final layers.
    guide = raw.resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    pixels = np.array(guide)
    # The generator compresses/softens the chroma slightly at some corners;
    # accept only the hot-magenta family, never natural green/rock colors.
    key = (pixels[:, :, 0] >= 220) & (pixels[:, :, 1] <= 80) & (pixels[:, :, 2] >= 200)
    for x, y in [(0, 0), (WIDTH - 1, 0), (0, HEIGHT - 1), (WIDTH - 1, HEIGHT - 1)]:
        if not key[y, x]:
            raise AssertionError(f"guide corner {x},{y} is not chroma magenta")
    guide_dir = destination / "guide"
    guide_dir.mkdir(parents=True, exist_ok=True)
    guide.save(guide_dir / "forest_cave_layout_magenta.png")
    keyed = guide.copy()
    keyed_pixels = np.array(keyed)
    keyed_pixels[:, :, 3] = np.where(key, 0, 255).astype(np.uint8)
    keyed = Image.fromarray(keyed_pixels, "RGBA")
    keyed.save(guide_dir / "forest_cave_layout_alpha_clean.png")
    return {
        "source": str(GUIDE_SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(GUIDE_SOURCE),
        "normalized_size": [WIDTH, HEIGHT],
        "normalization": "nearest-neighbor guide normalization only",
        "key_rgb": [255, 0, 255],
        "magenta_pixels": int(key.sum()),
        "final_layers_use_guide_pixels": False,
    }


def build_final_layers(destination: Path) -> tuple[list[dict], Image.Image]:
    source = {name: read_source(name) for name in SOURCE_LAYERS}
    # Exactly five layers.  Each is a composition of complete, documented
    # source layers; the generated guide never supplies final RGB values.
    definitions = [
        ("01_sol_chemin", ["01_soil", "02_path"], "soil and continuous canonical earth path"),
        ("02_vegetation_arriere", ["03_north_canopy"], "canonical north/back canopy"),
        ("03_cliff_grotte", ["04_cliff", "05_cave"], "canonical white cliff and separate cave opening"),
        ("04_arbres", ["06_trunks", "07_canopies"], "complete native tree trunks and canopies"),
        ("05_premier_plan", ["08_stones", "09_bushes"], "canonical stones and foreground cliff-foot vegetation"),
    ]
    layers_dir = destination / "provenance/final_layers"
    layers_dir.mkdir(parents=True, exist_ok=True)
    records = []
    final_layers = []
    for layer_id, sources, role in definitions:
        image = over(*(source[name] for name in sources))
        filename = f"ForestMagentaV1_{layer_id}.png"
        image.save(layers_dir / filename)
        final_layers.append((layer_id, image))
        records.append({
            "id": layer_id,
            "file": filename,
            "role": role,
            "source_layers": sources,
            "source_files": [SOURCE_LAYERS[name].name for name in sources],
            "source_hashes": {name: sha256(SOURCE_LAYERS[name]) for name in sources},
            "generated_pixels_used": False,
        })
    composition = over(*(image for _, image in final_layers))
    (destination / "review").mkdir(parents=True, exist_ok=True)
    composition.save(destination / "review/composition_final.png")
    # The five layers must reproduce the already reviewed canonical V3 scene.
    reference = Image.open(V3 / "composite.png").convert("RGBA")
    if composition.tobytes() != reference.tobytes():
        raise AssertionError("5-layer canonical composition differs from V3 source composition")
    return records, composition


def make_ground(destination: Path, layer_records: list[dict], final_layers: list[tuple[str, Image.Image]]) -> dict:
    banks = []
    ground_layers = []
    width, height = WIDTH // GRID, HEIGHT // GRID
    for index, ((layer_id, image), record) in enumerate(zip(final_layers, layer_records)):
        bank = TileBank(f"FMV1_FOREST_{index:02d}")
        banks.append(bank)
        # Only the last layer is Top=4.  The tree layer remains independently
        # editable on the normal plane; foreground vegetation can cover actors.
        draw = 4 if index == len(final_layers) - 1 else 0
        ground_layers.append(ground_layer(layer_id, build_tile_layer(image, bank, width, height), draw))
    for bank in banks:
        bank.write(destination / "Content/Tile" / f"{bank.name}.tile")
    write_index((destination / "Content/Tile").glob("*.tile"), destination / "Content/Tile/index.idx")

    path_pixels, free_cells = collision_cells(V3 / "path_connectivity_mask.png", WIDTH, HEIGHT)
    markers = [
        {
            "EntName": "entrance",
            "Direction": 0,
            "EntEnabled": True,
            "triggerType": 0,
            "Collider": {"X": 224, "Y": 632, "Width": 64, "Height": 8},
            "Comment": "Arrivee sud; aucune transition automatique.",
        },
        {
            "EntName": "donjon_seuil",
            "Direction": 0,
            "EntEnabled": True,
            "triggerType": 0,
            "Collider": {"X": 240, "Y": 136, "Width": 32, "Height": 16},
            "Comment": "Seuil nord; destination a configurer dans le projet de jeu.",
        },
    ]
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": 1,
        "Name": {"DefaultText": "Forêt — composition magenta, textures canoniques", "LocalTexts": {}},
        "Released": False,
        "Comment": "5 layers: magenta guide for composition, canonical source pixels for final terrain. No automatic warp.",
        "obstacles": obstacle_grid(width, height, free_cells),
        "rand": {
            "$type": "RogueElements.ReRandom, RogueElements",
            "FirstSeed": 0,
            "s": [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444],
        },
        "Status": {},
        "Background": {"$type": "RogueEssence.Dungeon.LayeredBG, RogueEssence", "Layers": []},
        "BlankBG": {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1},
        "Layers": ground_layers,
        "AssetName": ASSET,
        "Music": "",
        "EdgeView": 0,
        "NoSwitching": False,
        "ViewCenter": None,
        "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": None,
        "Decorations": [{"Name": "Decorations", "Layer": 2, "Visible": True, "Anims": []}],
        "Entities": [{
            "Name": "Arrivee et seuil",
            "Visible": True,
            "MapChars": [],
            "GroundObjects": [],
            "Spawners": [],
            "Markers": markers,
        }],
    }
    ground = destination / "Data/Ground" / f"{ASSET}.rsground"
    ground.parent.mkdir(parents=True, exist_ok=True)
    ground.write_text(json.dumps({"Version": VERSION, "Object": obj}, ensure_ascii=False, separators=(",", ":")) + "\n")
    script = destination / "Data/Script/ground" / ASSET / "init.lua"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("-- Magenta composition workflow; no automatic dungeon warp.\nreturn {}\n")
    return {
        "asset": ASSET,
        "size_px": [WIDTH, HEIGHT],
        "grid": [width, height],
        "layers": layer_records,
        "tilesets": [bank.name for bank in banks],
        "free_collision_cells": int(free_cells.sum()),
        "total_collision_cells": int(free_cells.size),
        "path_pixels": int(path_pixels.sum()),
        "markers": [{"name": "entrance", "role": "south_arrival"}, {"name": "donjon_seuil", "role": "north_threshold"}],
        "runtime": "NOT TESTED",
        "generated_guide_is_final_texture": False,
    }


def write_header(destination: Path) -> None:
    ident = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meromoonmeri/guilde-treehouse-pmd/" + ASSET)
    (destination / "Mod.xml").write_text(
        f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Forêt Magenta V1 — textures canoniques</Name>
  <Author>meromoonmeri</Author>
  <Description>Une Ground PMDO 0.8.12 en 5 calques : composition guidee sur magenta, terrain final reconstruit avec pixels canoniques.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>{VERSION}</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''', encoding="utf-8")
    source = destination / "Data/Script/ground" / ASSET / "init.lua"
    target = destination / "Data/Script" / NAMESPACE / "ground" / ASSET / "init.lua"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def write_preview(destination: Path, guide_info: dict, layer_records: list[dict]) -> None:
    def data_uri(path: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()

    guide = data_uri(destination / "provenance/guide/forest_cave_layout_magenta.png")
    final = data_uri(destination / "review/composition_final.png")
    layers = []
    for record in layer_records:
        layers.append({"id": record["id"], "uri": data_uri(destination / "provenance/final_layers" / record["file"])})
    payload = json.dumps({"guide": guide, "final": final, "layers": layers}, ensure_ascii=False)
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forêt Magenta V1 · 5 calques</title>
<style>body{{margin:0;background:#16231d;color:#f5f0d7;font:16px system-ui}}main{{max-width:1180px;margin:auto;padding:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}article{{background:#22352b;border:1px solid #55705b;border-radius:12px;padding:16px}}img{{display:block;width:100%;image-rendering:pixelated;background:#ff00ff}}label{{display:block;margin:9px 0}}small{{color:#b6c5ae}}button{{padding:8px 12px;border:0;border-radius:6px}}#final{{background:#ff00ff}}</style>
<main><h1>Forêt — composition magenta → 5 calques canoniques</h1><p>Le guide magenta est présenté comme composition uniquement. Le rendu final est recomposé avec les pixels canoniques des sources V3 ; aucun pixel du guide généré n’est utilisé dans le terrain.</p><div class="grid"><article><h2>Guide chroma-key</h2><img src="{guide}"><small>Guide généré, fond #FF00FF nettoyable par flood-fill.</small></article><article><h2>Composition finale</h2><canvas id="final" width="{WIDTH}" height="{HEIGHT}"></canvas><div id="checks"></div></article></div><h2>Contrôle des couches</h2><p id="note">Sol + chemin · végétation arrière · cliff/grotte · arbres · premier plan.</p></main>
<script>const D={payload};const c=document.querySelector('#final'),x=c.getContext('2d'),imgs=[],chs=[];function draw(){{x.clearRect(0,0,c.width,c.height);D.layers.forEach((l,i)=>{{if(chs[i].checked&&imgs[i].complete)x.drawImage(imgs[i],0,0)}})}}D.layers.forEach((l,i)=>{{const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=draw;chs.push(ch);label.append(ch,document.createTextNode(' '+l.id));document.querySelector('#checks').append(label);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri}});document.querySelector('#checks').insertAdjacentHTML('beforeend','<br><button onclick="chs.forEach(v=>v.checked=true);draw()">Tout afficher</button>');</script></html>'''
    (ROOT / "apercu_forest_cave_magenta_v1.html").write_text(html, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    guide_info = prepare_magenta_guide(OUT / "provenance")
    layer_records, composition = build_final_layers(OUT)
    # Copy all original V3 material maps and provenance into the pack so the
    # five compositions can be audited without relying on a hidden workspace.
    source_dir = OUT / "provenance/v3_source"
    source_dir.mkdir(parents=True)
    for path in list(SOURCE_LAYERS.values()) + list(SOURCE_PROVENANCE.values()) + [V3_ROOT / "manifest.json", V3 / "composite.png", V3 / "path_connectivity_mask.png"]:
        shutil.copyfile(path, source_dir / path.name)
    make_ground(OUT, layer_records, [(r["id"], Image.open(OUT / "provenance/final_layers" / r["file"]).convert("RGBA")) for r in layer_records])
    write_header(OUT)
    patch_installer(OUT)
    shutil.copyfile(HERE / "README.md", OUT / "README.md")
    manifest = {
        "project": "forest_cave_magenta_v1_pmdo",
        "target": "PMDO 0.8.12",
        "workflow": "magenta composition guide -> chroma cleanup -> final composition -> 5 canonical layers -> Ground",
        "guide": guide_info,
        "canonical_final_pixels": True,
        "generated_guide_pixels_in_final": False,
        "map": json.loads(json.dumps(make_manifest_stub(layer_records))),
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
        "warp_destinations": "NOT CONFIGURED",
    }
    # make_ground already returned the detailed map record; reconstruct the
    # same record from the Ground-independent measurements for a stable manifest.
    path_mask = np.array(Image.open(V3 / "path_connectivity_mask.png").convert("L")) > 0
    _, free = collision_cells(V3 / "path_connectivity_mask.png", WIDTH, HEIGHT)
    manifest["map"] = {
        "asset": ASSET,
        "title": "Forêt — arrivée sud, grotte au nord",
        "size_px": [WIDTH, HEIGHT],
        "grid": [WIDTH // GRID, HEIGHT // GRID],
        "layer_count": 5,
        "layers": layer_records,
        "tilesets": [f"FMV1_FOREST_{i:02d}" for i in range(5)],
        "free_collision_cells": int(free.sum()),
        "total_collision_cells": int(free.size),
        "path_pixels": int(path_mask.sum()),
        "markers": [
            {"name": "entrance", "rect": [224, 632, 64, 8], "role": "south_arrival"},
            {"name": "donjon_seuil", "rect": [240, 136, 32, 16], "role": "north_threshold"},
        ],
        "runtime": "NOT TESTED",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_preview(OUT, guide_info, layer_records)
    print(f"1 map forestière PMDO en 5 calques construite: {OUT}")


def make_manifest_stub(layer_records: list[dict]) -> dict:
    return {"layer_count": len(layer_records), "layers": layer_records}


if __name__ == "__main__":
    main()
