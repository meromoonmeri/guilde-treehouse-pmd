from __future__ import annotations

"""Construit la zone `Cliff` en layers modulaires, methode Halcyon.

Regles qui fixent le resultat, dans l'ordre ou elles ont ete posees :

1. **Layout de la reference.** Plateau herbeux a gauche, paroi qui tombe a
   pic, ocean a droite, horizon haut.
2. **La falaise touche les bords.** Elle mord le bord gauche et court sur tout
   le bord bas : aucun liseré de ciel ne doit apparaitre derriere elle.
3. **Texture et couleurs de `IMG_4892.png`.** Cette capture est un upscale x3
   exact : on en recupere les pixels natifs (504 x 384) et on en tire la
   palette de reference. Roche = gres finement moucheté en strates
   horizontales, veines mauves ; herbe = olive clair moucheté de touffes.
4. **Le ciel est un overlay**, et les **nuages defilent sur leur propre
   layer**, en **wrap loop parfait** : la bande de nuages fait exactement la
   largeur du cadre et tout nuage qui deborde a droite est redessine a gauche,
   donc la derniere frame se raccorde a la premiere au pixel pres.

Empilement, calque sur `metano_town.rsground` :

    Sky              0   degrade, plein cadre
    Stars            0   etoiles                                (nuit)
    Moon             0   lune / soleil
    Clouds           0   nuages, N frames en boucle             (overlay)
    Base             0   l'ocean                                 (Metano_Town_Base)
    Cliffs           0   la paroi rocheuse                       (Metano_Town_Cliffs)
    River            0   ressac au pied de la roche              (River_Animation)
    River_Sparkles   0   scintillements                          (River_Sparkles)
    Objects_Under    0   liseré de sable sous l'herbe            (Objects Under)
    Objects          0   le plateau herbeux                      (Objects)
    Objects_Over     0   affleurements de roche                  (Objects Over)
    Fringe           4   crete du plateau, DEVANT le joueur      (Metano_Town_Fringe)

Usage :
    python3 construire_cliff_layers.py
"""

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
REF = RACINE / "cliff" / "ref2"
SORTIE = RACINE / "cliff" / "layers"

TILE = 8
CADRE_W, CADRE_H = 720, 480
HORIZON = 144                      # 117/384 de la reference, arrondi a 8 px
N_FRAMES_NUAGES = 8                # la boucle de defilement

# --- sources ---------------------------------------------------------------
REF_SCENE = REF / "ref_metano_scene.png"     # IMG_4892 en pixels natifs
REF_ROCHE = REF / "ref_rock_texture.png"
REF_HERBE = REF / "ref_grass_texture.png"
REF_BORD = REF / "ref_cliff_edge.png"
GEN_CLIFF = REF / "gen_cliff.png"
GEN_SEA = REF / "gen_sea.png"
GEN_CLOUDS = REF / "gen_clouds.png"

PROFONDEUR = {
    "Sky": 0, "Stars": 0, "Moon": 0, "Clouds": 0, "Base": 0, "Cliffs": 0,
    "River": 0, "River_Sparkles": 0, "Objects_Under": 0, "Objects": 0,
    "Objects_Over": 0, "Fringe": 4,
}
ORDRE = ["Sky", "Stars", "Moon", "Clouds", "Base", "Cliffs", "River",
         "River_Sparkles", "Objects_Under", "Objects", "Objects_Over", "Fringe"]

# Bandes de ciel relevees une par une sur la reference, du zenith a l'horizon.
CIEL_JOUR = [
    (0.00, (111, 167, 255)), (0.36, (119, 175, 255)), (0.46, (127, 183, 255)),
    (0.51, (135, 191, 255)), (0.56, (135, 199, 255)), (0.61, (143, 207, 255)),
    (0.71, (151, 215, 255)), (0.77, (151, 223, 255)), (0.82, (159, 231, 255)),
    (0.90, (167, 231, 255)), (0.96, (223, 247, 255)),
]
CIEL_NUIT = [
    (0.00, (11, 19, 71)), (0.36, (15, 27, 87)), (0.46, (19, 35, 103)),
    (0.51, (23, 43, 115)), (0.56, (27, 51, 127)), (0.61, (31, 59, 139)),
    (0.71, (39, 71, 151)), (0.77, (47, 83, 159)), (0.82, (55, 95, 167)),
    (0.90, (67, 111, 175)), (0.96, (87, 135, 183)),
]

