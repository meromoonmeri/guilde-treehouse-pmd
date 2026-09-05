"""Kit modulaire 32 px : objets, parquet, spirales et couloirs top view.

Le générateur n'est pas appelé pendant le build. Sa planche retenue est
archivée dans source/tilesheets ; détourages et exports sont déterministes.
Les douze salles existantes ne sont jamais réécrites par ce script.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFont
import hashlib
import json
import math
import numpy as np

from rebuild_kit import ase

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/tilesheets"
OUT = ROOT / "tilesheets"
TILE = 32
FRAME = 96
MODES = ("jour", "nuit")
SEED = 9052026
NEIGHBORS = [(0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8),
             (1, -1, 16), (1, 1, 32), (-1, 1, 64), (-1, -1, 128)]
# Couleurs prélevées/rapprochées du plancher et du bois de notre guilde.
WOOD = {"joint": (146, 69, 4), "ombre": (152, 76, 8), "fonce": (199, 124, 24),
        "miel": (221, 145, 25), "ambre": (234, 167, 33), "clair": (243, 172, 57),
        "reflet": (251, 189, 78), "pale": (250, 206, 118)}
BASE_OBJECTS = [
    ("banniere_feuille", "Bannière feuille sur deux montants", (32, 52), "mur"),
    ("banniere_guilde", "Bannière verte et or", (32, 48), "mur"),
    ("liane_gauche", "Liane feuillue gauche", (24, 64), "mur"),
    ("guirlande_gauche", "Guirlande de lierre gauche", (64, 32), "mur"),
    ("nid_paille", "Paillasse de paille dorée", (48, 32), "sol"),
    ("nid_mousse", "Paillasse de mousse", (48, 32), "sol"),
    ("tapis_ocre", "Tapis tissé ocre", (64, 56), "tapis"),
    ("tapis_mauve", "Tapis tissé mauve", (64, 56), "tapis"),
    ("coffre_bleu", "Coffre cerclé bleu", (32, 32), "sol"),
    ("coffre_feuille", "Coffre de bois et feuille", (32, 32), "sol"),
    ("panier_baies", "Panier de baies", (32, 32), "sol"),
    ("jarre_feuille", "Jarre à bouchon feuille", (24, 32), "sol"),
    ("sac_explorateur", "Sac et carte roulée", (32, 32), "sol"),
    ("paillasses_roulees", "Paillasses roulées", (40, 32), "sol"),
    ("seau_bois", "Seau de bois", (24, 24), "sol"),
    ("buches", "Fagot de bûches", (32, 24), "sol"),
]


def rgba(path):
    return Image.open(path).convert("RGBA")


def save(im, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)


def json_file(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def night(im, alpha_factor=1.):
    a = np.array(im.convert("RGBA"))
    a[:, :, :3] = np.rint(a[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype("uint8")
    a[:, :, 3] = np.rint(a[:, :, 3] * alpha_factor).astype("uint8")
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def atlas(images, columns, cell):
    rows = math.ceil(len(images) / columns)
    result = Image.new("RGBA", (columns * cell, rows * cell))
    for i, im in enumerate(images):
        result.alpha_composite(im, (i % columns * cell, i // columns * cell))
    return result


def grid_ase(path, layers, size):
    # Le format reste le même que le kit de salles ; seule sa grille change.
    ase(path, layers, size)
    data = bytearray(path.read_bytes())
    import struct
    struct.pack_into("<HH", data, 40, TILE, TILE)
    path.write_bytes(data)


def object_shadow(im, group, mode):
    result = Image.new("RGBA", im.size)
    if group != "sol":
        return result
    w, h = im.size
    yy, xx = np.indices((h, w))
    radius = max(5, (im.getbbox()[2] - im.getbbox()[0]) * .45)
    distance = ((xx - w / 2) / radius) ** 2 + ((yy - (h - 6)) / 4) ** 2
    alpha = (np.rint(np.clip(1 - distance, 0, 1) * (68 if mode == "jour" else 76) / 8) * 8).astype("uint8")
    a = np.zeros((h, w, 4), np.uint8)
    a[:, :, :3] = (33, 19, 8) if mode == "jour" else (9, 12, 21)
    a[:, :, 3] = alpha
    a[alpha == 0] = 0
    return Image.fromarray(a)


def extract_objects():
    master = rgba(SOURCE / "objets_source.png")
    prepared = []
    for i, (ident, name, maximum, group) in enumerate(BASE_OBJECTS):
        col, row = i % 4, i // 4
        x0, x1 = round(col * master.width / 4), round((col + 1) * master.width / 4)
        y0, y1 = round(row * master.height / 4), round((row + 1) * master.height / 4)
        # Retirer les filets de grille de la proposition, jamais les silhouettes.
        crop = master.crop((x0 + 5, y0 + 5, x1 - 5, y1 - 5))
        a = np.array(crop)
        r, g, b = [a[:, :, j].astype(int) for j in range(3)]
        magenta = (r > g + 40) & (b > g + 35) & (b > 100)
        a[magenta] = 0
        # Décontaminer les très fins pixels de frange issus du fond magenta,
        # sans toucher le tissu mauve à l'intérieur de son cadre.
        from scipy.ndimage import binary_dilation
        border = binary_dilation(a[:, :, 3] == 0, iterations=1) & (a[:, :, 3] > 0)
        spill = border & (r > g + 25) & (b > g + 10)
        a[spill, 2] = np.minimum(a[spill, 2], np.rint(a[spill, 1] * .5).astype('uint8'))
        crop = Image.fromarray(a)
        crop = crop.crop(crop.getbbox())
        if ident == "banniere_feuille":
            # Garder le tissu et son emblème ; fabriquer les deux montants fins
            # demandés par la référence, plutôt qu'un fanion sur simple barre.
            crop = crop.crop((0, 22, crop.width, crop.height))
        crop.thumbnail(maximum, Image.Resampling.NEAREST)
        a = np.array(crop)
        a[:, :, 3] = np.where(a[:, :, 3] > 127, 255, 0)
        a[a[:, :, 3] == 0] = 0
        crop = Image.fromarray(a).quantize(colors=32 if group == "mur" else 64, method=Image.Quantize.FASTOCTREE).convert("RGBA")
        if ident == "banniere_feuille":
            pennant = Image.new("RGBA", (40, 80))
            d = ImageDraw.Draw(pennant)
            lx, rx = (40 - crop.width) // 2 + 2, (40 + crop.width) // 2 - 4
            for x in (lx, rx):
                d.rectangle((x, 3, x + 2, 30), fill=(85, 47, 16, 255))
                d.line((x + 1, 4, x + 1, 29), fill=(240, 181, 88, 255))
                for y in (9, 17, 24):
                    d.point((x + 1, y), fill=(153, 88, 25, 255))
            pennant.alpha_composite(crop, ((40 - crop.width) // 2, 29))
            d.rectangle((lx - 2, 27, rx + 4, 30), fill=(103, 57, 17, 255))
            d.line((lx - 1, 27, rx + 3, 27), fill=(248, 196, 102, 255))
            crop = pennant
        else:
            w = math.ceil((crop.width + 8) / 8) * 8
            h = math.ceil((crop.height + 8) / 8) * 8
            padded = Image.new("RGBA", (w, h))
            padded.alpha_composite(crop, ((w - crop.width) // 2, h - crop.height - 4))
            crop = padded
        prepared.append((ident, name, group, crop))
    for base, ident, name in [(2, "liane_droite", "Liane feuillue droite"), (3, "guirlande_droite", "Guirlande de lierre droite")]:
        _, _, group, im = prepared[base]
        prepared.append((ident, name, group, ImageOps.mirror(im)))
    small = prepared[4][3].resize((40, 32), Image.Resampling.NEAREST)
    prepared.append(("nid_paille_petit", "Petite paillasse", "sol", small))
    moss = np.array(prepared[7][3])
    r, g, b = [moss[:, :, j].astype(int) for j in range(3)]
    mask = (b > g) & (r < 205) & (moss[:, :, 3] > 0)
    value = moss[mask, :3].mean(axis=1)
    moss[mask, :3] = np.column_stack([value * .70, value * .86, value * .37]).clip(0, 255).astype("uint8")
    prepared.append(("tapis_mousse", "Tapis tissé mousse", "tapis", Image.fromarray(moss)))

    records = []
    frames, shadows = {m: [] for m in MODES}, {m: [] for m in MODES}
    object_images = {m: [] for m in MODES}
    shadow_images = {m: [] for m in MODES}
    for index, (ident, name, group, im) in enumerate(prepared):
        assert max(im.size) <= 88
        pivot = [im.width // 2, im.height - 4]
        files = {}
        for mode in MODES:
            sprite = im if mode == "jour" else night(im)
            shadow = object_shadow(sprite, group, mode)
            file = f"objets/individuels/{ident}_{mode}.png"
            shadow_file = f"objets/ombres/{ident}_{mode}.png"
            save(sprite, OUT / file)
            save(shadow, OUT / shadow_file)
            frame, sf = Image.new("RGBA", (FRAME, FRAME)), Image.new("RGBA", (FRAME, FRAME))
            pos = (FRAME // 2 - pivot[0], FRAME - 8 - pivot[1])
            frame.alpha_composite(sprite, pos)
            sf.alpha_composite(shadow, pos)
            frames[mode].append(frame)
            shadows[mode].append(sf)
            object_images[mode].append(sprite)
            shadow_images[mode].append(shadow)
            files[mode] = {"png": file, "ombre": shadow_file}
        records.append({"id": ident, "nom": name, "groupe": group, "taille": list(im.size),
                        "pivot": pivot, "ancrage": "bas-centre" if group != "mur" else "mur, ancrage à adapter",
                        "index": index, "rect_atlas": [index % 4 * FRAME, index // 4 * FRAME, FRAME, FRAME], "fichiers": files})
    for mode in MODES:
        sheet, shade = atlas(frames[mode], 4, FRAME), atlas(shadows[mode], 4, FRAME)
        save(sheet, OUT / "objets" / f"objets_{mode}.png")
        save(shade, OUT / "objets" / f"ombres_{mode}.png")
        grid_ase(OUT / "objets" / f"objets_{mode}.aseprite", [("Ombres séparées", shade), ("Objets", sheet)], sheet.size)
    return records, object_images, shadow_images


def floor_tile(index):
    """Planches horizontales à phase 8 px ; bords communs à toutes les variantes."""
    rng = np.random.default_rng(SEED + index)
    a = np.zeros((TILE, TILE, 4), np.uint8)
    shades = [WOOD[k] for k in ["miel", "ambre", "clair", "miel"]]
    for y in range(TILE):
        row, iy = y // 8, y % 8
        base = np.array(shades[row])
        if iy == 0:
            base = np.array(WOOD["joint"])
        elif iy == 1:
            base = np.array(WOOD["reflet"])
        elif iy == 7:
            base = np.array(WOOD["fonce"])
        a[y, :, :3] = base
        a[y, :, 3] = 255
    im = Image.fromarray(a)
    draw = ImageDraw.Draw(im)
    for row in range(4):
        for k in range(4):
            y = row * 8 + int(rng.integers(3, 7))
            x0 = int(rng.integers(3, 22))
            length = int(rng.integers(3, 13))
            color = WOOD["clair"] if k % 2 else WOOD["fonce"]
            draw.line((x0, y, min(28, x0 + length), y), fill=(*color, 255))
        if index in [3, 5, 7, 10, 12, 14] and row == index % 4:
            x = 7 + (index * 7) % 18
            draw.line((x, row * 8 + 2, x, row * 8 + 6), fill=(*WOOD["ombre"], 255))
            draw.line((x + 1, row * 8 + 3, x + 1, row * 8 + 6), fill=(*WOOD["clair"], 255))
    return im


def canonical(mask):
    for bit, adjacent in [(16, 1 | 2), (32, 2 | 4), (64, 4 | 8), (128, 8 | 1)]:
        if mask & adjacent:
            mask &= ~bit
    return mask


def distance_to_neighbors(mask):
    yy, xx = np.indices((TILE, TILE), dtype=float)
    xx += .5
    yy += .5
    distances = np.full((TILE, TILE), 100., dtype=float)
    for dx, dy, bit in NEIGHBORS:
        if not mask & bit:
            continue
        x0, y0 = dx * TILE, dy * TILE
        delta_x = np.maximum(np.maximum(x0 - xx, xx - (x0 + TILE)), 0)
        delta_y = np.maximum(np.maximum(y0 - yy, yy - (y0 + TILE)), 0)
        distances = np.minimum(distances, np.hypot(delta_x, delta_y))
    return np.floor(distances + 1e-8)


def wall_tile(mask):
    if mask == 0:
        return Image.new("RGBA", (TILE, TILE))
    d = distance_to_neighbors(mask)
    yy, xx = np.indices(d.shape)
    a = np.zeros((TILE, TILE, 4), np.uint8)
    colors = [(78, 40, 15), (125, 69, 22), (165, 98, 33), (188, 123, 48), (211, 151, 70), (94, 48, 16)]
    for mask2, col in [(d < 3, colors[0]), ((d >= 3) & (d < 8), colors[1]),
                       ((d >= 8) & (d < 13), colors[2]), ((d >= 13) & (d < 20), colors[3]),
                       ((d >= 20) & (d < 22), colors[4]), ((d >= 22) & (d < 24), colors[5])]:
        a[mask2] = (*col, 255)
    # Veines longues suivant le bois, plutôt qu'un bruit qui évoquerait du liège.
    # Les bords de chaque tuile restent communs aux pièces de raccord.
    gy, gx = np.gradient(d)
    tangent = np.where(np.abs(gy) >= np.abs(gx), xx, yy)
    inside = (d >= 8) & (d < 20) & (xx > 2) & (xx < 29) & (yy > 2) & (yy < 29)
    bend = np.rint(np.sin(tangent / 31 * math.pi) * 1.3)
    for level, lo, hi in [(10, 4, 21), (15, 8, 27), (18, 3, 16)]:
        grain = inside & (d == level + bend) & (tangent >= lo) & (tangent <= hi)
        a[grain, :3] = (146, 83, 26)
        highlight = inside & (d == level + bend + 1) & (tangent >= lo + 2) & (tangent < hi)
        a[highlight, :3] = (206, 142, 61)
    # Le clair reste une arête, jamais un halo.
    return Image.fromarray(a)


def contact_tile(mask):
    yy, xx = np.indices((TILE, TILE), dtype=float)
    alpha = np.zeros((TILE, TILE), float)
    for bit, distance, peak in [(1, yy, 88), (2, TILE - 1 - xx, 56), (4, TILE - 1 - yy, 52), (8, xx, 80)]:
        if mask & bit:
            alpha = np.maximum(alpha, peak * np.clip(1 - distance / 8, 0, 1) ** 1.4)
    a = np.zeros((TILE, TILE, 4), np.uint8)
    a[:, :, :3] = (34, 19, 7)
    a[:, :, 3] = np.rint(alpha / 8).astype("uint8") * 8
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def spiral(index):
    im = Image.new("RGBA", (64, 64))
    draw = ImageDraw.Draw(im)
    direction = -1 if index % 2 else 1
    radii = [13, 19, 24, 18]
    radius = radii[(index // 2) % 4]
    turns = [1.25, 1.65, 2.1, 1.45][index // 4]
    points = []
    for t in np.linspace(0, turns * math.tau, 120):
        r = 2 + (radius - 2) * t / (turns * math.tau)
        x = 32 + math.cos(t * direction + .3) * r
        y = 32 + math.sin(t * direction + .3) * r * (.7 if index >= 8 else .85)
        points.append((round(x), round(y)))
    # Faux creux très léger et usure claire : les deux restent transparents.
    draw.line([(x, y + 1) for x, y in points], fill=(119, 71, 16, 36), width=2)
    opacity = [72, 88, 100, 60][index // 4]
    draw.line(points, fill=(252, 221, 135, opacity), width=2 if index < 12 else 1)
    if index in [6, 7, 10, 11]:
        for x, y in points[::17]:
            draw.point((x + 2, y), fill=(254, 232, 167, 36))
    return im


def tile_set(name, file, width, height, count, columns, tiles=None):
    result = {"type": "tileset", "version": "1.10", "tiledversion": "1.11.0", "name": name,
              "tilewidth": TILE, "tileheight": TILE, "tilecount": count, "columns": columns,
              "margin": 0, "spacing": 0, "image": "../" + file, "imagewidth": width, "imageheight": height}
    if tiles is not None:
        result["tiles"] = tiles
    return result


def layouts():
    result = []
    def add(ident, name, width, height, rectangles, exits, objects=(), motif=None):
        mask = np.zeros((height, width), bool)
        for x0, y0, x1, y1 in rectangles:
            mask[y0:y1, x0:x1] = True
        result.append({"id": ident, "nom": name, "largeur": width, "hauteur": height,
                       "floor": mask, "exits": exits, "objects": list(objects), "motif": motif})
    add("couloir_horizontal", "Couloir est-ouest", 9, 5, [(0, 1, 9, 4)], ["E", "O"])
    add("couloir_vertical", "Couloir nord-sud", 5, 9, [(1, 0, 4, 9)], ["N", "S"])
    add("angle_nord_est", "Angle nord-est", 7, 7, [(2, 0, 5, 5), (2, 2, 7, 5)], ["N", "E"])
    add("angle_sud_ouest", "Angle sud-ouest", 7, 7, [(2, 2, 5, 7), (0, 2, 5, 5)], ["S", "O"])
    add("jonction_t", "Jonction en T", 9, 7, [(0, 3, 9, 6), (3, 0, 6, 6)], ["N", "E", "O"])
    add("croisement", "Croisement à quatre branches", 9, 9, [(0, 3, 9, 6), (3, 0, 6, 9)], ["N", "E", "S", "O"])
    add("palier_baies", "Palier des provisions", 11, 9, [(2, 2, 9, 7), (0, 3, 11, 6)], ["E", "O"],
        [(6, 176, 176), (10, 240, 119), (11, 112, 204), (9, 252, 204)], (5, 4, 5))
    add("antichambre", "Antichambre nord-sud", 9, 11, [(2, 2, 7, 9), (3, 0, 6, 11)], ["N", "S"],
        [(7, 144, 206), (4, 92, 134), (5, 196, 259), (12, 207, 114)], (8, 3, 3))
    add("halte_explorateurs", "Halte des explorateurs", 11, 11, [(2, 2, 9, 9), (4, 0, 7, 9), (2, 4, 11, 7)], ["N", "E"],
        [(19, 176, 220), (4, 100, 127), (5, 244, 260), (13, 114, 259), (14, 253, 117)], (10, 4, 3))
    return result


def neighbor_mask(floor, x, y, wanted=True, diagonals=True):
    h, w = floor.shape
    mask = 0
    for dx, dy, bit in NEIGHBORS[:8 if diagonals else 4]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and bool(floor[ny, nx]) == wanted:
            mask |= bit
    return mask


def paint_tiles(ids, sheet, cols, size):
    width, height = size
    result = Image.new("RGBA", (width * TILE, height * TILE))
    for y in range(height):
        for x in range(width):
            index = ids[y, x]
            if index < 0:
                continue
            sx, sy = int(index) % cols * TILE, int(index) // cols * TILE
            result.alpha_composite(sheet.crop((sx, sy, sx + TILE, sy + TILE)), (x * TILE, y * TILE))
    return result


def build():
    for folder in ["objets", "parquet", "spirales", "architecture", "tiled", "modules", "apercus"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    objects, object_images, shadow_images = extract_objects()
    horizontal = [floor_tile(i) for i in range(16)]
    floors = horizontal + [im.transpose(Image.Transpose.ROTATE_90) for im in horizontal]
    valid_masks = sorted({canonical(i) for i in range(256)})
    wall_lookup = {m: i for i, m in enumerate(valid_masks)}
    walls = [wall_tile(m) for m in valid_masks]
    contacts = [contact_tile(i) for i in range(16)]
    motifs = [spiral(i) for i in range(16)]
    sheets, refs = {}, {}
    for mode in MODES:
        def variant(items, alpha=1.):
            return items if mode == "jour" else [night(q, alpha) for q in items]
        sheets[mode] = {"parquet": atlas(variant(floors), 8, TILE),
                        "structure": atlas(variant(walls), 8, TILE),
                        "contacts": atlas(variant(contacts), 4, TILE),
                        "spirales": atlas(variant(motifs, .55), 4, 64)}
        specs = [("parquet", "parquet", 32, 8), ("structure", "architecture", math.ceil(len(walls) / 8) * 8, 8),
                 ("contacts", "architecture", 16, 4), ("spirales", "spirales", 64, 8)]
        refs[mode] = {}
        first = 1
        for key, folder, count, cols in specs:
            im = sheets[mode][key]
            filename = f"{folder}/{key}_{mode}.png"
            save(im, OUT / filename)
            if key == "structure":
                records = [{"id": i, "properties": [{"name": "voisins_sol", "type": "int", "value": m}]} for i, m in enumerate(valid_masks)]
            elif key == "parquet":
                records = [{"id": i, "properties": [{"name": "orientation", "type": "string", "value": "horizontal" if i < 16 else "vertical"}]} for i in range(32)]
            else:
                records = None
            ts = tile_set(f"{key}_{mode}", filename, *im.size, count, cols, records)
            json_file(ts, OUT / "tiled" / f"{key}_{mode}.tsj")
            refs[mode][key] = {"firstgid": first, "source": f"../../tiled/{key}_{mode}.tsj", "count": count}
            first += count
        for key, is_shadow in [("objets", False), ("ombres_objets", True)]:
            records = []
            for item in objects:
                file = item["fichiers"][mode]["ombre" if is_shadow else "png"]
                records.append({"id": item["index"], "image": "../" + file,
                                "imagewidth": item["taille"][0], "imageheight": item["taille"][1],
                                "properties": [{"name": "identifiant", "type": "string", "value": item["id"]}]})
            ts = {"type": "tileset", "version": "1.10", "tiledversion": "1.11.0", "name": key + "_" + mode,
                  "tilewidth": FRAME, "tileheight": FRAME, "tilecount": len(objects), "columns": 0,
                  "objectalignment": "bottomleft", "tiles": records}
            json_file(ts, OUT / "tiled" / f"{key}_{mode}.tsj")
            refs[mode][key] = {"firstgid": first, "source": f"../../tiled/{key}_{mode}.tsj", "count": len(objects)}
            first += len(objects)
        for i, im in enumerate(variant(motifs, .55)):
            save(im, OUT / "spirales" / "individuelles" / f"spirale_{i + 1:02d}_{mode}.png")
        # Un document de travail à deux vrais calques, pas des marques déjà peintes dans le parquet.
        floor_demo = Image.new("RGBA", (256, 256))
        for y in range(8):
            for x in range(8):
                tile = floors[(x * 3 + y * 5) % 16]
                floor_demo.alpha_composite(tile if mode == "jour" else night(tile), (x * TILE, y * TILE))
        grid_ase(OUT / "parquet" / f"parquet_et_spirales_{mode}.aseprite",
                 [("Parquet sans motifs", floor_demo), ("Traces spiralées transparentes", sheets[mode]["spirales"])], (256, 256))

    module_records = []
    gids = {mode: {key: data["firstgid"] for key, data in refs[mode].items()} for mode in MODES}
    for number, definition in enumerate(layouts()):
        ident, width, height, floor = definition["id"], definition["largeur"], definition["hauteur"], definition["floor"]
        fd = OUT / "modules" / ident
        fd.mkdir(parents=True, exist_ok=True)
        fields = {key: np.full((height, width), -1, dtype=int) for key in ["parquet", "structure", "contacts", "spirales"]}
        for y in range(height):
            for x in range(width):
                if floor[y, x]:
                    fields["parquet"][y, x] = (x * 7 + y * 11 + number * 3) % 16
                    fields["contacts"][y, x] = neighbor_mask(floor, x, y, False, False)
                else:
                    mask = canonical(neighbor_mask(floor, x, y))
                    if mask:
                        fields["structure"][y, x] = wall_lookup[mask]
        if definition["motif"]:
            mi, mx, my = definition["motif"]
            assert floor[my:my + 2, mx:mx + 2].all()
            for dy in range(2):
                for dx in range(2):
                    fields["spirales"][my + dy, mx + dx] = (mi // 4 * 2 + dy) * 8 + mi % 4 * 2 + dx
        exits = []
        for direction in definition["exits"]:
            edge = {"N": floor[0], "S": floor[-1], "O": floor[:, 0], "E": floor[:, -1]}[direction]
            locations = np.where(edge)[0]
            assert len(locations) == 3 and np.all(np.diff(locations) == 1)
            center = float((locations[0] + locations[-1] + 1) * TILE / 2)
            point = {"N": [center, 0], "S": [center, height * TILE], "O": [0, center], "E": [width * TILE, center]}[direction]
            exits.append({"direction": direction, "ancrage_px": point, "largeur_px": 96,
                          "cellules": [int(locations[0]), int(locations[-1])], "ouvert": True})
        save(Image.fromarray(floor.astype("uint8") * 255).resize((width * TILE, height * TILE), Image.Resampling.NEAREST), fd / "sol_praticable.png")
        rec = {"id": ident, "nom": definition["nom"], "cellules": [width, height], "dimensions": [width * TILE, height * TILE],
               "acces": exits, "famille": "salle_intermediaire" if definition["objects"] else "couloir", "fichiers": {}}
        for mode in MODES:
            layers = [paint_tiles(fields[key], sheets[mode][key], 8 if key != "contacts" else 4, (width, height))
                      for key in ["parquet", "structure", "contacts", "spirales"]]
            extra = [Image.new("RGBA", rec["dimensions"]) for _ in range(2)]
            tile_objects = [[], []]
            for ordinal, (index, fx, fy) in enumerate(definition["objects"]):
                item = objects[index]
                px, py = item["pivot"]
                x, y = fx - px, fy - py
                assert x >= 0 and y >= 0
                for k, source_images in enumerate([shadow_images, object_images]):
                    im = source_images[mode][index]
                    assert x + im.width <= width * TILE and y + im.height <= height * TILE
                    extra[k].alpha_composite(im, (x, y))
                    key = "ombres_objets" if k == 0 else "objets"
                    tile_objects[k].append({"id": ordinal + 1 + k * len(definition["objects"]), "name": item["id"],
                                            "gid": gids[mode][key] + index, "x": x, "y": y + im.height,
                                            "width": im.width, "height": im.height, "rotation": 0, "visible": True})
            layers += extra
            names = ["00_parquet", "01_structure", "02_contacts", "03_spirales", "04_ombres_objets", "05_objets"]
            composite = Image.new("RGBA", rec["dimensions"])
            files = []
            for name, im in zip(names, layers):
                file = f"modules/{ident}/calques/{mode}/{name}.png"
                save(im, OUT / file)
                files.append(file)
                composite.alpha_composite(im)
            save(composite, fd / f"{mode}.png")
            grid_ase(fd / f"{mode}.aseprite", list(zip(names, layers)), tuple(rec["dimensions"]))
            map_layers = []
            for i, key in enumerate(["parquet", "structure", "contacts", "spirales"]):
                ids = fields[key]
                data = np.where(ids < 0, 0, ids + gids[mode][key])
                map_layers.append({"id": i + 1, "name": names[i], "type": "tilelayer", "width": width, "height": height,
                                   "x": 0, "y": 0, "visible": True, "opacity": 1, "data": data.ravel().tolist()})
            for k in range(2):
                map_layers.append({"id": k + 5, "name": names[k + 4], "type": "objectgroup", "draworder": "index",
                                   "visible": True, "opacity": 1, "objects": tile_objects[k]})
            tm = {"type": "map", "version": "1.10", "tiledversion": "1.11.0", "orientation": "orthogonal", "renderorder": "right-down",
                  "tilewidth": TILE, "tileheight": TILE, "width": width, "height": height, "infinite": False,
                  "nextlayerid": 7, "nextobjectid": max(1, 2 * len(definition["objects"]) + 1), "layers": map_layers,
                  "tilesets": [{"firstgid": v["firstgid"], "source": v["source"]} for v in refs[mode].values()]}
            json_file(tm, fd / f"{mode}.tmj")
            rec["fichiers"][mode] = {"png": f"modules/{ident}/{mode}.png", "aseprite": f"modules/{ident}/{mode}.aseprite",
                                     "tiled": f"modules/{ident}/{mode}.tmj", "calques": files}
        module_records.append(rec)

    manifest = {"titre": "Guilde Treehouse — kit modulaire", "version": 1, "grille_px": TILE, "sous_grille_compatible_px": 8,
                "palettes": list(MODES), "animation": False, "cellule_objets_px": FRAME, "objets": objects,
                "parquet": {"tuiles": 32, "variantes_horizontales": 16, "variantes_verticales": 16, "colonnes": 8},
                "spirales": {"motifs": 16, "taille_motif": [64, 64], "tuiles_par_motif": [2, 2], "tuiles": 64,
                              "transparence": "alpha réel, aucun parquet intégré", "ordre": "au-dessus du parquet, avant les objets"},
                "architecture": {"tuiles": math.ceil(len(walls) / 8) * 8, "configurations": len(valid_masks), "masques_voisins_sol": valid_masks,
                                 "bits": {"N": 1, "E": 2, "S": 4, "O": 8, "NE": 16, "SE": 32, "SO": 64, "NO": 128},
                                 "contacts": 16, "epaisseur_visible_px": 24},
                "modules": module_records, "notes": ["Les objets et spirales sont optionnels et séparés.",
                                                        "Les paliers meublés sont des exemples : leurs objets sont des tile objects Tiled déplaçables.",
                                                        "Les modules ne sont pas insérés dans les 12 salles ; les accès donnent des ancrages pour le faire.",
                                                        "Le masque sol_praticable ne décide pas des collisions des objets ; intégration moteur à configurer."]}
    json_file(manifest, OUT / "kit.json")
    create_boards(manifest, sheets)
    print(f"Kit : {len(objects)} objets, 32 parquets, 16 spirales, {len(walls)} tuiles d'architecture, {len(module_records)} modules jour/nuit.")
    return manifest


def font(size, bold=False):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans" + ("-Bold" if bold else "") + ".ttf", size)


def checker(size):
    w, h = size
    yy, xx = np.indices((h, w))
    a = np.empty((h, w, 3), np.uint8)
    a[:] = [225, 231, 217]
    a[(xx // 16 + yy // 16) % 2 == 0] = [241, 242, 232]
    return Image.fromarray(a).convert("RGBA")


def create_boards(manifest, sheets):
    board = Image.new("RGB", (1440, 1480), (244, 242, 232))
    d = ImageDraw.Draw(board)
    d.text((32, 22), "GUILDE TREEHOUSE / PLANCHES MODULAIRES", font=font(27, True), fill=(33, 53, 39))
    d.text((32, 65), "Objets pixel art · parquet sans motifs · spirales en surimpression · modules 32 px", font=font(16), fill=(88, 105, 85))
    object_sheet = rgba(OUT / "objets/objets_jour.png")
    show = checker((object_sheet.width * 2, object_sheet.height * 2))
    show.alpha_composite(object_sheet.resize(show.size, Image.Resampling.NEAREST))
    board.paste(show, (32, 145))
    d.text((32, 111), "20 OBJETS / 2×", font=font(19, True), fill=(33, 53, 39))
    for key, title, pos in [("parquet", "32 TUILES DE PARQUET / 2×", (850, 145)), ("spirales", "16 SPIRALES TRANSPARENTES", (850, 505))]:
        im = sheets["jour"][key]
        if key == "parquet":
            im = im.resize((512, 256), Image.Resampling.NEAREST)
        else:
            im = im.resize((512, 512), Image.Resampling.NEAREST)
        bg = checker(im.size)
        if key == "spirales":
            floor = Image.new("RGBA", (256, 256))
            for y in range(8):
                for x in range(8):
                    floor.alpha_composite(floor_tile((x + y * 3) % 16), (x * TILE, y * TILE))
            bg = floor.resize(im.size, Image.Resampling.NEAREST)
        bg.alpha_composite(im)
        board.paste(bg, pos)
        d.text((pos[0], pos[1] - 34), title, font=font(18, True), fill=(33, 53, 39))
    d.text((32, 1145), "COULOIRS ET PALIERS EN VUE DE DESSUS", font=font(21, True), fill=(33, 53, 39))
    for i, ident in enumerate(["couloir_horizontal", "angle_nord_est", "jonction_t", "palier_baies"]):
        im = rgba(OUT / "modules" / ident / "jour.png")
        im.thumbnail((322, 255), Image.Resampling.NEAREST)
        bg = checker((326, 256))
        bg.alpha_composite(im, ((326 - im.width) // 2, (256 - im.height) // 2))
        board.paste(bg, (32 + i * 346, 1190))
    save(board, OUT / "apercus" / "planche_kit.png")
    for mode in MODES:
        board = Image.new("RGB", (1232, 1250), (23, 27, 29))
        d = ImageDraw.Draw(board)
        d.text((24, 20), f"MODULES TOP VIEW / {mode.upper()} / 32 PX", font=font(23, True), fill=(237, 218, 173))
        for i, r in enumerate(manifest["modules"]):
            im = rgba(OUT / r["fichiers"][mode]["png"])
            x, y = 16 + i % 3 * 408, 78 + i // 3 * 386
            board.paste(im, (x + (392 - im.width) // 2, y + (352 - im.height) // 2), im)
            d.text((x + 8, y + 355), r["nom"], font=font(13), fill=(237, 218, 173))
        save(board, OUT / "apercus" / f"modules_{mode}.png")


if __name__ == "__main__":
    build()
