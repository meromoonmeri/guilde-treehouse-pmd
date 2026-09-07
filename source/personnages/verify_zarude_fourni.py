#!/usr/bin/env python3
"""Relecture indépendante de `personnages/zarude_fourni/` (dessin de l'utilisateur mis au format).

Règles du SpriteBot / SkyTemple
- `AnimData.xml` lisible, `ShadowSize` dans 0-2, créneaux `<Index>` distincts hors copies,
  `CopyOf` non chaîné et pointant sur une animation existante ;
- trois feuilles de même taille par animation, divisibles par la case, 1 ou 8 lignes,
  colonnes = durées, durées ≥ 1, `Rush`/`Hit`/`Return` dans les images ;
- cases paires ; alpha strictement 0 ou 255 ; **15 couleurs opaques au plus** ;
- un seul pixel blanc par case dans `-Shadow.png`, un seul repère de chaque couleur dans `-Offsets.png`.

Contrôles propres à la méthode
- durées, déplacements d'ancre, cases et créneaux identiques au squelette Rillaboom #0812
  (la case peut être agrandie d'un multiple de 8, jamais réduite) ;
- la palette est exactement celle du dessin fourni après réduction à 15 couleurs — aucune
  couleur inventée ;
- chaque case ne contient que des pixels du dessin fourni : la silhouette de chaque image est,
  au pixel près, l'une des seize poses de la planche (éventuellement retournée) ;
- les feuilles de nuit ont la taille des feuilles de jour.
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
import pmd_sprite as P                                     # noqa: E402
from build_zarude_fourni import (                          # noqa: E402
    FRAME_PLAN, MAX_COLOURS, OUT, SKELETON, read_poses,
)


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def main() -> None:
    log: list[str] = []
    poses = read_poses()
    pose_shapes = set()
    pose_palette: set[tuple[int, int, int]] = set()
    for crop, _ in poses.values():
        mask = crop[:, :, 3] > 0
        pose_shapes.add(mask.tobytes() + bytes(mask.shape))
        pose_shapes.add(mask[:, ::-1].copy().tobytes() + bytes(mask.shape))
        pose_palette |= set(map(tuple, crop[mask][:, :3].tolist()))

    shadow_size, skel = P.load_sprite(SKELETON)
    root = ET.parse(OUT / "AnimData.xml").getroot()
    fail(int(root.findtext("ShadowSize")) == shadow_size, "ShadowSize repris du squelette", log)
    nodes = list(root.find("Anims").iter("Anim"))
    names = [n.findtext("Name") for n in nodes]
    fail(len(names) == len(set(names)), "pas de doublon de nom", log)
    indices = [int(n.findtext("Index")) for n in nodes if n.findtext("CopyOf") is None]
    fail(len(indices) == len(set(indices)), "créneaux <Index> distincts hors copies", log)
    for name in FRAME_PLAN:
        fail(name in names, f"{name} présent", log)

    palette: set[tuple[int, int, int]] = set()
    for node in nodes:
        name = node.findtext("Name")
        copy = node.findtext("CopyOf")
        if copy:
            fail(copy in names, f"{name} copie {copy} qui existe", log)
            fail(next(n for n in nodes if n.findtext("Name") == copy).findtext("CopyOf") is None,
                 f"{name} copie non chaînée", log)
            continue
        sk = skel[name]
        fw, fh = int(node.findtext("FrameWidth")), int(node.findtext("FrameHeight"))
        durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
        fail(int(node.findtext("Index")) == sk.index, f"{name} créneau du squelette", log)
        fail(durations == list(sk.durations), f"{name} durées du squelette", log)
        fail(fw % 2 == 0 and fh % 2 == 0, f"{name} case paire {fw} × {fh}", log)
        fail(fw >= sk.fw and fh >= sk.fh and (fw - sk.fw) % 8 == 0 and (fh - sk.fh) % 8 == 0,
             f"{name} case agrandie d'un multiple de 8 par rapport au squelette", log)

        sizes = []
        for kind in ("Anim", "Offsets", "Shadow"):
            im = Image.open(OUT / f"{name}-{kind}.png")
            fail(im.mode == "RGBA", f"{name}-{kind} en RGBA", log)
            sizes.append(im.size)
        fail(len(set(sizes)) == 1, f"{name} trois feuilles de même taille", log)
        w, h = sizes[0]
        fail(w % fw == 0 and h % fh == 0, f"{name} feuille divisible par la case", log)
        rows, cols = h // fh, w // fw
        fail(rows in (1, 8) and rows == sk.dirs, f"{name} {rows} ligne(s) comme le squelette", log)
        fail(cols == len(durations), f"{name} {cols} colonnes = {len(durations)} durées", log)
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            v = node.findtext(tag)
            if v is not None:
                fail(0 <= int(v) < cols, f"{name} {tag} dans les images", log)

        anim = np.array(Image.open(OUT / f"{name}-Anim.png"))
        offs = np.array(Image.open(OUT / f"{name}-Offsets.png"))
        shad = np.array(Image.open(OUT / f"{name}-Shadow.png"))
        fail(set(np.unique(anim[:, :, 3]).tolist()) <= {0, 255}, f"{name} alpha 0 ou 255", log)
        palette |= set(map(tuple, anim[anim[:, :, 3] > 0][:, :3].tolist()))
        for d in range(rows):
            for i in range(cols):
                s = shad[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                white = np.argwhere((s[:, :, 3] > 0) & np.all(s[:, :, :3] == 255, axis=2))
                fail(len(white) == 1, f"{name} un seul pixel blanc (dir {d}, image {i})", log)
                (ay, ax) = (int(v) for v in white[0])
                disp = (ax - fw // 2, ay - (fh // 2 + 4))
                fail(disp == sk.frames[0][i].disp, f"{name} déplacement d'ancre du squelette (dir {d}, image {i})", log)
                o = offs[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                for key, colour in P.MARK_COLOURS.items():
                    found = np.argwhere((o[:, :, 3] == 255) & np.all(o[:, :, :3] == colour, axis=2))
                    fail(len(found) <= 1, f"{name} un repère {key} au plus (dir {d}, image {i})", log)
                cell = anim[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                ys, xs = np.nonzero(cell[:, :, 3])
                mask = (cell[:, :, 3] > 0)[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                fail(mask.tobytes() + bytes(mask.shape) in pose_shapes,
                     f"{name} silhouette identique à une pose fournie (dir {d}, image {i})", log)
        nuit = Image.open(OUT / "nuit" / f"{name}-Anim.png")
        fail(nuit.size == (w, h), f"{name} feuille de nuit de même taille", log)

    fail(len(palette) <= MAX_COLOURS, f"{len(palette)} couleurs ≤ {MAX_COLOURS}", log)
    fail(palette <= pose_palette, "aucune couleur hors du dessin fourni", log)
    fail((OUT / "zarude_fourni.aseprite").stat().st_size > 1024, "Aseprite écrit", log)

    report = {"sprite": "Zarude — dessin fourni mis au format", "controles": len(log), "echecs": 0,
              "animations": len(FRAME_PLAN), "couleurs": len(palette), "squelette": "Rillaboom #0812",
              "journal": log}
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Zarude fourni : {len(log)} contrôles, {len(FRAME_PLAN)} animations, {len(palette)} couleurs — tout est conforme")


if __name__ == "__main__":
    main()
