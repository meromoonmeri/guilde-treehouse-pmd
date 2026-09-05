"""Couloirs PMD v2 : nouvelle géométrie, panneaux debout et immersion en plans.

Les murs ne sont ni une rotation ni une recoloration du parquet. Ils sont des
sprites de panneaux noueux, posés sur le contour de plans à pans coupés. Les
éléments végétaux proviennent de la banque de la guilde. Aucun générateur n'est
appelé et aucune des douze salles ni des autres tilesheets n'est réécrite.
"""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

from build_tilesheets import grid_ase, night, save, json_file, font, checker

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tilesheets"
SOURCE = ROOT / "source/hallways"
TILE = 32
MODES = ("jour", "nuit")
LAYERS = [
    ("00_fond_immersion", "Fond d’immersion", "fond", "tile"),
    ("01_soubassement", "Soubassement d’écorce", "soubassement", "tile"),
    ("02_feuillage_arriere", "Feuillage arrière", "vegetation", "sprite"),
    ("03_parquet", "Parquet", "sol_decoupe", "tile"),
    ("04_murs_fond", "Panneaux du fond", "murs_fond", "sprite"),
    ("05_murs_retours", "Murs de retour", "murs_retours", "sprite"),
    ("06_ombres_contact", "Ombres de contact", "contacts", "tile"),
    ("07_reflets_seuils", "Reflets des seuils", "reflets", "tile"),
    ("08_spirales", "Traces spiralées", "motifs", "external"),
    ("09_ombres_objets", "Ombres des objets", "ombres_objets", "external"),
    ("10_objets", "Objets et tentures", "objets", "external"),
    ("11_ecorce_racines_avant", "Écorce et racines avant", "ecorce_avant", "tile"),
    ("12_feuillage_avant", "Feuillage de premier plan", "vegetation", "sprite"),
]
VEGETATION = ["vegetation_08_01", "vegetation_08_13", "vegetation_01_01", "vegetation_05_10", "vegetation_01_05"]


def rgba(path):
    return Image.open(path).convert("RGBA")


def clear_transparent(im):
    a = np.array(im.convert("RGBA"))
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def mask_polygon(points, size, origin=(0, 0)):
    """Rasteriser aux centres des pixels : un accès de 96 reste 96, pas 97."""
    w, h = size
    yy, xx = np.indices((h, w), dtype=float)
    xx += origin[0] + .5
    yy += origin[1] + .5
    inside = np.zeros((h, w), bool)
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        if y0 == y1:
            continue
        inside ^= ((y0 > yy) != (y1 > yy)) & (xx < (x1 - x0) * (yy - y0) / (y1 - y0) + x0)
    return inside


def masked(im, mask):
    a = np.array(im)
    a[~mask] = 0
    return Image.fromarray(a)


def wood_texture(size, offset=(0, 0), light=1.):
    """Veinage NOUEUX VERTICAL, palette brune distincte des lames dorées du sol."""
    w, h = size
    yy, xx = np.indices((h, w), dtype=float)
    xx += offset[0]
    yy += offset[1]
    bend = 2.8 * np.sin(yy / 14 + .6 * np.sin(xx / 23)) + 1.2 * np.sin(yy / 5.3 + xx / 29)
    # Déviation localisée autour de nœuds ; pas de joints de planches horizontaux.
    for cx, cy in [(17, 30), (44, 82), (76, 53), (105, 108), (137, 23)]:
        bend += 6 * np.exp(-((xx - cx) / 11) ** 2 - ((yy - cy) / 18) ** 2) * np.sin((yy - cy) / 9)
    phase = (xx + bend) * .62
    f = (phase / math.tau) % 1
    # Champ brun mat et fibres fines. Des bandes claires trop larges évoqueraient
    # un rideau ondulé : le contraste se concentre sur les lignes du veinage.
    palette = np.array([(104, 58, 25), (178, 116, 57), (151, 91, 41), (157, 98, 45),
                        (134, 79, 34), (166, 105, 49), (146, 87, 38)], dtype=float)
    idx = np.select([f < .075, f < .15, f < .40, f < .67, f < .73, f < .81], [0, 1, 2, 3, 4, 5], default=6)
    a = np.zeros((h, w, 4), np.uint8)
    a[:, :, :3] = np.rint(palette[idx] * light).clip(0, 255)
    a[:, :, 3] = 255
    return Image.fromarray(a)


