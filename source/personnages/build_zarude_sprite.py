#!/usr/bin/env python3
"""Sprite Zarude (#0893) au format SpriteCollab / SkyTemple, sur le squelette d'animation de Rillaboom.

Zarude n'existe pas sur PMDCollab : le dessin est original (pièces de pixel art 1:1 dans
`zarude_pieces.py`, 13 couleurs). Pour rester dans la convention des sprites du dépôt, on
**recopie le squelette** du sprite de Rillaboom #0812 (baronessfaron, CC BY-NC 4.0) :

- mêmes animations (set donjon complet, Sing compris), mêmes cases, mêmes durées,
  mêmes RushFrame / HitFrame / ReturnFrame ;
- même déplacement du point d'ancrage à chaque image (charge de l'attaque, secousse,
  cercle de Swing, aller-retour de Double, saut de Hop), lu directement dans les feuilles
  `*-Shadow.png` de la référence (`source/personnages/reference/0812/`) ;
- même gabarit d'ombre 24 × 8 (ShadowSize 2), mêmes couleurs de repères ;
- pour Swing et Rotate, même sens de rotation : l'image i regarde la direction (d − i) mod 8.

Aucun pixel de Rillaboom n'est copié : ses feuilles servent de plan (cases, ancres, timing).

Les cinq orientations Bas, Bas-droite, Droite, Haut-droite, Haut sont dessinées ; Gauche,
Haut-gauche et Bas-gauche sont des miroirs autour de la colonne de l'ancre (comme les
sprites officiels). Chaque image est un assemblage de pièces (tête, crinière, torse, bras,
jambes, queue, lianes) déplacées de quelques pixels : la cohérence entre images est mécanique.

Sorties : personnages/zarude/ (feuilles, AnimData.xml, Aseprite, variantes nuit, aperçus,
kit.json, credits.txt).
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
from rebuild_kit import night  # noqa: E402
from build_falinks_sprite import (  # noqa: E402  (pipeline commun aux sprites du kit)
    DIRECTIONS, OFFSET_COLOURS, Composed, font, parquet_background, sheet, write_aseprite,
)
import zarude_pieces as P  # noqa: E402

REF = ROOT / "source" / "personnages" / "reference" / "0812"      # Rillaboom : squelette
OUT = ROOT / "personnages" / "zarude"
SHADOW_SIZE = 2
ANIM_ORDER = [("Walk", 0), ("Attack", 1), ("Strike", 2), ("Shoot", 3), ("Sing", 4), ("Sleep", 5), ("Hurt", 6),
              ("Idle", 7), ("Swing", 8), ("Double", 9), ("Hop", 10), ("Charge", 11), ("Rotate", 12)]
SPIN = ("Swing", "Rotate")          # l'image i regarde (d - i) mod 8
HOP_LIFT = [0, 10, 16, 20, 21, 23, 22, 18, 12, 0]      # hauteur du corps au-dessus du sol, relevée sur Rillaboom
HOP_POSE = ["crouch", "rest", "rest", "rest", "rest", "crouch", "crouch", "crouch", "crouch", "rest"]
MIRROR = {5: 3, 6: 2, 7: 1}


# ---------------------------------------------------------------------------
# Squelette : AnimData et déplacements d'ancre de la référence
# ---------------------------------------------------------------------------
def parse_animdata(path: Path) -> tuple[int, dict]:
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
    return int(root.find("ShadowSize").text), anims


def anchor_displacements(name: str, fw: int, fh: int) -> list[list[tuple[int, int]]]:
    """disp[d][i] = ancre de la référence − centre de la case (fw/2, fh/2 + 4)."""
    s = np.array(Image.open(REF / f"{name}-Shadow.png").convert("RGBA"))
    dirs, n = s.shape[0] // fh, s.shape[1] // fw
    out = []
    for d in range(dirs):
        row = []
        for i in range(n):
            cell = s[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
            white = np.argwhere((cell[:, :, 3] > 0) & np.all(cell[:, :, :3] == 255, axis=2))
            assert len(white) == 1, (name, d, i)
            y, x = (int(v) for v in white[0])
            row.append((x - fw // 2, y - (fh // 2 + 4)))
        out.append(row)
    return out


def shadow_template() -> np.ndarray:
    s = np.array(Image.open(REF / "Walk-Shadow.png").convert("RGBA"))
    return s[32:40, 12:36].copy()          # 24 × 8, blanc en (12, 4)


# ---------------------------------------------------------------------------
# Pièces articulées
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Arm:
    img: np.ndarray
    fist: tuple[int, int]
    shoulder: tuple[int, int]

    def flipped(self) -> "Arm":
        w = self.img.shape[1]
        return Arm(P.flip(self.img), (w - 1 - self.fist[0], self.fist[1]), (w - 1 - self.shoulder[0], self.shoulder[1]))

    def darker(self) -> "Arm":
        return Arm(P.darker(self.img), self.fist, self.shoulder)

    def shortened(self, n: int) -> "Arm":
        if n <= 0:
            return self
        keep = min(self.shoulder[1], self.fist[1]) + 1     # on retire des lignes entre l'épaule et le poing
        img = P.shorten(self.img, n, keep_top=keep)
        fx, fy = self.fist
        sx, sy = self.shoulder
        return Arm(img, (fx, fy - n if fy > sy else fy), (sx, sy - n if sy > fy else sy))


def arm_set(prefix: str) -> dict[str, Arm]:
    g = vars(P)
    return {kind: Arm(g[f"{name}_{prefix}"], g[f"{name}_{prefix}_FIST"], g[f"{name}_{prefix}_SHOULDER"])
            for kind, name in (("rest", "ARM"), ("up", "ARM_UP"), ("out", "ARM_OUT"), ("beat", "ARM_BEAT"), ("push", "ARM_PUSH"))}


ARMS = {0: arm_set("0"), 2: arm_set("2"), 4: arm_set("4")}


@dataclass
class Piece:
    name: str
    img: np.ndarray
    x: int
    y: int
    z: int


# Spécification de la pose de repos pour chaque orientation dessinée.
#   arms : nom -> (famille de bras, épaule (x, y), z, miroir ?, éloigné ?)
#   red  : bras portant le repère « main gauche » (rouge) — même convention que la référence :
#          de face le poing à gauche de l'écran, de dos celui de droite, de profil le poing éloigné.
#   front : direction écran « devant le personnage » (griffures de l'attaque, ondes du hurlement).
SPECS = {
    0: dict(head=(P.HEAD_0, P.HEAD_0_MARK, (-12, -32), 5), mane=(P.MANE_0, (-13, -25), 4),
            torso=(P.TORSO_0, P.TORSO_0_CENTER, (-6, -20), 3), tail=(P.TAIL_0, (10, -22), 0),
            legs={"legL": (P.LEG_0, (-7, -9), 1, False, False), "legR": (P.LEG_0, (2, -9), 1, True, False)},
            arms={"armL": (0, (-5, -18), 6, False, False), "armR": (0, (5, -18), 6, True, False)},
            red="armL", slash=(0, 6), howl=[((-18, -30), False), ((15, -30), True)], sparks=[(-15, -28), (15, -31)]),
    1: dict(head=(P.HEAD_1, P.HEAD_1_MARK, (-11, -32), 5), mane=(P.MANE_0, (-13, -25), 4),
            torso=(P.TORSO_1, P.TORSO_1_CENTER, (-6, -20), 3), tail=(P.TAIL_1, (7, -23), 0),
            legs={"legL": (P.LEG_0, (-7, -9), 2, False, False), "legR": (P.LEG_0, (2, -10), 1, True, True)},
            arms={"armL": (0, (-5, -18), 6, False, False), "armR": (0, (5, -20), 1, True, True)},
            red="armR", slash=(9, 3), howl=[((-18, -30), False), ((15, -30), True)], sparks=[(-15, -28), (15, -31)]),
    2: dict(head=(P.HEAD_2, P.HEAD_2_MARK, (-2, -32), 5), mane=(P.MANE_2, (-10, -30), 4), vines=(P.VINES_2, (-9, -24), 4),
            torso=(P.TORSO_2, P.TORSO_2_CENTER, (-9, -21), 3), tail=(P.TAIL_2, (-18, -25), 0),
            legs={"legL": (P.LEG_2, (-8, -13), 1, False, True), "legR": (P.LEG_2, (-3, -12), 2, False, False)},
            arms={"armL": (2, (-1, -21), 1, False, True), "armR": (2, (2, -20), 6, False, False)},
            red="armL", slash=(16, -2), howl=[((17, -27), True)], sparks=[(-6, -30), (18, -29)]),
    3: dict(head=(P.HEAD_3, P.HEAD_3_MARK, (-12, -32), 5), mane=(P.MANE_0, (-13, -25), 4),
            vines=(P.VINES_3, (-8, -26), 6),
            torso=(P.TORSO_4, P.TORSO_4_CENTER, (-6, -20), 3), tail=(P.TAIL_3, (-16, -16), 7),
            legs={"legL": (P.LEG_4, (-7, -9), 2, False, False), "legR": (P.LEG_4, (2, -10), 1, True, True)},
            arms={"armL": (4, (-5, -18), 2, False, False), "armR": (4, (5, -20), 1, True, True)},
            red="armL", slash=(8, -24), howl=[((-18, -30), False), ((15, -30), True)], sparks=[(-15, -28), (15, -31)]),
    4: dict(head=(P.HEAD_4, P.HEAD_4_MARK, (-12, -32), 5), mane=(P.MANE_0, (-13, -25), 4),
            vines=(P.VINES_4, (-5, -26), 6),
            torso=(P.TORSO_4, P.TORSO_4_CENTER, (-6, -20), 3), tail=(P.TAIL_4, (2, -16), 7),
            legs={"legL": (P.LEG_4, (-7, -9), 1, False, False), "legR": (P.LEG_4, (2, -9), 1, True, False)},
            arms={"armL": (4, (-5, -18), 2, False, False), "armR": (4, (5, -18), 2, True, False)},
            red="armR", slash=(0, -26), howl=[((-18, -30), False), ((15, -30), True)], sparks=[(-15, -28), (15, -31)]),
}

# Pas de marche : décalage (dx, dy) des jambes et des bras selon la famille d'orientation.
#   image 1 : jambe gauche avance, bras droit avance ; image 3 : l'inverse.
WALK = {
    "front": {"fwd_leg": (0, 2), "back_leg": (0, -1), "fwd_arm": (-2, 2, 0), "back_arm": (1, 0, 2)},
    "side": {"fwd_leg": (3, 0), "back_leg": (-2, 0), "fwd_arm": (3, 0, 1), "back_arm": (-3, 0, 1)},
    "back": {"fwd_leg": (0, -1), "back_leg": (0, 2), "fwd_arm": (-2, 0, 2), "back_arm": (1, 2, 0)},
}
FAMILY = {0: "front", 1: "front", 2: "side", 3: "back", 4: "back"}


def howl_mark(flipped: bool) -> np.ndarray:
    return P.flip(P.HOWL) if flipped else P.HOWL


def assemble(facing: int, pose: str = "rest", lift: int = 0, extras: list | None = None) -> tuple[list[Piece], dict]:
    """Pièces (coordonnées relatives à l'ancre) et repères d'une pose, pour une orientation dessinée (0-4)."""
    spec = SPECS[facing]
    fam = FAMILY[facing]
    body = [0, 0]                     # décalage du haut du corps (tête, crinière, torse, queue, épaules)
    leg_off = {"legL": (0, 0), "legR": (0, 0)}
    leg_short = {"legL": 0, "legR": 0}
    arm_kind = {"armL": "rest", "armR": "rest"}
    arm_off = {"armL": (0, 0), "armR": (0, 0)}
    arm_short = {"armL": 0, "armR": 0}
    arm_flip = {"armL": False, "armR": False}      # retournement supplémentaire (bras rejetés en arrière)
    head_off = (0, 0)
    extras = list(extras or [])

    if pose in ("walk1", "walk3"):
        w = WALK[fam]
        fwd, back = ("legL", "legR") if pose == "walk1" else ("legR", "legL")
        leg_off[fwd], leg_off[back] = w["fwd_leg"], w["back_leg"]
        fa, ba = ("armR", "armL") if pose == "walk1" else ("armL", "armR")
        arm_off[fa], arm_short[fa] = w["fwd_arm"][:2], w["fwd_arm"][2]
        arm_off[ba], arm_short[ba] = w["back_arm"][:2], w["back_arm"][2]
        body[1] += 1
        leg_short = {k: 1 for k in leg_short}
    elif pose in ("crouch", "slam", "push", "double"):
        body[1] += 2
        leg_short = {k: 2 for k in leg_short}
        arm_short = {k: 2 for k in arm_short}
        if pose == "slam":
            arm_kind = {k: "rest" for k in arm_kind}
            for k in arm_off:
                sx = spec["arms"][k][1][0]
                arm_off[k] = (-2 if sx < 0 else 2 if sx > 0 else 0, 1) if fam != "side" else (3, 1)
                arm_short[k] = 3
        elif pose == "push":
            arm_kind = {k: "push" for k in arm_kind}
            arm_short = {k: 0 for k in arm_short}
            if fam == "side":                      # bras tendus à hauteur du poitrail, sous le museau
                arm_off = {"armL": (-1, 2), "armR": (1, 5)}
    elif pose in ("windup", "raise"):
        arm_kind = {k: "up" for k in arm_kind}
        if pose == "raise":                        # bras à demi levés : tient dans les cases 48 × 64 de la référence
            arm_short = {k: 4 for k in arm_short}
    elif pose == "howl":
        arm_kind = {k: "up" for k in arm_kind}
        arm_short = {k: 4 for k in arm_short}
        head_off = (0, -1)
        for (hx, hy), fl in spec["howl"]:
            extras.append((howl_mark(fl), hx, hy, 9))
    elif pose in ("beatL", "beatR"):
        arm_kind[pose[-1:].join(["arm", ""])] = "beat"
    elif pose == "hurt":
        arm_kind = {k: "out" for k in arm_kind}
        if fam == "side":                          # de profil : bras rejetés en arrière
            arm_flip = {"armL": True, "armR": True}
            arm_off = {"armL": (0, -3), "armR": (0, -1)}
        head_off = (0, 1)
        for sx, sy in spec["sparks"]:
            extras.append((P.bmp(["W"]), sx, sy, 9))
    elif pose == "rest":
        pass
    else:
        raise ValueError(pose)

    pieces: list[Piece] = []
    bx, by = body
    img, mark, (x, y), z = spec["head"]
    pieces.append(Piece("head", img, x + bx + head_off[0], y + by + head_off[1] - lift, z))
    marks = {"head": (x + bx + head_off[0] + mark[0], y + by + head_off[1] + mark[1] - lift)}
    img, (x, y), z = spec["mane"]
    pieces.append(Piece("mane", img, x + bx, y + by - lift, z))
    if "vines" in spec:
        img, (x, y), z = spec["vines"]
        pieces.append(Piece("vines", img, x + bx, y + by - lift, z))
    img, centre, (x, y), z = spec["torso"]
    pieces.append(Piece("torso", img, x + bx, y + by - lift, z))
    marks["center"] = (x + bx + centre[0], y + by + centre[1] - lift)
    img, (x, y), z = spec["tail"]
    pieces.append(Piece("tail", img, x + bx, y + by - lift, z))
    for name, (img, (x, y), z, fl, far) in spec["legs"].items():
        leg = P.flip(img) if fl else img
        leg = P.darker(leg) if far else leg
        leg = P.shorten(leg, leg_short[name], keep_top=1)
        dx, dy = leg_off[name]
        dx = -dx if fl else dx
        pieces.append(Piece(name, leg, x + dx, y + dy + leg_short[name] - lift, z))
    fists = {}
    for name, (family, (sx, sy), z, fl, far) in spec["arms"].items():
        arm = ARMS[family][arm_kind[name]]
        if fl != arm_flip[name]:
            arm = arm.flipped()
        if far:
            arm = arm.darker()
        arm = arm.shortened(arm_short[name])
        dx, dy = arm_off[name]
        dx = -dx if fl else dx
        px, py = sx + bx + dx - arm.shoulder[0], sy + by + dy - arm.shoulder[1] - lift
        pieces.append(Piece(name, arm.img, px, py, z))
        fists[name] = (px + arm.fist[0], py + arm.fist[1])
    red = spec["red"]
    blue = "armR" if red == "armL" else "armL"
    marks["lhand"], marks["rhand"] = fists[red], fists[blue]
    for k, (img, cx, cy, z) in enumerate(extras):
        pieces.append(Piece(f"fx{k}", img, cx - img.shape[1] // 2, cy - img.shape[0] // 2, z))
    return pieces, marks


def flatten(pieces: list[Piece]) -> tuple[np.ndarray, tuple[int, int]]:
    """Image locale (RGBA) et coin haut-gauche relatif à l'ancre."""
    x0 = min(p.x for p in pieces)
    y0 = min(p.y for p in pieces)
    x1 = max(p.x + p.img.shape[1] for p in pieces)
    y1 = max(p.y + p.img.shape[0] for p in pieces)
    canvas = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    for p in sorted(pieces, key=lambda q: q.z):
        sub = canvas[p.y - y0:p.y - y0 + p.img.shape[0], p.x - x0:p.x - x0 + p.img.shape[1]]
        m = p.img[:, :, 3] > 0
        sub[m] = p.img[m]
    return canvas, (x0, y0)


def draw(facing: int, pose: str = "rest", lift: int = 0, extras: list | None = None) -> tuple[np.ndarray, tuple[int, int], dict]:
    """Image locale, origine et repères pour l'une des huit orientations (miroir pour 5, 6, 7)."""
    if facing in MIRROR:
        img, (x0, y0), marks = draw(MIRROR[facing], pose, lift, extras)
        w = img.shape[1]
        return P.flip(img), (-(x0 + w - 1), y0), {k: (-x, y) for k, (x, y) in marks.items()}
    pieces, marks = assemble(facing, pose, lift, extras)
    img, origin = flatten(pieces)
    return img, origin, marks


# ---------------------------------------------------------------------------
# Plan d'animation : pour chaque image, orientation regardée, pose, hauteur, effets
# ---------------------------------------------------------------------------
def slash_extra(facing: int) -> list:
    """Griffures de l'image d'impact, exprimées dans le repère de l'orientation dessinée
    (pour 5, 6, 7 : celle du miroir ; `draw` retourne le tout)."""
    base = MIRROR.get(facing, facing)
    sx, sy = SPECS[base]["slash"]
    return [(P.slash(base), sx, sy, 8)]


def frame_plan(name: str, d: int, i: int, n: int) -> tuple[int, str, int, list | None]:
    """→ (orientation regardée, pose, hauteur, effets) de l'image i de l'animation `name`, direction d."""
    facing = (d - i) % 8 if name in SPIN else d
    if name == "Walk":
        return facing, ["rest", "walk1", "rest", "walk3"][i], 0, None
    if name == "Idle":
        return facing, "rest", 0, None
    if name == "Attack":
        if i <= 4:
            return facing, "windup", 0, None
        if i <= 11:
            return facing, "slam", 0, (slash_extra(facing) if i == 5 else None)
        return facing, "rest", 0, None
    if name == "Shoot":
        if i <= 2 or i == n - 1:
            return facing, "rest", 0, None          # rebond vertical porté par l'ancre (référence)
        return facing, "push", 0, None
    if name == "Sing":
        if i in (0, 15):
            return facing, "rest", 0, None
        if i in (1, 14):
            return facing, "raise", 0, None
        if 2 <= i <= 7:
            return facing, "beatL" if i % 2 == 0 else "beatR", 0, None
        return facing, "howl", 0, None
    if name == "Hurt":
        return facing, "hurt", 0, None
    if name in SPIN or name == "Charge":
        return facing, "rest", 0, None
    if name == "Double":
        return facing, "double", 0, None
    if name == "Hop":
        return facing, HOP_POSE[i], HOP_LIFT[i], None
    raise ValueError(name)


# ---------------------------------------------------------------------------
# Composition des feuilles
# ---------------------------------------------------------------------------
class Builder:
    def __init__(self):
        self.shadow_size, self.meta = parse_animdata(REF / "AnimData.xml")
        self.template = shadow_template()

    def cell(self, fw: int, fh: int, disp: tuple[int, int], img: np.ndarray, origin: tuple[int, int], marks: dict, name: str):
        ax, ay = fw // 2 + disp[0], fh // 2 + 4 + disp[1]
        anim = np.zeros((fh, fw, 4), np.uint8)
        offs = np.zeros((fh, fw, 4), np.uint8)
        shad = np.zeros((fh, fw, 4), np.uint8)
        x0, y0 = ax + origin[0], ay + origin[1]
        h, w = img.shape[:2]
        assert 1 <= x0 and 1 <= y0 and x0 + w <= fw - 1 and y0 + h <= fh - 1, f"{name} : dessin hors de la case ({x0}, {y0}, {w}×{h} dans {fw}×{fh})"
        sub = anim[y0:y0 + h, x0:x0 + w]
        m = img[:, :, 3] > 0
        sub[m] = img[m]
        for key, (mx, my) in marks.items():
            px, py = ax + mx, ay + my
            current = offs[py, px]
            merged = np.maximum(current[:3], OFFSET_COLOURS[key]) if current[3] else np.array(OFFSET_COLOURS[key])
            offs[py, px] = (*merged, 255)
        shad[ay - 4:ay + 4, ax - 12:ax + 12] = self.template
        return (anim, offs, shad), (ax, ay)

    @staticmethod
    def fit(fw: int, fh: int, frames: list[tuple[tuple[int, int], np.ndarray, tuple[int, int]]]) -> tuple[int, int]:
        """Case de la référence, agrandie par pas de 8 px si la silhouette de Zarude (plus longue que celle de
        Rillaboom : queue, bras) déborde. L'ancre au repos reste en (fw/2, fh/2 + 4)."""
        need_w, need_h = fw, fh
        for (dx, dy), img, (ox, oy) in frames:
            h, w = img.shape[:2]
            left, right = -(dx + ox) + 1, dx + ox + w + 1            # marge d'un pixel de chaque côté
            top, bottom = -(dy + oy) + 1, dy + oy + h + 1
            need_w = max(need_w, 2 * max(left, right))
            need_h = max(need_h, 2 * max(top - 4, bottom + 4))      # l'ancre est 4 px sous le centre de la case
        return -(-need_w // 8) * 8, -(-need_h // 8) * 8

    def build(self, name: str) -> Composed:
        m = self.meta[name]
        fw, fh, durations = m["fw"], m["fh"], m["durations"]
        n = len(durations)
        if name == "Sleep":
            plan = [[]]
            for i, img in enumerate((P.SLEEP_A, P.SLEEP_B)):
                marks = {"head": P.SLEEP_HEAD_MARK, "center": P.SLEEP_CENTER, "lhand": P.SLEEP_FISTS[0], "rhand": P.SLEEP_FISTS[1]}
                ox, oy = -18, 6 - img.shape[0] + 1            # au sol : dernière ligne à +6 comme la référence
                plan[0].append(((0, 0), img, (ox, oy), {k: (ox + x, oy + y) for k, (x, y) in marks.items()}))
        else:
            disp = anchor_displacements(name, fw, fh)
            plan = []
            for d in range(8):
                row = []
                for i in range(n):
                    facing, pose, lift, extras = frame_plan(name, d, i, n)
                    img, origin, marks = draw(facing, pose, lift, extras)
                    row.append((disp[d][i], img, origin, marks))
                plan.append(row)
        fw2, fh2 = self.fit(fw, fh, [(dp, img, org) for row in plan for dp, img, org, _ in row])
        comp = Composed(name, fw2, fh2, list(durations), rush=m["rush"], hit=m["hit"], ret=m["ret"])
        for d, row in enumerate(plan):
            cells, anchors = [], []
            for i, (dp, img, origin, marks) in enumerate(row):
                cell, anchor = self.cell(fw2, fh2, dp, img, origin, marks, f"{name} dir {d} image {i}")
                cells.append(cell)
                anchors.append(anchor)
            comp.cells.append(cells)
            comp.anchors.append(anchors)
        comp.notes = NOTES[name] + ("" if (fw2, fh2) == (fw, fh) else f" ; case agrandie ({fw} × {fh} chez Rillaboom)")
        return comp

    def build_all(self) -> dict[str, Composed]:
        return {name: self.build(name) for name, _ in ANIM_ORDER if name != "Strike"}


NOTES = {
    "Walk": "repos / pas gauche / repos / pas droit ; le corps descend d'un pixel sur les pas",
    "Attack": "bras levés au-dessus de la tête (charge), frappe au sol accroupi avec griffures à l'image d'impact, retour",
    "Shoot": "rebond (ancre de la référence), puis accroupi bras tendus devant, secousse d'un pixel copiée de la référence",
    "Sing": "hurlement : bras levés, six coups de poing sur le poitrail (accélérés), tête levée bras au ciel avec ondes",
    "Sleep": "couché sur le flanc, deux images (respiration)",
    "Hurt": "bras écartés (de profil : rejetés en arrière), tête baissée, deux étincelles, recul copié de la référence",
    "Idle": "pose de repos, une image (comme la référence)",
    "Swing": "tour complet sur soi-même en décrivant un cercle : l'image i regarde la direction (d − i) mod 8",
    "Double": "accroupi, aller-retour latéral de l'ancre copié de la référence",
    "Hop": "accroupi, saut (corps levé jusqu'à 23 px), réception accroupie",
    "Charge": "pose de repos, tremblement d'un pixel copié de la référence",
    "Rotate": "tour complet sur place, même sens que Swing",
}


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
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


def ground_shadow(img: Image.Image, ax: int, ay: int, zoom: int) -> None:
    d = ImageDraw.Draw(img)
    d.ellipse([ax - 12 * zoom, ay - 4 * zoom, ax + 11 * zoom, ay + 3 * zoom], fill=(40, 24, 8, 90))


def cell_image(c: Composed, d: int, i: int, zoom: int, bg=(26, 26, 46, 255)) -> Image.Image:
    img = Image.new("RGBA", (c.fw * zoom, c.fh * zoom), bg)
    ax, ay = c.anchors[d][i]
    ground_shadow(img, ax * zoom + zoom // 2, ay * zoom + zoom // 2, zoom)
    cell = Image.fromarray(c.cells[d][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
    img.alpha_composite(cell)
    return img


def contact_sheet(comps: dict[str, Composed], path: Path) -> None:
    zoom = 2
    blocks = []
    for name, _ in ANIM_ORDER:
        if name == "Strike":
            continue
        c = comps[name]
        dirs = [0, 2] if name in ("Walk", "Attack", "Sing") and len(c.cells) > 1 else [0]
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
    d.text((12, 10), "ZARUDE #0893 — SPRITE PMD, FORMAT SPRITECOLLAB (× 2)", fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 36), "Dessin original sur le squelette d'animation de Rillaboom #0812 · Walk, Attack, Sing : ligne 1 = Bas, ligne 2 = Droite",
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


def reference_sheet(comps: dict[str, Composed], path: Path) -> None:
    """Zarude et Rillaboom côte à côte (Walk image 1, huit directions) : même case, même ancre."""
    zoom = 3
    c = comps["Walk"]
    ref = np.array(Image.open(REF / "Walk-Anim.png").convert("RGBA"))
    cw, ch = c.fw * zoom + 6, c.fh * zoom + 4
    out = Image.new("RGBA", (8 * cw + 6, 2 * ch + 60), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 8), "Contrôle de gabarit — ligne 1 : Zarude ; ligne 2 : Rillaboom #0812 (référence, © baronessfaron, CC BY-NC 4.0), Walk image 1, × 3",
           fill=(240, 240, 240, 255), font=font(13))
    for dd in range(8):
        out.alpha_composite(cell_image(c, dd, 0, zoom, (36, 36, 60, 255)), (6 + dd * cw, 34))
        img = Image.new("RGBA", (c.fw * zoom, c.fh * zoom), (36, 36, 60, 255))
        ground_shadow(img, (c.fw // 2) * zoom + zoom // 2, (c.fh // 2 + 4) * zoom + zoom // 2, zoom)
        cell = Image.fromarray(ref[dd * 64:(dd + 1) * 64, 0:48], "RGBA").resize((48 * zoom, 64 * zoom), Image.NEAREST)
        img.alpha_composite(cell)
        out.alpha_composite(img, (6 + dd * cw, 34 + ch))
        d.text((6 + dd * cw + 4, 34 + 2 * ch + 4), DIRECTIONS[dd], fill=(200, 200, 220, 255), font=font(12))
    out.save(path, optimize=True)


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
        for r, n in enumerate(names):
            c = comps[n]
            i = max(i for tt, i in tick_frames[n] if tt <= t)
            for col, direction in enumerate(directions):
                dd = direction if len(c.cells) > 1 else 0
                cell = Image.fromarray(c.cells[dd][i][0], "RGBA").resize((c.fw * zoom, c.fh * zoom), Image.NEAREST)
                ax, ay = c.anchors[dd][i]
                cx, cy = col * cw + cw // 2, r * ch + ch * 2 // 3
                ground_shadow(img, cx, cy, zoom)
                img.alpha_composite(cell, (cx - ax * zoom, cy - ay * zoom))
        frames_out.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations_out.append(int(round((nxt - t) * 1000 / 60)))
    frames_out[0].save(path, save_all=True, append_images=frames_out[1:], duration=durations_out, loop=0, optimize=True)


def player_html(comps: dict[str, Composed], path: Path) -> None:
    manifest = {name: {"fw": c.fw, "fh": c.fh, "durations": c.durations, "dirs": len(c.cells),
                       "anchors": c.anchors, "hit": c.hit, "rush": c.rush, "ret": c.ret} for name, c in comps.items()}
    names = [n for n, _ in ANIM_ORDER if n != "Strike"]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Zarude — sprite PMD</title>
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
<header><h1>Zarude #0893 — sprite PMD, format SpriteCollab</h1>
<p>Lecture hors ligne des feuilles <code>*-Anim.png</code>. Les images sont alignées sur le pixel blanc de <code>*-Shadow.png</code>, comme dans le jeu. Case du donjon = 24 px. Squelette d'animation : Rillaboom #0812.</p></header>
<div class="bar">
<label>Animation <select id="anim">{''.join(f'<option>{n}</option>' for n in names)}</select></label>
<label>Zoom <input id="zoom" type="range" min="2" max="8" value="4"></label>
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
        "# Zarude #0893 forme 0000 — crédits, format proche de SpriteCollab : date, auteur, statut, licence, animations",
        "2026-09-06 00:00:00.000000\tGuilde Treehouse (dessin original en pièces, assemblage scripté)\tCUR\tCC_BY-NC_4\tIdle,Walk,Sleep,Hurt,Attack,Charge,Shoot,Strike,Sing,Swing,Double,Rotate,Hop",
        "",
        "Dessin original : aucun pixel n'est repris d'un sprite existant.",
        "Squelette d'animation (cases, durées, RushFrame/HitFrame/ReturnFrame, déplacements de l'ancre, sens de rotation, gabarit d'ombre)",
        "relevé sur le sprite de Rillaboom #0812 de baronessfaron (<@!544245909639397378>), CC BY-NC 4.0 — https://sprites.pmdcollab.org/#/0812?form=0",
        "Licence de ce sprite : CC BY-NC 4.0 (usage, copie et modification autorisés avec crédit, hors usage commercial).",
        "Zarude n'existe pas sur le dépôt SpriteCollab ; ce sprite n'y a été ni soumis ni approuvé.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nuit").mkdir(exist_ok=True)
    builder = Builder()
    comps = builder.build_all()
    for name, c in comps.items():
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            sheet(c, which).save(OUT / f"{name}-{kind}.png", optimize=True)
        night(sheet(c, 0)).save(OUT / "nuit" / f"{name}-Anim.png", optimize=True)
    write_animdata(comps, OUT / "AnimData.xml")
    ase_info = write_aseprite(comps, OUT / "zarude.aseprite", [n for n, _ in ANIM_ORDER if n != "Strike"])
    contact_sheet(comps, OUT / "apercu.png")
    directions_sheet(comps, OUT / "apercu_directions.png")
    reference_sheet(comps, OUT / "apercu_reference.png")
    gif(comps, ["Walk", "Idle"], [0, 2, 4, 6], OUT / "apercu_marche_attente.gif")
    gif(comps, ["Attack", "Sing"], [0, 2, 4, 6], OUT / "apercu_attaque_hurlement.gif")
    player_html(comps, OUT / "apercu.html")
    write_credits(OUT / "credits.txt")

    used = set()
    for c in comps.values():
        for row in c.cells:
            for cell in row:
                a = cell[0]
                used |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
    kit = {
        "pokemon": {"numero": "0893", "nom": "Zarude", "forme": "0000", "base_squelette": "0812 Rillaboom forme 0 (baronessfaron, CC BY-NC 4.0)"},
        "format": {"convention": "SpriteCollab / SkyTemple : <Anim>-Anim.png, <Anim>-Offsets.png, <Anim>-Shadow.png + AnimData.xml",
                   "directions": DIRECTIONS, "ancre": "pixel blanc de Shadow, en (largeur/2, hauteur/2 + 4) au repos, déplacée comme dans la référence",
                   "shadow_size": SHADOW_SIZE, "reperes": "tête (noir), centre (vert), main gauche (rouge), main droite (bleu)",
                   "cases": "celles de la référence"},
        "dessin": {"orientations_dessinees": ["Bas", "Bas-droite", "Droite", "Haut-droite", "Haut"],
                   "miroirs": {"Gauche": "Droite", "Haut-gauche": "Haut-droite", "Bas-gauche": "Bas-droite"},
                   "pieces": "tête, crinière, torse, queue, deux jambes, deux bras (repos / levé / tendu / poing au poitrail), lianes du dos, griffures, ondes",
                   "hauteur_repos": 35, "source": "source/personnages/zarude_pieces.py"},
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
    print(f"{len(comps)} animations construites (+ Strike), {len(used)} couleurs, exportées dans {OUT.relative_to(ROOT)}")
    for name, _ in ANIM_ORDER:
        if name in comps:
            c = comps[name]
            print(f"  {name:8s} {c.fw:3d} × {c.fh:3d}  {len(c.durations):2d} images  {len(c.cells)} dir  {sum(c.durations):3d} ticks  durées {c.durations}")


if __name__ == "__main__":
    main()
