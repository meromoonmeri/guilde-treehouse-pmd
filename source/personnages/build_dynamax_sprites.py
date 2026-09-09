#!/usr/bin/env python3
"""Sprites Dynamax au format SpriteCollab, à partir des sprites complets de SpriteCollab.

Pour chaque Pokémon de POKEMON, **toutes** les animations du sprite d'origine sont reprises (mêmes noms, index,
durées, RushFrame / HitFrame / ReturnFrame, CopyOf, mêmes déplacements d'ancre) et transformées ainsi :

1. le dessin est agrandi × SCALE au plus proche voisin (aucun rééchantillonnage : chaque pixel devient un bloc),
   comme un Pokémon dynamaxé qui garde sa forme mais change d'échelle ;
2. une **aura rouge animée** entoure la silhouette : anneau plein d'un pixel (à l'échelle du dessin), anneau tramé
   dont le motif remonte d'un pixel par phase (quatre phases par cycle d'animation) et langues extérieures ;
3. les **nuages tournants** et la **transformation** ne sont pas dans le sprite : ce sont des VFX génériques sans
   personnage (`build_dynamax_vfx.py` → `personnages/dynamax/vfx/`), superposés en jeu ; `kit.json` donne la
   taille (M/L) et le décalage à appliquer (`--nuages-integres` dessine quand même l'anneau dans le sprite) ;
4. les repères (Offsets) et l'ancre (pixel blanc de Shadow) sont replacés à l'échelle, un seul pixel chacun ;
   le gabarit d'ombre de la référence est agrandi ; `ShadowSize` passe à 2 (grande ombre) ;
5. les cases sont agrandies par pas de 8 pour contenir aura et nuages, l'ancre au repos restant en
   (largeur / 2, hauteur / 2 + 4), et l'ancre suit les déplacements de la référence multipliés par SCALE.

Deux couleurs sont ajoutées à la palette d'origine (aura, aura claire) ; l'ombre des nuages reprend la couleur la
plus sombre du sprite. Les sprites d'origine comptant jusqu'à 15 couleurs, le résultat peut en compter 17 : il est
alors hors des critères d'importation stricts de SkyTemple / SpriteBot (15 couleurs), ce qui est de toute façon le
cas d'une forme non officielle. Rien d'autre n'est retouché : les pixels du Pokémon sont ceux de SpriteCollab,
agrandis.

Usage : python3 source/personnages/build_dynamax_sprites.py [slug ...] [--echelle N]
Sorties : personnages/dynamax/<numéro>_<slug>/ (feuilles, AnimData.xml, nuit/, Aseprite, aperçus, GIF, kit.json,
credits.txt, README.md). Vérification : verify_dynamax_sprites.py.
"""
from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
from rebuild_kit import night  # noqa: E402
from build_falinks_sprite import (  # noqa: E402  (pipeline commun aux sprites du kit)
    DIRECTIONS, Composed, font, parquet_background, sheet, write_aseprite,
)
import dynamax_fx as FX  # noqa: E402

REFS = ROOT / "source" / "personnages" / "reference"
OUT_ROOT = ROOT / "personnages" / "dynamax"
SCALE = 3                                   # facteur d'agrandissement (--echelle N) : un Dynamax fait trois fois sa taille
SHADOW_SIZE = 2                             # un Pokémon dynamaxé projette la grande ombre
PAD = 48                                    # marge de travail autour de la case d'origine (à l'échelle 1)

# Couleurs des effets : dynamax_fx (sombre, rouge, claire, blanc) ; le contour des nuages reprend la couleur la
# plus sombre du sprite.
AURA = FX.FX_RED
AURA_LIGHT = FX.FX_LIGHT

# numéro, slug, nom affiché, dossier source (format SpriteCollab), licence d'origine
POKEMON = [
    ("0186", "tarpaud", "Tarpaud (Politoed)", REFS / "0186"),
    ("0241", "ecremeuh", "Écrémeuh (Miltank)", REFS / "0241"),
    ("0282", "gardevoir", "Gardevoir", REFS / "0282"),
    ("0297", "hariyama", "Hariyama", REFS / "0297"),
    ("0424", "capidextre", "Capidextre (Ambipom)", REFS / "0424"),
    ("0443", "griknot", "Griknot (Gible)", REFS / "0443"),
    ("0674", "pandespiegle", "Pandespiègle (Pancham)", REFS / "0674"),
    ("0923", "patachiot", "Pâtachiot (Pawmi)", REFS / "0923"),
    ("0870", "falinks", "Falinks (escouade)", ROOT / "personnages" / "falinks"),
    ("0893", "zarude", "Zarude", ROOT / "personnages" / "zarude"),
]

LICENCES = {"Unspecified": "sprite original du jeu (CHUNSOFT), licence non précisée sur SpriteCollab : usage non commercial de fan uniquement",
            "PMDCollab_1": "PMDCollab_1 (usage libre avec crédit, dans le cadre des règles de PMDCollab)",
            "CC_BY-NC_4": "CC BY-NC 4.0"}


# ---------------------------------------------------------------------------
# Lecture d'un sprite SpriteCollab
# ---------------------------------------------------------------------------
@dataclass
class SrcAnim:
    name: str
    index: int | None                 # certains alias CopyOf de SpriteCollab n'ont pas d'<Index> : on le laisse absent
    copy_of: str | None = None
    fw: int = 0
    fh: int = 0
    durations: list[int] = field(default_factory=list)
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None
    anim: np.ndarray | None = None
    offs: np.ndarray | None = None
    shad: np.ndarray | None = None

    @property
    def dirs(self) -> int:
        return self.anim.shape[0] // self.fh

    def cell(self, sheet_: np.ndarray, d: int, i: int) -> np.ndarray:
        return sheet_[d * self.fh:(d + 1) * self.fh, i * self.fw:(i + 1) * self.fw]


