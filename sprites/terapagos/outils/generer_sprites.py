# -*- coding: utf-8 -*-
"""Génère les feuilles d'animation Terapagos au format PMD Sprite Collab.

Sortie par forme :
  <Anim>-Anim.png    : grille frames (colonnes) x directions (lignes)
  <Anim>-Offsets.png : décalages PMD (corps vert, tête noire, gauche/droite)
  <Anim>-Shadow.png  : position d'ombre
  AnimData.xml       : métadonnées d'animation
  frames/<Anim>/...  : frames individuelles pour AssetSprite
"""
import os
import sys
import json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import modele as M
from moteur import Toile, PAL
from animations import ANIMS

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIRS = M.DIRS
# Ordre des lignes SpriteCollab : S, SE, E, NE, N, NO, O, SO (bas -> horaire)
LIGNES = ["S", "SE", "E", "NE", "N", "NO", "O", "SO"]

FORMES = {
    "0000": ("Terapagos — Forme Teracristal", dict()),
    "0001": ("Terapagos — Forme Normale", dict(variante="normale")),
    "0002": ("Terapagos — Forme Stellaire", dict(variante="stellaire")),
}


def _appliquer_variante(t, variante):
    """Reteinte de palette par variante, sans changer la géométrie."""
    if not variante:
        return t
    return t


def rendre_frame(d, p, variante=None):
    kw = {k: v for k, v in p.items() if k != "duree"}
    if variante == "normale":
        kw["forme_normale"] = True
    t = M.terapagos(d=d, **{k: v for k, v in kw.items()
                            if k in ("phase", "expr", "pas", "saut", "incl",
                                     "ecrase", "clign", "retrait", "ech")})
    return t


def teinter(im, variante):
    if not variante:
        return im
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if variante == "normale":
                # forme Normale : carapace verte opaque, fourrure crème sobre
                if b > r + 20:
                    px[x, y] = (int(r * 0.85), min(255, int(g * 1.05)),
                                int(b * 0.68), a)
            elif variante == "stellaire":
                # forme Stellaire : vitrail saturé, nervures et or plus vifs
                if b > r + 20:
                    px[x, y] = (min(255, int(r * 1.12)), min(255, int(g * 0.95)),
                                min(255, int(b * 1.10)), a)
                elif r > b + 40:
                    px[x, y] = (min(255, r), min(255, int(g * 0.95)),
                                max(0, int(b * 0.65)), a)
    return im


def generer_forme(code, variante=None):
    base = os.path.join(RACINE, "sprite", code)
    os.makedirs(base, exist_ok=True)
    meta = []
    for nom, fn, ndirs, desc in ANIMS:
        frames = fn()
        nf = len(frames)
        lignes = LIGNES if ndirs == 8 else ["S"]
        L, H = M.L, M.H
        feuille = Image.new("RGBA", (L * nf, H * len(lignes)), (0, 0, 0, 0))
        off = Image.new("RGBA", feuille.size, (0, 0, 0, 0))
        sha = Image.new("RGBA", feuille.size, (0, 0, 0, 0))
        dfr = os.path.join(base, "frames", nom)
        os.makedirs(dfr, exist_ok=True)
        for li, d in enumerate(lignes):
            for fi, p in enumerate(frames):
                t = rendre_frame(d, p, variante)
                im = teinter(t.image(ombre=M.ombre_portee(p.get("saut", 0),
                                                          p.get("ecrase", 0))),
                             variante)
                feuille.paste(im, (fi * L, li * H))
                im.save(os.path.join(dfr, "%s-%s-%02d.png" % (nom, d, fi)))
                # offsets PMD : rouge=tête, vert=corps, bleu=main G, blanc=main D
                o = Image.new("RGBA", (L, H), (0, 0, 0, 0))
                po = o.load()
                vx, vy = M.VEC[d]
                hx = int(M.ANCRE_X + vx * 8.5 + p.get("incl", 0))
                hy = int(M.ANCRE_Y - 9 + vy * 3.0 + 1.5 - p.get("saut", 0))
                po[max(0, min(L - 1, hx)), max(0, min(H - 1, hy))] = (255, 0, 0, 255)
                po[M.ANCRE_X, M.ANCRE_Y - 8] = (0, 255, 0, 255)
                po[M.ANCRE_X - 9, M.ANCRE_Y - 6] = (0, 0, 255, 255)
                po[M.ANCRE_X + 9, M.ANCRE_Y - 6] = (255, 255, 255, 255)
                off.paste(o, (fi * L, li * H))
                s = Image.new("RGBA", (L, H), (0, 0, 0, 0))
                s.load()[M.ANCRE_X, M.ANCRE_Y] = (255, 255, 255, 255)
                sha.paste(s, (fi * L, li * H))
        feuille.save(os.path.join(base, "%s-Anim.png" % nom))
        off.save(os.path.join(base, "%s-Offsets.png" % nom))
        sha.save(os.path.join(base, "%s-Shadow.png" % nom))
        meta.append((nom, nf, len(lignes), [f["duree"] for f in frames], desc))
    ecrire_animdata(base, meta)
    return meta


def ecrire_animdata(base, meta):
    x = ['<?xml version="1.0" encoding="utf-8"?>', "<AnimData>",
         "  <ShadowSize>1</ShadowSize>", "  <Anims>"]
    for nom, nf, nd, durees, desc in meta:
        x += ["    <Anim>",
              "      <Name>%s</Name>" % nom,
              "      <Index>%d</Index>" % [m[0] for m in meta].index(nom),
              "      <FrameWidth>%d</FrameWidth>" % M.L,
              "      <FrameHeight>%d</FrameHeight>" % M.H,
              "      <Durations>"]
        for d in durees:
            x.append("        <Duration>%d</Duration>" % d)
        x += ["      </Durations>",
              "      <RushFrame>%d</RushFrame>" % max(0, nf // 3),
              "      <HitFrame>%d</HitFrame>" % max(0, nf // 2),
              "      <ReturnFrame>%d</ReturnFrame>" % max(0, nf - 1),
              "    </Anim>"]
    x += ["  </Anims>", "</AnimData>", ""]
    open(os.path.join(base, "AnimData.xml"), "w").write("\n".join(x))


if __name__ == "__main__":
    resume = {}
    for code, (titre, opt) in FORMES.items():
        m = generer_forme(code, opt.get("variante"))
        resume[code] = {"titre": titre,
                        "animations": [{"nom": a, "frames": b, "directions": c}
                                       for a, b, c, _, _ in m]}
        print(code, titre, len(m), "animations")
    json.dump(resume, open(os.path.join(RACINE, "sprite", "resume.json"), "w"),
              ensure_ascii=False, indent=2)
