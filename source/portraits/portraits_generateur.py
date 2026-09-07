#!/usr/bin/env python3
"""Portraits d'émotion produits **avec le générateur d'images**, disciplinés puis vérifiés.

L'utilisateur a demandé d'employer le générateur pour les portraits en lui envoyant les images
officielles. C'est ce que fait ce script : le `Normal` officiel de PMDCollab est soumis au
générateur avec la consigne de refaire **le même visage** avec une expression donnée, et la
sortie est ramenée dans les contraintes du format SpriteCollab.

────────────────────────────────────────────────────────────────────────────────
POURQUOI ÇA MARCHE MIEUX QUE SUR LES SPRITES
────────────────────────────────────────────────────────────────────────────────
Un portrait fait 40 × 40 avec un visage qui occupe presque tout le cadre : le générateur a de
la place pour dessiner une expression, là où un sprite de donjon de 17 px ne lui en laisse pas.
Mesuré sur les premières sorties, **le personnage est conservé à 88-95 %** alors que le fond,
lui, change entièrement — ce qui est voulu, puisque chaque émotion a son fond.

────────────────────────────────────────────────────────────────────────────────
LA DISCIPLINE, EN QUATRE TEMPS
────────────────────────────────────────────────────────────────────────────────
1. **Grille exacte** 40 × 40 par moyenne de bloc (`Image.BOX`), jamais `NEAREST`.
2. **Palette fermée** : chaque pixel rabattu sur la couleur la plus proche du portrait officiel.
   Le générateur sort 446 à 574 couleurs ; la limite du SpriteBot est 15.
3. **Le personnage vient du générateur, le fond non.** On ne garde la sortie que **hors du
   décor** ; le fond est ensuite repeint aux **couleurs canoniques de l'émotion**, dans la
   géométrie officielle (ciel plein, damier, sol plein). Le générateur invente des fonds
   plausibles mais jamais canoniques — autant ne pas les lui demander.
4. **Miroir `^`** produit par retournement exact, comme l'exige le format.

Ce qui reste du générateur : l'**expression** — les yeux, la bouche, l'inclinaison. C'est
précisément ce qu'il fait bien, et ce qui était le plus laborieux à écrire à la main.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from build_portraits_manquants import (          # noqa: E402
    BACKGROUNDS, DAMIER, HORIZON, SIZE, background_mask, load,
)

REF = ROOT / "source" / "portraits" / "reference"
BRUTS = ROOT / "source" / "portraits" / "essais_generateur"
MAX_COLOURS = 15

# Pokémon traités, avec la description que le générateur reçoit.
SUJETS = {
    "0186": ("politoed", "Politoed", "green frog Pokemon"),
    "0297": ("hariyama", "Hariyama", "orange sumo wrestler Pokemon"),
    "0424": ("ambipom", "Ambipom", "purple monkey Pokemon"),
    "0923": ("pawmot", "Pawmot", "orange rodent Pokemon"),
}

# Émotions demandées au générateur, avec la consigne d'expression.
EXPRESSIONS = {
    "Happy": "eyes closed into upward arcs, cheerful smile",
    "Angry": "eyes narrowed into a frown, brows lowered",
    "Sad": "eyes looking down, drooping brows",
    "Surprised": "eyes wide open, mouth open in surprise",
    "Crying": "eyes shut tight with tears running down the cheeks",
    "Joyous": "eyes closed happily, wide open smiling mouth",
}


def rabattre(brut: Image.Image, officiel: np.ndarray) -> tuple[np.ndarray, int]:
    """Grille exacte + palette du portrait officiel."""
    petit = np.array(brut.convert("RGB").resize((SIZE, SIZE), Image.BOX)).astype(int)
    brutes = len({tuple(int(v) for v in c) for c in petit.reshape(-1, 3)})
    pal = np.array(sorted({tuple(int(v) for v in c) for c in officiel.reshape(-1, 3)}))
    d = ((petit.reshape(-1, 3)[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    return pal[d.argmin(1)].reshape(SIZE, SIZE, 3), brutes


def fond_canonique(rgb: np.ndarray, bg: np.ndarray, emotion: str) -> None:
    """Repeint le décor aux couleurs officielles de l'émotion, en place."""
    ciel, sol = BACKGROUNDS[emotion]
    ys, xs = np.nonzero(bg)
    for y, x in zip(ys, xs):
        if y < HORIZON:
            rgb[y, x] = ciel
        elif y < HORIZON + DAMIER:
            rgb[y, x] = ciel if (x + y) % 2 == 0 else sol
        else:
            rgb[y, x] = sol


