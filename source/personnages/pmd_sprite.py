#!/usr/bin/env python3
"""Briques communes pour lire et écrire des sprites au format SpriteCollab / SkyTemple.

Extrait de `build_falinks_sprite.py` et généralisé pour servir à tous les personnages :
lecture d'un dossier de sprite (AnimData.xml + feuilles Anim / Offsets / Shadow) en cases
repérées par rapport à l'ancre, et réécriture de feuilles, d'AnimData.xml et d'Aseprite.

Conventions rappelées (§1 de METHODE_SPRITES_PMD.md) :
- une colonne par image, une ligne par direction (Bas, Bas-droite, Droite, Haut-droite,
  Haut, Haut-gauche, Gauche, Bas-gauche) ; 1 ligne pour les animations sans direction ;
- `-Shadow.png` : un pixel blanc par case = ancre au sol ; vert / rouge / bleu = gabarit
  d'ombre petite / normale / grande ;
- `-Offsets.png` : noir = tête, vert = centre, rouge = main gauche, bleu = main droite
  (couleurs additionnées lorsqu'ils se superposent) ;
- ancre au repos en (largeur / 2, hauteur / 2 + 4), cases paires (multiples de 8 ici) ;
- alpha strictement 0 ou 255, 15 couleurs opaques au maximum.
"""
from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

DIRECTIONS = ["Bas", "Bas-droite", "Droite", "Haut-droite", "Haut", "Haut-gauche", "Gauche", "Bas-gauche"]
# Index officiels (sprite_config.json du dépôt SpriteCollab).
ACTION_INDEX = {
    "Idle": 0, "Walk": 1, "Sleep": 2, "Hurt": 3, "Attack": 4, "Charge": 5, "Shoot": 6, "Strike": 7,
    "Chop": 8, "Scratch": 9, "Punch": 10, "Slap": 11, "Slice": 12, "MultiScratch": 13, "MultiStrike": 14,
    "Uppercut": 15, "Ricochet": 16, "Bite": 17, "Shake": 18, "Jab": 19, "Kick": 20, "Lick": 21,
    "Slam": 22, "Stomp": 23, "Appeal": 24, "Dance": 25, "Twirl": 26, "TailWhip": 27, "Sing": 28,
    "Sound": 29, "Rumble": 30, "FlapAround": 31, "Gas": 32, "Shock": 33, "Emit": 34, "SpAttack": 35,
    "Withdraw": 36, "RearUp": 37, "Swell": 38, "Swing": 39, "Double": 40, "Rotate": 41, "Hop": 42,
    "Hover": 43, "QuickStrike": 44, "EventSleep": 45, "Wake": 46, "Eat": 47, "Tumble": 48, "Pose": 49,
    "Pull": 50, "Pain": 51, "Float": 52, "DeepBreath": 53, "Nod": 54, "Sit": 55, "LookUp": 56,
    "Sink": 57, "Trip": 58, "Laying": 59, "LeapForth": 60, "Head": 61, "Cringe": 62, "LostBalance": 63,
    "TumbleBack": 64, "HitGround": 65, "Faint": 66,
}
# « Set complet » de SpriteCollab (completion_actions[2]) : donjon + scènes d'histoire.
COMPLETE_SET = [
    "Idle", "Walk", "Sleep", "Hurt", "Attack", "Charge", "Swing", "Double", "Rotate", "Hop",
    "EventSleep", "Wake", "Eat", "Tumble", "Pose", "Pull", "Pain", "Float", "DeepBreath", "Nod",
    "Sit", "LookUp", "Sink", "Trip", "Laying", "LeapForth", "Head", "Cringe", "LostBalance",
    "TumbleBack", "HitGround", "Faint",
]
MARK_COLOURS = {"head": (0, 0, 0), "center": (0, 255, 0), "lhand": (255, 0, 0), "rhand": (0, 0, 255)}


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------
@dataclass
class Frame:
    """Une case, décrite par rapport à son ancre (le pixel blanc de `-Shadow.png`)."""
    image: np.ndarray                       # cellule RGBA complète, telle qu'elle est dans la feuille
    anchor: tuple[int, int]                 # position du pixel blanc dans la cellule
    disp: tuple[int, int]                   # ancre − (fw/2, fh/2 + 4)
    marks: dict                             # repères relatifs à l'ancre
    bbox: tuple[int, int, int, int]         # contenu relatif à l'ancre (x0, y0, x1, y1 inclus)
    shadow: np.ndarray                      # gabarit d'ombre recadré autour de l'ancre
    shadow_box: tuple[int, int, int, int]   # sa boîte relative à l'ancre


