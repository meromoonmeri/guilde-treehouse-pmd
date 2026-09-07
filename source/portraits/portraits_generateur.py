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
3. **Deux couches séparées** (architecture proposée par l'utilisateur, et elle est la bonne) :

   * **couche 1, le fond** — entièrement reconstruit par code aux couleurs canoniques de
     l'émotion. Vérifié : sur les 245 pixels de décor visibles dans les coins d'un portrait
     officiel, la reconstruction est **identique au pixel près** (245/245). Le générateur
     n'a donc rien à apporter ici, et on ne le lui demande pas.
   * **couche 2, le personnage** — découpé dans la sortie du générateur, puis posé par-dessus.

   Le découpage se fait par les **teintes de décor du portrait officiel** (celles qui occupent
   son fond et que le personnage n'emploie jamais) : tout pixel qui les porte est du fond,
   qu'il touche le bord ou non. C'est ce dernier point qui compte — les poches de ciel
   enfermées entre les oreilles de Capidextre ne sont reliées à aucun bord, et une simple
   propagation depuis le cadre les laissait en place. C'était le défaut visible signalé.
4. **Miroir `^`** produit par retournement exact, comme l'exige le format.

Ce qui reste du générateur : l'**expression** seule. Le fond, la palette et la géométrie sont
imposés par le code.

"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from scipy import ndimage                        # noqa: E402
from build_portraits_manquants import (          # noqa: E402
    BACKGROUNDS, DAMIER, HORIZON, SIZE, background_mask, load,
)

REF = ROOT / "source" / "portraits" / "reference"
BRUTS = ROOT / "source" / "portraits" / "essais_generateur"
MAX_COLOURS = 15

# Pokémon traités, avec la description que le générateur reçoit.
SUJETS = {
    "0424": ("ambipom", "Ambipom (Capidextre)", "purple monkey Pokemon"),
    "0297": ("hariyama", "Hariyama", "orange sumo wrestler Pokemon"),
}

# Émotions demandées au générateur, avec la consigne d'expression.
# Les émotions demandées au générateur. `Normal`, `Happy` et `Surprised` sont déjà publiées sur
# PMDCollab pour ce Pokémon : elles sont reprises **telles quelles**, jamais régénérées.
# Émotions retenues **par Pokémon**, après revue de l'utilisateur. Sur Capidextre, dix
# expressions ont été produites et deux seulement validées : `Inspired` (yeux pétillants) et
# `Teary-Eyed` (yeux embués). Les huit autres ont été jugées « ça fait IA » et sont écartées —
# le générateur lisse les traits et perd le style Chunsoft dès que l'expression est appuyée.
RETENUES = {
    "0424": ["Inspired", "Teary-Eyed"],
    "0297": ["Happy", "Angry"],
}

EXPRESSIONS = {
    "Angry": "fierce glaring eyes, heavy lowered brows, teeth bared",
    "Happy": "eyes closed into cheerful upward arcs, broad open smile",
    "Teary-Eyed": "big watery shining eyes brimming with tears",
    "Inspired": "bright sparkling wide eyes looking up",
}


def rabattre(brut: Image.Image, officiel: np.ndarray) -> tuple[np.ndarray, int]:
    """Grille exacte + palette du portrait officiel."""
    petit = np.array(brut.convert("RGB").resize((SIZE, SIZE), Image.BOX)).astype(int)
    brutes = len({tuple(int(v) for v in c) for c in petit.reshape(-1, 3)})
    pal = np.array(sorted({tuple(int(v) for v in c) for c in officiel.reshape(-1, 3)}))
    d = ((petit.reshape(-1, 3)[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    return pal[d.argmin(1)].reshape(SIZE, SIZE, 3), brutes


def decor_du_portrait(officiel: np.ndarray) -> set[tuple]:
    """Teintes qui servent au décor du portrait officiel et **jamais** au personnage.

    Ce sont elles qui permettent de découper la sortie du générateur : il reprend le ciel du
    `Normal` qu'on lui a donné, donc tout pixel portant une de ces teintes est du fond.
    """
    bg = background_mask(officiel)
    au_fond = {tuple(int(v) for v in c) for c in officiel[bg].reshape(-1, 3)}
    au_perso = {tuple(int(v) for v in c) for c in officiel[~bg].reshape(-1, 3)}
    return au_fond - au_perso


def fond_pur(emotion: str) -> np.ndarray:
    """Couche 1 : le fond canonique seul, sans personnage — reconstruit entièrement par code."""
    ciel, sol = BACKGROUNDS[emotion]
    a = np.zeros((SIZE, SIZE, 3), np.uint8)
    for y in range(SIZE):
        for x in range(SIZE):
            if y < HORIZON:
                a[y, x] = ciel
            elif y >= HORIZON + DAMIER:
                a[y, x] = sol
            else:
                a[y, x] = ciel if (x + y) % 2 == 0 else sol
    return a


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
    snap, brutes = rabattre(Image.open(brut_path), officiel)
    # Couche 2 : le personnage, découpé dans la sortie du générateur. Tout pixel portant une
    # teinte de décor du portrait officiel appartient au fond — y compris les poches enfermées
    # (entre les oreilles de Capidextre par exemple), qu'une propagation depuis le bord raterait.
    teintes = decor_du_portrait(officiel)
    decor = np.zeros((SIZE, SIZE), bool)
    for couleur in teintes:
        decor |= np.all(snap == couleur, axis=2)
    perso = ~decor

    out = np.dstack([fond_pur(emotion), np.full((SIZE, SIZE, 1), 255, np.uint8)])
    out[perso, :3] = snap[perso]

    # Le fond canonique ajoute ses deux teintes : sur certaines émotions la planche passe à 16
    # alors que le SpriteBot en accepte 15. On rabat alors les couleurs les plus rares du
    # personnage sur leur voisine la plus proche — quelques pixels, invisible à l'œil.
    rabattues = []
    while True:
        uniq, cnt = np.unique(out[:, :, :3].reshape(-1, 3), axis=0, return_counts=True)
        if len(uniq) <= MAX_COLOURS:
            break
        protegees = set(BACKGROUNDS[emotion])
        ordre = np.argsort(cnt)
        rare = next(tuple(int(v) for v in uniq[i]) for i in ordre
                    if tuple(int(v) for v in uniq[i]) not in protegees)
        autres = [tuple(int(v) for v in uniq[i]) for i in ordre
                  if tuple(int(v) for v in uniq[i]) != rare]
        proche = min(autres, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, rare)))
        m = np.all(out[:, :, :3] == rare, axis=2)
        out[m, :3] = proche
        rabattues.append({"de": "#%02x%02x%02x" % rare, "vers": "#%02x%02x%02x" % proche,
                          "pixels": int(m.sum())})

    garde = int((snap[perso] == officiel[perso]).all(1).sum())  # fidélité indicative
    couleurs = len({tuple(int(v) for v in c) for c in out[:, :, :3].reshape(-1, 3)})
    return out, {"couleurs_brutes": brutes, "couleurs": couleurs,
                 "personnage_conserve": round(100 * garde / int(perso.sum()), 1),
                 "pixels_personnage": int(perso.sum()), "couleurs_rabattues": rabattues}


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


# Ordre officiel des 20 cases de la planche SpriteBot (5 colonnes × 4 rangées ; la moitié basse
# reprend les versions retournées « ^ »). Les cases `Special` restent vides.
ORDRE = ["Normal", "Happy", "Pain", "Angry", "Worried",
         "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
         "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
         "Special1", "Sigh", "Stunned", "Special2", "Special3"]


def planche_spritebot(dossier: str, dispo: dict, path: Path) -> int:
    """Planche 200 × 320 au format SpriteBot : émotions en haut, miroirs `^` en bas."""
    feuille = Image.new("RGBA", (5 * SIZE, 8 * SIZE), (0, 0, 0, 0))
    n = 0
    for i, nom in enumerate(ORDRE):
        if nom.startswith("Special") or nom not in dispo:
            continue
        cx, cy = (i % 5) * SIZE, (i // 5) * SIZE
        img = Image.open(dispo[nom]).convert("RGBA")
        feuille.alpha_composite(img, (cx, cy))
        feuille.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT), (cx, cy + 4 * SIZE))
        n += 1
    feuille.save(path, optimize=True)
    return n


def main() -> None:
    rapport = {}
    for num, (dossier, label, _) in SUJETS.items():
        out_dir = ROOT / "portraits" / dossier / "emotions_generateur"
        out_dir.mkdir(parents=True, exist_ok=True)
        faits = {}
        for emotion in RETENUES.get(num, []):
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
        # --- assemblage au format officiel -----------------------------------------
        # Les émotions déjà publiées sur PMDCollab sont reprises **octet pour octet** ; seules
        # les manquantes viennent du générateur. C'est ce dossier qui part à l'export.
        officiel_dir = ROOT / "portraits" / dossier / "emotions_officielles"
        officiel_dir.mkdir(parents=True, exist_ok=True)
        dispo = {}
        for nom in ORDRE:
            if nom.startswith("Special"):
                continue
            src_off = REF / num / f"{nom}.png"
            # une émotion générée n'entre dans la planche que si elle a été RETENUE : les
            # essais écartés restent dans `emotions_generateur/` pour mémoire, hors livraison.
            src_gen = out_dir / f"{nom}.png" if nom in RETENUES.get(num, []) else None
            src = src_off if src_off.is_file() else (src_gen if src_gen and src_gen.is_file() else None)
            if src is None:
                continue
            img = Image.open(src).convert("RGBA")
            img.save(officiel_dir / f"{nom}.png", optimize=True)
            img.transpose(Image.FLIP_LEFT_RIGHT).save(officiel_dir / f"{nom}^.png", optimize=True)
            dispo[nom] = officiel_dir / f"{nom}.png"
        nb = planche_spritebot(dossier, dispo, officiel_dir / "planche_spritebot.png")
        faits_off = sorted(set(dispo) & {p.stem for p in (REF / num).glob("*.png")})
        origine = REF / num / "credits.txt"
        (officiel_dir / "credits.txt").write_text(
            (origine.read_text(encoding="utf-8").strip() if origine.is_file() else "") + "\n"
            + "2026-09-07 00:00:00.000000\tGuilde Treehouse — émotions manquantes produites par "
              "générateur d'images\tCUR\tUnspecified\t"
            + ",".join(sorted(set(dispo) - set(faits_off))) + "\n"
              "Palette du portrait officiel et fonds canoniques imposés après génération.\n"
              "Émotions déjà publiées reprises à l'identique. Ni soumis ni approuvé sur SpriteCollab.\n",
            encoding="utf-8")
        print(f"   planche officielle : {nb} émotions ({len(faits_off)} officielles reprises) "
              f"→ {officiel_dir.relative_to(ROOT)}")

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
