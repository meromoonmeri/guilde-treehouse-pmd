from __future__ import annotations

"""Pipeline qui rend une generation d'image compatible pixel-art PMDO.

Voir `AUDIT_PIPELINE_SPRITE.md` pour l'audit complet qui motive chaque etape.
Resume du diagnostic : le defaut des interieurs et du decor n'est pas le
detourage ni le nombre de couleurs, c'est la **frequence spatiale du detail**.
Le generateur peint des motifs plus fins que le pixel cible ; une reduction a
facteur non entier les transforme en bruit, d'ou la perte de qualite en jeu.

Les quatre etapes, dans l'ordre :

  1. CADRAGE ENTIER   — la generation est ramenee a exactement K x la taille
     cible, puis reduite par blocs K x K. Le facteur de reduction devient
     entier : la grille de pixels de sortie est exacte, plus aucun pixel
     n'est a cheval sur deux blocs source.
  2. PALETTE D'ASSET  — chaque couleur est projetee sur la palette reellement
     extraite des tilesets du jeu. Le decor generé cesse d'avoir sa propre
     gamme et se fond avec les meubles extraits.
  3. NETTOYAGE        — les pixels orphelins (aucun voisin de meme couleur)
     sont absorbes par leur voisinage : c'est le bruit de reduction.
  4. CONTROLE         — mesure des metriques PMDO et refus si hors norme.

Usage :
    python3 pipeline_sprite_pmdo.py <source.png> <largeur_cible> [--palette ref.png]
"""

from collections import Counter
from pathlib import Path
import argparse
import sys

import numpy as np
from PIL import Image

TILE = 8

# Facteur de suréchantillonnage interne. 4 est le meilleur compromis mesure :
# assez grand pour que le vote de couleur soit stable, assez petit pour ne pas
# lisser les details volontaires.
K = 4

RACINE = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# 1. Cadrage entier
# --------------------------------------------------------------------------

def reduire_blocs(a: np.ndarray, k: int) -> np.ndarray:
    """Reduit d'un facteur ENTIER k en votant la couleur dominante par bloc.

    On vote sur la couleur exacte plutot que de moyenner : moyenner cree des
    teintes intermediaires qui n'existent dans aucune palette d'asset et fait
    exploser le nombre de couleurs par tuile.
    """
    h, w = a.shape[:2]
    hh, hw = h // k, w // k
    out = np.zeros((hh, hw, 4), dtype=np.uint8)
    for y in range(hh):
        for x in range(hw):
            bloc = a[y * k:(y + 1) * k, x * k:(x + 1) * k].reshape(-1, 4)
            opaques = [tuple(int(v) for v in p) for p in bloc if p[3] > 127]
            if len(opaques) * 2 < len(bloc):
                continue
            r, g, b, _ = Counter(opaques).most_common(1)[0][0]
            out[y, x] = (r, g, b, 255)
    return out


