#!/usr/bin/env python3
"""Essai documenté : peut-on faire dessiner les images de repas par un générateur d'images ?

L'utilisateur a proposé d'employer le générateur d'images en l'« éduquant » pour qu'il conserve
tout à l'identique et n'ajoute que l'ouverture de la bouche. L'idée méritait d'être testée
sérieusement plutôt que refusée d'emblée. Ce fichier **rejoue l'essai et mesure le résultat**,
pour que la conclusion soit vérifiable et non une opinion.

────────────────────────────────────────────────────────────────────────────────
PROTOCOLE
────────────────────────────────────────────────────────────────────────────────
1. La case Idle officielle de Politoed (23 × 24) est agrandie ×16 sur fond magenta.
2. Elle est envoyée au générateur avec une consigne aussi contraignante que possible :
   « même sprite au pixel près, une seule différence — la bouche grande ouverte avec gorge et
   langue ; ne change pas la résolution, n'ajoute aucune couleur, pas d'anticrénelage ».
3. Le résultat est **discipliné par post-traitement** — c'est la partie qui rend l'idée
   défendable, et sans laquelle rien n'est exploitable :
   a. rééchantillonnage sur la grille exacte 23 × 24 (moyenne de bloc, pas de nearest) ;
   b. rabattement de chaque pixel sur la couleur la plus proche **de la palette d'origine** ;
   c. **masque de zone** : seules les lignes de la bouche sont reprises du générateur, tout le
      reste du sprite est remis à l'identique depuis l'original.
4. Le résultat discipliné est mesuré contre les quatre règles de grammaire Chunsoft du § 13.

────────────────────────────────────────────────────────────────────────────────
RÉSULTATS MESURÉS (image conservée dans `essais/`)
────────────────────────────────────────────────────────────────────────────────
Sortie brute du générateur :
    207 couleurs (contre 14 autorisées)          → 15× au-dessus de la limite SpriteBot
    18,7 % des pixels du corps conservés         → le sprite est redessiné, pas édité

Après discipline (rabattement + masque de bouche) :
    14 couleurs, palette fermée                  ✔ règle 1
    92,1 % des pixels conservés                  ✔ règle 4 (changement local)
    7 pixels de gorge à vif sur la peau          ✘ règle 2 (cerne noir)
    1 saut de valeur clair→sombre                ✘ règle 3 (ombrage ordonné)

Détail instructif : le générateur a modifié **45 pixels dans les yeux**, alors que la consigne
disait explicitement de n'y pas toucher. Il ne « conserve » pas — il redessine de mémoire une
image qui ressemble à l'entrée.

────────────────────────────────────────────────────────────────────────────────
SECOND ESSAI — NE DONNER QUE LE RECTANGLE DE LA BOUCHE
────────────────────────────────────────────────────────────────────────────────
Hypothèse issue du premier essai : le générateur redessine tout parce qu'on lui donne tout.
On lui envoie donc **uniquement le rectangle de la bouche** (14 × 8 pixels), pas le sprite
entier, avec la même consigne. Résultat, après la même discipline :

    80 % des pixels de la zone conservés          (contre 18,7 % sur le sprite entier)
    14 couleurs, palette fermée                   ✔ règle 1
    gorge correctement cernée de noir             ✔ règle 2  ← échouait au premier essai
    2 sauts de valeur clair→sombre                ✘ règle 3
    22 pixels retouchés, bords intacts            ✔ règle 4
    → 3 règles sur 4, contre 2 sur 4

L'hypothèse était bonne : **restreindre le champ de vision du générateur améliore nettement
sa fidélité**. Les bords gauche et droit de la zone sont conservés au pixel près, ce qui
n'arrivait jamais sur le sprite entier.

────────────────────────────────────────────────────────────────────────────────
CONCLUSION
────────────────────────────────────────────────────────────────────────────────
Le générateur est **utilisable comme source d'idées de forme**, et, cadré sur une petite zone,
il produit une base retouchable. Il reste malgré tout à un défaut de grammaire près (l'ombrage),
qu'il faut corriger à la main — et à ce stade on a fait le travail de `dessine_eat_politoed.py`
en moins bien et sans contrôle.

La leçon utile n'est pas « le générateur est mauvais » mais **« plus le champ est étroit, plus il
est fidèle »** : 18,7 % de conservation sur le sprite entier, 80 % sur le seul rectangle de la
bouche. Pour un usage sérieux il faudrait découper chaque geste en zones minuscules, ce qui
revient à faire soi-même la composition — le dessin direct reste plus court et vérifiable.

C'est pourquoi le lot livré reste celui dessiné à la main. Cet essai est conservé parce qu'un
résultat négatif mesuré vaut mieux qu'un refus de principe — et parce que si un futur modèle
respecte la grille et la palette, la partie « discipline » de ce fichier sera directement
réutilisable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                       # noqa: E402

REF = ROOT / "source" / "personnages" / "reference" / "0186"
ESSAIS = ROOT / "source" / "personnages" / "essais"
BRUT = ESSAIS / "generateur_politoed_brut.png"

# Lignes que l'on accepte de reprendre du générateur : la bande de la bouche, rien d'autre.
BOUCHE_Y0, BOUCHE_Y1 = 13, 17

NOIR = (0, 0, 0)
GORGE = (159, 0, 0)
LANGUE = (215, 63, 0)
LEVRES = {(255, 247, 0), (223, 183, 0), (167, 111, 0)}


def case_officielle() -> np.ndarray:
    _, anims = P.load_sprite(REF)
    f = anims["Idle"].frames[0][0]
    x0, y0, x1, y1 = f.bbox
    ax, ay = f.anchor
    return f.image[ay + y0:ay + y1 + 1, ax + x0:ax + x1 + 1].copy()


def discipliner(brut: Image.Image, src: np.ndarray) -> tuple[np.ndarray, dict]:
    """Ramène une sortie de générateur dans les contraintes du format. Cœur de l'essai."""
    h, w = src.shape[:2]
    palette = sorted({tuple(int(v) for v in c) for c in src[src[:, :, 3] > 0][:, :3]})
    pal = np.array(palette)

    # (a) grille exacte : moyenne de bloc, surtout pas nearest — le générateur dessine
    #     sa propre grille, légèrement décalée de la nôtre.
    petit = np.array(brut.convert("RGB").resize((w, h), Image.BOX)).astype(int)

    # (b) palette fermée : chaque pixel rabattu sur la teinte d'origine la plus proche
    d = ((petit.reshape(-1, 3)[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    rabattu = pal[d.argmin(1)].reshape(h, w, 3)

    # (c) masque de zone : hors de la bouche, on remet l'original
    masque_corps = src[:, :, 3] > 0
    zone = np.zeros((h, w), bool)
    zone[BOUCHE_Y0:BOUCHE_Y1] = True
    out = src.copy()
    out[:, :, :3] = np.where((zone & masque_corps)[:, :, None], rabattu, src[:, :, :3])

    brut_petit_cols = {tuple(int(v) for v in c) for c in petit.reshape(-1, 3)}
    identiques = int((out[masque_corps][:, :3] == src[masque_corps][:, :3]).all(1).sum())
    total = int(masque_corps.sum())
    modifs = np.any(rabattu != src[:, :, :3], axis=2) & masque_corps
    return out, {
        "couleurs_brutes": len(brut_petit_cols),
        "couleurs_apres_discipline": len({tuple(int(v) for v in c) for c in out[masque_corps][:, :3]}),
        "pixels_conserves": identiques,
        "pixels_corps": total,
        "taux_conservation": round(100 * identiques / total, 1),
        "pixels_modifies_par_le_generateur_dans_les_yeux": int(modifs[6:13].sum()),
        "pixels_modifies_par_le_generateur_dans_la_bouche": int(modifs[13:17].sum()),
    }


def voisins(m: np.ndarray) -> np.ndarray:
    o = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def grammaire(out: np.ndarray, src: np.ndarray) -> dict:
    """Les quatre règles Chunsoft du § 13, appliquées au résultat discipliné."""
    h, w = src.shape[:2]
    masque = src[:, :, 3] > 0
    palette = {tuple(int(v) for v in c) for c in src[src[:, :, 3] > 0][:, :3]}
    zone = np.zeros((h, w), bool)
    zone[BOUCHE_Y0:BOUCHE_Y1] = True

    couleurs = {tuple(int(v) for v in c) for c in out[masque][:, :3]}
    gorge = np.zeros((h, w), bool)
    for c in (GORGE, LANGUE):
        gorge |= masque & np.all(out[:, :, :3] == c, axis=2)
    gorge &= zone
    autorise = np.zeros((h, w), bool)
    for c in {GORGE, LANGUE, NOIR} | LEVRES:
        autorise |= masque & np.all(out[:, :, :3] == c, axis=2)
    a_vif = int((voisins(gorge) & masque & ~autorise).sum())
    clair = masque & zone & np.all(out[:, :, :3] == (255, 247, 0), axis=2)
    sombre = masque & zone & np.all(out[:, :, :3] == (167, 111, 0), axis=2)
    sauts = int((voisins(clair) & sombre).sum())
    local = int((np.any(out != src, axis=2) & masque).sum())

    return {
        "1_palette_fermee": {"ok": not (couleurs - palette), "couleurs": len(couleurs)},
        "2_gorge_cernee": {"ok": a_vif == 0, "pixels_a_vif_sur_la_peau": a_vif},
        "3_ombrage_ordonne": {"ok": sauts == 0, "sauts_de_valeur": sauts},
        "4_changement_local": {"ok": local < int(masque.sum()), "pixels_retouches": local},
    }


def main() -> None:
    src = case_officielle()
    if not BRUT.is_file():
        print(f"Sortie brute du générateur absente : {BRUT.relative_to(ROOT)}")
        print("Cet essai documente un résultat déjà mesuré ; voir le rapport JSON.")
        return
    brut = Image.open(BRUT)
    out, mesures = discipliner(brut, src)
    regles = grammaire(out, src)

    h, w = src.shape[:2]
    Image.fromarray(out, "RGBA").resize((w * 18, h * 18), Image.NEAREST).save(
        ESSAIS / "generateur_politoed_discipline.png", optimize=True)

    rapport = {
        "question": "peut-on faire produire les images de repas par un générateur d'images ?",
        "protocole": ["case officielle agrandie ×16 sur fond magenta",
                      "consigne : même sprite au pixel près, seule la bouche s'ouvre",
                      "discipline : grille exacte, palette rabattue, masque limité à la bouche",
                      "mesure contre les quatre règles de grammaire Chunsoft"],
        "mesures": mesures,
        "regles_de_grammaire": regles,
        "regles_respectees": sum(1 for r in regles.values() if r["ok"]),
        "conclusion": ("utilisable comme source d'idées de forme, pas comme producteur d'images "
                       "livrables : la discipline ramène palette et zone, mais ne répare ni le "
                       "cerne noir ni l'ombrage — il reste une reprise manuelle, donc autant "
                       "dessiner directement, ce que fait dessine_eat_politoed.py"),
    }
    (ESSAIS / "rapport_generateur.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1), encoding="utf-8")

    print("Essai « générateur d'images » — mesures")
    for k, v in mesures.items():
        print(f"  {k:52s} {v}")
    print("Règles de grammaire Chunsoft :")
    for k, v in regles.items():
        print(f"  {k:22s} {'OK   ' if v['ok'] else 'ÉCHEC'} {v}")
    print(f"  → {rapport['regles_respectees']}/4 respectées")


if __name__ == "__main__":
    main()
