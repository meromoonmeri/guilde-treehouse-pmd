#!/usr/bin/env python3
"""Relecture indépendante des animations de scène ajoutées (personnages/*/animations_scenes/).

Rejoue les règles du SpriteBot de PMDCollab et de l'import SkyTemple, plus les contrôles
propres à la méthode de composition :

SpriteBot / SkyTemple
- `AnimData.xml` lisible, `ShadowSize` dans 0-2, index conformes à `sprite_config.json` ;
- pas de `CopyOf` chaîné, cible existante ;
- trois feuilles de même taille par animation, divisibles par la case, 1 ou 8 lignes ;
- nombre de colonnes = nombre de durées, durées ≥ 1 ;
- cases paires ; alpha strictement 0 ou 255 ; 15 couleurs opaques au plus ;
- un seul pixel blanc par case dans `-Shadow.png`, un seul repère par couleur dans `-Offsets.png`.

Composition
- les animations d'origine sont **octet pour octet** celles de la référence ;
- les durées, le nombre d'images et les déplacements d'ancre des animations ajoutées sont
  ceux du squelette #0155 ;
- la palette des animations ajoutées est incluse dans celle du sprite d'origine
  (aucun pixel n'a été repeint) ;
- les feuilles nuit ont la taille des feuilles de jour.

Écrit `controle_qualite.json` dans chaque dossier et sort en erreur au premier manquement.
"""
from __future__ import annotations

import filecmp
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                    # noqa: E402
from build_animations_scenes import POKEMON, RECIPES, SKELETON   # noqa: E402

REF = ROOT / "source" / "personnages" / "reference"
MAX_COLOURS = 15


def fail(cond: bool, message: str, log: list[str]) -> None:
    if cond:
        log.append("ok   " + message)
    else:
        log.append("ÉCHEC " + message)
        raise AssertionError(message)


