"""Kit modulaire 32 px : objets, parquet, spirales et couloirs top view.

Le générateur n'est pas appelé pendant le build. Sa planche retenue est
archivée dans source/tilesheets ; détourages et exports sont déterministes.
Les douze salles existantes ne sont jamais réécrites par ce script.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFont
import json
import math
import os
import numpy as np

from rebuild_kit import ase

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/tilesheets"
OUT = ROOT / "tilesheets"
TILE = 32
FRAME = 96
MODES = ("jour", "nuit")
SEED = 9052026
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


def build():
    """Reproduction historique seulement ; la nouvelle production est générative."""
    if os.environ.get("GUILDE_REPRODUIRE_LEGACY") != "1":
        raise RuntimeError("Constructeur procédural v2 désactivé : méthode et formes rejetées. Utiliser source/hallways/generations/exporter_methode_origine.py pour la galerie générée. GUILDE_REPRODUIRE_LEGACY=1 est réservé à la reproduction historique.")
    for folder in ["objets", "parquet", "spirales", "architecture", "tiled", "modules", "apercus"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    objects, _, _ = extract_objects()
    horizontal = [floor_tile(i) for i in range(16)]
    floors = horizontal + [im.transpose(Image.Transpose.ROTATE_90) for im in horizontal]
    motifs = [spiral(i) for i in range(16)]
    for mode in MODES:
        def variant(items, alpha=1.):
            return items if mode == "jour" else [night(q, alpha) for q in items]
        sheets = {"parquet": atlas(variant(floors), 8, TILE), "spirales": atlas(variant(motifs, .55), 4, 64)}
        for key, count in [("parquet", 32), ("spirales", 64)]:
            im = sheets[key]
            filename = f"{key}/{key}_{mode}.png"
            save(im, OUT / filename)
            records = None
            if key == "parquet":
                records = [{"id": i, "properties": [{"name": "orientation", "type": "string", "value": "horizontal" if i < 16 else "vertical"}]} for i in range(32)]
            json_file(tile_set(f"{key}_{mode}", filename, *im.size, count, 8, records), OUT / "tiled" / f"{key}_{mode}.tsj")
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
        for i, im in enumerate(variant(motifs, .55)):
            save(im, OUT / "spirales" / "individuelles" / f"spirale_{i + 1:02d}_{mode}.png")
        floor_demo = Image.new("RGBA", (256, 256))
        for y in range(8):
            for x in range(8):
                tile = floors[(x * 3 + y * 5) % 16]
                floor_demo.alpha_composite(tile if mode == "jour" else night(tile), (x * TILE, y * TILE))
        grid_ase(OUT / "parquet" / f"parquet_et_spirales_{mode}.aseprite",
                 [("Parquet sans motifs", floor_demo), ("Traces spiralées transparentes", sheets["spirales"])], (256, 256))
    manifest = {"titre": "Guilde Treehouse — kit modulaire", "version": 2, "grille_px": TILE, "sous_grille_compatible_px": 8,
                "palettes": list(MODES), "animation": False, "cellule_objets_px": FRAME, "objets": objects,
                "parquet": {"tuiles": 32, "variantes_horizontales": 16, "variantes_verticales": 16, "colonnes": 8},
                "spirales": {"motifs": 16, "taille_motif": [64, 64], "tuiles_par_motif": [2, 2], "tuiles": 64,
                              "transparence": "alpha réel, aucun parquet intégré", "ordre": "au-dessus du parquet, avant les objets"}}
    from build_hallways import build as build_hallways
    return build_hallways(manifest)


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


if __name__ == "__main__":
    build()
