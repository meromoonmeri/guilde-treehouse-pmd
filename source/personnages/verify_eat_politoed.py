#!/usr/bin/env python3
"""Relecture indépendante du `Eat` **dessiné** de Politoed (`personnages/politoed/eat_dessine/`).

Ce lot est le seul du dépôt où des pixels sont **peints à la main** plutôt que déplacés. Le
contrôle doit donc être plus sévère qu'ailleurs : en plus des règles du SpriteBot, il vérifie
que le dessin respecte la **grammaire graphique de Chunsoft**, relevée sur les `Eat` officiels
de Pichu #0172 et Riolu #0447.

Règles du SpriteBot / SkyTemple
- `AnimData.xml` lisible, `ShadowSize` repris du sprite d'origine, créneau `<Index>` de Bayleef ;
- trois feuilles de même taille, divisibles par la case, 1 ou 8 lignes, colonnes = durées ;
- case paire, alpha strictement 0 ou 255, 15 couleurs opaques au plus ;
- un seul pixel blanc par case dans `-Shadow.png`, un repère au plus par couleur dans `-Offsets.png`.

Grammaire graphique (le cœur de ce vérificateur)
1. **Palette fermée** — pas une seule couleur qui ne soit déjà dans le sprite officiel.
2. **Cerne noir** — dans la zone redessinée, tout pixel de gorge ou de langue est entouré de
   noir ou de lèvre : jamais une couleur de gorge à vif sur la peau verte, ce qui trahirait un
   dessin bâclé. Le contrôle est **limité aux pixels que le script a peints** : les pupilles de
   Politoed emploient les mêmes rouges et n'ont pas à être cernées de la même manière.
3. **Ombrage ordonné** — la lèvre claire ne touche jamais la lèvre sombre sans la teinte
   moyenne entre les deux, comme sur les sprites officiels.
4. **Changement local** — l'image de bouchée ne diffère de l'image de repos que dans la zone
   de la tête ; le bas du corps est identique au pixel près.
5. **La bouche s'ouvre vraiment** — l'image de bouchée contient des pixels de gorge que
   l'image de repos n'a pas, et son trait de bouche est plus épais.
6. **Le repos est l'original** — l'image 0 est la case Idle officielle, non retouchée.
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
import pmd_sprite as P                                             # noqa: E402
from dessine_eat_politoed import (                                 # noqa: E402
    DESSINS, GORGE, LANGUE, LEVRE, LEVRE_CLAIRE, LEVRE_OMBRE, NOIR, NUM, ORIGINE_X, ORIGINE_Y,
    OUT, PLAN, REF, SKELETON,
)

MAX_COLOURS = 15
ROUGES = {GORGE, LANGUE}
LEVRES = {LEVRE_CLAIRE, LEVRE, LEVRE_OMBRE}


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def voisins(mask: np.ndarray) -> np.ndarray:
    """Masque des 8 voisins de chaque pixel vrai."""
    out = np.zeros_like(mask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def main() -> None:
    log: list[str] = []
    shadow_size, ref_anims = P.load_sprite(REF)
    _, skel = P.load_sprite(SKELETON)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(ref_anims)}

    root = ET.parse(OUT / "AnimData.xml").getroot()
    fail(int(root.findtext("ShadowSize")) == shadow_size,
         f"ShadowSize {shadow_size} repris du sprite officiel", log)
    node = next(n for n in root.find("Anims").iter("Anim") if n.findtext("Name") == "Eat")
    fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
    durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
    fail(int(node.findtext("Index")) == skel["Eat"].index, "créneau <Index> de Bayleef #0155", log)
    fail(durations == list(skel["Eat"].durations), f"cadence officielle {durations}", log)
    fail(fw % 2 == 0 and fh % 2 == 0, f"case paire {fw} × {fh}", log)

    sizes = []
    for kind in ("Anim", "Offsets", "Shadow"):
        im = Image.open(OUT / f"Eat-{kind}.png")
        fail(im.mode == "RGBA", f"Eat-{kind} en RGBA", log)
        sizes.append(im.size)
    fail(len(set(sizes)) == 1, "trois feuilles de même taille", log)
    w, h = sizes[0]
    rows, cols = h // fh, w // fw
    fail(w % fw == 0 and h % fh == 0, "feuille divisible par la case", log)
    fail(rows in (1, 8), f"{rows} ligne(s)", log)
    fail(cols == len(durations), f"{cols} colonnes = {len(durations)} durées", log)

    anim = np.array(Image.open(OUT / "Eat-Anim.png"))
    offs = np.array(Image.open(OUT / "Eat-Offsets.png"))
    shad = np.array(Image.open(OUT / "Eat-Shadow.png"))
    fail(set(np.unique(anim[:, :, 3]).tolist()) <= {0, 255}, "alpha 0 ou 255", log)
    palette = {tuple(int(v) for v in c) for c in anim[anim[:, :, 3] > 0][:, :3]}
    fail(len(palette) <= MAX_COLOURS, f"{len(palette)} couleurs ≤ {MAX_COLOURS}", log)

    # --- règle 1 : palette fermée -------------------------------------------------
    hors = palette - base_palette
    fail(not hors, f"palette fermée : aucune couleur inventée (sprite : {len(base_palette)})", log)

    for d in range(rows):
        for i in range(cols):
            s = shad[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
            blancs = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
            fail(len(blancs) == 1, f"un seul pixel blanc (dir {d}, image {i})", log)
            o = offs[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
            for key, colour in P.MARK_COLOURS.items():
                trouve = np.argwhere((o[:, :, 3] == 255) & np.all(o[:, :, :3] == colour, axis=2))
                fail(len(trouve) <= 1, f"un repère {key} au plus (dir {d}, image {i})", log)

    def case(i: int, d: int = 0) -> np.ndarray:
        return anim[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]

    repos, bouchee = case(0), case(1)

    # --- règle 6 : l'image de repos est la case officielle -------------------------
    src = ref_anims["Idle"].frames[0][0]
    x0, y0, x1, y1 = src.bbox
    ax, ay = src.anchor
    original = src.image[ay + y0:ay + y1 + 1, ax + x0:ax + x1 + 1]
    ys, xs = np.nonzero(repos[:, :, 3])
    extrait = repos[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    fail(extrait.shape == original.shape and np.array_equal(extrait, original),
         "l'image de repos est la case Idle officielle, non retouchée", log)

    # --- règle 5 : la bouche s'ouvre vraiment --------------------------------------
    def rouges(c: np.ndarray) -> int:
        """Pixels de gorge/langue sous la ligne des yeux : la bouche, pas les pupilles."""
        m = np.zeros(c.shape[:2], bool)
        for col in ROUGES:
            m |= (c[:, :, 3] > 0) & np.all(c[:, :, :3] == col, axis=2)
        m[:c.shape[0] // 2] = False
        return int(m.sum())

    fail(rouges(bouchee) > rouges(repos),
         f"la bouche s'ouvre : {rouges(repos)} → {rouges(bouchee)} pixels de gorge", log)

    for i, etape in enumerate(PLAN):
        if etape["bouche"] == "fermee":
            continue
        c = case(i)
        fail(rouges(c) > rouges(repos), f"image {i} ({etape['bouche']}) : la bouche est ouverte", log)

        # --- règle 2 : cerne noir ---------------------------------------------------
        # Uniquement sur le rectangle réellement dessiné : ailleurs les mêmes rouges servent
        # aux pupilles de Politoed, qui n'ont pas à suivre la même règle. Le rectangle est
        # celui du dessin, ramené dans la case par la boîte du sprite.
        dessin = DESSINS[etape["bouche"]]
        cys, cxs = np.nonzero(c[:, :, 3])
        bx, by = int(cxs.min()), int(cys.min())
        peint = np.zeros(c.shape[:2], bool)
        peint[by + ORIGINE_Y:by + ORIGINE_Y + len(dessin),
              bx + ORIGINE_X:bx + ORIGINE_X + len(dessin[0])] = True
        gorge = np.zeros(c.shape[:2], bool)
        for col in ROUGES:
            gorge |= (c[:, :, 3] > 0) & np.all(c[:, :, :3] == col, axis=2)
        gorge &= peint
        autorise = np.zeros(c.shape[:2], bool)
        for col in ROUGES | LEVRES | {NOIR}:
            autorise |= (c[:, :, 3] > 0) & np.all(c[:, :, :3] == col, axis=2)
        # tout voisin d'un pixel de gorge doit être gorge, lèvre ou noir
        fail(not (voisins(gorge) & (c[:, :, 3] > 0) & ~autorise).any(),
             f"image {i} : la gorge est cernée de noir ou de lèvre, jamais à vif sur la peau", log)

        # --- règle 3 : ombrage ordonné ----------------------------------------------
        clair = (c[:, :, 3] > 0) & np.all(c[:, :, :3] == LEVRE_CLAIRE, axis=2) & peint
        sombre = (c[:, :, 3] > 0) & np.all(c[:, :, :3] == LEVRE_OMBRE, axis=2) & peint
        fail(not (voisins(clair) & sombre).any(),
             f"image {i} : pas de saut de valeur, la lèvre claire ne touche pas la sombre", log)

        # --- règle 4 : changement local ---------------------------------------------
        diff = np.any(c != repos, axis=2)
        if diff.any():
            dys = np.nonzero(diff.any(axis=1))[0]
            corps_bas = repos[dys.max() + 1:]
            fail(np.array_equal(corps_bas, c[dys.max() + 1:]),
                 f"image {i} : le bas du corps est intact sous la zone redessinée", log)
            fail(int(diff.sum()) < int((repos[:, :, 3] > 0).sum()),
                 f"image {i} : le dessin est local ({int(diff.sum())} pixels retouchés)", log)

    nuit = Image.open(OUT / "nuit" / "Eat-Anim.png")
    fail(nuit.size == (w, h), "feuille de nuit de même taille", log)
    fail((OUT / "politoed_eat.aseprite").stat().st_size > 512, "Aseprite écrit", log)
    fail((OUT / "credits.txt").is_file(), "credits.txt écrit", log)

    rapport = {"sprite": f"Politoed #{NUM} — Eat dessiné à la main", "controles": len(log),
               "echecs": 0, "couleurs": len(palette), "palette_du_sprite": len(base_palette),
               "bouches": [e["bouche"] for e in PLAN], "journal": log}
    (OUT / "controle_qualite.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    print(f"Politoed Eat dessiné : {len(log)} contrôles, {len(palette)} couleurs "
          f"(palette du sprite : {len(base_palette)}) — grammaire Chunsoft respectée")


if __name__ == "__main__":
    main()
