#!/usr/bin/env python3
"""Sprite d'escouade Falinks (#0870, forme 0000) au format SpriteCollab / SkyTemple.

PMDCollab publie les deux unités séparément — Brass (0870/0002) et Trooper (0870/0003) —
mais pas la formation complète. Ce script compose l'escouade (1 brass + 5 troopers) :

1. chaque image d'unité est extraite de sa feuille par rapport à son point d'ancrage
   (pixel blanc de la feuille Shadow) ; le déplacement de cet ancrage dans la case
   (charge de l'attaque, secousse, bond) est conservé ;
2. les six unités sont posées en file indienne derrière le brass, orientée selon la
   direction, et dessinées du plus lointain au plus proche ;
3. les feuilles Anim / Offsets / Shadow et AnimData.xml sont réassemblées dans la
   convention des dépôts : cases paires multiples de 8, ancre en (largeur/2, hauteur/2 + 4),
   pixel blanc, gabarit d'ombre 24 × 8, repères tête/centre/mains repris du brass.

Aucun pixel n'est peint : toutes les couleurs viennent des unités d'origine (13 teintes).
Sorties : personnages/falinks/ (feuilles, AnimData.xml, Aseprite animé, variantes nuit,
aperçus, kit.json, credits.txt).
"""
from __future__ import annotations

import json
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
from rebuild_kit import night  # noqa: E402  (même filtre nuit que les salles)

REF = ROOT / "source" / "personnages" / "reference" / "0870"
OUT = ROOT / "personnages" / "falinks"
BRASS, TROOPER = "0002", "0003"

# Ordre des lignes dans les feuilles SpriteCollab.
DIRECTIONS = ["Bas", "Bas-droite", "Droite", "Haut-droite", "Haut", "Haut-gauche", "Gauche", "Bas-gauche"]
FORWARD = {0: (0, 1), 1: (1, 1), 2: (1, 0), 3: (1, -1), 4: (0, -1), 5: (-1, -1), 6: (-1, 0), 7: (-1, 1)}

# ---------------------------------------------------------------------------
# Plan de formation : file indienne, brass en tête, cinq troopers derrière.
# Pas entre deux rangs (px écran) selon l'axe de marche ; léger décalage alterné
# perpendiculaire pour distinguer les casques, choisi pour ne jamais inverser
# l'ordre de profondeur (le rang de derrière reste derrière).
# ---------------------------------------------------------------------------
RANKS = 6
STEP_VERTICAL = 8
STEP_HORIZONTAL = 8
STEP_DIAGONAL = (7, 4)
STAGGER = {0: (2, 0), 4: (2, 0), 2: (0, 0), 6: (0, 0), 1: (0, 0), 7: (0, 0), 3: (0, 0), 5: (0, 0)}
SLEEP_STEP = (16, -10)         # bivouac : écart latéral, recul du second rang
WALK_PHASE_PER_RANK = 1        # décalage de phase (en images) par rang dans la marche
IDLE_WAVE_DELAY = 2            # ticks entre deux rangs dans la vague de l'attente
IDLE_TOTAL = 60                # durée du cycle d'attente (ticks de 1/60 s)
SHADOW_SIZE = 2                # ombre large : la formation couvre deux cases

ANIM_ORDER = [("Walk", 0), ("Attack", 1), ("Strike", 2), ("Shoot", 3), ("Sleep", 5), ("Hurt", 6),
              ("Idle", 7), ("Swing", 8), ("Double", 9), ("Hop", 10), ("Charge", 11), ("Rotate", 12)]
LOCKSTEP = ["Attack", "Swing", "Double", "Hop", "Charge", "Rotate"]
OFFSET_COLOURS = {"head": (0, 0, 0), "center": (0, 255, 0), "lhand": (255, 0, 0), "rhand": (0, 0, 255)}


@dataclass
class UnitFrame:
    image: np.ndarray                 # cellule RGBA complète
    anchor: tuple[int, int]           # pixel blanc dans la cellule
    disp: tuple[int, int]             # ancre - centre de référence de la cellule
    offsets: dict                     # repères relatifs à l'ancre
    bbox: tuple[int, int, int, int]   # contenu relatif à l'ancre (x0, y0, x1, y1 inclus)


@dataclass
class UnitAnim:
    name: str
    fw: int
    fh: int
    durations: list[int]
    frames: list[list[UnitFrame]]     # [direction][image]
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None


@dataclass
class Placement:
    frame: UnitFrame
    x: int                            # ancre de l'unité, relative au centre de la formation
    y: int
    rank: int
    layer: int = 0                    # 1 = étincelles dessinées en dernier


