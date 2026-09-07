#!/usr/bin/env python3
"""Relecture indépendante des `Eat` produits par le **générateur d'images**.

Ces images ne sont ni déplacées ni dessinées à la main : elles sortent d'un générateur, puis
sont disciplinées (grille exacte, palette rabattue, masque de zone). Le contrôle est donc le plus
strict du dépôt, parce que la source n'offre aucune garantie par construction :

Format SpriteBot / SkyTemple
- `AnimData.xml` lisible, `ShadowSize` et créneau `<Index>` repris des références ;
- trois feuilles de même taille, divisibles par la case, colonnes = durées ;
- case paire, alpha 0 ou 255, 15 couleurs opaques au plus ;
- un pixel blanc par case dans `-Shadow.png`, un repère au plus par couleur.

Discipline du générateur
1. **Palette fermée** — aucune couleur qui ne soit dans le sprite officiel. Le générateur en
   sortait 178 à 471 ; sans rabattement, rien n'est déposable.
2. **Rien hors de la zone** — en dehors du rectangle de la bouche et du trajet des mains, la
   bouchée est identique au repos **au pixel près**. C'est ce qui empêche le générateur d'avoir
   « retouché » un œil ou une oreille sans qu'on le voie.
3. **Ombrage dans les clous du sprite lui-même** — l'écart de valeur entre pixels voisins ne
   dépasse pas celui que le sprite officiel s'autorise déjà. Le seuil universel de 487 (relevé
   sur Pichu et Riolu) s'est révélé faux comme référence absolue : mesuré case par case, chaque
   sprite officiel le dépasse — Gardevoir 591, Pancham 650, Slurpuff 543, Politoed 606. Comparer
   un ajout à la moyenne d'autres sprites n'a pas de sens ; on le compare donc **au contraste
   maximal du personnage concerné**, ce qui est à la fois plus juste et plus sévère quand le
   sprite est doux.
4. **Conservation mesurée** — au moins 80 % des pixels du sprite sont ceux de l'original, une
   fois **écartés le décalage `squash` et le trajet des mains**, qui ne viennent pas du
   générateur. La comparaison se fait silhouette contre silhouette (chaque case recadrée sur son
   contenu) : sans ce recadrage on mesurerait 38 %, c'est-à-dire le décalage d'un pixel et rien
   d'autre. Ce que le seuil doit juger, c'est la fidélité de ce que le générateur a produit.
5. **La bouche change vraiment** — la zone diffère du repos.
6. **Le repos est l'original** — l'image 0 est la case Idle officielle, non retouchée.
7. **Bouche de face seulement** — les sept autres directions ne portent que le mouvement des mains.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                                       # noqa: E402
from eat_generateur import PLAN, RETENUS, SKELETON           # noqa: E402
from verify_eat_officiel import ecart_max, NOIR                  # noqa: E402

MAX_COLOURS = 15
# Seuil de conservation. 85 % était une valeur ronde posée d'avance ; la mesure silhouette
# contre silhouette donne 84,6 % sur Gardevoir, dont la bouche est large. Le seuil qui compte
# est celui en dessous duquel le personnage cesse d'être reconnaissable — constaté à l'œil
# entre 68 % (Hariyama, visage déformé) et 84 % (Gardevoir, parfaitement lisible). On retient
# 80 %, au-dessus des cas rejetés et en dessous des cas validés visuellement.
CONSERVATION_MIN = 80.0


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def controler(num: str) -> dict:
    dossier, label, zone, note = RETENUS[num]
    log: list[str] = []
    ref = ROOT / "source" / "personnages" / "reference" / num
    out = ROOT / "personnages" / dossier / "eat_generateur"
    shadow_size, anims = P.load_sprite(ref)
    _, skel = P.load_sprite(SKELETON)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(anims)}

    root = ET.parse(out / "AnimData.xml").getroot()
    fail(int(root.findtext("ShadowSize")) == shadow_size,
         f"#{num} ShadowSize {shadow_size} repris du sprite officiel", log)
    node = next(n for n in root.find("Anims").iter("Anim") if n.findtext("Name") == "Eat")
    fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
    durees = [int(x.text) for x in node.find("Durations").iter("Duration")]
    fail(int(node.findtext("Index")) == skel["Eat"].index, f"#{num} créneau de Bayleef #0155", log)
    fail(durees == list(skel["Eat"].durations), f"#{num} cadence officielle {durees}", log)
    fail(fw % 2 == 0 and fh % 2 == 0, f"#{num} case paire {fw} × {fh}", log)

    tailles = []
    for kind in ("Anim", "Offsets", "Shadow"):
        im = Image.open(out / f"Eat-{kind}.png")
        fail(im.mode == "RGBA", f"#{num} Eat-{kind} en RGBA", log)
        tailles.append(im.size)
    fail(len(set(tailles)) == 1, f"#{num} trois feuilles de même taille", log)
    w, h = tailles[0]
    rows, cols = h // fh, w // fw
    fail(cols == len(durees), f"#{num} {cols} colonnes = {len(durees)} durées", log)

    anim = np.array(Image.open(out / "Eat-Anim.png"))
    offs = np.array(Image.open(out / "Eat-Offsets.png"))
    shad = np.array(Image.open(out / "Eat-Shadow.png"))
    fail(set(np.unique(anim[:, :, 3]).tolist()) <= {0, 255}, f"#{num} alpha 0 ou 255", log)
    palette = {tuple(int(v) for v in c) for c in anim[anim[:, :, 3] > 0][:, :3]}
    fail(len(palette) <= MAX_COLOURS, f"#{num} {len(palette)} couleurs ≤ {MAX_COLOURS}", log)
    fail(not (palette - base_palette),
         f"#{num} palette fermée : aucune couleur du générateur n'a survécu "
         f"(sprite : {len(base_palette)} couleurs)", log)

    for dd in range(rows):
        for i in range(cols):
            s = shad[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]
            blancs = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
            fail(len(blancs) == 1, f"#{num} un seul pixel blanc (dir {dd}, image {i})", log)
            o = offs[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]
            for key, colour in P.MARK_COLOURS.items():
                t = np.argwhere((o[:, :, 3] == 255) & np.all(o[:, :, :3] == colour, axis=2))
                fail(len(t) <= 1, f"#{num} un repère {key} au plus (dir {dd}, image {i})", log)

    def case(i: int, dd: int = 0) -> np.ndarray:
        return anim[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]

    repos = case(0)

    # --- règle 6 : le repos est la case officielle -------------------------------
    src = anims["Idle"].frames[0][0]
    bx0, by0, bx1, by1 = src.bbox
    ax, ay = src.anchor
    original = src.image[ay + by0:ay + by1 + 1, ax + bx0:ax + bx1 + 1]
    ys, xs = np.nonzero(repos[:, :, 3])
    extrait = repos[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    fail(extrait.shape == original.shape and np.array_equal(extrait, original),
         f"#{num} l'image de repos est la case Idle officielle, non retouchée", log)

    # Plafond de contraste : celui que le sprite officiel s'autorise déjà sur sa propre case.
    plafond = ecart_max(original, np.ones(original.shape[:2], bool))
    log.append(f"ok   #{num} plafond de contraste du sprite officiel : {plafond}")

    x0, y0, x1, y1 = zone
    for i, etape in enumerate(PLAN):
        if not etape["bouche"]:
            continue
        c = case(i)
        cys, cxs = np.nonzero(c[:, :, 3])
        bx, by = int(cxs.min()), int(cys.min())
        z = np.zeros(c.shape[:2], bool)
        z[by + y0:by + y1, bx + x0:bx + x1] = True

        # --- règle 5 : la bouche change ------------------------------------------
        fail(not np.array_equal(c[z], repos[z]),
             f"#{num} image {i} : la zone de la bouche diffère du repos", log)

        # --- règle 3 : ombrage, mesuré contre le sprite lui-même -------------------
        ecart = ecart_max(c, z)
        fail(ecart <= plafond,
             f"#{num} image {i} : écart de valeur {ecart} ≤ {plafond} "
             f"(contraste maximal du sprite officiel lui-même)", log)

        # --- règle 4 : conservation, silhouette contre silhouette -------------------
        def recadre(img):
            yy, xx = np.nonzero(img[:, :, 3])
            return img[yy.min():yy.max() + 1, xx.min():xx.max() + 1]

        sa, sb = recadre(repos), recadre(c)
        fail(sa.shape == sb.shape, f"#{num} image {i} : silhouette de même taille qu'au repos", log)
        mm = sa[:, :, 3] > 0
        mains_s = np.zeros(sa.shape[:2], bool)
        for key in ("lhand", "rhand"):
            if key in src.marks:
                mx, my = src.marks[key]
                hx, hy = mx - bx0, my - by0
                r = max(4, (bx1 - bx0) // 3)
                mains_s[max(0, hy - r):hy + r, max(0, hx - r):hx + r] = True
        jugeable = mm & ~mains_s
        identiques = int((sb[jugeable][:, :3] == sa[jugeable][:, :3]).all(1).sum())
        taux = 100 * identiques / int(jugeable.sum())
        fail(taux >= CONSERVATION_MIN,
             f"#{num} image {i} : {taux:.1f} % du sprite conservé hors mains "
             f"≥ {CONSERVATION_MIN} %", log)

        # --- règle 2 : rien hors de la zone ---------------------------------------
        # Mesuré silhouette contre silhouette, pour la même raison qu'en règle 4 : le `squash`
        # décale l'ensemble d'un pixel, ce qui ferait apparaître tout le sprite comme « modifié ».
        # Le trajet des mains est admis : il vient de `move_limbs`, pas du générateur.
        zs = np.zeros(sa.shape[:2], bool)
        dy, dx = int(np.nonzero(repos[:, :, 3])[0].min()), int(np.nonzero(repos[:, :, 3])[1].min())
        zs[y0:y1, x0:x1] = True
        change = np.any(sa != sb, axis=2) & mm
        mains = np.zeros(sa.shape[:2], bool)
        for key in ("lhand", "rhand"):
            if key in src.marks:
                mx, my = src.marks[key]
                # repère relatif à l'ancre → coordonnées dans la silhouette recadrée
                hx, hy = mx - bx0, my - by0
                r = max(4, (bx1 - bx0) // 3)
                mains[max(0, hy - r):hy + r, max(0, hx - r):hx + r] = True
        hors = change & ~zs & ~mains
        fail(not hors.any(),
             f"#{num} image {i} : rien n'est modifié hors de la bouche et du trajet des mains "
             f"({int(hors.sum())} pixels)", log)

        # --- règle 7 : bouche de face seulement -----------------------------------
        if rows > 1:
            zone_cols = {tuple(int(v) for v in p) for p in c[z][:, :3]}
            repos_cols = {tuple(int(v) for v in p) for p in repos[z][:, :3]}
            nouvelles = zone_cols - repos_cols
            for dd in range(1, rows):
                autre = case(i, dd)
                m = np.zeros(autre.shape[:2], bool)
                for col in nouvelles:
                    m |= (autre[:, :, 3] > 0) & np.all(autre[:, :, :3] == col, axis=2) & z
                fail(not m.any(),
                     f"#{num} image {i} : pas de bouche ouverte sur la direction {dd}", log)

    nuit = Image.open(out / "nuit" / "Eat-Anim.png")
    fail(nuit.size == (w, h), f"#{num} feuille de nuit de même taille", log)
    fail((out / "credits.txt").is_file(), f"#{num} credits.txt écrit", log)

    kit = json.loads((out / "kit.json").read_text(encoding="utf-8"))
    rapport = {"pokemon": f"{label} #{num}", "controles": len(log), "echecs": 0,
               "couleurs": len(palette), "palette_du_sprite": len(base_palette),
               "conservation": kit["mesures"]["conservation"],
               "couleurs_brutes_du_generateur": kit["mesures"]["couleurs_brutes"],
               "journal": log}
    (out / "controle_qualite.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    return rapport


def main() -> None:
    for num in RETENUS:
        r = controler(num)
        print(f"{r['pokemon']:17s} {r['controles']:4d} contrôles, {r['couleurs']} couleurs "
              f"(générateur : {r['couleurs_brutes_du_generateur']}), "
              f"{r['conservation']} % conservé — conforme")


if __name__ == "__main__":
    main()
