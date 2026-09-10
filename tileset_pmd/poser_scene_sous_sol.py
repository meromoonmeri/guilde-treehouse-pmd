from __future__ import annotations

"""Amenage le sous-sol du cafe en salle de concert privee.

Rien de la variante caverne n'est regenere. La coque de la salle ET son
mobilier de cafe (comptoirs a auvent raye, guirlande de fanions, tables-souches,
panneau, caisses, plantes) viennent du calque d'origine
`interieur/variante_caverne/`, simplement passes au format PMDO par
`pipeline_sprite_pmdo.py`. Le sous-sol reprend donc litteralement la variante
caverne du cafe, a laquelle on ajoute la scene.

Seuls les elements specifiques au spectacle (estrade, rideaux, bancs, fauteuil,
lampadaires) sont generes, sur une planche d'objets detaches, comme le prescrit
`AUDIT_PIPELINE_SPRITE.md`.

Layout, calque sur celui de la salle du haut : la scene occupe le fond de la
salle (mur du nord), le public lui fait face en rangees, l'escalier reste
degage puisqu'il est l'entree.

Trois fichiers par moment de la journee :
  * `sous_sol_sans_deco_<moment>.png` — la salle vide ;
  * `sous_sol_deco_seule_<moment>.png` — les elements seuls, fond transparent ;
  * `sous_sol_avec_deco_<moment>.png` — la composition.

Usage :
    python3 poser_scene_sous_sol.py
"""

from collections import deque, Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

RACINE = Path(__file__).resolve().parent.parent
SALLE = RACINE / "sous_sol"
PLANCHE = SALLE / "scene_objets_pmdo.png"
# Le mobilier de cafe repris tel quel a la variante caverne d'origine.
PLANCHE_CAFE = SALLE / "cafe_caverne_deco_pmdo.png"

# Elements decoupes de la deco de `interieur/variante_caverne/`, par taille
# decroissante. Ce sont les pixels d'origine, pas une regeneration.
NOMS_CAFE = [
    "stand_gauche",        # comptoir a auvent raye rouge
    "stand_droit",         # comptoir a auvent raye bleu
    "coin_plantes_droit",
    "tables_gauche",       # tables-souches et tabourets
    "tables_droite",
    "panneau_caisses",     # panneau d'affichage et caisses
    "table_centre",
    "guirlande",           # guirlande de fanions rouges
    "buissons_bas",
]

CADRE_W, CADRE_H = 576, 400

# Les objets sont indexes dans l'ordre de lecture de la planche generee.
NOMS = [
    "estrade",        # 0  plateforme de scene
    "rideau",         # 1  grand rideau de velours rouge
    "bandeau",        # 2  frise de velours suspendue
    "banc",           # 3  banc du public, avec dossier
    "fauteuil",       # 4  fauteuil rouge capitonne
    "lampadaire",     # 5  lampadaire de scene en laiton
    "torche",         # 6  torche murale
    "tabouret",       # 7  tabouret rond en velours
    "pupitre",        # 8  pupitre a partition
    "tambour",        # 9  tambour
    "tapis",          # 10 tapis rouge
    "cordon",         # 11 cordon de velours sur poteau
    "tonneau",        # 12 tonneau
    "plante",         # 13 fougere en pot
]

# (objet, x du centre, y du BAS) dans le cadre 576 x 400.
# Le sol utile va de y=28 (fond) a y=320, large de ~445 px entre x=66 et x=510.
PLAN = [
    # --- la guirlande de fanions du cafe, en haut du mur du fond ---
    ("guirlande", 288, 88),
    # --- le fond de scene : trois pans de rideau formant un mur de velours ---
    ("rideau", 216, 132),
    ("rideau", 288, 132),
    ("rideau", 360, 132),
    ("bandeau", 232, 78),
    ("bandeau", 344, 78),
    # --- la scene ---
    ("estrade", 288, 162),
    ("pupitre", 214, 172),
    ("tambour", 366, 174),
    # --- le bar du cafe : les deux comptoirs a auvent, de part et d'autre ---
    ("stand_gauche", 118, 200),
    ("stand_droit", 458, 200),
    # --- eclairage de scene ---
    ("lampadaire", 206, 152),
    ("lampadaire", 370, 152),
    ("torche", 92, 122),
    ("torche", 484, 122),
    # --- le public : deux rangees de bancs face a la scene ---
    ("banc", 190, 244),
    ("banc", 386, 244),
    ("banc", 178, 292),
    ("banc", 398, 292),
    # --- places d'honneur au centre, devant la scene ---
    ("fauteuil", 288, 248),
    ("tabouret", 244, 284),
    ("tabouret", 332, 284),
    # --- coin cafe : tables-souches et plantes de la variante caverne ---
    ("table_centre", 150, 300),
    ("coin_plantes_droit", 452, 304),
    # --- allee centrale ---
    ("tapis", 288, 330),
    ("cordon", 214, 316),
    ("cordon", 362, 316),
]

# Elements adosses au mur ou suspendus : pas d'ombre portee au sol, sinon on
# obtient une flaque sombre en plein milieu de la piece.
SANS_OMBRE = {"bandeau", "rideau", "torche", "tapis", "guirlande"}

