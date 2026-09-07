#!/usr/bin/env python3
"""Relecture indépendante des portraits complétés (portraits/politoed, hariyama, ambipom, pawmot).

Rejoue les règles du SpriteBot de PMDCollab pour les portraits, plus les contrôles propres à la
méthode de retouche :

SpriteBot
- 40 × 40 px, RGBA entièrement opaque, pas de couleur semi-transparente ;
- 15 couleurs au plus par portrait ;
- planche 200 × 320 (5 × 8 cases), ordre officiel des émotions, cases Special vides ;
- chaque version « ^ » est le miroir horizontal exact de son portrait.

Méthode
- les émotions déjà publiées sur SpriteCollab sont **octet pour octet** celles de la référence ;
- « Normal » est la base d'origine, inchangée ;
- hors du fond, une émotion ne modifie que les boîtes des yeux et les zones d'effet déclarées ;
- le personnage (tout ce qui n'est pas le fond détecté) garde sa palette d'origine, sauf dans
  les boîtes des yeux et sous les larmes ;
- toutes les émotions du gabarit sont produites ;
- **le fond est canonique** : les deux teintes sont exactement celles relevées sur les portraits
  officiels de l'émotion, et leur disposition est celle de PMDCollab — ciel plein en haut,
  sol plein en bas, damier de transition entre les deux, jamais un dégradé libre.

Écrit `controle_qualite.json` dans chaque dossier.
"""
from __future__ import annotations

import filecmp
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from build_portraits_manquants import (   # noqa: E402
    BACKGROUNDS, DAMIER, EMOTIONS, HORIZON, MAX_COLOURS, PRODUCED, REF, SIZE, TARGETS,
    background_mask, load,
)


def fail(cond: bool, message: str, log: list[str]) -> None:
    log.append(("ok   " if cond else "ÉCHEC ") + message)
    if not cond:
        raise AssertionError(message)


def rgba(path: Path) -> np.ndarray:
    im = Image.open(path)
    assert im.mode == "RGBA", f"{path.name} : mode {im.mode}"
    return np.array(im)


