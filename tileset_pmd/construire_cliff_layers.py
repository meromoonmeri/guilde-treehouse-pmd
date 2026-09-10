from __future__ import annotations

"""Construit la zone `Cliff` en layers modulaires, methode Halcyon.

La methode auditee dans `AUDIT_METHODE_LAYERS_HALCYON.md` est appliquee ici de
bout en bout :

  * **un layer = une fonction visuelle**, pas un objet : tout le ciel dans un
    calque, toutes les etoiles dans un autre, etc. ;
  * **un layer = un fichier qui porte son nom**, `Cliff_<Layer>_<moment>.png`,
    exactement comme `Guild_Dining_Room_Floor.tile` ;
  * **le champ `Layer` vaut 0 ou 4** : 0 pour ce qui est rendu sous le joueur,
    4 pour ce qui passe devant lui ;
  * **vocabulaire d'exterieur** (`Base`, `Objects`, `Fringe`), jamais
    `Floor`/`Walls` qui sont reserves aux interieurs.

Empilement retenu, du fond vers l'avant :

    Sky            0   le degrade de ciel, seul calque opaque plein cadre
    Stars          0   etoiles et scintillements      (nuit seulement)
    Moon           0   lune ou soleil selon le moment
    Clouds         0   nuages
    Sea            0   la mer, jusqu'a la ligne d'horizon
    Base           0   la falaise et son plateau herbeux
    Objects        0   rochers et buissons poses sur le plateau
    Fringe         4   herbes hautes de premier plan, DEVANT le joueur

Chaque calque est produit en jour et en nuit, au meme cadre et au meme offset,
donc superposable au pixel pres.

Usage :
    python3 construire_cliff_layers.py
"""

from collections import Counter, deque
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_sprite_pmdo import (  # noqa: E402
    cadrage_entier,
    nettoyer_orphelins,
    palette_depuis,
    projeter_palette,
)

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "cliff" / "layers"
SOURCES = Path("/tmp")

TILE = 8
CADRE_W, CADRE_H = 648, 432          # meme cadre que `exterieur/`
HORIZON = 176                        # ligne de mer, multiple de 8

# Structure relevee sur `metano_town.rsground` (Halcyon) :
#   Base(0) > Cliffs(0) > River(0) > Objects Under(0) > Objects(0) >
#   Objects Over(0) > Fringe(4)
# On la reprend telle quelle, en prefixant les calques de ciel qui, chez eux,
# vivent dans `Background` et non dans `Layers`.
PROFONDEUR = {
    "Sky": 0,
    "Stars": 0,
    "Moon": 0,
    "Clouds": 0,
    "Base": 0,           # la mer : le terrain de fond de la zone
    "Cliffs": 0,         # la falaise, layer dedie comme chez Metano
    "River": 0,          # ressac et ecume au pied de la falaise
    "River_Sparkles": 0, # scintillements, comme Metano_Town_River_Sparkles
    "Objects_Under": 0,
    "Objects": 0,
    "Objects_Over": 0,
    "Fringe": 4,
}

ORDRE = ["Sky", "Stars", "Moon", "Clouds", "Base", "Cliffs", "River",
         "River_Sparkles", "Objects_Under", "Objects", "Objects_Over", "Fringe"]


# --------------------------------------------------------------------------

def detourer_magenta(chemin: Path) -> Image.Image:
    """Retire le fond magenta d'une generation, contour franc."""
    a = np.array(Image.open(chemin).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 110) & (b > 110) & (g < 120) & ((r - g) > 45) & ((b - g) > 45)
    m = Image.fromarray(((~mag) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))
    return Image.fromarray(np.dstack([a.astype(np.uint8), np.array(m)]), "RGBA")