def wall_piece(dx, dy, kind):
    """Un panneau réutilisable : face brune, montants, plinthe et chaperon."""
    length = math.hypot(dx, dy)
    nx, ny = dy / length, -dx / length
    height = 64 if kind == "murs_fond" else 40
    ox = round(nx * (12 if kind == "murs_fond" else 18))
    p0, p1 = (0, 0), (dx, dy)
    q0, q1 = (ox, -height), (dx + ox, dy - height)
    polygon = [p0, p1, q1, q0]
    minx, miny = math.floor(min(p[0] for p in polygon)) - 3, math.floor(min(p[1] for p in polygon)) - 3
    maxx, maxy = math.ceil(max(p[0] for p in polygon)) + 4, math.ceil(max(p[1] for p in polygon)) + 4
    size = (math.ceil((maxx - minx) / 8) * 8, math.ceil((maxy - miny) / 8) * 8)
    local = [(x - minx, y - miny) for x, y in polygon]
    area = mask_polygon(local, size)
    light = .86 if nx > .4 else (1.03 if nx < -.4 else 1.)
    # Le motif reste vertical dans le plan du mur, même sur les retours obliques.
    im = masked(wood_texture(size, (minx, miny + height), light), area)
    d = ImageDraw.Draw(im)
    if abs(dx) in (48, 56):
        cx, cy = np.rint(np.mean(local, axis=0)).astype(int)
        d.ellipse((cx - 3, cy - 9, cx + 3, cy + 8), outline=(105, 58, 25, 255), width=1)
        d.ellipse((cx - 1, cy - 5, cx + 1, cy + 4), fill=(120, 68, 28, 255))
        d.line((cx + 3, cy - 4, cx + 3, cy + 3), fill=(183, 121, 59, 255))
    pts = [(round(x), round(y)) for x, y in local]
    d.line(pts + [pts[0]], fill=(68, 35, 15, 255), width=3)
    d.line([pts[2], pts[3]], fill=(117, 64, 24, 255), width=6)
    d.line([(x, y + 1) for x, y in [pts[2], pts[3]]], fill=(204, 139, 65, 255), width=2)
    for a, b in [(pts[0], pts[3]), (pts[1], pts[2])]:
        d.line([a, b], fill=(91, 46, 17, 255), width=5)
        d.line([(a[0] - 1, a[1]), (b[0] - 1, b[1])], fill=(174, 107, 46, 255), width=2)
    d.line([pts[0], pts[1]], fill=(79, 41, 16, 255), width=5)
    d.line([(x, y - 3) for x, y in pts[:2]], fill=(183, 117, 50, 255), width=2)
    # Ne pas laisser le trait du pied déborder sur le parquet.
    im = masked(im, area)
    return im, (minx, miny), (ox, -height)


