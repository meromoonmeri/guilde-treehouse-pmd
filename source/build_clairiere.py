# -*- coding: utf-8 -*-
"""
build_clairiere.py — la clairière à l'arbre ancien (zone-pmd@0f9805e), mise à
l'échelle PMDO et exportée dans les formats natifs du moteur.

Entrée  : source/clairiere_master/   (masters 1120 × 960 récupérés tels quels)
Sortie  : zones/clairiere/

Étapes
  1. Réduction ÷2 exacte (bloc 2×2) → 560 × 480 = 70 × 60 cellules de 8 px.
     Aucun rognage : toute l'image est conservée. Un léger masque flou puis une
     palette de 256 couleurs (k-means) redonnent des aplats nets de pixel art.
  2. Calques alpha (eau, lumières) : réduction en prémultiplié, alpha re-seuillé
     au niveau d'origine, couleurs ramenées sur la palette d'origine du calque.
  3. Collision 8 px : sol praticable = herbe + sable, relevé sur le master,
     seuillé par cellule, restreint à la composante joignable depuis le sud.
  4. Banques `.tile` + `clairiere.rsground` (RogueEssence), carte Tiled 8 px
     avec tileset dédoublonné et eau animée, PNG de contrôle.

    python3 source/build_clairiere.py
"""
import os
import sys
import json
import shutil

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmdo_format import (CELL, DRAW_BOTTOM, DRAW_TOP, TAG_LIBRE, TAG_MUR,
                         write_tile, slice_sheet, map_layer, ground_map, ground_object,
                         marker, write_rsground)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source", "clairiere_master")
OUT = os.path.join(ROOT, "zones", "clairiere")
ZONE = "clairiere"
PREFIX = "Clairiere"
SCALE = 2
PALETTE = 256

# séquences des 8 frames d'origine exprimées en états uniques
SEQ_EAU = [0, 0, 1, 1, 2, 2, 3, 3]
SEQ_RAYON = [0, 1, 2, 2, 2, 2, 2, 1]
SEQ_ETINCELLES = [0, 1, 2, 3, 4, 3, 2, 1]
FRAME_LENGTH = 8          # ticks RogueEssence par frame (60 ticks/s) → 8 frames ≈ 1,07 s
FRAME_MS = 130            # équivalent Tiled


