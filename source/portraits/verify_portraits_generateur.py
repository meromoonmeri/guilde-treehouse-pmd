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
1. **Le fond est canonique au pixel près** : tout pixel portant une teinte de fond doit être
   exactement celui qu'un fond canonique reconstruit y placerait. C'est le point qui avait été
   signalé comme faux à plusieurs reprises ; il est maintenant mesuré, pas supposé.
2. **Aucun résidu du décor d'origine** : le générateur reprend le ciel du `Normal` qu'on lui
   donne. Si une seule teinte de ce décor subsiste dans l'image finale, le découpage a laissé
   passer quelque chose — c'était le cas des poches enfermées entre les oreilles de Capidextre.
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
    teintes_decor = decor_du_portrait(officiel)
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

        # --- couche 1 : le fond est canonique au pixel près ------------------------
        ciel, sol = BACKGROUNDS[nom]
        ref = fond_pur(nom)
        est_fond = np.all(a[:, :, :3] == ciel, axis=2) | np.all(a[:, :, :3] == sol, axis=2)
        fail(est_fond.any(), f"#{num} {nom} le fond canonique est présent", log)
        fail(bool((a[:, :, :3][est_fond] == ref[est_fond]).all()),
             f"#{num} {nom} fond canonique exact ({int(est_fond.sum())} pixels)", log)

        # --- couche 2 : aucun résidu du décor d'origine -----------------------------
        residu = 0
        for couleur in teintes_decor:
            residu += int(np.all(a[:, :, :3] == couleur, axis=2).sum())
        fail(residu == 0,
             f"#{num} {nom} aucun résidu du décor d'origine ({residu} pixels)", log)

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
