# -*- coding: utf-8 -*-
"""
pmdo_format.py — écriture / lecture des formats natifs de PMDO (RogueEssence).

Tout ce qui est ici a été relevé dans le code source du moteur
(RogueCollab/RogueEssence) et vérifié sur les fichiers de Palikadude/Halcyon :

  * GraphicsManager.TEX_SIZE = 8            → une ground map est tranchée en 8 px
  * GroundMap.obstacles[x][y].Tags          → 0 libre, 1 mur (SlideResponse),
                                              2/3 réservés aux objets déclencheurs
  * DrawLayer : Under=-1 Bottom=0 Back=1 Normal=2 Front=3 Top=4 NoDraw=5
  * Content/Tile/<Nom>.tile :
        int32 taille_tuile, int32 nb_entrées,
        nb × (int32 x, int32 y, int64 offset),
        puis à chaque offset : int64 longueur + PNG RGBA de la tuile.
    Dev.ImportHelper.SaveTileSheet omet les tuiles vides et DÉDOUBLONNE les
    octets identiques (plusieurs positions pointent le même offset).
  * Data/Ground/<asset>.rsground : JSON UTF-8 avec BOM, { Version, Object }.
    Chaque case de calque = { AutoTileset:"", Associates:[], NeighborCode:-1|0,
    Layers:[ { Frames:[{Sheet, TexLoc:{X,Y}}...], FrameLength } ] }.
"""
import io
import json
import struct
import hashlib

import numpy as np
from PIL import Image

CELL = 8
DRAW_UNDER, DRAW_BOTTOM, DRAW_BACK, DRAW_NORMAL, DRAW_FRONT, DRAW_TOP = -1, 0, 1, 2, 3, 4
TAG_LIBRE, TAG_MUR = 0, 1


# --------------------------------------------------------------------- .tile
def _png_bytes(tile):
    b = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(tile), "RGBA").save(b, "PNG", optimize=True)
    return b.getvalue()


def slice_sheet(img):
    """Tranche une image RGBA (H×W×4) en cellules de 8 px.

    Renvoie (positions, uniques) : positions[(x, y)] = index dans `uniques`
    (liste de PNG bytes), tuiles entièrement transparentes omises.
    """
    if isinstance(img, Image.Image):
        img = np.array(img.convert("RGBA"))
    h, w = img.shape[:2]
    gw, gh = w // CELL, h // CELL
    positions, uniques, index = {}, [], {}
    for y in range(gh):
        for x in range(gw):
            t = img[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]
            if t[..., 3].max() == 0:
                continue
            key = hashlib.md5(t.tobytes()).digest()
            if key not in index:
                index[key] = len(uniques)
                uniques.append(_png_bytes(t))
            positions[(x, y)] = index[key]
    return positions, uniques


def write_tile(path, img):
    """Écrit une banque `.tile` à partir d'une image RGBA (ou d'un np.array)."""
    positions, uniques = slice_sheet(img)
    head_len = 8 + 16 * len(positions)
    offsets, body, pos = [], b"", head_len
    for png in uniques:
        offsets.append(pos)
        body += struct.pack("<q", len(png)) + png
        pos += 8 + len(png)
    out = struct.pack("<ii", CELL, len(positions))
    for (x, y), i in positions.items():
        out += struct.pack("<iiq", x, y, offsets[i])
    with open(path, "wb") as f:
        f.write(out + body)
    return dict(entrees=len(positions), uniques=len(uniques),
                reemploi=round(len(positions) / max(1, len(uniques)), 2),
                octets=len(out) + len(body))


def read_tile(path):
    """Relit une banque `.tile` → (taille, {(x, y): Image RGBA})."""
    d = open(path, "rb").read()
    ts, n = struct.unpack("<ii", d[:8])
    tiles = {}
    for i in range(n):
        x, y, off = struct.unpack("<iiq", d[8 + 16 * i:24 + 16 * i])
        ln = struct.unpack("<q", d[off:off + 8])[0]
        tiles[(x, y)] = Image.open(io.BytesIO(d[off + 8:off + 8 + ln])).convert("RGBA")
    return ts, tiles


# ----------------------------------------------------------------- .rsground
def _cell(frames, frame_length):
    if not frames:
        return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}
    return {"AutoTileset": "", "Associates": [],
            "Layers": [{"Frames": [{"Sheet": s, "TexLoc": {"X": x, "Y": y}} for s, x, y in frames],
                        "FrameLength": frame_length}],
            "NeighborCode": 0}


