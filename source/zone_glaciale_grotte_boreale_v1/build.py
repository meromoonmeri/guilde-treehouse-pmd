"""Zone glaciale / grotte boréale V1.

Pipeline de rendu (méthode Guilde) : deux images de composition générées sur
magenta sont conservées brutes, détourées de manière reproductible, puis
réparties en calques alignés. Le ciel opaque est indépendant ; l'aurore est un
calque transparent animé par onde transversale et palettes cyclées.

Ce dossier produit un RENDU éditable, pas un tileset ni une carte PMDO native.
"""
from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import io
import json
import math
import shutil
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "zone_glaciale_grotte_boreale_v1"
BRUTS = OUT / "bruts"
W, H = 1264, 1008  # 158 × 126 cellules de 8 px; les pixels générés ne sont pas redimensionnés.
GRID = 8
FRAMES = 16
FRAME_MS = 100
AURORA_H = 600
# Le terrain généré touche le haut de son brut. Le décaler ouvre un vrai ciel
# lisible pour l'aurore tout en gardant son arrivée au bord sud du canevas.
TERRAIN_Y = 200
TERRAIN_SOURCE_H = 808
SKY_SOURCE_H = 848

TERRAIN_BRUT = BRUTS / "terrain_grotte_glace_magenta.png"
SKY_BRUT = BRUTS / "ciel_nuit_sans_boreale.png"
AURORA_BRUT = BRUTS / "aurore_ruban_magenta.png"

