from __future__ import annotations

"""Construit la zone `Cliff` en layers modulaires, methode Halcyon.

Deux principes, qui viennent des deux corrections successives du brief :

1. **Le layout est celui de la reference.** `IMG_4889.png` / `IMG_4890.png`
   sont la planche ripee du *Pelipper Post Office* : un plateau herbeux a
   gauche, une falaise qui tombe a pic, l'ocean a droite, l'horizon haut. On
   reprend cette composition telle quelle.

2. **Le ciel et l'ocean ne sont PAS generes.** Ils sont decoupes directement
   dans la planche officielle (`cliff/ref/ref_sky.png`,
   `cliff/ref/ref_ocean_*.png`), en pixels natifs 1x, sans passer par le
   pipeline de reduction. Seule la falaise est une generation, restylee sur
   le tileset de Metano Town (= Treasure Town).

Empilement, calque sur la structure relevee dans `metano_town.rsground` :

    Sky              0   degrade de ciel, decoupe dans la planche officielle
    Stars            0   etoiles                                (nuit)
    Moon             0   lune / soleil
    Clouds           0   nuages, extraits du ciel officiel
    Base             0   l'ocean, tuiles officielles             (Metano_Town_Base)
    Cliffs           0   la paroi rocheuse                       (Metano_Town_Cliffs)
    River            0   ressac au pied de la roche              (River_Animation)
    River_Sparkles   0   scintillements                          (River_Sparkles)
    Objects_Under    0   liseré sombre sous l'herbe              (Objects Under)
    Objects          0   le plateau herbeux                      (Objects)
    Objects_Over     0   affleurements de roche sur l'herbe      (Objects Over)
    Fringe           4   crete du plateau, DEVANT le joueur      (Metano_Town_Fringe)

Usage :
    python3 construire_cliff_layers.py
"""

from collections import Counter
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_sprite_pmdo import (  # noqa: E402
    cadrage_entier,
    nettoyer_orphelins,
    palette_depuis,
    projeter_palette,
)

RACINE = Path(__file__).resolve().parent.parent
REF = RACINE / "cliff" / "ref"
SORTIE = RACINE / "cliff" / "layers"

TILE = 8
# Le cadre est cale sur la planche officielle : son ciel fait exactement
# 720 x 208 px, donc on le pose au pixel pres sans jamais le redimensionner.
CADRE_W, CADRE_H = 720, 480
HORIZON = 208

PROFONDEUR = {
    "Sky": 0,
    "Stars": 0,
    "Moon": 0,
    "Clouds": 0,
    "Base": 0,
    "Cliffs": 0,
    "River": 0,
    "River_Sparkles": 0,
    "Objects_Under": 0,
    "Objects": 0,
    "Objects_Over": 0,
    "Fringe": 4,
}

ORDRE = ["Sky", "Stars", "Moon", "Clouds", "Base", "Cliffs", "River",
         "River_Sparkles", "Objects_Under", "Objects", "Objects_Over", "Fringe"]

# --- sources officielles, en pixels natifs -------------------------------
REF_SKY = REF / "ref_sky.png"
REF_OCEAN_DEEP = sorted(REF.glob("ref_ocean_deep_*.png"))
REF_OCEAN_SHALLOW = sorted(REF.glob("ref_ocean_shallow_*.png"))
REF_SCENE = REF / "ref_scene_land.png"

# --- generations restylees ------------------------------------------------
GEN_CLIFF = REF / "gen_cliff_metano.png"
GEN_SKYOBJ = REF / "gen_sky_objects.png"

# Tilesets Metano extraits de `Palikadude/Halcyon`, palette de reference.
REFS_METANO = [
    RACINE / "cliff" / "reference_metano_cliffs.png",
    RACINE / "cliff" / "reference_metano_fringe.png",
]

# L'herbe de Treasure Town n'est pas verte : elle est jaune-olive.
HERBE_METANO = np.array([
    (184, 208, 64),
    (200, 216, 80),
    (215, 224, 104),
    (184, 192, 80),
], dtype=int)


# --------------------------------------------------------------------------
# outils
# --------------------------------------------------------------------------

def charger(chemin: Path) -> np.ndarray:
    """Charge une source officielle SANS y toucher : pixels natifs."""
    return np.array(Image.open(chemin).convert("RGBA"))