@dataclass
class Composed:
    name: str
    fw: int
    fh: int
    durations: list[int]
    cells: list[list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = field(default_factory=list)
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None
    anchors: list[list[tuple[int, int]]] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Lecture des unités
# ---------------------------------------------------------------------------
def parse_animdata(path: Path) -> dict:
    root = ET.parse(path).getroot()
    anims = {}
    for node in root.find("Anims").iter("Anim"):
        name = node.find("Name").text
        copy = node.find("CopyOf")
        if copy is not None:
            anims[name] = {"copy_of": copy.text}
            continue
        entry = {"fw": int(node.find("FrameWidth").text), "fh": int(node.find("FrameHeight").text),
                 "durations": [int(d.text) for d in node.find("Durations").iter("Duration")]}
        for tag, key in (("RushFrame", "rush"), ("HitFrame", "hit"), ("ReturnFrame", "ret")):
            sub = node.find(tag)
            entry[key] = int(sub.text) if sub is not None else None
        anims[name] = entry
    return anims


def split_cell(sheet: np.ndarray, fw: int, fh: int, d: int, i: int) -> np.ndarray:
    return sheet[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]


def extract(anim: np.ndarray, offs: np.ndarray, shad: np.ndarray, fw: int, fh: int, d: int, i: int) -> UnitFrame:
    cell = split_cell(anim, fw, fh, d, i).copy()
    o = split_cell(offs, fw, fh, d, i)
    s = split_cell(shad, fw, fh, d, i)
    white = np.argwhere((s[:, :, 3] > 0) & (s[:, :, 0] == 255) & (s[:, :, 1] == 255) & (s[:, :, 2] == 255))
    assert len(white) == 1, f"pixel blanc absent ou multiple (dir {d}, image {i})"
    ay, ax = (int(v) for v in white[0])
    disp = (ax - fw // 2, ay - (fh // 2 + 4))
    offsets = {}
    for y, x in np.argwhere(o[:, :, 3] > 0):
        r, g, b = (int(v) for v in o[y, x, :3])
        rel = (int(x) - ax, int(y) - ay)
        if (r, g, b) == (0, 0, 0):
            offsets["head"] = rel
        if g == 255:
            offsets["center"] = rel
        if r == 255:
            offsets["lhand"] = rel
        if b == 255:
            offsets["rhand"] = rel
    assert "center" in offsets, f"centre absent (dir {d}, image {i})"
    offsets.setdefault("head", offsets["center"])
    ys, xs = np.nonzero(cell[:, :, 3])
    bbox = (int(xs.min()) - ax, int(ys.min()) - ay, int(xs.max()) - ax, int(ys.max()) - ay)
    return UnitFrame(cell, (ax, ay), disp, offsets, bbox)


def load_unit(form: str) -> dict[str, UnitAnim]:
    folder = REF / form
    meta = parse_animdata(folder / "AnimData.xml")
    unit = {}
    for name, m in meta.items():
        if "copy_of" in m:
            continue
        anim = np.array(Image.open(folder / f"{name}-Anim.png").convert("RGBA"))
        offs = np.array(Image.open(folder / f"{name}-Offsets.png").convert("RGBA"))
        shad = np.array(Image.open(folder / f"{name}-Shadow.png").convert("RGBA"))
        fw, fh = m["fw"], m["fh"]
        dirs, n = anim.shape[0] // fh, anim.shape[1] // fw
        assert n == len(m["durations"]), name
        frames = [[extract(anim, offs, shad, fw, fh, d, i) for i in range(n)] for d in range(dirs)]
        unit[name] = UnitAnim(name, fw, fh, m["durations"], frames, m["rush"], m["hit"], m["ret"])
    return unit


def split_marks(frame: UnitFrame) -> tuple[UnitFrame, UnitFrame]:
    """Sépare le corps (plus grande composante) des étincelles d'impact de Hurt."""
    alpha = frame.image[:, :, 3] > 0
    labels, n = ndimage.label(alpha)
    sizes = ndimage.sum(alpha, labels, range(1, n + 1))
    body_label = int(np.argmax(sizes)) + 1
    body = frame.image.copy()
    body[labels != body_label] = 0
    marks = frame.image.copy()
    marks[labels == body_label] = 0

    def rebuild(img):
        ys, xs = np.nonzero(img[:, :, 3])
        ax, ay = frame.anchor
        bbox = (int(xs.min()) - ax, int(ys.min()) - ay, int(xs.max()) - ax, int(ys.max()) - ay)
        return UnitFrame(img, frame.anchor, frame.disp, frame.offsets, bbox)

    return rebuild(body), rebuild(marks)


# ---------------------------------------------------------------------------
# Plan de formation
# ---------------------------------------------------------------------------
def formation(direction: int) -> list[tuple[int, int]]:
    """Positions écran des six ancres (rang 0 = brass), relatives au centre de la formation."""
    fx, fy = FORWARD[direction]
    if fx and fy:
        sx, sy = STEP_DIAGONAL
    elif fx:
        sx, sy = STEP_HORIZONTAL, 0
    else:
        sx, sy = 0, STEP_VERTICAL
    px, py = STAGGER[direction]
    positions = []
    for k in range(RANKS):
        side = 0 if k == 0 else (1 if k % 2 else -1)
        positions.append((-k * sx * fx + side * px, -k * sy * fy + side * py))
    cx = round(-(RANKS - 1) / 2 * sx * fx)
    cy = round(-(RANKS - 1) / 2 * sy * fy)
    return [(x - cx, y - cy) for x, y in positions]


def sleep_formation() -> list[tuple[int, int]]:
    """Bivouac : brass au centre du premier rang, deux rangs de trois."""
    sx, dy = SLEEP_STEP
    back = [(-sx, dy), (0, dy), (sx, dy)]
    front = [(-sx, 0), (0, 0), (sx, 0)]
    return [front[1]] + [front[0], front[2]] + back


# ---------------------------------------------------------------------------
# Pistes temporelles : chaque unité suit sa propre séquence, fusionnée ensuite
# ---------------------------------------------------------------------------
def cyclic_track(durations: list[int], start_frame: int, total: int) -> list[tuple[int, int]]:
    events, t, f = [], 0, start_frame % len(durations)
    while t < total:
        events.append((t, f))
        t += durations[f]
        f = (f + 1) % len(durations)
    return events


def sequence_track(durations: list[int], start_tick: int, first_frame: int, pre: int, post: int,
                   total: int) -> list[tuple[int, int]]:
    events, t = [(0, pre)], start_tick
    for k, d in enumerate(durations):
        events.append((t, first_frame + k))
        t += d
    if t < total:
        events.append((t, post))
    return events


def merge_tracks(tracks: list[list[tuple[int, int]]], total: int) -> list[tuple[int, int, list[int]]]:
    """Découpe le temps aux changements d'image : liste de (tick de début, durée, image par piste)."""
    points = sorted({t for track in tracks for t, _ in track if t < total} | {0})
    out = []
    for k, p in enumerate(points):
        nxt = points[k + 1] if k + 1 < len(points) else total
        state = []
        for track in tracks:
            current = track[0][1]
            for t, f in track:
                if t <= p:
                    current = f
            state.append(current)
        out.append((p, nxt - p, state))
    return out


def index_at(merged, tick: int) -> int:
    for i, (start, dur, _) in enumerate(merged):
        if start <= tick < start + dur:
            return i
    return len(merged) - 1


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------
class Composer:
    def __init__(self):
        self.brass = load_unit(BRASS)
        self.trooper = load_unit(TROOPER)
        template = self.brass["Walk"]
        s = np.array(Image.open(REF / BRASS / "Walk-Shadow.png").convert("RGBA"))
        ax, ay = template.frames[0][0].anchor
        self.shadow_template = s[ay - 4:ay + 4, ax - 12:ax + 12].copy()   # 24 × 8, blanc en (12, 4)
        self.palette = self.collect_palette()

    def collect_palette(self) -> set[tuple[int, int, int]]:
        colours = set()
        for unit in (self.brass, self.trooper):
            for anim in unit.values():
                for row in anim.frames:
                    for fr in row:
                        a = fr.image
                        colours |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
        return colours

    # -- plan d'une image de formation ------------------------------------------------
    @staticmethod
    def placements(positions: list[tuple[int, int]], unit_frames: list[UnitFrame],
                   marks: UnitFrame | None = None) -> list[Placement]:
        out = []
        for rank, (fr, (px, py)) in enumerate(zip(unit_frames, positions)):
            out.append(Placement(fr, px + fr.disp[0], py + fr.disp[1], rank))
        if marks is not None:
            bx, by = positions[0]
            out.append(Placement(marks, bx + marks.disp[0], by + marks.disp[1], 0, layer=1))
        # du plus lointain (haut de l'écran) au plus proche ; à égalité, la tête de file dessus
        out.sort(key=lambda p: (p.layer, p.y, -p.rank))
        return out

    @staticmethod
    def extent(pls: list[Placement], anchor: tuple[int, int]) -> tuple[int, int, int, int]:
        xs0, ys0, xs1, ys1 = [], [], [], []
        for p in pls:
            x0, y0, x1, y1 = p.frame.bbox
            xs0.append(p.x + x0); ys0.append(p.y + y0); xs1.append(p.x + x1); ys1.append(p.y + y1)
            for ox, oy in p.frame.offsets.values():
                xs0.append(p.x + ox); ys0.append(p.y + oy); xs1.append(p.x + ox); ys1.append(p.y + oy)
        ax, ay = anchor
        xs0.append(ax - 12); xs1.append(ax + 11); ys0.append(ay - 4); ys1.append(ay + 3)
        return min(xs0), min(ys0), max(xs1), max(ys1)

    def render(self, name: str, plan, durations: list[int], rush=None, hit=None, ret=None, notes="") -> Composed:
        """plan[direction][image] = (placements, déplacement de l'ancre de la formation)."""
        X0 = Y0 = 10 ** 6
        X1 = Y1 = -10 ** 6
        for row in plan:
            for pls, anchor in row:
                x0, y0, x1, y1 = self.extent(pls, anchor)
                X0, Y0, X1, Y1 = min(X0, x0), min(Y0, y0), max(X1, x1), max(Y1, y1)
        half_w = max(-X0, X1 + 1, 12) + 1
        half_h = max(-Y0 - 4, Y1 + 5, 8) + 1
        fw = -(-2 * half_w // 8) * 8
        fh = -(-2 * half_h // 8) * 8
        cx, cy = fw // 2, fh // 2 + 4
        comp = Composed(name, fw, fh, list(durations), rush=rush, hit=hit, ret=ret, notes=notes)
        for row in plan:
            cells, anchors = [], []
            for pls, (adx, ady) in row:
                anim = np.zeros((fh, fw, 4), np.uint8)
                offs = np.zeros((fh, fw, 4), np.uint8)
                shad = np.zeros((fh, fw, 4), np.uint8)
                for p in pls:
                    ax, ay = p.frame.anchor
                    bx0, by0, bx1, by1 = p.frame.bbox
                    img = p.frame.image[ay + by0:ay + by1 + 1, ax + bx0:ax + bx1 + 1]
                    tx, ty = cx + p.x + bx0, cy + p.y + by0
                    h, w = img.shape[:2]
                    assert tx >= 0 and ty >= 0 and tx + w <= fw and ty + h <= fh, (name, "débordement de case")
                    sub = anim[ty:ty + h, tx:tx + w]
                    m = img[:, :, 3] > 0
                    sub[m] = img[m]
                # repères : ceux du brass (rang 0), couleurs additionnées si superposées
                brass_pl = next(p for p in pls if p.rank == 0 and p.layer == 0)
                for key, (ox, oy) in brass_pl.frame.offsets.items():
                    px, py = cx + brass_pl.x + ox, cy + brass_pl.y + oy
                    current = offs[py, px]
                    merged = np.maximum(current[:3], OFFSET_COLOURS[key]) if current[3] else np.array(OFFSET_COLOURS[key])
                    offs[py, px] = (*merged, 255)
                # ombre : gabarit centré sur l'ancre de la formation
                sx, sy = cx + adx - 12, cy + ady - 4
                shad[sy:sy + 8, sx:sx + 24] = self.shadow_template
                cells.append((anim, offs, shad))
                anchors.append((cx + adx, cy + ady))
            comp.cells.append(cells)
            comp.anchors.append(anchors)
        return comp

    # -- animations -------------------------------------------------------------------
    @staticmethod
    def frame(unit_anim: UnitAnim, direction: int, index: int) -> UnitFrame:
        row = unit_anim.frames[direction if len(unit_anim.frames) > 1 else 0]
        return row[index]

    def build_lockstep(self, name: str) -> Composed:
        b, t = self.brass[name], self.trooper[name]
        assert b.durations == t.durations, f"{name} : cadences différentes entre brass et trooper"
        plan = []
        for d in range(8):
            row, positions = [], formation(d)
            for i in range(len(b.durations)):
                bf = self.frame(b, d, i)
                units = [bf] + [self.frame(t, d, i)] * (RANKS - 1)
                row.append((self.placements(positions, units), bf.disp))
            plan.append(row)
        return self.render(name, plan, b.durations, b.rush, b.hit, b.ret,
                           "toute la formation exécute le mouvement à l'unisson (cadence du brass)")

    def build_walk(self) -> Composed:
        b, t = self.brass["Walk"], self.trooper["Walk"]
        assert b.durations == t.durations
        total = sum(b.durations)
        tracks = [cyclic_track(b.durations, k * WALK_PHASE_PER_RANK, total) for k in range(RANKS)]
        merged = merge_tracks(tracks, total)
        plan = []
        for d in range(8):
            row, positions = [], formation(d)
            for _, _, state in merged:
                bf = self.frame(b, d, state[0])
                units = [bf] + [self.frame(t, d, state[k]) for k in range(1, RANKS)]
                row.append((self.placements(positions, units), bf.disp))
            plan.append(row)
        return self.render("Walk", plan, [dur for _, dur, _ in merged],
                           notes=f"pas cadencé en vague : chaque rang a {WALK_PHASE_PER_RANK} image de retard sur le précédent")

    def build_idle(self) -> Composed:
        b, t = self.brass["Idle"], self.trooper["Idle"]
        hold = b.durations[0]
        tracks = [sequence_track(b.durations[1:], hold, 1, 0, 0, IDLE_TOTAL)]
        for j in range(1, RANKS):
            tracks.append(sequence_track(t.durations[1:], hold + IDLE_WAVE_DELAY * j, 1, 0, 0, IDLE_TOTAL))
        merged = merge_tracks(tracks, IDLE_TOTAL)
        plan = []
        for d in range(8):
            row, positions = [], formation(d)
            for _, _, state in merged:
                bf = self.frame(b, d, state[0])
                units = [bf] + [self.frame(t, d, state[k]) for k in range(1, RANKS)]
                row.append((self.placements(positions, units), bf.disp))
            plan.append(row)
        return self.render("Idle", plan, [dur for _, dur, _ in merged],
                           notes=f"garde-à-vous {hold} ticks puis petit bond du brass repris de rang en rang ({IDLE_WAVE_DELAY} ticks d'écart)")

    def build_shoot(self) -> Composed:
        """Cadence du trooper (13 images : élan, tir, recul, retour) ; le brass suit par
        déformation temporelle linéaire de son propre Shoot (regard qui se concentre), calée
        sur le début de l'élan, l'instant de tir et le retour."""
        b, t = self.brass["Shoot"], self.trooper["Shoot"]
        b_starts = [sum(b.durations[:i]) for i in range(len(b.durations))]
        t_starts = [sum(t.durations[:i]) for i in range(len(t.durations))]
        keys = [(0, 0),
                (t_starts[t.hit - 1], b_starts[b.hit]),          # le regard se fige pendant l'élan des troopers
                (t_starts[t.ret], b_starts[b.ret]),
                (sum(t.durations), sum(b.durations))]

        def warp(tick: int) -> float:
            for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
                if tick <= x1:
                    return y0 + (tick - x0) * (y1 - y0) / (x1 - x0)
            return keys[-1][1]

        brass_seq = [max(i for i, start in enumerate(b_starts) if start <= warp(tick)) for tick in t_starts]
        plan = []
        for d in range(8):
            row, positions = [], formation(d)
            for i, bi in enumerate(brass_seq):
                bf = self.frame(b, d, bi)
                units = [bf] + [self.frame(t, d, i)] * (RANKS - 1)
                row.append((self.placements(positions, units), (0, 0)))
            plan.append(row)
        return self.render("Shoot", plan, t.durations, None, t.hit, t.ret,
                           "cadence du trooper (élan, tir, recul, retour) ; le brass fixe la cible, son Shoot est "
                           f"réparti sur ces images : {brass_seq}")

    def build_hurt(self) -> Composed:
        b, t = self.brass["Hurt"], self.trooper["Hurt"]
        assert b.durations == t.durations
        plan = []
        for d in range(8):
            row, positions = [], formation(d)
            for i in range(len(b.durations)):
                body, marks = split_marks(self.frame(b, d, i))
                tbody, _ = split_marks(self.frame(t, d, i))
                units = [body] + [tbody] * (RANKS - 1)
                row.append((self.placements(positions, units, marks), body.disp))
            plan.append(row)
        return self.render("Hurt", plan, b.durations,
                           notes="toutes les unités encaissent ; les étincelles d'impact sont gardées une seule fois, sur le brass")

    def build_sleep(self) -> Composed:
        b, t = self.brass["Sleep"], self.trooper["Sleep"]
        assert b.durations == t.durations
        row, positions = [], sleep_formation()
        for i in range(len(b.durations)):
            bf = b.frames[0][i]
            units = [bf] + [t.frames[0][i]] * (RANKS - 1)
            row.append((self.placements(positions, units), bf.disp))
        return self.render("Sleep", [row], b.durations, notes="bivouac sur deux rangs de trois, brass au centre du premier rang ; une seule direction")

    def build_all(self) -> dict[str, Composed]:
        out = {"Walk": self.build_walk(), "Idle": self.build_idle(), "Shoot": self.build_shoot(),
               "Hurt": self.build_hurt(), "Sleep": self.build_sleep()}
        for name in LOCKSTEP:
            out[name] = self.build_lockstep(name)
        return out


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def sheet(comp: Composed, which: int) -> Image.Image:
    dirs, n = len(comp.cells), len(comp.durations)
    canvas = np.zeros((dirs * comp.fh, n * comp.fw, 4), np.uint8)
    for d, row in enumerate(comp.cells):
        for i, cell in enumerate(row):
            canvas[d * comp.fh:(d + 1) * comp.fh, i * comp.fw:(i + 1) * comp.fw] = cell[which]
    return Image.fromarray(canvas, "RGBA")


def write_animdata(comps: dict[str, Composed], path: Path) -> None:
    lines = ['<?xml version="1.0" ?>', "<AnimData>", f"\t<ShadowSize>{SHADOW_SIZE}</ShadowSize>", "\t<Anims>"]
    for name, index in ANIM_ORDER:
        lines += ["\t\t<Anim>", f"\t\t\t<Name>{name}</Name>", f"\t\t\t<Index>{index}</Index>"]
        if name == "Strike":
            lines += ["\t\t\t<CopyOf>Attack</CopyOf>", "\t\t</Anim>"]
            continue
        c = comps[name]
        lines += [f"\t\t\t<FrameWidth>{c.fw}</FrameWidth>", f"\t\t\t<FrameHeight>{c.fh}</FrameHeight>"]
        for tag, value in (("RushFrame", c.rush), ("HitFrame", c.hit), ("ReturnFrame", c.ret)):
            if value is not None:
                lines.append(f"\t\t\t<{tag}>{value}</{tag}>")
        lines.append("\t\t\t<Durations>")
        lines += [f"\t\t\t\t<Duration>{d}</Duration>" for d in c.durations]
        lines += ["\t\t\t</Durations>", "\t\t</Anim>"]
    lines += ["\t</Anims>", "</AnimData>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# -- Aseprite animé : calques = directions, images = toutes les animations, étiquettes --
def _astr(text: str) -> bytes:
    data = text.encode()
    return struct.pack("<H", len(data)) + data


def _chunk(kind: int, data: bytes) -> bytes:
    return struct.pack("<IH", len(data) + 6, kind) + data


def write_aseprite(comps: dict[str, Composed], path: Path) -> dict:
    W = max(c.fw for c in comps.values())
    H = max(c.fh for c in comps.values())
    order = [n for n, _ in ANIM_ORDER if n != "Strike"]
    frames, tags, cursor = [], [], 0
    for name in order:
        c = comps[name]
        n = len(c.durations)
        for i in range(n):
            cels = []
            for d in range(8):
                if d < len(c.cells):
                    cels.append(Image.fromarray(c.cells[d][i][0], "RGBA"))
                else:
                    cels.append(None)
            frames.append((round(c.durations[i] * 1000 / 60), cels, (W - c.fw) // 2, (H - c.fh) // 2))
        tags.append((cursor, cursor + n - 1, name))
        cursor += n

    layer_chunks = b"".join(_chunk(0x2004, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + _astr(label))
                            for label in DIRECTIONS)
    tag_data = struct.pack("<H", len(tags)) + b"\0" * 8
    for start, end, label in tags:
        tag_data += struct.pack("<HHBH", start, end, 0, 0) + b"\0" * 6 + bytes((230, 180, 60)) + b"\0" + _astr(label)
    tag_chunk = _chunk(0x2018, tag_data)

    body = b""
    for k, (duration, cels, ox, oy) in enumerate(frames):
        chunks = []
        if k == 0:
            chunks.append(layer_chunks)
            chunks.append(tag_chunk)
        for layer, im in enumerate(cels):
            if im is None:
                continue
            box = im.getbbox()
            if not box:
                continue
            x, y = box[0] + ox, box[1] + oy
            q = im.crop(box)
            data = struct.pack("<HhhBHh", layer, x, y, 255, 2, 0) + b"\0" * 5
            data += struct.pack("<HH", q.width, q.height) + zlib.compress(q.tobytes(), 9)
            chunks.append(_chunk(0x2005, data))
        n_chunks = len(chunks) - 1 + len(DIRECTIONS) if k == 0 else len(chunks)   # layer_chunks contient 8 chunks
        data = b"".join(chunks)
        body += struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA, min(n_chunks, 0xFFFF), duration, b"\0\0", n_chunks) + data
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(body) + 128, 0xA5E0, len(frames), W, H, 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.write_bytes(header + body)
    return {"canvas": [W, H], "images": len(frames), "calques": DIRECTIONS, "etiquettes": [t[2] for t in tags],
            "ancre": [W // 2, H // 2 + 4]}


def font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def ground_shadow(draw: ImageDraw.ImageDraw, x: int, y: int, zoom: int) -> None:
    draw.ellipse([x - 12 * zoom, y - 4 * zoom, x + 11 * zoom, y + 3 * zoom], fill=(40, 24, 8, 90))


def cell_image(c: Composed, d: int, i: int, zoom: int, bg=(26, 26, 46, 255), shadow=True) -> Image.Image:
    img = Image.new("RGBA", (c.fw * zoom, c.fh * zoom), bg)
    if shadow:
        ax, ay = c.anchors[d][i]
        ground_shadow(ImageDraw.Draw(img), ax * zoom, ay * zoom, zoom)
    cell = Image.fromarray(c.cells[d][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
    img.alpha_composite(cell)
    return img


def contact_sheet(comps: dict[str, Composed], path: Path) -> None:
    """Toutes les animations, direction Bas (et Droite pour la marche), toutes les images, × 2."""
    zoom = 2
    blocks = []
    for name, _ in ANIM_ORDER:
        if name == "Strike":
            continue
        c = comps[name]
        dirs = [0, 2] if name in ("Walk", "Attack") and len(c.cells) > 1 else [0]
        n = len(c.durations)
        img = Image.new("RGBA", (n * (c.fw * zoom + 2) + 8, len(dirs) * (c.fh * zoom + 2) + 26), (26, 26, 46, 255))
        d = ImageDraw.Draw(img)
        extra = "".join(f" · {k} {v}" for k, v in (("Rush", c.rush), ("Hit", c.hit), ("Return", c.ret)) if v is not None)
        d.text((4, 4), f"{name} — case {c.fw} × {c.fh}, {n} images, {len(c.cells)} direction(s), durées {c.durations}{extra}",
               fill=(230, 230, 230, 255), font=font(12))
        for r, dd in enumerate(dirs):
            for i in range(n):
                img.alpha_composite(cell_image(c, dd, i, zoom, (36, 36, 60, 255)), (4 + i * (c.fw * zoom + 2), 26 + r * (c.fh * zoom + 2)))
        blocks.append(img)
    W = max(b.width for b in blocks)
    H = sum(b.height + 6 for b in blocks) + 64
    out = Image.new("RGBA", (W + 16, H), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), "FALINKS #0870 — SPRITE D'ESCOUADE, FORMAT SPRITECOLLAB (× 2)", fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 36), "Composé à partir des unités Brass et Trooper publiées sur PMDCollab · Idle, Walk, Attack : ligne 1 = Bas, ligne 2 = Droite",
           fill=(170, 170, 200, 255), font=font(12))
    y = 64
    for b in blocks:
        out.alpha_composite(b, (8, y))
        y += b.height + 6
    out.save(path, optimize=True)


def directions_sheet(comps: dict[str, Composed], path: Path) -> None:
    zoom = 4
    c = comps["Walk"]
    cw, ch = c.fw * zoom + 6, c.fh * zoom + 22
    out = Image.new("RGBA", (8 * cw + 6, ch + 40), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 8), "Walk, image 1 — les huit directions (× 4), ombre du jeu sous l'ancre", fill=(240, 240, 240, 255), font=font(14))
    for dd in range(8):
        out.alpha_composite(cell_image(c, dd, 0, zoom, (36, 36, 60, 255)), (6 + dd * cw, 40))
        d.text((6 + dd * cw + 4, 40 + c.fh * zoom + 4), DIRECTIONS[dd], fill=(200, 200, 220, 255), font=font(12))
    out.save(path, optimize=True)


def parquet_background(size: tuple[int, int], zoom: int) -> Image.Image:
    """Fond de contrôle : parquet de la salle d'accueil de la guilde, à la même échelle que le sprite,
    légèrement assombri pour que les jaunes du sprite ressortent."""
    src = ROOT / "salles" / "01_accueil" / "salle_jour.png"
    bg = Image.new("RGBA", size, (150, 104, 52, 255))
    if src.is_file():
        tile = Image.open(src).convert("RGBA").crop((264, 252, 392, 316))
        a = np.array(tile).astype(np.int16)
        a[:, :, :3] = (a[:, :, :3] * 0.72).clip(0, 255)
        tile = Image.fromarray(a.astype(np.uint8), "RGBA")
        tile = tile.resize((tile.width * zoom, tile.height * zoom), Image.NEAREST)
        for y in range(0, size[1], tile.height):
            for x in range(0, size[0], tile.width):
                bg.alpha_composite(tile, (x, y))
    return bg


def gif(comps: dict[str, Composed], names: list[str], directions: list[int], path: Path, zoom: int = 3, span: int = 240) -> None:
    """Animation de contrôle : une case par direction, ancre fixe, sur le parquet de la guilde."""
    cw = max(comps[n].fw for n in names) * zoom + 8
    ch = max(comps[n].fh for n in names) * zoom + 8
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
        d = ImageDraw.Draw(img)
        for r, n in enumerate(names):
            c = comps[n]
            i = max(i for tt, i in tick_frames[n] if tt <= t)
            for col, direction in enumerate(directions):
                dd = direction if len(c.cells) > 1 else 0
                cell = Image.fromarray(c.cells[dd][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
                ax, ay = c.anchors[dd][i]
                cx, cy = col * cw + cw // 2, r * ch + ch * 2 // 3
                ground_shadow(d, cx, cy, zoom)
                img.alpha_composite(cell, (cx - ax * zoom, cy - ay * zoom))
        frames_out.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations_out.append(int(round((nxt - t) * 1000 / 60)))
    frames_out[0].save(path, save_all=True, append_images=frames_out[1:], duration=durations_out, loop=0, optimize=True)


def player_html(comps: dict[str, Composed], path: Path) -> None:
    manifest = {}
    for name, c in comps.items():
        manifest[name] = {"fw": c.fw, "fh": c.fh, "durations": c.durations, "dirs": len(c.cells),
                          "anchors": c.anchors, "hit": c.hit, "rush": c.rush, "ret": c.ret}
    names = [n for n, _ in ANIM_ORDER if n != "Strike"]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Falinks — sprite d'escouade PMD</title>
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
<header><h1>Falinks #0870 — sprite d'escouade, format SpriteCollab</h1>
<p>Lecture hors ligne des feuilles <code>*-Anim.png</code>. Les images sont alignées sur le pixel blanc de <code>*-Shadow.png</code>, comme dans le jeu. Case du donjon = 24 px.</p></header>
<div class="bar">
<label>Animation <select id="anim">{''.join(f'<option>{n}</option>' for n in names)}</select></label>
<label>Zoom <input id="zoom" type="range" min="2" max="8" value="4"></label>
<label><input id="shadow" type="checkbox" checked> ombre</label>
<label><input id="offsets" type="checkbox"> repères</label>
<label><input id="grid" type="checkbox" checked> grille 24 px</label>
<button id="pause">Pause</button>
<span id="info"></span>
</div>
<div class="grid" id="grid8"></div>
<script>
const M = {json.dumps(manifest)};
const DIRS = {json.dumps(DIRECTIONS)};
const sheets = {{}};
function load(name, kind) {{
  const key = name + kind; if (sheets[key]) return sheets[key];
  const im = new Image(); im.src = name + '-' + kind + '.png'; sheets[key] = im; return im;
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
  const anim = load(name, 'Anim'), offs = load(name, 'Offsets');
  const now = paused ? pauseAt : performance.now();
  const ticks = Math.floor((now - t0) / 1000 * 60);
  const i = frameAt(m, ticks);
  const W = Math.max(m.fw, 48) * z, H = Math.max(m.fh, 48) * z;
  for (let d = 0; d < 8; d++) {{
    const c = cvs[d]; c.width = W; c.height = H; const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
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
      g.ellipse(ox + ax * z, oy + ay * z, 12 * z, 4 * z, 0, 0, Math.PI * 2); g.fill();
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


def write_credits(path: Path) -> None:
    lines = [
        "# Falinks #0870 forme 0000 (escouade) — crédits, format proche de SpriteCollab : date, auteur, statut, licence, animations",
        "2023-01-04 01:46:59.676997\t<@!215638650434617345>\tCUR\tPMDCollab_1\tIdle,Walk,Sleep,Hurt,Attack,Charge,Shoot,Strike,Swing,Double,Rotate,Hop",
        "2024-12-22 02:08:38.853154\t<@!544245909639397378>\tCUR\tCC_BY-NC_4\tIdle,Walk,Sleep,Hurt,Attack,Charge,Shoot,Strike,Twirl,Swing,Double,Rotate,Hop",
        "2024-12-27 20:18:49.561449\t<@!544245909639397378>\tCUR\tCC_BY-NC_4\tCharge,Double",
        "2026-09-06 00:00:00.000000\tGuilde Treehouse (composition scriptée, aucun pixel repeint)\tCUR\tCC_BY-NC_4\tIdle,Walk,Sleep,Hurt,Attack,Charge,Shoot,Strike,Swing,Double,Rotate,Hop",
        "",
        "Unité Brass 0870/0002 : ◥θ┴θ◤ (<@!215638650434617345>), licence PMDCollab_1 — https://sprites.pmdcollab.org/#/0870?form=2",
        "Unité Trooper 0870/0003 : baronessfaron (<@!544245909639397378>), licence CC BY-NC 4.0 — https://sprites.pmdcollab.org/#/0870?form=3",
        "L'escouade hérite de la licence la plus restrictive (CC BY-NC 4.0) : usage, copie et modification autorisés avec crédit aux deux auteurs, hors usage commercial.",
        "La forme 0000 n'existe pas sur le dépôt SpriteCollab ; cette composition n'y a été ni soumise ni approuvée.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nuit").mkdir(exist_ok=True)
    composer = Composer()
    comps = composer.build_all()
    for name, c in comps.items():
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            sheet(c, which).save(OUT / f"{name}-{kind}.png", optimize=True)
        night(sheet(c, 0)).save(OUT / "nuit" / f"{name}-Anim.png", optimize=True)
    write_animdata(comps, OUT / "AnimData.xml")
    ase_info = write_aseprite(comps, OUT / "falinks.aseprite")
    contact_sheet(comps, OUT / "apercu.png")
    directions_sheet(comps, OUT / "apercu_directions.png")
    gif(comps, ["Walk", "Idle"], [0, 2, 4, 6], OUT / "apercu_marche_attente.gif")
    gif(comps, ["Attack", "Hurt"], [0, 2, 4, 6], OUT / "apercu_attaque.gif")
    player_html(comps, OUT / "apercu.html")
    write_credits(OUT / "credits.txt")

    used = set()
    for c in comps.values():
        for row in c.cells:
            for cell in row:
                a = cell[0]
                used |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
    kit = {
        "pokemon": {"numero": "0870", "nom": "Falinks", "forme": "0000", "unites": {"brass": "0870/0002", "trooper": "0870/0003"}},
        "format": {"convention": "SpriteCollab / SkyTemple : <Anim>-Anim.png, <Anim>-Offsets.png, <Anim>-Shadow.png + AnimData.xml",
                   "directions": DIRECTIONS, "ancre": "pixel blanc de Shadow, en (largeur/2, hauteur/2 + 4) au repos",
                   "shadow_size": SHADOW_SIZE, "reperes": "tête (noir), centre (vert), main gauche (rouge), main droite (bleu), repris du brass",
                   "cases": "paires, multiples de 8"},
        "formation": {"rangs": RANKS, "pas_vertical": STEP_VERTICAL, "pas_horizontal": STEP_HORIZONTAL, "pas_diagonal": list(STEP_DIAGONAL),
                      "decalage_alterne": {DIRECTIONS[d]: list(v) for d, v in STAGGER.items()},
                      "positions_par_direction": {DIRECTIONS[d]: formation(d) for d in range(8)},
                      "sommeil": {"pas": list(SLEEP_STEP), "positions": sleep_formation()},
                      "ordre_de_dessin": "du plus lointain (haut) au plus proche (bas) ; à égalité la tête de file au-dessus"},
        "animations": {name: {"index": dict(ANIM_ORDER)[name], "case": [c.fw, c.fh], "images": len(c.durations),
                              "directions": len(c.cells), "durees": c.durations, "ticks": sum(c.durations),
                              "rush": c.rush, "hit": c.hit, "return": c.ret, "composition": c.notes}
                       for name, c in comps.items()},
        "copies": {"Strike": "Attack"},
        "aseprite": ase_info,
        "nuit": "nuit/<Anim>-Anim.png : même filtre que les salles (source/rebuild_kit.py night) ; Offsets et Shadow inchangés",
        "palette": sorted("#%02x%02x%02x" % c for c in used),
        "couleurs": len(used),
    }
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(comps)} animations composées (+ Strike), {len(used)} couleurs, exportées dans {OUT.relative_to(ROOT)}")
    for name, _ in ANIM_ORDER:
        if name in comps:
            c = comps[name]
            print(f"  {name:8s} {c.fw:3d} × {c.fh:3d}  {len(c.durations):2d} images  {len(c.cells)} dir  {sum(c.durations):3d} ticks  durées {c.durations}")


if __name__ == "__main__":
    main()
