"""Planche de contrôle : sprite + foulard, 8 directions, pour calibrage visuel."""
import sys, os, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P, foulard as F

def planche(pid, anim_nom="Idle", S=9, reglage=None, cols_max=3):
    d = f"{P.DOS_SPRITE}/{pid}"
    _, anims = P.lire_animdata(d)
    a = next(x for x in anims if x["nom"] == anim_nom and not x["copie_de"])
    anim, off = P.charger_planche(d, anim_nom)
    w, h = a["w"], a["h"]; cols = anim.shape[1]//w; rows = anim.shape[0]//h
    a_idle, _ = P.charger_planche(d, "Idle")
    idl = next(x for x in anims if x["nom"]=="Idle" and not x["copie_de"])
    tc = P.taille_corps(a_idle, idl["w"], idl["h"], a_idle.shape[1]//idl["w"], a_idle.shape[0]//idl["h"])
    nom, pal = P.choisir if False else (None, None)
    cc = P.couleurs_corps(d)
    nom, pal = F.choisir_palette(cc)
    reglage = reglage or {}
    fo = P.rendre_planche(anim, off, w, h, cols, rows, anim_nom, pal, reglage, tc)
    nc = min(cols, cols_max)
    out = Image.new("RGBA", (w*S*nc, h*S*rows), (38,38,48,255))
    for r in range(rows):
        for c in range(nc):
            base = Image.fromarray(anim[r*h:(r+1)*h, c*w:(c+1)*w])
            sc   = Image.fromarray(fo[r*h:(r+1)*h, c*w:(c+1)*w])
            comp = Image.alpha_composite(base, sc).resize((w*S,h*S), Image.NEAREST)
            out.paste(comp, (c*w*S, r*h*S), comp)
    return out, nom

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv)>1 else "0004"
    an  = sys.argv[2] if len(sys.argv)>2 else "Idle"
    img, nom = planche(pid, an)
    p = f"/home/user/pilote_{pid}_{an}.png"; img.save(p); print(p, nom)