def parse_animdata(path: Path) -> tuple[int, list[SrcAnim]]:
    root = ET.parse(path).getroot()
    anims = []
    for node in root.find("Anims").iter("Anim"):
        idx = node.find("Index")
        a = SrcAnim(node.find("Name").text, int(idx.text) if idx is not None else None)
        copy = node.find("CopyOf")
        if copy is not None:
            a.copy_of = copy.text
        else:
            a.fw, a.fh = int(node.find("FrameWidth").text), int(node.find("FrameHeight").text)
            a.durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
            for tag, key in (("RushFrame", "rush"), ("HitFrame", "hit"), ("ReturnFrame", "ret")):
                sub = node.find(tag)
                if sub is not None:
                    setattr(a, key, int(sub.text))
        anims.append(a)
    return int(root.find("ShadowSize").text), anims


def load_source(folder: Path) -> tuple[int, list[SrcAnim]]:
    shadow_size, anims = parse_animdata(folder / "AnimData.xml")
    for a in anims:
        if a.copy_of:
            continue
        a.anim = np.array(Image.open(folder / f"{a.name}-Anim.png").convert("RGBA"))
        a.offs = np.array(Image.open(folder / f"{a.name}-Offsets.png").convert("RGBA"))
        a.shad = np.array(Image.open(folder / f"{a.name}-Shadow.png").convert("RGBA"))
        assert a.anim.shape == a.offs.shape == a.shad.shape, a.name
        assert a.anim.shape[1] == a.fw * len(a.durations), a.name
    return shadow_size, anims


def save_png(img: Image.Image, path: Path) -> None:
    """PNG indexé (palette + tRNS) quand l'image compte ≤ 256 couleurs RGBA : mêmes pixels exactement, fichier deux
    fois plus petit que le RGBA ; sinon RGBA. Les lecteurs (Pillow, navigateurs, SkyTemple) relisent les deux."""
    a = np.array(img.convert("RGBA"))
    flat = a.reshape(-1, 4).astype(np.uint32)
    keys = (flat[:, 0] << 24) | (flat[:, 1] << 16) | (flat[:, 2] << 8) | flat[:, 3]
    uniq, inv = np.unique(keys, return_inverse=True)
    if len(uniq) > 256:
        img.save(path, optimize=True)
        return
    # la couleur transparente en premier, alpha 0 ⇒ tRNS court
    order = np.argsort((uniq & 255), kind="stable")
    rank = np.empty(len(uniq), np.int64)
    rank[order] = np.arange(len(uniq))
    idx = rank[inv].reshape(a.shape[:2]).astype(np.uint8)
    uniq = uniq[order]
    pal = Image.fromarray(idx, "P")
    pal.putpalette([int(v) for k in uniq for v in ((k >> 24) & 255, (k >> 16) & 255, (k >> 8) & 255)])
    alphas = bytes(int(k & 255) for k in uniq)
    pal.save(path, optimize=True, transparency=alphas)


def white_pixel(shad_cell: np.ndarray) -> tuple[int, int]:
    w = np.argwhere((shad_cell[:, :, 3] > 0) & np.all(shad_cell[:, :, :3] == 255, axis=2))
    assert len(w) == 1, "pixel blanc absent ou multiple"
    return int(w[0][1]), int(w[0][0])


# ---------------------------------------------------------------------------
# Effets (dessinés à l'échelle 1, agrandis avec le reste) : voir dynamax_fx.py
# ---------------------------------------------------------------------------
NARROW = 24                       # largeur du corps au repos (px) : au-delà, VFX de taille L (et grands nuages si intégrés)
BAKE_CLOUDS = False               # True (--nuages-integres) : dessiner l'anneau de nuages dans le sprite au lieu du VFX séparé
STRUCT = np.ones((3, 3), bool)


def dilate(mask: np.ndarray) -> np.ndarray:
    return binary_dilation(mask, STRUCT)


def darkest_colour(anims: list["SrcAnim"]) -> tuple[int, int, int]:
    walk = next(a for a in anims if a.name == "Walk")
    px = walk.anim[walk.anim[:, :, 3] > 0][:, :3].astype(int)
    lum = px @ np.array([299, 587, 114])
    return tuple(int(v) for v in px[int(lum.argmin())])


def paste(canvas: np.ndarray, img: np.ndarray, x: int, y: int) -> None:
    """Colle `img` (RGBA, alpha 0/255) en (x, y), pixels opaques seulement, avec découpe aux bords."""
    h, w = img.shape[:2]
    H, W = canvas.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    src = img[y0 - y:y1 - y, x0 - x:x1 - x]
    m = src[:, :, 3] > 0
    canvas[y0:y1, x0:x1][m] = src[m]


@dataclass
class Frame1x:
    """Une case composée à l'échelle 1, dans un canevas élargi de PAD ; ancre en (PAD + ax, PAD + ay)."""
    img: np.ndarray
    anchor: tuple[int, int]
    disp: tuple[int, int]
    marks: list[tuple[int, int, tuple[int, int, int]]]     # (x, y, rgb) relatifs à l'ancre
    template: list[tuple[int, int, tuple[int, int, int]]]  # gabarit d'ombre relatif à l'ancre (sans le blanc)