# Palette de reference : les tilesets de falaise REELS de Metano Town, extraits
# de `Palikadude/Halcyon` (`Metano_Town_Cliffs.tile`, `Metano_Town_Fringe.tile`).
# Metano partage ses tilesets avec Treasure Town : c'est donc la colorimetrie
# authentique du jeu — herbe jaune-olive (200,216,80), roche ocre-sable
# (191,131,111), eau cyan (80,128,184) — et non les verts froids de notre
# paysage de vallee.
REFS_METANO = [
    RACINE / "cliff" / "reference_metano_cliffs.png",
    RACINE / "cliff" / "reference_metano_fringe.png",
    RACINE / "cliff" / "reference_metano_river.png",
    RACINE / "cliff" / "reference_metano_sparkles.png",
]

# L'eau de Metano ne fait que 19 couleurs, cyan clair a liseré bleu. On la
# reserve au calque d'eau pour que la mer ne derive pas vers le vert.
REFS_EAU = [
    RACINE / "cliff" / "reference_metano_river.png",
    RACINE / "cliff" / "reference_metano_sparkles.png",
]


def palette_projet(extra: list[Path] | None = None, n_extra: int = 40) -> np.ndarray:
    """Palette des tilesets de falaise de Metano Town, elargie si besoin."""
    pal = palette_depuis(REFS_METANO)
    if extra:
        for c in extra:
            a = np.array(Image.open(c).convert("RGBA"))
            px = a[a[..., 3] > 127][:, :3]
            if len(px) == 0:
                continue
            q = Image.fromarray(px.reshape(-1, 1, 3)).quantize(
                colors=n_extra, method=Image.MEDIANCUT)
            sup = np.array(q.getpalette()[:n_extra * 3]).reshape(-1, 3)
            pal = np.vstack([pal, sup])
    return pal


# L'herbe de Metano Town n'est pas verte : elle est jaune-olive. Ces quatre
# tons sont ceux effectivement mesures dans `Metano_Town_Cliffs.tile`.
HERBE_METANO = np.array([
    (184, 208, 64),
    (200, 216, 80),
    (215, 224, 104),
    (184, 192, 80),
], dtype=int)


def virer_herbe_metano(a: np.ndarray) -> np.ndarray:
    """Bascule les verts de la generation vers l'olive de Treasure Town.

    Projeter sur la palette complete ne suffit pas : elle contient aussi les
    verts sombres du feuillage, et chaque vert froid trouvait un vert froid
    proche. On force donc explicitement tout pixel a dominante verte vers le
    ton d'herbe Metano de luminosite equivalente.
    """
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    vert = m & (g > r + 6) & (g > b + 24)
    if not vert.any():
        return out
    lum = rgb[vert].sum(1)
    lo, hi = lum.min(), max(lum.max(), lum.min() + 1)
    rang = ((lum - lo) / (hi - lo) * (len(HERBE_METANO) - 1)).round().astype(int)
    out[vert, :3] = HERBE_METANO[rang]
    return out


def au_format(img: Image.Image, largeur: int, palette: np.ndarray,
              herbe: bool = False) -> np.ndarray:
    a = cadrage_entier(img, largeur)
    if herbe:
        a = virer_herbe_metano(a)
    return nettoyer_orphelins(projeter_palette(a, palette))


def poser(cadre: np.ndarray, obj: np.ndarray, x: int, y: int) -> None:
    """Colle obj dans cadre a (x, y), en respectant l'alpha binaire."""
    h, w = obj.shape[:2]
    H, W = cadre.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sous = obj[y0 - y:y1 - y, x0 - x:x1 - x]
    m = sous[..., 3] > 0
    zone = cadre[y0:y1, x0:x1]
    zone[m] = sous[m]


