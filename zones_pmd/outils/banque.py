"""
banque.py — extraction de banques de tuiles depuis les cartes PMD d'origine.

Les rendus de PMD Sky sont de vraies tilemaps alignées sur 24 px : les 257
cartes examinées le sont sans exception. On peut donc en extraire les tuiles
telles quelles, au lieu d'imiter leur style.

Le point délicat n'est pas d'extraire les tuiles mais de savoir **laquelle
poser où**. La méthode retenue apprend l'autotuilage directement des cartes :

1. dans une carte source, les tuiles très répétées sont le sol ;
2. on en déduit un masque sol / mur pour toute la carte ;
3. pour chaque case, on calcule la signature de son voisinage sur 8 bits ;
4. les tuiles sont rangées par signature.

Pour bâtir une salle neuve, on calcule la même signature sur le plan voulu et
on tire une tuile de la banque correspondante. Le résultat reprend donc les
transitions exactes du jeu — coins, lisières, angles rentrants — sans avoir à
les décrire à la main.
"""

import os
import json
import glob
import numpy as np
from PIL import Image
from collections import Counter, defaultdict

T = 24
SRC = os.environ.get("PMD_PREVIEWS", "/home/user/sky_port/output/Previews")

# les huit voisins, dans l'ordre des bits de la signature
VOISINS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def decouper(chemin):
    """Renvoie la grille de tuiles d'une carte, ou None si non alignée."""
    im = Image.open(chemin).convert("RGB")
    w, h = im.size
    if w % T or h % T or w < T * 6 or h < T * 6:
        return None, None
    cols, lignes = w // T, h // T
    grille = [[im.crop((x * T, y * T, x * T + T, y * T + T))
               for x in range(cols)] for y in range(lignes)]
    return grille, (cols, lignes)


def _cle(t):
    return t.tobytes()


def masque_sol(grille, cols, lignes, couverture=0.16):
    """
    Repère le sol par classement de fréquence plutôt que par seuil absolu.

    On trie les tuiles non noires par nombre d'occurrences et on retient les
    plus fréquentes jusqu'à couvrir une fraction donnée de la carte. Un seuil
    fixe échouait sur les cartes à sol très varié, où aucune tuile seule
    n'atteignait le quota : la banque ressortait vide.
    """
    freq = Counter()
    infos = {}
    for y in range(lignes):
        for x in range(cols):
            k = _cle(grille[y][x])
            freq[k] += 1
            if k not in infos:
                a = np.frombuffer(k, dtype=np.uint8).reshape(T, T, 3).astype(np.float32)
                infos[k] = (a.mean(), a.std())
    total = cols * lignes
    candidats = [(n, k) for k, n in freq.items()
                 if infos[k][0] >= 12 and infos[k][1] <= 70]
    candidats.sort(reverse=True)
    sols, cumul = set(), 0
    for n, k in candidats:
        if cumul >= couverture * total and n < 3:
            break
        sols.add(k)
        cumul += n
        if cumul >= 0.55 * total:
            break
    m = np.zeros((lignes, cols), dtype=bool)
    for y in range(lignes):
        for x in range(cols):
            m[y, x] = _cle(grille[y][x]) in sols
    return m, freq


def signature(m, x, y, cols, lignes):
    """Code 8 bits du voisinage : 1 = voisin mur (ou hors carte)."""
    s = 0
    for i, (dx, dy) in enumerate(VOISINS):
        nx, ny = x + dx, y + dy
        mur = True
        if 0 <= nx < cols and 0 <= ny < lignes:
            mur = not m[ny, nx]
        s |= (1 << i) if mur else 0
    return s


