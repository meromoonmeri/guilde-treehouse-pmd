"""
generer_donjon.py — un étage de donjon construit intégralement, méthode EoS.

Rien n'est prélevé sur le jeu. La chaîne complète :

  1. textures de base produites au générateur d'image ;
  2. fabrication des 47 tuiles de chaque terrain au format DTEF ;
  3. génération de l'étage à la manière de Mystery Dungeon — grille de
     cellules, salles, couloirs de liaison ;
  4. pose par autotuilage : la configuration des 8 voisines est réduite à sa
     règle de base, qui désigne la tuile ;
  5. animation de l'eau par substitution de palette (DPLA) ;
  6. export en calques, planche DTEF + XML, .tsx et .tmx Tiled, .aseprite.
"""

import os
import sys
import json
import math
import numpy as np
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
sys.path.insert(0, os.path.join(ICI, "..", "..", "zones_pmd", "outils"))
import dtef_kit as K
import dpla as DPLA
import liquides as LQ
import aseprite

RACINE = os.path.abspath(os.path.join(ICI, ".."))
T = K.T
MUR, SOL, SEC = 0, 1, 2                     # types de terrain
COLS, LIGNES = 32, 24                       # taille de l'étage, en tuiles
DUREE_MS = 100


# --------------------------------------------------------------------------
# Génération de l'étage, à la façon de Mystery Dungeon
# --------------------------------------------------------------------------

