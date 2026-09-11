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
# PMD n'anime PAS l'eau en changeant les tuiles : les tuiles sont statiques et
# c'est la PALETTE qui tourne (color cycling). Mesure par la communaute de rip
# EoS : une rotation toutes les ~20 frames a 60 fps. On garde ce chiffre.
N_FRAMES_EAU = 8
PERIODE_EAU_FRAMES = 20            # 20/60e de seconde par pas
N_FRAMES_CIEL = 8
PERIODE_CIEL_FRAMES = 30

# --- sources ---------------------------------------------------------------
REF_SCENE = REF / "ref_metano_scene.png"     # IMG_4892 en pixels natifs
REF_ROCHE = REF / "ref_rock_texture.png"
REF_HERBE = REF / "ref_grass_texture.png"
REF_BORD = REF / "ref_cliff_edge.png"
GEN_CLIFF = REF / "gen_cliff.png"
TUILE_HERBE = REF / "tile_grass8.png"      # cellule 8x8 prelevee dans Metano
REF_PAROI = REF / "ref_paroi.png"          # la paroi rocheuse de la reference
TEX_PAROI = REF / "tex_paroi.png"          # colonnes rocheuses a facettes
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
# Crepuscule et nuit sont RELEVES sur les references fournies
# (`IMG_4888.jpeg`, `IMG_4889.png`) : mediane de chaque ligne de ciel sur la
# moitie droite du cadre, la ou aucune falaise ne masque le fond, puis
# quantification en 11 aplats francs comme le fait PMD.
CIEL_CREPUSCULE = [
    (0.00, (169, 149, 238)), (0.09, (171, 149, 229)), (0.18, (178, 145, 209)),
    (0.27, (192, 139, 184)), (0.36, (208, 137, 159)), (0.45, (218, 132, 135)),
    (0.54, (230, 125, 104)), (0.63, (238, 122, 83)), (0.72, (240, 128, 88)),
    (0.81, (243, 140, 96)), (0.90, (247, 158, 108)),
]
CIEL_NUIT = [
    (0.00, (0, 26, 96)), (0.20, (0, 31, 108)), (0.34, (0, 35, 118)),
    (0.46, (0, 39, 127)), (0.56, (0, 42, 134)), (0.64, (0, 46, 142)),
    (0.72, (0, 51, 150)), (0.79, (0, 55, 158)), (0.86, (8, 62, 165)),
    (0.92, (18, 72, 172)), (0.97, (34, 88, 180)),
]

# Un moment = une rampe de ciel, une planche de mer, un habillage.
MOMENTS = {
    # "nuit" = teinte appliquee a la falaise, "nuages" = teinte appliquee a la
    # bande de nuages. Sans cette derniere, les cumulus restaient blancs de
    # midi au-dessus d'un ciel orange, ce qui cassait toute l'ambiance.
    "jour":       {"ciel": "CIEL_JOUR",       "mer": None,
                   "nuit": None,             "nuages": None,
                   "astre": "soleil"},
    "crepuscule": {"ciel": "CIEL_CREPUSCULE", "mer": "mer_crepuscule.png",
                   "nuit": (0.46, (188, 104, 84)),
                   "nuages": (0.52, (240, 138, 96)),
                   "astre": "soleil"},
    "nuit":       {"ciel": "CIEL_NUIT",       "mer": "mer_nuit.png",
                   "nuit": (0.66, (34, 54, 132)),
                   "nuages": (0.58, (96, 108, 172)),
                   "astre": "lune"},
}

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


