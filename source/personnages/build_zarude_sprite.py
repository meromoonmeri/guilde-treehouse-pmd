#!/usr/bin/env python3
"""Sprite Zarude (#0893) au format SpriteCollab / SkyTemple, sur le squelette d'animation de Rillaboom.

Zarude n'existe pas sur PMDCollab. Le dessin vient de la **planche de marche fournie par l'utilisateur**
(`source/personnages/reference/zarude/`, 4 directions × 4 images, Game Character Hub), découpée en pièces
pixel-exactes dans `zarude_pieces.py` (tête, poitrail, bras, jambes, queue, dos) et complétée par des pièces
dessinées dans la même palette (diagonales, bras levés / tendus / au poitrail, sommeil, effets).

Pour rester dans la convention des sprites du dépôt, on **recopie le squelette** du sprite de Rillaboom #0812
(baronessfaron, CC BY-NC 4.0) :

- mêmes animations (set donjon complet, Sing compris), mêmes cases, mêmes durées,
  mêmes RushFrame / HitFrame / ReturnFrame ;
- même déplacement du point d'ancrage à chaque image (charge de l'attaque, secousse, cercle de Swing,
  aller-retour de Double, saut de Hop), lu directement dans les feuilles `*-Shadow.png` de la référence
  (`source/personnages/reference/0812/`) ;
- même gabarit d'ombre, mêmes couleurs de repères ; pour Swing et Rotate, même sens de rotation :
  l'image i regarde la direction (d − i) mod 8.

Aucun pixel de Rillaboom n'est copié : ses feuilles servent de plan (cases, ancres, timing).

Les cinq orientations Bas, Bas-droite, Droite, Haut-droite, Haut sont assemblées ; Gauche, Haut-gauche et
Bas-gauche sont des miroirs autour de la colonne de l'ancre (comme les sprites officiels). Chaque image est
un assemblage de pièces déplacées de quelques pixels : la cohérence entre images est mécanique.

Sorties : personnages/zarude/ (feuilles, AnimData.xml, Aseprite, variantes nuit, aperçus, kit.json, credits.txt).
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
PLANCHE = ROOT / "source" / "personnages" / "reference" / "zarude" / "zarude_overworld_1x.png"
OUT = ROOT / "personnages" / "zarude"
SHADOW_SIZE = 1                     # Zarude fait 22 px de haut : ombre moyenne (Rillaboom, 35 px : 2)
ANIM_ORDER = [("Walk", 0), ("Attack", 1), ("Strike", 2), ("Shoot", 3), ("Sing", 4), ("Sleep", 5), ("Hurt", 6),
              ("Idle", 7), ("Swing", 8), ("Double", 9), ("Hop", 10), ("Charge", 11), ("Rotate", 12)]
SPIN = ("Swing", "Rotate")          # l'image i regarde (d - i) mod 8
HOP_LIFT = [0, 10, 16, 20, 21, 23, 22, 18, 12, 0]      # hauteur du corps au-dessus du sol, relevée sur Rillaboom
HOP_POSE = ["crouch", "rest", "rest", "rest", "rest", "crouch", "crouch", "crouch", "crouch", "rest"]
MIRROR = {5: 3, 6: 2, 7: 1}
WALK_BOB = 1                        # sur les pas, le haut du corps descend d'un pixel (les pieds restent au sol)

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
    fist: tuple[int, int]          # coordonnées de la pièce
    shoulder: tuple[int, int]

    def flipped(self) -> "Arm":
        w = self.img.shape[1]
        return Arm(P.flip(self.img), (w - 1 - self.fist[0], self.fist[1]), (w - 1 - self.shoulder[0], self.shoulder[1]))

    def darker(self) -> "Arm":
        return Arm(P.darker(self.img), self.fist, self.shoulder)

    def shortened(self, n: int) -> "Arm":
        """Retire n lignes du haut du bras, côté épaule (bras à demi levé) ; la main garde sa forme."""
        if n <= 0:
            return self
        fx, fy = self.fist
        sx, sy = self.shoulder
        if sy > fy:                                   # épaule en bas (bras levé) : on coupe juste au-dessus
            img = P.shorten(self.img, n, keep_top=sy - n)
            return Arm(img, (fx, fy), (sx, sy - n))
        img = P.shorten(self.img, n, keep_top=sy + 1)  # épaule en haut : on coupe juste en dessous
        return Arm(img, (fx, fy - n), (sx, sy))


def arm(name: str) -> Arm:
    g = vars(P)
    return Arm(g[name], g[f"{name}_FIST"], g[f"{name}_SHOULDER"])


def mirror_at(at: tuple[int, int], img: np.ndarray) -> tuple[int, int]:
    """Position d'une pièce retournée : la planche est symétrique autour de x = −0,5 (entre deux colonnes)."""
    return (-at[0] - img.shape[1], at[1])