# L'herbe de Treasure Town n'est pas verte : elle est olive.
HERBE_METANO = np.array([
    (135, 159, 47), (167, 191, 47), (191, 207, 71),
    (215, 223, 87), (231, 239, 103),
], dtype=int)


# --------------------------------------------------------------------------
# outils
# --------------------------------------------------------------------------

def detourer_magenta(chemin: Path) -> Image.Image:
    a = np.array(Image.open(chemin).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 110) & (b > 110) & (g < 120) & ((r - g) > 45) & ((b - g) > 45)
    return Image.fromarray(
        np.dstack([a.astype(np.uint8), ((~mag) * 255).astype(np.uint8)]), "RGBA")


def palette_metano() -> np.ndarray:
    """Palette authentique, tiree des pixels natifs de `IMG_4892.png`."""
    return palette_depuis([REF_SCENE, REF_ROCHE, REF_HERBE, REF_BORD], maxi=200)


def virer_herbe_metano(a: np.ndarray) -> np.ndarray:
    """Bascule les verts de la generation vers l'olive de Treasure Town."""
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    vert = m & (g > r - 40) & (g > b + 24)
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


def composantes(a: np.ndarray, seuil: int = 200) -> list[np.ndarray]:
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
# ciel : overlay plein cadre
# --------------------------------------------------------------------------

def construire_ciel(bandes) -> np.ndarray:
    """Reconstruit le degrade en bandes franches, comme la reference.

    Pas d'interpolation : la reference empile des aplats horizontaux nets. On
    reproduit ce comportement, sinon le degrade lisse ferait exploser le
    nombre de couleurs par tuile.
    """
    out = np.zeros((CADRE_H, CADRE_W, 4), np.uint8)
    seuils = [int(round(t * HORIZON)) for t, _ in bandes]
    for i, (_, couleur) in enumerate(bandes):
        y0 = seuils[i]
        y1 = seuils[i + 1] if i + 1 < len(seuils) else HORIZON
        out[y0:y1, :, :3] = couleur
    out[HORIZON:, :, :3] = bandes[-1][1]
    out[..., 3] = 255
    return out


# --------------------------------------------------------------------------
# nuages : bande de largeur exacte, defilement en boucle parfaite
# --------------------------------------------------------------------------

def bande_nuages(pieces: list[np.ndarray]) -> np.ndarray:
    """Compose une bande de nuages de LARGEUR EXACTEMENT `CADRE_W`.

    Le wrap est garanti par construction : tout nuage qui deborde du bord
    droit est redessine a `x - CADRE_W`. La bande se raccorde donc a
    elle-meme, et un simple `np.roll` horizontal produit un defilement
    infini sans couture.
    """
    bande = np.zeros((HORIZON, CADRE_W, 4), np.uint8)
    if not pieces:
        return bande
    # Peu de nuages, bien espaces : la reference laisse le ciel largement
    # degage. En entasser davantage forme un banc continu qui masque
    # l'horizon.
    plan = [(40, 16), (300, 44), (540, 12)]
    for i, (x, y) in enumerate(plan):
        n = pieces[i % len(pieces)]
        if n.shape[0] > HORIZON - y:
            n = n[:max(1, HORIZON - y)]
        poser(bande, n, x, y)
        if x + n.shape[1] > CADRE_W:                  # la moitie qui deborde
            poser(bande, n, x - CADRE_W, y)
    return bande


# --------------------------------------------------------------------------
# ocean
# --------------------------------------------------------------------------

def construire_ocean(pal: np.ndarray) -> np.ndarray:
    """Pave l'ocean genere, en respectant la degression de la reference."""
    hauteur = CADRE_H - HORIZON
    src = nettoyer_orphelins(projeter_palette(
        cadrage_entier(Image.open(GEN_SEA).convert("RGBA"), CADRE_W), pal))
    out = np.zeros((hauteur, CADRE_W, 4), np.uint8)
    y = 0
    while y < hauteur:
        bout = src[:min(src.shape[0], hauteur - y)]
        out[y:y + bout.shape[0]] = bout
        y += bout.shape[0]
    out[..., 3] = 255
    return out


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


