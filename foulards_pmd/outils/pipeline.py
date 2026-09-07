"""
pipeline.py — lecture SpriteCollab + génération des calques de foulard.
"""

import os
import json
import math
import shutil
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np
from PIL import Image

import foulard as F

RACINE_SC = os.environ.get("SPRITECOLLAB", "/home/user/sc_tmp")
DOS_SPRITE = os.path.join(RACINE_SC, "sprite")


# --------------------------------------------------------------------------

def lire_animdata(dossier):
    """Renvoie (shadow_size, [dict d'anim]) depuis AnimData.xml."""
    root = ET.parse(os.path.join(dossier, "AnimData.xml")).getroot()
    anims = []
    for a in root.find("Anims"):
        e = {"nom": a.findtext("Name"), "index": a.findtext("Index"),
             "copie_de": a.findtext("CopyOf")}
        if not e["copie_de"]:
            e["w"] = int(a.findtext("FrameWidth"))
            e["h"] = int(a.findtext("FrameHeight"))
            e["durees"] = [int(x.text) for x in a.find("Durations")]
            for k, tag in (("rush", "RushFrame"), ("hit", "HitFrame"),
                           ("retour", "ReturnFrame")):
                v = a.findtext(tag)
                if v is not None:
                    e[k] = int(v)
        anims.append(e)
    return int(root.findtext("ShadowSize") or 1), anims


def charger_planche(dossier, nom):
    ap = os.path.join(dossier, f"{nom}-Anim.png")
    op = os.path.join(dossier, f"{nom}-Offsets.png")
    if not (os.path.isfile(ap) and os.path.isfile(op)):
        return None, None
    return (np.array(Image.open(ap).convert("RGBA")),
            np.array(Image.open(op).convert("RGBA")))


def couleurs_corps(dossier, nom="Idle"):
    """Échantillonne les couleurs dominantes du sprite (hors contour noir)."""
    anim, _ = charger_planche(dossier, nom)
    if anim is None:
        return []
    m = anim[..., 3] > 128
    px = anim[m][:, :3]
    if len(px) == 0:
        return []
    lum = px.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722])
    px = px[lum > 40]                       # on retire le contour très sombre
    if len(px) == 0:
        return []
    c = Counter(map(tuple, px.tolist()))
    return [(k, v) for k, v in c.most_common(24)]


def taille_corps(anim, w, h, cols, rows):
    """Largeur médiane du sprite : sert d'échelle pour le foulard."""
    largeurs = []
    for r in range(rows):
        for c in range(cols):
            a = anim[r * h:(r + 1) * h, c * w:(c + 1) * w, 3] > 0
            if not a.any():
                continue
            xs = np.nonzero(a.any(axis=0))[0]
            largeurs.append(xs[-1] - xs[0] + 1)
    return float(np.median(largeurs)) if largeurs else float(w)


# --------------------------------------------------------------------------

def rendre_planche(anim, offsets, w, h, cols, rows, nom_anim, pal, reglage, tc):
    """Renvoie la planche de foulard (même dimensions que Anim.png)."""
    sortie = np.zeros_like(anim)
    nrj = F.energie(nom_anim)
    for r in range(rows):
        for c in range(cols):
            y0, x0 = r * h, c * w
            masque = anim[y0:y0 + h, x0:x0 + w, 3] > 0
            if not masque.any():
                continue
            mk = F.marqueurs_case(offsets, x0, y0, w, h)
            phase = (c / cols) if cols > 1 else 0.0
            case = F.dessiner_foulard(masque, mk, r if rows == 8 else 0,
                                      phase, nrj, pal, reglage, tc)
            sortie[y0:y0 + h, x0:x0 + w] = case
    return sortie