def generer_etage(rng, cel_x=4, cel_y=3, part_salles=0.75, part_eau=0.55):
    """
    L'étage est découpé en cellules ; certaines reçoivent une salle, les
    autres restent vides. Les cellules voisines sont ensuite reliées par des
    couloirs. C'est la structure des donjons de la série : des salles
    rectangulaires cousues par des corridors d'une case de large.
    """
    g = np.full((LIGNES, COLS), MUR, dtype=np.int8)
    lc, hc = COLS // cel_x, LIGNES // cel_y
    salles = {}
    for cy in range(cel_y):
        for cx in range(cel_x):
            if rng.random() > part_salles:
                continue
            marge = 2
            lmax = lc - marge * 2
            hmax = hc - marge * 2
            if lmax < 3 or hmax < 3:
                continue
            w = int(rng.integers(3, max(4, lmax + 1)))
            h = int(rng.integers(3, max(4, hmax + 1)))
            x0 = cx * lc + marge + int(rng.integers(0, max(1, lmax - w + 1)))
            y0 = cy * hc + marge + int(rng.integers(0, max(1, hmax - h + 1)))
            g[y0:y0 + h, x0:x0 + w] = SOL
            salles[(cx, cy)] = (x0, y0, w, h)

    def centre(s):
        x0, y0, w, h = s
        return (x0 + w // 2, y0 + h // 2)

    def couloir(a, b):
        (xa, ya), (xb, yb) = a, b
        if rng.random() < 0.5:
            for x in range(min(xa, xb), max(xa, xb) + 1):
                g[ya, x] = SOL if g[ya, x] == MUR else g[ya, x]
            for y in range(min(ya, yb), max(ya, yb) + 1):
                g[y, xb] = SOL if g[y, xb] == MUR else g[y, xb]
        else:
            for y in range(min(ya, yb), max(ya, yb) + 1):
                g[y, xa] = SOL if g[y, xa] == MUR else g[y, xa]
            for x in range(min(xa, xb), max(xa, xb) + 1):
                g[yb, x] = SOL if g[yb, x] == MUR else g[yb, x]

    cles = sorted(salles)
    for i, k in enumerate(cles):
        cx, cy = k
        for vk in ((cx + 1, cy), (cx, cy + 1)):
            if vk in salles:
                couloir(centre(salles[k]), centre(salles[vk]))
    # une liaison de plus, pour éviter les étages en simple arbre
    if len(cles) > 2:
        a, b = rng.choice(len(cles), 2, replace=False)
        couloir(centre(salles[cles[a]]), centre(salles[cles[b]]))

    # nappes d'eau au cœur de certaines salles
    for k, (x0, y0, w, h) in salles.items():
        if rng.random() > part_eau or w < 4 or h < 3:
            continue
        mx = x0 + 1 + int(rng.integers(0, max(1, w - 3)))
        my = y0 + 1 + int(rng.integers(0, max(1, h - 3)))
        rw = int(rng.integers(2, max(3, w - 1)))
        rh = int(rng.integers(2, max(3, h - 1)))
        for y in range(my, min(my + rh, y0 + h - 1)):
            for x in range(mx, min(mx + rw, x0 + w - 1)):
                g[y, x] = SEC

    g[0, :] = MUR
    g[-1, :] = MUR
    g[:, 0] = MUR
    g[:, -1] = MUR
    return g, salles


def regle_de(g, x, y):
    """Configuration des 8 voisines : bit posé si le voisin est du même type."""
    t = g[y, x]
    r = 0
    for bit, (dx, dy) in ((K.N, (0, -1)), (K.S, (0, 1)), (K.W, (-1, 0)),
                          (K.E, (1, 0)), (K.NW, (-1, -1)), (K.NE, (1, -1)),
                          (K.SW, (-1, 1)), (K.SE, (1, 1))):
        nx, ny = x + dx, y + dy
        meme = True if not (0 <= nx < COLS and 0 <= ny < LIGNES) else g[ny, nx] == t
        if meme:
            r |= bit
    return r


# --------------------------------------------------------------------------
# Assemblage
# --------------------------------------------------------------------------

def charger_textures():
    src = os.path.join(RACINE, "sources_ia", "textures_base.png")
    brutes = LQ.decouper(src, ech=6, aire_min=0.01)
    if len(brutes) < 4:
        raise SystemExit(f"textures insuffisantes ({len(brutes)})")
    # ordre de la planche : sol, dessus de mur, eau, face de falaise
    return {"sol": brutes[0], "mur": brutes[1], "eau": brutes[2],
            "face": brutes[3]}


def moyenne(im, k=1.0):
    a = np.asarray(im.convert("RGB"), dtype=np.float32).reshape(-1, 3).mean(0)
    return tuple(int(min(255, v * k)) for v in a)


def main(graine=7):
    for d in ("tileset", "calques", "tiled", "aseprite", "apercus"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)
    rng = np.random.default_rng(graine)
    tex = charger_textures()

    sections = {
        "mur": K.construire_type(tex["mur"], moyenne(tex["mur"], 1.45),
                                 moyenne(tex["mur"], 0.45),
                                 face=tex["face"], graine=1),
        "secondaire": K.construire_type(tex["eau"], moyenne(tex["eau"], 1.5),
                                        moyenne(tex["eau"], 0.5), graine=2),
        "sol": K.construire_type(tex["sol"], moyenne(tex["sol"], 1.30),
                                 moyenne(tex["sol"], 0.55), graine=3),
    }
    planche = K.assembler(sections)
    planche.save(os.path.join(RACINE, "tileset", "tileset_0.png"), optimize=True)

    # Variantes. Le format prévoit des fichiers tileset_1, tileset_2, etc. :
    # même disposition, autres échantillons de texture. Sans elles, la masse
    # de mur se répète en bandes très visibles.
    variantes = [planche]
    for v in (1, 2, 3, 4):
        s2 = {
            "mur": K.construire_type(tex["mur"], moyenne(tex["mur"], 1.45),
                                     moyenne(tex["mur"], 0.45),
                                     face=tex["face"], graine=10 + v),
            "secondaire": K.construire_type(tex["eau"], moyenne(tex["eau"], 1.5),
                                            moyenne(tex["eau"], 0.5),
                                            graine=20 + v),
            "sol": K.construire_type(tex["sol"], moyenne(tex["sol"], 1.30),
                                     moyenne(tex["sol"], 0.55), graine=30 + v),
        }
        p2 = K.assembler(s2)
        p2.save(os.path.join(RACINE, "tileset", f"tileset_{v}.png"), optimize=True)
        variantes.append(p2)

    # animation de l'eau : rampe relevée sur la section secondaire
    rampe = DPLA.rampe_depuis_tuiles(
        [sections["secondaire"].crop((0, 0, T, T)).convert("RGB"),
         sections["secondaire"].crop((T, T, 2 * T, 2 * T)).convert("RGB")], 12)
    table = DPLA.table_depuis_rampe(rampe)
    n_img = 12
    periode = table.periode(0) or 12
    pas = max(1, periode // n_img)
    images_pal = [table.palette_a_l_image(0, k * pas) for k in range(n_img)]
    durees = [e.get("duree", 6) for e in table.emplacements[:16]]
    K.ecrire_xml(os.path.join(RACINE, "tileset", "tileset.dtef.xml"),
                 animations=[(10, images_pal, durees)])
    table.ecrire_json(os.path.join(RACINE, "tileset", "eau_dpla.json"))

    # étage
    g, salles = generer_etage(rng)
    print(f"  étage {COLS}x{LIGNES} : {len(salles)} salles, "
          f"{int((g == SOL).sum())} cases de sol, {int((g == SEC).sum())} d'eau")

    # calques : un par type de terrain
    noms = {MUR: "00_mur", SOL: "01_sol", SEC: "02_eau"}
    idx_type = {MUR: 0, SEC: 1, SOL: 2}          # ordre du format
    calques = {n: Image.new("RGBA", (COLS * T, LIGNES * T)) for n in noms.values()}
    for y in range(LIGNES):
        for x in range(COLS):
            t = int(g[y, x])
            pl = variantes[(x * 3 + y * 7 + (x // 2) * 5 + t) % len(variantes)]
            tuile = K.tuile_pour(pl, idx_type[t], regle_de(g, x, y))
            calques[noms[t]].paste(tuile, (x * T, y * T))

    # l'eau animée, image par image
    r = np.array(rampe, dtype=np.float32)
    base_eau = np.array(calques["02_eau"])
    plein = base_eau[..., 3] > 0
    if plein.any():
        px = base_eau[plein][:, :3].astype(np.float32)
        carte = np.zeros(base_eau.shape[:2], dtype=np.int32)
        carte[plein] = np.argmin(np.linalg.norm(px[:, None, :] - r[None, :, :],
                                                axis=2), axis=1)
    images = []
    for k in range(n_img):
        eau = calques["02_eau"]
        if plein.any():
            pal = images_pal[k]
            tab = np.array([pal[i] if i < len(pal) else rampe[min(i, len(rampe) - 1)]
                            for i in range(len(rampe))], dtype=np.uint8)
            o = np.zeros_like(base_eau)
            o[..., :3] = tab[np.clip(carte, 0, len(tab) - 1)]
            o[..., 3] = np.where(plein, 255, 0)
            eau = Image.fromarray(o, "RGBA")
        images.append({"00_mur": calques["00_mur"], "01_sol": calques["01_sol"],
                       "02_eau": eau})

    for nom, im in images[0].items():
        im.save(os.path.join(RACINE, "calques", f"{nom}.png"), optimize=True)
    compose = []
    for jeu in images:
        c = Image.new("RGBA", (COLS * T, LIGNES * T), (0, 0, 0, 255))
        for n in ("00_mur", "01_sol", "02_eau"):
            c = Image.alpha_composite(c, jeu[n])
        compose.append(c)
    compose[0].convert("RGB").save(os.path.join(RACINE, "calques", "compose.png"),
                                   optimize=True)

    structure = [{"nom": "00_mur"}, {"nom": "01_sol"}, {"nom": "02_eau"}]
    aseprite.ecrire_avance(os.path.join(RACINE, "aseprite", "etage.aseprite"),
                           structure, images, (COLS * T, LIGNES * T),
                           duree_ms=DUREE_MS,
                           palette=[tuple(c) for c in rampe],
                           tags=[("eau", 0, n_img - 1, aseprite.AVANT,
                                  (90, 170, 230))])

    gif = [c.convert("P", palette=Image.ADAPTIVE, colors=128) for c in compose]
    gif[0].save(os.path.join(RACINE, "apercus", "etage.gif"), save_all=True,
                append_images=gif[1:], duration=DUREE_MS, loop=0, disposal=2,
                optimize=True)

    ecrire_tiled(g, planche, idx_type)
    json.dump({"cols": COLS, "lignes": LIGNES, "tuile": T,
               "salles": len(salles), "regles": 47,
               "types": list(K.TYPES), "images_eau": n_img,
               "periode_tics": table.periode(0)},
              open(os.path.join(RACINE, "etage.json"), "w"), indent=1,
              ensure_ascii=False)
    print("  planche DTEF, XML, calques, .aseprite, .tsx, .tmx et GIF écrits")


def ecrire_tiled(g, planche, idx_type):
    """Jeu de tuiles et carte Tiled reprenant la planche DTEF telle quelle."""
    w, h = planche.size
    cols_ts = w // T
    total = (w // T) * (h // T)
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<tileset version="1.10" tiledversion="1.10.2" name="donjon_eos" '
         f'tilewidth="{T}" tileheight="{T}" tilecount="{total}" '
         f'columns="{cols_ts}">',
         f' <image source="../tileset/tileset_0.png" width="{w}" height="{h}"/>',
         '</tileset>']
    open(os.path.join(RACINE, "tiled", "donjon_eos.tsx"), "w").write(
        "\n".join(L) + "\n")

    lignes_csv = []
    for y in range(LIGNES):
        ligne = []
        for x in range(COLS):
            t = int(g[y, x])
            i = K.index_regle(regle_de(g, x, y))
            gid = 1 + idx_type[t] * (K.COLS * K.LIGNES) + i
            ligne.append(str(gid))
        lignes_csv.append(",".join(ligne))
    M = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" '
         f'renderorder="right-down" width="{COLS}" height="{LIGNES}" '
         f'tilewidth="{T}" tileheight="{T}" infinite="0" nextlayerid="2" '
         f'nextobjectid="1">',
         ' <tileset firstgid="1" source="donjon_eos.tsx"/>',
         f' <layer id="1" name="terrain" width="{COLS}" height="{LIGNES}">',
         '  <data encoding="csv">', ",\n".join(lignes_csv),
         '  </data>', ' </layer>', '</map>']
    open(os.path.join(RACINE, "tiled", "etage.tmx"), "w").write("\n".join(M) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