class Registry:
    def __init__(self, key, kind):
        self.key, self.kind = key, kind
        self.images, self.names, self.lookup = [], [], {}

    def add(self, im, name):
        im = clear_transparent(im)
        key = (im.size, hashlib.sha256(im.tobytes()).digest())
        if key not in self.lookup:
            self.lookup[key] = len(self.images)
            self.images.append(im.copy())
            self.names.append(name)
        return self.lookup[key]

    def export(self):
        count = len(self.images)
        # Nettoyage ciblé des anciens indices générés ; aucune pièce utilisateur
        # ni source n'est supprimée. Évite de conserver une tentative graphique.
        piece_folder = OUT / "architecture/pieces" / self.key
        for stale in piece_folder.glob("*.png"):
            index, _, suffix = stale.stem.partition("_")
            if len(index) == 3 and index.isdigit() and suffix in MODES and int(index) >= count:
                stale.unlink()
        if self.kind == "tile":
            cell, columns = 32, min(16, max(1, count))
        else:
            cell = math.ceil(max(max(im.size) for im in self.images) / 32) * 32
            columns = min(5, count)
        rows = math.ceil(count / columns)
        records = []
        for mode in MODES:
            sheet = Image.new("RGBA", (columns * cell, rows * cell))
            tiles = []
            for i, source in enumerate(self.images):
                im = grade(source, self.key, mode)
                if self.kind == "tile":
                    pos = (i % columns * cell, i // columns * cell)
                else:
                    pos = (i % columns * cell + (cell - im.width) // 2, i // columns * cell + cell - im.height)
                    filename = f"architecture/pieces/{self.key}/{i:03d}_{mode}.png"
                    save(im, OUT / filename)
                    tiles.append({"id": i, "image": "../" + filename, "imagewidth": im.width, "imageheight": im.height,
                                  "properties": [{"name": "piece", "type": "string", "value": self.names[i]}]})
                sheet.alpha_composite(im, pos)
                if mode == "jour":
                    records.append({"index": i, "nom": self.names[i], "taille": list(im.size),
                                    "rect_atlas": [pos[0], pos[1], im.width, im.height]})
            filename = f"architecture/{self.key}_{mode}.png"
            save(sheet, OUT / filename)
            if self.kind == "tile":
                ts = {"type": "tileset", "version": "1.10", "name": self.key + "_" + mode, "tilewidth": 32, "tileheight": 32,
                      "image": "../" + filename, "imagewidth": sheet.width, "imageheight": sheet.height,
                      "columns": columns, "tilecount": columns * rows, "margin": 0, "spacing": 0}
            else:
                ts = {"type": "tileset", "version": "1.10", "name": self.key + "_" + mode,
                      "tilewidth": cell, "tileheight": cell, "tilecount": count, "columns": 0,
                      "objectalignment": "bottomleft", "tiles": tiles}
            json_file(ts, OUT / "tiled" / f"hallways_{self.key}_{mode}.tsj")
        self.capacity = columns * rows if self.kind == "tile" else count
        return {"id": self.key, "type": self.kind, "pieces": count, "cases": self.capacity, "cellule_atlas": cell,
                "dimensions_atlas": [columns * cell, rows * cell], "detail": records,
                "fichiers": {m: f"architecture/{self.key}_{m}.png" for m in MODES}}


def grade(im, key, mode):
    if mode == "jour":
        return im.copy()
    if key == "fond":
        a = np.array(im)
        a[:, :, :3] = (11, 13, 23)
        a[a[:, :, 3] == 0] = 0
        return Image.fromarray(a)
    return night(im, .4 if key == "reflets" else 1.)


def segments(definition):
    w, h = definition["dimensions"]
    points = definition["polygone_sol"]
    for p0, p1 in zip(points, points[1:] + points[:1]):
        if (p0[0] == p1[0] and p0[0] in (0, w)) or (p0[1] == p1[1] and p0[1] in (0, h)):
            continue
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = np.array([dy, -dx], float) / math.hypot(dx, dy)
        kind = "murs_fond" if n[1] < -.25 else ("murs_retours" if abs(n[0]) > .75 else None)
        yield np.array(p0, float), np.array(p1, float), n, kind


def mask_sprite_in_world(im, pos, allowed):
    """Garder le sprite complet hors cadre ; masquer seulement les recouvrements interdits."""
    x, y = pos
    h, w = allowed.shape
    a = np.array(im)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(w, x + im.width), min(h, y + im.height)
    if x1 > x0 and y1 > y0:
        a[y0 - y:y1 - y, x0 - x:x1 - x][~allowed[y0:y1, x0:x1]] = 0
    return clear_transparent(Image.fromarray(a))


def stamp_inside_allowed(im, pos, allowed):
    x, y = pos
    h, w = allowed.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(w, x + im.width), min(h, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return False
    alpha = np.array(im.getchannel("A"))[y0-y:y1-y, x0-x:x1-x] > 0
    return not (alpha & ~allowed[y0:y1, x0:x1]).any()


def foliage_sources():
    result = []
    for name in VEGETATION:
        im = rgba(ROOT / "sprites/individuels" / (name + ".png"))
        maximum = (64, 54) if name != "vegetation_01_05" else (32, 68)
        im.thumbnail(maximum, Image.Resampling.NEAREST)
        for flip in (False, True):
            result.append(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im.copy())
    return result


def bark_layers(floor, definition):
    h, w = floor.shape
    yy, xx = np.indices(floor.shape)
    outer = distance_transform_edt(~floor)
    gy, gx = np.gradient(outer)
    rough = np.rint(1.5 * np.sin(xx * .29) + 1.2 * np.sin(yy * .37 + xx * .13))
    support = (~floor) & (outer < 21 + rough)
    # Un prélèvement du chant du plancher de la guilde, pas du parquet lui-même.
    bark = np.array(rgba(ROOT / "source/natives/05.png").crop((240, 364, 400, 376)))[:, :, :3]
    bad = (bark[:, :, 0] > 230) & (bark[:, :, 1] < 60) & (bark[:, :, 2] > 180)
    bark[bad] = (130, 74, 28)
    along = np.where(np.abs(gy) >= np.abs(gx), xx, yy * 2)
    a = np.zeros((h, w, 4), np.uint8)
    depth = np.maximum(0, outer - 4).astype(int)
    col = bark[depth % bark.shape[0], along % bark.shape[1]].astype(float)
    darkness = np.where(outer > 16 + rough, .45, np.where(outer > 12, .65, .8))
    a[:, :, :3] = (col * darkness[:, :, None]).clip(0, 255)
    a[:, :, 3] = support * 255
    a[~support] = 0
    base = Image.fromarray(a)
    # Le chant avant est plus proche et lisible. Le bord reste irrégulier.
    front = support & ((gy > -.1) | (np.abs(gx) > .8))
    b = a.copy()
    b[:, :, :3] = np.clip(col * np.where(outer > 15 + rough, .58, .95)[:, :, None], 0, 255)
    b[:, :, 3] = front * 255
    lip = front & (outer <= 3)
    b[lip] = (211, 148, 66, 255)
    b[front & (outer > 3) & (outer <= 5)] = (95, 48, 18, 255)
    b[~front] = 0
    foreground = Image.fromarray(b)
    d = ImageDraw.Draw(foreground)
    # Petites racines fourchues : une silhouette d'écorce, pas une bordure lisse.
    for j, (p0, p1, n, kind) in enumerate(segments(definition)):
        if kind == "murs_fond":
            continue
        length = np.linalg.norm(p1 - p0)
        tangent = (p1 - p0) / length
        for k, t in enumerate(np.arange(28, length, 64)):
            p = p0 + tangent * t + n * 9
            a0 = p - tangent * 7
            a1 = p + tangent * 6
            mid = p + n * (17 + (k % 2) * 4) + tangent * 3
            tip = mid + n * 9 - tangent * 8
            pts = [a0, a1, mid + tangent * 3, tip, mid - tangent * 4]
            pts = [tuple(np.rint(q).astype(int)) for q in pts]
            d.polygon(pts, fill=(78, 43, 19, 255))
            d.line(pts[:3], fill=(175, 109, 45, 255), width=2)
            d.line([tuple(np.rint(p).astype(int)), tuple(np.rint(mid).astype(int)), tuple(np.rint(tip).astype(int))],
                   fill=(119, 64, 25, 255), width=2)
    return base, foreground


def illumination(floor, definition):
    h, w = floor.shape
    yy, xx = np.indices(floor.shape, dtype=float)
    xx += .5
    yy += .5
    opacity = np.zeros(floor.shape)
    for p0, p1, n, kind in segments(definition):
        v = p1 - p0
        t = np.clip(((xx - p0[0]) * v[0] + (yy - p0[1]) * v[1]) / np.dot(v, v), 0, 1)
        dist = np.hypot(xx - (p0[0] + t * v[0]), yy - (p0[1] + t * v[1]))
        width, peak = (14, 94) if kind == "murs_fond" else ((9, 70) if kind else (5, 38))
        opacity = np.maximum(opacity, np.clip(1 - dist / width, 0, 1) ** 1.5 * peak)
    a = np.zeros((h, w, 4), np.uint8)
    a[:, :, :3] = (32, 18, 8)
    a[:, :, 3] = np.rint(opacity / 8).astype("uint8") * 8
    a[~floor | (a[:, :, 3] == 0)] = 0
    shadow = Image.fromarray(a)
    light = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(light)
    for exit in exits_for(floor, definition):
        x, y = exit["ancrage_px"]
        if exit["direction"] in ["E", "O"]:
            for oy in [-44, 43]:
                start = 3 if x == 0 else w - 14
                d.line((start, int(y + oy), start + 10, int(y + oy)), fill=(251, 211, 114, 88), width=1)
        else:
            for ox in [-44, 43]:
                start = 3 if y == 0 else h - 14
                d.line((int(x + ox), start, int(x + ox), start + 10), fill=(251, 211, 114, 64), width=1)
    return shadow, masked(light, floor)


def exits_for(floor, definition):
    h, w = floor.shape
    out = []
    for direction in definition["sorties"]:
        strip = {"N": floor[0], "S": floor[-1], "E": floor[:, -1], "O": floor[:, 0]}[direction]
        where = np.flatnonzero(strip)
        assert len(where) == 96 and (np.diff(where) == 1).all(), (definition["id"], direction, len(where))
        center = float((where[0] + where[-1] + 1) / 2)
        point = {"N": [center, 0], "S": [center, h], "E": [w, center], "O": [0, center]}[direction]
        out.append({"direction": direction, "ancrage_px": point, "largeur_px": 96, "intervalle_px": [int(where[0]), int(where[-1]) + 1]})
    return out


def entrance_guard(floor, definition):
    h, w = floor.shape
    guard = np.zeros(floor.shape, bool)
    for e in exits_for(floor, definition):
        a, b = e["intervalle_px"]
        if e["direction"] == "N": guard[:40, a:b] = True
        if e["direction"] == "S": guard[-40:, a:b] = True
        if e["direction"] == "O": guard[a:b, :40] = True
        if e["direction"] == "E": guard[a:b, -40:] = True
    return guard


def render_definition(definition, manifest, registries, plants):
    size = tuple(definition["dimensions"])
    w, h = size
    floor = mask_polygon(definition["polygone_sol"], size)
    inside = distance_transform_edt(floor)
    guard = entrance_guard(floor, definition)
    # Les bouts raccordables restent sans feuille coupée : on pourra végétaliser
    # les jonctions après assemblage, sans deux demi-buissons incompatibles.
    green_gutter = np.ones(floor.shape, bool)
    for direction in definition["sorties"]:
        if direction == "N": green_gutter[:40] = False
        if direction == "S": green_gutter[-40:] = False
        if direction == "O": green_gutter[:, :40] = False
        if direction == "E": green_gutter[:, -40:] = False
    canvases = [Image.new("RGBA", size) for _ in LAYERS]
    canvases[0].paste((23, 16, 29, 255), (0, 0, w, h))
    # Le fond extérieur est évidé : il ne contient PAS un rectangle opaque
    # sous le parquet. Isolé, il reproduit la découpe d'immersion de la référence.
    canvases[0] = masked(canvases[0], ~floor)
    canvases[1], canvases[11] = bark_layers(floor, definition)
    canvases[11] = masked(canvases[11], ~guard)
    floor_sheet = rgba(OUT / "parquet/parquet_jour.png")
    for y in range(h // 32):
        for x in range(w // 32):
            i = (x * 7 + y * 11) % 16
            tile = floor_sheet.crop((i % 8 * 32, i // 8 * 32, i % 8 * 32 + 32, i // 8 * 32 + 32))
            canvases[3].alpha_composite(tile, (x * 32, y * 32))
    canvases[3] = masked(canvases[3], floor)
    placements = defaultdict(list)

    def sprite(layer, im, pos, name, allowed=None):
        pos = tuple(int(v) for v in pos)
        if pos[0] + im.width <= 0 or pos[1] + im.height <= 0 or pos[0] >= w or pos[1] >= h:
            return
        if layer in (2, 12) and not stamp_inside_allowed(im, pos, green_gutter):
            return
        if allowed is not None:
            im = mask_sprite_in_world(im, pos, allowed)
        if im.getbbox() is None:
            return
        registry = registries[LAYERS[layer][2]]
        index = registry.add(im, name)
        canvases[layer].alpha_composite(im, pos)
        placements[layer].append({"index": index, "x": pos[0], "y": pos[1], "nom": name})

    for j, (p0, p1, n, kind) in enumerate(segments(definition)):
        length = np.linalg.norm(p1 - p0)
        tangent = (p1 - p0) / length
        if kind:
            steps = math.ceil(max(abs(p1 - p0)) / 64)
            step = (p1 - p0) / steps
            for k in range(steps):
                point = p0 + k * step
                im, offset, top = wall_piece(round(step[0]), round(step[1]), kind)
                pos = np.rint(point + offset).astype(int)
                wall_layer = 4 if kind == "murs_fond" and abs(n[0]) < .25 else 5
                sprite(wall_layer, im, pos, f"{kind}_{round(step[0])}_{round(step[1])}", ~floor)
                # Canopée derrière le chaperon : silhouettes entières et leur propre plan.
                center = point + step * .5 + top
                plant = plants[(j + k) % 4]
                position = np.rint(center - [plant.width / 2, plant.height - 13]).astype(int)
                sprite(2, plant, position, f"canopée_{(j + k) % 4}")
                # Quelques retombées passent DEVANT le haut des panneaux.
                if (j + k) % 3 == 0:
                    plant = plants[8 + (j % 2)] if kind == "murs_fond" else plants[(j + 3) % 8]
                    position = np.rint(center - [plant.width / 2, 6]).astype(int)
                    if stamp_inside_allowed(plant, position, (~guard) & ((inside < 17) | ~floor)):
                        sprite(12, plant, position, f"retombée_{j % 2}")
        # Racines et feuillage bas : surtout les côtés et le premier plan coupé.
        if kind != "murs_fond":
            for k, t in enumerate(np.arange(26, length, 58)):
                center = p0 + tangent * t
                plant = plants[(j * 3 + k) % 8]
                # Un plan en retrait sur les côtés, un vrai recouvrement léger devant.
                for distance in [14, 22, 30, 38]:
                    position = np.rint(center + n * distance - [plant.width / 2, plant.height / 2]).astype(int)
                    if stamp_inside_allowed(plant, position, (~guard) & ((inside < 17) | ~floor)):
                        sprite(12, plant, position, f"bordure_végétale_{(j * 3 + k) % 8}")
                        break
    # Fermer les raccords supérieurs des panneaux : les normales des deux faces
    # diffèrent aux angles, mais cela ne doit jamais laisser une fente de ciel.
    edge_list = list(segments(definition))
    for previous, following in zip(edge_list, edge_list[1:] + edge_list[:1]):
        a0, vertex, n0, kind0 = previous
        b0, b1, n1, kind1 = following
        if kind0 is None or kind1 is None or not np.array_equal(vertex, b0):
            continue
        top0 = np.array([round(n0[0] * (12 if kind0 == "murs_fond" else 18)), -64 if kind0 == "murs_fond" else -40])
        top1 = np.array([round(n1[0] * (12 if kind1 == "murs_fond" else 18)), -64 if kind1 == "murs_fond" else -40])
        if np.array_equal(top0, top1):
            continue
        points = [np.array([0, 0]), top0, top1]
        ox, oy = min(p[0] for p in points) - 2, min(p[1] for p in points) - 2
        sw = math.ceil((max(p[0] for p in points) - ox + 3) / 8) * 8
        sh = math.ceil((max(p[1] for p in points) - oy + 3) / 8) * 8
        local = [tuple((p - [ox, oy]).tolist()) for p in points]
        area = mask_polygon(local, (sw, sh))
        im = masked(wood_texture((sw, sh), (ox, oy + 64), .85), area)
        d = ImageDraw.Draw(im)
        d.line(local[1:], fill=(194, 128, 58, 255), width=2)
        d.line([local[0], tuple(np.rint((top0 + top1) / 2 - [ox, oy]).astype(int))], fill=(117, 63, 23, 255), width=2)
        im = masked(im, area)
        sprite(5, im, np.rint(vertex + [ox, oy]).astype(int), "joint_de_panneaux", ~floor)
    canvases[6], canvases[7] = illumination(floor, definition)
    external = defaultdict(list)
    if definition["spirale"]:
        i, x, y = definition["spirale"]
        im = rgba(OUT / "spirales/individuelles" / f"spirale_{i + 1:02d}_jour.png")
        assert floor[y:y + 64, x:x + 64].all()
        canvases[8].alpha_composite(im, (x, y))
        external[8].append({"index": i, "x": x, "y": y, "nom": f"spirale_{i + 1:02d}"})
    for i, x, y in definition["objets"]:
        obj = manifest["objets"][i]
        pos = (x - obj["pivot"][0], y - obj["pivot"][1])
        for layer, key in [(9, "ombre"), (10, "png")]:
            im = rgba(OUT / obj["fichiers"]["jour"][key])
            canvases[layer].alpha_composite(im, pos)
            external[layer].append({"index": i, "x": pos[0], "y": pos[1], "nom": obj["id"]})
    fields = {}
    for layer, (_, _, key, kind) in enumerate(LAYERS):
        if kind != "tile":
            continue
        field = np.full((h // 32, w // 32), -1, dtype=int)
        for y in range(h // 32):
            for x in range(w // 32):
                tile = canvases[layer].crop((x * 32, y * 32, x * 32 + 32, y * 32 + 32))
                if tile.getbbox():
                    field[y, x] = registries[key].add(tile, f"{key}_{x}_{y}")
        fields[layer] = field
    return {"definition": definition, "floor": floor, "guard": guard, "canvases": canvases,
            "placements": placements, "external": external, "fields": fields}


def export_external(manifest):
    """Les objets/spirales existants sont référencés, jamais repeints."""
    paths = {}
    for mode in MODES:
        for key in ["objets", "ombres_objets", "motifs"]:
            rows = []
            if key == "motifs":
                for i in range(16):
                    rows.append({"id": i, "image": f"../spirales/individuelles/spirale_{i + 1:02d}_{mode}.png", "imagewidth": 64, "imageheight": 64})
            else:
                for obj in manifest["objets"]:
                    file = obj["fichiers"][mode]["png" if key == "objets" else "ombre"]
                    rows.append({"id": obj["index"], "image": "../" + file, "imagewidth": obj["taille"][0], "imageheight": obj["taille"][1]})
            ts = {"type": "tileset", "version": "1.10", "name": "hallways_" + key + "_" + mode, "columns": 0,
                  "tilewidth": 96, "tileheight": 96, "tilecount": len(rows), "objectalignment": "bottomleft", "tiles": rows}
            filename = f"tiled/hallways_{key}_{mode}.tsj"
            json_file(ts, OUT / filename)
            paths[(key, mode)] = filename
    return paths


def scene_mode(scene, mode, registries, manifest):
    layers = []
    for layer, (_, _, key, kind) in enumerate(LAYERS):
        if kind != "external":
            layers.append(grade(scene["canvases"][layer], key, mode))
        else:
            canvas = Image.new("RGBA", tuple(scene["definition"]["dimensions"]))
            for item in scene["external"][layer]:
                i = item["index"]
                if key == "motifs":
                    im = rgba(OUT / "spirales/individuelles" / f"spirale_{i + 1:02d}_{mode}.png")
                else:
                    obj = manifest["objets"][i]
                    im = rgba(OUT / obj["fichiers"][mode]["png" if key == "objets" else "ombre"])
                canvas.alpha_composite(im, (item["x"], item["y"]))
            layers.append(canvas)
    return layers


def export_scene(scene, manifest, registries, gids):
    definition = scene["definition"]
    ident, size = definition["id"], tuple(definition["dimensions"])
    w, h = size
    folder = OUT / "modules" / ident
    folder.mkdir(parents=True, exist_ok=True)
    # Supprimer uniquement les anciens calques de CE module généré, pour qu'un
    # import par glob ne récupère jamais le vieux muret de la version refusée.
    keep = {name + ".png" for name, _, _, _ in LAYERS}
    for mode in MODES:
        for stale in (folder / "calques" / mode).glob("*.png"):
            if stale.name not in keep:
                stale.unlink()
    save(Image.fromarray(scene["floor"].astype("uint8") * 255), folder / "sol_praticable.png")
    record = {"id": ident, "nom": definition["nom"], "dimensions": list(size), "cellules": [w // 32, h // 32],
              "famille": "salle_intermediaire" if definition["objets"] else "couloir", "version_architecture": 2,
              "acces": exits_for(scene["floor"], definition), "calques": [{"id": name, "nom": label, "type": kind} for name, label, _, kind in LAYERS],
              "fichiers": {}}
    for mode in MODES:
        layers = scene_mode(scene, mode, registries, manifest)
        full, transparent = Image.new("RGBA", size), Image.new("RGBA", size)
        files = []
        for i, ((name, _, _, _), im) in enumerate(zip(LAYERS, layers)):
            file = f"modules/{ident}/calques/{mode}/{name}.png"
            save(im, OUT / file)
            files.append(file)
            full.alpha_composite(im)
            if i:
                transparent.alpha_composite(im)
        save(full, folder / f"{mode}.png")
        save(transparent, folder / f"{mode}_transparent.png")
        grid_ase(folder / f"{mode}.aseprite", [(name, im) for (name, _, _, _), im in zip(LAYERS, layers)], size)
        tm_layers, next_object = [], 1
        for i, (name, label, key, kind) in enumerate(LAYERS):
            base = {"id": i + 1, "name": name, "visible": True, "opacity": 1,
                    "properties": [{"name": "role", "type": "string", "value": label}]}
            if kind == "tile":
                field = scene["fields"][i]
                data = np.where(field < 0, 0, field + gids[key]).ravel().tolist()
                base.update({"type": "tilelayer", "width": w // 32, "height": h // 32, "x": 0, "y": 0, "data": data})
            else:
                objects = []
                for p in scene["external"][i] if kind == "external" else scene["placements"][i]:
                    index = p["index"]
                    if kind == "sprite":
                        im = registries[key].images[index]
                    elif key == "motifs":
                        im = Image.new("RGBA", (64, 64))
                    else:
                        im = Image.new("RGBA", tuple(manifest["objets"][index]["taille"]))
                    objects.append({"id": next_object, "name": p["nom"], "gid": gids[key] + index,
                                    "x": p["x"], "y": p["y"] + im.height, "width": im.width, "height": im.height,
                                    "rotation": 0, "visible": True})
                    next_object += 1
                base.update({"type": "objectgroup", "draworder": "index", "objects": objects})
            tm_layers.append(base)
        refs = [{"firstgid": gid, "source": f"../../tiled/hallways_{key}_{mode}.tsj"} for key, gid in gids.items()]
        tm = {"type": "map", "version": "1.10", "orientation": "orthogonal", "renderorder": "right-down", "infinite": False,
              "tilewidth": 32, "tileheight": 32, "width": w // 32, "height": h // 32, "nextlayerid": len(LAYERS) + 1,
              "nextobjectid": next_object, "layers": tm_layers, "tilesets": refs,
              "properties": [{"name": "architecture", "type": "string", "value": "panneaux verticaux + bordures d’immersion"}]}
        json_file(tm, folder / f"{mode}.tmj")
        record["fichiers"][mode] = {"png": f"modules/{ident}/{mode}.png", "transparent": f"modules/{ident}/{mode}_transparent.png",
                                    "aseprite": f"modules/{ident}/{mode}.aseprite", "tiled": f"modules/{ident}/{mode}.tmj", "calques": files}
    return record


def boards(manifest):
    # Planche de modules à échelle identique, pas de réduction qui masquerait les nouveaux murs.
    for mode in MODES:
        board = Image.new("RGB", (1632, 1824), (23, 16, 29))
        d = ImageDraw.Draw(board)
        d.text((28, 24), f"GUILDE TREEHOUSE / NOUVEAUX COULOIRS / {mode.upper()}", font=font(26, True), fill=(239, 216, 167))
        d.text((28, 65), "Panneaux noueux verticaux · pans coupés · racines et feuillage sur plans séparés", font=font(16), fill=(167, 181, 141))
        for i, r in enumerate(manifest["modules"]):
            im = rgba(OUT / r["fichiers"][mode]["png"])
            x, y = 8 + i % 3 * 540, 110 + i // 3 * 562
            board.paste(im, (x + (524 - im.width) // 2, y + (512 - im.height) // 2))
            d.text((x + 18, y + 523), r["nom"], font=font(15, True), fill=(239, 216, 167))
        save(board, OUT / "apercus" / f"modules_{mode}.png")
    # Preuve de séparation, centrée sur le couloir et non sur une planche d'objets.
    module = manifest["modules"][0]
    paths = module["fichiers"]["jour"]["calques"]
    layers = [rgba(OUT / p) for p in paths]
    size = layers[0].size
    groups = [([3], "01 / PARQUET"), ([4, 5], "02 / MURS SANS PARQUET"),
              ([0, 1, 2, 11, 12], "03 / BORDURES D’IMMERSION"), (list(range(len(layers))), "04 / COMPOSITION FINALE")]
    board = Image.new("RGB", (1024, 930), (244, 242, 232))
    d = ImageDraw.Draw(board)
    d.text((28, 22), "COULOIRS REPRIS DE ZÉRO / 13 CALQUES", font=font(24, True), fill=(39, 57, 37))
    d.text((28, 58), "Des panneaux verticaux, pas un ruban de parquet. L’immersion a ses propres plans.", font=font(15), fill=(93, 110, 80))
    for i, (indices, title) in enumerate(groups):
        x, y = 28 + i % 2 * 500, 130 + i // 2 * 400
        combined = Image.new("RGBA", size)
        for j in indices:
            combined.alpha_composite(layers[j])
        bg = checker(size)
        bg.alpha_composite(combined)
        board.paste(bg, (x, y))
        d.text((x, y - 30), title, font=font(16, True), fill=(39, 57, 37))
    save(board, OUT / "apercus/separation_couloir.png")


def build(manifest=None):
    if os.environ.get("GUILDE_REPRODUIRE_LEGACY") != "1":
        raise RuntimeError("Constructeur procédural v2 désactivé : conserver les arrondis et générer les décors. Voir plans/guilde_4_niveaux/plan_canonique.json. GUILDE_REPRODUIRE_LEGACY=1 permet uniquement de reproduire l’archive rejetée.")
    if manifest is None:
        manifest = json.loads((OUT / "kit.json").read_text())
    definitions = json.loads((SOURCE / "definitions.json").read_text())["modules"]
    registries = {}
    for _, _, key, kind in LAYERS:
        if kind != "external" and key not in registries:
            registries[key] = Registry(key, kind)
    plants = foliage_sources()
    scenes = [render_definition(d, manifest, registries, plants) for d in definitions]
    catalogues = [r.export() for r in registries.values()]
    export_external(manifest)
    gids, first = {}, 1
    for key, registry in registries.items():
        gids[key] = first
        first += registry.capacity
    for key, count in [("motifs", 16), ("ombres_objets", len(manifest["objets"])), ("objets", len(manifest["objets"]))]:
        gids[key] = first
        first += count
    records = [export_scene(s, manifest, registries, gids) for s in scenes]
    manifest["version"] = 2
    manifest["architecture"] = {"version": 2, "methode": "panneaux verticaux, coupe frontale et immersion multicouche",
                                "hauteur_panneaux_fond": 64, "hauteur_retours_obliques": 64, "hauteur_murs_lateraux": 40, "calques": len(LAYERS),
                                "catalogues": catalogues, "grille_decoupe": 32,
                                "source_geometrie": "source/hallways/definitions.json",
                                "notes": ["Fond sombre optionnel ; composition transparente fournie en plus.",
                                          "Les murs sont des tile objects de panneaux réutilisables, indépendants du parquet.",
                                          "Les découpes de sol et d’écorce sont des tuiles de contour ; pas un système de Wang complet.",
                                          "Deux plans de feuillage et un chant d’écorce/racines forment la bordure d’immersion."]}
    manifest["modules"] = records
    manifest["notes"] = ["Objets, parquet et spirales de la première livraison conservés sans changement.",
                          "Couloirs et paliers reconstruits de zéro : 13 calques, murs debout, premier plan végétal.",
                          "Les nouveaux accès de 96 px ne sont pas automatiquement connectés aux douze intérieurs."]
    json_file(manifest, OUT / "kit.json")
    boards(manifest)
    from build_tilesheets import create_boards
    create_boards(manifest, {"jour": {"parquet": rgba(OUT / "parquet/parquet_jour.png"),
                                     "spirales": rgba(OUT / "spirales/spirales_jour.png")}})
    # Retirer la bibliothèque de murets refusée, pas les autres tilesheets.
    for mode in MODES:
        for path in [OUT / "architecture" / f"structure_{mode}.png", OUT / "architecture" / f"contacts_{mode}.png",
                     OUT / "tiled" / f"structure_{mode}.tsj", OUT / "tiled" / f"contacts_{mode}.tsj"]:
            # contacts_<mode>.png est remplacé par le nouveau catalogue homonyme.
            if path.parent.name == "architecture" and path.stem.startswith("contacts_"):
                continue
            if path.exists():
                path.unlink()
    print(f"Couloirs v2 : {len(records)} modules, {len(LAYERS)} calques, {sum(len(r.images) for r in registries.values())} pièces/tuiles partagées.")
    return manifest


if __name__ == "__main__":
    build()