def check(num: str) -> dict:
    folder, label, _ = POKEMON[num]
    out = ROOT / "personnages" / folder / "animations_scenes"
    log: list[str] = []
    root = ET.parse(out / "AnimData.xml").getroot()
    shadow_size = int(root.findtext("ShadowSize"))
    fail(0 <= shadow_size <= 2, f"#{num} ShadowSize {shadow_size} dans 0-2", log)

    ref_size, ref_anims = P.load_sprite(REF / num)
    fail(shadow_size == ref_size, f"#{num} ShadowSize identique à la référence", log)
    _, skel = P.load_sprite(REF / SKELETON)
    ref_palette = P.palette_of(ref_anims)

    nodes = list(root.find("Anims").iter("Anim"))
    # les copies partagent volontairement le créneau de leur cible (Appeal/Twirl, SpAttack/RearUp…)
    indices = [int(n.findtext("Index")) for n in nodes if n.findtext("CopyOf") is None]
    fail(len(indices) == len(set(indices)), f"#{num} créneaux <Index> distincts hors copies", log)
    names = [n.findtext("Name") for n in nodes]
    fail(len(names) == len(set(names)), f"#{num} pas de doublon de nom", log)
    for name in RECIPES:
        fail(name in names, f"#{num} {name} présent", log)

    total_palette: set[tuple[int, int, int]] = set()
    added = 0
    for node in nodes:
        name = node.findtext("Name")
        index = int(node.findtext("Index"))
        expected = skel[name].index if name in RECIPES else ref_anims[name].index
        fail(index == expected, f"#{num} {name} créneau <Index> {index} attendu", log)
        copy = node.findtext("CopyOf")
        if copy:
            fail(copy in names, f"#{num} {name} copie {copy} qui existe", log)
            target = next(n for n in nodes if n.findtext("Name") == copy)
            fail(target.findtext("CopyOf") is None, f"#{num} {name} copie non chaînée", log)
            continue
        fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
        durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
        fail(fw % 2 == 0 and fh % 2 == 0, f"#{num} {name} case paire {fw} × {fh}", log)
        fail(all(d >= 1 for d in durations), f"#{num} {name} durées ≥ 1", log)
        sizes = []
        for kind in ("Anim", "Offsets", "Shadow"):
            im = Image.open(out / f"{name}-{kind}.png")
            fail(im.mode == "RGBA", f"#{num} {name}-{kind} en RGBA", log)
            sizes.append(im.size)
        fail(len(set(sizes)) == 1, f"#{num} {name} trois feuilles de même taille", log)
        w, h = sizes[0]
        fail(w % fw == 0 and h % fh == 0, f"#{num} {name} feuille divisible par la case", log)
        rows, cols = h // fh, w // fw
        fail(rows in (1, 8), f"#{num} {name} {rows} ligne(s)", log)
        fail(cols == len(durations), f"#{num} {name} {cols} colonnes = {len(durations)} durées", log)
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            v = node.findtext(tag)
            if v is not None:
                fail(0 <= int(v) < cols, f"#{num} {name} {tag} dans les images", log)

        anim = np.array(Image.open(out / f"{name}-Anim.png"))
        offs = np.array(Image.open(out / f"{name}-Offsets.png"))
        shad = np.array(Image.open(out / f"{name}-Shadow.png"))
        fail(set(np.unique(anim[:, :, 3]).tolist()) <= {0, 255}, f"#{num} {name} alpha 0 ou 255", log)
        px = anim[anim[:, :, 3] > 0]
        colours = set(map(tuple, px[:, :3].tolist()))
        total_palette |= colours
        for d in range(rows):
            for i in range(cols):
                s = shad[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                white = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
                fail(len(white) == 1, f"#{num} {name} un seul pixel blanc (dir {d}, image {i})", log)
                o = offs[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                for key, colour in P.MARK_COLOURS.items():
                    found = np.argwhere((o[:, :, 3] == 255) & np.all(o[:, :, :3] == colour, axis=2))
                    fail(len(found) <= 1, f"#{num} {name} un repère {key} au plus (dir {d}, image {i})", log)

        if name in RECIPES:
            added += 1
            sk = skel[name]
            fail(durations == list(sk.durations), f"#{num} {name} durées du squelette #{SKELETON}", log)
            fail(rows == RECIPES[name][0], f"#{num} {name} {rows} ligne(s) conformes à la recette", log)
            for i in range(cols):
                s = shad[0:fh, i * fw:(i + 1) * fw]
                (ay, ax), = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
                disp = (int(ax) - fw // 2, int(ay) - (fh // 2 + 4))
                fail(disp == sk.frames[0][i].disp, f"#{num} {name} déplacement d'ancre {i} = squelette", log)
            fail(colours <= ref_palette, f"#{num} {name} palette incluse dans celle du sprite d'origine", log)
            nuit = Image.open(out / "nuit" / f"{name}-Anim.png")
            fail(nuit.size == (w, h), f"#{num} {name} feuille de nuit de même taille", log)
        else:
            for kind in ("Anim", "Offsets", "Shadow"):
                fail(filecmp.cmp(out / f"{name}-{kind}.png", REF / num / f"{name}-{kind}.png", shallow=False),
                     f"#{num} {name}-{kind} identique à la référence", log)

    fail(len(total_palette) <= MAX_COLOURS, f"#{num} {len(total_palette)} couleurs ≤ {MAX_COLOURS}", log)
    fail(added == len(RECIPES), f"#{num} {added} animations ajoutées", log)
    fail((out / f"{folder}_scenes.aseprite").stat().st_size > 1024, f"#{num} Aseprite écrit", log)

    report = {"pokemon": f"{label} #{num}", "controles": len(log), "echecs": 0,
              "animations_ajoutees": added, "couleurs": len(total_palette),
              "squelette": SKELETON, "journal": log}
    (out / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def main() -> None:
    for num in POKEMON:
        r = check(num)
        print(f"{r['pokemon']:20s} {r['controles']:4d} contrôles, {r['animations_ajoutees']} animations, {r['couleurs']} couleurs — tout est conforme")


if __name__ == "__main__":
    main()