def construire(cartes, max_par_signature=12):
    """
    Banque à trois rôles, apprise sur les cartes fournies :

      sol    tuiles praticables, avec leur fréquence d'origine
      corps  tuiles de mur dont les huit voisins sont aussi du mur
      bord   tuiles de mur en lisière, rangées par signature de voisinage

    Séparer le corps de la lisière est indispensable. Un premier essai les
    mélangeait dans un même sac « mur » : les tuiles de transition, dessinées
    pour un contexte précis, se retrouvaient posées au milieu de la masse et
    la salle devenait illisible.
    """
    sol = []
    vus_sol = set()
    corps = []
    vus_corps = set()
    bord = defaultdict(list)
    vus_bord = defaultdict(set)
    props = []
    vus_props = set()
    n_cartes = 0

    for p in cartes:
        grille, dim = decouper(p)
        if grille is None:
            continue
        cols, lignes = dim
        m, freq = masque_sol(grille, cols, lignes)
        if m.mean() < 0.04 or m.mean() > 0.97:
            continue
        n_cartes += 1
        for y in range(lignes):
            for x in range(cols):
                t = grille[y][x]
                k = _cle(t)
                a = np.frombuffer(k, dtype=np.uint8).reshape(T, T, 3).astype(np.float32)
                if a.mean() < 10:
                    continue
                sg = signature(m, x, y, cols, lignes)
                if m[y, x]:
                    if k not in vus_sol:
                        vus_sol.add(k)
                        sol.append((t, freq[k]))
                elif sg == 255:
                    if k not in vus_corps:
                        vus_corps.add(k)
                        corps.append((t, freq[k]))
                elif sg == 0:
                    if k not in vus_props:
                        vus_props.add(k)
                        props.append(t)
                else:
                    if k in vus_bord[sg] or len(bord[sg]) >= max_par_signature:
                        continue
                    vus_bord[sg].add(k)
                    bord[sg].append((t, freq[k]))
    return {"sol": sol, "corps": corps, "bord": bord, "props": props}, n_cartes


def _tirer_pondere(lot, rng, variete=0.35):
    if not lot:
        return None
    poids = np.array([max(1, p) for _, p in lot], dtype=np.float64) ** (1.0 - variete)
    poids /= poids.sum()
    return lot[int(rng.choice(len(lot), p=poids))][0]


def tirer(banque, est_sol, sg, rng, variete=0.35):
    """Tuile adaptée au rôle et au voisinage, avec repli sur le plus proche."""
    if est_sol:
        return _tirer_pondere(banque["sol"], rng, variete)
    if sg == 255:
        return (_tirer_pondere(banque["corps"], rng, variete)
                or _tirer_pondere(banque["sol"], rng, variete))
    b = banque["bord"]
    if sg in b and b[sg]:
        return _tirer_pondere(b[sg], rng, variete)
    dispo = [s for s in b if b[s]]
    if dispo:
        best = min(dispo, key=lambda s: bin(s ^ sg).count("1"))
        return _tirer_pondere(b[best], rng, variete)
    return (_tirer_pondere(banque["corps"], rng, variete)
            or _tirer_pondere(banque["sol"], rng, variete))


def resume(banque):
    return {"sol": len(banque["sol"]), "corps": len(banque["corps"]),
            "bord_signatures": len(banque["bord"]),
            "bord_tuiles": sum(len(v) for v in banque["bord"].values()),
            "props": len(banque["props"])}


def grouper_par_donjon(cartes):
    """Regroupe les cartes par donjon d'après leur nom (d54p31a -> d54)."""
    import re
    g = defaultdict(list)
    for p in cartes:
        n = os.path.basename(p)[:-4]
        m = re.match(r"^([a-z]+\d+)", n)
        g[m.group(1) if m else n].append(p)
    return g


def cartes_alignees(dossier=None, mini=8):
    """Liste des cartes exploitables : alignées sur 24 px et assez grandes."""
    d = dossier or SRC
    out = []
    for p in sorted(glob.glob(os.path.join(d, "*.png"))):
        try:
            w, h = Image.open(p).size
        except Exception:
            continue
        if w % T == 0 and h % T == 0 and w // T >= mini and h // T >= mini:
            out.append(p)
    return out


def dominance_sol(cartes):
    """
    Part de la carte occupée par sa tuile de sol la plus fréquente.

    C'est le meilleur discriminant entre une vraie tilemap de donjon, où une
    dalle domine largement, et un décor de scène ou de village, qui est une
    illustration unique. Sans ce filtre, les cartes les plus fournies du lot
    sont justement les décors, et les salles produites virent au patchwork.
    """
    best = 0.0
    for p in cartes:
        grille, dim = decouper(p)
        if grille is None:
            continue
        cols, lignes = dim
        freq = Counter()
        for y in range(lignes):
            for x in range(cols):
                k = _cle(grille[y][x])
                a = np.frombuffer(k, dtype=np.uint8).reshape(T, T, 3)
                if a.mean() < 12:
                    continue
                freq[k] += 1
        if freq:
            best = max(best, freq.most_common(1)[0][1] / (cols * lignes))
    return best