def decouper_objets(a: np.ndarray, seuil: int = 60) -> list[np.ndarray]:
    """Isole chaque element d'une planche par composante connexe."""
    m = a[..., 3] > 0
    H, W = m.shape
    seen = np.zeros_like(m)
    out = []
    for y in range(H):
        for x in range(W):
            if m[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = 1
                pts = []
                while q:
                    cy, cx = q.popleft()
                    pts.append((cy, cx))
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = 1
                                q.append((ny, nx))
                if len(pts) > seuil:
                    ys = [p[0] for p in pts]
                    xs = [p[1] for p in pts]
                    out.append(a[min(ys):max(ys) + 1, min(xs):max(xs) + 1].copy())
    out.sort(key=lambda o: -(o[..., 3] > 0).sum())
    return out


def teinte_nuit(a: np.ndarray, force: float = 0.55,
                cible=(70, 88, 150)) -> np.ndarray:
    """Bascule un calque de jour vers une ambiance nocturne froide."""
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[m][:, :3].astype(float)
    for i in range(3):
        rgb[:, i] = rgb[:, i] * (1 - force) + cible[i] * force * (rgb[:, i] / 255.0)
    out[m, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
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
    pal_base = palette_projet()

    # --- sources, une seule fois ---
    cliff = detourer_magenta(SOURCES / "cl_cliff.png")
    objets_ciel = detourer_magenta(SOURCES / "cl_ciel_obj.png")
    mer = Image.open(SOURCES / "cl_mer.png").convert("RGBA")
    ciel_j = Image.open(SOURCES / "cl_ciel_jour.png").convert("RGBA")
    ciel_n = Image.open(SOURCES / "cl_ciel_nuit.png").convert("RGBA")

    pal_ciel = palette_projet([SOURCES / "cl_ciel_nuit.png"], 32)
    pal_obj = palette_projet([SOURCES / "cl_ciel_obj.png"], 48)
    pal_eau = palette_depuis(REFS_EAU)

    cliff_px = au_format(cliff, 560, palette_projet(), herbe=True)
    objets_px = au_format(objets_ciel, 520, pal_obj)
    mer_px = au_format(mer, CADRE_W, palette_depuis(REFS_EAU))
    ciel = {
        "jour": au_format(ciel_j, CADRE_W, pal_ciel),
        "nuit": au_format(ciel_n, CADRE_W, pal_ciel),
    }

    pieces = decouper_objets(objets_px)

    # On classe par la TEINTE, pas par la taille : le soleil est dore, les
    # lunes sont grises et rondes, les nuages sont blancs et larges, les
    # etoiles sont minuscules. Trier par taille melangeait lune et nuage.
    def teinte(p):
        m = p[..., 3] > 0
        return p[m][:, :3].astype(int).mean(0)

    def rond(p):
        h, w = p.shape[:2]
        return 0.7 < w / max(h, 1) < 1.45

    soleil, lunes, nuages, etoiles = None, [], [], []
    for p in pieces:
        r, g, b = teinte(p)
        n = int((p[..., 3] > 0).sum())
        if n < 320:
            etoiles.append(p)
        elif r - b > 55 and rond(p):
            soleil = p if soleil is None else soleil
        elif rond(p) and abs(r - b) < 40:
            lunes.append(p)
        else:
            nuages.append(p)
    # la plus petite lune fait une jolie pleine lune ; sinon on prend ce qu'on a
    lunes.sort(key=lambda p: (p[..., 3] > 0).sum())

    manifeste = {"zone": "Cliff", "tile_px": TILE,
                 "cadre": [CADRE_W, CADRE_H], "horizon_y": HORIZON,
                 "moments": {}}

    for moment in ("jour", "nuit"):
        couches: dict[str, np.ndarray] = {}
        vide = lambda: np.zeros((CADRE_H, CADRE_W, 4), np.uint8)  # noqa: E731

        # --- Sky : plein cadre, opaque ---
        c = vide()
        s = ciel[moment]
        poser(c, s[:CADRE_H, :CADRE_W], 0, 0)
        if (c[..., 3] == 0).any():        # complete si la source est plus courte
            manque = c[..., 3] == 0
            c[manque] = c[c[..., 3] > 0][0]
        couches["Sky"] = c

        # --- Stars : nuit seulement ---
        if moment == "nuit" and etoiles:
            c = vide()
            rng = np.random.default_rng(7)
            for i in range(46):
                e = etoiles[i % len(etoiles)]
                x = int(rng.integers(4, CADRE_W - e.shape[1] - 4))
                y = int(rng.integers(4, HORIZON - 44))
                poser(c, e, x, y)
            couches["Stars"] = c

        # --- Moon : la lune la nuit, le soleil le jour ---
        astre = soleil if moment == "jour" else (lunes[0] if lunes else None)
        if astre is not None:
            c = vide()
            poser(c, astre, CADRE_W - astre.shape[1] - 72, 28)
            couches["Moon"] = c

        # --- Clouds ---
        if nuages:
            c = vide()
            placements = [(40, 30), (250, 16), (430, 44), (150, 78), (520, 92)]
            for (x, y), n in zip(placements, nuages):
                nn = n if moment == "jour" else teinte_nuit(n, 0.6)
                poser(c, nn, x, y)
            couches["Clouds"] = c

        # --- Base : la mer, terrain de fond de la zone ---
        # Chez Metano, `Base` est le sol de la carte et `Cliffs` un layer a
        # part. Ici le sol de la zone, c'est l'ocean.
        c = vide()
        m2 = mer_px if moment == "jour" else teinte_nuit(mer_px, 0.62, (40, 60, 130))
        hauteur = CADRE_H - HORIZON
        tuile = m2[:hauteur] if m2.shape[0] >= hauteur else np.resize(m2, (hauteur, CADRE_W, 4))
        poser(c, tuile[:, :CADRE_W], 0, HORIZON)
        couches["Base"] = c

        # --- Cliffs : la falaise, layer dedie comme Metano_Town_Cliffs ---
        c = vide()
        cl = cliff_px if moment == "jour" else teinte_nuit(cliff_px, 0.5)
        poser(c, cl, (CADRE_W - cl.shape[1]) // 2, CADRE_H - cl.shape[0] + 16)
        couches["Cliffs"] = c

        cliff_m = couches["Cliffs"][..., 3] > 0
        ys, xs = np.nonzero(cliff_m)
        haut = ys.min()

        # --- River : le ressac au pied de la falaise ---
        # Metano garde son eau dans un layer separe de la Base. On fait pareil :
        # la frange d'ecume qui borde la roche vit dans `River`, donc on peut
        # l'animer plus tard sans toucher a la mer ni a la falaise.
        c = vide()
        eau_m = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(cliff_m[:, x])[0]
            if len(col) == 0:
                continue
            bas = col.max()
            if bas >= CADRE_H - 2:
                continue
            eau_m[bas + 1:min(CADRE_H, bas + 9), x] = True
        eau_m &= couches["Base"][..., 3] > 0
        src = couches["Base"]
        c[eau_m] = src[eau_m]
        c[..., 3] = np.where(eau_m, 255, 0)
        # on eclaircit le ressac vers le cyan clair de Metano
        if eau_m.any():
            c[eau_m, :3] = np.clip(c[eau_m, :3].astype(int) + 46, 0, 255).astype(np.uint8)
            couches["River"] = nettoyer_orphelins(projeter_palette(c, pal_eau))

        # --- River_Sparkles : quelques scintillements sur l'eau ---
        c = vide()
        rng = np.random.default_rng(11)
        eau_libre = (couches["Base"][..., 3] > 0) & ~cliff_m
        pts = np.argwhere(eau_libre)
        if len(pts):
            blanc = (246, 250, 255) if moment == "jour" else (156, 234, 246)
            for k in rng.choice(len(pts), size=min(90, len(pts)), replace=False):
                y, x = pts[k]
                if x + 2 < CADRE_W:
                    c[y, x:x + 2, :3] = blanc
                    c[y, x:x + 2, 3] = 255
            couches["River_Sparkles"] = c

        # --- l'herbe du plateau ---
        # L'herbe de Metano est olive : G domine B franchement, mais R reste
        # eleve. Tester "vert > rouge" ne marche donc plus une fois la
        # colorimetrie appliquee — on teste G contre B.
        br = couches["Cliffs"][..., :3].astype(int)
        vert = (br[..., 1] > br[..., 2] + 55) & (br[..., 1] > 140)
        herbe = cliff_m & vert

        # --- Objects_Under : la lisiere d'herbe qui mord sur la roche ---
        c = vide()
        sous = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            bas = col.max()
            sous[bas:min(CADRE_H, bas + 4), x] = cliff_m[bas:min(CADRE_H, bas + 4), x]
        c[sous] = couches["Cliffs"][sous]
        c[..., 3] = np.where(sous, 255, 0)
        if sous.sum() > 40:
            couches["Objects_Under"] = c

        # --- Objects : rochers et buissons du plateau ---
        c = vide()
        zone_obj = herbe & (np.arange(CADRE_H)[:, None] < haut + 60)
        c[zone_obj] = couches["Cliffs"][zone_obj]
        c[..., 3] = np.where(zone_obj, 255, 0)
        couches["Objects"] = c

        # --- Objects_Over : les rochers sombres poses sur l'herbe ---
        c = vide()
        roche = cliff_m & (np.arange(CADRE_H)[:, None] < haut + 40) & ~vert
        c[roche] = couches["Cliffs"][roche]
        c[..., 3] = np.where(roche, 255, 0)
        if roche.sum() > 40:
            couches["Objects_Over"] = c

        # --- Fringe : la crete, DEVANT le joueur (Layer = 4) ---
        c = vide()
        zone_fr = np.zeros((CADRE_H, CADRE_W), bool)
        for x in range(CADRE_W):
            col = np.nonzero(herbe[:, x])[0]
            if len(col) == 0:
                continue
            bas = col.max()
            zone_fr[max(0, bas - 5):bas + 1, x] = herbe[max(0, bas - 5):bas + 1, x]
        c[zone_fr] = couches["Cliffs"][zone_fr]
        c[..., 3] = np.where(zone_fr, 255, 0)
        if zone_fr.sum() > 40:
            couches["Fringe"] = c

        infos = {}
        for nom in ORDRE:
            if nom not in couches:
                continue
            img = couches[nom]
            if (img[..., 3] > 0).sum() == 0:
                continue
            fichier = f"Cliff_{nom}_{moment}.png"
            Image.fromarray(img, "RGBA").save(SORTIE / fichier)
            infos[nom] = {"fichier": fichier, "Layer": PROFONDEUR[nom], **controler(img)}
        manifeste["moments"][moment] = infos

        # apercu compose
        comp = Image.new("RGBA", (CADRE_W, CADRE_H), (0, 0, 0, 0))
        for nom in ORDRE:
            if nom in couches:
                comp.alpha_composite(Image.fromarray(couches[nom], "RGBA"))
        comp.save(RACINE / "cliff" / f"cliff_{moment}.png")

    (SORTIE / "Cliff_layers.json").write_text(json.dumps(manifeste, indent=2))

    print("=== Cliff ===")
    for moment, infos in manifeste["moments"].items():
        print(f"\n  [{moment}]")
        print(f"    {'layer':<10}{'Layer':>6}{'cellules':>10}{'coul':>7}"
              f"{'moy/tui':>9}{'<=16':>8}{'semi':>6}{'occup':>9}")
        for nom, d in infos.items():
            print(f"    {nom:<10}{d['Layer']:>6}{d['cellules_occupees']:>10}"
                  f"{d['couleurs']:>7}{d['moy_par_tuile']:>9}"
                  f"{d['pct_tuiles_conformes']:>7}%{d['semi_transparents']:>6}"
                  f"{d['occupation_pct']:>8}%")


if __name__ == "__main__":
    construire()