def source_marks(a: SrcAnim, d: int, i: int, ax: int, ay: int):
    offs = a.cell(a.offs, d, i)
    shad = a.cell(a.shad, d, i)
    marks = [(int(x) - ax, int(y) - ay, tuple(int(v) for v in offs[y, x, :3])) for y, x in np.argwhere(offs[:, :, 3] > 0)]
    template = [(int(x) - ax, int(y) - ay, tuple(int(v) for v in shad[y, x, :3]))
                for y, x in np.argwhere(shad[:, :, 3] > 0) if (int(x), int(y)) != (ax, ay)]
    return marks, template


def draw_clouds(canvas: np.ndarray, mask: np.ndarray, cx: int, orbit: tuple[int, int], clouds: list[np.ndarray],
                t: int, total: int, d: int, body_paste) -> None:
    """Anneau de nuages-cyclones au-dessus de la silhouette : moitié arrière derrière le corps, moitié avant devant,
    volute qui tourne (trois phases), traînée dans le sens du mouvement."""
    ys = np.nonzero(mask.any(axis=1))[0]
    top = int(ys.min()) if len(ys) else PAD
    rx, ry = orbit
    oy = top - ry - 1                                       # bas de l'ellipse juste au-dessus de la tête
    placements = []
    for ang, phase in FX.cloud_ring(t, total, d):
        c = clouds[phase]
        px = int(round(cx + rx * math.cos(ang))) - c.shape[1] // 2
        py = int(round(oy + ry * math.sin(ang))) - c.shape[0] // 2
        # traînée : derrière le nuage par rapport au sens de rotation (sens horaire vu de dessus)
        trail = FX.TRAIL_SMALL if c.shape[1] < 14 else FX.TRAIL
        tx = px - trail.shape[1] if math.sin(ang) > 0 else px + c.shape[1]
        ty = py + c.shape[0] // 2
        placements.append((math.sin(ang) > 0, c, px, py, trail, tx, ty))
    for front, c, px, py, trail, tx, ty in placements:
        if not front:
            paste(canvas, trail, tx, ty)
            paste(canvas, c, px, py)
    body_paste()
    for front, c, px, py, trail, tx, ty in placements:
        if front:
            paste(canvas, trail, tx, ty)
            paste(canvas, c, px, py)


def compose_frame(a: SrcAnim, d: int, i: int, orbit: tuple[int, int], clouds: list[np.ndarray], t: int, total: int) -> Frame1x:
    """Case Dynamax ordinaire : corps agrandi (plus tard), aura ondulante, anneau de nuages."""
    body = a.cell(a.anim, d, i)
    ax, ay = white_pixel(a.cell(a.shad, d, i))
    disp = (ax - a.fw // 2, ay - (a.fh // 2 + 4))
    canvas = np.zeros((a.fh + 2 * PAD, a.fw + 2 * PAD, 4), np.uint8)
    mask = np.zeros(canvas.shape[:2], bool)
    mask[PAD:PAD + a.fh, PAD:PAD + a.fw] = body[:, :, 3] > 0
    cx, cy = PAD + ax, PAD + ay
    phase = int(4 * t / total) % 4 if total else 0          # l'aura fait un cycle de flux par animation

    def body_paste():
        paste(canvas, FX.aura(mask, phase, dilate), 0, 0)
        paste(canvas, body, PAD, PAD)

    if BAKE_CLOUDS:
        draw_clouds(canvas, mask, cx, orbit, clouds, t, total, d, body_paste)
    else:
        body_paste()
    marks, template = source_marks(a, d, i, ax, ay)
    return Frame1x(canvas, (cx, cy), disp, marks, template)


# ---------------------------------------------------------------------------
# Cases agrandies
# ---------------------------------------------------------------------------
def fit(frames: list[Frame1x], scale: int) -> tuple[int, int]:
    """Plus petite case (multiple de 8) contenant toutes les images, ancre au repos en (fw/2, fh/2 + 4)."""
    need_w = need_h = 8
    for f in frames:
        ys, xs = np.nonzero(f.img[:, :, 3])
        cx, cy = f.anchor
        rx, ry = cx - f.disp[0], cy - f.disp[1]                       # ancre au repos dans le canevas
        left, right = (rx - int(xs.min())) * scale + 1, (int(xs.max()) + 1 - rx) * scale + 1
        top, bottom = (ry - int(ys.min())) * scale + 1, (int(ys.max()) + 1 - ry) * scale + 1
        need_w = max(need_w, 2 * max(left, right))
        need_h = max(need_h, 2 * max(top - 4, bottom + 4))
    return -(-need_w // 8) * 8, -(-need_h // 8) * 8


def upscale(img: np.ndarray, scale: int) -> np.ndarray:
    return np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)


def make_cell(f: Frame1x, fw: int, fh: int, scale: int) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], tuple[int, int]]:
    ax, ay = fw // 2 + f.disp[0] * scale, fh // 2 + 4 + f.disp[1] * scale
    anim = np.zeros((fh, fw, 4), np.uint8)
    offs = np.zeros((fh, fw, 4), np.uint8)
    shad = np.zeros((fh, fw, 4), np.uint8)
    big = upscale(f.img, scale)
    ox, oy = ax - f.anchor[0] * scale, ay - f.anchor[1] * scale
    ys, xs = np.nonzero(big[:, :, 3])
    assert xs.min() + ox >= 1 and ys.min() + oy >= 1 and xs.max() + ox <= fw - 2 and ys.max() + oy <= fh - 2, "dessin hors de la case"
    paste(anim, big, ox, oy)
    for mx, my, rgb in f.marks:
        offs[ay + my * scale, ax + mx * scale] = (*rgb, 255)
    for tx, ty, rgb in f.template:
        y0, x0 = ay + ty * scale, ax + tx * scale
        shad[y0:y0 + scale, x0:x0 + scale] = (*rgb, 255)
    shad[ay:ay + scale, ax:ax + scale] = (0, 255, 0, 255)          # le bloc de l'ancre : vert, sauf le pixel blanc
    shad[ay, ax] = (255, 255, 255, 255)
    return (anim, offs, shad), (ax, ay)