def decontaminer(a: np.ndarray) -> np.ndarray:
    """Rend transparents les pixels teintes par le fond magenta.

    Le generateur anti-aliase le sujet contre son fond : la frange qui en
    resulte est un melange sujet/magenta. Si on la garde, le vote de bloc la
    propage et la projection sur palette la transforme en liseré sombre autour
    de chaque objet. On la retire AVANT le vote : le contour redevient franc.
    """
    out = a.copy()
    rgb = out[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Teinte magenta residuelle : rouge et bleu simultanement au-dessus du vert.
    frange = ((r - g) > 28) & ((b - g) > 28) & (out[..., 3] > 0)
    out[frange, 3] = 0
    return out


def cadrage_entier(img: Image.Image, cible_w: int, cible_h: int | None = None) -> np.ndarray:
    """Amene l'image a la taille cible avec un facteur de reduction ENTIER."""
    if cible_h is None:
        cible_h = round(img.size[1] * cible_w / img.size[0])
    # On passe d'abord par exactement K x la cible. Ce redimensionnement-la
    # peut etre lisse : il travaille encore dans le domaine continu du rendu.
    inter = img.resize((cible_w * K, cible_h * K), Image.LANCZOS)
    return reduire_blocs(decontaminer(np.array(inter.convert("RGBA"))), K)


# --------------------------------------------------------------------------
# 2. Palette d'asset
# --------------------------------------------------------------------------

def palette_depuis(chemins: list[Path], maxi: int = 256) -> np.ndarray:
    """Collecte la palette des vrais assets, ponderee par frequence d'usage."""
    compte: Counter = Counter()
    for c in chemins:
        if not c.exists():
            continue
        a = np.array(Image.open(c).convert("RGBA"))
        px = a[a[..., 3] > 127][:, :3]
        compte.update(tuple(int(v) for v in p) for p in px)
    return np.array([c for c, _ in compte.most_common(maxi)], dtype=int)


def projeter_palette(a: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Projette chaque couleur sur la plus proche de la palette d'asset.

    La distance est calculee en ponderant les canaux comme l'oeil les percoit
    (2,4,3) : une derive de vert se voit plus qu'une derive de bleu.
    """
    if len(palette) == 0:
        return a
    out = a.copy()
    m = a[..., 3] > 0
    cols, inv = np.unique(a[m][:, :3].astype(int), axis=0, return_inverse=True)
    poids = np.array([2, 4, 3])
    d = (((cols[:, None, :] - palette[None, :, :]) ** 2) * poids).sum(2)
    table = palette[d.argmin(1)]
    out[m, :3] = table[inv]
    return out


# --------------------------------------------------------------------------
# 3. Nettoyage des orphelins
# --------------------------------------------------------------------------

def voisins_identiques(a: np.ndarray) -> np.ndarray:
    rgb = a[..., :3].astype(int)
    m = a[..., 3] > 0
    n = np.zeros(m.shape, int)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        sh = np.roll(np.roll(rgb, dy, 0), dx, 1)
        shm = np.roll(np.roll(m, dy, 0), dx, 1)
        n += ((np.abs(rgb - sh).sum(2) == 0) & shm).astype(int)
    return n


def nettoyer_orphelins(a: np.ndarray, passes: int = 2) -> np.ndarray:
    """Remplace les pixels sans aucun voisin de meme couleur par la couleur
    dominante de leur voisinage 3x3. Ce sont les residus de reduction, pas du
    detail voulu : un vrai pixel-art n'isole presque jamais un pixel."""
    out = a.copy()
    for _ in range(passes):
        n = voisins_identiques(out)
        m = out[..., 3] > 0
        cibles = np.argwhere((n == 0) & m)
        if len(cibles) == 0:
            break
        h, w = m.shape
        for y, x in cibles:
            vois = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and out[ny, nx, 3] > 0:
                        vois.append(tuple(int(v) for v in out[ny, nx, :3]))
            if vois:
                out[y, x, :3] = Counter(vois).most_common(1)[0][0]
    return out


# --------------------------------------------------------------------------
# 4. Controle qualite
# --------------------------------------------------------------------------

def controler(a: np.ndarray, label: str = "") -> dict:
    al = a[..., 3]
    m = al > 0
    h, w = al.shape
    semi = int(((al > 0) & (al < 255)).sum())
    couleurs = len(np.unique(a[m][:, :3], axis=0))
    tuiles = []
    for ty in range(0, h, TILE):
        for tx in range(0, w, TILE):
            t = a[ty:ty + TILE, tx:tx + TILE].reshape(-1, 4)
            c = {tuple(int(v) for v in p[:3]) for p in t if p[3] > 0}
            if c:
                tuiles.append(len(c))
    tuiles = np.array(tuiles) if tuiles else np.array([0])
    n = voisins_identiques(a)
    orph = float((n[m] == 0).mean() * 100) if m.any() else 0.0
    aplats = float((n[m] == 4).mean() * 100) if m.any() else 0.0

    res = {
        "taille": f"{w}x{h}",
        "grille_8px": (w % TILE == 0 and h % TILE == 0),
        "couleurs": couleurs,
        "moy_par_tuile": round(float(tuiles.mean()), 1),
        "max_par_tuile": int(tuiles.max()),
        "pct_tuiles_conformes": round(float((tuiles <= 16).mean() * 100), 1),
        "semi_transparents": semi,
        "pct_orphelins": round(orph, 1),
        "pct_aplats": round(aplats, 1),
    }
    if label:
        print(f"  {label:<26}"
              f"{res['taille']:>10}"
              f"{res['couleurs']:>8}"
              f"{res['moy_par_tuile']:>9}"
              f"{res['pct_tuiles_conformes']:>8}%"
              f"{res['semi_transparents']:>7}"
              f"{res['pct_orphelins']:>9}%"
              f"{res['pct_aplats']:>9}%")
    return res


def entete() -> None:
    print(f"  {'etape':<26}{'taille':>10}{'coul':>8}{'moy/tui':>9}{'<=16':>9}"
          f"{'semi':>7}{'orphel':>10}{'aplats':>10}")
    print("  " + "-" * 89)


# --------------------------------------------------------------------------

def traiter(src: Path, cible_w: int, palette: np.ndarray, sortie: Path) -> dict:
    img = Image.open(src).convert("RGBA")
    print(f"\n{src.name} -> {sortie.name}  (source {img.size[0]}x{img.size[1]})")
    entete()
    controler(np.array(img), "0. source brute")

    a = cadrage_entier(img, cible_w)
    controler(a, "1. cadrage entier")

    a = projeter_palette(a, palette)
    controler(a, "2. palette d'asset")

    a = nettoyer_orphelins(a)
    res = controler(a, "3. nettoyage orphelins")

    Image.fromarray(a, "RGBA").save(sortie)
    return res


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("largeur", type=int)
    p.add_argument("--sortie", default=None)
    p.add_argument("--palette", nargs="*", default=None)
    args = p.parse_args()

    refs = [Path(x) for x in args.palette] if args.palette else [
        RACINE / "interieur" / "reference" / "spinda_cafe_officiel_pmd_sky.png",
        RACINE / "interieur" / "reference" / "metano_cafe_interieur_halcyon.png",
    ]
    palette = palette_depuis(refs)
    print(f"palette d'asset : {len(palette)} couleurs, depuis {len(refs)} reference(s)")

    src = Path(args.source)
    sortie = Path(args.sortie) if args.sortie else src.with_name(src.stem + "_pmdo.png")
    traiter(src, args.largeur, palette, sortie)


if __name__ == "__main__":
    main()