def flipped_leg(img: np.ndarray, at: tuple[int, int]) -> tuple[np.ndarray, tuple[int, int]]:
    return P.flip(img), mirror_at(at, img)


def flipped_arm(a: Arm, at: tuple[int, int]) -> tuple[Arm, tuple[int, int]]:
    return a.flipped(), mirror_at(at, a.img)


KINDS = {fam: {k: arm(f"ARM_{k.upper()}_{fam}") for k in ("up", "out", "beat", "push")} for fam in (0, 2, 4)}


@dataclass
class Piece:
    name: str
    img: np.ndarray
    x: int
    y: int
    z: int


def _turned(off: dict, dx: int, dy: int = 0, z: int | None = None):
    """Applique un décalage (et un plan z) à une entrée (pièce, position[, z])."""
    img, (x, y), *rest = off
    zz = [z] if z is not None else rest
    return (img, (x + dx, y + dy), *zz)


def _front_spec(head, head_at, torso, torso_at, head_mark=(0, -10), tail=None, red="armL", turn=0):
    """Face (0) ou trois quarts face (1). Les membres viennent de la planche « bas » ; pour le trois quarts,
    les deux bras se rapprochent du centre (rotation de 45°) et le bras éloigné (droite-écran) passe derrière."""
    legL = flipped_leg(P.LEG_0, P.LEG_0_AT)
    armL = arm("ARM_L_0")
    armR, armR_at = flipped_arm(armL, P.ARM_L_0_AT)
    swingR = (arm("ARM_R_0"), P.ARM_R_0_AT)                        # bras droit-écran balancé (pas A)
    swingL = flipped_arm(*swingR)                                     # bras gauche-écran balancé (pas B)
    legUpL = (P.LEG_UP_0, P.LEG_UP_0_AT)
    legUpR = flipped_leg(*legUpL)
    n, f, fz = (3, -3, 2) if turn else (0, 0, 6)                     # décalage du bras proche / éloigné, plan du bras éloigné
    ln, lf = (1, -1) if turn else (0, 0)
    body = [("head", head, head_at, 5), ("torso", torso, torso_at, 3)]
    if tail is not None:
        body.append(("tail", *tail, 0))
    return dict(
        fam=0, body=body, head_mark=head_mark, center=(0, -4),
        legs={"legL": _turned((*legL, 1), ln), "legR": _turned((P.LEG_0, P.LEG_0_AT, 1), lf)},
        arms={"armL": _turned((armL, P.ARM_L_0_AT, 6), n), "armR": _turned((armR, armR_at, 6), f, 0 if not turn else -1, fz)},
        walk={"walk1": {"legL": _turned(legUpL, ln), "armR": _turned(swingR, f, 0 if not turn else -1)},
              "walk3": {"legR": _turned(legUpR, lf), "armL": _turned(swingL, n),
                        "torso": (P.flip(torso), mirror_at(torso_at, torso) if not turn else torso_at)}},
        red=red, slash=(0, 6), howl=[((-13, -19), False), ((12, -19), True)], sparks=[(-12, -15), (12, -17)],
    )


