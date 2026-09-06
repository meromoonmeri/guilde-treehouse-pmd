#!/usr/bin/env python3
"""Contrôles indépendants des portraits Falinks : format SpriteBot, palette,
conservation de la base et cohérence de la planche 200 × 320."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "portraits" / "falinks"
REF = ROOT / "source" / "portraits" / "reference" / "0870_Normal.png"
EMOTIONS = ["Normal", "Happy", "Pain", "Angry", "Worried",
            "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
            "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
            "Special1", "Sigh", "Stunned", "Special2", "Special3"]
PRODUCED = [e for e in EMOTIONS if not e.startswith("Special")]
# Zone du visage susceptible d'être retouchée (yeux + larmes) et zones d'effets.
FACE_ZONE = (13, 21, 33, 34)          # x0, y0, x1, y1 exclusifs
EFFECT_ZONES = [(0, 0, 40, 9)]        # bord haut : gouttes, croix, marque de colère
PRESERVED_MIN = 0.80                  # part du personnage identique à la base


def rgb(path: Path) -> np.ndarray:
    im = Image.open(path)
    assert im.mode == "RGBA", f"{path.name} : mode {im.mode}"
    a = np.array(im)
    assert a.shape == (40, 40, 4), f"{path.name} : taille {a.shape}"
    assert np.all(a[:, :, 3] == 255), f"{path.name} : transparence inattendue"
    return a[:, :, :3]


def n_colours(a: np.ndarray) -> int:
    return len(set(map(tuple, a.reshape(-1, 3).tolist())))


def main() -> None:
    base = rgb(REF)
    base_keys = {}
    bg = np.zeros((40, 40), bool)
    for colour in [(119, 199, 215), (178, 221, 201), (239, 255, 200)]:
        bg |= np.all(base == colour, axis=2)
    character = ~bg
    results = {"portraits": {}, "planche": {}, "erreurs": []}
    sheet = np.array(Image.open(OUT / "planche_spritebot.png").convert("RGBA"))
    assert sheet.shape == (320, 200, 4), "planche : 200 × 320 attendus"
    small = np.array(Image.open(OUT / "planche_spritebot_160.png").convert("RGBA"))
    assert small.shape == (160, 200, 4), "planche courte : 200 × 160 attendus"
    assert np.array_equal(small, sheet[:160]), "planche courte ≠ moitié haute"

    for i, name in enumerate(EMOTIONS):
        cx, cy = (i % 5) * 40, (i // 5) * 40
        cell = sheet[cy:cy + 40, cx:cx + 40]
        flip_cell = sheet[160 + cy:160 + cy + 40, cx:cx + 40]
        if name not in PRODUCED:
            assert np.all(cell[:, :, 3] == 0) and np.all(flip_cell[:, :, 3] == 0), f"{name} : case non vide"
            continue
        a = rgb(OUT / "emotions" / f"{name}.png")
        f = rgb(OUT / "emotions" / f"{name}^.png")
        assert np.array_equal(cell[:, :, :3], a) and np.all(cell[:, :, 3] == 255), f"{name} : planche ≠ PNG"
        assert np.array_equal(flip_cell[:, :, :3], f), f"{name}^ : planche ≠ PNG"
        assert np.array_equal(f, a[:, ::-1]), f"{name}^ : n'est pas le miroir"
        colours = n_colours(a)
        assert colours <= 15, f"{name} : {colours} couleurs"
        changed = np.any(a != base, axis=2)
        # Le fond peut changer partout ; le personnage seulement dans les zones prévues.
        allowed = bg.copy()
        x0, y0, x1, y1 = FACE_ZONE
        allowed[y0:y1, x0:x1] = True
        for ex0, ey0, ex1, ey1 in EFFECT_ZONES:
            allowed[ey0:ey1, ex0:ex1] = True
        allowed[26:29, 0] = True      # fentes du troupier gauche
        allowed[22:26, 39] = True     # fentes du troupier droit
        stray = changed & ~allowed
        if stray.any():
            ys, xs = np.nonzero(stray)
            results["erreurs"].append(f"{name} : {int(stray.sum())} pixels hors zones, ex. {(int(xs[0]), int(ys[0]))}")
        preserved = float(1 - (changed & character).sum() / character.sum())
        if name == "Normal":
            assert not changed.any(), "Normal doit être identique à la base"
        else:
            assert preserved >= PRESERVED_MIN, f"{name} : personnage conservé à {preserved:.0%}"
            assert (changed & (~bg)).any(), f"{name} : yeux identiques à la base"
        results["portraits"][name] = {
            "couleurs": colours,
            "pixels_modifies": int(changed.sum()),
            "personnage_conserve": round(preserved, 4),
            "miroir_ok": True,
        }
    results["planche"] = {"taille": [200, 320], "cases_pleines": len(PRODUCED) * 2,
                          "cases_vides": 8, "ordre": EMOTIONS}
    kit = json.loads((OUT / "kit.json").read_text(encoding="utf-8"))
    assert kit["format"]["ordre"] == EMOTIONS
    assert set(kit["emotions"]) == set(PRODUCED)
    credits = (OUT / "credits.txt").read_text(encoding="utf-8")
    assert "Emmuffin" in credits and "PMDCollab_2" in credits, "credits.txt incomplet"
    results["statut"] = "ok" if not results["erreurs"] else "erreurs"
    (OUT / "controle_qualite.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    if results["erreurs"]:
        raise SystemExit("\n".join(results["erreurs"]))
    print(f"{len(PRODUCED)} portraits vérifiés : format, palette ≤ 15, miroirs, planche et zones de retouche conformes.")


if __name__ == "__main__":
    main()
