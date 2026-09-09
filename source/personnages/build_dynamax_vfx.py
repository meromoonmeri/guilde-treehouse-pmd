#!/usr/bin/env python3
"""VFX Dynamax génériques : effets seuls, sans personnage ni fond, à superposer en jeu sur n'importe quel sprite.

Trois effets (la formation des nuages en plus), chacun en deux tailles (M : corps ≤ 24 px à l'échelle 1, L : au-delà), dessinés en pixel art à
l'échelle 1 puis agrandis × 3 comme les sprites Dynamax (`dynamax_fx.py` pour les pièces) :

- `transformation` : 15 images, 62 ticks — rayon fin qui descend du ciel, colonne d'énergie opaque (bord clair,
  bandes rouges où coulent des étincelles, cœur cramoisi) enroulée d'éclairs épais et opaques en zigzag qui
  s'abattent en tournant, flash en étoile (colonne surexposée), dissolution en lames, onde de choc au sol. Le
  sprite du Pokémon n'y figure pas : le jeu masque le petit sprite quand la colonne devient opaque (image 5) et
  affiche le sprite Dynamax à HitFrame (image 11, le flash). Ancre = sol.
- `nuages` : apparition (5 images, 24 ticks : 1, 2 puis 3 nuages) puis boucle de 12 images (48 ticks) — trois
  nuages-cyclones tournent sur une ellipse au-dessus de la tête ; volute à trois phases et traînée effilée. Un tiers
  de tour par boucle : continue ; la dernière image de l'apparition précède l'image 0 de la boucle. Ancre = centre
  de l'anneau (à poser 2 px au-dessus du sommet du sprite : `kit.json` de chaque pack donne le décalage).
- `aura` : 4 images en boucle (16 ticks) — anneau d'énergie générique (ellipse) pour un sprite qui n'a pas d'aura
  intégrée ; les packs Dynamax de ce dépôt ont déjà l'aura dans leurs feuilles, cet effet sert aux autres sprites.

Format : feuilles `<Effet>-<Taille>.png` (une ligne, une colonne par image), `AnimData.xml` façon SpriteCollab
(index libres ≥ 13 ; une seule direction : un VFX n'a pas d'orientation), `*-Offsets.png` (centre vert = ancre)
et `*-Shadow.png` (pixel blanc = ancre) pour que les lecteurs du dépôt et SkyTemple les affichent ; Aseprite,
GIF sur fond damier et sur le parquet, `kit.json`, `README.md`.

Usage : python3 source/personnages/build_dynamax_vfx.py [--echelle N]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
from build_falinks_sprite import Composed, font, parquet_background, sheet, write_aseprite  # noqa: E402
from build_dynamax_sprites import save_png  # noqa: E402
import dynamax_fx as FX  # noqa: E402

OUT = ROOT / "personnages" / "dynamax" / "vfx"
SCALE = 3
STRUCT = np.ones((3, 3), bool)

# paramètres par taille : largeur du corps visé (px à l'échelle 1), orbite des nuages (rx, ry), largeur de colonne
# `geant` : hauteur nominale du Pokémon Dynamax dans l'unité du VFX (1 px = 1 px du sprite source, puisque le sprite
# Dynamax et le VFX sont tous deux agrandis × 3) ; le Pokémon normal fait donc un tiers de cette hauteur.
SIZES = {
    "M": {"corps": 20, "geant": 24, "orbite": (13, 4), "colonne": 22, "hauteur": 60, "petits_nuages": True},
    "L": {"corps": 32, "geant": 28, "orbite": (19, 5), "colonne": 34, "hauteur": 72, "petits_nuages": False},
}
TRANSFORM_PLAN = [
    ("beam1", 4), ("beam2", 4), ("beam3", 4), ("beam4", 3),
    ("column0", 5), ("column1", 5), ("column2", 5), ("column3", 5), ("column4", 5), ("column5", 5),
    ("flash0", 3), ("flash1", 3), ("flash2", 3),
    ("burst0", 4), ("burst1", 4),
]
# apparition des nuages : (nombre de nuages, image de la boucle Nuages reprise, durée) ; la dernière précède l'image 0
CLOUD_INTRO = [(1, 0, 5), (2, 3, 5), (3, 6, 5), (3, 9, 5), (3, 11, 4)]
CLOUD_FRAMES = 12
CLOUD_TICKS = 4
AURA_FRAMES = 4
AURA_TICKS = 4


def dilate(mask: np.ndarray) -> np.ndarray:
    return binary_dilation(mask, STRUCT)


def paste(canvas: np.ndarray, img: np.ndarray, x: int, y: int) -> None:
    h, w = img.shape[:2]
    H, W = canvas.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    src = img[y0 - y:y1 - y, x0 - x:x1 - x]
    m = src[:, :, 3] > 0
    canvas[y0:y1, x0:x1][m] = src[m]


def upscale(img: np.ndarray, scale: int) -> np.ndarray:
    return np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)


# ---------------------------------------------------------------------------
# Nuages : anneau au-dessus de la tête, ancre = centre de l'anneau
# ---------------------------------------------------------------------------
def cloud_frame(size: str, k: int, n: int, n_clouds: int = 3, spin: float = 0.0) -> np.ndarray:
    """Canevas 1:1 centré sur l'ancre (W/2, H/2) ; les nuages font un tiers de tour sur les n images."""
    p = SIZES[size]
    rx, ry = p["orbite"]
    clouds = FX.clouds(small=p["petits_nuages"])
    cw, ch = clouds[0].shape[1], clouds[0].shape[0]
    W, H = 2 * (rx + cw) + 8, 2 * (ry + ch) + 8
    canvas = np.zeros((H, W, 4), np.uint8)
    cx, cy = W // 2, H // 2
    frac = k / n
    base = -math.pi / 2 + spin + (2 * math.pi / 3) * frac
    placements = []
    for j in range(n_clouds):
        ang = base + j * 2 * math.pi / 3
        phase = (int(frac * 9) + j) % 3
        c = clouds[phase]
        px = int(round(cx + rx * math.cos(ang))) - cw // 2
        py = int(round(cy + ry * math.sin(ang))) - ch // 2
        trail = FX.TRAIL_SMALL if p["petits_nuages"] else FX.TRAIL
        # devant (sin > 0) le nuage va vers la droite : traînée à gauche ; derrière il va vers la gauche : à droite
        if math.sin(ang) > 0:
            tx, trail = px - trail.shape[1] + 1, trail
        else:
            tx, trail = px + cw - 1, trail[:, ::-1]
        placements.append((math.sin(ang), c, px, py, trail, tx, py + ch // 2 - 1))
    # ordre de profondeur : du fond (sin < 0) vers l'avant
    for _, c, px, py, trail, tx, ty in sorted(placements, key=lambda t: t[0]):
        paste(canvas, trail, tx, ty)
        paste(canvas, c, px, py)
    return canvas


# ---------------------------------------------------------------------------
# Aura générique : ellipse d'énergie autour d'un corps de la taille visée
# ---------------------------------------------------------------------------
def aura_frame(size: str, k: int) -> np.ndarray:
    p = SIZES[size]
    bw, bh = p["corps"], int(p["corps"] * 1.15)
    W, H = bw + 12, bh + 12
    yy, xx = np.indices((H, W))
    cx, cy = W / 2 - 0.5, H / 2 - 0.5
    body = ((xx - cx) / (bw / 2)) ** 2 + ((yy - cy) / (bh / 2)) ** 2 <= 1.0
    img = FX.aura(body, k % 4, dilate)
    return img


# ---------------------------------------------------------------------------
# Transformation : ancre = sol (bas du canevas - 4)
# ---------------------------------------------------------------------------
def transform_geometry(size: str) -> dict:
    p = SIZES[size]
    W, H = p["colonne"] + 40, p["hauteur"] + 6
    return {"W": W, "H": H, "cx": W // 2, "ground": H - 4, "geant": p["geant"], "col_w": p["colonne"]}


def transform_frame(size: str, step: str) -> np.ndarray:
    """Une image de la transformation, à l'échelle 1 ; ancre = (W/2, H - 4) = sol du Pokémon."""
    g = transform_geometry(size)
    W, H, cx, ground, geant, col_w = (g[k] for k in ("W", "H", "cx", "ground", "geant", "col_w"))
    canvas = np.zeros((H, W, 4), np.uint8)
    body_top = ground - geant // SCALE                        # sommet du Pokémon normal
    giant_top = ground - geant                                # sommet du Pokémon Dynamax
    cloud_y = giant_top - 6                                   # hauteur vers laquelle montent les volutes

    if step.startswith("beam"):
        k = int(step[-1])
        w = (3, 5, 7, 9)[k - 1]
        paste(canvas, FX.beam(w, body_top + 2, k), cx - w // 2, 0)
        FX.filled_ellipse(canvas, cx, body_top + 1, 2 + 2 * k, 1 + k // 2, FX.FX_LIGHT)
        FX.filled_ellipse(canvas, cx, body_top + 1, 1 + k, max(1, k // 2), FX.FX_WHITE)
        if k >= 3:
            FX.flash_burst(cx, body_top, 5 + 3 * k, 8, k, canvas, 1)
        return canvas

    if step.startswith("column"):
        k = int(step[-1])
        w = col_w if k >= 1 else col_w * 2 // 3
        col = FX.column(w, ground + 1, k)
        # un éclair épais en hélice (un tour sur la hauteur), zigzag large ; sa moitié arrière avant la colonne
        pts, front = FX.spiral_bolt(cx, 2, ground - 3, w // 2 + 5, 3, 1.0, k * 0.8, 9, 6)
        back = [pt for pt, f in zip(pts, front) if not f]
        if len(back) >= 2:
            FX.bolt(back, 2, canvas)
        paste(canvas, col, cx - w // 2, 0)
        FX.filled_ellipse(canvas, cx, ground, w // 2 + 3 + (k % 2), 3, FX.FX_RED)
        FX.filled_ellipse(canvas, cx, ground, w // 2 - 1, 2, FX.FX_LIGHT)
        fr = [pt for pt, f in zip(pts, front) if f]
        if len(fr) >= 2:
            FX.bolt(fr, 3, canvas)
        # second éclair, plus court, qui s'abat sur la moitié haute (décalé d'un demi-tour)
        pts2, front2 = FX.spiral_bolt(cx, 2, ground // 2, w // 2 + 4, 2, 0.5, k * 0.8 + math.pi, 5, 5)
        fr2 = [pt for pt, f in zip(pts2, front2) if f]
        if len(fr2) >= 2:
            FX.bolt(fr2, 2, canvas)
        for j2 in range(-3, 4):
            if (j2 + k) % 2 and j2:
                x = cx + j2 * (w // 5 + 1)
                y = ground - 2 - abs(j2) - (k % 3)
                if 1 <= x < W - 2 and 1 <= y < H - 2:
                    canvas[y:y + 2, x:x + 2] = (*FX.FX_WHITE, 255)
        return canvas

    if step.startswith("flash"):
        k = int(step[-1])
        mid = (giant_top + ground) // 2
        if k == 0:                                             # colonne surexposée + grand éclat en étoile
            col = FX.column(col_w + 4, ground + 1, 0, white=True)
            paste(canvas, col, cx - (col_w + 4) // 2, 0)
            FX.flash_burst(cx, mid, W // 2 - 1, 16, 0, canvas, 3)
            FX.filled_ellipse(canvas, cx, mid, col_w // 2 + 4, 10, FX.FX_WHITE)
        elif k == 1:                                           # la colonne se dissout en lames qui montent
            for j2, x in enumerate(range(cx - col_w // 2 - 4, cx + col_w // 2 + 5, 4)):
                bottom = ground - 6 - 8 * (j2 % 3)
                top = 4 * ((j2 + 1) % 2)
                colour = FX.FX_WHITE if j2 % 2 else FX.FX_LIGHT
                if 0 <= x < W - 3:
                    canvas[top:bottom, x:x + 3] = (*colour, 255)
            FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 4, 3, 2, FX.FX_LIGHT)
            FX.flash_burst(cx, mid, W // 2 - 3, 12, 1, canvas, 2)
        else:                                                  # dernières lames dans le haut, anneau qui s'ouvre
            for j2, x in enumerate(range(cx - col_w // 2 - 8, cx + col_w // 2 + 9, 6)):
                bottom = ground // 2 - 6 * (j2 % 3)
                if 0 <= x < W - 2:
                    canvas[2 + 3 * (j2 % 2):bottom, x:x + 2] = (*FX.FX_LIGHT, 255)
            FX.ellipse_ring(canvas, cx, mid, col_w // 2 + 10, 18, 2, FX.FX_RED)
            FX.flash_burst(cx, mid, W // 3, 8, 2, canvas, 1)
        return canvas

    if step.startswith("burst"):
        k = int(step[-1])
        FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 6 + 8 * k, 4 + 2 * k, 3, FX.FX_LIGHT if k == 0 else FX.FX_RED)
        for j2 in range(10):
            ang = j2 * math.pi / 5 + k * 0.5
            dist = col_w // 2 + 4 + 6 * k
            x = int(round(cx + dist * math.cos(ang)))
            y = int(round(ground - 10 - 12 * k - 8 * abs(math.sin(ang))))
            if 1 <= x < W - 2 and 1 <= y < H - 2:
                canvas[y:y + 2, x:x + 2] = (*(FX.FX_RED if j2 % 2 else FX.FX_WHITE), 255)
        rx, ry = SIZES[size]["orbite"]
        for j2 in range(6):                                    # brumes (petites volutes) qui montent vers l'anneau
            ang = j2 * math.pi / 3 + k * 0.4
            x = int(round(cx + (rx - 2 * k) * math.cos(ang)))
            y = int(round(cloud_y + 12 - 6 * k + ry * math.sin(ang)))
            if 2 <= x < W - 5 and 2 <= y < H - 3:
                canvas[y - 1:y + 2, x:x + 3 + k] = (*FX.FX_RED, 255)
                canvas[y, x + 1:x + 2 + k] = (*FX.FX_LIGHT, 255)
        return canvas

    raise ValueError(step)


def cloud_intro_frame(size: str, k: int) -> np.ndarray:
    """Apparition des nuages (même canevas et même ancre que la boucle) : 1, 2 puis 3 nuages, avec des volutes
    résiduelles autour de l'anneau sur les trois premières images."""
    n_clouds, step, _ = CLOUD_INTRO[k]
    canvas = cloud_frame(size, step, CLOUD_FRAMES, n_clouds)
    H, W = canvas.shape[:2]
    cx, cy = W // 2, H // 2
    rx, ry = SIZES[size]["orbite"]
    if k < 3:
        for j2 in range(5 - k):
            ang = j2 * 1.3 + k
            x = int(round(cx + (rx + 5) * math.cos(ang)))
            y = int(round(cy + (ry + 3) * math.sin(ang)))
            if 1 <= x < W - 3 and 1 <= y < H - 2:
                canvas[y, x:x + 2] = (*FX.FX_RED, 255)
    return canvas


# ---------------------------------------------------------------------------
# Assemblage en Composed (une direction) et exports
# ---------------------------------------------------------------------------
def to_composed(name: str, frames1x: list[np.ndarray], anchors1x: list[tuple[int, int]], durations: list[int],
                scale: int, hit: int | None = None, ret: int | None = None) -> Composed:
    imgs = [upscale(f, scale) for f in frames1x]
    ancs = [(ax * scale + scale // 2, ay * scale + scale // 2) for ax, ay in anchors1x]
    need_w = need_h = 8
    for img, (ax, ay) in zip(imgs, ancs):
        ys, xs = np.nonzero(img[:, :, 3])
        if len(xs) == 0:
            continue
        need_w = max(need_w, 2 * max(ax - int(xs.min()) + 1, int(xs.max()) + 2 - ax))
        need_h = max(need_h, 2 * max(ay - int(ys.min()) + 1 - 4, int(ys.max()) + 2 - ay + 4))
    fw, fh = -(-need_w // 8) * 8, -(-need_h // 8) * 8
    comp = Composed(name, fw, fh, list(durations), hit=hit, ret=ret)
    cells, anchors = [], []
    for img, (ax, ay) in zip(imgs, ancs):
        cx, cy = fw // 2, fh // 2 + 4
        anim = np.zeros((fh, fw, 4), np.uint8)
        offs = np.zeros((fh, fw, 4), np.uint8)
        shad = np.zeros((fh, fw, 4), np.uint8)
        paste(anim, img, cx - ax, cy - ay)
        offs[cy, cx] = (0, 255, 0, 255)
        shad[cy, cx] = (255, 255, 255, 255)
        cells.append((anim, offs, shad))
        anchors.append((cx, cy))
    comp.cells.append(cells)
    comp.anchors.append(anchors)
    return comp


def build_all(scale: int) -> dict[str, Composed]:
    comps = {}
    for size in SIZES:
        # transformation : ancre = sol
        frames = [transform_frame(size, step) for step, _ in TRANSFORM_PLAN]
        anchors = [(f.shape[1] // 2, f.shape[0] - 4) for f in frames]
        durs = [d for _, d in TRANSFORM_PLAN]
        hit = next(k for k, (s, _) in enumerate(TRANSFORM_PLAN) if s == "flash0")
        ret = next(k for k, (s, _) in enumerate(TRANSFORM_PLAN) if s == "burst0")
        comps[f"Transformation-{size}"] = to_composed(f"Transformation-{size}", frames, anchors, durs, scale, hit, ret)
        # apparition puis boucle des nuages : ancre = centre de l'anneau
        frames = [cloud_intro_frame(size, k) for k in range(len(CLOUD_INTRO))]
        anchors = [(f.shape[1] // 2, f.shape[0] // 2) for f in frames]
        comps[f"NuagesApparition-{size}"] = to_composed(f"NuagesApparition-{size}", frames, anchors, [d for _, _, d in CLOUD_INTRO], scale)
        frames = [cloud_frame(size, k, CLOUD_FRAMES) for k in range(CLOUD_FRAMES)]
        anchors = [(f.shape[1] // 2, f.shape[0] // 2) for f in frames]
        comps[f"Nuages-{size}"] = to_composed(f"Nuages-{size}", frames, anchors, [CLOUD_TICKS] * CLOUD_FRAMES, scale)
        # aura : ancre = centre du corps
        frames = [aura_frame(size, k) for k in range(AURA_FRAMES)]
        anchors = [(f.shape[1] // 2, f.shape[0] // 2) for f in frames]
        comps[f"Aura-{size}"] = to_composed(f"Aura-{size}", frames, anchors, [AURA_TICKS] * AURA_FRAMES, scale)
    return comps


def write_animdata(comps: dict[str, Composed], path: Path) -> None:
    lines = ['<?xml version="1.0" ?>', "<AnimData>", "\t<ShadowSize>0</ShadowSize>", "\t<Anims>"]
    for k, (name, c) in enumerate(comps.items()):
        lines += ["\t\t<Anim>", f"\t\t\t<Name>{name}</Name>", f"\t\t\t<Index>{13 + k}</Index>",
                  f"\t\t\t<FrameWidth>{c.fw}</FrameWidth>", f"\t\t\t<FrameHeight>{c.fh}</FrameHeight>"]
        for tag, value in (("HitFrame", c.hit), ("ReturnFrame", c.ret)):
            if value is not None:
                lines.append(f"\t\t\t<{tag}>{value}</{tag}>")
        lines.append("\t\t\t<Durations>")
        lines += [f"\t\t\t\t<Duration>{d}</Duration>" for d in c.durations]
        lines += ["\t\t\t</Durations>", "\t\t</Anim>"]
    lines += ["\t</Anims>", "</AnimData>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def checker(size: tuple[int, int], zoom: int) -> Image.Image:
    a = np.zeros((size[1], size[0], 4), np.uint8)
    yy, xx = np.indices((size[1], size[0]))
    dark = ((xx // (8 * zoom) + yy // (8 * zoom)) % 2) == 0
    a[dark] = (58, 58, 82, 255)
    a[~dark] = (70, 70, 96, 255)
    return Image.fromarray(a, "RGBA")


def contact_sheet(comps: dict[str, Composed], path: Path) -> None:
    zoom = 1
    blocks = []
    for name, c in comps.items():
        n = len(c.durations)
        img = Image.new("RGBA", (n * (c.fw * zoom + 2) + 8, c.fh * zoom + 2 + 26), (26, 26, 46, 255))
        d = ImageDraw.Draw(img)
        extra = "".join(f" · {k} {v}" for k, v in (("Hit", c.hit), ("Return", c.ret)) if v is not None)
        d.text((4, 4), f"{name} — case {c.fw} × {c.fh}, {n} images, durées {c.durations}{extra}", fill=(230, 230, 230, 255), font=font(12))
        for i in range(n):
            cell = Image.fromarray(c.cells[0][i][0], "RGBA")
            bg = checker((c.fw * zoom, c.fh * zoom), zoom)
            bg.alpha_composite(cell.resize((c.fw * zoom, c.fh * zoom), Image.NEAREST))
            # ancre
            ax, ay = c.anchors[0][i]
            dd = ImageDraw.Draw(bg)
            dd.line([(ax * zoom - 3, ay * zoom), (ax * zoom + 3, ay * zoom)], fill=(0, 255, 0, 255))
            dd.line([(ax * zoom, ay * zoom - 3), (ax * zoom, ay * zoom + 3)], fill=(0, 255, 0, 255))
            img.alpha_composite(bg, (4 + i * (c.fw * zoom + 2), 26))
        blocks.append(img)
    W = max(b.width for b in blocks)
    H = sum(b.height + 6 for b in blocks) + 64
    out = Image.new("RGBA", (W + 16, H), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), "VFX DYNAMAX — EFFETS SEULS, SANS PERSONNAGE (× 3)", fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 36), "Transformation (ancre = sol), Nuages (ancre = centre de l'anneau), Aura (ancre = centre du corps) · tailles M et L · croix verte = ancre",
           fill=(170, 170, 200, 255), font=font(12))
    y = 64
    for b in blocks:
        out.alpha_composite(b, (8, y))
        y += b.height + 6
    out.save(path, optimize=True)


def gif(comps: dict[str, Composed], names: list[str], path: Path, zoom: int = 1, span: int | None = None,
        background: str = "damier", sprite: tuple[np.ndarray, tuple[int, int], int] | None = None) -> None:
    """Lecture des effets côte à côte. `sprite` = (image RGBA, ancre, image à partir de laquelle l'afficher) pour la
    démonstration sur le parquet ; sinon fond damier, effets seuls."""
    cw = max(comps[n].fw for n in names) * zoom + 8
    ch = max(comps[n].fh for n in names) * zoom + 8
    span = span or max(sum(comps[n].durations) for n in names)
    tick_frames = {}
    for n in names:
        c = comps[n]
        seq, t = [], 0
        while t < span:
            for i, d in enumerate(c.durations):
                seq.append((t, i))
                t += d
        tick_frames[n] = seq
    events = sorted({t for seq in tick_frames.values() for t, _ in seq if t < span} | {0})
    if background == "parquet":
        bg = parquet_background((len(names) * cw, ch), zoom)
    else:
        bg = checker((len(names) * cw, ch), zoom)
    frames_out, durations_out = [], []
    for k, t in enumerate(events):
        nxt = events[k + 1] if k + 1 < len(events) else span
        img = bg.copy()
        for col, n in enumerate(names):
            c = comps[n]
            i = max(i for tt, i in tick_frames[n] if tt <= t)
            ax, ay = c.anchors[0][i]
            cx = col * cw + cw // 2
            cy = ch - 12 if n.startswith("Transformation") else ch // 2
            if sprite is not None and n.startswith("Transformation") and i >= sprite[2]:
                simg, (sax, say), _ = sprite
                img.alpha_composite(Image.fromarray(simg, "RGBA").resize((simg.shape[1] * zoom, simg.shape[0] * zoom), Image.NEAREST),
                                    (cx - sax * zoom, cy - say * zoom))
            cell = Image.fromarray(c.cells[0][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
            img.alpha_composite(cell, (cx - ax * zoom, cy - ay * zoom))
        frames_out.append(img.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations_out.append(int(round((nxt - t) * 1000 / 60)))
    frames_out[0].save(path, save_all=True, append_images=frames_out[1:], duration=durations_out, loop=0, optimize=True)


def demo_gif(comps: dict[str, Composed], path: Path, zoom: int = 1) -> None:
    """Démonstration : petit Hariyama, transformation L, apparition des nuages, puis Hariyama Dynamax (aura intégrée)
    sous la boucle des nuages — exactement la séquence à jouer en jeu."""
    src = ROOT / "source" / "personnages" / "reference" / "0297"
    big = ROOT / "personnages" / "dynamax" / "0297_hariyama"
    if not (src / "Idle-Anim.png").is_file() or not (big / "kit.json").is_file():
        return
    kit = json.loads((big / "kit.json").read_text(encoding="utf-8"))
    if "vfx" not in kit.get("dynamax", {}):
        return
    small = np.array(Image.open(src / "Idle-Anim.png").convert("RGBA"))[0:56, 0:40]
    sshad = np.array(Image.open(src / "Idle-Shadow.png").convert("RGBA"))[0:56, 0:40]
    w = np.argwhere((sshad[:, :, 3] > 0) & np.all(sshad[:, :, :3] == 255, axis=2))[0]
    small_anchor = (int(w[1]), int(w[0]))
    fw, fh = kit["animations"]["Idle"]["case"]
    giants = [np.array(Image.open(big / "Idle-Anim.png").convert("RGBA"))[0:fh, i * fw:(i + 1) * fw]
              for i in range(kit["animations"]["Idle"]["images"])]
    gdurs = kit["animations"]["Idle"]["durees"]
    gshad = np.array(Image.open(big / "Idle-Shadow.png").convert("RGBA"))[0:fh, 0:fw]
    w = np.argwhere((gshad[:, :, 3] > 0) & np.all(gshad[:, :, :3] == 255, axis=2))[0]
    giant_anchor = (int(w[1]), int(w[0]))
    size = kit["dynamax"]["vfx"]["taille"]
    cloud_dy = kit["dynamax"]["vfx"]["ancre_nuages_decalage"][1]
    tr, intro, loop = comps[f"Transformation-{size}"], comps[f"NuagesApparition-{size}"], comps[f"Nuages-{size}"]

    def timeline(c: Composed, start: int) -> list[tuple[int, int]]:
        seq, t = [], start
        for i, d in enumerate(c.durations):
            seq.append((t, i)); t += d
        return seq

    tr_seq = timeline(tr, 0)
    t_ret = tr_seq[tr.ret][0]
    intro_seq = timeline(intro, t_ret)
    t_loop = intro_seq[-1][0] + intro.durations[-1]
    t_end = tr_seq[-1][0] + tr.durations[-1]
    total = t_loop + 2 * sum(loop.durations)
    W, H = max(tr.fw, fw + 40) * zoom + 16, (tr.fh // 2 + 40) * zoom + 16
    bg = parquet_background((W, H), zoom)
    cx, cy = W // 2, H - 14 * zoom
    events = sorted({t for t, _ in tr_seq} | {t for t, _ in intro_seq} | set(range(t_loop, total, CLOUD_TICKS)) | {20, 40})
    frames, durs = [], []

    def blit(img, arr, ax, ay, dx=0, dy=0):
        im = Image.fromarray(arr, "RGBA")
        if zoom != 1:
            im = im.resize((arr.shape[1] * zoom, arr.shape[0] * zoom), Image.NEAREST)
        img.alpha_composite(im, (cx - ax * zoom + dx * zoom, cy - ay * zoom + dy * zoom))

    gt = 0
    for k, e in enumerate(events):
        nxt = events[k + 1] if k + 1 < len(events) else total
        img = bg.copy()
        i = max((i for tt, i in tr_seq if tt <= e), default=None) if e < t_end else None
        if i is not None and i < 4:
            blit(img, small, *small_anchor)
        if i is None or i >= tr.hit:
            gi = 0
            acc = 0
            for gi, d in enumerate(gdurs):
                acc += d
                if (e - t_ret) % sum(gdurs) < acc:
                    break
            blit(img, giants[gi], *giant_anchor)
        if i is not None:
            blit(img, tr.cells[0][i][0], *tr.anchors[0][i])
        if t_ret <= e < t_loop:
            j = max(j for tt, j in intro_seq if tt <= e)
            blit(img, intro.cells[0][j][0], *intro.anchors[0][j], 0, cloud_dy)
        elif e >= t_loop:
            j = ((e - t_loop) // CLOUD_TICKS) % CLOUD_FRAMES
            blit(img, loop.cells[0][j][0], *loop.anchors[0][j], 0, cloud_dy)
        frames.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durs.append(int(round((nxt - e) * 1000 / 60)))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


def pack_sizes() -> dict[str, list[str]]:
    """Taille de VFX retenue par chaque pack Dynamax du dépôt (lue dans leur kit.json)."""
    sizes: dict[str, list[str]] = {"M": [], "L": []}
    for kit_path in sorted((ROOT / "personnages" / "dynamax").glob("*_*/kit.json")):
        kit = json.loads(kit_path.read_text(encoding="utf-8"))
        vfx = kit.get("dynamax", {}).get("vfx")
        if vfx:
            sizes.setdefault(vfx["taille"], []).append(kit["pokemon"]["nom"])
    return sizes


def write_readme(comps: dict[str, Composed], colours: int, path: Path, scale: int) -> None:
    rows = "\n".join(f"| {n} | {c.fw} × {c.fh} | {len(c.durations)} | {sum(c.durations)} ticks | "
                     f"{'sol' if n.startswith('Transformation') else 'centre de l’anneau' if n.startswith('Nuages') else 'centre du corps'} |"
                     f" {'oui' if n.startswith('Nuages-') or n.startswith('Aura') else 'non'} |"
                     for n, c in comps.items())
    sizes = pack_sizes()
    who = {k: (", ".join(v) if v else "—") for k, v in sizes.items()}
    text = f"""# VFX Dynamax — effets seuls, à superposer sur n'importe quel sprite

![Aperçu](apercu.png)

Effets visuels de la Dynamax **sans personnage ni fond**, dessinés en pixel art à l'échelle 1 et agrandis × {scale}
comme les sprites Dynamax du dépôt. Deux tailles : **M** (corps ≤ 24 px de large à l'échelle 1 : {who['M']})
et **L** (au-delà : {who['L']}). L'entrée `dynamax.vfx` du `kit.json` de chaque pack Dynamax donne la taille et le
décalage à appliquer ; pour un autre sprite, mesurer la largeur du corps au repos.

| Effet | Case | Images | Durée | Ancre | Boucle |
| --- | --- | --- | --- | --- | --- |
{rows}

## Séquence en jeu

1. Le Pokémon (sprite normal) est à l'arrêt. Lancer **Transformation** avec l'ancre sur son sol (pixel blanc de
   sa feuille Shadow), dessinée par-dessus le sprite. Images 1–4 : un rayon fin descend du ciel et frappe le sommet
   du Pokémon (hauteur calibrée pour un corps de taille M ou L). Images 5–10 : la **colonne d'énergie opaque**
   s'abat (bord clair, bandes rouges où coulent des étincelles, cœur cramoisi), enroulée d'**éclairs épais et
   opaques** cramoisi bordé de rose qui tournent en descendant ; **masquer le sprite normal à l'image 5**.
2. Image 11 (`HitFrame` = 10) : **flash** — la colonne devient blanche, grand éclat en étoile : **afficher le sprite
   Dynamax** (× {scale}) à cet instant. Images 12–13 : la colonne se dissout en lames de lumière qui montent.
3. Images 14–15 (`ReturnFrame` = 13) : onde de choc au sol, étincelles, volutes qui montent. Lancer à cet instant
   **NuagesApparition** (5 images, 24 ticks : 1, 2 puis 3 nuages qui tournent déjà) avec l'ancre au centre de
   l'anneau : décalage `ancre_nuages_decalage` du `kit.json` (2 px au-dessus du sommet du sprite Dynamax au repos,
   à l'échelle). Enchaîner la boucle **Nuages** (12 images, 48 ticks, un tiers de tour par boucle : la boucle est
   invisible, et la dernière image de l'apparition précède l'image 1 de la boucle). L'anneau est aplati : la moitié
   arrière passe derrière la tête si le moteur trie par profondeur ; sinon le dessiner par-dessus, il reste lisible.
4. **Aura** : les sprites Dynamax du dépôt ont déjà l'aura animée dans leurs feuilles. Cet effet générique (ellipse
   d'énergie, 4 images) sert à donner l'aura à un sprite qui ne l'a pas (ancre au centre du corps).

Palette des effets : {colours} couleurs — sombre (20, 8, 16), cramoisi (138, 12, 48), rouge (232, 40, 72), claire
(255, 144, 128), blanc (255, 236, 232) ; tout est opaque (aucune transparence partielle). Feuilles à une ligne (un
VFX n'a pas d'orientation), `AnimData.xml` façon SpriteCollab (index 13+),
`*-Offsets.png` (centre vert = ancre) et `*-Shadow.png` (pixel blanc = ancre) pour les lecteurs du dépôt,
`dynamax_vfx.aseprite` (une étiquette par effet), `apercu.png`, `apercu_effets.gif` (effets seuls sur damier),
`apercu_demonstration.gif` (Hariyama : petit sprite, transformation, sprite Dynamax, apparition puis boucle des nuages).

Design : brouillons du générateur d'images `source/personnages/reference/dynamax/concept_*.png` (volutes à cœur
clair, colonne à cœur sombre enroulée d'éclairs, flash en étoile, formation des nuages) ; tout est redessiné à la
main sur la grille dans `source/personnages/dynamax_fx.py` et `build_dynamax_vfx.py`. Reconstruire :
`python3 source/personnages/build_dynamax_vfx.py`.
"""
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> None:
    scale = SCALE
    it = iter(argv)
    for arg in it:
        if arg == "--echelle":
            scale = int(next(it))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    comps = build_all(scale)
    for name, c in comps.items():
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            save_png(sheet(c, which), OUT / f"{name}-{kind}.png")
    write_animdata(comps, OUT / "AnimData.xml")
    ase = write_aseprite(comps, OUT / "dynamax_vfx.aseprite", list(comps))
    contact_sheet(comps, OUT / "apercu.png")
    gif(comps, ["Transformation-M", "Transformation-L", "NuagesApparition-M", "Nuages-M", "NuagesApparition-L", "Nuages-L", "Aura-M", "Aura-L"],
        OUT / "apercu_effets.gif")
    demo_gif(comps, OUT / "apercu_demonstration.gif")
    used = set()
    for c in comps.values():
        for cell in c.cells[0]:
            a = cell[0]
            used |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
    write_readme(comps, len(used), OUT / "README.md", scale)
    kit = {"vfx": {n: {"case": [c.fw, c.fh], "images": len(c.durations), "durees": c.durations, "hit": c.hit, "return": c.ret,
                       "ancre": "sol" if n.startswith("Transformation") else "centre de l'anneau" if n.startswith("Nuages") else "centre du corps",
                       "taille": n.split("-")[1]} for n, c in comps.items()},
           "echelle": scale, "palette": sorted(used), "tailles": SIZES,
           "sequence": ["Transformation à l'ancre du sprite (masquer le sprite normal à l'image 5, afficher le sprite Dynamax à HitFrame)",
                        "NuagesApparition à ReturnFrame, ancre = ancre du sprite + ancre_nuages_decalage (kit.json de chaque pack)",
                        "Nuages en boucle au même endroit",
                        "Aura : seulement pour un sprite sans aura intégrée"],
           "aseprite": ase}
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VFX : {len(comps)} effets, {sum(len(c.durations) for c in comps.values())} images, {len(used)} couleurs → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