def make_cell_scaled(img: np.ndarray, anchor: tuple[int, int], fw: int, fh: int, marks, template, scale: int):
    """Comme make_cell, pour une image déjà à l'échelle (transformation) ; ancre au repos, sans déplacement."""
    ax, ay = fw // 2, fh // 2 + 4
    anim = np.zeros((fh, fw, 4), np.uint8)
    offs = np.zeros((fh, fw, 4), np.uint8)
    shad = np.zeros((fh, fw, 4), np.uint8)
    ox, oy = ax - anchor[0], ay - anchor[1]
    ys, xs = np.nonzero(img[:, :, 3])
    assert xs.min() + ox >= 1 and ys.min() + oy >= 1 and xs.max() + ox <= fw - 2 and ys.max() + oy <= fh - 2, "transformation hors de la case"
    paste(anim, img, ox, oy)
    for mx, my, rgb in marks:
        offs[ay + my * scale, ax + mx * scale] = (*rgb, 255)
    for tx, ty, rgb in template:
        y0, x0 = ay + ty * scale, ax + tx * scale
        shad[y0:y0 + scale, x0:x0 + scale] = (*rgb, 255)
    shad[ay:ay + scale, ax:ax + scale] = (0, 255, 0, 255)
    shad[ay, ax] = (255, 255, 255, 255)
    return (anim, offs, shad), (ax, ay)


def body_size(anims: list[SrcAnim]) -> tuple[int, int]:
    walk = next(a for a in anims if a.name == "Walk")
    body = walk.cell(walk.anim, 0, 0)
    xs = np.nonzero(body[:, :, 3].any(axis=0))[0]
    ys = np.nonzero(body[:, :, 3].any(axis=1))[0]
    return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def orbit_for(anims: list[SrcAnim]) -> tuple[int, int]:
    """Ellipse des nuages, en pixels du dessin : demi-largeur = demi-largeur du corps au repos + 3, demi-hauteur
    = un sixième de la hauteur du corps (au moins 3) : un halo aplati vu de trois quarts, comme l'anneau de nuages
    au-dessus des Pokémon dynamaxés de Pokémon GO."""
    width, height = body_size(anims)
    return width // 2 + 3, max(3, int(round(height / 6)))


def build_pack(anims: list[SrcAnim], scale: int) -> dict[str, Composed]:
    orbit = orbit_for(anims)
    dark = darkest_colour(anims)
    clouds = FX.clouds(small=body_size(anims)[0] < NARROW, dark=dark)
    comps: dict[str, Composed] = {}
    for a in anims:
        if a.copy_of:
            continue
        total = sum(a.durations)
        frames = []
        for d in range(a.dirs):
            t = 0
            row = []
            for i, dur in enumerate(a.durations):
                row.append(compose_frame(a, d, i, orbit, clouds, t, total))
                t += dur
            frames.append(row)
        fw, fh = fit([f for row in frames for f in row], scale)
        comp = Composed(a.name, fw, fh, list(a.durations), rush=a.rush, hit=a.hit, ret=a.ret)
        for row in frames:
            cells, anchors = [], []
            for f in row:
                cell, anchor = make_cell(f, fw, fh, scale)
                cells.append(cell)
                anchors.append(anchor)
            comp.cells.append(cells)
            comp.anchors.append(anchors)
        comp.notes = f"case d'origine {a.fw} × {a.fh}"
        comps[a.name] = comp
    return comps


