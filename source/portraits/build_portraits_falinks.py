#!/usr/bin/env python3
"""Portraits d'émotions de Falinks (#0870) au format PMDCollab / SpriteBot.

Méthode : le portrait « Normal » publié sur PMDCollab (Emmuffin, licence PMDCollab_2)
sert de base et n'est jamais redessiné. Chaque émotion est une retouche pixel décrite
ci-dessous : yeux du brass (et des deux troupiers visibles sur les bords), effets
(goutte, larmes, marque de colère, croix, étincelles) et fond aux couleurs Chunsoft
de l'émotion, relevées sur les portraits officiels de Pikachu. Aucun pixel n'est
peint par un générateur d'images : le résultat est une feuille pixel-art contrôlée.

Sorties, dans portraits/falinks/ :
- emotions/<Emotion>.png et emotions/<Emotion>^.png : 40 × 40, RGBA opaque ;
- planche_spritebot.png : 200 × 320, ordre officiel du gabarit, moitié basse retournée ;
- planche_spritebot_160.png : mêmes 16 émotions sans la moitié retournée ;
- apercu.png : planche de lecture × 4 ;
- kit.json et credits.txt.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "source" / "portraits"
OUT = ROOT / "portraits" / "falinks"
REF = SRC / "reference" / "0870_Normal.png"
MAX_COLOURS = 15

# Ordre officiel de sprite_config.json (SpriteCollab) : 5 colonnes × 4 rangées ;
# la moitié basse du gabarit reçoit les versions retournées (« ^ »).
EMOTIONS = ["Normal", "Happy", "Pain", "Angry", "Worried",
            "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
            "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
            "Special1", "Sigh", "Stunned", "Special2", "Special3"]
PRODUCED = [e for e in EMOTIONS if not e.startswith("Special")]

# Palette du portrait Normal : 11 couleurs du personnage + 4 couleurs de fond.
PAL = {
    "0": (52, 50, 56), "5": (71, 71, 80), "2": (87, 87, 95),
    "1": (154, 34, 35), "8": (203, 61, 63),
    "6": (143, 112, 32), "4": (213, 167, 51), "7": (245, 209, 83),
    "A": (58, 155, 202), "E": (150, 226, 227), "B": (255, 255, 255),
    "3": (119, 199, 215), "D": (178, 221, 201), "9": (239, 255, 200), "C": (196, 195, 176),
}
FACE = PAL["2"]
OUTLINE = PAL["0"]
SKY_ROWS = 9          # les pixels « A » situés au-dessus sont l'anticrénelage ciel/cimier
BOTTOM_ROWS = 34      # le gris « C » en dessous est l'anticrénelage du fond bas

# Fonds Chunsoft par émotion (haut, bas), relevés sur les portraits officiels.
BACKGROUNDS = {
    "Happy": ((255, 255, 191), (255, 239, 119)),
    "Pain": ((111, 135, 183), (167, 207, 223)),
    "Angry": ((247, 111, 143), (223, 127, 175)),
    "Worried": ((143, 167, 207), (167, 207, 223)),
    "Sad": ((119, 135, 183), (167, 207, 223)),
    "Crying": ((119, 135, 175), (167, 207, 223)),
    "Teary-Eyed": ((247, 191, 199), (231, 143, 175)),
    "Determined": ((239, 143, 191), (247, 111, 151)),
    "Joyous": ((255, 255, 191), (255, 231, 127)),
    "Inspired": ((255, 255, 191), (255, 239, 135)),
    "Sigh": ((253, 241, 165), (253, 229, 120)),
    "Stunned": ((119, 134, 177), (143, 207, 199)),
    "Dizzy": ((143, 207, 199), (143, 207, 199)),
    "Surprised": ((223, 231, 239), (223, 231, 239)),
    "Shouting": ((135, 199, 247), (191, 247, 191)),
}
ZIGZAG = (119, 135, 175)      # rayures de Surprised (palette Chunsoft)
SALMON = (255, 143, 135)      # croix de Joyous (palette Chunsoft)

# Yeux de la base : gauche x 17-20 / y 23-28, droit x 26-28 / y 23-28.
LEFT_BOX = (16, 22, 5, 8)
RIGHT_BOX = (26, 22, 5, 8)
TROOPER_EYES = [(0, 26), (0, 27), (0, 28), (39, 22), (39, 23), (39, 24), (39, 25)]

# Légende des motifs : A/E/B = lumière de l'œil ; W = blanc ; Z = rayure ;
# 0/5/2 = ombres du visage ; '.' = pixel conservé.
LEGEND = {"A": PAL["A"], "E": PAL["E"], "B": PAL["B"], "W": PAL["B"], "Z": ZIGZAG, "S": SALMON,
          "0": PAL["0"], "5": PAL["5"], "2": PAL["2"]}


def rows(text: str) -> list[str]:
    return text.strip("\n").splitlines()


# ----------------------------------------------------------------------------
# Yeux : (x, y, motif) pour l'œil gauche (proche) et droit (éloigné).
# ----------------------------------------------------------------------------
EYES = {
    "Happy": {   # arches fermées « ∩ »
        "left": (17, 24, rows(".AA.\nABBA\nA..A\nA..A")),
        "right": (26, 24, rows(".A.\nABA\nA.A\nA.A")),
    },
    "Joyous": {  # arches plus hautes, remontées d'un pixel
        "left": (17, 23, rows(".AA.\nABBA\nA..A\nA..A\nA..A")),
        "right": (26, 23, rows(".A.\nABA\nA.A\nA.A\nA.A")),
    },
    "Pain": {    # œil proche fermé en chevron « > », œil éloigné à demi ouvert
        "left": (17, 24, rows("AA..\n..AA\nAA..")),
        "right": (26, 25, rows(".A.\nABE\nAEA\n.A.")),
    },
    "Angry": {   # fentes rabattues vers le nez « \ / »
        "left": (17, 24, rows("A...\nABA.\nABBA\nAEBA\n.AA.")),
        "right": (26, 24, rows("..A\n.EA\nABA\nAEA\n.A.")),
    },
    "Determined": {  # même pente, plus douce, œil plein et lumineux
        "left": (17, 23, rows(".A..\nAEBA\nABBA\nABBA\nAEBA\n.AA.")),
        "right": (26, 23, rows("..A\n.BE\nABE\nABE\nAEA\n.A.")),
    },
    "Worried": {  # coin intérieur relevé « / \ »
        "left": (17, 24, rows("...A\n.ABA\nABBA\nAEBA\n.AA.")),
        "right": (26, 24, rows("A..\nAB.\nABA\nAEA\n.A.")),
    },
    "Sad": {      # paupière plate à mi-hauteur, regard abaissé
        "left": (17, 26, rows("AAAA\nABBA\nAEBA\n.AA.")),
        "right": (26, 26, rows("AAA\nABE\nAEA\n.A.")),
    },
    "Crying": {   # yeux serrés « > < »
        "left": (17, 23, rows("AA..\n.AA.\n..AB\n.AA.\nAA..")),
        "right": (26, 23, rows("..AA\n.AA.\nBA..\n.AA.\n..AA")),
    },
    "Shouting": {  # yeux grands ouverts, pente de colère : cri de guerre
        "left": (17, 22, rows("A...\nABA.\nABBA\nABBA\nABBA\nAEBA\n.AA.")),
        "right": (26, 22, rows("..A\n.EA\nABA\nABE\nABE\nAEA\n.A.")),
    },
    "Teary-Eyed": {  # yeux normaux, lumière mouillée
        "left": (17, 23, rows(".AA.\nAEB.\nAEBA\nAEBA\nAEEA\n.AA.")),
        "right": (26, 23, rows(".A.\nABE\nABE\nAEE\nAEA\n.A.")),
    },
    "Inspired": {  # étoiles
        "left": (16, 23, rows("..B..\n.EBE.\nBBBBB\n.EBE.\n..B..")),
        "right": (26, 23, rows(".B.\nEBE\nBBB\nEBE\n.B.")),
    },
    "Surprised": {  # yeux écarquillés, petite pupille
        "left": (16, 22, rows(".AAA.\nABBBA\nABBBA\nABEBA\nABEBA\nABBBA\n.AAA.")),
        "right": (26, 22, rows(".AA.\nABBA\nABBA\nAEBA\nAEBA\nABBA\n.AA.")),
    },
    "Dizzy": {    # spirales : anneau ouvert avec point central
        "left": (16, 23, rows(".AAA.\nA...A\nA.A.A\nA...A\n.AA..")),
        "right": (26, 23, rows(".AAA.\nA...A\nA.A.A\nA...A\n..AA.")),
    },
    "Sigh": {     # yeux fermés, détendus
        "left": (17, 25, rows("A..A\n.EE.")),
        "right": (26, 25, rows("A.A\n.E.")),
    },
    "Stunned": {  # lumière éteinte, pupille fixe
        "left": (17, 23, rows(".AA.\nA..A\nA.BA\nA..A\n.AA.")),
        "right": (26, 23, rows(".A.\nA.A\nABA\nA.A\n.A.")),
    },
}

# ----------------------------------------------------------------------------
# Effets : (x, y, motif, mode). « over » recouvre le personnage (goutte sur le
# cimier, larmes sur la joue) ; « bg » ne peint que sur le fond.
# ----------------------------------------------------------------------------
DROP = rows("..0..\n.0E0.\n0EEE0\n0EEB0\n0EBB0\n.000.")
ANGER_MARK = rows("..W.W..\n..W.W..\nWW...WW\n.......\nWW...WW\n..W.W..\n..W.W..")
CROSS = rows("SS..SS\nSSSSSS\n.SSSS.\n.SSSS.\nSSSSSS\nSS..SS")
SPARKLE = rows("..W..\n..W..\nWWWWW\n..W..\n..W..")
TEAR_L = rows("E\nB\nE\nE\nB")
TEAR_R = rows("E\nB\nE\nE")

EFFECTS = {
    "Pain": [(33, 0, DROP, "over")],
    "Angry": [(32, 0, ANGER_MARK, "over")],
    "Crying": [(17, 29, TEAR_L, "over"), (29, 29, TEAR_R, "over"),
               (14, 23, rows("EB\nEE"), "over"), (30, 23, rows("BE\nEE"), "over")],
    "Teary-Eyed": [(16, 28, rows(".E\nEB"), "over"), (29, 28, rows("E.\nBE"), "over")],
    "Joyous": [(1, 0, CROSS, "bg"), (33, 0, CROSS, "bg")],
    "Inspired": [(2, 0, SPARKLE, "bg"), (33, 0, SPARKLE, "bg"), (12, 1, rows("W"), "bg")],
    "Sigh": [(7, 0, DROP, "over")],
    "Stunned": [(33, 0, DROP, "over")],
}
# Toute l'escouade réagit : les fentes des troupiers visibles se ferment aussi.
TROOPERS_CLOSED = {"Happy", "Joyous", "Sigh", "Crying"}

# Versions retournées « ^ » : miroir horizontal exact. Le dépôt PMDCollab n'a pas de
# Normal^ pour la forme normale ; c'est aussi ce que fait le moteur sans fichier « ^ ».


def load_base() -> tuple[np.ndarray, np.ndarray]:
    im = Image.open(REF).convert("RGBA")
    assert im.size == (40, 40)
    rgb = np.array(im)[:, :, :3].copy()
    inv = {v: k for k, v in PAL.items()}
    keys = np.empty((40, 40), dtype="<U1")
    for y in range(40):
        for x in range(40):
            keys[y, x] = inv[tuple(int(v) for v in rgb[y, x])]
    return rgb, keys


def mix(a, b, t=0.5):
    return tuple(int(round(p * (1 - t) + q * t)) for p, q in zip(a, b))


def paint(rgb, x0, y0, motif, mask=None, touched=None):
    for dy, line in enumerate(motif):
        for dx, ch in enumerate(line):
            if ch == ".":
                continue
            x, y = x0 + dx, y0 + dy
            if not (0 <= x < 40 and 0 <= y < 40):
                continue
            if mask is not None and not mask[y, x]:
                continue
            rgb[y, x] = LEGEND[ch]
            if touched is not None:
                touched[y, x] = True


def masks(keys):
    ys = np.arange(40)[:, None]
    bg = np.isin(keys, ["3", "D", "9"])
    sky_aa = (keys == "A") & (ys < SKY_ROWS)
    return bg, sky_aa


def background(name, rgb, keys, bg, sky_aa):
    top, bottom = BACKGROUNDS[name]
    ys, xs = np.nonzero(bg)
    if name == "Shouting":
        cx, cy = 22.0, 28.0
        for y, x in zip(ys, xs):
            sector = int(np.floor((np.arctan2(y - cy, x - cx) + np.pi) / (2 * np.pi / 14)))
            rgb[y, x] = top if sector % 2 == 0 else bottom
        rgb[sky_aa] = mix(top, OUTLINE)
        return {"type": "rayons", "couleurs": [top, bottom]}
    if name == "Surprised":
        tri = [0, 1, 2, 3, 3, 2, 1, 0]
        for y, x in zip(ys, xs):
            rgb[y, x] = ZIGZAG if (y + tri[x % 8]) % 6 < 3 else top
        rgb[sky_aa] = ZIGZAG
        return {"type": "zigzag", "couleurs": [top, ZIGZAG]}
    for y, x in zip(ys, xs):
        rgb[y, x] = top if keys[y, x] in ("3", "D") else bottom
    rgb[sky_aa] = mix(top, OUTLINE)
    return {"type": "degrade" if top != bottom else "uni", "couleurs": [top, bottom]}


def clear_eyes(rgb, keys, touched):
    for (x0, y0, w, h) in (LEFT_BOX, RIGHT_BOX):
        zone = keys[y0:y0 + h, x0:x0 + w]
        sel = np.isin(zone, ["A", "E", "B"])
        rgb[y0:y0 + h, x0:x0 + w][sel] = FACE
        touched[y0:y0 + h, x0:x0 + w] |= sel


def build_emotion(name, base_rgb, keys):
    rgb = base_rgb.copy()
    touched = np.zeros((40, 40), bool)
    bg, sky_aa = masks(keys)
    info = {"fond": None, "yeux": [], "effets": [], "troupiers": "ouverts"}
    if name == "Normal":
        return rgb, info
    info["fond"] = background(name, rgb, keys, bg, sky_aa)
    clear_eyes(rgb, keys, touched)
    for side in ("left", "right"):
        x0, y0, motif = EYES[name][side]
        paint(rgb, x0, y0, motif, touched=touched)
        info["yeux"].append({"cote": side, "x": x0, "y": y0,
                             "largeur": max(map(len, motif)), "hauteur": len(motif)})
    if name in TROOPERS_CLOSED:
        for x, y in TROOPER_EYES:
            rgb[y, x] = FACE
            touched[y, x] = True
        info["troupiers"] = "fermes"
    for x0, y0, motif, mode in EFFECTS.get(name, []):
        paint(rgb, x0, y0, motif, mask=bg if mode == "bg" else None, touched=touched)
        info["effets"].append({"x": x0, "y": y0, "largeur": max(map(len, motif)),
                               "hauteur": len(motif), "mode": mode})
    ys, xs = np.nonzero(touched)
    info["pixels_retouches_hors_fond"] = int(touched.sum())
    info["zone_retouchee"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return rgb, info


def flipped(rgb):
    return rgb[:, ::-1].copy()


def to_image(rgb):
    rgba = np.dstack([rgb, np.full((40, 40), 255, np.uint8)])
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def colours(rgb):
    return sorted(set(map(tuple, rgb.reshape(-1, 3).tolist())))


def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(images, path):
    zoom, cols = 4, 4
    cell_w, cell_h = 40 * zoom + 24, 40 * zoom + 40
    rows_n = -(-len(PRODUCED) // cols)
    sheet = Image.new("RGBA", (cols * cell_w + 24, rows_n * cell_h + 72), (26, 26, 46, 255))
    d = ImageDraw.Draw(sheet)
    d.text((24, 18), "FALINKS #0870 — PORTRAITS D'ÉMOTIONS PMD (×4)", fill=(240, 240, 240, 255), font=font(20))
    d.text((24, 44), "Base : portrait Normal PMDCollab (Emmuffin) · 16 émotions · 40 × 40 px · 15 couleurs max",
           fill=(170, 170, 200, 255), font=font(13))
    for i, n in enumerate(PRODUCED):
        x = 24 + (i % cols) * cell_w
        y = 72 + (i // cols) * cell_h
        sheet.paste(images[n].resize((40 * zoom, 40 * zoom), Image.NEAREST), (x, y))
        count = len(colours(np.array(images[n])[:, :, :3]))
        d.text((x, y + 40 * zoom + 6), f"{n}  ·  {count} couleurs", fill=(230, 230, 230, 255), font=font(13))
    sheet.save(path)


def spritebot_sheet(images, flips):
    sheet = Image.new("RGBA", (200, 320), (0, 0, 0, 0))
    for i, name in enumerate(EMOTIONS):
        if name in images:
            sheet.paste(images[name], ((i % 5) * 40, (i // 5) * 40))
            sheet.paste(flips[name], ((i % 5) * 40, 160 + (i // 5) * 40))
    return sheet


def main():
    base_rgb, keys = load_base()
    (OUT / "emotions").mkdir(parents=True, exist_ok=True)
    images, flips, infos = {}, {}, {}
    for name in PRODUCED:
        rgb, info = build_emotion(name, base_rgb, keys)
        pal = colours(rgb)
        assert len(pal) <= MAX_COLOURS, f"{name} : {len(pal)} couleurs"
        info["couleurs"] = len(pal)
        info["palette"] = ["#%02x%02x%02x" % c for c in pal]
        images[name] = to_image(rgb)
        flips[name] = to_image(flipped(rgb))
        images[name].save(OUT / "emotions" / f"{name}.png")
        flips[name].save(OUT / "emotions" / f"{name}^.png")
        infos[name] = info
    sheet = spritebot_sheet(images, flips)
    sheet.save(OUT / "planche_spritebot.png")
    sheet.crop((0, 0, 200, 160)).save(OUT / "planche_spritebot_160.png")
    contact_sheet(images, OUT / "apercu.png")
    kit = {
        "pokemon": {"numero": "0870", "nom": "Falinks", "forme": "0000"},
        "base": {"fichier": "source/portraits/reference/0870_Normal.png",
                 "auteur": "Emmuffin (<@!356635814668664832>)", "licence": "PMDCollab_2",
                 "source": "https://sprites.pmdcollab.org/#/0870"},
        "format": {"portrait": [40, 40], "planche": [200, 320], "grille": [5, 8], "ordre": EMOTIONS,
                   "moitie_basse": "versions retournées « ^ » : miroir horizontal exact de chaque portrait",
                   "cases_vides": ["Special0", "Special1", "Special2", "Special3"]},
        "palette_base": {k: "#%02x%02x%02x" % v for k, v in PAL.items()},
        "boites_yeux": {"gauche": LEFT_BOX, "droite": RIGHT_BOX, "troupiers": TROOPER_EYES},
        "emotions": infos,
    }
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(images)} portraits (+ versions ^), planche 200 × 320, aperçu et kit écrits dans {OUT.relative_to(ROOT)}")
    for name in PRODUCED:
        print(f"  {name:11s} {infos[name]['couleurs']:2d} couleurs")


if __name__ == "__main__":
    main()
