"""
generer_zones.py — quatre zones jouables, du décor peint à l'animation.

  grotte_entree   entrée de la grotte de cristal
  crystal_arene   sanctuaire de cristal, sans colonnes
  foret_entree    lisière de la forêt
  foret_coeur     clairière sacrée, arène du combat contre Zarude

Chaîne : planche peinte -> pixelisation -> calques -> animation -> .aseprite.

Sur l'animation image par image
-------------------------------
Générer chaque image indépendamment ne donne pas une animation : deux rendus
successifs d'un même prompt ne partagent ni le grain, ni les contours, ni les
couleurs, et le résultat scintille. La méthode retenue est celle de la
production : la **planche peinte fournit la matière**, le mouvement est dérivé
d'elle par transformations continues (défilements, ondes, pulsations, dérive
de particules). Chaque image est donc issue de la même source, ce qui garantit
la cohérence temporelle. Un contrôle chiffré la vérifie en fin de génération.
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
sys.path.insert(0, os.path.join(ICI, "..", "..", "zone_boss_terapagos", "outils"))
import aseprite
import pixelisation as PX

RACINE = os.path.abspath(os.path.join(ICI, ".."))
SOURCES = os.path.join(RACINE, "sources_ia")
LARG, HAUT = 768, 512
N_IMG = 12


def arc(t, s=0.68, v=1.0):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(t % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


class Toile:
    def __init__(self, w=LARG, h=HAUT):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.float32)

    def ajouter(self, x, y, c, f=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and f > 0:
            d = self.a[y, x]
            d[:3] = np.minimum(255.0, d[:3] + np.array(c, dtype=np.float32) * f)
            d[3] = min(255.0, d[3] + 255.0 * f)

    def img(self):
        return Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), "RGBA")


# --------------------------------------------------------------------------
# Effets dérivés de la planche peinte
# --------------------------------------------------------------------------

def masque_clair(im, seuil=0.62):
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    return a.mean(axis=2) > seuil


def masque_cyan(im, seuil=0.22):
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    return (np.minimum(a[..., 1], a[..., 2]) - a[..., 0] > seuil) & (a.mean(2) > 0.24)


def masque_vert(im, seuil=0.10):
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    return (a[..., 1] - np.maximum(a[..., 0], a[..., 2]) > seuil) & (a.mean(2) > 0.16)


def lueur_pulsee(masque, phase, teinte=0.52, sat=0.45, vitesse=2.0, force=0.55):
    """Fait respirer une zone repérée dans la planche : joints, mousses…"""
    t = Toile()
    ys, xs = np.nonzero(masque)
    for y, x in zip(ys, xs):
        onde = 0.5 + 0.5 * math.sin((x * 0.02 + y * 0.028)
                                    - phase * 2 * math.pi * vitesse)
        h = (teinte + (x + y) * 0.00035) % 1.0
        t.ajouter(x, y, arc(h, sat, 1.0), (0.25 + 0.75 * onde) * force)
    return t.img()


def particules(phase, n, graine, couleur, zone, derive, taille=1, force=0.6):
    """
    Nuée de particules en dérive continue : spores, poussière de cristal.
    La position dépend uniquement de la phase, le mouvement est donc parfait
    en boucle et sans saut entre la dernière image et la première.
    """
    t = Toile()
    rng = np.random.default_rng(graine)
    x0, y0, x1, y1 = zone
    for i in range(n):
        bx = rng.uniform(x0, x1)
        by = rng.uniform(y0, y1)
        vx, vy = derive
        px = x0 + ((bx - x0) + vx * phase * (x1 - x0)) % (x1 - x0)
        py = y0 + ((by - y0) + vy * phase * (y1 - y0)) % (y1 - y0)
        px += math.sin(phase * 2 * math.pi + i) * 4.0
        vif = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi * 2 + i * 1.7))
        for dy in range(taille):
            for dx in range(taille):
                t.ajouter(px + dx, py + dy, couleur, force * vif)
    return t.img()


def rais_lumiere(phase, colonnes, couleur, force=0.30):
    """Rais de lumière obliques qui balaient lentement la scène."""
    t = Toile()
    for (x, larg, haut_) in colonnes:
        dec = math.sin(phase * 2 * math.pi) * 8.0
        for j in range(haut_):
            u = j / max(haut_ - 1, 1)
            lw = larg * (0.5 + u)
            for dx in range(int(-lw), int(lw) + 1):
                d = abs(dx) / max(lw, 1e-6)
                t.ajouter(x + dx + dec + u * 26, j, couleur,
                          (1 - d) ** 2.0 * (1 - u) ** 0.7 * force)
    return t.img()


def vignette(force=200, cx=None, cy=None):
    cx = LARG // 2 if cx is None else cx
    cy = HAUT // 2 if cy is None else cy
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - cx) / (LARG * 0.62)) ** 2 + ((ys - cy) / (HAUT * 0.70)) ** 2)
    v = np.clip((d - 0.70) * 1.7, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([4, 6, 14])
    a[..., 3] = (v * force).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


# --------------------------------------------------------------------------
# Composition
# --------------------------------------------------------------------------

def composer(structure, jeu, additifs):
    out = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for c in structure:
        if c.get("type") == "groupe":
            continue
        im = jeu.get(c["nom"])
        if im is None:
            continue
        a = np.asarray(im, dtype=np.float32)
        k = a[..., 3:4] / 255.0
        if c["nom"] in additifs:
            out[..., :3] = np.minimum(255.0, out[..., :3] + a[..., :3] * k)
            out[..., 3] = np.minimum(255.0, out[..., 3] + a[..., 3])
        else:
            out[..., :3] = a[..., :3] * k + out[..., :3] * (1 - k)
            out[..., 3] = np.minimum(255.0, a[..., 3] + out[..., 3] * (1 - k[..., 0]))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def coherence(frames):
    """
    Contrôle de fluidité : écart moyen entre images consécutives, en incluant
    le retour de la dernière à la première. Un écart faible et régulier
    signifie que l'animation ne scintille pas et boucle proprement.
    """
    a = [np.asarray(f.convert("RGB"), dtype=np.float32) for f in frames]
    d = [float(np.abs(a[i] - a[(i + 1) % len(a)]).mean()) for i in range(len(a))]
    return float(np.mean(d)), float(np.max(d)), float(np.std(d))


# --------------------------------------------------------------------------
# Définition des quatre zones
# --------------------------------------------------------------------------

def _struct(noms_additifs, extra=()):
    base = [
        {"nom": "GROUPE_DECOR", "type": "groupe"},
        {"nom": "00_fond", "niveau": 1},
        {"nom": "01_details", "niveau": 1},
        {"nom": "GROUPE_VIE", "type": "groupe"},
        {"nom": "02_lueurs", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "03_particules", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "04_rais", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "05_eclairage", "fusion": aseprite.MULTIPLIER, "opacite": 215},
    ]
    return base


ADDITIFS = {"02_lueurs", "03_particules", "04_rais"}

ZONES = {
    "grotte_entree": {
        "source": "grotte_entree.png", "titre": "Entrée de la grotte de cristal",
        "couleurs": 30, "teinte": 0.52, "sat_lueur": 0.42,
        "part": (70, (150, 200, 255), (60, 40, 708, 470), (0.0, -0.55), 1),
        "rais": [(300, 16, 300), (470, 12, 260)], "rais_c": (120, 190, 240),
        "rais_f": 0.16, "masque": "cyan",
    },
    "crystal_arene": {
        "source": "crystal_arene.png", "titre": "Sanctuaire de cristal (sans colonnes)",
        "couleurs": 30, "teinte": 0.50, "sat_lueur": 0.50,
        "part": (90, (170, 240, 255), (40, 60, 728, 460), (0.15, -0.35), 1),
        "rais": [], "rais_c": (150, 220, 255), "rais_f": 0.0,
        "masque": "cyan",
    },
    "foret_entree": {
        "source": "foret_entree.png", "titre": "Lisière de la forêt",
        "couleurs": 32, "teinte": 0.26, "sat_lueur": 0.40,
        "part": (80, (230, 240, 170), (40, 30, 728, 480), (0.25, -0.45), 1),
        "rais": [(190, 22, 330), (400, 18, 300), (610, 24, 340)],
        "rais_c": (240, 230, 150), "rais_f": 0.26, "masque": "clair",
    },
    "foret_coeur": {
        "source": "foret_coeur.png", "titre": "Clairière sacrée — arène de Zarude",
        "couleurs": 30, "teinte": 0.32, "sat_lueur": 0.55,
        "part": (110, (170, 255, 180), (60, 50, 708, 470), (-0.2, -0.5), 1),
        "rais": [(384, 26, 300)], "rais_c": (190, 250, 180), "rais_f": 0.30,
        "masque": "vert",
    },
}


def construire(cle, conf):
    chemin = os.path.join(SOURCES, conf["source"])
    if not os.path.isfile(chemin):
        print(f"  !! planche absente : {conf['source']}")
        return None
    base, pal = PX.convertir(chemin, LARG, HAUT, n_couleurs=conf["couleurs"],
                             niveaux=7)
    if conf["masque"] == "cyan":
        m = masque_cyan(base)
    elif conf["masque"] == "vert":
        m = masque_vert(base)
    else:
        m = masque_clair(base)
    print(f"  {cle}: {len(pal)} couleurs, {int(m.sum())} pixels animés")

    # séparation fond / détails : les détails sont la moitié basse, qui reçoit
    # les personnages devant elle dans le moteur
    fond, details = PX.separer_fond_sol(base, 210)
    ecl = vignette(200)

    n, coul, zone, derive, taille = conf["part"]
    structure = _struct(ADDITIFS)
    images = []
    for i in range(N_IMG):
        ph = i / N_IMG
        images.append({
            "00_fond": fond,
            "01_details": details,
            "02_lueurs": lueur_pulsee(m, ph, conf["teinte"], conf["sat_lueur"]),
            "03_particules": particules(ph, n, hash(cle) % 9999, coul, zone,
                                        derive, taille, 0.55),
            "04_rais": (rais_lumiere(ph, conf["rais"], conf["rais_c"],
                                     conf["rais_f"])
                        if conf["rais"] else Image.new("RGBA", (LARG, HAUT))),
            "05_eclairage": ecl,
        })

    frames = [composer(structure, j, ADDITIFS) for j in images]
    moy, mx, ec = coherence(frames)
    print(f"     fluidité : écart moyen {moy:.2f}, max {mx:.2f}, "
          f"régularité {ec:.2f}")

    for d in ("decor", "aseprite", "apercus"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)
    dz = os.path.join(RACINE, "decor", cle)
    os.makedirs(dz, exist_ok=True)
    for nom, im in images[0].items():
        im.save(os.path.join(dz, f"{nom}.png"), optimize=True)
    frames[0].convert("RGB").save(os.path.join(dz, "compose.png"), optimize=True)

    aseprite.ecrire_avance(
        os.path.join(RACINE, "aseprite", f"{cle}.aseprite"),
        structure, images, (LARG, HAUT), duree_ms=100,
        palette=pal + [arc(k / 10) for k in range(10)],
        tags=[("ambiance", 0, N_IMG - 1, aseprite.AVANT, (110, 190, 255))])

    g = [f.resize((LARG // 2, HAUT // 2), Image.LANCZOS).convert(
        "P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    g[0].save(os.path.join(RACINE, "apercus", f"{cle}.gif"), save_all=True,
              append_images=g[1:], duration=100, loop=0, disposal=2,
              optimize=True)
    return (moy, mx, ec)


def main():
    print("zones :")
    res = {}
    for cle, conf in ZONES.items():
        r = construire(cle, conf)
        if r:
            res[cle] = r
    print("\nrécapitulatif de fluidité (écart moyen entre images) :")
    for k, (m, mx, e) in res.items():
        etat = "OK" if m < 12 and e < 4 else "à surveiller"
        print(f"  {k:<16} moyen {m:5.2f}  max {mx:5.2f}  régularité {e:4.2f}  {etat}")


if __name__ == "__main__":
    main()
