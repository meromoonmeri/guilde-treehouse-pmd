"""Grotte glaciaire boréale V1.

Pipeline de rendu de la Guilde : trois sources générées sont conservées, les
fonds magenta sont détourés par inondation depuis les bords, puis la scène est
séparée en calques alignés.  Les aurores sont une animation en place de quatre
poses générées retenues et de douze intercalaires alpha-prémultipliés.

Ce script construit un rendu éditable/documenté.  Il ne produit pas un Ground,
un tileset natif ou des collisions PMDO.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import shutil
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict, deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUTPUT = ROOT / "renders/grotte_glaciaire_boreale_v1"
GENERATION = SOURCE / "generation"

CANVAS_W, CANVAS_H = 768, 640
GRID = 8
TERRAIN_RENDER_H = 429
AURORA_CELL_GRID = (2, 4)
SELECTED_AURORA_POSES = (0, 1, 2, 3)
FINAL_AURORA_FRAMES = 16
FRAME_MS = 120

INPUTS = OrderedDict(
    terrain=GENERATION / "terrain_magenta.png",
    aurora_sheet=GENERATION / "aurore_8_poses_magenta.png",
    sky=GENERATION / "ciel_nuit_sans_aurore.png",
)

TERRAIN_LAYER_LABELS = OrderedDict(
    [
        ("02_neige_et_sol", "Neige et sol visibles"),
        ("03_chemin_sud_nord", "Chemin praticable Sud → Nord"),
        ("04_grotte_et_seuil", "Vide de la grotte et seuil"),
        ("05_falaise_nord", "Falaise nord / couronne"),
        ("06_falaise_gauche", "Falaise latérale gauche"),
        ("07_falaise_droite", "Falaise latérale droite"),
        ("08_rochers_cristaux_avant", "Rochers et cristaux de premier plan"),
    ]
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def blank(size: tuple[int, int] = (CANVAS_W, CANVAS_H)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def flood_from_border(candidate: np.ndarray) -> np.ndarray:
    """Return only candidate pixels connected to the image border (4-connected)."""
    height, width = candidate.shape
    visited = np.zeros((height, width), dtype=bool)
    todo: deque[tuple[int, int]] = deque()

    for x in range(width):
        if candidate[0, x] and not visited[0, x]:
            visited[0, x] = True
            todo.append((0, x))
        if candidate[height - 1, x] and not visited[height - 1, x]:
            visited[height - 1, x] = True
            todo.append((height - 1, x))
    for y in range(height):
        if candidate[y, 0] and not visited[y, 0]:
            visited[y, 0] = True
            todo.append((y, 0))
        if candidate[y, width - 1] and not visited[y, width - 1]:
            visited[y, width - 1] = True
            todo.append((y, width - 1))

    while todo:
        y, x = todo.pop()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < height and 0 <= xx < width and candidate[yy, xx] and not visited[yy, xx]:
                visited[yy, xx] = True
                todo.append((yy, xx))
    return visited


def remove_border_magenta(image: Image.Image) -> tuple[Image.Image, int]:
    """Détoure le fond magenta sans effacer les accents violet/fuchsia internes.

    Le critère chromatique est volontairement large, mais seuls les pixels
    atteignables depuis le bord sont supprimés. Une lueur fuchsia enfermée dans
    un ruban conserve donc son dessin.
    """
    pixels = np.array(image.convert("RGBA"), copy=True)
    r, g, b = pixels[:, :, :3].astype(np.int16).transpose(2, 0, 1)
    candidate = (r > 165) & (b > 135) & (g < 140) & ((r - g) > 90) & ((b - g) > 60)
    background = flood_from_border(candidate)
    pixels[background] = 0
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels, "RGBA"), int(background.sum())


def fit_sky(image: Image.Image) -> tuple[Image.Image, dict]:
    """Centre-crop then uniformly nearest-neighbour scale; never stretch pixels."""
    source_w, source_h = image.size
    target_ratio = CANVAS_W / CANVAS_H
    source_ratio = source_w / source_h
    if source_ratio > target_ratio:
        crop_w = round(source_h * target_ratio)
        crop_h = source_h
        crop_x = (source_w - crop_w) // 2
        crop_y = 0
    else:
        crop_w = source_w
        crop_h = round(source_w / target_ratio)
        crop_x = 0
        crop_y = (source_h - crop_h) // 2
    crop = image.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    result = crop.resize((CANVAS_W, CANVAS_H), Image.Resampling.NEAREST)
    return result, {
        "source_size": [source_w, source_h],
        "crop_rect": [crop_x, crop_y, crop_x + crop_w, crop_y + crop_h],
        "output_size": [CANVAS_W, CANVAS_H],
        "scale": CANVAS_W / crop_w,
        "method": "center crop then uniform nearest-neighbor scale; no anisotropic resize",
    }


def place_terrain(image: Image.Image) -> tuple[Image.Image, dict]:
    """Keep the complete generated ravine and reserve open sky above it."""
    source_w, source_h = image.size
    render_w = CANVAS_W
    render_h = round(source_h * render_w / source_w)
    if render_h != TERRAIN_RENDER_H:
        # The expected source is 1376×768. This fallback still remains uniform.
        render_h = min(CANVAS_H, render_h)
    resized = image.resize((render_w, render_h), Image.Resampling.NEAREST)
    terrain = blank()
    x = (CANVAS_W - render_w) // 2
    y = CANVAS_H - render_h
    terrain.alpha_composite(resized, (x, y))
    return terrain, {
        "source_size": [source_w, source_h],
        "render_size": [render_w, render_h],
        "placement": [x, y],
        "uniform_scale": render_w / source_w,
        "method": "uniform nearest-neighbor scale, bottom anchored; open sky intentionally retained above",
    }


def polygon_mask(points: list[tuple[int, int]]) -> np.ndarray:
    image = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    ImageDraw.Draw(image).polygon(points, fill=255)
    return np.array(image) > 0


def apply_mask(image: Image.Image, mask: np.ndarray) -> Image.Image:
    pixels = np.array(image, copy=True)
    pixels[~mask] = 0
    return Image.fromarray(pixels, "RGBA")


def build_terrain_partitions(terrain: Image.Image) -> tuple[OrderedDict[str, Image.Image], OrderedDict[str, np.ndarray]]:
    """Create disjoint, aligned visible-surface partitions of the generated terrain.

    The partitions are not claims of complete 3-D objects behind every occluder;
    they are the editable visible surfaces of this one approved composition.
    """
    pixels = np.array(terrain)
    valid = pixels[:, :, 3] > 0
    yy, xx = np.indices((CANVAS_H, CANVAS_W))
    lum = (0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2])

    # The generated cave is visibly dark. Its rim remains in the north-cliff layer.
    cave_region = polygon_mask([(270, 306), (497, 306), (519, 353), (479, 410), (291, 410), (249, 353)])
    cave = cave_region & (lum < 132)

    # A deliberately generous continuous route, starting at the south map edge and
    # narrowing toward the cave threshold. It is only a visual/access audit mask.
    path = polygon_mask(
        [
            (286, 640), (482, 640), (459, 604), (439, 566), (448, 532),
            (429, 501), (441, 468), (421, 437), (426, 397), (346, 397),
            (351, 437), (330, 468), (338, 502), (318, 533), (329, 568),
            (309, 605),
        ]
    )
    foreground = valid & (
        ((yy >= 510) & ((xx < 300) | (xx > 475)))
        | ((yy >= 462) & ((xx < 102) | (xx > 666)))
    )
    north = valid & (yy < 430)
    left = valid & polygon_mask(
        [(0, 354), (128, 354), (232, 390), (305, 455), (315, 520), (284, 586), (248, 640), (0, 640)])
    right = valid & polygon_mask(
        [(768, 354), (640, 354), (536, 390), (462, 455), (453, 520), (484, 586), (520, 640), (768, 640)])

    claimed = np.zeros_like(valid)
    partitions: OrderedDict[str, np.ndarray] = OrderedDict()

    def take(layer_id: str, candidate: np.ndarray) -> None:
        nonlocal claimed
        selected = valid & candidate & ~claimed
        partitions[layer_id] = selected
        claimed |= selected

    # Claim in the semantic order below, then output in the documented compositing order.
    take("04_grotte_et_seuil", cave)
    take("03_chemin_sud_nord", path)
    take("08_rochers_cristaux_avant", foreground)
    take("05_falaise_nord", north)
    take("06_falaise_gauche", left)
    take("07_falaise_droite", right)
    partitions["02_neige_et_sol"] = valid & ~claimed

    ordered_masks = OrderedDict((layer_id, partitions[layer_id]) for layer_id in TERRAIN_LAYER_LABELS)
    layers = OrderedDict((layer_id, apply_mask(terrain, mask)) for layer_id, mask in ordered_masks.items())
    return layers, ordered_masks


def translate_without_wrap(image: Image.Image, dx: int, dy: int) -> Image.Image:
    source = np.array(image)
    destination = np.zeros_like(source)
    height, width = source.shape[:2]
    source_x0, source_x1 = max(0, -dx), min(width, width - dx)
    source_y0, source_y1 = max(0, -dy), min(height, height - dy)
    destination_x0, destination_x1 = max(0, dx), min(width, width + dx)
    destination_y0, destination_y1 = max(0, dy), min(height, height + dy)
    if source_x0 < source_x1 and source_y0 < source_y1:
        destination[destination_y0:destination_y1, destination_x0:destination_x1] = source[source_y0:source_y1, source_x0:source_x1]
    return Image.fromarray(destination, "RGBA")


def alpha_centroid(image: Image.Image) -> tuple[float, float]:
    alpha = np.array(image)[:, :, 3].astype(np.float64)
    total = alpha.sum()
    if not total:
        return CANVAS_W / 2, CANVAS_H / 2
    yy, xx = np.indices(alpha.shape)
    return float((xx * alpha).sum() / total), float((yy * alpha).sum() / total)


def iou(first: Image.Image, second: Image.Image) -> float:
    a = np.array(first)[:, :, 3] > 0
    b = np.array(second)[:, :, 3] > 0
    union = (a | b).sum()
    return float((a & b).sum() / union) if union else 1.0


def prepare_aurora_keyposes(sheet: Image.Image) -> tuple[list[Image.Image], list[Image.Image], list[dict], list[list[float]]]:
    """Extract the 2×4 sheet, retain its four coherent first poses, and anchor them."""
    columns, rows = AURORA_CELL_GRID
    cell_w, cell_h = sheet.width // columns, sheet.height // rows
    all_poses: list[Image.Image] = []
    removed: list[dict] = []

    for index in range(columns * rows):
        col, row = index % columns, index // columns
        cell = sheet.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
        cut, removed_pixels = remove_border_magenta(cell)
        scale = CANVAS_W / cell_w
        scaled_h = round(cell_h * scale)
        scaled = cut.resize((CANVAS_W, scaled_h), Image.Resampling.NEAREST)
        canvas = blank()
        canvas.alpha_composite(scaled, (0, 0))
        all_poses.append(canvas)
        removed.append(
            {
                "index": index,
                "cell_rect": [col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h],
                "removed_border_magenta_pixels": removed_pixels,
                "scaled_size": [CANVAS_W, scaled_h],
            }
        )

    matrix = [[round(iou(all_poses[i], all_poses[j]), 6) for j in range(len(all_poses))] for i in range(len(all_poses))]
    chosen_unaligned = [all_poses[index] for index in SELECTED_AURORA_POSES]
    reference_center = alpha_centroid(chosen_unaligned[0])
    alignment: list[dict] = []
    chosen: list[Image.Image] = []
    for source_index, image in zip(SELECTED_AURORA_POSES, chosen_unaligned):
        center = alpha_centroid(image)
        dx = round(reference_center[0] - center[0])
        dy = round(reference_center[1] - center[1])
        chosen.append(translate_without_wrap(image, dx, dy))
        alignment.append(
            {
                "source_pose": source_index,
                "centroid_before": [round(center[0], 3), round(center[1], 3)],
                "offset_px": [dx, dy],
                "centroid_after": [round(alpha_centroid(chosen[-1])[0], 3), round(alpha_centroid(chosen[-1])[1], 3)],
            }
        )
    return all_poses, chosen, alignment, matrix


def premultiplied_blend(first: Image.Image, second: Image.Image, amount: float) -> Image.Image:
    """Blend two transparent light layers without coloured fringes."""
    if amount <= 0:
        return first.copy()
    if amount >= 1:
        return second.copy()
    a = np.array(first).astype(np.float64)
    b = np.array(second).astype(np.float64)
    alpha_a = a[:, :, 3:4] / 255.0
    alpha_b = b[:, :, 3:4] / 255.0
    out_alpha = alpha_a * (1.0 - amount) + alpha_b * amount
    premultiplied = a[:, :, :3] * alpha_a * (1.0 - amount) + b[:, :, :3] * alpha_b * amount
    rgb = np.divide(premultiplied, np.maximum(out_alpha, 1e-12), out=np.zeros_like(premultiplied), where=out_alpha > 0)
    output = np.concatenate((rgb, out_alpha * 255.0), axis=2)
    output = np.rint(np.clip(output, 0, 255)).astype(np.uint8)
    output[output[:, :, 3] == 0, :3] = 0
    return Image.fromarray(output, "RGBA")


def aurora_frame_at(keyposes: list[Image.Image], frame_index: int) -> Image.Image:
    interval = FINAL_AURORA_FRAMES // len(keyposes)
    phase = frame_index % FINAL_AURORA_FRAMES
    source_index = phase // interval
    amount = (phase % interval) / interval
    result = premultiplied_blend(keyposes[source_index], keyposes[(source_index + 1) % len(keyposes)], amount)
    # The original sheet lets a few antialiased light pixels touch a cell edge.
    # Clear a six-pixel safety gutter after every blend: the overlay is genuinely
    # bounded and never relies on wrap-around pixels to hide a seam.
    pixels = np.array(result, copy=True)
    pixels[:, :6] = 0
    pixels[:, -6:] = 0
    return Image.fromarray(pixels, "RGBA")


def make_route_overlay(path_mask: np.ndarray) -> Image.Image:
    pixels = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)
    pixels[path_mask] = (255, 197, 54, 58)
    overlay = Image.fromarray(pixels, "RGBA")
    draw = ImageDraw.Draw(overlay)
    points = [(384, 632), (371, 591), (383, 552), (389, 517), (384, 482), (392, 447), (386, 407)]
    draw.line(points, fill=(255, 216, 91, 205), width=3)
    draw.polygon([(386, 393), (376, 412), (396, 412)], fill=(255, 216, 91, 220))
    return overlay


def compose_scene(sky: Image.Image, aurora: Image.Image, terrain_layers: OrderedDict[str, Image.Image]) -> Image.Image:
    scene = sky.copy()
    scene.alpha_composite(aurora)
    for layer in terrain_layers.values():
        scene.alpha_composite(layer)
    return scene


def write_ora(path: Path, layers: OrderedDict[str, Image.Image]) -> None:
    root = ET.Element("image", w=str(CANVAS_W), h=str(CANVAS_H), name="Grotte glaciaire boréale V1")
    stack = ET.SubElement(root, "stack")
    merged = blank()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        # ORA lists topmost first. Reversing here lets a consumer reverse the list
        # and alpha-composite it bottom-to-top.
        for index, (name, image) in reversed(list(enumerate(layers.items()))):
            file_name = f"data/layer{index}.png"
            ET.SubElement(
                stack,
                "layer",
                name=name,
                src=file_name,
                x="0",
                y="0",
                opacity="1.0",
                visibility="visible",
                **{"composite-op": "svg:src-over"},
            )
            payload = io.BytesIO()
            image.save(payload, format="PNG")
            archive.writestr(file_name, payload.getvalue())
        for image in layers.values():
            merged.alpha_composite(image)
        payload = io.BytesIO()
        merged.save(payload, format="PNG")
        archive.writestr("mergedimage.png", payload.getvalue())
        archive.writestr("stack.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True))


def image_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    media = {".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}[suffix]
    return f"data:{media};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_contact_sheet(keyposes: list[Image.Image], scenes: list[Image.Image]) -> None:
    review = OUTPUT / "review"
    board = Image.new("RGB", (768, 448), (8, 18, 43))
    label_draw = ImageDraw.Draw(board)
    for index, keypose in enumerate(keyposes):
        thumb = Image.new("RGBA", (768, 320), (8, 18, 43, 255))
        thumb.alpha_composite(keypose.crop((0, 0, 768, 320)))
        thumb = thumb.convert("RGB").resize((384, 160), Image.Resampling.NEAREST)
        x, y = (index % 2) * 384, (index // 2) * 224
        board.paste(thumb, (x, y + 22))
        # Pillow's portable default bitmap font is ASCII only.
        label_draw.text((x + 12, y + 4), f"Pose {SELECTED_AURORA_POSES[index]} - ancree", fill=(194, 231, 248))
    board.save(review / "planche_poses_retenues.png")

    # Four full scene thumbnails, not cropped strips: this is the visual review of
    # the actual south-to-north composition through the cycle.
    composition = Image.new("RGB", (768, 640), (8, 18, 43))
    for index, phase in enumerate((0, 4, 8, 12)):
        thumb = scenes[phase].resize((384, 320), Image.Resampling.NEAREST)
        x, y = (index % 2) * 384, (index // 2) * 320
        composition.paste(thumb, (x, y))
    composition.save(review / "planche_animation_4_phases.png")


def output_readme() -> str:
    return """# Grotte glaciaire boréale V1 — chemin Sud → Nord

