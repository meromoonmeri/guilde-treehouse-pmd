#!/usr/bin/env python3
"""Build one generated PMD-style forest render as five aligned PMDO layers.

This is intentionally different from the canonical-pixel calibration pack:
the magenta composition is the final artwork, and the five layers are masks
cut from that same final composition so that their recomposition is exact.
Canonical PMD references are provenance/style references, not substituted RGB
for this render workflow.
"""
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
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# The current final composition is produced by the image generator.  Keep the
# earlier magenta/canonical source lot untouched as a separate archive.
COMPOSITION_SOURCE = ROOT / "source/forest_cave_render_v1/generation/forest_cave_final_generated_v3.png"
OUT = ROOT / "exports/forest_cave_render_v1_pmdo"
WIDTH, HEIGHT, GRID = 512, 640, 8
ASSET = "forest_cave_render_v1"
NAMESPACE = "forest_cave_render_v1"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key_magenta(image: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    rgba = np.array(image.convert("RGBA"))
    # The image generator slightly antialiases the hot-magenta border.  Key
    # only magenta-like pixels connected to the image edge, so isolated pink
    # details inside the map are never removed as background.
    r, g, b = (rgba[:, :, i].astype(int) for i in range(3))
    candidate = (r >= 200) & (g <= 120) & (b >= 180) & (r - g >= 100) & (b - g >= 90)
    edge = np.zeros(candidate.shape, dtype=bool)
    edge[0, :] = candidate[0, :]
    edge[-1, :] = candidate[-1, :]
    edge[:, 0] |= candidate[:, 0]
    edge[:, -1] |= candidate[:, -1]
    key = nd.binary_propagation(edge, mask=candidate, structure=np.ones((3, 3), dtype=bool))
    return rgba, key


def build_masks(rgba: np.ndarray, outside: np.ndarray) -> dict[str, np.ndarray]:
    h, w = outside.shape
    yy, xx = np.mgrid[:h, :w]
    r, g, b = rgba[:, :, 0].astype(float), rgba[:, :, 1].astype(float), rgba[:, :, 2].astype(float)
    solid = ~outside

    # Canonical semantic order for the generated render.  These are masks of
    # the one final composition, not separately generated/warped scenes.
    neutral = np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b])
    # White/gray stone is separated from the green canopy by both neutrality
    # and brightness; the cave mouth is kept as a central dark component.
    gray_rock = (neutral < 55) & (r > 120) & (g > 110) & (b > 90)
    dark_stone = (neutral < 48) & (np.maximum.reduce([r, g, b]) < 150) & (yy < 140) & (xx > 120) & (xx < w - 120)
    dark_cave = (np.maximum.reduce([r, g, b]) < 78) & (xx > 185) & (xx < w - 185) & (yy < 235)
    cliff = solid & (yy < 215) & (xx > 75) & (xx < w - 75) & (gray_rock | dark_stone | dark_cave)
    # Keep the green ledge below the cliff in the ground/vegetation planes.

    green = (g > r * 0.92) & (g > b * 1.18) & (g > 65)
    tree_green = green & ((g < 215) | (r < 125))
    brown_trunk = (r > 65) & (r > g * 1.05) & (g > b * 1.05) & (g < 150) & (b < 125)
    side = (xx < 185) | (xx > w - 185)
    lower_side = ((xx < 220) | (xx > w - 292)) & (yy > 500)
    tree_candidate = solid & ~cliff & side & (tree_green | brown_trunk)
    foreground = solid & ~cliff & lower_side & (tree_candidate | gray_rock | brown_trunk)
    tree = tree_candidate & ~foreground

    # Small plants, grass highlights and stones not selected as trees/foreground
    # are placed on their own vegetation layer.
    decor = solid & ~cliff & ~tree & ~foreground & ((green & (yy > 130)) | gray_rock)
    base = solid & ~cliff & ~tree & ~foreground & ~decor

    # Ensure every visible generated pixel belongs to exactly one layer.  The
    # priority keeps a readable cave/tree depth while preserving exact RGB.
    masks = {
        "01_sol_chemin": base,
        "02_vegetation": decor,
        "03_cliff_grotte": cliff,
        "04_arbres": tree,
        "05_premier_plan": foreground,
    }
    union = np.zeros_like(solid)
    for mask in masks.values():
        if np.any(union & mask):
            raise AssertionError("layer masks overlap")
        union |= mask
    if not np.array_equal(union, solid):
        masks["01_sol_chemin"] |= solid & ~union
    return masks