def _back_spec(head, head_at, back, back_b, back_at, head_mark=(0, -15), red="armR", turn=0):
    """Dos (4) ou trois quarts dos (3) : pour le trois quarts, le bras éloigné (gauche-écran) passe derrière."""
    legL = flipped_leg(P.LEG_4, P.LEG_4_AT)
    armL = arm("ARM_L_4")
    armR, armR_at = flipped_arm(armL, P.ARM_L_4_AT)
    swingR = (arm("ARM_R_4"), P.ARM_R_4_AT)
    swingL = flipped_arm(*swingR)
    legUpL = (P.LEG_UP_4, P.LEG_UP_4_AT)
    legUpR = flipped_leg(*legUpL)
    n, f, fz = (3, -3, 4) if turn else (0, 0, 2)                      # éloigné = gauche-écran (armL, derrière), proche = droite-écran (armR)
    ln, lf = (1, -1) if turn else (0, 0)
    return dict(
        fam=4, body=[("head", head, head_at, 5), ("back", back, back_at, 3)], head_mark=head_mark, center=(0, -6),
        legs={"legL": _turned((*legL, 1), n and ln), "legR": _turned((P.LEG_4, P.LEG_4_AT, 1), n and lf)},
        arms={"armL": _turned((armL, P.ARM_L_4_AT, 2), n, 0 if not turn else -1, 2), "armR": _turned((armR, armR_at, 2), f, 0, fz)},
        walk={"walk1": {"legL": _turned(legUpL, n and ln), "armR": _turned(swingR, f)},
              "walk3": {"legR": _turned(legUpR, n and lf), "armL": _turned(swingL, n, 0 if not turn else -1),
                        "back": (back_b, back_at)}},
        red=red, slash=(0, -22), howl=[((-13, -18), False), ((12, -18), True)], sparks=[(-12, -14), (12, -16)],
    )


def _side_spec():
    """Profil : le repos est le pas A de la planche (jambe sous le corps, bras proche pendant, main éloignée
    tendue devant le poitrail) ; les deux images de pas sont le pas B (jambe tendue en arrière, bras balancé)."""
    near = arm("ARM_2A")
    far = Arm(P.HAND_F_2, P.HAND_F_2_FIST, P.HAND_F_2_SHOULDER)
    stride = {"armN": (arm("ARM_2B"), P.ARM_2B_AT), "legN": (P.LEG_2B, P.LEG_2B_AT),
              "tail": (P.TAIL_2B, P.TAIL_2B_AT), "torso": (P.TORSO_2B, P.TORSO_2B_AT)}
    return dict(
        fam=2, body=[("head", P.HEAD_2, P.HEAD_2_AT, 5), ("torso", P.TORSO_2, P.TORSO_2_AT, 3), ("tail", P.TAIL_2A, P.TAIL_2A_AT, 0)],
        head_mark=(3, -10), center=(-4, -4),
        legs={"legN": (P.LEG_2A, P.LEG_2A_AT, 1)},
        arms={"armN": (near, P.ARM_2A_AT, 6), "armF": (far, P.HAND_F_2_AT, 4)},
        walk={"walk1": stride, "walk3": stride},
        red="armF", slash=(14, -4), howl=[((14, -18), True)], sparks=[(-8, -18), (13, -14)],
    )


SPECS = {
    0: _front_spec(P.HEAD_0, P.HEAD_0_AT, P.TORSO_0, P.TORSO_0_AT),
    1: _front_spec(P.HEAD_1, P.HEAD_1_AT, P.TORSO_1, P.TORSO_1_AT, head_mark=(1, -10), tail=(P.TAIL_1, P.TAIL_1_AT), red="armR", turn=1),
    2: _side_spec(),
    3: _back_spec(P.HEAD_3, P.HEAD_3_AT, P.BACK_3, P.BACK_3B, P.BACK_3_AT, head_mark=(0, -15), red="armL", turn=1),
    4: _back_spec(P.HEAD_4, P.HEAD_4_AT, P.BACK_4, P.BACK_4B, P.BACK_4_AT),
}
FAMILY = {0: "front", 1: "front", 2: "side", 3: "back", 4: "back"}


def howl_mark(flipped: bool) -> np.ndarray:
    return P.flip(P.HOWL) if flipped else P.HOWL


