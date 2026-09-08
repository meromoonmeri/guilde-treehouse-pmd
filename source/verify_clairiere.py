# -*- coding: utf-8 -*-
"""
verify_clairiere.py — contrôle indépendant de zones/clairiere/.

  * relit les banques .tile et le .rsground exactement comme le moteur
    (TexSize 1 → cellules de 8 px, Frames[i].TexLoc) et recompose l'image ;
  * compare aux composites PNG ;
  * relit la carte Tiled (tileset + CSV) et la recompose aussi ;
  * vérifie la grille d'obstacles (taille, valeurs, entrée sud ouverte).

    python3 source/verify_clairiere.py
"""
import os
import sys
import json
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmdo_format import CELL, read_rsground, render_rsground, read_tile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = os.path.join(ROOT, "zones", "clairiere")
ok = True


def check(cond, msg):
    global ok
    print(("  OK   " if cond else "  ECHEC") + " " + msg)
    ok &= bool(cond)


def main():
    meta = json.load(open(f"{Z}/zone.json"))
    W, H = meta["taille_px"]
    gw, gh = meta["cellules_8px"]
    check(W == gw * CELL and H == gh * CELL, f"toile {W}x{H} = {gw}x{gh} cellules de {CELL} px")
    check(W % 8 == 0 and H % 8 == 0, "multiple de 8 (grille de collision PMDO)")

    # ---- rsground
    rs = read_rsground(f"{Z}/pmdo/Data/Ground/clairiere.rsground")
    o = rs["Object"]
    check(o["TexSize"] == 1, "TexSize = 1 (cellules 8 px)")
    check(len(o["obstacles"]) == gw and len(o["obstacles"][0]) == gh, "obstacles[x][y] à la taille de la grille")
    tags = {w["Tags"] for col in o["obstacles"] for w in col}
    check(tags <= {0, 1}, f"tags d'obstacles ⊂ {{0,1}} : {sorted(tags)}")
    for L in o["Layers"]:
        T = L["Tiles"]
        check(len(T) == gw and len(T[0]) == gh, f"calque « {L['Name']} » {len(T)}x{len(T[0])}")
    tile_dir = f"{Z}/pmdo/Content/Tile"
    sheets = {fr["Sheet"] for L in o["Layers"] for col in L["Tiles"] for c in col for sub in c["Layers"] for fr in sub["Frames"]}
    for s in sorted(sheets):
        check(os.path.exists(f"{tile_dir}/{s}.tile"), f"banque {s}.tile présente")
    # toutes les TexLoc référencées existent dans la banque
    for s in sorted(sheets):
        _, tiles = read_tile(f"{tile_dir}/{s}.tile")
        refs = {(fr["TexLoc"]["X"], fr["TexLoc"]["Y"]) for L in o["Layers"] for col in L["Tiles"] for c in col
                for sub in c["Layers"] for fr in sub["Frames"] if fr["Sheet"] == s}
        manquantes = refs - set(tiles)
        check(not manquantes, f"{s} : {len(refs)} TexLoc référencées, {len(manquantes)} manquantes")

    fond = np.array(Image.open(f"{Z}/fond.png").convert("RGBA")).astype(int)
    r0 = np.array(render_rsground(rs, tile_dir, frame=0)).astype(int)
    check(np.abs(r0 - fond).max() <= 1, "rendu rsground frame 0 == fond.png (±1 d'arrondi alpha)")
    seq = meta["calques"][1]["sequence"]
    frames = [np.array(render_rsground(rs, tile_dir, frame=f)) for f in range(len(seq))]
    distinct = len({f.tobytes() for f in frames})
    check(distinct == len(set(seq)), f"eau animée : {distinct} images distinctes sur {len(seq)} frames")

    # ---- collision
    grid = np.array([[c == "#" for c in l] for l in open(f"{Z}/obstacles.txt").read().split()])
    check(grid.shape == (gh, gw), "obstacles.txt à la taille de la grille")
    rs_grid = np.array([[o["obstacles"][x][y]["Tags"] for x in range(gw)] for y in range(gh)]) == 1
    check((grid == rs_grid).all(), "obstacles.txt == obstacles du rsground")
    sud = [x for x in range(gw) if not grid[gh - 1, x]]
    check(len(sud) >= 3, f"entrée sud ouverte sur le bord : {len(sud)} cellules ({min(sud) if sud else '-'}..{max(sud) if sud else '-'})")
    objs = o["Entities"][0]["GroundObjects"]
    check(any(g["EntName"] == "South_Exit" for g in objs), "déclencheur South_Exit présent")

    # ---- Tiled
    t = ET.parse(f"{Z}/tiled/clairiere.tmx").getroot()
    ts = ET.parse(f"{Z}/tiled/clairiere_tuiles.tsx").getroot()
    cols = int(ts.attrib["columns"])
    sheet = np.array(Image.open(f"{Z}/tiled/{ts.find('image').attrib['source']}").convert("RGBA"))
    out = np.zeros((gh * CELL, gw * CELL, 4), np.uint8)
    for L in t.findall("layer"):
        if L.attrib["name"] == "Collision":
            continue
        data = [int(v) for v in L.find("data").text.replace("\n", "").split(",")]
        check(len(data) == gw * gh, f"Tiled calque « {L.attrib['name']} » : {len(data)} cases")
        for i, g in enumerate(data):
            if g == 0:
                continue
            y, x = divmod(i, gw)
            r, c = divmod(g - 1, cols)
            tl = sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            dst = out[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]
            a = tl[..., 3:4].astype(int)
            dst[..., :3] = (tl[..., :3].astype(int) * a + dst[..., :3].astype(int) * (255 - a)) // 255
            dst[..., 3] = np.maximum(dst[..., 3], tl[..., 3])
    check(np.abs(out.astype(int) - fond).max() <= 1, "recomposition Tiled == fond.png (±1)")
    anims = [x for x in ts.findall("tile") if x.find("animation") is not None]
    check(len(anims) == meta["tiled"]["animations_eau"], f"{len(anims)} tuiles animées dans le .tsx")
    col = [L for L in t.findall("layer") if L.attrib["name"] == "Collision"][0]
    data = np.array([int(v) for v in col.find("data").text.replace("\n", "").split(",")]).reshape(gh, gw)
    mur_id = int([x for x in ts.findall("tile") if x.find("properties") is not None and
                  x.find("properties/property").attrib["value"] == "mur"][0].attrib["id"]) + 1
    check(((data == mur_id) == grid).all(), "calque Collision Tiled == obstacles.txt")

    print("\nRESULTAT :", "tout est conforme" if ok else "des contrôles échouent")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