# Palette explicite du calque boréal indexé. Les rampes 2..5 et 6..9 sont
# les seules entrées tournées : l'image-index et l'alpha restent inchangés.
BASE_PALETTE = [
    (0, 0, 0),       # 0 : RGB transparent, alpha fourni séparément
    (18, 13, 54),    # 1 : corps indigo fixe
    (9, 73, 119),    # 2..5 : rampe cyan / turquoise
    (12, 132, 156),
    (25, 203, 205),
    (149, 250, 239),
    (72, 20, 112),   # 6..9 : rampe violet / rose
    (138, 35, 169),
    (210, 58, 202),
    (247, 128, 227),
    (242, 210, 252), # 10 : éclat glacé fixe
    (34, 79, 164),   # 11 : bleu secondaire fixe
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def empty(size: tuple[int, int] = (W, H)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def mask_png(mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L")


def rgba_from_mask(source: Image.Image, mask: np.ndarray) -> Image.Image:
    arr = np.array(source.convert("RGBA"), copy=True)
    arr[~mask] = 0
    return Image.fromarray(arr, "RGBA")


def polygon(points: list[tuple[int, int]]) -> np.ndarray:
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(points, fill=255)
    return np.asarray(im) > 0


def flood_border(candidate: np.ndarray) -> np.ndarray:
    """Retourne la composante de candidate reliée à un bord de l'image."""
    seed = np.zeros(candidate.shape, dtype=bool)
    seed[0, :] = candidate[0, :]
    seed[-1, :] = candidate[-1, :]
    seed[:, 0] |= candidate[:, 0]
    seed[:, -1] |= candidate[:, -1]
    return ndimage.binary_propagation(seed, mask=candidate)


def extract_terrain() -> tuple[Image.Image, dict]:
    """Détoure le fond magenta du terrain sans modifier les pixels conservés."""
    raw = rgb(TERRAIN_BRUT)
    if raw.size != (W, SKY_SOURCE_H):
        raise ValueError(f"terrain brut inattendu : {raw.size}, attendu {(W, SKY_SOURCE_H)}")
    arr = np.asarray(raw)[:TERRAIN_SOURCE_H].copy()
    r, g, b = np.moveaxis(arr, -1, 0)
    # Il n'y a pas de rose dans ce terrain : le critère peut donc être plus
    # large que celui de l'aurore et absorbe aussi le dithering du fond.
    magenta_like = (
        (r > 150)
        & (b > 145)
        & (g < 105)
        & (np.abs(r.astype(np.int16) - b.astype(np.int16)) < 125)
    )
    background = flood_border(magenta_like)
    alpha = ~background
    cropped = np.dstack((arr, np.where(alpha, 255, 0).astype(np.uint8)))
    cropped[~alpha] = 0
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[TERRAIN_Y:TERRAIN_Y + TERRAIN_SOURCE_H] = cropped
    return Image.fromarray(out, "RGBA"), {
        "source_size": list(raw.size),
        "crop": [0, 0, W, TERRAIN_SOURCE_H],
        "placement": [0, TERRAIN_Y],
        "normalization": "crop vertical de 40 px de fond magenta inférieur, puis translation de 200 px pour ouvrir le ciel; aucun redimensionnement",
        "magenta_pixels_removed": int(background.sum()),
        "opaque_pixels": int(alpha.sum()),
    }


def extract_aurora() -> tuple[np.ndarray, np.ndarray, dict]:
    """Détoure l'aurore et recadre une fenêtre native de 1264×600.

    Les roses lumineux restent : seuls le magenta pur et son halo connexe aux
    bords deviennent transparents. Les poussières isolées de moins de 56 px
    sont retirées, ce qui évite de prendre des restes du fond pour des étoiles.
    """
    raw = np.asarray(rgb(AURORA_BRUT))
    if raw.shape[:2] != (768, 1376):
        raise ValueError(f"aurore brute inattendue : {raw.shape[1]}×{raw.shape[0]}")
    r, g, b = np.moveaxis(raw, -1, 0)
    pure_magenta = (r > 218) & (b > 198) & (g < 36) & (np.abs(r.astype(np.int16) - b.astype(np.int16)) < 68)
    border_candidate = (
        (r > 174)
        & (b > 155)
        & (g < 88)
        & (np.abs(r.astype(np.int16) - b.astype(np.int16)) < 105)
    )
    background = pure_magenta | flood_border(border_candidate)
    foreground = ~background
    labels, count = ndimage.label(foreground)
    sizes = np.bincount(labels.ravel())
    keep_ids = np.flatnonzero(sizes >= 56)
    keep_ids = keep_ids[keep_ids != 0]
    foreground = np.isin(labels, keep_ids)
    raw = raw.copy()
    raw[~foreground] = 0

    # Le recadrage garde le grand rideau et ses franges. Il ne change ni la
    # taille des pixels, ni le ratio du dessin généré.
    x0, y0 = 56, 0
    cropped_rgb = raw[y0:y0 + AURORA_H, x0:x0 + W]
    cropped_alpha = foreground[y0:y0 + AURORA_H, x0:x0 + W].astype(np.uint8) * 255
    cropped_rgb[cropped_alpha == 0] = 0
    return cropped_rgb, cropped_alpha, {
        "source_size": [1376, 768],
        "crop": [x0, y0, x0 + W, y0 + AURORA_H],
        "background_method": "magenta pur + composante magenta reliée aux bords; composants <56 px retirés",
        "opaque_pixels_after_crop": int((cropped_alpha > 0).sum()),
        "kept_components": int(len(keep_ids)),
    }


def split_stars(raw: Image.Image) -> tuple[Image.Image, Image.Image, dict]:
    """Extrait seulement les petites étoiles nettes; le grain reste dans le ciel."""
    if raw.size != (W, SKY_SOURCE_H):
        raise ValueError(f"ciel brut inattendu : {raw.size}")
    source = np.asarray(raw.convert("RGBA"))
    # Le brut est moins haut que le canevas final. Ses derniers pixels sombres
    # prolongent le fond derrière le terrain, qui les masque presque totalement.
    # Aucun pixel visible du brut n'est remis à l'échelle.
    arr = np.empty((H, W, 4), dtype=np.uint8)
    arr[:SKY_SOURCE_H] = source
    arr[SKY_SOURCE_H:] = source[SKY_SOURCE_H - 1:SKY_SOURCE_H]
    full = Image.fromarray(arr, "RGBA")
    median = np.asarray(full.convert("RGB").filter(ImageFilter.MedianFilter(9)))
    value = arr[:, :, :3].max(axis=2)
    delta = arr[:, :, :3].astype(np.int16) - median.astype(np.int16)
    bright = (delta.max(axis=2) > 40) & (value > 122)
    # Les pics de montagne et l'horizon ne font pas partie du calque étoiles.
    bright[H // 2:, :] = False
    labels, count = ndimage.label(bright)
    sizes = np.bincount(labels.ravel())
    keep = np.zeros_like(bright)
    for label_id in range(1, count + 1):
        if 1 <= sizes[label_id] <= 52:
            keep |= labels == label_id
    stars = np.zeros((H, W, 4), dtype=np.uint8)
    stars[keep, :3] = arr[keep, :3]
    stars[keep, 3] = 255
    sky = arr.copy()
    sky[keep, :3] = median[keep]
    sky[:, :, 3] = 255
    return Image.fromarray(sky, "RGBA"), Image.fromarray(stars, "RGBA"), {
        "source_size": [W, SKY_SOURCE_H],
        "source_placement": [0, 0],
        "bottom_extension": H - SKY_SOURCE_H,
        "method": "différence au médian local 9×9, composantes lumineuses de 1 à 52 px au-dessus de l'horizon",
        "star_pixels": int(keep.sum()),
        "star_components": int(sum(1 for i in range(1, count + 1) if 1 <= sizes[i] <= 52)),
    }


def centerline_x(y: np.ndarray | float) -> np.ndarray | float:
    """Axe doux du chemin, orienté explicitement sud → nord."""
    local_y = np.asarray(y) - TERRAIN_Y
    t = np.clip((local_y - 348) / (TERRAIN_SOURCE_H - 348), 0, 1)
    return 632 + 16 * np.sin(math.pi * t) - 9 * np.sin(2 * math.pi * t)


def route_mask(radius: float = 46.0) -> np.ndarray:
    yy, xx = np.mgrid[:H, :W]
    valid_y = (yy >= TERRAIN_Y + 342) & (yy < H)
    # Largeur qui se resserre légèrement à l'approche de la grotte.
    local_y = yy - TERRAIN_Y
    t = np.clip((local_y - 348) / (TERRAIN_SOURCE_H - 348), 0, 1)
    local_radius = radius + 12 * t
    return valid_y & (np.abs(xx - centerline_x(yy)) <= local_radius)


def detail_mask(alpha: np.ndarray) -> np.ndarray:
    """Détails en avant : cristaux et petits rochers autour du passage.

    Les boîtes sont intentionnellement larges : elles conservent les ombres de
    contact avec chaque cristal au lieu de découper l'objet à mi-pixel.
    """
    boxes = [
        # Grands cristaux et pierres situés DANS la vallée (les cristaux
        # accrochés aux parois restent dans les calques de falaise).
        (414, 420, 506, 501),
        (323, 495, 438, 622),
        (891, 486, 1022, 621),
        (781, 565, 866, 647),
        (210, 637, 287, 731),
        (327, 728, 439, 808),
    ]
    out = np.zeros((H, W), dtype=bool)
    for x0, y0, x1, y1 in boxes:
        out[y0 + TERRAIN_Y:y1 + TERRAIN_Y, x0:x1] = True
    # Fenêtres serrées : chaque pièce garde son ombre de contact sans emporter
    # une large tranche du sol de vallée.
    return out & alpha


def semantic_masks(terrain: Image.Image) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Crée une partition exhaustive du terrain généré en couches Guilde."""
    arr = np.asarray(terrain)
    alpha = arr[:, :, 3] > 0
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2])

    def at_terrain_y(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(x, y + TERRAIN_Y) for x, y in points]

    cave_region = polygon(at_terrain_y([
        (500, 204), (532, 162), (584, 142), (640, 144), (705, 166),
        (756, 215), (770, 365), (490, 365)
    ]))
    cave_dark = cave_region & alpha & (lum < 120)
    cave_rim = cave_region & alpha & ~cave_dark

    north_region = polygon(at_terrain_y([
        (0, 0), (W, 0), (W, 274), (1130, 310), (1050, 354), (920, 390),
        (785, 398), (756, 365), (500, 365), (468, 398), (335, 394),
        (210, 348), (0, 309)
    ]))
    left_region = polygon(at_terrain_y([
        (0, 208), (170, 163), (307, 212), (391, 310), (443, 402),
        (414, 492), (361, 570), (338, 684), (396, TERRAIN_SOURCE_H), (0, TERRAIN_SOURCE_H)
    ]))
    right_region = polygon(at_terrain_y([
        (W, 164), (1080, 188), (953, 245), (884, 345), (819, 414),
        (837, 500), (893, 587), (927, 694), (874, TERRAIN_SOURCE_H), (W, TERRAIN_SOURCE_H)
    ]))

    # Priorités : cave, falaise nord, détails ancrés, puis parois latérales.
    # Les rochers de vallée restent donc entiers devant une falaise et ne sont
    # pas découpés par la frontière large du volume latéral.
    used = cave_region
    north = alpha & north_region & ~used
    used |= north
    details = detail_mask(alpha) & ~used
    used |= details
    side = alpha & (left_region | right_region) & ~used
    used |= side
    path = alpha & route_mask() & ~used
    used |= path
    floor = alpha & ~used

    masks = {
        "02_sol_vallee_visible": floor,
        "03_chemin_sud_nord": path,
        "04_falaise_nord_glace": north,
        "05_falaises_laterales": side,
        "06_encadrement_grotte": cave_rim,
        "07_obscurite_grotte": cave_dark,
        "08_cristaux_rochers_avant": details,
    }
    # La partition doit inclure la région cave entière, même si les pixels
    # clairs/noirs sont découpés dans deux calques.
    union = np.zeros_like(alpha)
    for m in masks.values():
        union |= m
    if not np.array_equal(union, alpha):
        missing = int((alpha & ~union).sum())
        overlap = int(sum(m.astype(np.uint8) for m in masks.values()).max() > 1)
        raise AssertionError(f"partition terrain invalide: {missing} pixels manquants, overlap={overlap}")
    return masks, alpha, route_mask(radius=25)


def make_hidden_floor(terrain: Image.Image, alpha: np.ndarray) -> tuple[Image.Image, np.ndarray]:
    """Sol sous les reliefs : palette générée depuis le sol visible, jamais du ciel.

    Il est recouvert exactement par les calques visibles dans la composition.
    Il sert seulement à éviter le vide quand l'utilisateur isole les falaises.
    """
    arr = np.asarray(terrain)
    # Empreinte : silhouette terrain + continuité à la limite sud sur le chemin.
    footprint = alpha.copy()
    footprint[H - 3:H, 570:695] = True
    yy, xx = np.mgrid[:H, :W]
    palette = np.array([
        [178, 205, 237], [190, 215, 246], [203, 225, 248],
        [216, 236, 252], [228, 247, 253]
    ], dtype=np.uint8)
    # Motif discret : blocs de 8 px + ondes très lentes, sans flou ni alpha.
    coarse = (
        np.sin((xx // 8) * 0.43 + (yy // 8) * 0.17)
        + np.sin((xx // 8) * 0.09 - (yy // 8) * 0.37)
        + np.cos((xx // 16) * 0.21 + (yy // 16) * 0.19)
    )
    index = np.clip(np.rint((coarse + 3) / 6 * 4), 0, 4).astype(np.int8)
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[:, :, :3] = palette[index]
    out[:, :, 3] = np.where(footprint, 255, 0).astype(np.uint8)
    out[out[:, :, 3] == 0] = 0
    return Image.fromarray(out, "RGBA"), footprint


def indexed_aurora(rgb_arr: np.ndarray, alpha_arr: np.ndarray) -> tuple[np.ndarray, Image.Image]:
    """Réduit le dessin à des rampes lisibles qui peuvent réellement cycler."""
    rr = rgb_arr[:, :, 0].astype(float) / 255.0
    gg = rgb_arr[:, :, 1].astype(float) / 255.0
    bb = rgb_arr[:, :, 2].astype(float) / 255.0
    maximum = np.maximum.reduce([rr, gg, bb])
    minimum = np.minimum.reduce([rr, gg, bb])
    saturation = np.divide(maximum - minimum, maximum, out=np.zeros_like(maximum), where=maximum > 0)
    # Teinte HSV 0..1, sans dépendance à colorsys pixel par pixel.
    delta = maximum - minimum
    hue = np.zeros_like(maximum)
    nonzero = delta > 1e-6
    rmax = nonzero & (maximum == rr)
    gmax = nonzero & (maximum == gg)
    bmax = nonzero & (maximum == bb)
    hue[rmax] = ((gg[rmax] - bb[rmax]) / delta[rmax]) % 6
    hue[gmax] = (bb[gmax] - rr[gmax]) / delta[gmax] + 2
    hue[bmax] = (rr[bmax] - gg[bmax]) / delta[bmax] + 4
    hue /= 6.0
    lum = 0.299 * rr + 0.587 * gg + 0.114 * bb
    opaque = alpha_arr > 0
    idx = np.zeros(alpha_arr.shape, dtype=np.uint8)
    # Blanc glacé : seulement des éclats peu saturés très lumineux.
    icy_white = opaque & (maximum > 0.82) & (saturation < 0.34)
    # Les verts-cyan et bleus clairs sont dans une rampe de quatre valeurs.
    cyan = opaque & ~icy_white & ((hue >= 0.40) & (hue <= 0.61) | ((gg > rr * 1.12) & (gg >= bb * 0.72)))
    magenta = opaque & ~icy_white & ~cyan & ((hue >= 0.75) | (hue < 0.04))
    dark = opaque & (lum < 0.23)
    secondary_blue = opaque & ~cyan & ~magenta & ~icy_white & ~dark & (bb > rr * 1.20)
    level = np.clip((lum * 4).astype(int), 0, 3)
    idx[opaque] = 1
    idx[cyan] = 2 + level[cyan]
    idx[magenta] = 6 + level[magenta]
    idx[icy_white] = 10
    idx[secondary_blue] = 11
    idx[dark] = 1

    p = Image.fromarray(idx, "P")
    flat = [channel for colour in BASE_PALETTE for channel in colour] + [0] * (3 * (256 - len(BASE_PALETTE)))
    p.putpalette(flat)
    return idx, p


def palette_for_frame(frame: int) -> list[tuple[int, int, int]]:
    """Palette cycling : cyan vers l'avant, magenta en contre-courant."""
    phase = frame % 4
    pal = list(BASE_PALETTE)
    cyan = BASE_PALETTE[2:6]
    magenta = BASE_PALETTE[6:10]
    pal[2:6] = cyan[-phase:] + cyan[:-phase] if phase else cyan
    pal[6:10] = magenta[phase:] + magenta[:phase] if phase else magenta
    return pal


def deform_indices(index: np.ndarray, alpha: np.ndarray, frame: int) -> tuple[np.ndarray, np.ndarray]:
    """Onde transversale physique, sans wrap ni translation globale.

    Une même colonne se déplace verticalement de manière solidaire. Deux ondes
    de périodes entières font que l'étape 16 est strictement l'étape 0.
    """
    h, w = index.shape
    dest_index = np.zeros_like(index)
    dest_alpha = np.zeros_like(alpha)
    rows = np.arange(h)
    for x in range(w):
        wave = (
            8.0 * math.sin(2 * math.pi * (2 * x / w - frame / FRAMES))
            + 3.0 * math.sin(2 * math.pi * (5 * x / w + 2 * frame / FRAMES + 0.17))
        )
        dy = int(round(wave))
        source_y = rows - dy
        valid = (source_y >= 0) & (source_y < h)
        dest_index[valid, x] = index[source_y[valid], x]
        dest_alpha[valid, x] = alpha[source_y[valid], x]
    return dest_index, dest_alpha


def render_indexed(index: np.ndarray, alpha: np.ndarray, pal: list[tuple[int, int, int]]) -> Image.Image:
    table = np.asarray(pal, dtype=np.uint8)
    out = np.zeros((*index.shape, 4), dtype=np.uint8)
    out[:, :, :3] = table[index]
    out[:, :, 3] = alpha
    out[out[:, :, 3] == 0] = 0
    return Image.fromarray(out, "RGBA")


def full_canvas(overlay: Image.Image, y: int = 0) -> Image.Image:
    result = empty()
    result.alpha_composite(overlay, (0, y))
    return result


def compose(layers: list[Image.Image]) -> Image.Image:
    image = empty()
    for layer in layers:
        image.alpha_composite(layer)
    return image


def make_ora(path: Path, layers: list[tuple[str, Image.Image]]) -> None:
    """OpenRaster minimal, avec tous les calques de la composition phase 0."""
    root = ET.Element("image", w=str(W), h=str(H), name="Zone glaciale / grotte boréale V1")
    stack = ET.SubElement(root, "stack", opacity="1.0", visibility="visible", **{"composite-op": "svg:src-over"})
    merged = empty()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        # ORA convention : la première entrée de la pile est visuellement au-dessus.
        for n, (name, image) in enumerate(reversed(layers)):
            filename = f"data/layer{n:02d}.png"
            ET.SubElement(stack, "layer", name=name, src=filename, x="0", y="0", opacity="1.0", visibility="visible", **{"composite-op": "svg:src-over"})
            data = io.BytesIO()
            image.save(data, format="PNG")
            archive.writestr(filename, data.getvalue())
        for _, image in layers:
            merged.alpha_composite(image)
        data = io.BytesIO()
        merged.save(data, format="PNG")
        archive.writestr("mergedimage.png", data.getvalue())
        archive.writestr("stack.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True))


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_gallery(
    sky_path: Path,
    stars_path: Path,
    frame_paths: list[Path],
    terrain_layers: list[tuple[str, Path]],
) -> None:
    """Aperçu autonome, sans serveur ni ressources externes."""
    data = {
        "width": W,
        "height": H,
        "grid": GRID,
        "frameMs": FRAME_MS,
        "sky": data_uri(sky_path),
        "stars": data_uri(stars_path),
        "aurora": [data_uri(path) for path in frame_paths],
        "layers": [{"id": layer_id, "label": label, "src": data_uri(path)} for (layer_id, label), (_, path) in zip(LAYER_META, terrain_layers)],
    }
    template = (Path(__file__).with_name("viewer.html").read_text(encoding="utf-8"))
    (ROOT / "apercu_zone_glaciale_grotte_boreale_v1.html").write_text(
        template.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))),
        encoding="utf-8",
    )


LAYER_META = [
    ("01_sol_reconstitue", "sol reconstitué sous relief"),
    ("02_sol_vallee_visible", "sol de vallée visible"),
    ("03_chemin_sud_nord", "chemin sud → nord"),
    ("04_falaise_nord_glace", "falaise glaciaire nord"),
    ("05_falaises_laterales", "falaises latérales"),
    ("06_encadrement_grotte", "encadrement de grotte"),
    ("07_obscurite_grotte", "profondeur de grotte"),
    ("08_cristaux_rochers_avant", "cristaux et rochers avant"),
]


def review_sheets(
    static_layers: list[tuple[str, Image.Image]],
    aurora_frames: list[Image.Image],
) -> None:
    review = OUT / "review"
    # Planche de calques sur damier, lisible sans confondre transparence et noir.
    tile_w, tile_h = 316, 252
    cols = 3
    rows = math.ceil(len(static_layers) / cols)
    board = Image.new("RGBA", (cols * tile_w, rows * (tile_h + 26)), (12, 22, 42, 255))
    draw = ImageDraw.Draw(board)
    for i, (name, image) in enumerate(static_layers):
        x = (i % cols) * tile_w
        y = (i // cols) * (tile_h + 26)
        checker = Image.new("RGBA", (tile_w, tile_h), (31, 43, 68, 255))
        cd = ImageDraw.Draw(checker)
        for cy in range(0, tile_h, 16):
            for cx in range(0, tile_w, 16):
                if (cx // 16 + cy // 16) % 2:
                    cd.rectangle((cx, cy, cx + 15, cy + 15), fill=(21, 31, 51, 255))
        checker.alpha_composite(image.resize((tile_w, tile_h), Image.Resampling.NEAREST))
        board.alpha_composite(checker, (x, y))
        draw.text((x + 7, y + tile_h + 5), name, fill=(220, 237, 255, 255))
    board.convert("RGB").save(review / "planche_calques.png")

    # 4×4 phases complètes : permet de voir la déformation et le cycle coloré.
    phase_w, phase_h = 316, 252
    phases = Image.new("RGBA", (phase_w * 4, phase_h * 4), (5, 12, 29, 255))
    for i, frame in enumerate(aurora_frames):
        # Cette planche montre l'aurore sur un damier pour bien lire le mouvement,
        # sans faire passer une vignette réduite pour un asset d'import.
        thumb = frame.resize((phase_w, phase_h), Image.Resampling.NEAREST)
        phases.alpha_composite(thumb, ((i % 4) * phase_w, (i // 4) * phase_h))
    phases.convert("RGB").save(review / "planche_aurore_16_phases.png")


def build() -> None:
    for relative in ("calques", "masques", "animation/frames", "scene", "review"):
        target = OUT / relative
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    terrain, terrain_info = extract_terrain()
    sky, stars, sky_info = split_stars(rgba(SKY_BRUT))
    aurora_rgb, aurora_alpha, aurora_info = extract_aurora()
    masks, terrain_alpha, geometric_corridor = semantic_masks(terrain)
    hidden_floor, footprint = make_hidden_floor(terrain, terrain_alpha)

    # Exports de terrain, une partition source par calque + sol sous les volumes.
    static_images: dict[str, Image.Image] = {"01_sol_reconstitue": hidden_floor}
    for layer_id, _label in LAYER_META[1:]:
        static_images[layer_id] = rgba_from_mask(terrain, masks[layer_id])
    terrain.save(OUT / "review" / "terrain_detoure.png")
    mask_png(terrain_alpha).save(OUT / "masques" / "00_terrain_total.png")
    mask_png(footprint).save(OUT / "masques" / "01_empreinte_sol_reconstitue.png")
    mask_png(geometric_corridor).save(OUT / "masques" / "09_corridor_geometrique_sud_nord.png")
    for layer_id, source_mask in masks.items():
        mask_png(source_mask).save(OUT / "masques" / f"{layer_id}.png")

    sky_path = OUT / "calques" / "ZoneGlacialeV1_00_ciel_nuit.png"
    stars_path = OUT / "calques" / "ZoneGlacialeV1_00b_etoiles.png"
    sky.save(sky_path)
    stars.save(stars_path)
    terrain_layer_paths: list[tuple[str, Path]] = []
    for layer_id, label in LAYER_META:
        path = OUT / "calques" / f"ZoneGlacialeV1_{layer_id}.png"
        static_images[layer_id].save(path)
        terrain_layer_paths.append((layer_id, path))

    # Au préalable, conserve l'asset indexé et son alpha : la palette seule peut
    # être utilisée par une intégration future sans perdre la géométrie.
    indices, indexed = indexed_aurora(aurora_rgb, aurora_alpha)
    indexed.save(OUT / "animation" / "aurore_indexee.png")
    Image.fromarray(aurora_alpha, "L").save(OUT / "animation" / "aurore_alpha.png")

    aurora_frames: list[Image.Image] = []
    palettes: list[dict] = []
    frame_paths: list[Path] = []
    for frame_no in range(FRAMES):
        warped_index, warped_alpha = deform_indices(indices, aurora_alpha, frame_no)
        pal = palette_for_frame(frame_no)
        overlay = render_indexed(warped_index, warped_alpha, pal)
        canvas = full_canvas(overlay, 0)
        output_path = OUT / "animation" / "frames" / f"ZoneGlacialeV1_Aurore_{frame_no:02d}.png"
        canvas.save(output_path)
        frame_paths.append(output_path)
        aurora_frames.append(canvas)
        palettes.append({"frame": frame_no, "palette": [list(c) for c in pal]})
    (OUT / "animation" / "palettes_16frames.json").write_text(
        json.dumps(
            {
                "asset": "aurore_indexee.png",
                "alpha": "aurore_alpha.png",
                "period": 4,
                "animation_frames": FRAMES,
                "method": "rampes cyan 2-5 vers l'avant, violet-rose 6-9 en contre-courant; indices et alpha source fixes avant onde",
                "frames": palettes,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    # Effet seul et scènes complètes. Le GIF est volontairement demi-résolution
    # pour rester manipulable; les 16 PNG alignés sont les exports de référence.
    aurora_frames[0].save(
        OUT / "animation" / "aurore_16frames.webp",
        save_all=True,
        append_images=aurora_frames[1:],
        duration=FRAME_MS,
        loop=0,
        lossless=True,
        method=4,
    )
    solo_bg = Image.new("RGBA", (W, H), (8, 15, 36, 255))
    gif_frames = []
    for frame in aurora_frames:
        visual = solo_bg.copy()
        visual.alpha_composite(frame)
        gif_frames.append(visual.resize((W // 2, H // 2), Image.Resampling.NEAREST).convert("P", palette=Image.Palette.ADAPTIVE))
    gif_frames[0].save(
        OUT / "review" / "aurore_16frames.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False,
    )

    static_stack = [sky, stars]
    semantic_stack = [static_images[layer_id] for layer_id, _ in LAYER_META]
    scenes: list[Image.Image] = []
    for frame_no, aurora in enumerate(aurora_frames):
        scene = compose(static_stack + [aurora] + semantic_stack)
        scenes.append(scene)
        if frame_no in (0, 4, 8, 12):
            scene.save(OUT / "scene" / f"scene_{frame_no:02d}.png")
    scenes[0].save(OUT / "COMPOSITION.png")
    scene_gif = [scene.resize((W // 2, H // 2), Image.Resampling.NEAREST).convert("P", palette=Image.Palette.ADAPTIVE) for scene in scenes]
    scene_gif[0].save(
        OUT / "review" / "animation_complete.gif",
        save_all=True,
        append_images=scene_gif[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False,
    )

    # Visualisation de la route contrôlée : rouge=limites, vert=trajet sud→nord.
    control = scenes[0].copy()
    ca = np.asarray(control).copy()
    corridor = geometric_corridor
    ca[corridor, 0] = np.minimum(255, ca[corridor, 0].astype(np.int16) + 55)
    ca[corridor, 1] = np.maximum(0, ca[corridor, 1].astype(np.int16) - 28)
    ca[corridor, 2] = np.maximum(0, ca[corridor, 2].astype(np.int16) - 28)
    Image.fromarray(ca, "RGBA").save(OUT / "PASSAGE_SUD_NORD_CONTROLE.png")

    # ORA : phase 0 seulement, les phases sont livrées séparément et alignées.
    ora_layers = [
        ("00 Ciel nuit", sky),
        ("00b Étoiles", stars),
        ("00c Aurore frame 00", aurora_frames[0]),
        *[(label, static_images[layer_id]) for layer_id, label in LAYER_META],
    ]
    make_ora(OUT / "zone_glaciale_grotte_boreale_v1.ora", ora_layers)

    # Planches après les scènes, pour ne jamais afficher une donnée de preview
    # comme si elle était un asset importable.
    review_static = [("00 ciel nuit", sky), ("00b étoiles", stars), ("00c aurore frame 00", aurora_frames[0])] + [
        (label, static_images[layer_id]) for layer_id, label in LAYER_META
    ]
    review_sheets(review_static, aurora_frames)

    # La partition exacte du terrain ne dépend pas du sol caché. Sert également
    # de preuve de recomposition dans le test.
    partition = empty()
    for layer_id, _ in LAYER_META[1:]:
        partition.alpha_composite(static_images[layer_id])
    partition.save(OUT / "review" / "recomposition_terrain.png")

    manifest = {
        "title": "Zone glaciale — grotte boréale V1",
        "canvas_px": [W, H],
        "grid_px": GRID,
        "grid_cells": [W // GRID, H // GRID],
        "scope": "rendu multicouche éditable; pas un tileset, Ground, collision ni import PMDO certifié",
        "brief": "chemin praticable visuellement du sud au nord vers une grande grotte naturelle glaciaire; ciel nocturne à aurore animée",
        "route": {
            "from": {"edge": "sud", "approx_px": [632, H - 1]},
            "to": {"feature": "seuil de grotte nord", "approx_px": [632, TERRAIN_Y + 348]},
            "minimum_geometric_half_width_px": 25,
            "validation": "masque géométrique continu uniquement; pas une collision moteur",
        },
        "sources": [
            {"file": str(TERRAIN_BRUT.relative_to(ROOT)), "sha256": sha256(TERRAIN_BRUT), "role": "composition terrain générée sur magenta"},
            {"file": str(SKY_BRUT.relative_to(ROOT)), "sha256": sha256(SKY_BRUT), "role": "ciel opaque généré séparément"},
            {"file": str(AURORA_BRUT.relative_to(ROOT)), "sha256": sha256(AURORA_BRUT), "role": "dessin d'aurore généré sur magenta"},
        ],
        "matting": {"terrain": terrain_info, "sky_stars": sky_info, "aurora": aurora_info},
        "layers": [
            {"id": "00_ciel_nuit", "file": "calques/ZoneGlacialeV1_00_ciel_nuit.png", "role": "fond opaque"},
            {"id": "00b_etoiles", "file": "calques/ZoneGlacialeV1_00b_etoiles.png", "role": "overlay transparent fixe"},
            {"id": "00c_aurore", "file": "animation/frames/ZoneGlacialeV1_Aurore_00.png", "role": "overlay transparent animé"},
            *[
                {"id": layer_id, "file": f"calques/ZoneGlacialeV1_{layer_id}.png", "role": label}
                for layer_id, label in LAYER_META
            ],
        ],
        "animation": {
            "frames": FRAMES,
            "frame_ms": FRAME_MS,
            "duration_s": FRAMES * FRAME_MS / 1000,
            "movement": "onde transversale verticale par colonne; sans scroll ni wrap",
            "formula": "dy(x,f)=round(8*sin(2π*(2x/W-f/16))+3*sin(2π*(5x/W+2f/16+0.17)))",
            "palette_cycling": "indices fixes; rampes cyan 2..5 et violet-rose 6..9 tournent à contre-courant, période quatre",
            "loop": "frame 16 est mathématiquement identique à frame 0 avant encodage",
        },
        "outputs": {
            "composition": "COMPOSITION.png",
            "editable_ora": "zone_glaciale_grotte_boreale_v1.ora",
            "animation_webp": "animation/aurore_16frames.webp",
            "viewer": "apercu_zone_glaciale_grotte_boreale_v1.html",
        },
        "art_approved": False,
        "runtime_PMDO": "NOT TESTED",
        "credits": "Références Pokémon Mystery Dungeon fournies dans le dépôt; nouveaux rendus générés à revoir artistiquement. Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "placement_recipe.json").write_text(
        json.dumps(
            {
                "type": "descriptive render placement, not a PMDO file",
                "canvas_px": [W, H],
                "order_bottom_to_top": ["00_ciel_nuit", "00b_etoiles", "00c_aurore_frame_xx", *[layer_id for layer_id, _ in LAYER_META]],
                "animation": {"frames": FRAMES, "frame_ms": FRAME_MS, "loop": True, "scroll": False, "wrap": False},
                "route": f"centre sud (632,{H - 1}) vers seuil de grotte nord (632,{TERRAIN_Y + 348})",
                "note": "Configurer colliders, occlusion et warp dans le moteur cible; le masque de corridor est uniquement un contrôle de composition.",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    write_gallery(sky_path, stars_path, frame_paths, terrain_layer_paths)
    print(f"Built {OUT.relative_to(ROOT)}: {W}×{H}, {len(LAYER_META)} terrain layers, {FRAMES} aurora frames.")


if __name__ == "__main__":
    build()