def separer_terrain(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coupe le terrain en (herbe, roche).

    La roche ocre de Metano a elle aussi G nettement au-dessus de B : ce qui
    la distingue, c'est qu'elle est CHAUDE, son rouge domine largement son
    vert. L'olive, lui, a R et G proches.
    """
    m = a[..., 3] > 0
    br = a[..., :3].astype(int)
    herbe = m & (br[..., 1] >= br[..., 0] - 20) & (br[..., 1] > br[..., 2] + 40)
    return herbe, m & ~herbe


def virer_pixels_mer(a: np.ndarray) -> np.ndarray:
    """Rend transparents les pixels de mer restes dans le decoupage.

    `gen_cliff.png` est decoupe dans une scene complete : le long du bord de
    la falaise, le remplissage de trous a avale des pixels d'eau. Ils sont
    francs a reconnaitre — bleu tres dominant — et ils ressortaient sous forme
    de mouchetis bleu dans la paroi.
    """
    out = a.copy()
    m = out[..., 3] > 0
    rgb = out[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mer = m & (b > r + 40) & (b > g + 10)
    out[mer, 3] = 0
    return out


# Rampe de roche, relevee au compte-gouttes sur `ref_cliff_edge.png`. La
# reference n'empile PAS des strates : elle pose des AMAS arrondis dans une
# gamme ocre serree, traverses de veines mauves, le tout cercle d'un contour
# brun fonce. Ces neuf tons sont les dominantes mesurees, du plus sombre au
# plus clair.
ROCHE_METANO = np.array([
    (119, 79, 39), (151, 103, 55), (167, 111, 55), (183, 127, 79),
    (199, 135, 71), (215, 167, 95), (231, 167, 103), (247, 207, 135),
    (255, 191, 119),
], dtype=np.uint8)

# Les veines d'erosion de la reference ne sont pas brunes mais MAUVES.
VEINE_METANO = np.array([(183, 103, 135), (199, 111, 151)], dtype=np.uint8)

# Contour : la falaise est cernee d'un trait brun fonce d'un pixel.
CONTOUR_METANO = np.array((119, 79, 39), dtype=np.uint8)


def _bruit(forme, freq, graine):
    """Bruit de valeur lisse — grille basse frequence interpolee.

    Le mouchetis pixel par pixel est exactement ce qu'il faut EVITER : la
    reference dessine des amas lisibles. On tire donc une grille grossiere
    puis on l'agrandit en bilineaire, ce qui donne des taches larges.
    """
    h, w = forme
    rng = np.random.default_rng(graine)
    gh, gw = max(2, h // freq + 2), max(2, w // freq + 2)
    g = rng.random((gh, gw))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.array(im).astype(float) / 255.0


def peindre_roche(masque: np.ndarray) -> np.ndarray:
    """Pave la paroi avec la VRAIE texture rocheuse, dans la silhouette donnee.

    C'est la methode du premier jet, retrouvee dans l'historique (commit
    b632cee) : la falaise d'origine venait de `gen_cliff_metano.png`, une
    illustration 1103x960 NETTE, ou la roche est dessinee en colonnes
    verticales a facettes. La source utilisee ensuite, `gen_cliff.png`
    (350x280), est floue — d'ou les tentatives de RECONSTRUIRE la texture au
    bruit, qui n'ont jamais rendu le pixel art de Metano.

    On prend donc un pave propre de cette illustration, remis a l'echelle du
    jeu (facteur 496/1103, celui du cadrage d'origine), et on le repete dans
    la silhouette. Les colonnes de la reference sont verticales : le pavage se
    fait donc en x seulement, et on decale chaque bande d'un cran vertical
    variable pour ne pas voir la repetition.
    """
    H, W = masque.shape
    src = Image.open(TEX_PAROI).convert("RGB")
    # La texture est etiree pour couvrir TOUTE la hauteur de la paroi d'un
    # seul tenant. Empiler plusieurs rangees laissait des coutures
    # horizontales franches en travers de la falaise, et la roche de la
    # reference est faite de colonnes verticales : l'etirer dans leur sens ne
    # la deforme pas, il allonge simplement les facettes.
    if H > src.height:
        src = src.resize((src.width, H), Image.LANCZOS)
    t = np.array(src)
    th, tw = t.shape[:2]

    # Pavage en miroir alterne. Decaler chaque bande verticalement (premier
    # essai) faisait apparaitre de longues DIAGONALES parasites : les facettes
    # de deux bandes voisines s'alignaient de biais. Le miroir, lui, raccorde
    # bord a bord sans creer de direction privilegiee.
    # Pavage en miroir alterne, DECALE en x a chaque rangee. Deux essais
    # avant celui-ci : un decalage vertical par bande creait de longues
    # diagonales (les facettes voisines s'alignaient de biais), et le miroir
    # seul laissait lire des symetries en papillon. Le decalage horizontal
    # aleatoire de chaque rangee casse ces axes.
    # Une seule rangee, mais des colonnes de LARGEUR VARIABLE, miroitees au
    # hasard et decalees verticalement. Le miroir systematique une colonne sur
    # deux donnait des paires en papillon tres lisibles ; le tirage aleatoire
    # de la largeur et du decalage les supprime tout en gardant le raccord.
    rng = np.random.default_rng(5)
    motif = np.zeros((H, W, 3), np.uint8)
    x = 0
    while x < W:
        larg = int(rng.integers(max(8, tw // 3), tw))
        x1 = int(rng.integers(0, max(1, tw - larg + 1)))
        bloc = t[:, x1:x1 + larg]
        if rng.random() < 0.5:
            bloc = bloc[:, ::-1]
        bloc = np.roll(bloc, int(rng.integers(0, th)), axis=0)
        pris = min(larg, W - x)
        motif[:, x:x + pris] = bloc[:H, :pris]
        x += pris

    # Projection sur la palette Metano : l'illustration source est en
    # milliers de teintes, PMDO en demande 16 par tuile.
    pal = palette_depuis([REF_PAROI, REF_ROCHE], maxi=48)
    chaud = (pal[:, 0] > pal[:, 2] + 25) & (pal[:, 0] > 70)
    pal = pal[chaud]
    d = (motif.reshape(-1, 1, 3).astype(int) - pal[None, :, :].astype(int))
    motif = pal[(d ** 2).sum(2).argmin(1)].reshape(H, W, 3).astype(np.uint8)

    out = np.zeros((H, W, 4), np.uint8)
    out[masque, :3] = motif[masque]
    out[masque, 3] = 255

    # Occlusion sous la levre herbeuse : la reference pose une ombre franche
    # juste sous le plateau, c'est elle qui detache la falaise du gazon.
    haut = np.full(W, H, dtype=int)
    for x in range(W):
        col = np.nonzero(masque[:, x])[0]
        if len(col):
            haut[x] = col.min()
    yy = np.mgrid[0:H, 0:W][0]
    prof = yy - haut[None, :]
    ombre = masque & (prof < 4)
    out[ombre, :3] = (out[ombre, :3].astype(int) * 0.62).astype(np.uint8)

    # Contour brun d'un pixel sur tout le pourtour visible.
    bord = np.zeros((H, W), bool)
    for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= ~np.roll(masque, (ddy, ddx), (0, 1))
    out[masque & bord, :3] = CONTOUR_METANO
    return out


def peindre_herbe(masque: np.ndarray, roche: np.ndarray) -> np.ndarray:
    """Pave le plateau, puis l'ourle d'ombre le long du bord de falaise."""
    H, W = masque.shape
    out = np.zeros((H, W, 4), np.uint8)
    if TUILE_HERBE.exists():
        t = np.array(Image.open(TUILE_HERBE).convert("RGB"))
        th, tw = t.shape[:2]
        motif = np.tile(t, (H // th + 1, W // tw + 1, 1))[:H, :W]
        out[masque, :3] = motif[masque]
    else:
        out[masque, :3] = HERBE_METANO[-1]
    out[masque, 3] = 255

    # Touffes : des amas plus sombres, pas un grain uniforme.
    # Touffes discretes : deux tons voisins seulement. Avec des tons eloignes,
    # le plateau prenait un aspect de camouflage militaire.
    touffe = _bruit((H, W), 13, 51)
    out[masque & (touffe < 0.24), :3] = HERBE_METANO[3]
    out[masque & (touffe > 0.84), :3] = HERBE_METANO[-1]

    # Ourlet : l'herbe s'assombrit sur les trois derniers pixels avant le
    # vide et avant la roche — sans lui, le plateau flotte au-dessus du bord.
    voisin = np.zeros((H, W), bool)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d = np.roll(masque, (dy, dx), (0, 1))
        voisin |= ~d
    bord = masque & (voisin | np.roll(roche, -1, 0) | np.roll(roche, -2, 0)
                     | np.roll(roche, -3, 0))
    out[bord, :3] = HERBE_METANO[0]
    return out


def habiller_terrain(a: np.ndarray) -> np.ndarray:
    """Redessine entierement le terrain aux materiaux de Metano Town.

    Ancienne approche, abandonnee : remapper la generation par luminosite sur
    une rampe ocre. Elle rendait la bonne GAMME mais gardait le mouchetis
    aleatoire de la generation, sans strate ni ombre — rien a voir avec le
    pixel art de la reference. On garde donc uniquement la SILHOUETTE et on
    repeint par-dessus.
    """
    out = virer_pixels_mer(a)
    herbe, roche = separer_terrain(out)

    res = np.zeros_like(out)
    if roche.any():
        res = peindre_roche(roche)
    if herbe.any():
        g = peindre_herbe(herbe, roche)
        sel = g[..., 3] > 0
        res[sel] = g[sel]
    res[out[..., 3] == 0] = 0
    return res


def cycler_palette(a: np.ndarray, rampe: np.ndarray, pas: int) -> np.ndarray:
    """Anime a la maniere de PMD : la tuile ne bouge pas, la palette tourne.

    C'est la technique reelle d'Explorers of Sky — verifiee par la communaute
    qui a rippe les tilesets : « every dungeon tile in the games are still
    sprites, they don't ever change graphics in order to animate ; water has
    the illusion of animating because its palette row changes color ».

    On identifie donc, dans le calque, les pixels qui portent une couleur de
    la rampe, et on les remplace par la couleur decalee de `pas` crans dans
    cette meme rampe. Aucun pixel ne se deplace : seule sa couleur change.
    """
    out = a.copy()
    m = out[..., 3] > 0
    if not m.any() or len(rampe) == 0:
        return out
    rgb = out[..., :3].astype(int)
    n = len(rampe)
    for i, couleur in enumerate(rampe):
        sel = m & (np.abs(rgb - couleur).sum(2) == 0)
        if sel.any():
            out[sel, :3] = rampe[(i + pas) % n]
    return out


def rampe_depuis(a: np.ndarray, mini: int = 24) -> np.ndarray:
    """Ordonne les couleurs d'un calque par luminosite : la rampe a cycler."""
    m = a[..., 3] > 0
    if not m.any():
        return np.zeros((0, 3), int)
    cols, comptes = np.unique(a[m][:, :3].astype(int), axis=0, return_counts=True)
    cols = cols[comptes >= mini]
    if len(cols) < 2:
        return np.zeros((0, 3), int)
    return cols[np.argsort(cols.sum(1))]


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

def laver_nuage(pc: np.ndarray) -> np.ndarray:
    """Efface les pixels mauves parasites des cumulus decoupes.

    Les nuages sont preleves dans la scene source, ou ils cotoient une
    banniere : quelques pixels lilas sont partis avec eux et formaient une
    tache violette en plein ciel. Le seuil est volontairement BAS — les
    fautifs vont du lilas franc au blanc a peine rose (255, 237, 255), qu'un
    seuil large laissait passer.
    """
    m = pc[..., 3] > 0
    r, g, b = (pc[..., k].astype(int) for k in range(3))
    sale = m & (b > g + 6) & (r > g)
    if not sale.any():
        return pc
    pc = pc.copy()
    gris = np.minimum(pc[..., 1], np.minimum(pc[..., 0], pc[..., 2]))
    for k in range(3):
        pc[..., k] = np.where(sale, np.maximum(gris, 200), pc[..., k])
    return pc


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
    # Les cumulus decoupes dans la scene source trainent quelques pixels
    # mauves parasites (bord d'une banniere voisine). Ils ressortaient comme
    # une tache violette en plein ciel : on les repousse vers le blanc.
    pieces = [laver_nuage(pc) for pc in pieces]
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

def construire_ocean(pal: np.ndarray, planche: str | None = None) -> np.ndarray:
    """Pave l'ocean, en respectant la degression de la reference.

    `planche` pointe une mer RELEVEE sur les references de crepuscule / nuit
    (`cliff/ref2/mer_*.png`) : chaque ligne y porte la couleur mediane de la
    ligne correspondante dans l'image d'origine. On garde alors la STRUCTURE
    de vagues de la mer de jour et on ne remplace que sa gamme, ligne a ligne.
    """
    hauteur = CADRE_H - HORIZON
    src = nettoyer_orphelins(projeter_palette(
        cadrage_entier(Image.open(GEN_SEA).convert("RGBA"), CADRE_W), pal))
    if planche and (REF / planche).exists():
        rampe = np.array(Image.open(REF / planche).convert("RGB")).astype(int)
        base = src[:min(src.shape[0], hauteur)].astype(int)
        h = base.shape[0]
        lum = base[..., :3].sum(2) / 765.0
        lo, hi = lum.min(), max(lum.max(), lum.min() + 1e-6)
        t = (lum - lo) / (hi - lo)
        out = src.copy()
        # On quantifie le facteur de relief AVANT de l'appliquer : moduler en
        # continu creait une couleur par pixel et faisait exploser le compte
        # par tuile (597 couleurs, 95 % de conformite). Avec 5 crans, chaque
        # ligne ne porte plus que 5 teintes et la mer reste conforme.
        crans = 5
        q = np.round(t * (crans - 1)) / (crans - 1)
        for y in range(h):
            cible = rampe[min(y, rampe.shape[0] - 1), 0].astype(float)
            f = (0.74 + 0.52 * q[y])[:, None]
            out[y, :, :3] = np.clip(cible[None, :] * f, 0, 255).astype(np.uint8)
        src = nettoyer_orphelins(out)
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

    oceans = {m: construire_ocean(pal, r["mer"]) for m, r in MOMENTS.items()}

    # --- la falaise : collee au bord GAUCHE et au bord BAS ----------------
    # Elle mord ces deux bords, donc aucun liseré de ciel ne peut apparaitre
    # derriere. En revanche elle ne couvre PAS toute la largeur : la mer doit
    # rester visible a droite et la ligne d'horizon doit se lire, comme sur la
    # reference.
    # `gen_cliff.png` est desormais decoupe dans la reference editee : il
    # arrive deja detoure, avec un vrai canal alpha. Il ne faut donc SURTOUT
    # pas le repasser par `detourer_magenta()`, qui le relirait en RGB et
    # rendrait tout le rectangle opaque. La reference a la mer a gauche et la
    # terre a droite : on la retourne pour retrouver notre layout.
    src = Image.open(GEN_CLIFF).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
    # On cadre par la HAUTEUR, pas par la largeur : rogner le haut amputait le
    # plateau et ne laissait qu'une lisiere d'herbe au-dessus de la paroi.
    MARGE_MER = 64
    HAUT_TERRE = CADRE_H - HORIZON - MARGE_MER
    LARGEUR_TERRE = max(8, round(src.width * HAUT_TERRE / src.height))
    # ORDRE IMPORTANT : on habille le terrain AVANT toute projection globale.
    # Passer d'abord par `virer_herbe_metano` + `projeter_palette(pal)` melait
    # les teintes d'herbe et de roche, et la separation qui suit reclassait
    # alors des pixels de paroi en herbe — d'ou un mouchetis jaune dans la
    # falaise. On separe donc sur l'image redimensionnee brute.
    cliff_px = nettoyer_orphelins(
        habiller_terrain(cadrage_entier(src, LARGEUR_TERRE, HAUT_TERRE)))

    # --- nuages ------------------------------------------------------------
    nuages_src = nettoyer_orphelins(
        cadrage_entier(detourer_magenta(GEN_CLOUDS), 560))
    pieces = composantes(nuages_src)

    manifeste = {"zone": "Cliff", "tile_px": TILE, "cadre": [CADRE_W, CADRE_H],
                 "horizon_y": HORIZON,
                 "animations": {
                     "Clouds": {"type": "defilement", "frames": N_FRAMES_NUAGES,
                                "wrap": "horizontal",
                                "pas_px": CADRE_W // N_FRAMES_NUAGES},
                     "Base": {"type": "palette_cycling", "frames": N_FRAMES_EAU,
                              "periode_frames_60fps": PERIODE_EAU_FRAMES},
                     "River": {"type": "palette_cycling", "frames": N_FRAMES_EAU,
                               "periode_frames_60fps": PERIODE_EAU_FRAMES},
                     "Sky": {"type": "palette_cycling", "frames": N_FRAMES_CIEL,
                             "periode_frames_60fps": PERIODE_CIEL_FRAMES},
                 },
                 "moments": {}}

    for moment, reglage in MOMENTS.items():
        nuit = moment == "nuit"
        sombre = reglage["nuit"]          # (force, teinte) ou None
        couches: dict[str, np.ndarray] = {}
        vide = lambda: np.zeros((CADRE_H, CADRE_W, 4), np.uint8)  # noqa: E731

        # --- Sky ----------------------------------------------------------
        couches["Sky"] = construire_ciel(globals()[reglage["ciel"]])

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
        if reglage["astre"] == "lune":
            rayon, cy, cx = 22, 46, 96
            ton, halo = (247, 247, 215), (215, 223, 175)
        elif moment == "crepuscule":
            # au crepuscule le soleil est bas sur l'horizon et vire au rouge
            rayon, cy, cx = 24, HORIZON - 26, 108
            ton, halo = (255, 179, 71), (247, 122, 63)
        else:
            rayon, cy, cx = 18, 46, 96
            ton, halo = (255, 231, 111), (255, 207, 71)
        yy, xx = np.ogrid[:CADRE_H, :CADRE_W]
        d2 = (yy - cy) ** 2 + (xx - cx) ** 2
        c[d2 <= rayon ** 2, :3] = ton
        c[(d2 <= rayon ** 2) & (d2 > (rayon - 3) ** 2), :3] = halo
        c[..., 3] = np.where(d2 <= rayon ** 2, 255, 0)
        couches["Moon"] = c

        # --- Base : l'ocean ---------------------------------------------------
        c = vide()
        poser(c, oceans[moment], 0, HORIZON)
        couches["Base"] = c

        # --- la falaise, decomposee comme chez Metano ------------------------
        terre = teinte_nuit(cliff_px, *sombre) if sombre else cliff_px
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

        # `Cliffs` porte la falaise ENTIERE — plateau herbeux et paroi
        # rocheuse ensemble — sur un layer unique, comme demande. On ne la
        # redecoupe donc plus en Objects / Objects_Over / Fringe.
        couches["Cliffs"] = extraire(masque)

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
        # `masque` seul ne suffit pas : la falaise a ete cadree par la hauteur
        # et ses pixels transparents laissaient passer les scintillements, qui
        # se posaient alors SUR la roche. On exclut donc toute la boite de la
        # terre, pas seulement ses pixels opaques.
        boite = np.zeros((CADRE_H, CADRE_W), bool)
        ys_t, xs_t = np.nonzero(masque)
        if len(ys_t):
            boite[ys_t.min():, :xs_t.max() + 1] = True
        libre = (couches["Base"][..., 3] > 0) & ~masque & ~boite
        pts = np.argwhere(libre)
        if len(pts):
            blanc = (156, 234, 246) if nuit else (223, 247, 255)
            for k in rng.choice(len(pts), size=min(120, len(pts)), replace=False):
                y, x = pts[k]
                if x + 2 < CADRE_W:
                    c[y, x:x + 2, :3] = blanc
                    c[y, x:x + 2, 3] = 255
            couches["River_Sparkles"] = c

        # --- Clouds : N frames, defilement en boucle parfaite -------------------
        base = laver_nuage(bande_nuages(pieces))
        if reglage["nuages"]:
            base = nettoyer_orphelins(teinte_nuit(base, *reglage["nuages"]))
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

        # --- animation par cycling de palette, comme PMD ----------------------
        # L'eau et le ciel ne changent pas de tuile : on ecrit N variantes du
        # MEME calque, ou seule la palette a tourne. Le moteur les joue en
        # boucle sur place.
        anim = {}
        for nom, n_frames, largeur in (("Base", N_FRAMES_EAU, 1),
                                       ("River", N_FRAMES_EAU, 1),
                                       ("Sky", N_FRAMES_CIEL, 1)):
            # le ciel derive plus lentement que la mer : voir PERIODE_*
            src = couches.get(nom)
            if src is None:
                continue
            rampe = rampe_depuis(src)
            if len(rampe) < 2:
                continue
            noms = []
            for i in range(n_frames):
                # PMD decale la palette d'UN cran a la fois : le mouvement est
                # une ondulation lente, pas un clignotement. Un pas
                # proportionnel a la longueur de rampe faisait sauter l'eau de
                # plusieurs teintes d'un coup.
                pas = i * largeur
                f = cycler_palette(src, rampe, pas)
                fichier = f"Cliff_{nom}_{moment}_c{i}.png"
                Image.fromarray(f, "RGBA").save(SORTIE / fichier)
                noms.append(fichier)
            anim[nom] = noms

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
                infos[nom]["animation"] = "defilement"
            if nom in anim:
                infos[nom]["frames"] = anim[nom]
                infos[nom]["animation"] = "palette_cycling"
        manifeste["moments"][moment] = infos

        comp = Image.new("RGBA", (CADRE_W, CADRE_H), (0, 0, 0, 0))
        for nom in ORDRE:
            if nom in couches:
                comp.alpha_composite(Image.fromarray(couches[nom], "RGBA"))
        comp.save(RACINE / "cliff" / f"cliff_{moment}.png")

        # --- le rendu final anime, en GIF -------------------------------------
        # On rejoue le meme empilement N fois : a la frame i, chaque layer
        # anime prend SA variante i — cycling de palette pour l'eau et le
        # ciel, defilement pour les nuages. Les layers fixes sont reutilises
        # tels quels. Le GIF boucle donc exactement comme en jeu.
        n_gif = max(N_FRAMES_EAU, N_FRAMES_NUAGES, N_FRAMES_CIEL)
        images = []
        for i in range(n_gif):
            f = Image.new("RGBA", (CADRE_W, CADRE_H), (0, 0, 0, 0))
            for nom in ORDRE:
                if nom not in couches:
                    continue
                if nom == "Clouds":
                    src = frames[i % N_FRAMES_NUAGES]
                elif nom in anim:
                    lst = anim[nom]
                    src = np.array(Image.open(SORTIE / lst[i % len(lst)]))
                else:
                    src = couches[nom]
                f.alpha_composite(Image.fromarray(src, "RGBA"))
            images.append(f.convert("P", palette=Image.ADAPTIVE, colors=256))
        images[0].save(RACINE / "cliff" / f"cliff_{moment}.gif",
                       save_all=True, append_images=images[1:],
                       duration=int(1000 * PERIODE_EAU_FRAMES / 60),
                       loop=0, disposal=2, optimize=False)

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