OMBRE_FACTEUR = 0.72
OMBRE_LARGEUR = 0.34
OMBRE_HAUTEUR = 0.26


def decouper(chemin: Path, noms: list[str] | None = None,
             seuil: int = 120, par_taille: bool = False) -> dict[str, Image.Image]:
    """Isole chaque objet de la planche par composante connexe."""
    noms = noms if noms is not None else NOMS
    a = np.array(Image.open(chemin).convert("RGBA"))
    m = a[..., 3] > 0
    H, W = m.shape
    seen = np.zeros_like(m)
    boites = []
    aires: dict[tuple[int, int], int] = {}
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
                    boites.append((min(xs), min(ys), max(xs), max(ys)))
                    aires[(min(xs), min(ys))] = len(pts)
    if par_taille:
        # tri par nombre de pixels reels, pas par aire de boite englobante :
        # une guirlande large et plate a une grande boite mais peu de matiere.
        boites.sort(key=lambda b: -aires[(b[0], b[1])])
    else:
        boites.sort(key=lambda b: (b[1] // 40, b[0]))
    objets = {}
    for nom, (x0, y0, x1, y1) in zip(noms, boites):
        objets[nom] = Image.fromarray(a[y0:y1 + 1, x0:x1 + 1], "RGBA")
    # Le banc est genere dossier vers le fond : le public tournerait le dos a
    # la scene. On le retourne pour qu'il regarde l'estrade.
    if "banc" in objets:
        objets["banc"] = ImageOps.flip(objets["banc"])
    return objets


def poser_ombre(base: np.ndarray, cx: int, bas: int, larg: int) -> None:
    """Assombrit le sol sous l'objet, sans ajouter de pixel semi-transparent."""
    rw = max(3, int(larg * OMBRE_LARGEUR))
    rh = max(2, int(rw * OMBRE_HAUTEUR / OMBRE_LARGEUR * 0.8))
    cy = bas - 1
    H, W = base.shape[:2]
    for y in range(max(0, cy - rh), min(H, cy + rh + 1)):
        for x in range(max(0, cx - rw), min(W, cx + rw + 1)):
            if base[y, x, 3] == 0:
                continue
            dx = (x - cx) / rw
            dy = (y - cy) / rh
            if dx * dx + dy * dy <= 1.0:
                base[y, x, :3] = (base[y, x, :3].astype(float) * OMBRE_FACTEUR).astype(np.uint8)


def composer(moment: str, objets: dict[str, Image.Image]) -> None:
    salle = Image.open(SALLE / f"sous_sol_sans_deco_{moment}.png").convert("RGBA")
    base = np.array(salle).copy()

    # 1. les ombres, dans le sol lui-meme
    for nom, cx, bas in PLAN:
        im = objets.get(nom)
        if im is None or nom in SANS_OMBRE:
            continue
        poser_ombre(base, cx, bas, im.size[0])

    avec = Image.fromarray(base, "RGBA")
    avant_ombres = np.array(salle)

    # 2. les objets, tries par y croissant pour que l'occlusion soit correcte
    for nom, cx, bas in sorted(PLAN, key=lambda p: p[2]):
        im = objets.get(nom)
        if im is None:
            continue
        w, h = im.size
        avec.alpha_composite(im, (cx - w // 2, bas - h))

    # 3. le calque de deco seule = tout ce qui differe de la salle nue
    apres = np.array(avec)
    diff = (np.abs(apres[..., :3].astype(int) - avant_ombres[..., :3].astype(int)).sum(2) > 0)
    diff |= (apres[..., 3] > 0) & (avant_ombres[..., 3] == 0)
    deco = np.zeros_like(apres)
    deco[diff] = apres[diff]
    deco[..., 3] = np.where(diff, 255, 0)

    Image.fromarray(deco, "RGBA").save(SALLE / f"sous_sol_deco_seule_{moment}.png")
    avec.save(SALLE / f"sous_sol_avec_deco_{moment}.png")

    al = apres[..., 3]
    semi = int(((al > 0) & (al < 255)).sum())
    ys, xs = np.nonzero(al > 0)
    couleurs = len(np.unique(apres[al > 0][:, :3], axis=0))
    print(f"  {moment:5s} -> {len(PLAN)} elements  couleurs {couleurs}"
          f"  semi {semi}  bbox ({xs.min()}, {ys.min()}, {xs.max()}, {ys.max()})")


def main() -> None:
    objets = decouper(PLANCHE)
    objets.update(decouper(PLANCHE_CAFE, NOMS_CAFE, seuil=200, par_taille=True))
    print(f"{len(objets)} elements decoupes "
          f"({len(NOMS)} de scene + {len(NOMS_CAFE)} du cafe caverne)\n")
    manquants = {n for n, _, _ in PLAN} - set(objets)
    if manquants:
        print(f"  ATTENTION, absents de la planche : {sorted(manquants)}")
    for moment in ("jour", "nuit"):
        composer(moment, objets)


if __name__ == "__main__":
    main()