def assemble(facing: int, pose: str = "rest", lift: int = 0, extras: list | None = None) -> tuple[list[Piece], dict]:
    """Pièces (coordonnées relatives à l'ancre) et repères d'une pose, pour une orientation dessinée (0-4)."""
    spec = SPECS[facing]
    fam = FAMILY[facing]
    kinds = KINDS[spec["fam"]]
    body_dy = 0
    head_off = (0, 0)
    legs = {k: v for k, v in spec["legs"].items()}          # name -> (img, at, z)
    arms = {k: v for k, v in spec["arms"].items()}          # name -> (Arm, at, z)
    body = {name: (img, at, z) for name, img, at, z in spec["body"]}
    leg_short = {k: 0 for k in legs}
    arm_kind = {k: "rest" for k in arms}
    arm_off = {k: (0, 0) for k in arms}
    arm_short = {k: 0 for k in arms}
    arm_flip = {k: False for k in arms}
    extras = list(extras or [])

    if pose in ("walk1", "walk3"):
        for name, (img, at) in spec["walk"][pose].items():
            if name in legs:
                legs[name] = (img, at, legs[name][2])
            elif name in arms:
                arms[name] = (img, at, arms[name][2])
            else:
                body[name] = (img, at, body[name][2])
        body_dy = WALK_BOB
    elif pose in ("crouch", "slam", "push", "double"):
        body_dy = 2
        leg_short = {k: 2 for k in legs}
        arm_short = {k: 2 for k in arms}
        if pose == "slam":
            head_off = (0, 1)
            for k in arms:
                ax = arms[k][1][0] + arms[k][0].fist[0]
                arm_off[k] = (2 if ax < 0 else -2, 0) if fam != "side" else (3, 0)
        elif pose == "push":
            arm_kind = {k: "push" for k in arms}
            arm_short = {k: 0 for k in arms}
            arm_off = {k: (0, 2) for k in arms} if fam != "side" else {"armN": (1, 1), "armF": (0, 0)}
    elif pose in ("windup", "raise"):
        arm_kind = {k: "up" for k in arms}
        if pose == "raise":
            arm_short = {k: 4 for k in arms}
    elif pose == "howl":
        arm_kind = {k: "up" for k in arms}
        arm_short = {k: 4 for k in arms}
        head_off = (0, -1)
        for (hx, hy), fl in spec["howl"]:
            extras.append((howl_mark(fl), hx, hy, 9))
    elif pose in ("beatL", "beatR"):
        names = sorted(arms)
        arm_kind[names[0] if pose == "beatL" else names[-1]] = "beat"
    elif pose == "hurt":
        arm_kind = {k: "out" for k in arms}
        head_off = (0, 1)
        if fam == "side":                          # de profil : bras rejetés en arrière
            arm_flip = {k: True for k in arms}
        for sx, sy in spec["sparks"]:
            extras.append((P.SPARK, sx, sy, 9))
    elif pose == "rest":
        pass
    else:
        raise ValueError(pose)

    pieces: list[Piece] = []
    for name, (img, (x, y), z) in body.items():
        dy = body_dy + (head_off[1] if name == "head" else 0)
        dx = head_off[0] if name == "head" else 0
        pieces.append(Piece(name, img, x + dx, y + dy - lift, z))
    hx, hy = spec["head_mark"]
    cx, cy = spec["center"]
    marks = {"head": (hx + head_off[0], hy + body_dy + head_off[1] - lift), "center": (cx, cy + body_dy - lift)}
    for name, (img, (x, y), z) in legs.items():
        n = leg_short[name]
        pieces.append(Piece(name, P.shorten(img, n, keep_top=1), x, y + n - lift, z))
    fists = {}
    for name, (base, (x, y), z) in arms.items():
        sx, sy = x + base.shoulder[0], y + base.shoulder[1] + body_dy         # épaule, suit le corps
        kind = arm_kind[name]
        if kind == "rest":
            a = base
        else:
            a = kinds[kind]
            if name == "armR":                        # variantes dessinées pour le bras gauche-écran
                a = a.flipped()
            if name == "armF":                        # bras éloigné, de profil : assombri, derrière le corps
                a = a.darker()
                z = 2
                if kind in ("up", "out", "push"):
                    dx0, dy0 = arm_off[name]
                    arm_off[name] = (dx0 - 2, dy0) if kind == "up" else (dx0 - 3, dy0 + 2)
        if arm_flip[name]:
            a = a.flipped()
        a = a.shortened(arm_short[name])
        dx, dy = arm_off[name]
        if kind == "rest":
            px, py = x + dx, y + body_dy + dy - lift
        else:
            px, py = sx - a.shoulder[0] + dx, sy - a.shoulder[1] + dy - lift
        pieces.append(Piece(name, a.img, px, py, z))
        fists[name] = (px + a.fist[0], py + a.fist[1])
    red = spec["red"]
    blue = [k for k in arms if k != red][0]
    marks["lhand"], marks["rhand"] = fists[red], fists[blue]
    for k, (img, ex, ey, z) in enumerate(extras):
        pieces.append(Piece(f"fx{k}", img, ex - img.shape[1] // 2, ey - img.shape[0] // 2, z))
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
                ox, oy = P.SLEEP_A_AT
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
    d.text((12, 36), "Planche de marche fournie, complétée · squelette d'animation de Rillaboom #0812 · Walk, Attack, Sing : ligne 1 = Bas, ligne 2 = Droite",
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
        "2026-09-07 00:00:00.000000\tGuilde Treehouse (découpe de la planche fournie + pièces complémentaires, assemblage scripté)\tCUR\tCC_BY-NC_4\tIdle,Walk,Sleep,Hurt,Attack,Charge,Shoot,Strike,Sing,Swing,Double,Rotate,Hop",
        "",
        "Dessin : planche de marche de Zarude fournie par le commanditaire (4 directions × 4 images, fichier « Made with Game Character Hub »,",
        "source/personnages/reference/zarude/zarude_overworld_2x.png) ; auteur d'origine non renseigné — à compléter si connu.",
        "Les vues Bas, Droite/Gauche et Haut de Walk reprennent ses pixels tels quels ; les diagonales, les bras des attaques,",
        "le sommeil et les effets sont dessinés dans sa palette (11 couleurs).",
        "Squelette d'animation (cases, durées, RushFrame/HitFrame/ReturnFrame, déplacements de l'ancre, sens de rotation)",
        "relevé sur le sprite de Rillaboom #0812 de baronessfaron (<@!544245909639397378>), CC BY-NC 4.0 — https://sprites.pmdcollab.org/#/0812?form=0",
        "Licence de ce sprite : CC BY-NC 4.0 (usage, copie et modification autorisés avec crédit, hors usage commercial),",
        "sous réserve des droits de l'auteur de la planche d'origine.",
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
        "pokemon": {"numero": "0893", "nom": "Zarude", "forme": "0000", "base_dessin": "planche de marche 4 directions fournie par l'utilisateur (Game Character Hub)",
                    "base_squelette": "0812 Rillaboom forme 0 (baronessfaron, CC BY-NC 4.0)"},
        "format": {"convention": "SpriteCollab / SkyTemple : <Anim>-Anim.png, <Anim>-Offsets.png, <Anim>-Shadow.png + AnimData.xml",
                   "directions": DIRECTIONS, "ancre": "pixel blanc de Shadow, en (largeur/2, hauteur/2 + 4) au repos, déplacée comme dans la référence",
                   "shadow_size": SHADOW_SIZE, "reperes": "tête (noir), centre (vert), main gauche (rouge), main droite (bleu)",
                   "cases": "celles de la référence"},
        "dessin": {"orientations_dessinees": ["Bas", "Bas-droite", "Droite", "Haut-droite", "Haut"],
                   "miroirs": {"Gauche": "Droite", "Haut-gauche": "Haut-droite", "Bas-gauche": "Bas-droite"},
                   "pieces": "relevées sur la planche fournie (tête, poitrail, bras, jambes, queue, dos ; 4 directions) + dessinées (diagonales, bras levé / tendu / au poitrail / poussée, sommeil, effets)",
                   "hauteur_repos": 22, "planche": "source/personnages/reference/zarude/zarude_overworld_2x.png", "source": "source/personnages/zarude_pieces.py"},
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