def apply_mask(rgba: np.ndarray, mask: np.ndarray) -> Image.Image:
    layer = np.zeros_like(rgba)
    layer[mask] = rgba[mask]
    layer[:, :, 3] = np.where(mask, rgba[:, :, 3], 0).astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def path_from_composition(rgba: np.ndarray, outside: np.ndarray) -> np.ndarray:
    r, g, b = rgba[:, :, 0].astype(float), rgba[:, :, 1].astype(float), rgba[:, :, 2].astype(float)
    yy, xx = np.mgrid[:rgba.shape[0], :rgba.shape[1]]
    tan = (r > 150) & (g > 115) & (b < 205) & (r > g * 0.82) & (g > b * 1.12)
    candidate = tan & ~outside & (xx > 150) & (xx < 370) & (yy > 135)
    # Select the connected central route rather than isolated stones.
    labels, count = nd.label(candidate, structure=np.ones((3, 3), dtype=bool))
    best = np.zeros_like(candidate)
    best_score = -1
    for i in range(1, count + 1):
        ys, xs = np.where(labels == i)
        if len(xs) < 50:
            continue
        score = len(xs) + (ys.max() - ys.min()) * 3 - abs(float(xs.mean()) - rgba.shape[1] / 2)
        if score > best_score:
            best_score = score
            best = labels == i
    # Close tiny antialiased gaps while retaining the generated composition's
    # centerline.  This is a review collision mask, not a gameplay claim.
    best = nd.binary_closing(best, structure=np.ones((5, 5), dtype=bool), iterations=2)
    best = nd.binary_dilation(best, iterations=2)
    return best


def empty_auto() -> dict:
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}