def detourer_magenta(chemin: Path) -> Image.Image:
    """Retire le fond magenta d'une generation, contour franc."""
    a = np.array(Image.open(chemin).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 110) & (b > 110) & (g < 120) & ((r - g) > 45) & ((b - g) > 45)
    al = ((~mag) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), al]), "RGBA")


def palette_metano() -> np.ndarray:
    return palette_depuis(REFS_METANO)


def virer_herbe_metano(a: np.ndarray) -> np.ndarray:
    """Bascule les verts de la generation vers l'olive de Treasure Town."""
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    vert = m & (g > r - 30) & (g > b + 24)
    if not vert.any():
        return out
    lum = rgb[vert].sum(1)
    lo, hi = lum.min(), max(lum.max(), lum.min() + 1)
    rang = ((lum - lo) / (hi - lo) * (len(HERBE_METANO) - 1)).round().astype(int)
    out[vert, :3] = HERBE_METANO[rang]
    return out


def poser(cadre: np.ndarray, obj: np.ndarray, x: int, y: int) -> None:
    h, w = obj.shape[:2]
    H, W = cadre.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sous = obj[y0 - y:y1 - y, x0 - x:x1 - x]
    m = sous[..., 3] > 0
    cadre[y0:y1, x0:x1][m] = sous[m]


def composantes(a: np.ndarray, seuil: int = 60) -> list[np.ndarray]:
    """Isole chaque element d'une planche par composante connexe (BFS pile)."""
    m = a[..., 3] > 0
    H, W = m.shape
    seen = np.zeros_like(m)
    out = []
    for y in range(H):
        for x in range(W):
            if not m[y, x] or seen[y, x]:
                continue
            pile = [(y, x)]
            seen[y, x] = True
            pts = []
            while pile:
                cy, cx = pile.pop()
                pts.append((cy, cx))
                for dy in (-2, -1, 0, 1, 2):
                    for dx in (-2, -1, 0, 1, 2):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            pile.append((ny, nx))
            if len(pts) > seuil:
                ys = [p[0] for p in pts]
                xs = [p[1] for p in pts]
                out.append(a[min(ys):max(ys) + 1, min(xs):max(xs) + 1].copy())
    out.sort(key=lambda o: -(o[..., 3] > 0).sum())
    return out