def composer(num: str, emotion: str) -> tuple[np.ndarray, dict] | None:
    """Assemble le portrait final : personnage du générateur + fond canonique."""
    brut_path = BRUTS / f"{num}_{emotion}.png"
    if not brut_path.is_file():
        return None
    officiel = load(REF / num / "Normal.png")
    bg = background_mask(officiel)
    snap, brutes = rabattre(Image.open(brut_path), officiel)

    out = np.dstack([officiel.copy(), np.full((SIZE, SIZE, 1), 255, np.uint8)])
    perso = ~bg
    out[:, :, :3] = np.where(perso[:, :, None], snap, officiel)      # personnage : générateur
    fond_canonique(out[:, :, :3], bg, emotion)                        # fond : canonique

    garde = int((snap[perso] == officiel[perso]).all(1).sum())
    couleurs = len({tuple(int(v) for v in c) for c in out[:, :, :3].reshape(-1, 3)})
    return out, {"couleurs_brutes": brutes, "couleurs": couleurs,
                 "personnage_conserve": round(100 * garde / int(perso.sum()), 1),
                 "pixels_personnage": int(perso.sum())}


def police(t: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", t)
    except OSError:
        return ImageFont.load_default()


def planche(num: str, faits: dict, path: Path) -> None:
    dossier, label, _ = SUJETS[num]
    Z = 5
    noms = list(faits)
    largeur = (len(noms) + 1) * (SIZE + 2) * Z + 12
    img = Image.new("RGBA", (largeur, SIZE * Z + 64), (26, 26, 46, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 8), f"{label.upper()} #{num} — PORTRAITS PRODUITS PAR GÉNÉRATEUR D'IMAGES",
           fill=(240, 240, 240, 255), font=police(15))
    d.text((10, 28), "expression du générateur, palette et fond canoniques imposés",
           fill=(165, 165, 195, 255), font=police(11))
    officiel = load(REF / num / "Normal.png")
    img.alpha_composite(Image.fromarray(officiel, "RGB").convert("RGBA")
                        .resize((SIZE * Z, SIZE * Z), Image.NEAREST), (10, 48))
    d.text((12, 48 + SIZE * Z + 1), "Normal (officiel)", fill=(200, 200, 220, 255), font=police(10))
    for k, nom in enumerate(noms):
        cell = Image.open(ROOT / "portraits" / dossier / "emotions_generateur" / f"{nom}.png")
        img.alpha_composite(cell.resize((SIZE * Z, SIZE * Z), Image.NEAREST),
                            (10 + (k + 1) * (SIZE + 2) * Z, 48))
        d.text((12 + (k + 1) * (SIZE + 2) * Z, 48 + SIZE * Z + 1),
               f"{nom} {faits[nom]['personnage_conserve']}%", fill=(200, 200, 220, 255), font=police(10))
    img.save(path, optimize=True)


def main() -> None:
    rapport = {}
    for num, (dossier, label, _) in SUJETS.items():
        out_dir = ROOT / "portraits" / dossier / "emotions_generateur"
        out_dir.mkdir(parents=True, exist_ok=True)
        faits = {}
        for emotion in EXPRESSIONS:
            r = composer(num, emotion)
            if r is None:
                continue
            image, mesures = r
            assert mesures["couleurs"] <= MAX_COLOURS, \
                f"#{num} {emotion} : {mesures['couleurs']} couleurs"
            Image.fromarray(image, "RGBA").save(out_dir / f"{emotion}.png", optimize=True)
            Image.fromarray(image[:, ::-1], "RGBA").save(out_dir / f"{emotion}^.png", optimize=True)
            faits[emotion] = mesures
        if not faits:
            continue
        planche(num, faits, out_dir / "apercu.png")
        (out_dir / "kit.json").write_text(json.dumps(
            {"pokemon": {"nom": label, "numero": num},
             "demarche": "expression produite par générateur d'images ; palette du portrait "
                         "officiel et fond canonique de l'émotion imposés",
             "emotions": faits}, ensure_ascii=False, indent=1), encoding="utf-8")
        origine = REF / num / "credits.txt"
        (out_dir / "credits.txt").write_text(
            (origine.read_text(encoding="utf-8").strip() if origine.is_file() else "") + "\n"
            + "2026-09-07 00:00:00.000000\tGuilde Treehouse — expressions produites par générateur "
              "d'images\tCUR\tUnspecified\t" + ",".join(sorted(faits)) + "\n"
              "Palette du portrait officiel et fonds canoniques imposés après génération.\n"
              "Ces portraits n'ont été ni soumis ni approuvés sur SpriteCollab.\n", encoding="utf-8")
        rapport[num] = {"nom": label, "emotions": faits}
        moy = sum(m["personnage_conserve"] for m in faits.values()) / len(faits)
        print(f"#{num} {label:10s} : {len(faits)} émotions (+ miroirs), "
              f"personnage conservé {moy:.1f} % en moyenne → {out_dir.relative_to(ROOT)}")
    BRUTS.mkdir(parents=True, exist_ok=True)
    (BRUTS / "rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                        encoding="utf-8")


if __name__ == "__main__":
    main()