def generer_pokemon(pid, dossier_src, dossier_dst, pal, reglage,
                    nom_pal="", nom_fr="", nom_en=""):
    os.makedirs(dossier_dst, exist_ok=True)
    ombre, anims = lire_animdata(dossier_src)

    # échelle globale : mesurée sur Idle
    a_idle, _ = charger_planche(dossier_src, "Idle")
    idle = next(a for a in anims if a["nom"] == "Idle" and not a["copie_de"])
    tc = taille_corps(a_idle, idle["w"], idle["h"],
                      a_idle.shape[1] // idle["w"], a_idle.shape[0] // idle["h"])

    faites, copiees, cases = [], [], 0
    for a in anims:
        if a["copie_de"]:
            copiees.append(a["nom"])
            continue
        anim, offsets = charger_planche(dossier_src, a["nom"])
        if anim is None:
            continue
        w, h = a["w"], a["h"]
        cols, rows = anim.shape[1] // w, anim.shape[0] // h
        planche = rendre_planche(anim, offsets, w, h, cols, rows,
                                 a["nom"], pal, reglage, tc)
        Image.fromarray(planche).save(
            os.path.join(dossier_dst, f"{a['nom']}-Anim.png"), optimize=True)
        faites.append(a["nom"])
        cases += cols * rows

    ecrire_animdata(os.path.join(dossier_dst, "AnimData.xml"), ombre, anims)

    return {"id": pid, "nom_en": nom_en, "nom_fr": nom_fr,
            "palette": nom_pal, "rampe": {k: "#%02X%02X%02X" % v for k, v in pal.items()},
            "echelle_corps": round(tc, 1), "reglage": reglage,
            "animations_rendues": faites, "animations_copiees": copiees,
            "cases": cases}


def ecrire_animdata(chemin, ombre, anims):
    """Réécrit un AnimData.xml identique en structure à celui de SpriteCollab."""
    L = ['<?xml version="1.0" ?>', "<AnimData>",
         f"\t<ShadowSize>{ombre}</ShadowSize>", "\t<Anims>"]
    for a in anims:
        L.append("\t\t<Anim>")
        L.append(f"\t\t\t<Name>{a['nom']}</Name>")
        if a["index"] is not None:
            L.append(f"\t\t\t<Index>{a['index']}</Index>")
        if a["copie_de"]:
            L.append(f"\t\t\t<CopyOf>{a['copie_de']}</CopyOf>")
        else:
            L.append(f"\t\t\t<FrameWidth>{a['w']}</FrameWidth>")
            L.append(f"\t\t\t<FrameHeight>{a['h']}</FrameHeight>")
            for k, tag in (("rush", "RushFrame"), ("hit", "HitFrame"),
                           ("retour", "ReturnFrame")):
                if k in a:
                    L.append(f"\t\t\t<{tag}>{a[k]}</{tag}>")
            L.append("\t\t\t<Durations>")
            for d in a["durees"]:
                L.append(f"\t\t\t\t<Duration>{d}</Duration>")
            L.append("\t\t\t</Durations>")
        L.append("\t\t</Anim>")
    L += ["\t</Anims>", "</AnimData>", ""]
    open(chemin, "w").write("\n".join(L))


def largeur_cou(dossier, anims=None):
    """
    Estime la largeur du col à partir de l'écartement des marqueurs de mains
    sur l'animation Idle (vues de face et de dos, les plus stables).
    """
    if anims is None:
        _, anims = lire_animdata(dossier)
    a = next(x for x in anims if x["nom"] == "Idle" and not x["copie_de"])
    anim, off = charger_planche(dossier, "Idle")
    if anim is None:
        return None
    w, h = a["w"], a["h"]
    rows = anim.shape[0] // h
    ecarts = []
    for r in ([0, 4] if rows == 8 else [0]):
        mk = F.marqueurs_case(off, 0, r * h, w, h)
        if mk["main_g"] and mk["main_d"]:
            ecarts.append(abs(mk["main_g"][0] - mk["main_d"][0]))
    if not ecarts:
        return None
    a_idle, _ = charger_planche(dossier, "Idle")
    tc = taille_corps(a_idle, w, h, a_idle.shape[1] // w, rows)
    return float(min(max(0.62 * float(np.median(ecarts)), 0.32 * tc), 0.62 * tc))


def rayon_tete(dossier, anims=None):
    """
    Rayon apparent de la tête : distance entre le marqueur de tête et le haut
    de la silhouette sur la vue de dos (direction N), mesurée dans une bande
    étroite autour du marqueur pour ne pas être faussée par une crête, une
    fleur ou une flamme dorsale.
    """
    if anims is None:
        _, anims = lire_animdata(dossier)
    a = next(x for x in anims if x["nom"] == "Idle" and not x["copie_de"])
    anim, off = charger_planche(dossier, "Idle")
    if anim is None:
        return None
    w, h = a["w"], a["h"]
    rows, cols = anim.shape[0] // h, anim.shape[1] // w
    tc = taille_corps(anim, w, h, cols, rows)
    vals = []
    for r in ([4] if rows == 8 else [0]):
        for c in range(min(cols, 4)):
            mk = F.marqueurs_case(off, c * w, r * h, w, h)
            m = anim[r * h:(r + 1) * h, c * w:(c + 1) * w, 3] > 0
            if mk["tete"] is None or not m.any():
                continue
            hx = int(round(mk["tete"][0]))
            bande = m[:, max(0, hx - 1):hx + 2]
            if not bande.any():
                continue
            ys = np.nonzero(bande.any(axis=1))[0]
            vals.append(mk["tete"][1] - ys[0])
    if not vals:
        return 0.16 * tc
    return float(min(max(float(np.median(vals)), 0.10 * tc), 0.24 * tc))
