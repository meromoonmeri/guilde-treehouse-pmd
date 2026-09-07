#!/usr/bin/env python3
"""Relecture indépendante des portraits produits par le **générateur d'images**.

Ces portraits sont construits en deux couches : un fond canonique reconstruit par code, et un
personnage découpé dans la sortie du générateur puis posé par-dessus. Le contrôle vérifie les
deux séparément, parce que ce sont deux sources de confiance très différentes.

Format SpriteCollab
- 40 × 40, RGBA entièrement opaque ;
- 15 couleurs au plus ;
- pour les portraits **générés**, palette incluse dans celle du `Normal` officiel — aucune
  couleur inventée par le générateur ne survit. Les portraits déjà publiés gardent la leur,
  qui est celle de leur auteur ;
- version `^` miroir horizontal exact ;
- planche 200 × 320 (5 × 8 cases), ordre officiel, cases `Special` vides.

Les deux couches
1. **Hors de la silhouette, TOUT est le fond canonique** — pixel par pixel, sans exception.
   Le contrôle parcourt la zone située hors du masque de silhouette du portrait officiel et
   exige que chaque pixel soit exactement celui qu'un fond canonique reconstruit y placerait.

   La version précédente de ce test ne vérifiait que les pixels **déjà** aux couleurs
   canoniques : elle était circulaire et validait des images où des bouts de personnage
   (saumon, orange) traînaient dans les coins. C'est le défaut que l'utilisateur a vu et que
   le contrôle ne voyait pas. Il faut partir de la **position**, jamais de la couleur.

2. **Aucune teinte de décor ne subsiste dans la silhouette** : le générateur peint parfois son
   propre ciel *à l'intérieur* du personnage (entre les oreilles de Capidextre, sur les épaules
   de Hariyama). Ces pixels-là ne sont pas rattrapables par la position — il faut les repérer
   par la couleur. Les deux critères sont donc nécessaires, chacun traitant ce que l'autre
   laisse passer.

3. **Les émotions officielles sont reprises à l'identique**, octet pour octet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from build_portraits_manquants import BACKGROUNDS, SIZE, load        # noqa: E402
from build_portraits_manquants import background_mask                # noqa: E402
from portraits_generateur import (                                    # noqa: E402
    ORDRE, REF, RETENUES, SUJETS, decor_du_portrait, fond_pur,
)

MAX_COLOURS = 15


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def controler(num: str) -> dict:
    dossier, label, _ = SUJETS[num]
    out = ROOT / "portraits" / dossier / "emotions_officielles"
    log: list[str] = []
    officiel = load(REF / num / "Normal.png")
    palette_off = {tuple(int(v) for v in c) for c in officiel.reshape(-1, 3)}
    perso_officiel = ~background_mask(officiel)
    publiees = {p.stem for p in (REF / num).glob("*.png")}

    presentes = sorted(p.stem for p in out.glob("*.png")
                       if not p.stem.endswith("^") and p.stem in ORDRE)
    fail(bool(presentes), f"#{num} des portraits sont produits", log)

    for nom in presentes:
        img = Image.open(out / f"{nom}.png")
        a = np.array(img)
        fail(img.size == (SIZE, SIZE), f"#{num} {nom} en {SIZE} × {SIZE}", log)
        fail(img.mode == "RGBA" and (a[:, :, 3] == 255).all(),
             f"#{num} {nom} entièrement opaque", log)
        couleurs = {tuple(int(v) for v in c) for c in a[:, :, :3].reshape(-1, 3)}
        fail(len(couleurs) <= MAX_COLOURS, f"#{num} {nom} {len(couleurs)} couleurs ≤ {MAX_COLOURS}", log)
        flip = np.array(Image.open(out / f"{nom}^.png"))
        fail(np.array_equal(flip, a[:, ::-1]), f"#{num} {nom}^ miroir exact", log)

        if nom in publiees:
            # portrait déjà publié : repris tel quel, avec la palette de son auteur
            fail(np.array_equal(a[:, :, :3], load(REF / num / f"{nom}.png")),
                 f"#{num} {nom} repris à l'identique du portrait officiel", log)
            continue

        # portrait généré : sa palette doit tenir dans celle du Normal officiel, augmentée des
        # deux teintes canoniques du fond de l'émotion (que le Normal n'a évidemment pas).
        admises = palette_off | set(BACKGROUNDS[nom])
        fail(couleurs <= admises,
             f"#{num} {nom} palette fermée : aucune couleur du générateur n'a survécu", log)

        # --- couche 1 : hors de la silhouette, tout est le fond canonique -----------
        # Contrôle par la POSITION, pas par la couleur : on compare chaque pixel hors du
        # masque de silhouette à ce qu'un fond canonique y placerait. Un seul écart = échec.
        ref = fond_pur(nom)
        hors = ~perso_officiel
        ecarts = int((~(a[:, :, :3][hors] == ref[hors]).all(axis=1)).sum())
        fail(ecarts == 0,
             f"#{num} {nom} : les {int(hors.sum())} pixels hors silhouette sont tous le fond "
             f"canonique ({ecarts} écart(s))", log)

        # --- couche 2 : pas de décor resté dans la silhouette -----------------------
        residu = 0
        for couleur in decor_du_portrait(officiel):
            residu += int(np.all(a[:, :, :3] == couleur, axis=2).sum())
        fail(residu == 0,
             f"#{num} {nom} : aucune teinte de décor d'origine dans la silhouette "
             f"({residu} pixel(s))", log)

        fail(not np.array_equal(a[:, :, :3], officiel),
             f"#{num} {nom} diffère bien du portrait Normal", log)

    # --- planche SpriteBot ---------------------------------------------------------
    planche = np.array(Image.open(out / "planche_spritebot.png"))
    fail(planche.shape == (8 * SIZE, 5 * SIZE, 4), f"#{num} planche 200 × 320", log)
    for i, nom in enumerate(ORDRE):
        cx, cy = (i % 5) * SIZE, (i // 5) * SIZE
        case = planche[cy:cy + SIZE, cx:cx + SIZE]
        if nom.startswith("Special") or nom not in presentes:
            fail((case[:, :, 3] == 0).all(), f"#{num} planche : case {nom} vide", log)
            continue
        haut = np.array(Image.open(out / f"{nom}.png"))
        fail(np.array_equal(case[:, :, :3], haut[:, :, :3]),
             f"#{num} planche : {nom} à sa place", log)
        bas = planche[4 * SIZE + cy:4 * SIZE + cy + SIZE, cx:cx + SIZE]
        fail(np.array_equal(bas[:, :, :3], haut[:, ::-1, :3]),
             f"#{num} planche : {nom}^ à sa place", log)

    fail((out / "credits.txt").is_file(), f"#{num} credits.txt écrit", log)

    generees = [n for n in presentes if n not in publiees]
    rapport = {"pokemon": f"{label} #{num}", "controles": len(log), "echecs": 0,
               "portraits": len(presentes), "officiels_repris": sorted(set(presentes) & publiees),
               "generes": generees, "retenues": RETENUES.get(num, []), "journal": log}
    (out / "controle_qualite.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    return rapport


def main() -> None:
    for num in SUJETS:
        r = controler(num)
        print(f"{r['pokemon']:26s} {r['controles']:3d} contrôles, {r['portraits']} portraits "
              f"({len(r['officiels_repris'])} officiels repris, {len(r['generes'])} générés) "
              f"— fond canonique exact")


if __name__ == "__main__":
    main()