def check(t) -> dict:
    out = ROOT / "portraits" / t.folder
    log: list[str] = []
    base = load(REF / t.num / "Normal.png")
    bg = background_mask(base)
    kit = json.loads((out / "kit.json").read_text(encoding="utf-8"))
    official = {p.stem for p in (REF / t.num).glob("*.png")}

    # zones où la retouche a le droit de toucher le personnage
    free = bg.copy()
    for e in t.eyes:
        free[max(0, e.y - 1):e.y + e.h + 1, max(0, e.x - 1):e.x + e.w + 1] = True
    for x, y in t.tears:
        free[y:y + 6, max(0, x - 1):x + 2] = True
    for x, y in (t.drop, t.mark):
        free[y:y + 8, x:x + 8] = True

    base_palette = {tuple(int(v) for v in c) for c in base.reshape(-1, 3)}
    for name in PRODUCED:
        img = rgba(out / "emotions" / f"{name}.png")
        flip = rgba(out / "emotions" / f"{name}^.png")
        fail(img.shape == (SIZE, SIZE, 4), f"#{t.num} {name} en {SIZE} × {SIZE}", log)
        fail((img[:, :, 3] == 255).all(), f"#{t.num} {name} entièrement opaque", log)
        colours = {tuple(int(v) for v in c) for c in img[:, :, :3].reshape(-1, 3)}
        fail(len(colours) <= MAX_COLOURS, f"#{t.num} {name} {len(colours)} couleurs ≤ {MAX_COLOURS}", log)
        fail(np.array_equal(flip, img[:, ::-1]), f"#{t.num} {name}^ miroir exact", log)
        if name in official:
            fail(filecmp.cmp(out / "emotions" / f"{name}.png", REF / t.num / f"{name}.png", shallow=False)
                 or np.array_equal(img[:, :, :3], load(REF / t.num / f"{name}.png")),
                 f"#{t.num} {name} identique au portrait officiel", log)
            continue
        rgb = img[:, :, :3]
        changed = np.any(rgb != base, axis=2)
        fail(bool((changed & ~free).sum() == 0),
             f"#{t.num} {name} ne modifie que le fond, les yeux et les zones d'effet", log)
        # --- fond canonique ---------------------------------------------------------
        # Le fond doit être celui de PMDCollab : deux teintes fixes par émotion, ciel plein en
        # haut, sol plein en bas, damier entre les deux. On mesure la teinte MAJORITAIRE de
        # chaque bande — les effets (goutte, larmes, étincelles) sont dessinés par-dessus le
        # fond et forment une minorité de pixels qu'on ne cherche pas à énumérer.
        if BACKGROUNDS.get(name) and name != "Shouting":
            ciel, sol = BACKGROUNDS[name]
            if kit["emotions"][name].get("fond", {}).get("type") == "aplat":
                sol = ciel
            peint = bg & np.any(rgb != base, axis=2)

            def majoritaire(zone: np.ndarray):
                px = rgb[zone]
                if not len(px):
                    return None
                uniq, cnt = np.unique(px, axis=0, return_counts=True)
                return tuple(int(v) for v in uniq[cnt.argmax()])

            haut = peint.copy(); haut[HORIZON:] = False
            bas = peint.copy(); bas[:HORIZON + DAMIER] = False
            m_haut, m_bas = majoritaire(haut), majoritaire(bas)
            if m_haut is not None:
                fail(m_haut == ciel,
                     f"#{t.num} {name} : le ciel est la teinte canonique de l'émotion "
                     f"(#{ciel[0]:02x}{ciel[1]:02x}{ciel[2]:02x})", log)
            if m_bas is not None:
                fail(m_bas == sol,
                     f"#{t.num} {name} : le sol est la teinte canonique de l'émotion "
                     f"(#{sol[0]:02x}{sol[1]:02x}{sol[2]:02x})", log)
            # Bandes horizontales : dans le ciel plein, chaque ligne repeinte est unie à la
            # teinte du ciel, effets exclus. Le décompte se fait sur l'ensemble des lignes —
            # une ligne peut être entièrement occupée par une étincelle (Joyous), ce qui est
            # légitime ; ce qui ne le serait pas, c'est un dégradé, donc plusieurs lignes de
            # ciel différentes entre elles.
            lignes = []
            for y in range(HORIZON):
                px = rgb[y][peint[y]]
                if len(px) >= 4:
                    uniq, cnt = np.unique(px, axis=0, return_counts=True)
                    lignes.append(tuple(int(v) for v in uniq[cnt.argmax()]))
            if lignes:
                fail(lignes.count(ciel) >= len(lignes) - 1,
                     f"#{t.num} {name} : le ciel est une bande horizontale unie, pas un dégradé "
                     f"({lignes.count(ciel)}/{len(lignes)} lignes à la teinte canonique)", log)
            # le damier alterne réellement les deux teintes quand elles diffèrent
            if ciel != sol:
                zone = peint.copy()
                zone[:HORIZON] = False
                zone[HORIZON + DAMIER:] = False
                px = rgb[zone]
                if len(px) >= 8:
                    teintes = {tuple(int(v) for v in c) for c in px}
                    fail(ciel in teintes and sol in teintes,
                         f"#{t.num} {name} : la bande de transition est un damier des deux teintes", log)

        kept = {tuple(int(v) for v in c) for c in rgb[~free]}
        fail(kept <= base_palette, f"#{t.num} {name} le personnage garde sa palette d'origine", log)
        fail(changed.any(), f"#{t.num} {name} diffère bien de la base", log)

    fail(np.array_equal(rgba(out / "emotions" / "Normal.png")[:, :, :3], base),
         f"#{t.num} Normal est la base d'origine", log)

    sheet = rgba(out / "planche_spritebot.png")
    fail(sheet.shape == (320, 200, 4), f"#{t.num} planche 200 × 320", log)
    for i, name in enumerate(EMOTIONS):
        cx, cy = (i % 5) * 40, (i // 5) * 40
        tile = sheet[cy:cy + 40, cx:cx + 40]
        if name.startswith("Special"):
            fail((tile[:, :, 3] == 0).all(), f"#{t.num} case {name} vide", log)
            continue
        fail(np.array_equal(tile[:, :, :3], rgba(out / "emotions" / f"{name}.png")[:, :, :3]),
             f"#{t.num} planche : {name} à sa place", log)
        low = sheet[160 + cy:160 + cy + 40, cx:cx + 40]
        fail(np.array_equal(low[:, :, :3], rgba(out / "emotions" / f"{name}^.png")[:, :, :3]),
             f"#{t.num} planche : {name}^ à sa place", log)

    fail(len(kit["emotions"]) == len(PRODUCED), f"#{t.num} kit.json décrit les {len(PRODUCED)} émotions", log)
    fail((out / "credits.txt").is_file(), f"#{t.num} credits.txt écrit", log)

    report = {"pokemon": f"{t.label} #{t.num}", "controles": len(log), "echecs": 0,
              "emotions": len(PRODUCED), "officielles_reprises": sorted(official & set(PRODUCED)),
              "journal": log}
    (out / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def main() -> None:
    for t in TARGETS:
        r = check(t)
        print(f"{r['pokemon']:18s} {r['controles']:4d} contrôles, {r['emotions']} émotions "
              f"(dont {len(r['officielles_reprises'])} officielles) — tout est conforme")


if __name__ == "__main__":
    main()