@dataclass
class Anim:
    name: str
    index: int
    fw: int
    fh: int
    durations: list[int]
    frames: list[list[Frame]]               # [direction][image]
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None
    copy_of: str | None = None
    notes: str = ""

    @property
    def dirs(self) -> int:
        return len(self.frames)


def parse_animdata(path: Path) -> tuple[int, dict]:
    root = ET.parse(path).getroot()
    shadow_size = int(root.findtext("ShadowSize"))
    anims: dict[str, dict] = {}
    for node in root.find("Anims").iter("Anim"):
        name = node.findtext("Name")
        entry: dict = {"index": int(node.findtext("Index")) if node.find("Index") is not None else ACTION_INDEX.get(name)}
        copy = node.find("CopyOf")
        if copy is not None:
            entry["copy_of"] = copy.text
            anims[name] = entry
            continue
        entry.update(fw=int(node.findtext("FrameWidth")), fh=int(node.findtext("FrameHeight")),
                     durations=[int(d.text) for d in node.find("Durations").iter("Duration")])
        for tag, key in (("RushFrame", "rush"), ("HitFrame", "hit"), ("ReturnFrame", "ret")):
            sub = node.find(tag)
            entry[key] = int(sub.text) if sub is not None else None
        anims[name] = entry
    return shadow_size, anims


def _cell(sheet: np.ndarray, fw: int, fh: int, d: int, i: int) -> np.ndarray:
    return sheet[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]