def construire() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    pal = palette_metano()

    ocean = construire_ocean(pal)

    # --- la falaise : collee au bord GAUCHE et au bord BAS ----------------
    # Elle mord ces deux bords, donc aucun liseré de ciel ne peut apparaitre
    # derriere. En revanche elle ne couvre PAS toute la largeur : la mer doit
    # rester visible a droite et la ligne d'horizon doit se lire, comme sur la
    # reference.
    LARGEUR_TERRE = 496
    cliff_px = nettoyer_orphelins(projeter_palette(
        virer_herbe_metano(cadrage_entier(detourer_magenta(GEN_CLIFF),
                                          LARGEUR_TERRE)), pal))
    # on rogne le haut pour que le plateau demarre sous l'horizon
    HAUT_TERRE = 296
    if cliff_px.shape[0] > HAUT_TERRE:
        cliff_px = cliff_px[cliff_px.shape[0] - HAUT_TERRE:]

    # --- nuages ------------------------------------------------------------
    nuages_src = nettoyer_orphelins(
        cadrage_entier(detourer_magenta(GEN_CLOUDS), 560))
    pieces = composantes(nuages_src)

    manifeste = {"zone": "Cliff", "tile_px": TILE, "cadre": [CADRE_W, CADRE_H],
                 "horizon_y": HORIZON,
                 "nuages": {"frames": N_FRAMES_NUAGES, "wrap": "horizontal",
                            "pas_px": CADRE_W // N_FRAMES_NUAGES},
                 "moments": {}}

    for moment in ("jour", "nuit"):
        nuit = moment == "nuit"
        couches: dict[str, np.ndarray] = {}
        vide = lambda: np.zeros((CADRE_H, CADRE_W, 4), np.uint8)  # noqa: E731

        # --- Sky ----------------------------------------------------------
        couches["Sky"] = construire_ciel(CIEL_NUIT if nuit else CIEL_JOUR)

        # --- Stars ---------------------------------------------------------
        if nuit:
            c = vide()
            rng = np.random.default_rng(7)
            for _ in range(150):
                x = int(rng.integers(3, CADRE_W - 3))
                y = int(rng.integers(3, HORIZON - 16))
                ton = (255, 255, 255) if rng.random() < 0.6 else (200, 216, 248)
                c[y, x, :3] = ton
                c[y, x, 3] = 255
                if rng.random() < 0.28:
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        c[y + dy, x + dx, :3] = ton
                        c[y + dy, x + dx, 3] = 255
            couches["Stars"] = c

        # --- Moon -----------------------------------------------------------
        c = vide()
        rayon = 22 if nuit else 18
        cy, cx = 46, 96
        ton = (247, 247, 215) if nuit else (255, 231, 111)
        halo = (215, 223, 175) if nuit else (255, 207, 71)
        yy, xx = np.ogrid[:CADRE_H, :CADRE_W]
        d2 = (yy - cy) ** 2 + (xx - cx) ** 2
        c[d2 <= rayon ** 2, :3] = ton
        c[(d2 <= rayon ** 2) & (d2 > (rayon - 3) ** 2), :3] = halo
        c[..., 3] = np.where(d2 <= rayon ** 2, 255, 0)
        couches["Moon"] = c

        # --- Base : l'ocean ---------------------------------------------------
        c = vide()
        poser(c, teinte_nuit(ocean, 0.66, (34, 54, 132)) if nuit else ocean,
              0, HORIZON)
        couches["Base"] = c

        # --- la falaise, decomposee comme chez Metano ------------------------
        terre = teinte_nuit(cliff_px, 0.5) if nuit else cliff_px
        plein = vide()
        poser(plein, terre, 0, CADRE_H - terre.shape[0])
        masque = plein[..., 3] > 0
        br = plein[..., :3].astype(int)
        # Distinguer herbe et roche par « vert > bleu » ne suffit pas : la
        # roche ocre de Metano (167,119,71) a elle aussi G nettement au-dessus
        # de B. Ce qui les separe, c'est que la roche est CHAUDE — son rouge
        # domine largement son vert — alors que l'herbe olive a R et G proches.
        herbe = (masque & (br[..., 1] >= br[..., 0] - 20)
                 & (br[..., 1] > br[..., 2] + 40))
        roche = masque & ~herbe

        def extraire(sel):
            c = vide()
            c[sel] = plein[sel]
            c[..., 3] = np.where(sel, 255, 0)
            return c

        couches["Cliffs"] = extraire(roche)

        # --- River : le ressac au pied et au flanc de la paroi ---------------
        c = vide()
        eau = np.zeros((CADRE_H, CADRE_W), bool)
        for y in range(HORIZON, CADRE_H):
            ligne = np.nonzero(masque[y])[0]
            if len(ligne):
                d = ligne.max()
                eau[y, d + 1:min(CADRE_W, d + 7)] = True
        for x in range(CADRE_W):
            col = np.nonzero(masque[:, x])[0]
            if len(col) and col.max() < CADRE_H - 2:
                b = col.max()
                eau[b + 1:min(CADRE_H, b + 6), x] = True
        eau &= couches["Base"][..., 3] > 0
        if eau.sum() > 40:
            c[eau] = couches["Base"][eau]
            c[eau, :3] = np.clip(c[eau, :3].astype(int) + 56, 0, 255).astype(np.uint8)
            c[..., 3] = np.where(eau, 255, 0)
            couches["River"] = nettoyer_orphelins(c)

        # --- River_Sparkles ---------------------------------------------------
        c = vide()
        rng = np.random.default_rng(11)
        libre = (couches["Base"][..., 3] > 0) & ~masque
        pts = np.argwhere(libre)
        if len(pts):
            blanc = (156, 234, 246) if nuit else (223, 247, 255)
            for k in rng.choice(len(pts), size=min(120, len(pts)), replace=False):
                y, x = pts[k]
                if x + 2 < CADRE_W:
                    c[y, x:x + 2, :3] = blanc
                    c[y, x:x + 2, 3] = 255
            couches["River_Sparkles"] = c

        # --- Objects_Under : le liseré de sable sous l'herbe ------------------
        sous = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            b = col.max()
            sous[b:min(CADRE_H, b + 4), x] = masque[b:min(CADRE_H, b + 4), x]
        if sous.sum() > 40:
            couches["Objects_Under"] = extraire(sous)

        # --- Objects : le plateau herbeux --------------------------------------
        couches["Objects"] = extraire(herbe & ~sous)

        # --- Objects_Over : affleurements de roche sur le plateau --------------
        haut = np.nonzero(masque.any(1))[0].min()
        aff = roche & (np.arange(CADRE_H)[:, None] < haut + 40)
        if aff.sum() > 40:
            couches["Objects_Over"] = extraire(aff)

        # --- Fringe : la crete, DEVANT le joueur --------------------------------
        crete = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            b = col.max()
            crete[max(0, b - 5):b + 1, x] = herbe[max(0, b - 5):b + 1, x]
        if crete.sum() > 40:
            couches["Fringe"] = extraire(crete)

        # --- Clouds : N frames, defilement en boucle parfaite -------------------
        base = bande_nuages(pieces)
        if nuit:
            base = teinte_nuit(base, 0.58, (96, 108, 172))
        pas = CADRE_W // N_FRAMES_NUAGES
        frames = []
        for i in range(N_FRAMES_NUAGES):
            c = vide()
            poser(c, np.roll(base, i * pas, axis=1), 0, 0)
            frames.append(c)
        couches["Clouds"] = frames[0]

        for i, f in enumerate(frames):
            Image.fromarray(f, "RGBA").save(
                SORTIE / f"Cliff_Clouds_{moment}_f{i}.png")

        # --- sortie --------------------------------------------------------------
        infos = {}
        for nom in ORDRE:
            img = couches.get(nom)
            if img is None or (img[..., 3] > 0).sum() == 0:
                continue
            fichier = f"Cliff_{nom}_{moment}.png"
            Image.fromarray(img, "RGBA").save(SORTIE / fichier)
            infos[nom] = {"fichier": fichier, "Layer": PROFONDEUR[nom], **controler(img)}
            if nom == "Clouds":
                infos[nom]["frames"] = [f"Cliff_Clouds_{moment}_f{i}.png"
                                        for i in range(N_FRAMES_NUAGES)]
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
