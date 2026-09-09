#!/usr/bin/env python3
"""Sprites Dynamax de tous les Pokémon animés de SpriteCollab → sprite/<dex>_<slug>/ (format SpriteCollab).

Pour chaque espèce dont le dossier `sprite/<dex>/` de https://github.com/PMDCollab/SpriteCollab contient un
`AnimData.xml`, **toutes** ses animations sont reprises (noms, index, CopyOf, durées, RushFrame / HitFrame /
ReturnFrame, déplacements d'ancre) et transformées :

1. agrandissement × 3 au plus proche voisin (aucun pixel du Pokémon redessiné) ;
2. aura rouge animée collée à la silhouette (anneau plein + anneau tramé dont le motif remonte à chaque image
   + langues extérieures) — deux couleurs ajoutées : (232, 40, 72) et (255, 144, 128) ;
3. trois nuages-cyclones rouges qui tournent au-dessus de la tête (un tiers de tour par cycle d'animation, boucle
   continue ; volute à trois phases ; la moitié arrière de l'anneau passe derrière le corps) — contour = couleur
   la plus sombre du sprite, pas de couleur ajoutée ; petits nuages si le corps fait moins de 24 px de large
   ou moins de 20 px de haut ;
4. repères d'Offsets et ancre de Shadow replacés à l'échelle, gabarit d'ombre agrandi, ShadowSize 2 ;
5. cases élargies par pas de 8, ancre au repos en (largeur / 2, hauteur / 2 + 4).

Sorties par espèce : `AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (PNG indexés, mêmes
pixels qu'en RGBA), `credits.txt` (crédits SpriteCollab repris + ligne Dynamax). Pas d'aperçu par espèce : voir
`apercu.py` (planche et GIF globaux) et `verify_dynamax.py` (contrôles).

La source est le dépôt SpriteCollab lui-même, cloné en sparse (dossiers `sprite/<dex>/` racine seulement, ~300 Mo)
dans `--source` (défaut : /tmp/spritecollab) s'il n'y est pas déjà.

Usage :
  python3 source/sprite/build_dynamax.py 0025 0297          # quelques espèces (numéros)
  python3 source/sprite/build_dynamax.py --tous              # les 978
  python3 source/sprite/build_dynamax.py --de 0001 --a 0151  # une tranche
  options : --echelle N (3), --procs N (2), --source DIR, --sans-nuages,
            --credits-seulement (réécrit credits.txt + licence de l'index sans reconstruire les feuilles)
  Falinks (0870) et Zarude (0893), absents de SpriteCollab, sont lus dans personnages/ (LOCAL_SOURCES).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dynamax_fx as FX  # noqa: E402

OUT_ROOT = ROOT / "sprite"
DEFAULT_SOURCE = Path("/tmp/spritecollab")
SPRITECOLLAB = "https://github.com/PMDCollab/SpriteCollab"
NAMES = json.loads((HERE / "noms.json").read_text(encoding="utf-8"))

SCALE = 3
SHADOW_SIZE = 2
PAD = 28                          # marge du canevas 1:1 autour de la case source (aura 3 px + nuages)
NARROW = 24                       # largeur du corps (px, échelle 1) sous laquelle on prend les petits nuages
STRUCT = np.ones((3, 3), bool)
AURA, AURA_LIGHT = FX.FX_RED, FX.FX_LIGHT
# sprites du projet au format SpriteCollab mais absents de SpriteCollab (pas de forme 0000 pour 0870, pas de dossier 0893)
LOCAL_SOURCES = {"0870": ROOT / "personnages" / "falinks", "0893": ROOT / "personnages" / "zarude"}
DIRECTIONS = ["Bas", "Bas-droite", "Droite", "Haut-droite", "Haut", "Haut-gauche", "Gauche", "Bas-gauche"]


# ---------------------------------------------------------------------------
# Source SpriteCollab
# ---------------------------------------------------------------------------
def ensure_source(source: Path) -> str:
    """Clone sparse de SpriteCollab (dossiers sprite/<dex>/ racine, sans les formes) ; renvoie le commit."""
    if not (source / "sprite").is_dir():
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--depth", "1", "--sparse", SPRITECOLLAB, str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "sparse-checkout", "set", "--no-cone", "/sprite/*", "!/sprite/*/*/", "/tracker.json"], check=True)
    return subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def list_species(source: Path) -> list[str]:
    found = {d.name for d in (source / "sprite").iterdir() if (d / "AnimData.xml").is_file() and d.name != "0000"}  # 0000 = gabarit Missingno
    found |= {d for d, f in LOCAL_SOURCES.items() if (f / "AnimData.xml").is_file()}
    return sorted(found)


def source_folder(dex: str, source: Path) -> Path:
    return LOCAL_SOURCES.get(dex) or source / "sprite" / dex


def slug_of(dex: str) -> str:
    return NAMES.get(dex, {}).get("slug", f"pokemon-{dex}")


def name_of(dex: str) -> str:
    n = NAMES.get(dex, {})
    fr, en = n.get("fr", dex), n.get("en", "")
    return fr if not en or en == fr else f"{fr} ({en})"


# ---------------------------------------------------------------------------
# Lecture d'un sprite SpriteCollab
# ---------------------------------------------------------------------------
@dataclass
class SrcAnim:
    name: str
    index: int | None                 # certains alias CopyOf n'ont pas d'<Index> : on le laisse absent
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


def load_source(folder: Path, light: bool = False) -> tuple[int, list[SrcAnim]]:
    """Animations exploitables de la source ; `light` ne lit que les en-têtes PNG (liste des noms, pour les crédits)."""
    shadow_size, anims = parse_animdata(folder / "AnimData.xml")
    kept = []
    for a in anims:
        if a.copy_of:
            kept.append(a)
            continue
        p = folder / f"{a.name}-Anim.png"
        if not p.is_file():
            continue                                        # animation déclarée sans feuille : ignorée
        if light:
            sizes = [Image.open(folder / f"{a.name}-{k}.png").size for k in ("Anim", "Offsets", "Shadow")]
            w, h = sizes[0]
            if len(set(sizes)) != 1 or w != a.fw * len(a.durations) or h % a.fh:
                continue
            kept.append(a)
            continue
        a.anim = np.array(Image.open(p).convert("RGBA"))
        a.offs = np.array(Image.open(folder / f"{a.name}-Offsets.png").convert("RGBA"))
        a.shad = np.array(Image.open(folder / f"{a.name}-Shadow.png").convert("RGBA"))
        if not (a.anim.shape == a.offs.shape == a.shad.shape) or a.anim.shape[1] != a.fw * len(a.durations) or a.anim.shape[0] % a.fh:
            continue                                        # feuille incohérente : ignorée
        kept.append(a)
    names = {a.name for a in kept if not a.copy_of}
    kept = [a for a in kept if not a.copy_of or a.copy_of in names]
    return shadow_size, kept


def white_pixel(shad_cell: np.ndarray, fw: int, fh: int) -> tuple[int, int]:
    w = np.argwhere((shad_cell[:, :, 3] > 0) & np.all(shad_cell[:, :, :3] == 255, axis=2))
    if len(w) == 0:
        return fw // 2, fh // 2 + 4
    return int(w[0][1]), int(w[0][0])


def darkest_colour(anims: list[SrcAnim]) -> tuple[int, int, int]:
    walk = next((a for a in anims if a.name == "Walk" and a.anim is not None), None) or next(a for a in anims if a.anim is not None)
    px = walk.anim[walk.anim[:, :, 3] > 0][:, :3].astype(int)
    if len(px) == 0:
        return FX.FX_DARK
    lum = px @ np.array([299, 587, 114])
    return tuple(int(v) for v in px[int(lum.argmin())])


def body_size(anims: list[SrcAnim]) -> tuple[int, int]:
    walk = next((a for a in anims if a.name == "Walk" and a.anim is not None), None) or next(a for a in anims if a.anim is not None)
    body = walk.cell(walk.anim, 0, 0)
    xs = np.nonzero(body[:, :, 3].any(axis=0))[0]
    ys = np.nonzero(body[:, :, 3].any(axis=1))[0]
    if len(xs) == 0:
        return 16, 16
    return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


# ---------------------------------------------------------------------------
# Composition d'une case à l'échelle 1 (aura + nuages), puis agrandissement
# ---------------------------------------------------------------------------
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


@dataclass
class Frame1x:
    img: np.ndarray
    anchor: tuple[int, int]
    disp: tuple[int, int]
    marks: list[tuple[int, int, tuple[int, int, int]]]
    template: list[tuple[int, int, tuple[int, int, int]]]


def draw_clouds(canvas: np.ndarray, mask: np.ndarray, cx: int, orbit: tuple[int, int], clouds: list[np.ndarray],
                t: int, total: int, d: int, body_paste) -> None:
    ys = np.nonzero(mask.any(axis=1))[0]
    top = int(ys.min())
    rx, ry = orbit
    oy = top - ry - 1
    placements = []
    for ang, phase in FX.cloud_ring(t, total, d):
        c = clouds[phase]
        px = int(round(cx + rx * math.cos(ang))) - c.shape[1] // 2
        py = int(round(oy + ry * math.sin(ang))) - c.shape[0] // 2
        trail = FX.TRAIL_SMALL if c.shape[1] < 14 else FX.TRAIL
        if math.sin(ang) > 0:
            tx, tr = px - trail.shape[1] + 1, trail
        else:
            tx, tr = px + c.shape[1] - 1, trail[:, ::-1]
        placements.append((math.sin(ang) > 0, c, px, py, tr, tx, py + c.shape[0] // 2 - 1))
    for front, c, px, py, tr, tx, ty in placements:
        if not front:
            paste(canvas, tr, tx, ty)
            paste(canvas, c, px, py)
    body_paste()
    for front, c, px, py, tr, tx, ty in placements:
        if front:
            paste(canvas, tr, tx, ty)
            paste(canvas, c, px, py)


def compose_frame(a: SrcAnim, d: int, i: int, orbit, clouds, t: int, total: int, with_clouds: bool) -> Frame1x:
    body = a.cell(a.anim, d, i)
    ax, ay = white_pixel(a.cell(a.shad, d, i), a.fw, a.fh)
    disp = (ax - a.fw // 2, ay - (a.fh // 2 + 4))
    canvas = np.zeros((a.fh + 2 * PAD, a.fw + 2 * PAD, 4), np.uint8)
    mask = np.zeros(canvas.shape[:2], bool)
    mask[PAD:PAD + a.fh, PAD:PAD + a.fw] = body[:, :, 3] > 0
    cx, cy = PAD + ax, PAD + ay
    phase = int(4 * t / total) % 4 if total else 0

    def body_paste():
        paste(canvas, FX.aura(mask, phase, dilate), 0, 0)
        paste(canvas, body, PAD, PAD)

    if mask.any():
        if with_clouds:
            draw_clouds(canvas, mask, cx, orbit, clouds, t, total, d, body_paste)
        else:
            body_paste()
    offs = a.cell(a.offs, d, i)
    shad = a.cell(a.shad, d, i)
    marks = [(int(x) - ax, int(y) - ay, tuple(int(v) for v in offs[y, x, :3])) for y, x in np.argwhere(offs[:, :, 3] > 0)]
    template = [(int(x) - ax, int(y) - ay, tuple(int(v) for v in shad[y, x, :3]))
                for y, x in np.argwhere(shad[:, :, 3] > 0) if (int(x), int(y)) != (ax, ay)]
    return Frame1x(canvas, (cx, cy), disp, marks, template)


def fit(frames: list[Frame1x], scale: int) -> tuple[int, int]:
    """Plus petite case (multiple de 8) contenant toutes les images, ancre au repos en (fw/2, fh/2 + 4)."""
    need_w = need_h = 8
    for f in frames:
        ys, xs = np.nonzero(f.img[:, :, 3])
        cx, cy = f.anchor
        rx, ry = cx - f.disp[0], cy - f.disp[1]
        pts_x = [int(xs.min()), int(xs.max()) + 1] if len(xs) else []
        pts_y = [int(ys.min()), int(ys.max()) + 1] if len(ys) else []
        for mx, my, _ in f.marks + f.template:
            pts_x += [cx + mx, cx + mx + 1]
            pts_y += [cy + my, cy + my + 1]
        pts_x += [cx, cx + 1]
        pts_y += [cy, cy + 1]
        left, right = (rx - min(pts_x)) * scale + 1, (max(pts_x) - rx) * scale + 1
        top, bottom = (ry - min(pts_y)) * scale + 1, (max(pts_y) - ry) * scale + 1
        need_w = max(need_w, 2 * max(left, right))
        need_h = max(need_h, 2 * max(top - 4, bottom + 4))
    return -(-need_w // 8) * 8, -(-need_h // 8) * 8


def upscale(img: np.ndarray, scale: int) -> np.ndarray:
    return np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)


def make_cell(f: Frame1x, fw: int, fh: int, scale: int):
    ax, ay = fw // 2 + f.disp[0] * scale, fh // 2 + 4 + f.disp[1] * scale
    anim = np.zeros((fh, fw, 4), np.uint8)
    offs = np.zeros((fh, fw, 4), np.uint8)
    shad = np.zeros((fh, fw, 4), np.uint8)
    ys, xs = np.nonzero(f.img[:, :, 3])
    if len(xs):
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        big = upscale(f.img[y0:y1, x0:x1], scale)
        paste(anim, big, ax + (x0 - f.anchor[0]) * scale, ay + (y0 - f.anchor[1]) * scale)
    for mx, my, rgb in f.marks:
        offs[ay + my * scale, ax + mx * scale] = (*rgb, 255)
    for tx, ty, rgb in f.template:
        y0, x0 = ay + ty * scale, ax + tx * scale
        shad[y0:y0 + scale, x0:x0 + scale] = (*rgb, 255)
    shad[ay:ay + scale, ax:ax + scale] = (0, 255, 0, 255)
    shad[ay, ax] = (255, 255, 255, 255)
    return (anim, offs, shad), (ax, ay)


@dataclass
class Composed:
    name: str
    fw: int
    fh: int
    durations: list[int]
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None
    cells: list[list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = field(default_factory=list)
    anchors: list[list[tuple[int, int]]] = field(default_factory=list)


def build_pack(anims: list[SrcAnim], scale: int, with_clouds: bool) -> dict[str, Composed]:
    width, height = body_size(anims)
    orbit = (width // 2 + 3, max(3, int(round(height / 6))))
    small = width < NARROW or height < 20                    # corps étroit ou bas (Fantyrm, Racaillou) : petits nuages
    clouds = FX.clouds(small=small, dark=darkest_colour(anims))
    comps: dict[str, Composed] = {}
    for a in anims:
        if a.copy_of:
            continue
        total = sum(a.durations)
        frames = []
        for d in range(a.dirs):
            t, row = 0, []
            for i, dur in enumerate(a.durations):
                row.append(compose_frame(a, d, i, orbit, clouds, t, total, with_clouds))
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
        comps[a.name] = comp
    return comps


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def sheet(comp: Composed, which: int) -> np.ndarray:
    dirs, n = len(comp.cells), len(comp.durations)
    canvas = np.zeros((dirs * comp.fh, n * comp.fw, 4), np.uint8)
    for d, row in enumerate(comp.cells):
        for i, cell in enumerate(row):
            canvas[d * comp.fh:(d + 1) * comp.fh, i * comp.fw:(i + 1) * comp.fw] = cell[which]
    return canvas


def save_png(a: np.ndarray, path: Path) -> None:
    """PNG indexé (palette + tRNS) : index 0 = transparent, puis les couleurs opaques (≤ 255) ; mêmes pixels qu'en
    RGBA, fichier bien plus petit. Au-delà de 255 couleurs opaques : RGBA."""
    a = np.ascontiguousarray(a)
    opaque = a[:, :, 3] > 0
    vals = a.view(np.uint32).reshape(a.shape[:2])[opaque]
    uniq = np.unique(vals)
    if len(uniq) > 255:
        Image.fromarray(a, "RGBA").save(path, compress_level=6)
        return
    idx = np.zeros(a.shape[:2], np.uint8)
    idx[opaque] = (np.searchsorted(uniq, vals) + 1).astype(np.uint8)
    rgba = uniq.view(np.uint8).reshape(-1, 4)                 # petit-boutiste : R, G, B, A
    pal = Image.fromarray(idx, "P")
    pal.putpalette([0, 0, 0] + rgba[:, :3].reshape(-1).tolist())
    pal.save(path, compress_level=6, transparency=bytes([0] + rgba[:, 3].tolist()))


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


def source_credit_lines(folder: Path) -> list[str]:
    p = folder / "credits.txt"
    if not p.is_file():
        return []
    return [line for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def licence_of(lines: list[str]) -> str:
    """Licences des contributions en vigueur (statut CUR), dans l'ordre d'apparition, jointes par « + » : un sprite
    SpriteCollab mélange souvent des animations CHUNSOFT (Unspecified) et des ajouts de spriteurs (PMDCollab_1/2,
    CC BY-NC) ; la version dérivée cumule toutes ces conditions."""
    found: list[str] = []
    for status in ("CUR", None):
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 4 and (status is None or parts[2] == status) and parts[3] not in found:
                found.append(parts[3])
        if found:
            break
    return "+".join(found) or "Unspecified"


def write_credits(dex: str, folder: Path, anims: list[SrcAnim], path: Path, scale: int, commit: str, with_clouds: bool) -> str:
    src_lines = source_credit_lines(folder)
    lic = licence_of(src_lines)
    names = ",".join(a.name for a in anims)
    effects = "aura et nuages Dynamax" if with_clouds else "aura Dynamax"
    lines = [
        f"# {name_of(dex)} #{dex} — version Dynamax (agrandissement × {scale}, {effects}), format SpriteCollab : date, auteur, statut, licence, animations",
        f"{time.strftime('%Y-%m-%d')} 00:00:00.000000\tDynamax scripté (source/sprite/build_dynamax.py)\tCUR\t{lic}\t{names}",
        "",
        (f"Sprite d'origine : {folder.relative_to(ROOT)} (sprite du projet, absent de SpriteCollab), crédits repris tels quels :" if dex in LOCAL_SOURCES
         else f"Sprite d'origine : {SPRITECOLLAB}/tree/{commit[:12]}/sprite/{dex} (https://sprites.pmdcollab.org/#/{dex}), crédits repris tels quels :"),
    ]
    lines += ["  " + line for line in src_lines] or ["  (pas de credits.txt dans la source)"]
    lines += [
        "",
        f"Transformation : chaque pixel du sprite d'origine est agrandi × {scale} (aucun pixel du Pokémon redessiné) ; aura rouge animée ajoutée",
        "autour de la silhouette (deux couleurs : (232, 40, 72) et (255, 144, 128))" + (" ; trois nuages rouges tournent au-dessus de la tête" if with_clouds else "") + ".",
        "Toutes les animations d'origine sont reprises avec leurs index, durées, RushFrame / HitFrame / ReturnFrame et déplacements d'ancre (× échelle).",
        f"Licence : {lic} — cette version dérivée suit la ou les licences du sprite d'origine (Unspecified = sprite du jeu, usage de fan non commercial ;",
        "PMDCollab_1 / PMDCollab_2 / CC_BY-NC_4 = usage non commercial avec crédit des auteurs ci-dessus).",
        "Forme non officielle : ce sprite n'a été ni soumis ni approuvé sur SpriteCollab.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lic


# ---------------------------------------------------------------------------
# Une espèce
# ---------------------------------------------------------------------------
def build_species(args: tuple) -> dict:
    dex, source, scale, with_clouds, commit = args
    folder = source_folder(dex, Path(source))
    out = OUT_ROOT / f"{dex}_{slug_of(dex)}"
    try:
        src_shadow, anims = load_source(folder)
        if not any(a.anim is not None for a in anims):
            return {"dex": dex, "erreur": "aucune feuille exploitable"}
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.png"):
            old.unlink()
        comps = build_pack(anims, scale, with_clouds)
        used: set = set()
        cells = 0
        size = 0
        for name, c in comps.items():
            for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
                arr = sheet(c, which)
                p = out / f"{name}-{kind}.png"
                save_png(arr, p)
                size += p.stat().st_size
                if which == 0:
                    used |= set(map(tuple, arr[arr[:, :, 3] > 0][:, :3].tolist()))
            cells += len(c.cells) * len(c.durations)
        write_animdata(anims, comps, out / "AnimData.xml")
        lic = write_credits(dex, folder, anims, out / "credits.txt", scale, commit, with_clouds)
        width, height = body_size(anims)
        walk = comps.get("Walk") or next(iter(comps.values()))
        return {"dex": dex, "nom": name_of(dex), "slug": slug_of(dex), "dossier": out.name, "animations": len(anims),
                "cases": cells, "couleurs": len(used), "corps": [width, height], "case_walk": [walk.fw, walk.fh],
                "petits_nuages": width < NARROW or height < 20, "licence": lic, "octets": size, "shadow_size_origine": src_shadow,
                "origine": str(folder.relative_to(ROOT)) if dex in LOCAL_SOURCES else f"SpriteCollab sprite/{dex}"}
    except Exception as exc:  # noqa: BLE001 — une espèce cassée ne doit pas arrêter le lot
        return {"dex": dex, "erreur": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str]) -> None:
    scale, procs, source, with_clouds = SCALE, 2, DEFAULT_SOURCE, True
    dexes: list[str] = []
    all_species = credits_only = False
    lo = hi = None
    it = iter(argv)
    for arg in it:
        if arg == "--echelle":
            scale = int(next(it))
        elif arg == "--procs":
            procs = int(next(it))
        elif arg == "--source":
            source = Path(next(it))
        elif arg == "--sans-nuages":
            with_clouds = False
        elif arg == "--tous":
            all_species = True
        elif arg == "--credits-seulement":
            credits_only = True
        elif arg == "--de":
            lo = next(it)
        elif arg == "--a":
            hi = next(it)
        else:
            dexes.append(arg.zfill(4))
    commit = ensure_source(source)
    available = list_species(source)
    if all_species or lo or hi:
        dexes = [d for d in available if (lo is None or d >= lo) and (hi is None or d <= hi)]
    if not dexes:
        print(__doc__)
        return
    missing = [d for d in dexes if d not in available]
    if missing:
        print("absents de SpriteCollab :", ", ".join(missing))
    dexes = [d for d in dexes if d in available]
    OUT_ROOT.mkdir(exist_ok=True)
    index_path = OUT_ROOT / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {"source": {}, "especes": {}}
    index["source"] = {"depot": SPRITECOLLAB, "commit": commit, "echelle": scale, "nuages": with_clouds, "shadow_size": SHADOW_SIZE}
    t0 = time.time()
    if credits_only:                                      # réécrit credits.txt et la licence de l'index sans toucher aux feuilles
        for d in dexes:
            r = index["especes"].get(d)
            if not r or "erreur" in r or not (OUT_ROOT / r["dossier"] / "AnimData.xml").is_file():
                continue
            folder = source_folder(d, source)
            _, anims = load_source(folder, light=True)
            r["licence"] = write_credits(d, folder, anims, OUT_ROOT / r["dossier"] / "credits.txt", scale, commit, with_clouds)
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"crédits réécrits pour {len(dexes)} espèces ({time.time() - t0:.0f} s)")
        return
    jobs = [(d, str(source), scale, with_clouds, commit) for d in dexes]
    done = 0
    with Pool(procs) as pool:
        for r in pool.imap_unordered(build_species, jobs, chunksize=1):
            done += 1
            if "erreur" in r:
                print(f"[{done}/{len(jobs)}] {r['dex']} ERREUR {r['erreur']}", flush=True)
            else:
                print(f"[{done}/{len(jobs)}] {r['dex']} {r['nom']} : {r['animations']} anim, {r['cases']} cases, "
                      f"{r['couleurs']} coul., {r['octets'] // 1024} Ko ({time.time() - t0:.0f} s)", flush=True)
            index["especes"][r["dex"]] = r
            if done % 10 == 0 or done == len(jobs):
                index["especes"] = dict(sorted(index["especes"].items()))
                index_path.write_text(json.dumps(index, ensure_ascii=False, indent=0), encoding="utf-8")
    ok = [r for r in index["especes"].values() if "erreur" not in r]
    print(f"{len(ok)} espèces OK, {sum(r['cases'] for r in ok)} cases, {sum(r['octets'] for r in ok) / 1e6:.0f} Mo, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