def read_frame(anim: np.ndarray, offs: np.ndarray, shad: np.ndarray, fw: int, fh: int, d: int, i: int) -> Frame:
    cell = _cell(anim, fw, fh, d, i).copy()
    o = _cell(offs, fw, fh, d, i)
    s = _cell(shad, fw, fh, d, i)
    white = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
    assert len(white) == 1, f"pixel blanc absent ou multiple (dir {d}, image {i})"
    ay, ax = (int(v) for v in white[0])
    marks: dict[str, tuple[int, int]] = {}
    for y, x in np.argwhere(o[:, :, 3] > 0):
        r, g, b = (int(v) for v in o[y, x, :3])
        rel = (int(x) - ax, int(y) - ay)
        if (r, g, b) == (0, 0, 0):
            marks["head"] = rel
        if g == 255:
            marks["center"] = rel
        if r == 255:
            marks["lhand"] = rel
        if b == 255:
            marks["rhand"] = rel
    marks.setdefault("center", (0, -8))
    marks.setdefault("head", marks["center"])
    ys, xs = np.nonzero(cell[:, :, 3])
    bbox = (int(xs.min()) - ax, int(ys.min()) - ay, int(xs.max()) - ax, int(ys.max()) - ay)
    sy, sx = np.nonzero(s[:, :, 3])
    keep = ~((sy == ay) & (sx == ax))     # le pixel blanc lui-même n'est pas du gabarit
    sy, sx = sy[keep], sx[keep]
    if len(sy):
        y0, y1, x0, x1 = int(sy.min()), int(sy.max()), int(sx.min()), int(sx.max())
        shadow = s[y0:y1 + 1, x0:x1 + 1].copy()
        sbox = (x0 - ax, y0 - ay, x1 - ax, y1 - ay)
    else:
        shadow, sbox = np.zeros((0, 0, 4), np.uint8), (0, 0, -1, -1)
    return Frame(cell, (ax, ay), (ax - fw // 2, ay - (fh // 2 + 4)), marks, bbox, shadow, sbox)


def load_sprite(folder: Path) -> tuple[int, dict[str, Anim]]:
    """Lit un dossier SpriteCollab complet et renvoie (ShadowSize, {nom: Anim})."""
    shadow_size, meta = parse_animdata(folder / "AnimData.xml")
    anims: dict[str, Anim] = {}
    for name, m in meta.items():
        if "copy_of" in m:
            anims[name] = Anim(name, m["index"], 0, 0, [], [], copy_of=m["copy_of"])
            continue
        a = np.array(Image.open(folder / f"{name}-Anim.png").convert("RGBA"))
        o = np.array(Image.open(folder / f"{name}-Offsets.png").convert("RGBA"))
        s = np.array(Image.open(folder / f"{name}-Shadow.png").convert("RGBA"))
        fw, fh = m["fw"], m["fh"]
        rows, cols = a.shape[0] // fh, a.shape[1] // fw
        assert cols == len(m["durations"]), f"{folder.name}/{name} : {cols} colonnes pour {len(m['durations'])} durées"
        frames = [[read_frame(a, o, s, fw, fh, d, i) for i in range(cols)] for d in range(rows)]
        anims[name] = Anim(name, m["index"], fw, fh, m["durations"], frames, m["rush"], m["hit"], m["ret"])
    return shadow_size, anims


def palette_of(anims: dict[str, Anim]) -> set[tuple[int, int, int]]:
    used: set[tuple[int, int, int]] = set()
    for a in anims.values():
        for row in a.frames:
            for f in row:
                px = f.image[f.image[:, :, 3] > 0]
                used |= set(map(tuple, px[:, :3].tolist()))
    return used


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------
@dataclass
class Built:
    """Animation reconstruite, prête à être écrite."""
    name: str
    index: int
    fw: int
    fh: int
    durations: list[int]
    cells: list[list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = field(default_factory=list)
    anchors: list[list[tuple[int, int]]] = field(default_factory=list)
    rush: int | None = None
    hit: int | None = None
    ret: int | None = None
    notes: str = ""

    @property
    def dirs(self) -> int:
        return len(self.cells)


def sheet(built: Built, which: int) -> Image.Image:
    canvas = np.zeros((built.dirs * built.fh, len(built.durations) * built.fw, 4), np.uint8)
    for d, row in enumerate(built.cells):
        for i, cell in enumerate(row):
            canvas[d * built.fh:(d + 1) * built.fh, i * built.fw:(i + 1) * built.fw] = cell[which]
    return Image.fromarray(canvas, "RGBA")


def write_animdata(shadow_size: int, entries: list, path: Path) -> None:
    """`entries` : liste de Built, ou de tuples (nom, index, copy_of)."""
    lines = ['<?xml version="1.0" ?>', "<AnimData>", f"\t<ShadowSize>{shadow_size}</ShadowSize>", "\t<Anims>"]
    for e in entries:
        if isinstance(e, tuple):
            name, index, copy_of = e
            lines += ["\t\t<Anim>", f"\t\t\t<Name>{name}</Name>", f"\t\t\t<Index>{index}</Index>",
                      f"\t\t\t<CopyOf>{copy_of}</CopyOf>", "\t\t</Anim>"]
            continue
        lines += ["\t\t<Anim>", f"\t\t\t<Name>{e.name}</Name>", f"\t\t\t<Index>{e.index}</Index>",
                  f"\t\t\t<FrameWidth>{e.fw}</FrameWidth>", f"\t\t\t<FrameHeight>{e.fh}</FrameHeight>"]
        for tag, value in (("RushFrame", e.rush), ("HitFrame", e.hit), ("ReturnFrame", e.ret)):
            if value is not None:
                lines.append(f"\t\t\t<{tag}>{value}</{tag}>")
        lines.append("\t\t\t<Durations>")
        lines += [f"\t\t\t\t<Duration>{d}</Duration>" for d in e.durations]
        lines += ["\t\t\t</Durations>", "\t\t</Anim>"]
    lines += ["\t</Anims>", "</AnimData>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# -- Aseprite : un calque par direction, toutes les animations bout à bout, une étiquette par anim --
# (même écriture que build_falinks_sprite.py, généralisée à une liste de Built)
def _astr(text: str) -> bytes:
    data = text.encode()
    return struct.pack("<H", len(data)) + data


def _chunk(kind: int, data: bytes) -> bytes:
    return struct.pack("<IH", len(data) + 6, kind) + data


def write_aseprite(builts: list[Built], path: Path) -> dict:
    W = max(b.fw for b in builts)
    H = max(b.fh for b in builts)
    layers = max(b.dirs for b in builts)
    labels = DIRECTIONS[:layers] if layers > 1 else ["Sans direction"]
    frames, tags, cursor = [], [], 0
    for b in builts:
        n = len(b.durations)
        for i in range(n):
            cels = [Image.fromarray(b.cells[d][i][0], "RGBA") if d < b.dirs else None for d in range(layers)]
            frames.append((round(b.durations[i] * 1000 / 60), cels, (W - b.fw) // 2, (H - b.fh) // 2))
        tags.append((cursor, cursor + n - 1, b.name))
        cursor += n

    layer_chunks = b"".join(_chunk(0x2004, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + _astr(label))
                            for label in labels)
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
        n_chunks = len(chunks) - 1 + len(labels) if k == 0 else len(chunks)
        data = b"".join(chunks)
        body += struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA, min(n_chunks, 0xFFFF), duration, b"\0\0", n_chunks) + data
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(body) + 128, 0xA5E0, len(frames), W, H, 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.write_bytes(header + body)
    return {"canvas": [W, H], "images": len(frames), "calques": labels,
            "etiquettes": [t[2] for t in tags], "ancre": [W // 2, H // 2 + 4]}