def make_ground(destination: Path, layer_images: list[tuple[str, Image.Image]], path_mask: np.ndarray) -> dict:
    width, height = WIDTH // GRID, HEIGHT // GRID
    banks = []
    layers = []
    for index, (layer_id, image) in enumerate(layer_images):
        bank = TileBank(f"FCRV1_FOREST_{index:02d}")
        banks.append(bank)
        draw = 4 if index == len(layer_images) - 1 else 0
        layers.append(ground_layer(layer_id, build_tile_layer(image, bank, width, height), draw))
    for bank in banks:
        bank.write(destination / "Content/Tile" / f"{bank.name}.tile")
    write_index((destination / "Content/Tile").glob("*.tile"), destination / "Content/Tile/index.idx")

    path_file = destination / "review/path_mask.png"
    path_file.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((path_mask.astype(np.uint8) * 255)).save(path_file)
    # Use the same conservative clearance rule as the existing PMDO packs.
    _, free_cells = collision_cells(path_file, WIDTH, HEIGHT)
    markers = [
        {"EntName": "entrance", "Direction": 0, "EntEnabled": True, "triggerType": 0,
         "Collider": {"X": 224, "Y": 632, "Width": 64, "Height": 8},
         "Comment": "South arrival; no automatic transition."},
        {"EntName": "donjon_seuil", "Direction": 0, "EntEnabled": True, "triggerType": 0,
         "Collider": {"X": 240, "Y": 136, "Width": 32, "Height": 16},
         "Comment": "North threshold; destination supplied by the game project."},
    ]
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": 1,
        "Name": {"DefaultText": "Forêt render magenta — sud vers grotte", "LocalTexts": {}},
        "Released": False,
        "Comment": "Generated final composition cut into five aligned layers. Canonical references guided style only; see provenance.",
        "obstacles": obstacle_grid(width, height, free_cells),
        "rand": {"$type": "RogueElements.ReRandom, RogueElements", "FirstSeed": 0,
                 "s": [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
        "Status": {},
        "Background": {"$type": "RogueEssence.Dungeon.LayeredBG, RogueEssence", "Layers": []},
        "BlankBG": empty_auto(),
        "Layers": layers,
        "AssetName": ASSET,
        "Music": "", "EdgeView": 0, "NoSwitching": False,
        "ViewCenter": None, "ViewOffset": {"X": 0, "Y": 0}, "ActiveChar": None,
        "Decorations": [{"Name": "Decorations", "Layer": 2, "Visible": True, "Anims": []}],
        "Entities": [{"Name": "Arrivee et seuil", "Visible": True, "MapChars": [],
                      "GroundObjects": [], "Spawners": [], "Markers": markers}],
    }
    ground = destination / "Data/Ground" / f"{ASSET}.rsground"
    ground.parent.mkdir(parents=True, exist_ok=True)
    ground.write_text(json.dumps({"Version": VERSION, "Object": obj}, ensure_ascii=False, separators=(",", ":")) + "\n")
    script = destination / "Data/Script/ground" / ASSET / "init.lua"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("-- Generated render layer pack. No automatic warp.\nreturn {}\n")
    return {"free_collision_cells": int(free_cells.sum()), "total_collision_cells": int(free_cells.size),
            "tilesets": [bank.name for bank in banks]}


def write_header(destination: Path) -> None:
    ident = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meromoonmeri/guilde-treehouse-pmd/" + ASSET)
    (destination / "Mod.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Forêt Render Magenta V1</Name>
  <Author>meromoonmeri</Author>
  <Description>Une map finale generee sur magenta puis decoupee en cinq calques alignes PMDO 0.8.12.</Description>
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


def write_preview(destination: Path, guide: Image.Image, layers: list[tuple[str, Image.Image]]) -> None:
    def uri(image: Image.Image) -> str:
        import io
        stream = io.BytesIO(); image.save(stream, format="PNG")
        return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()
    payload = json.dumps({"guide": uri(guide), "layers": [{"id": i, "uri": uri(im)} for i, im in layers]}, ensure_ascii=False)
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forêt Render Magenta V1</title><style>body{{background:#15231c;color:#f5f0d7;font:16px system-ui;margin:0}}main{{max-width:1180px;margin:auto;padding:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}}article{{background:#22352b;border:1px solid #55705b;border-radius:12px;padding:16px}}img,canvas{{width:100%;image-rendering:pixelated;background:#ff00ff;display:block}}label{{display:block;margin:8px}}small{{color:#b5c4af}}</style><main><h1>Forêt · composition finale générée → 5 calques</h1><p>Le guide magenta est la composition finale. Les couches ci-dessous sont des découpes alignées de la même image, pas des reconstructions pixel-perfect d’une autre map.</p><div class="grid"><article><h2>Composition finale sur magenta</h2><img src="{uri(guide)}"><small>Fond chroma conservé pour contrôle.</small></article><article><h2>Recomposition</h2><canvas id="c" width="{WIDTH}" height="{HEIGHT}"></canvas><div id="checks"></div></article></div></main><script>const D={payload};const c=document.querySelector('#c'),x=c.getContext('2d'),ims=[],chs=[];function draw(){{x.clearRect(0,0,c.width,c.height);D.layers.forEach((l,i)=>{{if(chs[i].checked&&ims[i].complete)x.drawImage(ims[i],0,0)}})}}D.layers.forEach((l,i)=>{{let q=document.createElement('label'),b=document.createElement('input');b.type='checkbox';b.checked=true;b.onchange=draw;chs.push(b);q.append(b,' '+l.id);document.querySelector('#checks').append(q);let im=new Image();ims.push(im);im.onload=draw;im.src=l.uri}});</script></html>'''
    (ROOT / "apercu_forest_cave_render_v1.html").write_text(html, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    raw = Image.open(COMPOSITION_SOURCE).convert("RGBA")
    composition = raw.resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    rgba, outside = key_magenta(composition)
    for x, y in [(0, 0), (WIDTH - 1, 0), (0, HEIGHT - 1), (WIDTH - 1, HEIGHT - 1)]:
        assert outside[y, x], "final composition guide has a non-magenta outside corner"
    guide_dir = OUT / "provenance/generation"
    guide_dir.mkdir(parents=True, exist_ok=True)
    composition.save(guide_dir / "forest_cave_final_composition_magenta.png")
    clean = rgba.copy()
    clean[outside, :3] = 0
    clean[:, :, 3] = np.where(outside, 0, 255).astype(np.uint8)
    clean_image = Image.fromarray(clean, "RGBA")
    (OUT / "review").mkdir(parents=True, exist_ok=True)
    clean_image.save(OUT / "review/composition_final_transparent.png")
    masks = build_masks(rgba, outside)
    layers_dir = OUT / "provenance/final_layers"
    layers_dir.mkdir(parents=True, exist_ok=True)
    layers = []
    layer_records = []
    for layer_id, mask in masks.items():
        image = apply_mask(rgba, mask)
        filename = f"ForestRenderV1_{layer_id}.png"
        image.save(layers_dir / filename)
        layers.append((layer_id, image))
        layer_records.append({"id": layer_id, "file": filename, "pixels": int(mask.sum()), "generated_from_final_composition": True})
    recomposed = Image.new("RGBA", (WIDTH, HEIGHT))
    for _, image in layers:
        recomposed.alpha_composite(image)
    if recomposed.tobytes() != clean_image.tobytes():
        raise AssertionError("five generated layers do not recompose the final composition")
    recomposed.save(OUT / "review/composition_final.png")
    path_mask = path_from_composition(rgba, outside)
    stats = make_ground(OUT, layers, path_mask)
    shutil.copyfile(COMPOSITION_SOURCE, OUT / "provenance/generation/source_generation.png")
    write_header(OUT)
    patch_installer(OUT)
    shutil.copyfile(HERE / "README.md", OUT / "README.md")
    manifest = {
        "project": "forest_cave_render_v1_pmdo",
        "target": "PMDO 0.8.12",
        "workflow": "final generated composition on magenta -> chroma cleanup -> five aligned layers",
        "composition_source": {"file": str(COMPOSITION_SOURCE.relative_to(ROOT)), "sha256": sha256(COMPOSITION_SOURCE), "normalized_size": [WIDTH, HEIGHT]},
        "canonical_references": ["forêtglomypmdsky.png", "source/zones_south_north_v3/references/native_tree_complete.png"],
        "canonical_references_are_style_guides": True,
        "final_pixels_are_generated": True,
        "layer_count": 5,
        "layers": layer_records,
        "map": {"asset": ASSET, "size_px": [WIDTH, HEIGHT], "grid": [WIDTH // GRID, HEIGHT // GRID], **stats,
                "markers": [{"name": "entrance", "role": "south_arrival"}, {"name": "donjon_seuil", "role": "north_threshold"}]},
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
        "warp_destinations": "NOT CONFIGURED",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_preview(OUT, composition, layers)
    print(f"1 final generated forest composition -> 5 layers: {OUT}")


if __name__ == "__main__":
    main()