# ------------------------------------------------------------------ réduction
def reduce_rgb(im):
    """÷2 par bloc, masque flou léger, palette k-means → RGB net."""
    w, h = im.width // SCALE, im.height // SCALE
    box = im.convert("RGB").resize((w, h), Image.BOX)
    sharp = box.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))
    a = np.array(sharp)
    z = a.reshape(-1, 3).astype(np.float32)
    cv2.setRNGSeed(7)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.25)
    _, lab, cen = cv2.kmeans(z, PALETTE, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    q = np.rint(cen[lab.ravel()]).clip(0, 255).astype(np.uint8).reshape(a.shape)
    return Image.fromarray(q, "RGB")


def reduce_alpha(im, seuil=0.5):
    """÷2 d'un calque RGBA à alpha binaire : alpha re-seuillé, couleurs d'origine.

    `seuil` = fraction du bloc 2×2 qui doit être opaque. 0.25 conserve les traits
    de 1 px du master (rides de l'eau) ; 0.5 pour les aplats (lumières)."""
    a = np.array(im.convert("RGBA")).astype(np.float32)
    alpha_val = int(a[..., 3].max())
    pal = np.unique(a[a[..., 3] > 0][:, :3].astype(np.uint8), axis=0)
    h, w = a.shape[0] // SCALE, a.shape[1] // SCALE
    al = a[..., 3:4] / 255.0
    pre = a[..., :3] * al
    blk = lambda x: x.reshape(h, SCALE, w, SCALE, -1).mean((1, 3))
    pre_r, al_r = blk(pre), blk(al)[..., 0]
    keep = al_r >= seuil
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[keep] = pre_r[keep] / al_r[keep][:, None]
    flat = rgb[keep]
    if len(pal) <= 64:
        # petite palette (eau) : plus proche couleur d'origine
        d = ((flat[:, None, :] - pal[None, :, :].astype(np.float32)) ** 2).sum(-1)
        rgb_q = pal[d.argmin(1)]
    else:
        # dégradés (lumières) : palette k-means de 64 couleurs
        cv2.setRNGSeed(7)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.25)
        k = min(64, len(flat))
        _, lab, cen = cv2.kmeans(np.ascontiguousarray(flat), k, None, crit, 2, cv2.KMEANS_PP_CENTERS)
        rgb_q = np.rint(cen[lab.ravel()]).clip(0, 255).astype(np.uint8)
    out = np.zeros((h, w, 4), np.uint8)
    out[keep, :3] = rgb_q
    out[keep, 3] = alpha_val
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ collision
def walkable_master(base_master):
    m = np.array(base_master.convert("RGB"))
    hsv = cv2.cvtColor(m, cv2.COLOR_RGB2HSV)
    h, s, v = [hsv[..., i].astype(int) for i in range(3)]
    grass = (h >= 30) & (h <= 55) & (v >= 125) & (s >= 60)
    sand = (h >= 10) & (h <= 25) & (v >= 170) & (s >= 60)
    water = (h >= 85) & (h <= 105) & (v >= 140) & (s >= 40)
    walk = (grass | sand).astype(np.uint8)
    walk = cv2.morphologyEx(walk, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    walk = cv2.morphologyEx(walk, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    wm = cv2.morphologyEx(water.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab = cv2.connectedComponents(wm)
    big = np.argmax(np.bincount(lab.ravel())[1:]) + 1
    wm = (lab == big).astype(np.uint8)
    walk[wm == 1] = 0
    return walk, wm


def collision_grid(walk, water, gw, gh, seuil=0.55):
    px = CELL * SCALE                     # taille d'une cellule sur le master
    def frac(mask):
        return mask[:gh * px, :gw * px].reshape(gh, px, gw, px).mean((1, 3))
    free = (frac(walk) >= seuil) & (frac(water) < 0.20)
    # composante joignable depuis le bord sud
    lab_n, lab = cv2.connectedComponents(free.astype(np.uint8), connectivity=4)
    south = set(lab[gh - 1, x] for x in range(gw) if free[gh - 1, x])
    south.discard(0)
    if south:
        free = np.isin(lab, list(south))
    grid = np.where(free, TAG_LIBRE, TAG_MUR).astype(np.uint8)
    return grid


# ----------------------------------------------------------------------- Tiled
def tiled_export(base, eau_states, grid, dossier):
    """Carte Tiled 8 px : tileset dédoublonné (tuiles réelles) + eau animée."""
    gw, gh = base.width // CELL, base.height // CELL
    tiles = []                 # liste de np.array 8×8×4
    index = {}

    def tid(arr):
        k = arr.tobytes()
        if k not in index:
            index[k] = len(tiles)
            tiles.append(arr.copy())
        return index[k]

    base_a = np.array(base.convert("RGBA"))
    base_ids = np.zeros((gh, gw), int)
    for y in range(gh):
        for x in range(gw):
            base_ids[y, x] = tid(base_a[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]) + 1

    eau_a = [np.array(s.convert("RGBA")) for s in eau_states]
    eau_ids = np.zeros((gh, gw), int)
    anims = {}                 # tuple d'ids d'états -> id animé
    for y in range(gh):
        for x in range(gw):
            cells = [a[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] for a in eau_a]
            if all(c[..., 3].max() == 0 for c in cells):
                continue
            ids = tuple(tid(c) for c in cells)
            if ids not in anims:
                first = ids[0]
                # un même tuile de départ ne peut porter qu'une animation
                if any(v == first for v in anims.values()):
                    tiles.append(tiles[first].copy())
                    first = len(tiles) - 1
                anims[ids] = first
            eau_ids[y, x] = anims[ids] + 1

    # tuiles de collision (2 pinceaux) ajoutées en fin de tileset
    libre = np.zeros((CELL, CELL, 4), np.uint8)
    libre[..., :] = (0, 0, 0, 0)
    mur = np.zeros((CELL, CELL, 4), np.uint8)
    mur[..., :] = (220, 40, 70, 150)
    id_libre = len(tiles); tiles.append(libre)
    id_mur = len(tiles); tiles.append(mur)
    col_ids = np.where(grid == TAG_MUR, id_mur + 1, id_libre + 1)

    cols = 32
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.zeros((rows * CELL, cols * CELL, 4), np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = t
    Image.fromarray(sheet, "RGBA").save(f"{dossier}/{ZONE}_tuiles.png", optimize=True)

    tsx = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<tileset version="1.10" tiledversion="1.10.2" name="{ZONE}_tuiles" '
           f'tilewidth="{CELL}" tileheight="{CELL}" tilecount="{len(tiles)}" columns="{cols}">',
           f' <image source="{ZONE}_tuiles.png" width="{cols * CELL}" height="{rows * CELL}"/>']
    for ids, first in anims.items():
        frames = "".join(f'<frame tileid="{ids[s]}" duration="{FRAME_MS}"/>' for s in SEQ_EAU)
        tsx.append(f' <tile id="{first}"><animation>{frames}</animation></tile>')
    tsx.append(f' <tile id="{id_libre}"><properties><property name="collision" value="libre"/></properties></tile>')
    tsx.append(f' <tile id="{id_mur}"><properties><property name="collision" value="mur"/></properties></tile>')
    tsx.append('</tileset>')
    open(f"{dossier}/{ZONE}_tuiles.tsx", "w").write("\n".join(tsx))

    def layer(lid, name, ids, opacity=1.0, visible=True):
        rows_csv = ",\n".join(",".join(str(v) for v in row) for row in ids)
        vis = "" if visible else ' visible="0"'
        return (f' <layer id="{lid}" name="{name}" width="{gw}" height="{gh}" opacity="{opacity}"{vis}>\n'
                f'  <data encoding="csv">\n{rows_csv}\n  </data>\n </layer>')

    tmx = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" '
           f'width="{gw}" height="{gh}" tilewidth="{CELL}" tileheight="{CELL}" infinite="0" '
           f'nextlayerid="5" nextobjectid="3">',
           ' <properties>',
           '  <property name="moteur" value="RogueEssence / PMDO"/>',
           '  <property name="cellule_collision_px" type="int" value="8"/>',
           '  <property name="case_lecture_px" type="int" value="24"/>',
           '  <property name="viewport" value="320x240"/>',
           ' </properties>',
           f' <tileset firstgid="1" source="{ZONE}_tuiles.tsx"/>',
           layer(1, "Base", base_ids),
           layer(2, "Eau", eau_ids),
           layer(3, "Collision", col_ids, 0.6),
           '</map>']
    open(f"{dossier}/{ZONE}.tmx", "w").write("\n".join(tmx))
    return dict(tuiles=len(tiles), tuiles_base=int(len(np.unique(base_ids))),
                animations_eau=len(anims), cases=gw * gh)


# --------------------------------------------------------------------- aperçus
def apercu_collision(fond, grid, path):
    im = fond.convert("RGBA").copy()
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    gh, gw = grid.shape
    for y in range(gh):
        for x in range(gw):
            if grid[y, x] == TAG_MUR:
                d.rectangle([x * CELL, y * CELL, (x + 1) * CELL - 1, (y + 1) * CELL - 1], fill=(255, 60, 90, 90))
    for x in range(0, im.width, 24):
        d.line([(x, 0), (x, im.height)], fill=(255, 255, 255, 40))
    for y in range(0, im.height, 24):
        d.line([(0, y), (im.width, y)], fill=(255, 255, 255, 40))
    # cadre viewport 320×240 centré sur le bassin
    cx, cy = im.width // 2, im.height // 2
    d.rectangle([cx - 160, cy - 120, cx + 159, cy + 119], outline=(255, 255, 0, 200), width=1)
    im.alpha_composite(ov)
    im.save(path, optimize=True)


def apercu_echelle(fond, grid, path):
    """Sprites étalon de Halcyon (Salamèche, Arcko) posés à 1:1 sur des cellules libres."""
    halcyon = os.environ.get("HALCYON_DIR", "/tmp/halcyon")
    charas = [os.path.join(halcyon, f) for f in ("4.chara", "252.chara")]
    if not all(os.path.exists(c) for c in charas):
        charas = [os.path.join(halcyon, "Content", "Chara", f) for f in ("4.chara", "252.chara")]
    if not all(os.path.exists(c) for c in charas):
        print("  (aperçu d'échelle sauté : .chara de Halcyon introuvables, HALCYON_DIR)")
        return
    sys.path.insert(0, os.path.join(ROOT, "analyse_echelle"))
    from apercus import sprite_from_chara
    sprs = [sprite_from_chara(c) for c in charas]
    im = fond.convert("RGBA").copy()
    gh, gw = grid.shape
    libres = [(x, y) for y in range(gh) for x in range(gw) if grid[y, x] == TAG_LIBRE]
    cibles = [(35, 59), (22, 34), (49, 34), (35, 25), (27, 44), (44, 46)]
    d = ImageDraw.Draw(im)
    for i, (cx, cy) in enumerate(cibles):
        x, y = min(libres, key=lambda c: (c[0] - cx) ** 2 + (c[1] - cy) ** 2)
        fx, fy = x * CELL + CELL // 2, (y + 1) * CELL
        spr = sprs[i % len(sprs)]
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([fx - 7, fy - 2, fx + 7, fy + 2], fill=(0, 0, 0, 70))
        im.alpha_composite(ov)
        im.alpha_composite(spr, (fx - spr.width // 2, fy - spr.height))
    cx, cy = im.width // 2, im.height // 2
    d.rectangle([cx - 160, cy - 120, cx + 159, cy + 119], outline=(255, 255, 0, 220))
    im.save(path, optimize=True)


# ------------------------------------------------------------------------ main
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for d in ("calques", "pmdo/Content/Tile", "pmdo/Data/Ground", "tiled"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    master = Image.open(os.path.join(SRC, "base.png"))
    assert master.size == (1120, 960), master.size
    W, H = master.width // SCALE, master.height // SCALE
    gw, gh = W // CELL, H // CELL
    print(f"master {master.size} -> {W}x{H} = {gw}x{gh} cellules de {CELL} px")

    # 1. base
    base = reduce_rgb(master)
    base.save(f"{OUT}/calques/00_base.png", optimize=True)
    print("  base :", len(base.getcolors(1 << 24)), "couleurs")

    # 2. calques alpha
    def states(sub, seuil=0.5):
        files = sorted(f for f in os.listdir(os.path.join(SRC, sub)) if f.endswith(".png"))
        return [reduce_alpha(Image.open(os.path.join(SRC, sub, f)), seuil) for f in files]
    eau = states("eau", 0.25)
    rayon = states("lumiere_simple")
    etincelles = states("lumiere_evolution")
    for i, s in enumerate(eau):
        s.save(f"{OUT}/calques/01_eau_etat{i}.png", optimize=True)
    for i, s in enumerate(rayon):
        s.save(f"{OUT}/calques/02_lumiere_rayon_etat{i}.png", optimize=True)
    for i, s in enumerate(etincelles):
        s.save(f"{OUT}/calques/03_lumiere_etincelles_etat{i}.png", optimize=True)
    print(f"  eau {len(eau)} états, rayon {len(rayon)} états, étincelles {len(etincelles)} états")

    # 3. collision
    walk, water = walkable_master(master)
    grid = collision_grid(walk, water, gw, gh)
    libres = int((grid == TAG_LIBRE).sum())
    print(f"  collision : {libres} cellules libres / {gw * gh} ({100 * libres / (gw * gh):.1f} %)")
    Image.fromarray(np.where(grid == TAG_MUR, 255, 0).astype(np.uint8), "L").save(f"{OUT}/collision.png")
    with open(f"{OUT}/obstacles.txt", "w") as f:
        f.write("\n".join("".join("#" if v else "." for v in row) for row in grid) + "\n")

    # entrée sud : cellules libres de la dernière ligne
    xs = [x for x in range(gw) if grid[gh - 1, x] == TAG_LIBRE]
    sud = dict(x0=min(xs), x1=max(xs)) if xs else None
    print("  entrée sud : cellules", sud)

    # 4. banques .tile
    tile_dir = f"{OUT}/pmdo/Content/Tile"
    stats = {}
    stats["Base"] = write_tile(f"{tile_dir}/{PREFIX}_Base.tile", base.convert("RGBA"))
    pos_base = set(slice_sheet(base.convert("RGBA"))[0])

    def anim_sheet(name, sts):
        """États côte à côte ; une cellule utilisée dans un état l'est dans tous (tuiles vides forcées)."""
        n = len(sts)
        sheet = Image.new("RGBA", (W * n, H), (0, 0, 0, 0))
        for i, s in enumerate(sts):
            sheet.paste(s, (i * W, 0))
        used = set()
        for s in sts:
            used |= set(slice_sheet(s)[0])
        arr = np.array(sheet)
        # forcer une tuile vide non transparente ? Non : on marque les cellules
        # vides d'un alpha 1 invisible pour qu'elles existent dans la banque.
        for (x, y) in used:
            for i in range(n):
                cx = (x + i * gw) * CELL
                blk = arr[y * CELL:(y + 1) * CELL, cx:cx + CELL]
                if blk[..., 3].max() == 0:
                    blk[0, 0, 3] = 1
        st = write_tile(f"{tile_dir}/{PREFIX}_{name}.tile", arr)
        Image.fromarray(arr, "RGBA").save(f"{OUT}/calques/planche_{name.lower()}.png", optimize=True)
        return st, used

    stats["Eau"], pos_eau = anim_sheet("Eau", eau)
    stats["Lumiere_Rayon"], pos_rayon = anim_sheet("Lumiere_Rayon", rayon)
    stats["Lumiere_Etincelles"], pos_etin = anim_sheet("Lumiere_Etincelles", etincelles)
    for k, v in stats.items():
        print(f"  {PREFIX}_{k}.tile : {v['entrees']} entrées, {v['uniques']} uniques, {v['octets'] // 1024} Ko")

    # 5. rsground
    def anim_layer(name, sheet, positions, seq, draw, visible):
        tiles = []
        for x in range(gw):
            col = []
            for y in range(gh):
                if (x, y) in positions:
                    col.append({"AutoTileset": "", "Associates": [],
                                "Layers": [{"Frames": [{"Sheet": sheet, "TexLoc": {"X": x + s * gw, "Y": y}} for s in seq],
                                            "FrameLength": FRAME_LENGTH}],
                                "NeighborCode": 0})
                else:
                    col.append({"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1})
            tiles.append(col)
        return {"Name": name, "Layer": draw, "Visible": visible, "Tiles": tiles}

    layers = [
        map_layer("Base", gw, gh, f"{PREFIX}_Base", pos_base, DRAW_BOTTOM),
        anim_layer("Eau", f"{PREFIX}_Eau", pos_eau, SEQ_EAU, DRAW_BOTTOM, True),
        anim_layer("Lumiere Rayon", f"{PREFIX}_Lumiere_Rayon", pos_rayon, SEQ_RAYON, DRAW_TOP, False),
        anim_layer("Lumiere Etincelles", f"{PREFIX}_Lumiere_Etincelles", pos_etin, SEQ_ETINCELLES, DRAW_TOP, False),
    ]
    objets, marqueurs = [], []
    if sud:
        x0, x1 = sud["x0"] * CELL, (sud["x1"] + 1) * CELL
        objets.append(ground_object("South_Exit", x0, H - CELL, x1 - x0, CELL))
        cx = (x0 + x1) // 2
        marqueurs.append(marker("Main_Entrance_Marker", cx - 8, H - 3 * CELL, direction=0))
    rs = ground_map(ZONE, "Clairière de l'arbre ancien", gw, gh, layers, grid, objets, marqueurs,
                    comment="Clairiere zone-pmd@0f9805e, master 1120x960 reduit /2, palette 256.")
    write_rsground(f"{OUT}/pmdo/Data/Ground/{ZONE}.rsground", rs)
    print("  rsground écrit")

    # 6. Tiled
    ts = tiled_export(base, eau, grid, f"{OUT}/tiled")
    print("  tiled :", ts)

    # 7. composites et aperçus
    fond = base.convert("RGBA")
    fond.alpha_composite(eau[0])
    fond.save(f"{OUT}/fond.png", optimize=True)
    lum = fond.copy(); lum.alpha_composite(rayon[0]); lum.alpha_composite(etincelles[0])
    lum.save(f"{OUT}/fond_lumiere.png", optimize=True)
    apercu_collision(fond, grid, f"{OUT}/apercu_collision.png")
    apercu_echelle(fond, grid, f"{OUT}/apercu_echelle.png")
    fond.resize((W * 3, H * 3), Image.NEAREST).save(f"{OUT}/apercu_x3.png", optimize=True)
    strip = Image.new("RGBA", (W * len(eau), H))
    for i, s in enumerate(eau):
        f = base.convert("RGBA"); f.alpha_composite(s); strip.paste(f, (i * W, 0))
    strip.crop((0, 200, W * len(eau), 380)).save(f"{OUT}/apercu_eau_frames.png", optimize=True)

    # 8. descripteur
    meta = dict(
        zone=ZONE, source="meromoonmeri/zone-pmd@0f9805e (layers/src/clairiere_pmdo + render_layers)",
        master_px=[1120, 960], facteur=f"1/{SCALE}", taille_px=[W, H], cellules_8px=[gw, gh],
        cases_24px=[round(W / 24, 2), round(H / 24, 2)], ecrans_320x240=round(W * H / (320 * 240), 2),
        palette_base=len(base.getcolors(1 << 24)),
        collision=dict(libres=libres, murs=int(gw * gh - libres), fichier="obstacles.txt", masque="collision.png"),
        entree_sud=sud,
        calques=[
            dict(nom="Base", tile=f"{PREFIX}_Base.tile", draw_layer="Bottom", frames=1),
            dict(nom="Eau", tile=f"{PREFIX}_Eau.tile", draw_layer="Bottom", etats=len(eau), sequence=SEQ_EAU, frame_length_ticks=FRAME_LENGTH),
            dict(nom="Lumiere Rayon", tile=f"{PREFIX}_Lumiere_Rayon.tile", draw_layer="Top", visible=False, etats=len(rayon), sequence=SEQ_RAYON),
            dict(nom="Lumiere Etincelles", tile=f"{PREFIX}_Lumiere_Etincelles.tile", draw_layer="Top", visible=False, etats=len(etincelles), sequence=SEQ_ETINCELLES),
        ],
        tile_stats=stats, tiled=ts,
    )
    json.dump(meta, open(f"{OUT}/zone.json", "w"), indent=1, ensure_ascii=False)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