def teinte_nuit(a: np.ndarray, force: float = 0.55,
                cible=(70, 88, 150)) -> np.ndarray:
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[m][:, :3].astype(float)
    for i in range(3):
        rgb[:, i] = rgb[:, i] * (1 - force) + cible[i] * force * (rgb[:, i] / 255.0)
    out[m, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return out


# --------------------------------------------------------------------------
# ciel officiel : on le separe en degrade + nuages
# --------------------------------------------------------------------------

def separer_ciel() -> tuple[np.ndarray, np.ndarray]:
    """Decoupe `ref_sky.png` en (degrade sans nuages, nuages seuls).

    Les nuages sont les pixels desatures et clairs ; le ciel est franchement
    bleu. Une fois les nuages retires, chaque ligne du degrade est remplie par
    sa couleur dominante : on obtient un ciel propre, reutilisable de nuit.
    """
    src = charger(REF_SKY)
    rgb = src[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    nuage = (b - r) < 90                       # le ciel a un bleu tres dominant

    degrade = np.zeros_like(src)
    for y in range(src.shape[0]):
        ligne = rgb[y][~nuage[y]]
        if len(ligne) == 0:
            ligne = rgb[y]
        couleurs, comptes = np.unique(ligne, axis=0, return_counts=True)
        degrade[y, :, :3] = couleurs[comptes.argmax()]
    degrade[..., 3] = 255

    nuages = np.zeros_like(src)
    nuages[nuage] = src[nuage]
    nuages[..., 3] = np.where(nuage, 255, 0)
    return degrade, nuages


def ciel_nuit(degrade_jour: np.ndarray) -> np.ndarray:
    """Rejoue le degrade officiel en gamme nocturne.

    On garde la STRUCTURE du ciel ripe — meme nombre de bandes, memes hauteurs
    de transition — et on ne remappe que la teinte, vers le bleu nuit de la
    reference `IMG_4889.png`.
    """
    out = degrade_jour.copy()
    rgb = out[..., :3].astype(float)
    lum = rgb.sum(2) / 765.0                        # 0 = sombre, 1 = clair
    haut = np.array([14, 22, 92], float)            # zenith
    bas = np.array([40, 78, 168], float)            # juste au-dessus de la mer
    t = (lum - lum.min()) / max(float(lum.max() - lum.min()), 1e-6)
    for i in range(3):
        out[..., i] = np.clip(haut[i] + (bas[i] - haut[i]) * t, 0, 255)
    out[..., 3] = 255
    return out


# --------------------------------------------------------------------------
# ocean officiel
# --------------------------------------------------------------------------

def construire_ocean() -> np.ndarray:
    """Pave l'ocean avec les tuiles officielles, sans redimensionnement.

    La planche fournit deux jeux : `deep` (14 couleurs, sombre en haut et clair
    en bas, c'est la bande d'horizon) et `shallow` (4 couleurs, le large calme
    du premier plan). On les empile dans cet ordre, ce qui reproduit exactement
    la degression de la reference.
    """
    hauteur = CADRE_H - HORIZON
    out = np.zeros((hauteur, CADRE_W, 4), np.uint8)

    deep = [charger(p) for p in REF_OCEAN_DEEP]
    shallow = [charger(p) for p in REF_OCEAN_SHALLOW]
    if not deep or not shallow:
        raise SystemExit("tuiles d'ocean officielles absentes de cliff/ref/")

    hd = deep[0].shape[0]
    for i, x in enumerate(range(0, CADRE_W, deep[0].shape[1])):
        poser(out, deep[i % len(deep)], x, 0)
    y = hd
    k = 0
    while y < hauteur:
        for i, x in enumerate(range(0, CADRE_W, shallow[0].shape[1])):
            poser(out, shallow[(i + k) % len(shallow)], x, y)
        y += shallow[0].shape[0]
        k += 1
    return out


# --------------------------------------------------------------------------
# controle
# --------------------------------------------------------------------------

def controler(a: np.ndarray) -> dict:
    al = a[..., 3]
    m = al > 0
    h, w = al.shape
    tuiles = []
    for ty in range(0, h, TILE):
        for tx in range(0, w, TILE):
            t = a[ty:ty + TILE, tx:tx + TILE].reshape(-1, 4)
            c = {tuple(int(v) for v in p[:3]) for p in t if p[3] > 0}
            if c:
                tuiles.append(len(c))
    tuiles = np.array(tuiles) if tuiles else np.array([0])
    return {
        "cellules_occupees": int(len(tuiles)),
        "couleurs": int(len(np.unique(a[m][:, :3], axis=0))) if m.any() else 0,
        "moy_par_tuile": round(float(tuiles.mean()), 1),
        "pct_tuiles_conformes": round(float((tuiles <= 16).mean() * 100), 1),
        "semi_transparents": int(((al > 0) & (al < 255)).sum()),
        "occupation_pct": round(float(m.mean() * 100), 2),
    }


# --------------------------------------------------------------------------

def construire() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    pal = palette_metano()

    # --- le ciel et la mer : sources officielles, pixels natifs -----------
    degrade_j, nuages_src = separer_ciel()
    degrade_n = ciel_nuit(degrade_j)
    ocean = construire_ocean()

    # --- la falaise : seule piece generee, restylee Metano -----------------
    cliff_img = detourer_magenta(GEN_CLIFF)
    cliff_px = nettoyer_orphelins(
        projeter_palette(virer_herbe_metano(cadrage_entier(cliff_img, 560)), pal))

    # --- astres, extraits de la planche de generation ---------------------
    objets = nettoyer_orphelins(cadrage_entier(detourer_magenta(GEN_SKYOBJ), 440))
    pieces = composantes(objets)

    def teinte(p):
        m = p[..., 3] > 0
        return p[m][:, :3].astype(int).mean(0)

    def rond(p):
        h, w = p.shape[:2]
        return 0.7 < w / max(h, 1) < 1.45

    soleil, lunes, etoiles = None, [], []
    for p in pieces:
        r, g, b = teinte(p)
        n = int((p[..., 3] > 0).sum())
        if n < 240:
            etoiles.append(p)
        elif rond(p) and r - b > 55:
            soleil = soleil or p
        elif rond(p) and r > 180 and g > 180:
            lunes.append(p)
    lunes.sort(key=lambda p: -(p[..., 3] > 0).sum())

    # --- placement de la falaise ------------------------------------------
    # Comme dans la reference : le plateau occupe la gauche, la paroi tombe a
    # pic et la mer occupe la droite du cadre.
    CX, CY = -8, CADRE_H - cliff_px.shape[0] + 8

    manifeste = {"zone": "Cliff", "tile_px": TILE, "cadre": [CADRE_W, CADRE_H],
                 "horizon_y": HORIZON,
                 "sources_officielles": [p.name for p in
                                         [REF_SKY, *REF_OCEAN_DEEP, *REF_OCEAN_SHALLOW]],
                 "moments": {}}

    for moment in ("jour", "nuit"):
        nuit = moment == "nuit"
        couches: dict[str, np.ndarray] = {}
        vide = lambda: np.zeros((CADRE_H, CADRE_W, 4), np.uint8)  # noqa: E731

        # --- Sky --------------------------------------------------------
        c = vide()
        deg = degrade_n if nuit else degrade_j
        poser(c, deg, 0, 0)
        c[HORIZON:] = c[HORIZON - 1]           # prolonge la derniere bande
        c[..., 3] = 255
        couches["Sky"] = c

        # --- Stars ------------------------------------------------------
        # Dessinees a la main plutot qu'extraites : reduire une etoile ripee
        # donne un paté de 3 x 3, alors qu'une etoile PMD est un point ou une
        # croix de 3 px. On les pose donc directement en pixels.
        if nuit:
            c = vide()
            rng = np.random.default_rng(7)
            for _ in range(150):
                x = int(rng.integers(3, CADRE_W - 3))
                y = int(rng.integers(3, HORIZON - 24))
                ton = (255, 255, 255) if rng.random() < 0.6 else (200, 216, 248)
                c[y, x, :3] = ton
                c[y, x, 3] = 255
                if rng.random() < 0.3:                  # les plus brillantes
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        c[y + dy, x + dx, :3] = ton
                        c[y + dy, x + dx, 3] = 255
            couches["Stars"] = c

        # --- Moon -------------------------------------------------------
        astre = (lunes[0] if lunes else None) if nuit else soleil
        if astre is not None:
            # L'astre sort d'une generation : on le ramene a une poignee de
            # tons, sinon il pese a lui seul plus de couleurs que toute la
            # falaise. Et on le pose a GAUCHE, dans la portion de ciel que les
            # nuages officiels laissent degagee.
            a = astre.copy()
            m = a[..., 3] > 0
            q = Image.fromarray(a[..., :3]).quantize(colors=6, method=Image.MEDIANCUT)
            a[..., :3] = np.array(q.convert("RGB"))
            a[..., 3] = np.where(m, 255, 0)
            c = vide()
            poser(c, a, 56, 20)
            couches["Moon"] = c

        # --- Clouds : les nuages du ciel officiel, en calque separe ------
        c = vide()
        n = teinte_nuit(nuages_src, 0.62, (86, 96, 168)) if nuit else nuages_src
        poser(c, n, 0, 0)
        couches["Clouds"] = c

        # --- Base : l'ocean officiel ------------------------------------
        c = vide()
        o = teinte_nuit(ocean, 0.66, (34, 54, 132)) if nuit else ocean
        poser(c, o, 0, HORIZON)
        couches["Base"] = c

        # --- la falaise, decomposee comme chez Metano --------------------
        terre = cliff_px if not nuit else teinte_nuit(cliff_px, 0.5)
        plein = vide()
        poser(plein, terre, CX, CY)
        masque = plein[..., 3] > 0
        br = plein[..., :3].astype(int)
        herbe = masque & (br[..., 1] > br[..., 2] + 55) & (br[..., 1] > 110)
        roche = masque & ~herbe

        def extraire(sel):
            c = vide()
            c[sel] = plein[sel]
            c[..., 3] = np.where(sel, 255, 0)
            return c

        couches["Cliffs"] = extraire(roche)

        # --- River : le ressac au pied de la paroi ------------------------
        c = vide()
        eau = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(masque[:, x])[0]
            if len(col) == 0 or col.max() >= CADRE_H - 2:
                continue
            bas = col.max()
            eau[bas + 1:min(CADRE_H, bas + 7), x] = True
        # le ressac longe aussi le flanc droit de la falaise
        for y in range(HORIZON, CADRE_H):
            ligne = np.nonzero(masque[y])[0]
            if len(ligne):
                d = ligne.max()
                eau[y, d + 1:min(CADRE_W, d + 6)] = True
        eau &= couches["Base"][..., 3] > 0
        if eau.sum() > 40:
            c[eau] = couches["Base"][eau]
            c[eau, :3] = np.clip(c[eau, :3].astype(int) + 52, 0, 255).astype(np.uint8)
            c[..., 3] = np.where(eau, 255, 0)
            couches["River"] = nettoyer_orphelins(c)

        # --- River_Sparkles ----------------------------------------------
        c = vide()
        rng = np.random.default_rng(11)
        libre = (couches["Base"][..., 3] > 0) & ~masque
        pts = np.argwhere(libre)
        if len(pts):
            blanc = (156, 234, 246) if nuit else (246, 250, 255)
            for k in rng.choice(len(pts), size=min(110, len(pts)), replace=False):
                y, x = pts[k]
                if x + 2 < CADRE_W:
                    c[y, x:x + 2, :3] = blanc
                    c[y, x:x + 2, 3] = 255
            couches["River_Sparkles"] = c

        # --- Objects_Under : le liseré sombre sous l'herbe ----------------
        sous = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            bas = col.max()
            sous[bas:min(CADRE_H, bas + 4), x] = masque[bas:min(CADRE_H, bas + 4), x]
        if sous.sum() > 40:
            couches["Objects_Under"] = extraire(sous)

        # --- Objects : le plateau herbeux ---------------------------------
        couches["Objects"] = extraire(herbe & ~sous)

        # --- Objects_Over : les affleurements de roche sur le plateau -----
        haut = np.nonzero(masque.any(1))[0].min()
        aff = roche & (np.arange(CADRE_H)[:, None] < haut + 40)
        if aff.sum() > 40:
            couches["Objects_Over"] = extraire(aff)

        # --- Fringe : la crete, DEVANT le joueur --------------------------
        crete = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            bas = col.max()
            crete[max(0, bas - 5):bas + 1, x] = herbe[max(0, bas - 5):bas + 1, x]
        if crete.sum() > 40:
            couches["Fringe"] = extraire(crete)

        # --- sortie -------------------------------------------------------
        infos = {}
        for nom in ORDRE:
            img = couches.get(nom)
            if img is None or (img[..., 3] > 0).sum() == 0:
                continue
            fichier = f"Cliff_{nom}_{moment}.png"
            Image.fromarray(img, "RGBA").save(SORTIE / fichier)
            infos[nom] = {"fichier": fichier, "Layer": PROFONDEUR[nom], **controler(img)}
        manifeste["moments"][moment] = infos

        comp = Image.new("RGBA", (CADRE_W, CADRE_H), (0, 0, 0, 0))
        for nom in ORDRE:
            if nom in couches:
                comp.alpha_composite(Image.fromarray(couches[nom], "RGBA"))
        comp.save(RACINE / "cliff" / f"cliff_{moment}.png")

    (SORTIE / "Cliff_layers.json").write_text(json.dumps(manifeste, indent=2))

    print("=== Cliff ===")
    for moment, infos in manifeste["moments"].items():
        print(f"\n  [{moment}]")
        print(f"    {'layer':<16}{'Layer':>6}{'cellules':>10}{'coul':>7}"
              f"{'moy/tui':>9}{'<=16':>8}{'semi':>6}{'occup':>9}")
        for nom, d in infos.items():
            print(f"    {nom:<16}{d['Layer']:>6}{d['cellules_occupees']:>10}"
                  f"{d['couleurs']:>7}{d['moy_par_tuile']:>9}"
                  f"{d['pct_tuiles_conformes']:>7}%{d['semi_transparents']:>6}"
                  f"{d['occupation_pct']:>8}%")


if __name__ == "__main__":
    construire()