## Livraison visuelle

Nouvelle zone glaciale **768 × 640 px**, sur grille de présentation 8 px : un chemin enneigé arrive au **sud**, remonte sans coupure vers une **grotte prise dans la falaise nord**, sous un ciel nocturne dont l’aurore vit sur son propre calque. La scène est une proposition de rendu PMD et un document de travail éditable ; ce n’est ni un tileset natif, ni une Ground PMDO, ni une collision jouable.

## Méthode Guilde appliquée

1. Trois images originales ont été générées séparément : terrain complet sur magenta, ciel sans aurore, planche 2 × 4 d’aurores sur magenta.
2. Le magenta extérieur est retiré par inondation depuis les bords, sans supprimer les accents violets enfermés dans les rubans.
3. Le terrain reste une composition complète — **aucun morceau de map existante n’est assemblé** — et est réparti en surfaces visibles indépendantes : neige, chemin, vide de grotte, falaise nord, deux falaises latérales et premier plan.
4. Les quatre poses générées les plus cohérentes sont ancrées au même repère ; leurs intercalaires sont fondus en alpha prémultiplié. L’aurore a 16 phases de 120 ms (1,92 s), sur transparence, **sans wrap ni défilement**.
5. Chaque rendu est vérifié : séparation exacte des calques, absence du fond magenta extérieur, chemin continu Sud → seuil nord, animation bouclée, ORA, GIF/WebP et aperçu autonome.

