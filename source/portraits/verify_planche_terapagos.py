#!/usr/bin/env python3
"""Contrôle de la planche à base verrouillée de Terapagos Terastal.

Le cahier des charges demandait une « fidélité 100 sur 100 » : une tête de base qui ne bouge pas
d'un pixel, un fond strictement identique, une palette figée, du vrai pixel art. Ce vérificateur
teste chacun de ces points **par comparaison directe avec la case Normal**, sans tolérance.

Chaque contrôle est chiffré, aucun n'est déclaratif :

1. **Format** — 40 × 40, RGBA opaque, 15 couleurs au plus.
2. **Base verrouillée** — hors de la boîte de l'œil, chaque expression est identique à `Normal`
   **octet pour octet**. C'est le contrôle central : il rend impossible tout déplacement,
   redimensionnement ou déformation de la tête.
3. **Silhouette intacte** — le contour extérieur du personnage est le même partout.
4. **Fond identique** — les quatre bords et les coins sont ceux de `Normal`, au pixel près.
5. **Palette figée** — aucune couleur qui ne soit dans le portrait officiel.
6. **Vrai pixel art** — pas de pixel semi-transparent ; aucune couleur créée par interpolation
   (toute teinte employée existe déjà dans la palette d'origine).
7. **Expressions distinctes** — deux cases ne sont jamais identiques, et chacune diffère de
   `Normal` (sauf `Normal` elle-même).
8. **Miroirs `^`** — retournement horizontal exact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from build_portraits_manquants import SIZE, background_mask, load     # noqa: E402
from planche_terapagos_terastal import (                              # noqa: E402
    EXPRESSIONS, OEIL_H, OEIL_W, OEIL_X, OEIL_Y, OUT, REF,
)

MAX_COLOURS = 15


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def main() -> None:
    log: list[str] = []
    base = load(REF / "Normal.png")
    palette = {tuple(int(v) for v in c) for c in base.reshape(-1, 3)}
    silhouette_ref = ~background_mask(base)

    hors_oeil = np.ones((SIZE, SIZE), bool)
    hors_oeil[OEIL_Y:OEIL_Y + OEIL_H, OEIL_X:OEIL_X + OEIL_W] = False

    images = {}
    for nom in EXPRESSIONS:
        f = OUT / f"{nom}.png"
        fail(f.is_file(), f"{nom} : le portrait existe", log)
        im = Image.open(f)
        a = np.array(im)

        # --- 1. format ------------------------------------------------------------
        fail(im.size == (SIZE, SIZE), f"{nom} : {SIZE} × {SIZE}", log)
        fail(im.mode == "RGBA" and (a[:, :, 3] == 255).all(),
             f"{nom} : RGBA entièrement opaque (pas de pixel semi-transparent)", log)
        rgb = a[:, :, :3]
        couleurs = {tuple(int(v) for v in c) for c in rgb.reshape(-1, 3)}
        fail(len(couleurs) <= MAX_COLOURS, f"{nom} : {len(couleurs)} couleurs ≤ {MAX_COLOURS}", log)

        # --- 2. base verrouillée ---------------------------------------------------
        ecarts = int((~(rgb[hors_oeil] == base[hors_oeil]).all(axis=1)).sum())
        fail(ecarts == 0,
             f"{nom} : base verrouillée — {int(hors_oeil.sum())} pixels hors boîte de l'œil "
             f"identiques à Normal ({ecarts} écart)", log)

        # --- 3. silhouette ---------------------------------------------------------
        fail(np.array_equal(~background_mask(rgb), silhouette_ref),
             f"{nom} : contour extérieur identique à Normal", log)

        # --- 4. fond ---------------------------------------------------------------
        bords = np.zeros((SIZE, SIZE), bool)
        bords[0] = bords[-1] = True
        bords[:, 0] = bords[:, -1] = True
        fail(bool((rgb[bords] == base[bords]).all()), f"{nom} : bords du cadre identiques", log)

        # --- 5. palette figée ------------------------------------------------------
        fail(couleurs <= palette,
             f"{nom} : palette figée — aucune couleur hors du portrait officiel", log)

        # --- 8. miroir -------------------------------------------------------------
        flip = np.array(Image.open(OUT / f"{nom}^.png"))
        fail(np.array_equal(flip, a[:, ::-1]), f"{nom}^ : miroir horizontal exact", log)

        images[nom] = rgb

    # --- 7. expressions distinctes -------------------------------------------------
    fail(np.array_equal(images["Normal"], base), "Normal est la case officielle intacte", log)
    noms = list(images)
    for i, n1 in enumerate(noms):
        if n1 != "Normal":
            fail(not np.array_equal(images[n1], base), f"{n1} diffère de Normal", log)
        for n2 in noms[i + 1:]:
            fail(not np.array_equal(images[n1], images[n2]),
                 f"{n1} et {n2} sont deux expressions distinctes", log)

    modifs = {n: int(np.any(a != base, axis=2).sum()) for n, a in images.items()}
    rapport = {"pokemon": "Terapagos Terastal #1024 forme 0001",
               "controles": len(log), "echecs": 0, "expressions": len(images),
               "boite_oeil": {"x": OEIL_X, "y": OEIL_Y, "w": OEIL_W, "h": OEIL_H},
               "pixels_hors_boite_verrouilles": int(hors_oeil.sum()),
               "pixels_modifies_par_expression": modifs, "journal": log}
    (OUT / "controle_qualite.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    moy = sum(modifs.values()) / len(modifs)
    print(f"Terapagos Terastal — planche verrouillée : {len(log)} contrôles, "
          f"{len(images)} expressions, {int(hors_oeil.sum())} pixels verrouillés par case, "
          f"{moy:.0f} pixels modifiés en moyenne — conforme")


if __name__ == "__main__":
    main()
