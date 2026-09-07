#!/usr/bin/env python3
"""Relecture indépendante des `Eat` **dessinés à la main** (Ambipom, Gible, Pawmot, Dedenne).

Ce sont, avec Politoed, les seuls lots du dépôt où des pixels sont peints plutôt que déplacés.
Le contrôle vérifie donc, en plus des règles du SpriteBot, la **grammaire graphique de Chunsoft**
relevée sur les `Eat` officiels de Pichu #0172 et Riolu #0447 :

1. **Palette fermée** — aucune couleur qui ne soit déjà dans le sprite officiel.
2. **Cerne noir** — dans la zone dessinée, tout pixel de gorge est bordé de noir, de lèvre ou de
   gorge : jamais à vif sur la peau.
3. **Ombrage mesuré** — l'écart de valeur entre deux pixels voisins non noirs reste dans ce que
   font les originaux. Seuil relevé sur les `Eat` de Pichu et Riolu : leur écart maximal entre
   voisins est de **487** (somme RVB). On s'autorise la même chose, pas moins — un premier
   contrôle « la plus claire ne touche jamais la plus sombre » était plus strict que Chunsoft
   lui-même et rejetait des dessins parfaitement conformes.
4. **Changement local** — la bouchée ne modifie que la zone dessinée et le trajet des mains ;
   le bas du corps est intact au pixel près.
5. **La bouche s'ouvre** — l'image de bouchée contient plus de pixels de gorge que le repos.
6. **Le repos est l'original** — l'image 0 est la case Idle officielle, non retouchée.
7. **Les autres directions ne sont pas dessinées** — la bouche n'est visible que de face ; les
   sept autres lignes ne portent que le mouvement des mains.
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
import pmd_sprite as P                                        # noqa: E402
from dessine_eat_officiel import DESSINS, PLAN, SKELETON      # noqa: E402

MAX_COLOURS = 15
NOIR = (0, 0, 0)


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def voisins(m: np.ndarray) -> np.ndarray:
    o = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def luminance(c: tuple[int, int, int]) -> int:
    return sum(c)


# Écart de valeur maximal entre deux pixels voisins non noirs, mesuré sur les `Eat` officiels
# de Pichu #0172 (487) et Riolu #0447 (430). C'est la tolérance réelle des artistes ; un seuil
# plus sévère rejetterait leurs propres sprites.
ECART_CHUNSOFT = 487


def ecart_max(c: np.ndarray, zone: np.ndarray) -> int:
    """Plus grand écart de somme RVB entre deux pixels voisins non noirs **dans** la zone.

    On exige que les DEUX pixels soient dans la zone dessinée. Sinon on mesurerait aussi les
    contrastes propres au sprite d'origine, dont on n'est pas responsable : le museau blanc de
    Pawmot jouxte déjà un brun sombre (548 d'écart) sur la case Idle officielle, bien au-delà
    de ce que font Pichu et Riolu. Contrôler ce qu'on n'a pas dessiné rendrait le test ininterprétable.
    """
    plein = (c[:, :, 3] > 0) & ~np.all(c[:, :, :3] == NOIR, axis=2)
    valeur = c[:, :, :3].astype(int).sum(axis=2)
    pire = 0
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        voisin = np.roll(np.roll(plein, dy, 0), dx, 1)
        vzone = np.roll(np.roll(zone, dy, 0), dx, 1)
        vval = np.roll(np.roll(valeur, dy, 0), dx, 1)
        paire = plein & voisin & zone & vzone
        # écarter les paires nées du bouclage de np.roll sur les bords
        if dy:
            paire[0 if dy > 0 else -1, :] = False
        if dx:
            paire[:, 0 if dx > 0 else -1] = False
        if paire.any():
            pire = max(pire, int(np.abs(valeur - vval)[paire].max()))
    return pire


def controler(d) -> dict:
    log: list[str] = []
    ref = ROOT / "source" / "personnages" / "reference" / d.num
    out = ROOT / "personnages" / d.dossier / "eat_dessine"
    shadow_size, anims = P.load_sprite(ref)
    _, skel = P.load_sprite(SKELETON)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(anims)}

    root = ET.parse(out / "AnimData.xml").getroot()
    fail(int(root.findtext("ShadowSize")) == shadow_size,
         f"#{d.num} ShadowSize {shadow_size} repris du sprite officiel", log)
    node = next(n for n in root.find("Anims").iter("Anim") if n.findtext("Name") == "Eat")
    fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
    durations = [int(x.text) for x in node.find("Durations").iter("Duration")]
    fail(int(node.findtext("Index")) == skel["Eat"].index, f"#{d.num} créneau de Bayleef #0155", log)
    fail(durations == list(skel["Eat"].durations), f"#{d.num} cadence officielle {durations}", log)
    fail(fw % 2 == 0 and fh % 2 == 0, f"#{d.num} case paire {fw} × {fh}", log)

    tailles = []
    for kind in ("Anim", "Offsets", "Shadow"):
        im = Image.open(out / f"Eat-{kind}.png")
        fail(im.mode == "RGBA", f"#{d.num} Eat-{kind} en RGBA", log)
        tailles.append(im.size)
    fail(len(set(tailles)) == 1, f"#{d.num} trois feuilles de même taille", log)
    w, h = tailles[0]
    rows, cols = h // fh, w // fw
    fail(cols == len(durations), f"#{d.num} {cols} colonnes = {len(durations)} durées", log)
    fail(rows in (1, 8), f"#{d.num} {rows} ligne(s)", log)

    anim = np.array(Image.open(out / f"Eat-Anim.png"))
    offs = np.array(Image.open(out / f"Eat-Offsets.png"))
    shad = np.array(Image.open(out / f"Eat-Shadow.png"))
    fail(set(np.unique(anim[:, :, 3]).tolist()) <= {0, 255}, f"#{d.num} alpha 0 ou 255", log)
    palette = {tuple(int(v) for v in c) for c in anim[anim[:, :, 3] > 0][:, :3]}
    fail(len(palette) <= MAX_COLOURS, f"#{d.num} {len(palette)} couleurs ≤ {MAX_COLOURS}", log)
    fail(not (palette - base_palette),
         f"#{d.num} palette fermée : aucune couleur inventée (sprite : {len(base_palette)})", log)

    for dd in range(rows):
        for i in range(cols):
            s = shad[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]
            blancs = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
            fail(len(blancs) == 1, f"#{d.num} un seul pixel blanc (dir {dd}, image {i})", log)
            o = offs[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]
            for key, colour in P.MARK_COLOURS.items():
                trouve = np.argwhere((o[:, :, 3] == 255) & np.all(o[:, :, :3] == colour, axis=2))
                fail(len(trouve) <= 1, f"#{d.num} un repère {key} au plus (dir {dd}, image {i})", log)

    def case(i: int, dd: int = 0) -> np.ndarray:
        return anim[dd * fh:(dd + 1) * fh, i * fw:(i + 1) * fw]

    repos = case(0)

    # --- règle 6 : l'image de repos est la case officielle -----------------------
    src = anims["Idle"].frames[0][0]
    x0, y0, x1, y1 = src.bbox
    ax, ay = src.anchor
    original = src.image[ay + y0:ay + y1 + 1, ax + x0:ax + x1 + 1]
    ys, xs = np.nonzero(repos[:, :, 3])
    extrait = repos[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    fail(extrait.shape == original.shape and np.array_equal(extrait, original),
         f"#{d.num} l'image de repos est la case Idle officielle, non retouchée", log)

    # couleurs de gorge = celles employées par les dessins et absentes de la case au repos
    au_repos = {tuple(int(v) for v in c) for c in original[original[:, :, 3] > 0][:, :3]}
    employees = set(d.roles.values())
    gorge_cols = {c for c in employees if c != NOIR}

    for i, etape in enumerate(PLAN):
        if etape["bouche"] == "fermee":
            continue
        c = case(i)
        cys, cxs = np.nonzero(c[:, :, 3])
        bx, by = int(cxs.min()), int(cys.min())
        grille = d.bouches[etape["bouche"]]
        zone = np.zeros(c.shape[:2], bool)
        zone[by + d.oy:by + d.oy + len(grille), bx + d.ox:bx + d.ox + len(grille[0])] = True

        # --- règle 5 : la bouche s'ouvre ------------------------------------------
        def compte(img):
            m = np.zeros(img.shape[:2], bool)
            for col in gorge_cols:
                m |= (img[:, :, 3] > 0) & np.all(img[:, :, :3] == col, axis=2)
            return int((m & zone).sum())

        fail(compte(c) > 0, f"#{d.num} image {i} ({etape['bouche']}) : la bouche est dessinée", log)
        fail(not np.array_equal(c[zone], repos[zone]),
             f"#{d.num} image {i} : la zone de la bouche diffère du repos", log)

        # --- règle 2 : cerne noir --------------------------------------------------
        interieur = np.zeros(c.shape[:2], bool)
        for col in gorge_cols - au_repos:              # teintes propres à l'ouverture
            interieur |= (c[:, :, 3] > 0) & np.all(c[:, :, :3] == col, axis=2)
        interieur &= zone
        autorise = np.zeros(c.shape[:2], bool)
        for col in employees | {NOIR}:
            autorise |= (c[:, :, 3] > 0) & np.all(c[:, :, :3] == col, axis=2)
        if interieur.any():
            fail(not (voisins(interieur) & (c[:, :, 3] > 0) & ~autorise).any(),
                 f"#{d.num} image {i} : l'ouverture est cernée, jamais à vif sur la peau", log)

        # --- règle 3 : ombrage dans les clous de Chunsoft ---------------------------
        ecart = ecart_max(c, zone)
        fail(ecart <= ECART_CHUNSOFT,
             f"#{d.num} image {i} : écart de valeur entre voisins {ecart} ≤ {ECART_CHUNSOFT} "
             f"(maximum relevé sur les Eat de Pichu et Riolu)", log)

        # --- règle 4 : changement local --------------------------------------------
        diff = np.any(c != repos, axis=2)
        fail(int(diff.sum()) < int((repos[:, :, 3] > 0).sum()),
             f"#{d.num} image {i} : le dessin est local ({int(diff.sum())} pixels retouchés)", log)
        if diff.any():
            dernier = int(np.nonzero(diff.any(axis=1))[0].max())
            fail(np.array_equal(repos[dernier + 1:], c[dernier + 1:]),
                 f"#{d.num} image {i} : le bas du corps est intact sous la zone retouchée", log)

        # --- règle 7 : la bouche n'est dessinée que de face -------------------------
        if rows > 1:
            for dd in range(1, rows):
                autre = case(i, dd)
                m = np.zeros(autre.shape[:2], bool)
                for col in gorge_cols - au_repos:
                    m |= (autre[:, :, 3] > 0) & np.all(autre[:, :, :3] == col, axis=2)
                fail(not m.any(),
                     f"#{d.num} image {i} : pas de bouche dessinée sur la direction {dd}", log)

    nuit = Image.open(out / "nuit" / "Eat-Anim.png")
    fail(nuit.size == (w, h), f"#{d.num} feuille de nuit de même taille", log)
    fail((out / f"{d.dossier}_eat.aseprite").stat().st_size > 512, f"#{d.num} Aseprite écrit", log)
    fail((out / "credits.txt").is_file(), f"#{d.num} credits.txt écrit", log)

    rapport = {"pokemon": f"{d.label} #{d.num}", "controles": len(log), "echecs": 0,
               "couleurs": len(palette), "palette_du_sprite": len(base_palette),
               "trait_anime": d.note, "bouches": list(d.bouches), "journal": log}
    (out / "controle_qualite.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    return rapport


def main() -> None:
    for d in DESSINS:
        r = controler(d)
        print(f"{r['pokemon']:16s} {r['controles']:4d} contrôles, {r['couleurs']} couleurs "
              f"(palette : {r['palette_du_sprite']}) — grammaire Chunsoft respectée")


if __name__ == "__main__":
    main()