## Fichiers

- `bruts/` — sources générées exactes, magenta et ciel conservés.
- `calques/` — ciel opaque et 7 plans terrain RGBA alignés.
- `animation/aurore_frames/` — 16 overlays transparents 768 × 640 ; `aurore_16frames.webp` est la boucle sans perte.
- `animation/keyposes/` — les quatre poses générées retenues et ancrées ; les quatre autres restent visibles dans le brut, mais ne sont pas intégrées car leurs silhouettes dérivent trop pour une boucle propre.
- `masques/` — masques binaires des surfaces visibles.
- `grotte_glaciaire_boreale_v1.ora` — scène multicouche, phase 0 incluse.
- `review/` — GIFs, planches, scène pleine définition et tracé de contrôle du passage (ce dernier n’est pas un asset de jeu).
- `placement_recipe.json` / `manifest.json` — ordre de rendu, timing, provenance, positions et limites.
- `apercu.html` dans le ZIP ; `apercu_grotte_glaciaire_boreale_v1.html` à la racine du dépôt : lecture/pause, phases, calques, grille et tracé Sud → Nord.

## Animation et limites

L’aurore est une **nouvelle animation proposée**, construite à partir de poses générées avec la référence PMD fournie : ce n’est pas un cycle officiel extrait du jeu. Le ciel et le terrain restent fixes. Les huit poses du brut ne sont pas toutes acceptées automatiquement : l’audit de recouvrement sélectionne 0–3 afin de conserver une déformation douce autour d’un ancrage commun ; 4–7 sont archivées dans la planche source, pas silencieusement recyclées.

