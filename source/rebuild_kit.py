"""Reconstruit les 12 salles depuis les bases et masques artistiques validés.

Aucune génération d'image et aucune segmentation aléatoire à l'export.
Les natifs du premier pack restent inchangés dans source/natives/.
GUILDE_ROOMS=01,03 permet de reconstruire un sous-ensemble sans modifier le reste.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_fill_holes
import json
import os
import struct
import zlib
import numpy as np

from pmd_lighting import access_lighting

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/passages"
OLD = json.loads((ROOT / "source/base_kit.json").read_text())
RULES = json.loads((ROOT / "source/regles_acces.json").read_text())
DEFINITIONS = json.loads((SOURCE / "definitions.json").read_text())["salles"]
MODES = ["jour", "nuit", "crepuscule", "aube", "soir", "orageux"]
LABELS = [
    ("00_exterieur", "Paysage extérieur interchangeable"),
    ("01_sol", "Sol continu et passages"),
    ("02_structure", "Structure et retours des passages"),
    ("03_cadres_fenetres", "Cadres et persiennes — sans paysage"),
    ("04_tableaux", "Contenu des tableaux encastrés"),
    ("05_porte_maitre", "Porte nord du bureau — hall uniquement"),
    ("06_decorations", "Décorations — vide"),
    ("07_objets", "Objets — vide"),
    ("08_ombres_acces", "Ombres de contact des accès"),
    ("09_eclairage_fixe", "Lumière et reflets des seuils"),
    ("10_bordure_avant", "Bordure avant et joues basses"),
]


def png(im, path):
    """Palette sans perte si possible ; aucun rééchantillonnage graphique."""
    a = np.array(im.convert("RGBA"))
    colors, idx = np.unique(a.reshape(-1, 4), axis=0, return_inverse=True)
    if len(colors) <= 256:
        q = Image.fromarray(idx.reshape(a.shape[:2]).astype("uint8"), "P")
        palette = np.zeros((256, 3), np.uint8)
        palette[:len(colors)] = colors[:, :3]
        q.putpalette(palette.ravel())
        q.info["transparency"] = bytes(colors[:, 3])
        q.save(path, optimize=True)
    else:
        im.save(path, optimize=True)


def night(im):
    a = np.array(im.convert("RGBA"))
    a[:, :, :3] = np.rint(a[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype("uint8")
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def cut(im, mask):
    a = np.array(im)
    a[~mask] = 0
    return Image.fromarray(a)


def astr(text):
    data = text.encode()
    return struct.pack("<H", len(data)) + data


def chunk(kind, data):
    return struct.pack("<IH", len(data) + 6, kind) + data


def ase(path, layers, size):
    w, h = size
    chunks = []
    for name, _ in layers:
        chunks.append(chunk(0x2004, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + astr(name)))
    for i, (_, im) in enumerate(layers):
        box = im.getbbox()
        if box:
            x, y, _, _ = box
            q = im.crop(box)
        else:
            x = y = 0
            q = Image.new("RGBA", (1, 1))
        data = struct.pack("<HhhBHh", i, x, y, 255, 2, 0) + b"\0" * 5
        data += struct.pack("<HH", q.width, q.height) + zlib.compress(q.tobytes(), 9)
        chunks.append(chunk(0x2005, data))
    data = b"".join(chunks)
    frame = struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA, len(chunks), 100, b"\0\0", len(chunks)) + data
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(frame) + 128, 0xA5E0, 1, w, h, 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.write_bytes(header + frame)


def tiled(path, room, images):
    w, h = room["dimensions"]
    cols, rows = w // 8, h // 8
    count = cols * rows
    sets, layers = [], []
    for i, ((name, label), q) in enumerate(zip(LABELS, images)):
        a = np.array(q)
        occupied = a[:, :, 3].reshape(rows, 8, cols, 8).max((1, 3)) > 0
        first = 1 + i * count
        data = np.arange(first, first + count, dtype=np.uint32).reshape(rows, cols)
        data[~occupied] = 0
        mode = path.stem.split("_")[1]
        sets.append({"firstgid": first, "name": name, "tilewidth": 8, "tileheight": 8,
                     "tilecount": count, "columns": cols, "image": f'../calques/{room["dossier"]}/{mode}/{name}.png',
                     "imagewidth": w, "imageheight": h, "margin": 0, "spacing": 0})
        layers.append({"id": i + 1, "name": label, "type": "tilelayer", "width": cols,
                       "height": rows, "x": 0, "y": 0, "opacity": 1, "visible": True, "data": data.ravel().tolist()})
    document = {"type": "map", "version": "1.10", "tiledversion": "1.11.0", "orientation": "orthogonal",
                "renderorder": "right-down", "tilewidth": 8, "tileheight": 8, "width": cols, "height": rows,
                "infinite": False, "nextlayerid": len(LABELS) + 1, "nextobjectid": 1, "layers": layers, "tilesets": sets,
                "properties": [{"name": "reperes_acces", "type": "file", "value": "../source/passages/definitions.json"}]}
    path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")))


def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_room(info):
    rid = info["id"]
    definition = DEFINITIONS[rid]
    base = Image.open(SOURCE / "bases" / f"{rid}.png").convert("RGBA")
    semantic = np.array(Image.open(SOURCE / "masques" / f"{rid}.png"))
    w, h = base.size
    assert [w, h] == info["dimensions"] == definition["dimensions"]
    alpha = np.array(base)[:, :, 3] > 0
    assert np.array_equal(semantic > 0, alpha)
    assert set(np.unique(semantic)) <= {0, 1, 2, 3, 4, 5, 10}

    # TOUS les interstices fermés sont conservés, y compris ceux de 1 à 11 pixels.
    hole = binary_fill_holes(alpha) & ~alpha
    windows = definition["fenetres"]
    expected_window_area = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in windows:
        expected_window_area[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = True
    assert not (hole & ~expected_window_area).any(), f"{rid}: trou hors fenêtre dans la source validée"
    fd = ROOT / "salles" / info["dossier"]
    hd = ROOT / "fenetres_exterieur" / rid
    fd.mkdir(parents=True, exist_ok=True)
    hd.mkdir(parents=True, exist_ok=True)
    Image.fromarray(hole.astype("uint8") * 255).save(hd / "masque.png", optimize=True)

    # Garder la position du panorama approuvé : l'inclusion des petits trous ne le déplace pas.
    scale = w / 648
    pan_h = round(432 * scale)
    target_y = np.mean([(b[1] + b[3]) / 2 for b in windows]) if windows else h * .3
    oy = round(target_y - 215 * scale)
    views = {}
    for weather in MODES:
        panorama = Image.open(ROOT / "exterieur" / f"{weather}.png").convert("RGBA").resize((w, pan_h), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (w, h))
        canvas.alpha_composite(panorama, (0, oy))
        pa = np.array(canvas)
        pa[:, :, 3] = hole.astype("uint8") * 255
        pa[~hole] = 0
        views[weather] = Image.fromarray(pa)
        png(views[weather], hd / f"{weather}.png")

    row = {"id": rid, "nom": info["nom"], "dossier": info["dossier"], "dimensions": [w, h],
           "cellules": [w // 8, h // 8], "acces": RULES["passages"][rid], "fenetres": windows,
           "trous_fenetres": int(hole.sum()), "porte_nord": [1019, 77, 1093, 214] if rid == "02" else None,
           "objets": [], "decorations": [], "passages_pmd": definition["passages"],
           "source_base": f"source/passages/bases/{rid}.png", "source_masque": f"source/passages/masques/{rid}.png", "fichiers": {}}
    for mode in ["jour", "nuit"]:
        body_base = base if mode == "jour" else night(base)
        shadow, light = access_lighting(base, semantic, definition["passages"], mode)
        blank = Image.new("RGBA", (w, h))
        bodies = [cut(body_base, semantic == i) for i in [1, 2, 3, 4, 5]]
        bodies += [blank.copy(), blank.copy(), shadow, light, cut(body_base, semantic == 10)]
        base_comp = Image.new("RGBA", (w, h))
        for q in bodies:
            base_comp.alpha_composite(q)
        assert np.array_equal(np.array(base_comp)[:, :, 3] > 0, alpha)
        png(base_comp, fd / f"base_{mode}_transparente.png")
        magenta = Image.new("RGBA", (w, h), (255, 0, 255, 255))
        magenta.alpha_composite(base_comp)
        png(magenta, fd / f"base_{mode}_magenta.png")
        images = [views[mode]] + bodies
        ld = ROOT / "calques" / info["dossier"] / mode
        ld.mkdir(parents=True, exist_ok=True)
        composed = Image.new("RGBA", (w, h))
        for (name, _), q in zip(LABELS, images):
            png(q, ld / f"{name}.png")
            composed.alpha_composite(q)
        png(composed, fd / f"salle_{mode}.png")
        ase(fd / f"{rid}_{mode}.aseprite", [(label, q) for (_, label), q in zip(LABELS, images)], (w, h))
        tiled(ROOT / "tiled" / f"{rid}_{mode}.tmj", row, images)
        row["fichiers"][mode] = {"png": f'salles/{info["dossier"]}/salle_{mode}.png',
                                "base": f'salles/{info["dossier"]}/base_{mode}_transparente.png',
                                "magenta": f'salles/{info["dossier"]}/base_{mode}_magenta.png',
                                "aseprite": f'salles/{info["dossier"]}/{rid}_{mode}.aseprite'}
    print(rid, "passages", len(definition["passages"]), "fenêtres", len(windows), "pixels transparents", int(hole.sum()))
    return row


def main():
    for name in ["salles", "calques", "fenetres_exterieur", "apercus", "tiled"]:
        (ROOT / name).mkdir(exist_ok=True)
    selected = set(filter(None, os.environ.get("GUILDE_ROOMS", "").split(",")))
    known = {r["id"] for r in OLD["salles"]}
    if selected - known:
        raise ValueError(f"Salles inconnues : {sorted(selected - known)}")
    manifest = {"titre": "Guilde Treehouse — entrées et sorties PMD", "version_passages": 2,
                "grille_px": 8, "animation": False, "ambiances": MODES, "regles_acces": RULES,
                "calques": [{"id": lid, "nom": name} for lid, name in LABELS], "salles": []}
    existing = json.loads((ROOT / "kit.json").read_text()) if selected else None
    previous = {r["id"]: r for r in existing["salles"]} if existing else {}
    for room in OLD["salles"]:
        if selected and room["id"] not in selected:
            manifest["salles"].append(previous[room["id"]])
        else:
            manifest["salles"].append(build_room(room))
    (ROOT / "kit.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    for mode in ["jour", "nuit"]:
        board = Image.new("RGB", (1536, 1240), (18, 20, 47))
        draw = ImageDraw.Draw(board)
        draw.text((24, 16), f"GUILDE TREEHOUSE / ACCÈS PMD / {mode.upper()}", font=font(21), fill=(237, 226, 190))
        draw.text((24, 48), "DA conservée · passages en retrait · sols continus · contacts et lumières des seuils · fenêtres corrigées", font=font(13), fill=(178, 192, 180))
        for i, row in enumerate(manifest["salles"]):
            q = Image.open(ROOT / row["fichiers"][mode]["png"]).convert("RGBA")
            q.thumbnail((494, 250), Image.Resampling.NEAREST)
            x, y = i % 3 * 512, 80 + i // 3 * 285
            board.paste(q, (x + (512 - q.width) // 2, y + (250 - q.height) // 2), q)
            draw.text((x + 20, y + 255), row["id"] + "  " + row["nom"], font=font(13), fill=(237, 226, 190))
        board.save(ROOT / "apercus" / f"planche_{mode}.png", optimize=True)
    print("Kit reconstruit : 12 salles fixes, masques validés, contacts et lumières jour/nuit.")


if __name__ == "__main__":
    main()
