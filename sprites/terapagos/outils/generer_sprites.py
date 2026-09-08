# -*- coding: utf-8 -*-
"""Génère le dossier sprite/ au format exact PMD Sprite Collab.

Source : bases/<DIR>.png (poses nettes dérivées de l'artwork officiel).
Les animations sont produites par transformations entières de la pose de base
(translation, écrasement, saut, inclinaison) — jamais de redimensionnement
interpolé, afin de préserver la grille de pixels et la palette.

Conforme à la spec PMDOWiki (Tutorial:PMD Sprite Format) :
  - noms d'animations pris dans la liste officielle ;
  - <Index> officiels (Walk 0, Attack 1, Sleep 5, Hurt 6, Idle 7, ...) ;
  - <CopyOf> pour les animations dupliquées ;
  - FrameWidth/FrameHeight pairs, identiques aux PNG ;
  - Offsets.png : VERT = centre du corps, ROUGE = main gauche,
    BLEU = main droite, NOIR = tête ;
  - Shadow.png : pixel BLANC = centre du sprite au sol.
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from importer_base import importer, PALETTE  # noqa

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
L = H = 48
ANCRE_X, ANCRE_Y = 24, 40
# Ordre des lignes = ordre des directions PMD (bas, puis sens horaire).
LIGNES = ["S", "SO", "O", "NO", "N", "NE", "E", "SE"]

FORMES = {
    "0000": ("Terapagos — Forme Teracristal", None),
    "0001": ("Terapagos — Forme Normale", "normale"),
    "0002": ("Terapagos — Forme Stellaire", "stellaire"),
}


# --------------------------------------------------------------------------
# Animations : nom officiel, index officiel, 8 directions ?, frames.
# Chaque frame = (dx, dy, ecrase, duree) appliqué à la pose de base.
def _idle():
    return [(0, 0, 0, 20), (0, -1, 0, 14), (0, 0, 0, 20), (0, 0, 1, 14)]


def _walk():
    return [(0, 0, 0, 8), (0, -1, 0, 6), (0, 0, 0, 8), (0, -1, 0, 6)]


def _attack():
    return [(0, 0, 2, 4), (-1, 0, 3, 4), (2, -2, 0, 2), (3, 0, 1, 3),
            (1, 0, 1, 4), (0, 0, 0, 6)]


def _shoot():
    return [(0, 0, 1, 4), (-1, 0, 2, 5), (1, -1, 0, 3), (0, 0, 1, 4),
            (0, 0, 0, 6)]


def _strike():
    return [(0, -3, 0, 4), (0, -5, 0, 3), (0, 0, 4, 4), (0, 0, 1, 5),
            (0, 0, 0, 6)]


def _swing():
    return [(-1, 0, 1, 3), (-2, 0, 2, 3), (1, -1, 0, 3), (2, 0, 1, 3),
            (0, 0, 0, 5)]


def _hurt():
    return [(-2, 0, 2, 4), (-3, 0, 1, 8), (-1, 0, 0, 5), (0, 0, 0, 6)]


def _sleep():
    return [(0, 0, 2, 30), (0, 0, 3, 35)]


def _charge():
    return [(0, 0, 1, 6), (1, 0, 2, 6), (0, 0, 1, 6), (-1, 0, 2, 6)]


def _rotate():
    return [(0, 0, 1, 3), (1, 0, 2, 3), (0, 0, 3, 3), (-1, 0, 2, 3),
            (0, 0, 1, 3), (0, 0, 0, 3)]


def _hop():
    return [(0, 0, 4, 4), (0, -4, 0, 4), (0, -7, 0, 5), (0, -4, 0, 4),
            (0, 0, 4, 4), (0, 0, 0, 5)]


def _double():
    return [(0, 0, 0, 3), (-2, 0, 0, 3), (2, 0, 0, 3), (0, 0, 0, 3),
            (-2, 0, 0, 3), (2, 0, 0, 3), (0, 0, 0, 4)]


ANIMS = [
    # nom,       index, 8 dirs, frames,   copie de
    ("Walk",     0,  True,  _walk,   None),
    ("Attack",   1,  True,  _attack, None),
    ("Strike",   2,  True,  _strike, None),
    ("Shoot",    3,  True,  _shoot,  None),
    ("Twirl",    4,  None,  None,    "Rotate"),
    ("Sleep",    5,  False, _sleep,  None),
    ("Hurt",     6,  True,  _hurt,   None),
    ("Idle",     7,  True,  _idle,   None),
    ("Swing",    8,  True,  _swing,  None),
    ("Double",   9,  True,  _double, None),
    ("Hop",     10,  True,  _hop,    None),
    ("Charge",  11,  True,  _charge, None),
    ("Rotate",  12,  True,  _rotate, None),
]

# Frames d'attaque : Rush / Hit / Return (spec PMD).
CLES = {"Attack": (1, 3, 5), "Strike": (None, 2, 4), "Shoot": (None, 2, 4),
        "Swing": (None, 2, 4), "Charge": (None, 2, 3), "Rotate": (None, 3, None),
        "Hop": (None, 3, None)}


# --------------------------------------------------------------- rendu ----
def transformer(base, dx, dy, ecrase):
    """Translation entière + écrasement par suppression de lignes.

    Aucun filtrage : on retire `ecrase` lignes réparties dans la hauteur du
    sprite et on redescend le tout sur la ligne de sol. La palette et la
    grille de pixels restent donc strictement intactes.
    """
    bb = base.getbbox()
    out = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    if bb is None:
        return out
    c = base.crop(bb)
    if ecrase > 0:
        w, hh = c.size
        garder = [y for y in range(hh)]
        if ecrase < hh - 2:
            pas = hh / float(ecrase + 1)
            retirer = {int(pas * (k + 1)) for k in range(ecrase)}
            garder = [y for y in range(hh) if y not in retirer]
        n = Image.new("RGBA", (w, len(garder)), (0, 0, 0, 0))
        for j, y in enumerate(garder):
            n.paste(c.crop((0, y, w, y + 1)), (0, j))
        c = n
    # ancrage : pieds sur ANCRE_Y, centre horizontal sur ANCRE_X
    x = ANCRE_X - c.size[0] // 2 + dx
    y = ANCRE_Y - c.size[1] + dy
    out.paste(c, (x, y), c)
    return out


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
                # Forme Normale : carapace opaque verte, vitrail éteint
                if b > r and b > 70:
                    px[x, y] = (int(r * 0.80), min(255, int(g * 1.06)),
                                int(b * 0.70), a)
            else:
                # Forme Stellaire : vitrail plus saturé, or plus vif
                if b > r:
                    px[x, y] = (min(255, int(r * 1.10)), int(g * 0.94),
                                min(255, int(b * 1.12)), a)
                elif r > b + 40:
                    px[x, y] = (min(255, r), min(255, int(g * 0.96)),
                                int(b * 0.70), a)
    return im


def offsets_frame(d):
    """Offsets PMD : vert corps, rouge main G, bleu main D, noir tête."""
    o = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    p = o.load()
    p[ANCRE_X, ANCRE_Y - 6] = (0, 255, 0, 255)          # centre du corps
    tetes = {"S": (24, 33), "SE": (30, 32), "E": (34, 31), "NE": (30, 30),
             "N": (24, 29), "NO": (18, 30), "O": (14, 31), "SO": (18, 32)}
    tx, ty = tetes[d]
    p[max(0, min(L - 1, tx)), max(0, min(H - 1, ty))] = (0, 0, 0, 255)  # tête
    p[max(0, ANCRE_X - 9), ANCRE_Y - 5] = (255, 0, 0, 255)   # main gauche
    p[min(L - 1, ANCRE_X + 9), ANCRE_Y - 5] = (0, 0, 255, 255)  # main droite
    return o


def ombre_frame():
    s = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    s.load()[ANCRE_X, ANCRE_Y] = (255, 255, 255, 255)
    return s


def generer_forme(code, variante, bases):
    base_dir = os.path.join(R, "sprite", code)
    os.makedirs(base_dir, exist_ok=True)
    infos = []
    for nom, idx, huit, fn, copie in ANIMS:
        if copie:
            infos.append((nom, idx, None, None, copie))
            continue
        frames = fn()
        lignes = LIGNES if huit else ["S"]
        feuille = Image.new("RGBA", (L * len(frames), H * len(lignes)),
                            (0, 0, 0, 0))
        offs = Image.new("RGBA", feuille.size, (0, 0, 0, 0))
        shad = Image.new("RGBA", feuille.size, (0, 0, 0, 0))
        dfr = os.path.join(base_dir, "frames", nom)
        os.makedirs(dfr, exist_ok=True)
        for li, d in enumerate(lignes):
            for fi, (dx, dy, ec, _dur) in enumerate(frames):
                sx = dx if d not in ("O", "NO", "SO") else -dx
                im = transformer(bases[d], sx, dy, ec)
                im = teinter(im, variante)
                feuille.paste(im, (fi * L, li * H))
                im.save(os.path.join(dfr, "%s-%s-%02d.png" % (nom, d, fi)))
                offs.paste(offsets_frame(d), (fi * L, li * H))
                shad.paste(ombre_frame(), (fi * L, li * H))
        feuille.save(os.path.join(base_dir, "%s-Anim.png" % nom))
        offs.save(os.path.join(base_dir, "%s-Offsets.png" % nom))
        shad.save(os.path.join(base_dir, "%s-Shadow.png" % nom))
        infos.append((nom, idx, [f[3] for f in frames], len(lignes), None))
    ecrire_animdata(base_dir, infos)
    ecrire_credits(base_dir)
    return infos


def ecrire_animdata(base_dir, infos):
    x = ['<?xml version="1.0" ?>', "<AnimData>",
         "\t<ShadowSize>1</ShadowSize>", "\t<Anims>"]
    for nom, idx, durees, _nd, copie in infos:
        x.append("\t\t<Anim>")
        x.append("\t\t\t<Name>%s</Name>" % nom)
        x.append("\t\t\t<Index>%d</Index>" % idx)
        if copie:
            x.append("\t\t\t<CopyOf>%s</CopyOf>" % copie)
            x.append("\t\t</Anim>")
            continue
        x.append("\t\t\t<FrameWidth>%d</FrameWidth>" % L)
        x.append("\t\t\t<FrameHeight>%d</FrameHeight>" % H)
        r, h, rt = CLES.get(nom, (None, None, None))
        if r is not None:
            x.append("\t\t\t<RushFrame>%d</RushFrame>" % r)
        if h is not None:
            x.append("\t\t\t<HitFrame>%d</HitFrame>" % h)
        if rt is not None:
            x.append("\t\t\t<ReturnFrame>%d</ReturnFrame>" % rt)
        x.append("\t\t\t<Durations>")
        for d in durees:
            x.append("\t\t\t\t<Duration>%d</Duration>" % d)
        x.append("\t\t\t</Durations>")
        x.append("\t\t</Anim>")
    x += ["\t</Anims>", "</AnimData>", ""]
    open(os.path.join(base_dir, "AnimData.xml"), "w").write("\n".join(x))


def ecrire_credits(base_dir):
    open(os.path.join(base_dir, "credits.txt"), "w").write(
        "Guilde Treehouse\tTerapagos — sprites générés, conformes au format "
        "PMD Sprite Collab (CC BY-NC 4.0)\n")


if __name__ == "__main__":
    bases = importer()
    for code, (titre, var) in FORMES.items():
        infos = generer_forme(code, var, bases)
        print(code, titre, len(infos), "animations")