Les images de référence Pokémon restent la propriété de leurs ayants droit. Les rendus ici sont générés, inspirés par la DA fournie, et **ne prétendent pas être des pixels canoniques ni une autorisation de redistribution**. Aucun import PMDO, parallax moteur, collision, warp, test GPU ou approbation artistique utilisateur n’est déclaré. Le contrôle de chemin est géométrique ; il ne remplace pas les collisions moteur.

## Reproduction

```sh
.venv/bin/python source/grotte_glaciaire_boreale_v1/build.py
.venv/bin/python source/grotte_glaciaire_boreale_v1/package.py
```
"""


def write_viewer(sky_path: Path, aurora_paths: list[Path], terrain_paths: OrderedDict[str, Path], route_path: Path) -> None:
    data = {
        "width": CANVAS_W,
        "height": CANVAS_H,
        "frameMs": FRAME_MS,
        "sky": image_data_uri(sky_path),
        "aurora": [image_data_uri(path) for path in aurora_paths],
        "route": image_data_uri(route_path),
        "terrain": [
            {"id": layer_id, "label": TERRAIN_LAYER_LABELS[layer_id], "uri": image_data_uri(path)}
            for layer_id, path in terrain_paths.items()
        ],
    }
    template = (SOURCE / "viewer.html").read_text()
    (ROOT / "apercu_grotte_glaciaire_boreale_v1.html").write_text(template.replace("__DATA__", json.dumps(data, ensure_ascii=False)))


def build() -> None:
    missing = [str(path) for path in INPUTS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing generated input(s): " + ", ".join(missing))

    for relative in ("bruts", "calques", "masques", "animation/aurore_frames", "animation/keyposes", "review"):
        (OUTPUT / relative).mkdir(parents=True, exist_ok=True)

    # Preserve the exact generator responses alongside the delivery.
    for key, path in INPUTS.items():
        destination = OUTPUT / "bruts" / path.name
        shutil.copy2(path, destination)

    raw_terrain, terrain_background_removed = remove_border_magenta(rgba(INPUTS["terrain"]))
    terrain, terrain_normalization = place_terrain(raw_terrain)
    sky, sky_normalization = fit_sky(rgba(INPUTS["sky"]))
    terrain_layers, terrain_masks = build_terrain_partitions(terrain)

    sky_path = OUTPUT / "calques/GrotteGlaciaireV1_00_ciel_nuit.png"
    sky.save(sky_path)
    terrain_paths: OrderedDict[str, Path] = OrderedDict()
    for layer_id, layer in terrain_layers.items():
        layer_path = OUTPUT / "calques" / f"GrotteGlaciaireV1_{layer_id}.png"
        mask_path = OUTPUT / "masques" / f"GrotteGlaciaireV1_{layer_id}.png"
        layer.save(layer_path)
        Image.fromarray(np.where(terrain_masks[layer_id], 255, 0).astype(np.uint8), "L").save(mask_path)
        terrain_paths[layer_id] = layer_path
    terrain.save(OUTPUT / "review/terrain_detoure.png")

    all_poses, keyposes, alignment, iou_matrix = prepare_aurora_keyposes(rgba(INPUTS["aurora_sheet"]))
    for index, keypose in enumerate(keyposes):
        keypose.save(OUTPUT / "animation/keyposes" / f"GrotteGlaciaireV1_pose_{SELECTED_AURORA_POSES[index]:02d}_ancree.png")

    aurora_frames = [aurora_frame_at(keyposes, frame) for frame in range(FINAL_AURORA_FRAMES)]
    aurora_paths: list[Path] = []
    for frame, image in enumerate(aurora_frames):
        path = OUTPUT / "animation/aurore_frames" / f"GrotteGlaciaireV1_Aurore_{frame:02d}.png"
        image.save(path)
        aurora_paths.append(path)
    aurora_frames[0].save(
        OUTPUT / "animation/aurore_16frames.webp",
        save_all=True,
        append_images=aurora_frames[1:],
        duration=[FRAME_MS] * FINAL_AURORA_FRAMES,
        loop=0,
        lossless=True,
        method=4,
    )

    scenes = [compose_scene(sky, aurora, terrain_layers) for aurora in aurora_frames]
    for phase in (0, 4, 8, 12):
        scenes[phase].save(OUTPUT / "review" / f"scene_phase_{phase:02d}.png")
    scenes[0].save(OUTPUT / "review/COMPOSITION_PHASE_00.png")

    # GIFs are view-only previews; authoritative alpha/RGB data stays in the PNG/WebP files.
    scene_palette = scenes[0].convert("RGB").quantize(colors=256)
    scene_gif = [scene.convert("RGB").quantize(palette=scene_palette, dither=Image.Dither.NONE) for scene in scenes]
    scene_gif[0].save(
        OUTPUT / "review/animation_scene.gif",
        save_all=True,
        append_images=scene_gif[1:],
        duration=[FRAME_MS] * FINAL_AURORA_FRAMES,
        loop=0,
        disposal=1,
        optimize=False,
    )
    aurora_preview = []
    for image in aurora_frames:
        background = sky.crop((0, 0, CANVAS_W, 320))
        background.alpha_composite(image.crop((0, 0, CANVAS_W, 320)))
        aurora_preview.append(background.convert("RGB"))
    aurora_palette = aurora_preview[0].quantize(colors=256)
    aurora_gif = [image.quantize(palette=aurora_palette, dither=Image.Dither.NONE) for image in aurora_preview]
    aurora_gif[0].save(
        OUTPUT / "review/animation_aurore_seule.gif",
        save_all=True,
        append_images=aurora_gif[1:],
        duration=[FRAME_MS] * FINAL_AURORA_FRAMES,
        loop=0,
        disposal=1,
        optimize=False,
    )
    write_contact_sheet(keyposes, scenes)

    route_overlay = make_route_overlay(terrain_masks["03_chemin_sud_nord"])
    route_path = OUTPUT / "review/trace_sud_nord_CONTROLE_NON_IMPORT.png"
    route_overlay.save(route_path)
    route_review = scenes[0].copy()
    route_review.alpha_composite(route_overlay)
    route_review.save(OUTPUT / "review/PASSAGE_SUD_NORD_CONTROLE.png")

    ora_layers: OrderedDict[str, Image.Image] = OrderedDict(
        [("00_ciel_nuit", sky), ("01_aurore_phase_00", aurora_frames[0]), *terrain_layers.items()]
    )
    write_ora(OUTPUT / "grotte_glaciaire_boreale_v1.ora", ora_layers)

    min_path_width = min(int(terrain_masks["03_chemin_sud_nord"][y].sum()) for y in range(410, CANVAS_H) if terrain_masks["03_chemin_sud_nord"][y].any())
    manifest = {
        "title": "Grotte glaciaire boréale V1",
        "canvas_px": [CANVAS_W, CANVAS_H],
        "presentation_grid_px": GRID,
        "orientation": "arrival at the south edge, continuous snowy route to the north ice-cave threshold",
        "workflow": [
            "separate generated terrain on magenta, generated sky without aurora, and generated aurora pose sheet",
            "border-connected magenta removed by flood fill; enclosed violet/fuchsia light accents retained",
            "full generated terrain retained as one composition and partitioned into editable visible-surface layers",
            "four coherent generated aurora poses anchored and alpha-premultiplied interpolated into sixteen in-place frames",
            "non-destructive PNG masks, ORA, animation previews, manifest, tests and standalone layer viewer",
        ],
        "inputs": [
            {
                "id": key,
                "file": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "size": list(rgba(path).size),
            }
            for key, path in INPUTS.items()
        ],
        "magenta_extraction": {
            "terrain_border_pixels_removed": terrain_background_removed,
            "method": "chroma candidate plus 4-connected flood fill from the external image border",
        },
        "terrain": {
            "origin": "new complete generated ravine/cave composition, not assembled from map fragments",
            "normalization": terrain_normalization,
            "visible_surface_partition_only": True,
            "layers": [
                {"id": layer_id, "label": label, "file": str(terrain_paths[layer_id].relative_to(OUTPUT))}
                for layer_id, label in TERRAIN_LAYER_LABELS.items()
            ],
        },
        "sky": {
            "origin": "new generated opaque night sky without aurora",
            "normalization": sky_normalization,
            "file": str(sky_path.relative_to(OUTPUT)),
            "animated": False,
        },
        "aurora": {
            "origin": "four selected generated poses, interpolated into a new proposed in-place animation; not an official recovered PMD cycle",
            "sheet_grid": list(AURORA_CELL_GRID),
            "candidate_poses": list(range(8)),
            "selected_source_poses": list(SELECTED_AURORA_POSES),
            "not_integrated_source_poses": [4, 5, 6, 7],
            "selection_reason": "poses 0–3 maintain the same anchored ribbon family; later raw cells have larger silhouette/hue drift and remain archived in the untouched source sheet",
            "pairwise_iou_raw_poses": iou_matrix,
            "alignment": alignment,
            "frames": FINAL_AURORA_FRAMES,
            "frame_ms": FRAME_MS,
            "cycle_ms": FINAL_AURORA_FRAMES * FRAME_MS,
            "interpolation": "four intervals × four steps; premultiplied-alpha crossfades, no geometric scroll or wrap",
            "loop": "virtual frame 16 equals frame 0 exactly",
            "wrap": False,
            "placement": [0, 0],
            "frames_directory": "animation/aurore_frames",
            "webp": "animation/aurore_16frames.webp",
        },
        "path_audit": {
            "direction": "south to north",
            "arrival_edge": "south/bottom edge",
            "target": "ice-cave threshold at north",
            "minimum_visual_mask_width_px": min_path_width,
            "route_mask": "masques/GrotteGlaciaireV1_03_chemin_sud_nord.png",
            "collision": "NOT CONFIGURED — visual continuity is not a PMDO collision test",
        },
        "render_order": list(ora_layers),
        "ora": "grotte_glaciaire_boreale_v1.ora",
        "runtime_PMDO": "NOT TESTED",
        "art_approved": False,
        "limits": [
            "Generated PMD-inspired artwork is not a canonical-native tile extraction.",
            "Visible-surface layer separation does not reconstruct every hidden cliff backface or interior.",
            "No Ground, tileset, parallax setup, collision, warp, GPU test or runtime PMDO test is provided.",
        ],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    placement = {
        "schema": "descriptive placement recipe, not a native PMDO engine file",
        "canvas_px": [CANVAS_W, CANVAS_H],
        "grid_px": GRID,
        "render_order": list(ora_layers),
        "aurora": {
            "frames": FINAL_AURORA_FRAMES,
            "frame_duration_ms": FRAME_MS,
            "cycle_ms": FINAL_AURORA_FRAMES * FRAME_MS,
            "position_px": [0, 0],
            "loop": True,
            "wrap": False,
            "note": "swap only the aurora texture every 120 ms; keep sky and terrain fixed",
        },
        "route": {
            "entry": [384, 639],
            "target": [386, 407],
            "direction": "South -> North",
            "collision_imported": False,
        },
    }
    (OUTPUT / "placement_recipe.json").write_text(json.dumps(placement, ensure_ascii=False, indent=2) + "\n")
    (OUTPUT / "README.md").write_text(output_readme())
    write_viewer(sky_path, aurora_paths, terrain_paths, route_path)
    print(
        f"Built Grotte glaciaire boréale V1: {CANVAS_W}x{CANVAS_H}, "
        f"7 terrain layers, {FINAL_AURORA_FRAMES} aurora frames / {FINAL_AURORA_FRAMES * FRAME_MS / 1000:.2f}s."
    )


if __name__ == "__main__":
    build()
