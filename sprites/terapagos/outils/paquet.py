# -*- coding: utf-8 -*-
"""Assemble le paquet Terapagos : planches AssetSprite, métadonnées, aperçu."""
import os
import sys
import json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import modele as M
from animations import ANIMS
from portraits import EMOTIONS, T

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FORMES = [("0000", "Forme Teracristal"), ("0001", "Forme Normale"),
          ("0002", "Forme Stellaire")]
MARGE = 0  # grille jointive, découpe exacte 48x48


def planche(code):
    """Planche unique toutes animations, grille régulière 48x48 sans marge."""
    base = os.path.join(R, "sprite", code)
    blocs = []
    for nom, fn, nd, desc in ANIMS:
        im = Image.open(os.path.join(base, "%s-Anim.png" % nom))
        blocs.append((nom, im))
    larg = max(b.size[0] for _, b in blocs)
    haut = sum(b.size[1] for _, b in blocs)
    out = Image.new("RGBA", (larg, haut), (0, 0, 0, 0))
    y = 0
    index = []
    for nom, im in blocs:
        out.paste(im, (0, y))
        index.append({"animation": nom, "x": 0, "y": y,
                      "largeur": im.size[0], "hauteur": im.size[1],
                      "colonnes": im.size[0] // M.L,
                      "lignes": im.size[1] // M.H})
        y += im.size[1]
    chemin = os.path.join(R, "assetsprite", "terapagos_%s_sprites.png" % code)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    out.save(chemin)
    return chemin, index


def metadonnees():
    meta = {
        "pokemon": {"numero": 1024, "nom": "Terapagos",
                    "nom_en": "Terapagos", "generation": 9},
        "convention": "PMD Sprite Collab",
        "cadre": {"largeur": M.L, "hauteur": M.H,
                  "ancre_x": M.ANCRE_X, "ancre_y": M.ANCRE_Y,
                  "taille_ombre": 1, "grille": "48x48 jointive, sans marge"},
        "directions": M.LIGNES if hasattr(M, "LIGNES") else
                      ["S", "SE", "E", "NE", "N", "NO", "O", "SO"],
        "palette": {"tons_par_matiere": 3, "anti_aliasing": False,
                    "contour": "#1A182E"},
        "formes": [], "portraits": {"taille": T, "emotions": EMOTIONS},
        "animations": [{"nom": a, "frames": len(f()), "directions": d,
                        "description": s} for a, f, d, s in ANIMS],
    }
    for code, titre in FORMES:
        chemin, index = planche(code)
        meta["formes"].append({
            "code": code, "titre": titre,
            "dossier_sprite": "sprite/%s" % code,
            "dossier_portrait": "portrait/%s" % code,
            "planche_assetsprite": os.path.relpath(chemin, R),
            "decoupe": index,
        })
    json.dump(meta, open(os.path.join(R, "terapagos.json"), "w"),
              ensure_ascii=False, indent=2)
    return meta


def apercu(meta):
    h = ["<!doctype html><html lang=fr><meta charset=utf-8>",
         "<title>Terapagos — pack PMD</title>",
         "<style>body{background:#171a24;color:#e8e6de;font:14px/1.5 system-ui;"
         "margin:0;padding:24px}h1{font-size:20px}h2{font-size:16px;margin-top:28px;"
         "border-bottom:1px solid #333a4a;padding-bottom:6px}"
         "img{image-rendering:pixelated}.g{display:flex;flex-wrap:wrap;gap:14px}"
         ".c{background:#20242f;padding:8px;border-radius:6px;text-align:center;"
         "font-size:11px;color:#9aa3b5}</style>",
         "<h1>Terapagos #1024 — pack de sprites PMD</h1>",
         "<p>Cadre 48×48, ancre (%d,%d), 8 directions, %d animations, %d émotions."
         "</p>" % (M.ANCRE_X, M.ANCRE_Y, len(ANIMS), len(EMOTIONS))]
    for f in meta["formes"]:
        h.append("<h2>%s — %s</h2>" % (f["code"], f["titre"]))
        h.append("<div class=g>")
        for a in meta["animations"]:
            h.append("<div class=c><img src='%s/%s-Anim.png' style='width:%dpx'>"
                     "<div>%s</div></div>" %
                     (f["dossier_sprite"], a["nom"],
                      min(420, a["frames"] * M.L * 2), a["nom"]))
        h.append("</div>")
        h.append("<div class=c style='display:inline-block;margin-top:12px'>"
                 "<img src='%s/Portraits.png' style='width:400px'>"
                 "<div>Portraits — 20 émotions + miroirs</div></div>"
                 % f["dossier_portrait"])
    h.append("</html>")
    open(os.path.join(R, "apercu.html"), "w").write("\n".join(h))


if __name__ == "__main__":
    m = metadonnees()
    apercu(m)
    print("planches et métadonnées écrites")
