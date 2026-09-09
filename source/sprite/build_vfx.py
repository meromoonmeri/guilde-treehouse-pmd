#!/usr/bin/env python3
"""VFX de transformation Dynamax, image par image → sprite/vfx/ (effet seul : aucun personnage, aucun fond).

Douze images dessinées une à une à l'échelle 1 (`frame_01` … `frame_12`, décrites dans FRAMES) puis agrandies × 3
comme les sprites de `sprite/`. Deux gabarits : **M** (corps < 24 px de large ou < 20 px de haut à l'échelle 1) et **L** (au-delà).

  1  rayon fin qui descend du ciel (traînée haute)                 7  colonne pleine, second éclair, étincelles au sol
  2  le rayon touche le sol : impact, premières étincelles         8  la colonne s'élargit, éclairs au plus épais
  3  colonne étroite qui s'élève, premier éclair                   9  FLASH : colonne blanche, éclat en étoile (HitFrame)
  4  colonne large, deux éclairs en hélice qui s'abattent         10  la colonne se dissout en lames de lumière qui montent
  5  éclairs qui tournent (¼ de tour), disque d'énergie au sol    11  onde de choc au sol, dernières lames
  6  éclairs qui tournent (½ tour), étincelles projetées          12  brumes rouges qui montent (avant les nuages du sprite)

Ancre = sol du Pokémon (pixel blanc de sa feuille Shadow). Le jeu masque le sprite normal à l'image 3 (la colonne
devient opaque) et affiche le sprite Dynamax de `sprite/<dex>_<slug>/` à l'image 9 (HitFrame) : ce sprite porte
déjà l'aura et les nuages, le VFX n'a donc rien à faire après l'image 12.

Sorties : `Transformation-M-Anim.png`, `Transformation-L-Anim.png` (une ligne, une colonne par image) avec leurs
`-Offsets.png` / `-Shadow.png` (ancre), `AnimData.xml` (index 13 et 14, HitFrame 8, ReturnFrame 11), `apercu.png`
et `apercu.gif` sur fond transparent, `kit.json`, `README.md`.

Usage : python3 source/sprite/build_vfx.py [--echelle N]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dynamax_fx as FX  # noqa: E402
from build_dynamax import paste, save_png, upscale  # noqa: E402

OUT = ROOT / "sprite" / "vfx"
SCALE = 3
PALETTE = [FX.FX_DARK, FX.FX_CRIMSON, FX.FX_RED, FX.FX_LIGHT, FX.FX_WHITE]

# gabarits : largeur de colonne et hauteur totale (px, échelle 1)
SIZES = {"M": {"colonne": 22, "hauteur": 66, "geant": 24}, "L": {"colonne": 34, "hauteur": 84, "geant": 30}}
# (nom, durée en ticks de 1/60 s) — 12 images, 60 ticks = 1 s
FRAMES = [("rayon", 5), ("impact", 4), ("colonne_etroite", 4), ("colonne", 5), ("rotation_1", 5), ("rotation_2", 5),
          ("colonne_pleine", 5), ("colonne_large", 4), ("flash", 4), ("lames", 5), ("onde", 6), ("brumes", 8)]
HIT = 8            # image 9 : flash → afficher le sprite Dynamax
RET = 11           # image 12 : le VFX rend la main (le sprite porte déjà nuages et aura)


# ---------------------------------------------------------------------------
# Pièces
# ---------------------------------------------------------------------------
def rect(canvas: np.ndarray, x0: int, y0: int, x1: int, y1: int, colour) -> None:
    H, W = canvas.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x0 < x1 and y0 < y1:
        canvas[y0:y1, x0:x1] = (*colour, 255)


def sparks(canvas: np.ndarray, cx: int, cy: int, n: int, radius: int, seed: int, colours=(FX.FX_WHITE, FX.FX_LIGHT), size: int = 2) -> None:
    """Étincelles réparties autour de (cx, cy), déterministes (seed) : carrés de `size` px."""
    for k in range(n):
        ang = (k / n) * 2 * math.pi + seed * 0.7
        r = radius * (0.6 + 0.4 * ((k * 7 + seed) % 3) / 2)
        x = int(round(cx + r * math.cos(ang)))
        y = int(round(cy - abs(r * 0.55 * math.sin(ang))))
        rect(canvas, x, y, x + size, y + size, colours[k % len(colours)])


def helix_bolts(canvas: np.ndarray, cx: int, top: int, bottom: int, rx: int, phase: float, thick: int, n_bolts: int = 2,
                back_only: bool = False, front_only: bool = False) -> None:
    """`n_bolts` éclairs épais en zigzag enroulés en hélice autour de la colonne (un tour sur la hauteur)."""
    for b in range(n_bolts):
        pts, front = FX.spiral_bolt(cx, top, bottom, rx, 3, 1.0, phase + b * 2 * math.pi / n_bolts, 9, 6)
        if back_only:
            seg = [pt for pt, f in zip(pts, front) if not f]
        elif front_only:
            seg = [pt for pt, f in zip(pts, front) if f]
        else:
            seg = pts
        if len(seg) >= 2:
            FX.bolt(seg, thick, canvas)


def draw_column(canvas: np.ndarray, cx: int, ground: int, w: int, phase: int, rx_bolt: int, bolt_phase: float, thick: int,
                n_bolts: int = 2, white: bool = False) -> None:
    """Colonne opaque du haut du canevas au sol, éclairs arrière derrière / avant devant, disque d'énergie au pied."""
    helix_bolts(canvas, cx, 2, ground - 3, rx_bolt, bolt_phase, max(2, thick - 1), n_bolts, back_only=True)
    paste(canvas, FX.column(w, ground + 1, phase, white), cx - w // 2, 0)
    FX.filled_ellipse(canvas, cx, ground, w // 2 + 3 + (phase % 2), 3, FX.FX_RED if not white else FX.FX_LIGHT)
    FX.filled_ellipse(canvas, cx, ground, w // 2 - 1, 2, FX.FX_LIGHT if not white else FX.FX_WHITE)
    helix_bolts(canvas, cx, 2, ground - 3, rx_bolt, bolt_phase, thick, n_bolts, front_only=True)


# ---------------------------------------------------------------------------
# Les douze images
# ---------------------------------------------------------------------------
def frame(size: str, k: int) -> np.ndarray:
    p = SIZES[size]
    col_w, H = p["colonne"], p["hauteur"] + 6
    W = col_w + 44
    canvas = np.zeros((H, W, 4), np.uint8)
    cx, ground = W // 2, H - 4
    small_top = ground - p["geant"] // SCALE                  # sommet du Pokémon normal (le rayon vise sa tête)
    name = FRAMES[k][0]

    if name == "rayon":                                       # 1 · rayon fin, la pointe arrive au-dessus de la tête
        paste(canvas, FX.beam(3, small_top - 2, 0), cx - 1, 0)
        rect(canvas, cx, small_top - 6, cx + 1, small_top - 1, FX.FX_WHITE)
    elif name == "impact":                                    # 2 · le rayon touche : impact clair, étincelles
        paste(canvas, FX.beam(5, ground - 1, 1), cx - 2, 0)
        FX.filled_ellipse(canvas, cx, ground, 7, 2, FX.FX_LIGHT)
        FX.filled_ellipse(canvas, cx, ground, 4, 1, FX.FX_WHITE)
        FX.flash_burst(cx, small_top, 9, 8, 1, canvas, 1)
        sparks(canvas, cx, ground - 1, 6, 10, 1)
    elif name == "colonne_etroite":                           # 3 · la colonne s'élève, un premier éclair
        w = col_w * 2 // 3
        helix_bolts(canvas, cx, 2, ground - 3, w // 2 + 4, 0.0, 2, 1, back_only=True)
        paste(canvas, FX.column(w, ground + 1, 0), cx - w // 2, 0)
        FX.filled_ellipse(canvas, cx, ground, w // 2 + 3, 3, FX.FX_RED)
        FX.filled_ellipse(canvas, cx, ground, w // 2 - 1, 2, FX.FX_LIGHT)
        helix_bolts(canvas, cx, 2, ground - 3, w // 2 + 4, 0.0, 3, 1, front_only=True)
        sparks(canvas, cx, ground - 2, 4, w // 2 + 8, 2)
    elif name == "colonne":                                   # 4 · colonne large, deux éclairs qui s'abattent
        draw_column(canvas, cx, ground, col_w, 1, col_w // 2 + 5, 0.8, 3)
        sparks(canvas, cx, ground - 2, 5, col_w // 2 + 9, 3)
    elif name == "rotation_1":                                # 5 · les éclairs tournent d'un quart de tour
        draw_column(canvas, cx, ground, col_w, 2, col_w // 2 + 5, 0.8 + math.pi / 2, 3)
        sparks(canvas, cx, ground - 2, 6, col_w // 2 + 10, 4)
    elif name == "rotation_2":                                # 6 · un demi-tour, étincelles projetées plus haut
        draw_column(canvas, cx, ground, col_w, 3, col_w // 2 + 6, 0.8 + math.pi, 3)
        sparks(canvas, cx, ground - 6, 7, col_w // 2 + 12, 5)
    elif name == "colonne_pleine":                            # 7 · trois quarts de tour, troisième éclair court
        draw_column(canvas, cx, ground, col_w, 4, col_w // 2 + 6, 0.8 + 3 * math.pi / 2, 3)
        pts, front = FX.spiral_bolt(cx, 2, ground // 2, col_w // 2 + 3, 2, 0.5, 2.4, 5, 5)
        seg = [pt for pt, f in zip(pts, front) if f]
        if len(seg) >= 2:
            FX.bolt(seg, 2, canvas)
        sparks(canvas, cx, ground - 4, 6, col_w // 2 + 12, 6)
    elif name == "colonne_large":                             # 8 · la colonne s'élargit, éclairs au plus épais
        draw_column(canvas, cx, ground, col_w + 4, 5, col_w // 2 + 8, 0.8 + 2 * math.pi, 4)
        sparks(canvas, cx, ground - 8, 8, col_w // 2 + 14, 7)
    elif name == "flash":                                     # 9 · FLASH (HitFrame) : colonne blanche, éclat en étoile
        mid = ground - p["geant"] // 2
        w = col_w + 6
        paste(canvas, FX.column(w, ground + 1, 0, white=True), cx - w // 2, 0)
        FX.filled_ellipse(canvas, cx, ground, w // 2 + 4, 3, FX.FX_WHITE)
        FX.flash_burst(cx, mid, W // 2 - 1, 16, 0, canvas, 3)
        FX.filled_ellipse(canvas, cx, mid, w // 2 + 3, 10, FX.FX_WHITE)
    elif name == "lames":                                     # 10 · la colonne se dissout en lames qui montent
        mid = ground - p["geant"] // 2
        for j, x in enumerate(range(cx - col_w // 2 - 6, cx + col_w // 2 + 7, 4)):
            bottom = ground - 4 - 8 * (j % 3)
            top = 2 + 5 * ((j + 1) % 2)
            rect(canvas, x, top, x + 3, bottom, FX.FX_WHITE if j % 2 else FX.FX_LIGHT)
        FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 5, 3, 2, FX.FX_LIGHT)
        FX.flash_burst(cx, mid, W // 2 - 4, 12, 1, canvas, 2)
    elif name == "onde":                                      # 11 · onde de choc au sol, dernières lames
        FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 12, 5, 3, FX.FX_LIGHT)
        FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 5, 3, 2, FX.FX_RED)
        for j, x in enumerate(range(cx - col_w // 2 - 8, cx + col_w // 2 + 9, 6)):
            if j % 2:
                rect(canvas, x, 2 + 4 * (j % 3), x + 2, ground // 2 - 6 * (j % 3), FX.FX_LIGHT)
        sparks(canvas, cx, ground - 12, 10, col_w // 2 + 14, 8, (FX.FX_RED, FX.FX_WHITE))
    else:                                                     # 12 · brumes rouges qui montent vers la tête du géant
        FX.ellipse_ring(canvas, cx, ground, col_w // 2 + 18, 6, 2, FX.FX_RED)
        top = ground - p["geant"] - 2
        for j in range(7):
            ang = j * 0.9
            x = int(round(cx + (col_w // 2 + 4) * math.cos(ang)))
            y = int(round(top + 6 + 4 * math.sin(ang) + 3 * (j % 3)))
            rect(canvas, x - 2, y - 1, x + 3, y + 2, FX.FX_RED)
            rect(canvas, x - 1, y, x + 2, y + 1, FX.FX_LIGHT)
        sparks(canvas, cx, top + 14, 6, col_w // 2 + 10, 9, (FX.FX_RED, FX.FX_RED, FX.FX_WHITE))
    return canvas


# ---------------------------------------------------------------------------
# Feuilles (une ligne), ancre au sol, cases par pas de 8
# ---------------------------------------------------------------------------
def compose(size: str, scale: int) -> dict:
    frames1x = [frame(size, k) for k in range(len(FRAMES))]
    imgs = [upscale(f, scale) for f in frames1x]
    ancs = [(f.shape[1] // 2 * scale + scale // 2, (f.shape[0] - 4) * scale + scale // 2) for f in frames1x]
    need_w = need_h = 8
    for img, (ax, ay) in zip(imgs, ancs):
        ys, xs = np.nonzero(img[:, :, 3])
        need_w = max(need_w, 2 * max(ax - int(xs.min()) + 1, int(xs.max()) + 2 - ax))
        need_h = max(need_h, 2 * max(ay - int(ys.min()) + 1 - 4, int(ys.max()) + 2 - ay + 4))
    fw, fh = -(-need_w // 8) * 8, -(-need_h // 8) * 8
    cx, cy = fw // 2, fh // 2 + 4
    anim = np.zeros((fh, fw * len(imgs), 4), np.uint8)
    offs = np.zeros_like(anim)
    shad = np.zeros_like(anim)
    for i, (img, (ax, ay)) in enumerate(zip(imgs, ancs)):
        paste(anim[:, i * fw:(i + 1) * fw], img, cx - ax, cy - ay)
        offs[cy, i * fw + cx] = (0, 255, 0, 255)
        shad[cy, i * fw + cx] = (255, 255, 255, 255)
    return {"fw": fw, "fh": fh, "anim": anim, "offs": offs, "shad": shad, "anchor": (cx, cy), "frames1x": frames1x}


def write_animdata(comps: dict[str, dict], path: Path) -> None:
    lines = ['<?xml version="1.0" ?>', "<AnimData>", "\t<ShadowSize>0</ShadowSize>", "\t<Anims>"]
    for k, (name, c) in enumerate(comps.items()):
        lines += ["\t\t<Anim>", f"\t\t\t<Name>{name}</Name>", f"\t\t\t<Index>{13 + k}</Index>",
                  f"\t\t\t<FrameWidth>{c['fw']}</FrameWidth>", f"\t\t\t<FrameHeight>{c['fh']}</FrameHeight>",
                  f"\t\t\t<HitFrame>{HIT}</HitFrame>", f"\t\t\t<ReturnFrame>{RET}</ReturnFrame>", "\t\t\t<Durations>"]
        lines += [f"\t\t\t\t<Duration>{d}</Duration>" for _, d in FRAMES]
        lines += ["\t\t\t</Durations>", "\t\t</Anim>"]
    lines += ["\t</Anims>", "</AnimData>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def label(text: str) -> np.ndarray:
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except OSError:
        f = ImageFont.load_default()
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    _, _, x1, y1 = probe.textbbox((3, 1), text, font=f)
    mask = Image.new("1", (x1 + 4, y1 + 3), 0)
    ImageDraw.Draw(mask).text((3, 1), text, font=f, fill=1)
    m = np.array(mask, bool)
    out = np.zeros((*m.shape, 4), np.uint8)
    halo = m.copy()
    halo[1:] |= m[:-1]; halo[:-1] |= m[1:]; halo[:, 1:] |= m[:, :-1]; halo[:, :-1] |= m[:, 1:]
    out[halo] = (*FX.FX_WHITE, 255)
    out[m] = (*FX.FX_DARK, 255)
    return out


def contact_sheet(comps: dict[str, dict], path: Path) -> None:
    blocks = []
    for name, c in comps.items():
        lab = label(f"{name} — case {c['fw']} × {c['fh']}, {len(FRAMES)} images, durées {[d for _, d in FRAMES]} · HitFrame {HIT} · ReturnFrame {RET}")
        n = len(FRAMES)
        strip = np.zeros((c["fh"] + 20, n * (c["fw"] + 2), 4), np.uint8)
        for i in range(n):
            strip[20:, i * (c["fw"] + 2):i * (c["fw"] + 2) + c["fw"]] = c["anim"][:, i * c["fw"]:(i + 1) * c["fw"]]
            paste(strip, label(f"{i + 1} {FRAMES[i][0]}"), i * (c["fw"] + 2) + 2, 0)
        blocks.append((lab, strip))
    W = max(max(l.shape[1], s.shape[1]) for l, s in blocks) + 8
    H = sum(l.shape[0] + s.shape[0] + 10 for l, s in blocks) + 8
    out = np.zeros((H, W, 4), np.uint8)
    y = 4
    for lab, strip in blocks:
        paste(out, lab, 4, y)
        y += lab.shape[0]
        paste(out, strip, 4, y)
        y += strip.shape[0] + 10
    save_png(out, path)


def gif_frame(arr: np.ndarray) -> Image.Image:
    idx = np.zeros(arr.shape[:2], np.uint8)
    opaque = arr[:, :, 3] > 0
    for k, col in enumerate(PALETTE, start=1):
        idx[opaque & np.all(arr[:, :, :3] == col, axis=2)] = k
    im = Image.fromarray(idx, "P")
    im.putpalette([0, 0, 0] + [v for c in PALETTE for v in c])
    return im


def gif(comps: dict[str, dict], path: Path) -> None:
    cw = max(c["fw"] for c in comps.values()) + 8
    ch = max(c["fh"] for c in comps.values()) + 8
    frames, durs = [], []
    for i, (_, d) in enumerate(FRAMES):
        img = np.zeros((ch, len(comps) * cw, 4), np.uint8)
        for col, c in enumerate(comps.values()):
            cell = c["anim"][:, i * c["fw"]:(i + 1) * c["fw"]]
            ax, ay = c["anchor"]
            paste(img, cell, col * cw + cw // 2 - ax, ch - 12 - ay)
        frames.append(gif_frame(img))
        durs.append(int(round(d * 1000 / 60)))
    frames.append(gif_frame(np.zeros((ch, len(comps) * cw, 4), np.uint8)))      # pause vide avant de reboucler
    durs.append(700)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, transparency=0, disposal=2)


def write_readme(comps: dict[str, dict], colours: int, path: Path, scale: int) -> None:
    rows = "\n".join(f"| {i + 1} | `{n}` | {d} | {desc} |" for i, ((n, d), desc) in enumerate(zip(FRAMES, [
        "rayon fin qui descend du ciel, pointe blanche au-dessus de la tête",
        "le rayon touche le sol : impact clair, éclat à hauteur de tête, premières étincelles",
        "la colonne s'élève (étroite), premier éclair épais — **masquer le sprite normal**",
        "colonne large, deux éclairs en hélice qui s'abattent",
        "les éclairs tournent d'un quart de tour, disque d'énergie au pied",
        "un demi-tour, étincelles projetées plus haut",
        "trois quarts de tour, troisième éclair court en haut",
        "la colonne s'élargit, éclairs au plus épais",
        "**FLASH** (`HitFrame`) : colonne blanche, éclat en étoile — **afficher le sprite Dynamax**",
        "la colonne se dissout en lames de lumière qui montent",
        "onde de choc au sol, dernières lames",
        "brumes rouges qui montent vers la tête (`ReturnFrame` : le VFX rend la main)",
    ])))
    cases = " · ".join(f"{n} : {c['fw']} × {c['fh']} px" for n, c in comps.items())
    text = f"""# VFX Transformation Dynamax — image par image, effet seul

![Les douze images](apercu.png)

Effet de transformation joué **par-dessus** n'importe quel sprite quand la Dynamax s'active : **aucun personnage,
aucun fond** — {len(FRAMES)} images dessinées une à une à l'échelle 1 et agrandies × {scale} comme les sprites de
`sprite/`. Deux gabarits : `Transformation-M` (corps < 24 px de large ou < 20 px de haut à l'échelle 1) et `Transformation-L`
(au-delà) ; `sprite/index.json` donne `petits_nuages` (= gabarit M) pour chaque espèce. Cases : {cases}.
Durée totale {sum(d for _, d in FRAMES)} ticks (1/60 s) ≈ {sum(d for _, d in FRAMES) / 60:.1f} s.

| # | Image | Ticks | Contenu |
| --- | --- | --- | --- |
{rows}

## Séquence en jeu

1. Le Pokémon (sprite SpriteCollab normal) est à l'arrêt. Lancer `Transformation-<gabarit>` avec l'**ancre sur son
   sol** (pixel blanc de sa feuille Shadow), dessinée par-dessus.
2. Image 3 : la colonne est opaque → **masquer le sprite normal**.
3. Image 9 (`HitFrame` = {HIT}) : le flash → **afficher le sprite Dynamax** de `sprite/<dex>_<slug>/`, même ancre.
   Il porte déjà l'aura rouge animée et les trois nuages qui tournent : rien d'autre à superposer.
4. Image 12 (`ReturnFrame` = {RET}) : le VFX se termine sur des brumes qui montent vers les nuages du sprite.

## Format

Palette : {colours} couleurs opaques — sombre (20, 8, 16), cramoisi (138, 12, 48), rouge (232, 40, 72), claire
(255, 144, 128), blanc (255, 236, 232) ; aucune transparence partielle, fond alpha 0. Feuilles à une ligne (un VFX
n'a pas d'orientation) ; `AnimData.xml` façon SpriteCollab (index 13 et 14, hors des index réservés) ;
`*-Offsets.png` (centre vert) et `*-Shadow.png` (pixel blanc) portent l'ancre pour les lecteurs SpriteCollab /
SkyTemple ; `apercu.png` (les douze images, étiquetées) et `apercu.gif` (lecture M et L côte à côte) sont sur fond
transparent. Reconstruire : `python3 source/sprite/build_vfx.py`.
"""
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> None:
    scale = SCALE
    it = iter(argv)
    for arg in it:
        if arg == "--echelle":
            scale = int(next(it))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in list(OUT.glob("*.png")) + list(OUT.glob("*.gif")):
        old.unlink()
    comps = {f"Transformation-{size}": compose(size, scale) for size in SIZES}
    used: set = set()
    for name, c in comps.items():
        save_png(c["anim"], OUT / f"{name}-Anim.png")
        save_png(c["offs"], OUT / f"{name}-Offsets.png")
        save_png(c["shad"], OUT / f"{name}-Shadow.png")
        used |= set(map(tuple, c["anim"][c["anim"][:, :, 3] > 0][:, :3].tolist()))
    write_animdata(comps, OUT / "AnimData.xml")
    contact_sheet(comps, OUT / "apercu.png")
    gif(comps, OUT / "apercu.gif")
    write_readme(comps, len(used), OUT / "README.md", scale)
    kit = {"contenu": "effet seul : aucun personnage, aucun fond",
           "echelle": scale, "palette": sorted(used), "images": [{"n": i + 1, "nom": n, "ticks": d} for i, (n, d) in enumerate(FRAMES)],
           "hit": HIT, "return": RET, "ancre": "sol du sprite (pixel blanc de Shadow)",
           "effets": {n: {"case": [c["fw"], c["fh"]], "images": len(FRAMES), "durees": [d for _, d in FRAMES], "gabarit": n.split("-")[1],
                          "pour": "corps < 24 px de large ou < 20 px de haut à l'échelle 1 (index.json : petits_nuages = true)" if n.endswith("M") else "corps plus grand (petits_nuages = false)"}
                      for n, c in comps.items()},
           "sequence": ["Transformation-<gabarit> à l'ancre du sprite normal", "image 3 : masquer le sprite normal",
                        "image 9 (HitFrame) : afficher le sprite Dynamax de sprite/<dex>_<slug>/ (aura + nuages intégrés)",
                        "image 12 (ReturnFrame) : fin du VFX"]}
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VFX : {len(comps)} feuilles × {len(FRAMES)} images, {len(used)} couleurs → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