def vfx_info(anims: list[SrcAnim], scale: int) -> dict:
    """Comment poser les VFX génériques (personnages/dynamax/vfx/) sur ce sprite : taille (M si le corps fait
    ≤ 24 px de large à l'échelle 1, sinon L) et décalage vertical de l'anneau de nuages par rapport à l'ancre
    (2 px au-dessus du sommet du sprite au repos, à l'échelle)."""
    width, _ = body_size(anims)
    walk = next(a for a in anims if a.name == "Walk")
    body = walk.cell(walk.anim, 0, 0)
    ax, ay = white_pixel(walk.cell(walk.shad, 0, 0))
    top = int(np.nonzero(body[:, :, 3].any(axis=1))[0].min())
    return {"taille": "M" if width <= NARROW else "L",
            "dossier": "personnages/dynamax/vfx/",
            "ancre_transformation": "ancre du sprite (pixel blanc de Shadow), au sol",
            "ancre_nuages_decalage": [0, (top - ay) * scale - 2 * scale],
            "sequence": "Transformation-<taille> à l'ancre du sprite (masquer le sprite d'origine dès l'image 5, afficher ce sprite à HitFrame) ; "
                        "à ReturnFrame, NuagesApparition-<taille> puis boucle Nuages-<taille> à l'ancre + ancre_nuages_decalage"}


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def write_animdata(anims: list[SrcAnim], comps: dict[str, Composed], path: Path) -> None:
    lines = ['<?xml version="1.0" ?>', "<AnimData>", f"\t<ShadowSize>{SHADOW_SIZE}</ShadowSize>", "\t<Anims>"]
    for a in anims:
        lines += ["\t\t<Anim>", f"\t\t\t<Name>{a.name}</Name>"]
        if a.index is not None:
            lines.append(f"\t\t\t<Index>{a.index}</Index>")
        if a.copy_of:
            lines += [f"\t\t\t<CopyOf>{a.copy_of}</CopyOf>", "\t\t</Anim>"]
            continue
        c = comps[a.name]
        lines += [f"\t\t\t<FrameWidth>{c.fw}</FrameWidth>", f"\t\t\t<FrameHeight>{c.fh}</FrameHeight>"]
        for tag, value in (("RushFrame", c.rush), ("HitFrame", c.hit), ("ReturnFrame", c.ret)):
            if value is not None:
                lines.append(f"\t\t\t<{tag}>{value}</{tag}>")
        lines.append("\t\t\t<Durations>")
        lines += [f"\t\t\t\t<Duration>{d}</Duration>" for d in c.durations]
        lines += ["\t\t\t</Durations>", "\t\t</Anim>"]
    lines += ["\t</Anims>", "</AnimData>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def ground_shadow(img: Image.Image, ax: int, ay: int, zoom: int, scale: int) -> None:
    d = ImageDraw.Draw(img)
    r = 12 * scale * zoom
    d.ellipse([ax - r, ay - r // 3, ax + r - zoom, ay + r // 4], fill=(40, 24, 8, 90))


def cell_image(c: Composed, d: int, i: int, zoom: int, scale: int, bg=(26, 26, 46, 255)) -> Image.Image:
    img = Image.new("RGBA", (c.fw * zoom, c.fh * zoom), bg)
    ax, ay = c.anchors[d][i]
    ground_shadow(img, ax * zoom + zoom // 2, ay * zoom + zoom // 2, zoom, scale)
    cell = Image.fromarray(c.cells[d][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
    img.alpha_composite(cell)
    return img


def contact_sheet(title: str, subtitle: str, anims: list[SrcAnim], comps: dict[str, Composed], path: Path, scale: int) -> None:
    zoom = 1
    blocks = []
    for a in anims:
        if a.copy_of:
            continue
        c = comps[a.name]
        dirs = [0, 2] if a.name in ("Walk", "Attack") and len(c.cells) > 1 else [0]
        n = len(c.durations)
        img = Image.new("RGBA", (n * (c.fw * zoom + 2) + 8, len(dirs) * (c.fh * zoom + 2) + 26), (26, 26, 46, 255))
        d = ImageDraw.Draw(img)
        extra = "".join(f" · {k} {v}" for k, v in (("Rush", c.rush), ("Hit", c.hit), ("Return", c.ret)) if v is not None)
        d.text((4, 4), f"{a.name} (index {a.index}) — case {c.fw} × {c.fh}, {n} images, {len(c.cells)} direction(s), durées {c.durations}{extra}",
               fill=(230, 230, 230, 255), font=font(12))
        for r, dd in enumerate(dirs):
            for i in range(n):
                img.alpha_composite(cell_image(c, dd, i, zoom, scale, (36, 36, 60, 255)), (4 + i * (c.fw * zoom + 2), 26 + r * (c.fh * zoom + 2)))
        blocks.append(img)
    W = max(b.width for b in blocks)
    H = sum(b.height + 6 for b in blocks) + 64
    out = Image.new("RGBA", (W + 16, H), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), title, fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 36), subtitle, fill=(170, 170, 200, 255), font=font(12))
    y = 64
    for b in blocks:
        out.alpha_composite(b, (8, y))
        y += b.height + 6
    out.save(path, optimize=True)


def directions_sheet(comps: dict[str, Composed], path: Path, scale: int) -> None:
    zoom = 2
    c = comps["Walk"]
    cw, ch = c.fw * zoom + 6, c.fh * zoom + 22
    out = Image.new("RGBA", (8 * cw + 6, ch + 40), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 8), f"Walk, image 1 — les huit directions (× {zoom}), ombre du jeu sous l'ancre", fill=(240, 240, 240, 255), font=font(14))
    for dd in range(8):
        out.alpha_composite(cell_image(c, dd, 0, zoom, scale, (36, 36, 60, 255)), (6 + dd * cw, 40))
        d.text((6 + dd * cw + 4, 40 + c.fh * zoom + 4), DIRECTIONS[dd], fill=(200, 200, 220, 255), font=font(12))
    out.save(path, optimize=True)


def comparison_sheet(name: str, anims: list[SrcAnim], comps: dict[str, Composed], path: Path, scale: int) -> None:
    """Le sprite d'origine et sa version Dynamax côte à côte sur le parquet, même échelle d'affichage."""
    zoom = 3
    walk = next(a for a in anims if a.name == "Walk")
    c = comps["Walk"]
    ch = c.fh * zoom + 8
    cw = c.fw * zoom + 8
    out = parquet_background((2 * cw + 24, ch + 44), zoom)
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, out.width, 30], fill=(26, 26, 46, 255))
    d.text((8, 8), f"{name} — à gauche le sprite SpriteCollab, à droite la version Dynamax (× {scale}), affichage × {zoom}",
           fill=(240, 240, 240, 255), font=font(13))
    # origine
    body = walk.cell(walk.anim, 0, 0)
    ax, ay = white_pixel(walk.cell(walk.shad, 0, 0))
    bx, by = 12 + cw // 2, 36 + ch * 3 // 4
    ground_shadow(out, bx, by, zoom, 1)
    out.alpha_composite(Image.fromarray(body, "RGBA").resize((walk.fw * zoom, walk.fh * zoom), Image.NEAREST), (bx - ax * zoom, by - ay * zoom))
    # dynamax
    ax2, ay2 = c.anchors[0][0]
    bx2 = 12 + cw + 12 + cw // 2
    ground_shadow(out, bx2, by, zoom, scale)
    out.alpha_composite(Image.fromarray(c.cells[0][0][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST), (bx2 - ax2 * zoom, by - ay2 * zoom))
    out.save(path, optimize=True)


def gif(comps: dict[str, Composed], names: list[str], directions: list[int], path: Path, scale: int, zoom: int = 1, span: int = 240) -> None:
    """Animation de contrôle : une case par direction, ancre fixe, sur le parquet de la guilde."""
    names = [n for n in names if n in comps]
    # taille des cases du GIF : étendue réelle du dessin autour de l'ancre (les cases de QuickStrike ou Swing sont
    # bien plus grandes que leur contenu)
    ext = [0, 0, 0, 0]                                   # gauche, droite, haut, bas
    for n in names:
        c = comps[n]
        for d, row in enumerate(c.cells):
            for i, cell in enumerate(row):
                ys, xs = np.nonzero(cell[0][:, :, 3])
                ax, ay = c.anchors[d][i]
                ext = [max(ext[0], ax - int(xs.min())), max(ext[1], int(xs.max()) + 1 - ax),
                       max(ext[2], ay - int(ys.min())), max(ext[3], int(ys.max()) + 1 - ay)]
    half_w = max(ext[0], ext[1]) + 4
    cw = 2 * half_w * zoom + 8
    ch = (ext[2] + max(ext[3], 8) + 8) * zoom + 8
    cols, rows = len(directions), len(names)
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
    bg = parquet_background((cols * cw, rows * ch), zoom)
    frames_out, durations_out = [], []
    for k, t in enumerate(events):
        nxt = events[k + 1] if k + 1 < len(events) else span
        img = bg.copy()
        for r, n in enumerate(names):
            c = comps[n]
            i = max(i for tt, i in tick_frames[n] if tt <= t)
            for col, direction in enumerate(directions):
                dd = direction if len(c.cells) > 1 else 0
                cell = Image.fromarray(c.cells[dd][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
                ax, ay = c.anchors[dd][i]
                cx, cy = col * cw + cw // 2, r * ch + 4 + (ext[2] + 4) * zoom
                ground_shadow(img, cx, cy, zoom, scale)
                img.alpha_composite(cell, (cx - ax * zoom, cy - ay * zoom))
        frames_out.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations_out.append(int(round((nxt - t) * 1000 / 60)))
    frames_out[0].save(path, save_all=True, append_images=frames_out[1:], duration=durations_out, loop=0, optimize=True)


def player_html(title: str, anims: list[SrcAnim], comps: dict[str, Composed], path: Path, scale: int) -> None:
    manifest = {name: {"fw": c.fw, "fh": c.fh, "durations": c.durations, "dirs": len(c.cells),
                       "anchors": c.anchors, "hit": c.hit, "rush": c.rush, "ret": c.ret} for name, c in comps.items()}
    names = [a.name for a in anims if not a.copy_of]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>{title} — sprite Dynamax PMD</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#1a1a2e;color:#eee}}
header{{padding:12px 16px;border-bottom:1px solid #333}}
h1{{font-size:18px;margin:0 0 4px}} p{{margin:2px 0;color:#aab;font-size:13px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px 16px;padding:10px 16px;align-items:center;font-size:14px}}
select,input,button,label{{font-size:14px}}
canvas{{image-rendering:pixelated;background:#2a2a3e;display:block;border:1px solid #444}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:0 16px 16px}}
.grid div{{text-align:center;font-size:12px;color:#aab}} .grid canvas{{margin:4px auto}}
</style></head><body>
<header><h1>{title} — sprite Dynamax, format SpriteCollab (× {scale})</h1>
<p>Lecture hors ligne des feuilles <code>*-Anim.png</code>. Les images sont alignées sur le pixel blanc de <code>*-Shadow.png</code>, comme dans le jeu. Case du donjon = 24 px.</p></header>
<div class="bar">
<label>Animation <select id="anim">{''.join(f'<option>{n}</option>' for n in names)}</select></label>
<label>Zoom <input id="zoom" type="range" min="1" max="6" value="2"></label>
<label><input id="shadow" type="checkbox" checked> ombre du jeu</label>
<label><input id="offsets" type="checkbox"> repères</label>
<label><input id="grid" type="checkbox" checked> grille 24 px</label>
<label><input id="night" type="checkbox"> nuit</label>
<button id="pause">Pause</button>
<span id="info"></span>
</div>
<div class="grid" id="grid8"></div>
<script>
const M = {json.dumps(manifest)};
const DIRS = {json.dumps(DIRECTIONS)};
const SCALE = {scale};
const sheets = {{}};
function load(name, kind, night) {{
  const key = name + kind + (night ? 'n' : ''); if (sheets[key]) return sheets[key];
  const im = new Image(); im.src = (night && kind === 'Anim' ? 'nuit/' : '') + name + '-' + kind + '.png'; sheets[key] = im; return im;
}}
const grid = document.getElementById('grid8');
const cvs = [];
for (let d = 0; d < 8; d++) {{
  const box = document.createElement('div'); const c = document.createElement('canvas');
  box.appendChild(c); const cap = document.createElement('span'); cap.textContent = DIRS[d]; box.appendChild(cap);
  grid.appendChild(box); cvs.push(c);
}}
let t0 = performance.now(), paused = false, pauseAt = 0;
document.getElementById('pause').onclick = () => {{ paused = !paused; if (paused) pauseAt = performance.now(); else t0 += performance.now() - pauseAt; document.getElementById('pause').textContent = paused ? 'Lecture' : 'Pause'; }};
function frameAt(m, ticks) {{
  const total = m.durations.reduce((a, b) => a + b, 0); let t = ticks % total;
  for (let i = 0; i < m.durations.length; i++) {{ if (t < m.durations[i]) return i; t -= m.durations[i]; }}
  return 0;
}}
function draw() {{
  const name = document.getElementById('anim').value, m = M[name], z = +document.getElementById('zoom').value;
  const nightMode = document.getElementById('night').checked;
  const anim = load(name, 'Anim', nightMode), offs = load(name, 'Offsets', false);
  const now = paused ? pauseAt : performance.now();
  const ticks = Math.floor((now - t0) / 1000 * 60);
  const i = frameAt(m, ticks);
  const W = Math.max(m.fw, 48) * z, H = Math.max(m.fh, 48) * z;
  for (let d = 0; d < 8; d++) {{
    const c = cvs[d]; c.width = W; c.height = H; const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
    if (nightMode) {{ g.fillStyle = '#12121f'; g.fillRect(0, 0, W, H); }}
    const dd = m.dirs > 1 ? d : 0;
    const [ax, ay] = m.anchors[dd][i];
    const ox = Math.round(W / 2 - ax * z), oy = Math.round(H * 0.62 - ay * z);
    if (document.getElementById('grid').checked) {{
      g.strokeStyle = 'rgba(255,255,255,0.12)';
      for (let x = (W / 2) % (24 * z); x < W; x += 24 * z) {{ g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }}
      for (let y = (H * 0.62) % (24 * z); y < H; y += 24 * z) {{ g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }}
    }}
    if (document.getElementById('shadow').checked) {{
      g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath();
      g.ellipse(ox + ax * z, oy + ay * z, 12 * SCALE * z, 4 * SCALE * z, 0, 0, Math.PI * 2); g.fill();
    }}
    g.drawImage(anim, i * m.fw, dd * m.fh, m.fw, m.fh, ox, oy, m.fw * z, m.fh * z);
    if (document.getElementById('offsets').checked) g.drawImage(offs, i * m.fw, dd * m.fh, m.fw, m.fh, ox, oy, m.fw * z, m.fh * z);
  }}
  document.getElementById('info').textContent = `${{name}} · image ${{i + 1}}/${{m.durations.length}} · case ${{m.fw}}×${{m.fh}} px · durées ${{m.durations.join(',')}}` + (m.hit != null ? ` · HitFrame ${{m.hit}}` : '');
  requestAnimationFrame(draw);
}}
requestAnimationFrame(draw);
</script></body></html>
"""
    path.write_text(html, encoding="utf-8")


def source_credit_lines(folder: Path) -> list[str]:
    text = (folder / "credits.txt").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line.strip() and not line.startswith("#")]


def licence_of(folder: Path) -> str:
    for line in source_credit_lines(folder):
        parts = line.split("\t")
        if len(parts) >= 4 and parts[3] in LICENCES:
            return parts[3]
    return "Unspecified"


def write_credits(number: str, name: str, folder: Path, anims: list[SrcAnim], path: Path, scale: int) -> None:
    lic = licence_of(folder)
    names = ",".join(a.name for a in anims)
    src = folder.relative_to(ROOT)
    lines = [
        f"# {name} #{number} — version Dynamax, crédits au format SpriteCollab : date, auteur, statut, licence, animations",
        f"2026-09-08 00:00:00.000000\tGuilde Treehouse (agrandissement × {scale}, aura et nuages Dynamax, assemblage scripté)\tCUR\t{lic}\t{names}",
        "",
        f"Sprite d'origine : {src} (copie du dépôt SpriteCollab, https://sprites.pmdcollab.org/#/{number}?form=0), crédits repris tels quels :",
    ]
    lines += ["  " + line for line in source_credit_lines(folder)]
    lines += [
        "",
        f"Transformation : chaque pixel du sprite d'origine est agrandi × {scale} (aucun pixel du Pokémon redessiné) ; l'aura rouge, son anneau",
        "tramé animé est ajouté autour (deux couleurs ajoutées : aura, aura claire) ; nuages et transformation sont des VFX séparés. Toutes les animations",
        "du sprite d'origine sont reprises avec leurs index, durées, RushFrame / HitFrame / ReturnFrame et déplacements d'ancre (× échelle).",
        f"Licence : {LICENCES[lic]} ; cette version dérivée suit la licence du sprite d'origine.",
        "Forme non officielle : ce sprite n'a été ni soumis ni approuvé sur SpriteCollab.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(number: str, slug: str, name: str, folder: Path, anims: list[SrcAnim], comps: dict[str, Composed],
                 colours: int, path: Path, scale: int) -> None:
    lic = licence_of(folder)
    rows = []
    for a in anims:
        if a.copy_of:
            rows.append(f"| {a.name} | {a.index if a.index is not None else '—'} | — | — | — | copie de {a.copy_of} |")
            continue
        c = comps[a.name]
        extra = ", ".join(f"{k} {v}" for k, v in (("Rush", c.rush), ("Hit", c.hit), ("Return", c.ret)) if v is not None)
        rows.append(f"| {a.name} | {a.index} | {c.fw} × {c.fh} (origine {a.fw} × {a.fh}) | {len(c.durations)} | {sum(c.durations)} ticks | {extra or '—'} |")
    text = f"""# {name} #{number} — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de {name} : toutes les animations du sprite d'origine
(`{folder.relative_to(ROOT)}`) sont reprises, agrandies × {scale} au plus proche voisin et entourées d'une aura rouge
animée (anneau plein + trame qui remonte le long du corps). Aucun pixel du Pokémon n'est redessiné ; deux couleurs
sont ajoutées ({colours} couleurs au total). `ShadowSize` passe à 2 (grande ombre). **Les nuages tournants et la
transformation sont des VFX séparés**, sans personnage, à superposer en jeu : voir
[`personnages/dynamax/vfx/`](../vfx/README.md) et l'entrée `dynamax.vfx` de `kit.json` (taille et décalage).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `{slug}.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × {scale} puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

{LICENCES[lic]}. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
"""
    path.write_text(text, encoding="utf-8")


def build_one(number: str, slug: str, name: str, folder: Path, scale: int) -> dict:
    out = OUT_ROOT / f"{number}_{slug}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "nuit").mkdir(exist_ok=True)
    for old in list(out.glob("*.png")) + list(out.glob("nuit/*.png")):
        old.unlink()
    src_shadow, anims = load_source(folder)
    comps = build_pack(anims, scale)
    for name_, c in comps.items():
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            save_png(sheet(c, which), out / f"{name_}-{kind}.png")
        save_png(night(sheet(c, 0)), out / "nuit" / f"{name_}-Anim.png")
    write_animdata(anims, comps, out / "AnimData.xml")
    order = [a.name for a in anims if not a.copy_of]
    ase_info = write_aseprite(comps, out / f"{slug}.aseprite", order)
    title = f"{name.upper()} #{number} — SPRITE DYNAMAX, FORMAT SPRITECOLLAB (× {scale})"
    contact_sheet(title, "Toutes les animations du sprite SpriteCollab d'origine, agrandies, avec l'aura animée · nuages et transformation : VFX séparés · Walk, Attack : ligne 1 = Bas, ligne 2 = Droite",
                  anims, comps, out / "apercu.png", scale)
    directions_sheet(comps, out / "apercu_directions.png", scale)
    comparison_sheet(name, anims, comps, out / "apercu_comparaison.png", scale)
    gif(comps, ["Walk", "Idle"], [0, 2, 4, 6], out / "apercu_marche_attente.gif", scale)
    specials = [a.name for a in anims if not a.copy_of and a.name not in
                ("Walk", "Idle", "Sleep", "Hurt", "Attack", "Charge", "Shoot", "Swing", "Double", "Hop", "Rotate")]
    gif(comps, ["Attack"] + specials[:1] + (["Shoot"] if not specials and "Shoot" in comps else []), [0, 2, 4, 6], out / "apercu_attaques.gif", scale)
    player_html(f"{name} #{number}", anims, comps, out / "apercu.html", scale)
    write_credits(number, name, folder, anims, out / "credits.txt", scale)

    used = set()
    for c in comps.values():
        for row in c.cells:
            for cell in row:
                a = cell[0]
                used |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
    write_readme(number, slug, name, folder, anims, comps, len(used), out / "README.md", scale)
    kit = {
        "pokemon": {"numero": number, "nom": name, "forme": "Dynamax (non officielle)", "source": str(folder.relative_to(ROOT)),
                    "licence": LICENCES[licence_of(folder)]},
        "format": {"convention": "SpriteCollab / SkyTemple : <Anim>-Anim.png, <Anim>-Offsets.png, <Anim>-Shadow.png + AnimData.xml",
                   "directions": DIRECTIONS, "ancre": "pixel blanc de Shadow, en (largeur/2, hauteur/2 + 4) au repos, déplacée comme dans la source (× échelle)",
                   "shadow_size": SHADOW_SIZE, "shadow_size_origine": src_shadow,
                   "reperes": "tête (noir), centre (vert), main gauche (rouge), main droite (bleu), un pixel chacun replacé à l'échelle"},
        "dynamax": {"echelle": scale, "couleurs_effets": {"sombre": FX.FX_DARK, "rouge": FX.FX_RED, "claire": FX.FX_LIGHT, "blanc": FX.FX_WHITE, "contour_nuages": darkest_colour(anims)},
                    "aura": "anneau plein rouge + anneau tramé clair dont le motif remonte d'un pixel par phase (4 phases par cycle d'animation) + langues extérieures",
                    "nuages_integres": BAKE_CLOUDS,
                    "vfx": vfx_info(anims, scale)},
        "animations": {a.name: ({"index": a.index, "copie_de": a.copy_of} if a.copy_of else
                                {"index": a.index, "case": [comps[a.name].fw, comps[a.name].fh], "case_origine": [a.fw, a.fh],
                                 "images": len(a.durations), "durees": a.durations, "directions": comps[a.name].cells.__len__(),
                                 "rush": a.rush, "hit": a.hit, "return": a.ret}) for a in anims},
        "palette": {"couleurs_opaques": len(used), "ajoutees": 2 if not BAKE_CLOUDS else 3, "limite_spritebot": 15,
                    "note": "au-delà de 15 couleurs le sprite n'est pas importable en mode strict SkyTemple (forme non officielle de toute façon)"},
        "aseprite": ase_info,
        "fichiers": {"feuilles": "<Anim>-Anim.png, <Anim>-Offsets.png, <Anim>-Shadow.png", "nuit": "nuit/<Anim>-Anim.png",
                     "apercus": ["apercu.png", "apercu_directions.png", "apercu_comparaison.png", "apercu_marche_attente.gif", "apercu_attaques.gif", "apercu.html"]},
    }
    (out / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding="utf-8")
    cells = sum(len(c.durations) * len(c.cells) for c in comps.values())
    print(f"{number} {name} : {len(anims)} animations, {cells} cases, {len(used)} couleurs → {out.relative_to(ROOT)}")
    return kit


def main(argv: list[str]) -> None:
    scale = SCALE
    slugs = []
    it = iter(argv)
    global BAKE_CLOUDS
    for arg in it:
        if arg == "--echelle":
            scale = int(next(it))
        elif arg == "--nuages-integres":
            BAKE_CLOUDS = True
        else:
            slugs.append(arg)
    for number, slug, name, folder in POKEMON:
        if slugs and slug not in slugs and number not in slugs:
            continue
        build_one(number, slug, name, folder, scale)


if __name__ == "__main__":
    main(sys.argv[1:])
