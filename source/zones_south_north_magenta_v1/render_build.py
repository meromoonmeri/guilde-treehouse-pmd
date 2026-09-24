#!/usr/bin/env python3
"""Build the generated final forest render from its magenta composition."""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GUIDE_SOURCE = HERE / "generation/forest_cave_magenta_v2.png"
OUT = ROOT / "exports/forest_cave_render_v1_pmdo"
WIDTH, HEIGHT, GRID = 512, 640, 8
ASSET = "forest_render_v1"
NAMESPACE = "forest_render_v1"
VERSION = "0.8.12.0"

sys.path.insert(0, str(ROOT))
from source.zones_south_north_v3.pmdo_build import (  # noqa: E402
    TileBank,
    build_tile_layer,
    collision_cells,
    ground_layer,
    obstacle_grid,
    patch_installer,
    write_index,
)

REFERENCES = {
    "forest_reference": ROOT / "forêtglomypmdsky.png",
    "forest_guide_reference": ROOT / "source/zones_south_north_v3/generation/forest_guide.png",
    "native_tree_reference": ROOT / "source/zones_south_north_v3/references/native_tree_complete.png",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hot_magenta(rgb: np.ndarray) -> np.ndarray:
    # Key the exact chroma and its anti-aliased magenta/purple family.  Cast to
    # signed integers before channel differences: uint8 arithmetic would wrap
    # at 255 and leave a visible pink fringe around the generated silhouette.
    r, g, b = rgb.astype(np.int16).transpose(2, 0, 1)
    exact = (r >= 220) & (g <= 80) & (b >= 200)
    softened = (r > 100) & (b > 80) & (r - g > 40) & (b - g > 35)
    return exact | softened


def build_render_layers() -> tuple[dict, list[tuple[str, Image.Image]], Image.Image]:
    raw = Image.open(GUIDE_SOURCE).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    source = np.array(raw)
    rgb = source[:, :, :3].copy()
    key = hot_magenta(rgb)
    valid = ~key
    yy, xx = np.mgrid[:HEIGHT, :WIDTH]
    r, g, b = rgb.astype(float).transpose(2, 0, 1)
    green = (g > r * 1.03) & (g > b * 1.14) & (g > 60)
    path = valid & (r > 180) & (g > 145) & (b < 195) & (r > g * 1.04) & (g > b * 1.04)
    # The cliff and cave occupy the north, while the generated trees sit on the
    # side banks.  The masks are layout masks, not claims of native pixels.
    cliff = valid & (yy < HEIGHT * .33) & ~green & ~path
    side = ((xx < WIDTH * .40) | (xx > WIDTH * .60)) & (yy > HEIGHT * .16)
    tree_like = green & ((g < 205) | (r < 110) | (b < 75))
    brown = (r > g * .82) & (g > b * 1.04) & (r > 45) & (g < 175)
    trees = valid & side & (tree_like | brown) & ~cliff
    neutral = (np.max(rgb, axis=2).astype(float) - np.min(rgb, axis=2).astype(float) < 52) & (g > 55)
    front = valid & neutral & ~green & ~path & ~cliff & ~trees & (yy > HEIGHT * .18)
    vegetation = valid & green & ~path & ~cliff & ~trees & ~front
    # Explicitly disjoint masks make recomposition auditable.
    assigned = cliff | trees | front | vegetation
    base_mask = ~assigned
    # Keep the chroma-key result as alpha: the final map never paints the
    # magenta outside the generated silhouette with canonical or invented
    # pixels. The generated scene remains the sole visual source.
    base_pixels = np.zeros_like(source)
    base_pixels[base_mask & valid] = source[base_mask & valid]
    base = Image.fromarray(base_pixels, "RGBA")

    def transparent_mask(mask: np.ndarray) -> Image.Image:
        layer = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
        layer[mask] = source[mask]
        return Image.fromarray(layer, "RGBA")

    layers = [
        ("01_sol_chemin", base),
        ("02_vegetation", transparent_mask(vegetation)),
        ("03_arbres", transparent_mask(trees)),
        ("04_cliff_grotte", transparent_mask(cliff)),
        ("05_premier_plan", transparent_mask(front)),
    ]
    composition = Image.new("RGBA", (WIDTH, HEIGHT))
    for _, image in layers:
        composition.alpha_composite(image)
    composition_alpha = np.array(composition)[:, :, 3]
    assert np.all(composition_alpha[valid] == 255) and np.all(composition_alpha[~valid] == 0)
    masks = {"path": path, "vegetation": vegetation, "trees": trees, "cliff": cliff, "front": front}
    return {
        "guide_source_sha256": sha256(GUIDE_SOURCE),
        "guide_source": str(GUIDE_SOURCE.relative_to(ROOT)),
        "normalized_size": [WIDTH, HEIGHT],
        "key_rgb": [255, 0, 255],
        "key_pixels": int(key.sum()),
        "generated_final": True,
        "canonical_pixels_in_final": False,
        "references_are_style_layout_only": True,
        "masks": masks,
    }, layers, composition


def write_ground(destination: Path, layers: list[tuple[str, Image.Image]], path_mask: np.ndarray) -> dict:
    width, height = WIDTH // GRID, HEIGHT // GRID
    banks = []
    ground_layers = []
    for index, (layer_id, image) in enumerate(layers):
        bank = TileBank(f"FRV1_FOREST_{index:02d}")
        banks.append(bank)
        ground_layers.append(ground_layer(layer_id, build_tile_layer(image, bank, width, height), 4 if index == 4 else 0))
    for bank in banks:
        bank.write(destination / "Content/Tile" / f"{bank.name}.tile")
    write_index((destination / "Content/Tile").glob("*.tile"), destination / "Content/Tile/index.idx")
    path_file = destination / "review/generated_path_mask.png"
    Image.fromarray((path_mask.astype(np.uint8) * 255), "L").save(path_file)
    # collision_cells uses the stored mask so the PMDO scaffold follows the
    # generated final route, not the older canonical V3 route.
    _, free_cells = collision_cells(path_file, WIDTH, HEIGHT)
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": 1,
        "Name": {"DefaultText": "Forêt Render V1 — composition magenta", "LocalTexts": {}},
        "Released": False,
        "Comment": "Generated final render from magenta composition; canonical references guide style/layout only. Five editable layers.",
        "obstacles": obstacle_grid(width, height, free_cells),
        "rand": {"$type": "RogueElements.ReRandom, RogueElements", "FirstSeed": 0, "s": [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
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
        "Entities": [{"Name": "Arrivee et seuil", "Visible": True, "MapChars": [], "GroundObjects": [], "Spawners": [], "Markers": [
            {"EntName": "entrance", "Direction": 0, "EntEnabled": True, "triggerType": 0, "Collider": {"X": 224, "Y": 632, "Width": 64, "Height": 8}, "Comment": "Arrivee sud; warp non configure."},
            {"EntName": "donjon_seuil", "Direction": 0, "EntEnabled": True, "triggerType": 0, "Collider": {"X": 240, "Y": 136, "Width": 32, "Height": 16}, "Comment": "Seuil nord; destination a fournir."},
        ]}],
    }
    ground = destination / "Data/Ground" / f"{ASSET}.rsground"
    ground.parent.mkdir(parents=True, exist_ok=True)
    ground.write_text(json.dumps({"Version": VERSION, "Object": obj}, ensure_ascii=False, separators=(",", ":")) + "\n")
    script = destination / "Data/Script/ground" / ASSET / "init.lua"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("-- Generated render V1. No automatic dungeon warp.\nreturn {}\n")
    return {"free_collision_cells": int(free_cells.sum()), "total_collision_cells": int(free_cells.size), "path_pixels": int(path_mask.sum()), "tilesets": [b.name for b in banks]}


def write_header(destination: Path) -> None:
    ident = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meromoonmeri/guilde-treehouse-pmd/" + ASSET)
    (destination / "Mod.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Forêt Render V1 — composition magenta</Name>
  <Author>meromoonmeri</Author>
  <Description>Une map PMDO 0.8.12 generee sur magenta puis separee en 5 calques finaux.</Description>
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


def write_preview(destination: Path, layers: list[tuple[str, Image.Image]]) -> None:
    def uri(path: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
    data = {"guide": uri(destination / "provenance/guide/forest_cave_layout_magenta.png"), "final": uri(destination / "review/composition_final.png"), "layers": [{"id": n, "uri": uri(destination / "review/layers" / f"{n}.png")} for n, _ in layers]}
    payload = json.dumps(data, ensure_ascii=False)
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forêt Render V1 · méthode magenta</title><style>body{{margin:0;background:#17221f;color:#f7f0d5;font:16px system-ui}}main{{max-width:1180px;margin:auto;padding:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}}article{{background:#25372f;padding:16px;border-radius:12px}}img{{width:100%;image-rendering:pixelated;background:#ff00ff}}canvas{{width:100%;image-rendering:pixelated;background:#111a17}}label{{display:block;margin:8px 0}}</style><main><h1>Forêt Render V1 — composition finale magenta</h1><p>La composition générée est le rendu final. Le magenta est retiré, puis le rendu est organisé en cinq calques. Les références canoniques servent à la continuité PMD, pas à remplacer les textures générées.</p><div class="grid"><article><h2>Guide magenta</h2><img src="{data['guide']}"></article><article><h2>Composition finale générée</h2><img src="{data['final']}" alt="Composition finale alpha nettoyée"><h3>Recomposer par calques</h3><canvas id="c" width="{WIDTH}" height="{HEIGHT}"></canvas><div id="controls"></div></article></div></main><script>const D={payload},c=document.querySelector('#c'),x=c.getContext('2d'),imgs=[],checks=[];function draw(){{x.clearRect(0,0,c.width,c.height);D.layers.forEach((l,i)=>{{if(checks[i].checked&&imgs[i].complete)x.drawImage(imgs[i],0,0)}})}}D.layers.forEach((l,i)=>{{const im=new Image(),ch=document.createElement('input'),lab=document.createElement('label');ch.type='checkbox';ch.checked=true;ch.onchange=draw;lab.append(ch,document.createTextNode(' '+l.id));document.querySelector('#controls').append(lab);checks.push(ch);imgs.push(im);im.onload=draw;im.src=l.uri}});</script></html>'''
    (ROOT / "apercu_forest_cave_render_v1.html").write_text(html, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    guide_info, layers, composition = build_render_layers()
    masks = guide_info.pop("masks")
    guide_dir = OUT / "provenance/guide"
    guide_dir.mkdir(parents=True, exist_ok=True)
    raw = Image.open(GUIDE_SOURCE).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    raw.save(guide_dir / "forest_cave_layout_magenta.png")
    keyed = np.array(raw)
    key = hot_magenta(keyed[:, :, :3])
    keyed[key] = [0, 0, 0, 0]
    keyed[~key, 3] = 255
    Image.fromarray(keyed, "RGBA").save(guide_dir / "forest_cave_layout_alpha_clean.png")
    layer_dir = OUT / "review/layers"
    layer_dir.mkdir(parents=True, exist_ok=True)
    layer_records = []
    for name, image in layers:
        filename = f"{name}.png"
        image.save(layer_dir / filename)
        layer_records.append({"id": name, "file": filename, "generated_final": True, "canonical_pixels": False})
    (OUT / "review/composition_final.png").parent.mkdir(parents=True, exist_ok=True)
    composition.save(OUT / "review/composition_final.png")
    mask_dir = OUT / "review/masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    path_mask = masks["path"]
    # Re-use the exact segmentation for the path control image.
    Image.fromarray(path_mask.astype(np.uint8) * 255, "L").save(mask_dir / "generated_path.png")
    write_guide_and_references(OUT, guide_info, masks)
    ground_info = write_ground(OUT, layers, path_mask)
    write_header(OUT)
    patch_installer(OUT)
    shutil.copyfile(HERE / "RENDER_README.md", OUT / "README.md")
    manifest = {
        "project": "forest_cave_render_v1_pmdo",
        "target": "PMDO 0.8.12",
        "workflow": "generated final composition on magenta -> chroma cleanup -> five final render layers",
        "material_status": "generated final render, canonical PMD references used for style/layout continuity",
        "guide": {k: v for k, v in guide_info.items() if k != "masks"},
        "layers": layer_records,
        "ground": ground_info,
        "reference_hashes": [{"id": k, "file": v.name, "sha256": sha256(v)} for k, v in REFERENCES.items()],
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
        "warp_destinations": "NOT CONFIGURED",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_preview(OUT, layers)
    print(f"1 generated render forestière en 5 calques construite: {OUT}")


def write_guide_and_references(destination: Path, guide_info: dict, masks: dict) -> None:
    mask_dir = destination / "review/masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    for name, mask in masks.items():
        Image.fromarray((mask.astype(np.uint8) * 255), "L").save(mask_dir / f"{name}.png")
    ref_dir = destination / "provenance/references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, path in REFERENCES.items():
        shutil.copyfile(path, ref_dir / path.name)
        records.append({"id": name, "file": path.name, "sha256": sha256(path)})
    (ref_dir / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    (ref_dir / "generation_method.txt").write_text("Generated final scene on #FF00FF; canonical references guide style and continuity only.\n")


if __name__ == "__main__":
    main()
