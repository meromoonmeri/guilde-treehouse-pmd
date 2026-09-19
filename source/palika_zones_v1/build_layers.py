"""Post-process the two AI-generated zone guides into Palika-style aligned layers.

The image generator creates the visual compositions.  This script deliberately does
not paint terrain or invent sprites: it only rescales the generated guides to the
native map canvas, builds semantic masks, writes transparent RGBA layers, and checks
that the ordered layers reconstruct each generated guide byte-for-byte.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import struct
import zipfile
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "palika_zones_v1"
# Palika's documented guided-zone canvas. The 512 coordinate helpers below are
# only normalized geometry templates; all delivered pixels use this native canvas.
SIZE = (2048, 1536)
TEMPLATE = (512, 512)
TILE = 8
GRID = (SIZE[0] // TILE, SIZE[1] // TILE)
RESAMPLE = Image.Resampling.LANCZOS
SCALE_X = SIZE[0] / TEMPLATE[0]
SCALE_Y = SIZE[1] / TEMPLATE[1]
AREA_SCALE = (SIZE[0] * SIZE[1]) / (TEMPLATE[0] * TEMPLATE[1])
PIXEL_SCALE = max(SCALE_X, SCALE_Y)

SOURCES = {
    "vast_steppe_automne_sud_nord": OUT / "generated_guides" / "vast_steppe_automne_zone_sud_nord_4x3.png",
    "foret_neigee_entree_nord_sud": OUT / "generated_guides" / "foret_neigee_entree_zone_nord_sud_4x3.png",
}

# Bottom-to-top order.  It follows the existing Amp Plains/Palika ordering while
# making the generated, dry entry layers explicit instead of pretending they are
# canonical Halcyon tiles.
COMMON_ORDER = [
    ("01_sol", "Sol de zone"),
    ("02_chemin", "Chemin sud vers nord"),
    ("03_bordures", "Bordures du passage"),
    ("04_parois", "Parois et retours rocheux"),
    ("05_rochers", "Rochers"),
    ("06_vegetation_basse", "Végétation basse"),
    ("07_arbres_massifs", "Arbres et massifs"),
    ("08_ombres_profondeur", "Ombres et profondeur"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_guide(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGB")
    if source.size != SIZE:
        # The image generator returns its own raster size (1200x896 here). Fit it
        # to Palika's documented 4:3 delivery canvas; this is not generation.
        source = source.resize(SIZE, RESAMPLE)
    return source


def rgb_masks(arr: np.ndarray):
    r, g, b = arr.astype(np.float32).transpose(2, 0, 1)
    hi = np.maximum.reduce([r, g, b])
    lo = np.minimum.reduce([r, g, b])
    return r, g, b, hi - lo, (r + g + b) / 3.0


def polygon_mask(polygons: list[list[tuple[int, int]]]) -> np.ndarray:
    im = Image.new("1", SIZE, 0)
    draw = ImageDraw.Draw(im)
    for poly in polygons:
        scaled = [(round(x * SCALE_X), round(y * SCALE_Y)) for x, y in poly]
        draw.polygon(scaled, fill=1)
    return np.asarray(im, dtype=bool)


def ellipse_mask(ellipses: list[tuple[int, int, int, int]]) -> np.ndarray:
    im = Image.new("1", SIZE, 0)
    draw = ImageDraw.Draw(im)
    for x0, y0, x1, y1 in ellipses:
        draw.ellipse((round(x0 * SCALE_X), round(y0 * SCALE_Y), round(x1 * SCALE_X), round(y1 * SCALE_Y)), fill=1)
    return np.asarray(im, dtype=bool)


def corridor_mask(zone: str) -> np.ndarray:
    """A deliberately generous S-N route guide; source pixels stay untouched."""
    y, x = np.mgrid[:SIZE[1], :SIZE[0]]
    # Evaluate the path template in 512x512 normalized coordinates, then map it
    # onto the 2048x1536 canvas without changing its south-to-north direction.
    yn = y / SCALE_Y
    xn = x / SCALE_X
    if zone == "vast_steppe_automne_sud_nord":
        center = 256 + 9 * np.sin((yn - 40) / 118.0)
        width = 30 + 13 * (yn / 511.0)
    else:
        center = 258 + 8 * np.sin((yn + 22) / 137.0)
        width = 35 + 12 * (yn / 511.0)
    return np.abs(xn - center) <= width


def rocky_banks(zone: str) -> np.ndarray:
    if zone == "vast_steppe_automne_sud_nord":
        polygons = [
            [(0, 214), (122, 214), (153, 236), (165, 268), (139, 301), (0, 301)],
            [(512, 214), (390, 214), (359, 236), (347, 268), (373, 301), (512, 301)],
            [(0, 430), (104, 430), (118, 512), (0, 512)],
            [(512, 430), (408, 430), (394, 512), (512, 512)],
        ]
    else:
        polygons = [
            [(0, 205), (138, 205), (161, 237), (153, 278), (121, 300), (0, 300)],
            [(512, 205), (374, 205), (351, 237), (359, 278), (391, 300), (512, 300)],
        ]
    return polygon_mask(polygons)


def entrance_mask() -> np.ndarray:
    # Central gateway, its dark opening, and the immediate stone/wood frame. The
    # forest beyond remains on the tree/massive layer, preserving depth.
    return polygon_mask([
        [(150, 208), (153, 152), (178, 112), (220, 88), (292, 88), (335, 112),
         (360, 154), (362, 218), (330, 224), (182, 224)],
        [(195, 111), (220, 76), (292, 76), (322, 112), (322, 178), (195, 178)],
    ])


def mountains_mask() -> np.ndarray:
    # The remote ridge is the upper background band in zone B.
    return polygon_mask([[(0, 0), (512, 0), (512, 92), (480, 83), (450, 91),
                          (420, 75), (386, 86), (350, 70), (315, 84), (278, 69),
                          (238, 84), (202, 68), (165, 85), (128, 70), (92, 86),
                          (54, 72), (0, 90)]])


def connected_components(mask: np.ndarray, min_size: int, max_size: int | None = None) -> np.ndarray:
    labels, count = ndi.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    keep = sizes >= min_size
    if max_size is not None:
        keep &= sizes <= max_size
    keep[0] = False
    return keep[labels]


def object_masks(zone: str, arr: np.ndarray, assigned: np.ndarray):
    """Return masks for rocks, low vegetation, and trees from generated pixels.

    These are conservative semantic selections. Any pixel not selected remains in
    the generated source and is assigned to 01_sol, so no repainting is hidden.
    """
    r, g, b, sat, lum = rgb_masks(arr)
    if zone == "vast_steppe_automne_sud_nord":
        foliage = ((r > g * 1.13) & (g > b * 1.24) & (g < 154) & (r > 75))
        foliage |= ((g >= r * 0.84) & (g > b * 1.14) & (g < 157) & (r > 40))
        dark_plant = (sat > 38) & (lum < 145) & (lum > 35)
    else:
        foliage = ((g >= r * 0.77) & (b >= r * 0.82) & (lum < 172) & (sat > 20))
        foliage |= ((g > r * 1.04) & (g > b * 1.05) & (g < 165))
        dark_plant = (sat > 20) & (lum < 155) & (lum > 30)

    # Large connected foliage clusters are massifs. Small clusters become low
    # vegetation, while the separate gray/brown connected components become rocks.
    trees = connected_components(foliage, round(55 * AREA_SCALE))
    # Dilate in output pixels to preserve the intended semantic edge width; the
    # pixels written still come from arr, never from a generated replacement.
    trees = ndi.binary_dilation(trees, iterations=round(PIXEL_SCALE))
    if zone == "foret_neigee_entree_nord_sud":
        trees &= ~mountains_mask()
        trees &= ~entrance_mask()

    rock_colour = ((sat < 62) & (lum > 62) & (lum < 184) & (r > b * 0.82))
    rocks = connected_components(rock_colour & ~trees, round(7 * AREA_SCALE), round(700 * AREA_SCALE))
    rocks = ndi.binary_dilation(rocks, iterations=round(PIXEL_SCALE))

    low = connected_components(dark_plant & ~trees & ~rocks, round(4 * AREA_SCALE), round(700 * AREA_SCALE))
    # Avoid turning the generated path into vegetation.
    low &= ~corridor_mask(zone)
    return rocks, low, trees


def make_layer_masks(zone: str, image: Image.Image):
    arr = np.asarray(image)
    assigned = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
    masks: list[tuple[str, str, np.ndarray]] = []

    def add(key: str, title: str, mask: np.ndarray):
        nonlocal assigned
        mask = np.asarray(mask, dtype=bool) & ~assigned
        masks.append((key, title, mask))
        assigned |= mask

    if zone == "foret_neigee_entree_nord_sud":
        add("00_montagnes_arriere_plan", "Chaîne de montagnes PMD au loin", mountains_mask())

    path = corridor_mask(zone)
    add("02_chemin", "Chemin sud vers nord", path)
    add("03_bordures", "Bordures du passage", ndi.binary_dilation(path, iterations=round(3 * PIXEL_SCALE)) & ~path)
    add("04_parois", "Parois et retours rocheux", rocky_banks(zone))

    rocks, low, trees = object_masks(zone, arr, assigned)
    add("05_rochers", "Rochers", rocks)
    add("06_vegetation_basse", "Végétation basse", low)
    add("07_arbres_massifs", "Arbres et massifs", trees)

    if zone == "foret_neigee_entree_nord_sud":
        add("09_entree_foret", "Entrée de la forêt enneigée", entrance_mask())

    # Keep a small dark ring as an explicit depth layer. It is selected only from
    # still-unassigned generated pixels, never painted by this script.
    r, g, b, sat, lum = rgb_masks(arr)
    depth_context = ndi.binary_dilation(assigned, iterations=round(2 * PIXEL_SCALE)) | ndi.binary_dilation(path, iterations=round(2 * PIXEL_SCALE))
    shadows = depth_context & (lum < 105) & ~assigned
    add("08_ombres_profondeur", "Ombres et profondeur", shadows)

    # Sol receives all residual generated pixels. This guarantees a complete,
    # disjoint partition and makes the reconstruction check meaningful.
    title = "Sol de zone"
    residual = ~assigned
    masks.insert(0 if zone != "foret_neigee_entree_nord_sud" else 1, ("01_sol", title, residual))
    assigned |= residual

    assert assigned.all(), f"Unassigned pixels in {zone}"
    keys = [key for key, _, _ in masks]
    assert len(keys) == len(set(keys))
    return masks


def rgba_masked(image: Image.Image, mask: np.ndarray) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    rgba[:, :, 3] = np.where(mask, 255, 0).astype(np.uint8)
    rgba[~mask, :3] = 0
    return Image.fromarray(rgba, "RGBA")


def compose(layers: list[Image.Image]) -> Image.Image:
    out = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    for layer in layers:
        out.alpha_composite(layer)
    return out


def write_ora(path: Path, named_layers: list[tuple[str, Image.Image]], composite: Image.Image):
    path.parent.mkdir(parents=True, exist_ok=True)
    def png_bytes(im: Image.Image) -> bytes:
        import io
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        return b.getvalue()

    root = ET.Element("image", w=str(SIZE[0]), h=str(SIZE[1]), name=path.stem)
    stack = ET.SubElement(root, "stack")
    # OpenRaster's first stack child is the top layer. Write in reverse of the
    # composition order while keeping every source at x=0,y=0.
    entries = []
    for i, (name, im) in enumerate(reversed(named_layers)):
        fn = f"data/{i:02d}.png"
        entries.append((fn, im))
        ET.SubElement(stack, "layer", name=name, src=fn, x="0", y="0", opacity="1.0", visibility="visible")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", ET.tostring(root, encoding="utf-8"))
        for fn, im in entries:
            z.writestr(fn, png_bytes(im))
        z.writestr("mergedimage.png", png_bytes(composite))


def _ase_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<H", len(raw)) + raw


def _ase_chunk(kind: int, payload: bytes) -> bytes:
    return struct.pack("<IH", len(payload) + 6, kind) + payload


def write_aseprite(path: Path, named_layers: list[tuple[str, Image.Image]]):
    """Write one fixed-frame RGBA Aseprite file, matching the local convention."""
    chunks = []
    for name, _ in named_layers:
        chunks.append(_ase_chunk(0x2004, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + _ase_string(name)))
    for index, (_, image) in enumerate(named_layers):
        box = image.getbbox()
        if box:
            x, y, _, _ = box
            cropped = image.crop(box)
        else:
            x = y = 0
            cropped = Image.new("RGBA", (1, 1))
        cel = struct.pack("<HhhBHh", index, x, y, 255, 2, 0)
        cel += b"\0" * 5 + struct.pack("<HH", cropped.width, cropped.height)
        cel += zlib.compress(cropped.tobytes(), 9)
        chunks.append(_ase_chunk(0x2005, cel))
    body = b"".join(chunks)
    frame = struct.pack("<IHHH2sI", len(body) + 16, 0xF1FA, len(chunks), 100, b"\0\0", len(chunks)) + body
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(frame) + 128, 0xA5E0, 1, SIZE[0], SIZE[1], 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.write_bytes(header + frame)


def write_tiled(path: Path, named_layers: list[tuple[str, Image.Image]]):
    # Image layers are intentional: the generated artwork is not claimed to be a
    # canonical tile atlas. The map keeps Palika's 8 px/256x192 coordinate contract.
    layers = []
    for i, (name, _) in enumerate(named_layers):
        layers.append({
            "id": i + 1,
            "name": name,
            "type": "imagelayer",
            "x": 0,
            "y": 0,
            "offsetx": 0,
            "offsety": 0,
            "opacity": 1,
            "visible": True,
            "image": f"layers/{name}.png",
            "imagewidth": SIZE[0],
            "imageheight": SIZE[1],
        })
    tmj = {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.10.2",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "width": GRID[0],
        "height": GRID[1],
        "tilewidth": TILE,
        "tileheight": TILE,
        "infinite": False,
        "layers": layers,
        "properties": [
            {"name": "palika_method", "type": "bool", "value": True},
            {"name": "generated_guide_only", "type": "bool", "value": True},
            {"name": "source_scale_correction", "type": "string", "value": "1200x896 to 2048x1536 after generator output"},
        ],
    }
    path.write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + "\n")


def write_control_mask(path: Path, mask: np.ndarray):
    im = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L")
    im.save(path, optimize=True)


def build_zone(zone: str, source: Path):
    out = OUT / zone
    layers_dir = out / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)
    image = load_guide(source)
    image.save(out / "COMPOSITION.png", optimize=True)
    masks = make_layer_masks(zone, image)
    named_layers = []
    for key, title, mask in masks:
        layer = rgba_masked(image, mask)
        layer.save(layers_dir / f"{key}.png", optimize=True)
        named_layers.append((key, layer))

    rebuilt = compose([im for _, im in named_layers])
    target = image.convert("RGBA")
    assert rebuilt.tobytes() == target.tobytes(), f"layer reconstruction failed for {zone}"
    assert all(im.mode == "RGBA" and im.size == SIZE for _, im in named_layers)
    alpha_sum = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
    for _, im in named_layers:
        alpha_sum += (np.asarray(im)[:, :, 3] > 0).astype(np.uint8)
    assert int(alpha_sum.max()) == 1, f"overlapping masks in {zone}"

    write_ora(out / "zone_seche.ora", named_layers, rebuilt)
    write_aseprite(out / "zone_seche.aseprite", named_layers)
    write_tiled(out / "zone_seche.tmj", named_layers)
    write_control_mask(out / "MASQUE_CHEMIN_SUD_NORD.png", corridor_mask(zone))
    if zone == "foret_neigee_entree_nord_sud":
        write_control_mask(out / "MASQUE_ENTREE_FORET.png", entrance_mask())
        write_control_mask(out / "MASQUE_MONTAGNES_LOINTAINES.png", mountains_mask())

    # Keep a compact layer index for gallery tooling and human inspection.
    index = [{"id": k, "name": t, "file": f"layers/{k}.png"} for k, t, _ in masks]
    manifest = {
        "id": zone,
        "source_generated_guide": str(source.relative_to(ROOT)),
        "source_generated_sha256": sha256(source),
        "source_generated_dimensions": list(Image.open(source).size),
        "delivery_dimensions": list(SIZE),
        "grid": {"tile_px": TILE, "columns": GRID[0], "rows": GRID[1], "origin": [0, 0]},
        "method": "Palika/Halcyon-inspired generated composition -> transparent semantic layers; no procedural terrain generation",
        "layer_order_bottom_to_top": index,
        "exports": ["COMPOSITION.png", "zone_seche.ora", "zone_seche.aseprite", "zone_seche.tmj"],
        "checks": {
            "rgba_layers": True,
            "common_canvas": True,
            "disjoint_alpha_masks": True,
            "ordered_reconstruction_exact": True,
            "path_reaches_south": bool(corridor_mask(zone)[-1].any()),
            "path_reaches_north": bool(corridor_mask(zone)[0].any()),
            "runtime_pmdo_validated": False,
            "collision_validated": False,
        },
        "notes": [
            "The image generator produced the two visual guides independently.",
            "The generator returned 1200x896; Lanczos fit to Palika's requested 2048x1536 map canvas is the only scale correction.",
            "Layer pixels are copied from the generated guide; Python supplies masks, alignment, controls, and exports only.",
            "The layers are generated composition assets, not certified canonical Halcyon tiles.",
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return image, named_layers, manifest


def build_gallery(results):
    # A small standalone viewer is the user-facing deliverable; no server or
    # runtime dependency is required.
    cards = []
    for zone, (image, layers, manifest) in results.items():
        layer_images = "".join(
            f'<img class="layer" data-layer="{entry["id"]}" src="{zone}/{entry["file"]}" alt="{entry["name"]}">'
            for entry in manifest["layer_order_bottom_to_top"]
        )
        options = "".join(
            f'<label><input type="checkbox" data-zone="{zone}" data-layer="{entry["id"]}" checked> {entry["name"]}</label>'
            for entry in manifest["layer_order_bottom_to_top"]
        )
        cards.append(f'''<section class="zone" data-zone="{zone}">
          <h2>{zone}</h2>
          <div class="canvas layerstack">{layer_images}</div>
          <div class="controls">{options}</div>
          <p><a href="{zone}/COMPOSITION.png">Composition PNG</a> · <a href="{zone}/zone_seche.ora">OpenRaster</a> · <a href="{zone}/zone_seche.aseprite">Aseprite</a> · <a href="{zone}/zone_seche.tmj">Tiled</a> · <a href="{zone}/manifest.json">manifest</a></p>
        </section>''')
    html = '''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Palika · deux zones générées et multicouches</title>
<style>body{background:#17261d;color:#edf1d7;font:15px system-ui;max-width:1180px;margin:24px auto;padding:0 20px}h1{color:#f0d69a}h2{color:#f0d69a;font-size:18px}.intro{line-height:1.55;max-width:950px}.zone{border:1px solid #587052;background:#21372a;padding:14px;margin:22px 0}.canvas{max-width:640px;background:repeating-conic-gradient(#2b4636 0 25%,#3b5943 0 50%) 0/16px 16px}.layerstack{position:relative;aspect-ratio:1}.layerstack .layer{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;image-rendering:pixelated}.controls{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.controls label{background:#304c38;border:1px solid #61785b;padding:6px 8px;border-radius:3px}.controls input{accent-color:#e5b65e}.zone a{color:#eac579}.hint{color:#b7c9b5}</style>
<h1>Palika · deux zones séparées</h1><p class="intro">Deux compositions générées séparément : Vast Steppe automnale avec passage sud → nord, puis entrée de forêt enneigée avec chaîne de montagnes PMD au loin. Les cases ci-dessous documentent les calques transparents RGBA sur canevas commun 2048 × 1536, grille 8 px. La génération visuelle vient du générateur d’image ; Python intervient seulement pour le redimensionnement de livraison, les masques, contrôles et exports.</p>
<div id="app">''' + "\n".join(cards) + '''</div><p class="hint">Les contrôles indiquent l’ordre Palika du bas vers le haut. Pour l’édition, ouvrir le fichier .ora dans Aseprite ou Krita ; le .tmj contient des image layers à cause du statut de guide généré, et ne prétend pas fournir un atlas canonique.</p>
<script>document.querySelectorAll('.zone').forEach(zone=>{zone.querySelectorAll('input').forEach(cb=>cb.addEventListener('change',()=>{const layer=zone.querySelector('.layer[data-layer="'+cb.dataset.layer+'"]');if(layer)layer.style.display=cb.checked?'block':'none'}));});</script></html>'''
    (OUT / "apercu_palika_zones_v1.html").write_text(html)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    manifest_zones = []
    for zone, source in SOURCES.items():
        image, layers, manifest = build_zone(zone, source)
        results[zone] = (image, layers, manifest)
        manifest_zones.append(manifest)
    build_gallery(results)
    root_manifest = {
        "method": "Palika/Halcyon-inspired multi-layer export of two separately generated compositions",
        "canvas": {"width": SIZE[0], "height": SIZE[1], "tilewidth": TILE, "tileheight": TILE, "grid": list(GRID)},
        "zones": [{"id": m["id"], "composition": f'{m["id"]}/COMPOSITION.png', "ora": f'{m["id"]}/zone_seche.ora', "aseprite": f'{m["id"]}/zone_seche.aseprite', "tmj": f'{m["id"]}/zone_seche.tmj'} for m in manifest_zones],
        "limitations": ["No PMDO import, collision, or runtime validation has been performed.", "Generated guides are not canonical Halcyon tiles."],
    }
    (OUT / "manifest.json").write_text(json.dumps(root_manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {len(results)} separate zones on {SIZE[0]}x{SIZE[1]} canvas with {TILE}px grid")


if __name__ == "__main__":
    main()