def map_layer(name, gw, gh, sheet, positions, draw_layer=DRAW_BOTTOM, visible=True,
              frames=1, frame_stride=0, frame_length=60):
    """Construit un MapLayer.

    `positions` : ensemble des (x, y) non vides de la planche (frame 0).
    Si `frames` > 1, la planche contient les frames côte à côte, décalées de
    `frame_stride` cellules en X (comme Altere_Pond_River_Animations chez Halcyon).
    """
    tiles = []
    for x in range(gw):
        col = []
        for y in range(gh):
            if (x, y) in positions:
                col.append(_cell([(sheet, x + f * frame_stride, y) for f in range(frames)], frame_length))
            else:
                col.append(_cell([], frame_length))
        tiles.append(col)
    return {"Name": name, "Layer": draw_layer, "Visible": visible, "Tiles": tiles}


def ground_object(name, x, y, w, h, trigger=2):
    """Objet invisible (déclencheur) — triggerType 2 = Touch, comme les *_Exit de Halcyon."""
    anim = {"$type": "RogueEssence.Content.ObjAnimData, RogueEssence", "AnimIndex": "",
            "FrameTime": 1, "StartFrame": -1, "EndFrame": -1, "AnimDir": -1, "Alpha": 255, "AnimFlip": 0}
    return {"EntName": name, "Direction": 0, "EntEnabled": True, "triggerType": trigger,
            "ObjectAnim": anim, "Passable": False,
            "CurrentAnim": dict(anim, AnimDir=0), "AnimTime": {"Ticks": 0}, "Cycles": 0,
            "DrawOffset": {"X": 0, "Y": 0},
            "Collider": {"X": x, "Y": y, "Width": w, "Height": h}}


def marker(name, x, y, direction=0):
    return {"EntName": name, "Direction": direction, "EntEnabled": True, "triggerType": 0,
            "Collider": {"X": x, "Y": y, "Width": 16, "Height": 16}}


def ground_map(asset, display_name, gw, gh, layers, obstacles, objects=(), markers=(),
               music="", comment="", version="0.7.15.1"):
    """`obstacles` : np.array (gh, gw) d'entiers Tags (0 libre, 1 mur)."""
    obs = []
    for x in range(gw):
        col = []
        for y in range(gh):
            col.append({"Bounds": {"X": x * CELL, "Y": y * CELL, "Width": CELL, "Height": CELL},
                        "Tags": int(obstacles[y, x])})
        obs.append(col)
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": 1,
        "Name": {"DefaultText": display_name, "LocalTexts": {}},
        "Released": True,
        "Comment": comment,
        "obstacles": obs,
        "rand": {"$type": "RogueElements.ReRandom, RogueElements", "FirstSeed": 0,
                 "s": [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
        "Status": {},
        "Background": {"$type": "RogueEssence.Dungeon.MapBG, RogueEssence", "MapLoc": {"X": 0, "Y": 0},
                       "BGAnim": {"AnimIndex": "", "FrameTime": 1, "StartFrame": -1, "EndFrame": -1,
                                  "AnimDir": -1, "Alpha": 255, "AnimFlip": 0},
                       "BGMovement": {"X": 0, "Y": 0}, "Parallax": "0, 0", "RepeatX": False, "RepeatY": False},
        "BlankBG": {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1},
        "Layers": layers,
        "AssetName": asset,
        "Music": music,
        "EdgeView": 1,
        "NoSwitching": False,
        "ViewCenter": None,
        "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": None,
        "Decorations": [{"Name": "New Deco", "Layer": 0, "Visible": True, "Anims": []}],
        "Entities": [{"Name": "New EntLayer", "Visible": True, "MapChars": [],
                      "GroundObjects": list(objects), "Spawners": [], "Markers": list(markers)}],
    }
    return {"Version": version, "Object": obj}


def write_rsground(path, data):
    with open(path, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def read_rsground(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def render_rsground(rsground, tile_dir, frame=0, only_visible=True):
    """Recompose l'image d'une ground map depuis ses .tile — contrôle indépendant."""
    import os
    o = rsground["Object"]
    layers = o["Layers"]
    W, H = len(layers[0]["Tiles"]), len(layers[0]["Tiles"][0])
    canvas = Image.new("RGBA", (W * CELL, H * CELL), (0, 0, 0, 0))
    sheets = {}
    for L in sorted(layers, key=lambda l: l["Layer"]):
        if only_visible and not L.get("Visible", True):
            continue
        T = L["Tiles"]
        for x in range(W):
            for y in range(H):
                for sub in T[x][y]["Layers"]:
                    fr = sub["Frames"][frame % len(sub["Frames"])]
                    name = fr["Sheet"]
                    if name not in sheets:
                        sheets[name] = read_tile(os.path.join(tile_dir, name + ".tile"))[1]
                    img = sheets[name].get((fr["TexLoc"]["X"], fr["TexLoc"]["Y"]))
                    if img is not None:
                        canvas.alpha_composite(img, (x * CELL, y * CELL))
    return canvas
