#!/usr/bin/env python3
"""Terapagos Terastal — planche de 20 expressions à **base verrouillée**.

Cahier des charges de l'utilisateur : « fidélité 100 sur 100 ». Une seule tête de base, qui ne
bouge pas d'un pixel entre deux cases ; seule l'expression change ; fond strictement identique ;
vrai pixel art, palette figée.

────────────────────────────────────────────────────────────────────────────────
POURQUOI CE N'EST PAS LE GÉNÉRATEUR QUI DESSINE
────────────────────────────────────────────────────────────────────────────────
Mesuré sur mes propres sorties de générateur pour ce Pokémon : la silhouette se déplaçait sur
2 émotions sur 7 (jusqu'à 71 pixels d'écart), et 12 à 34 % de l'image changeait à chaque fois.
Un générateur d'images ne peut pas garantir « pas un pixel de la tête ne bouge » : il redessine.

Ici, la garantie est **structurelle** : le script part de la case officielle, la copie, et ne
réécrit que les pixels d'une petite boîte autour de l'œil. Tout le reste est le même tableau
d'octets. Il n'y a donc rien à vérifier a posteriori sur la tête — elle ne peut pas différer.

────────────────────────────────────────────────────────────────────────────────
ANATOMIE, RELEVÉE SUR LA CASE OFFICIELLE
────────────────────────────────────────────────────────────────────────────────
Le portrait `Normal` de la forme Terastal (`1024/0001`) montre la tête de trois quarts, un seul
œil visible, la carapace en facettes de cristal occupant tout le haut du cadre.

Dump de la zone (x 10..18, y 21..32), lettres = couleurs de la palette :

        012345678          a contour bleu nuit   m blanc de l'œil
    24  ajbieadba          j liseré rose         b iris cyan
    25  ajimbbaca          i turquoise très clair
    26  ajmbeiadb          e turquoise
    27  acmeembab
    28  cdiimmbac
    29  aaemembda

    œil            x 12..16, y 24..29   ovale blanc `m` + iris cyan `b`, cerné de `a`
    liseré rose    x 11,     y 22..31   la bande `j` qui borde l'œil côté museau
    palette        13 couleurs, dont `a` #303f4d, `m` #ffffff, `b` #31a5ce

Les 20 expressions sont dessinées **dans cette boîte de 8 × 8** et nulle part ailleurs. C'est
étroit, et c'est justement la contrainte : sur un portrait PMD de trois quarts, tout se joue
dans l'œil.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "portraits"))
from build_portraits_manquants import SIZE, load                     # noqa: E402

NUM = "1024_0001"
REF = ROOT / "source" / "portraits" / "reference" / NUM
OUT = ROOT / "portraits" / "terapagos_terastal" / "planche_verrouillee"

# Boîte de l'œil : la seule zone que le script a le droit de réécrire.
OEIL_X, OEIL_Y, OEIL_W, OEIL_H = 12, 23, 6, 8

# Rôles de couleur, relevés sur la case officielle. Aucune teinte n'est inventée : le
# constructeur refuse au démarrage toute couleur absente du portrait `Normal`.
ROLES = {
    "a": "#303f4d",   # contour bleu nuit
    "b": "#31a5ce",   # iris cyan
    "c": "#457ebb",   # bleu moyen
    "d": "#5051a0",   # bleu-violet (chair sous l'œil)
    "e": "#6addbf",   # turquoise clair
    "g": "#77c7d7",   # cyan pâle
    "j": "#dd4e97",   # rose vif (liseré du coin de l'œil)
    "k": "#ee919c",   # rose pâle (rougeur, larme rosée)
    "m": "#ffffff",   # blanc de l'œil / reflet
}

# ---------------------------------------------------------------------------
# LES VINGT EXPRESSIONS
#
# Grille de 9 × 10 posée en (OEIL_X, OEIL_Y). Un espace = garder le pixel d'origine, ce qui
# permet de ne toucher qu'une partie de la boîte. Les dessins ne changent que la forme de la
# paupière, la position de la pupille et les petits signes (larme, goutte, rougeur) — jamais
# le contour de la tête, qui est hors boîte.
# ---------------------------------------------------------------------------
NORMAL = [
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
    "         ",
]

def _grille(lignes: list[str]) -> list[str]:
    """Complète une grille à 9 × 10 pour que les dessins restent lisibles à l'écriture."""
    out = [(l + " " * OEIL_W)[:OEIL_W] for l in lignes]
    while len(out) < OEIL_H:
        out.append(" " * OEIL_W)
    return out[:OEIL_H]


EXPRESSIONS: dict[str, list[str]] = {
    # 1. repos — la case officielle, non retouchée
    "Normal": _grille(NORMAL),

    # 2. heureux — la paupière se ferme, l'œil devient un arc vers le haut
    "Heureux": _grille([
        "      ",
        " aaa  ",
        "ammma ",
        "aaaaa ",
    ]),
    # 3. très heureux — arc plus franc et plus large
    "Tres_heureux": _grille([
        "      ",
        "aaaaa ",
        "ammmma",
        "aaaaa ",
        " aa   ",
    ]),
    # 4. triste — paupière haute abaissée, iris poussé vers le bas
    "Triste": _grille([
        " aaa  ",
        "aaaaa ",
        "ammma ",
        "ambma ",
        "ammma ",
        " aaa  ",
    ]),
    # 5. en colère — paupière inclinée depuis le haut, iris resserré
    "En_colere": _grille([
        "aa    ",
        "aaaa  ",
        "ambba ",
        "ammma ",
        " aaa  ",
    ]),
    # 6. très en colère — paupière très basse, iris réduit à un point
    "Tres_en_colere": _grille([
        "aaa   ",
        "aaaaa ",
        "abbba ",
        "ammma ",
        " aaa  ",
    ]),
    # 7. surpris — œil grand ouvert, iris petit et flottant
    "Surpris": _grille([
        " aaa  ",
        "ammma ",
        "ambma ",
        "ammma ",
        "ammma ",
        " aaa  ",
    ]),
    # 8. choqué — œil écarquillé au maximum, iris minuscule
    "Choque": _grille([
        " aaa  ",
        "ammma ",
        "ammma ",
        "ambma ",
        "ammma ",
        "ammma ",
        " aaa  ",
    ]),
    # 9. effrayé — pupille remontée, blanc visible dessous
    "Effraye": _grille([
        " aaa  ",
        "ambma ",
        "ammma ",
        "ammma ",
        "ammma ",
        " aaa  ",
    ]),
    # 10. inquiet — paupière haute relevée d'un côté, regard oblique
    "Inquiet": _grille([
        " aa   ",
        "aamma ",
        "ambma ",
        "ammma ",
        " aaa  ",
    ]),
    # 11. confus — iris décalé vers le coin, paupières inégales
    "Confus": _grille([
        " aaa  ",
        "ammma ",
        "abbma ",
        "ammma ",
        " aaa  ",
    ]),
    # 12. pensif — œil mi-clos, regard levé
    "Pensif": _grille([
        "      ",
        " aaa  ",
        "ambma ",
        "aaaaa ",
    ]),
    # 13. déterminé — paupière basse et droite, iris franc et centré
    "Determine": _grille([
        "aaaa  ",
        "aaaaa ",
        "ambma ",
        "ammma ",
        " aaa  ",
    ]),
    # 14. combatif — sourcil très abaissé, iris large et brillant
    "Combatif": _grille([
        "aaaa  ",
        "aaaaa ",
        "abbba ",
        "ambma ",
        " aaa  ",
    ]),
    # 15. fatigué — paupière à mi-hauteur, regard éteint
    "Fatigue": _grille([
        "      ",
        "aaaaa ",
        "aaaaa ",
        "ambma ",
        " aaa  ",
    ]),
    # 16. endormi — œil clos, simple trait
    "Endormi": _grille([
        "      ",
        "      ",
        "aaaaa ",
        " aaa  ",
    ]),
    # 17. gêné — œil mi-clos détourné, rougeur sous l'œil
    "Gene": _grille([
        "      ",
        " aaa  ",
        "ambma ",
        "aaaaa ",
        " kk   ",
    ]),
    # 18. embarrassé — regard fuyant vers le bas, rougeur plus large
    "Embarrasse": _grille([
        "      ",
        " aaa  ",
        "ammma ",
        "abbma ",
        " aaa  ",
        "kkk   ",
    ]),
    # 19. douleur — œil serré, larme qui coule
    "Douleur": _grille([
        "      ",
        "aaaaa ",
        "ammma ",
        " aaa  ",
        "  b   ",
        "  b   ",
    ]),
    # 20. déçu — paupière tombante, coin extérieur abaissé
    "Decu": _grille([
        "      ",
        "aaaa  ",
        "ammaa ",
        "ambma ",
        " aaa  ",
    ]),
}


def peindre(base: np.ndarray, dessin: list[str], roles: dict) -> np.ndarray:
    """Applique un dessin dans la boîte de l'œil. Le reste du tableau n'est pas touché."""
    out = base.copy()
    for j, ligne in enumerate(dessin):
        for i, sym in enumerate(ligne):
            if sym == " ":
                continue
            y, x = OEIL_Y + j, OEIL_X + i
            if 0 <= y < SIZE and 0 <= x < SIZE:
                out[y, x] = roles[sym]
    return out


def police(t: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", t)
    except OSError:
        return ImageFont.load_default()


def planche_contact(images: dict, path: Path) -> None:
    Z = 5
    cols = 5
    lignes = (len(images) + cols - 1) // cols
    img = Image.new("RGBA", (cols * (SIZE + 3) * Z, lignes * ((SIZE + 3) * Z + 12) + 40),
                    (26, 26, 46, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 8), "TERAPAGOS TERASTAL — 20 EXPRESSIONS, BASE VERROUILLÉE",
           fill=(240, 240, 240, 255), font=police(16))
    d.text((10, 26), "une seule tête de base ; seule la boîte de l'œil est redessinée",
           fill=(165, 165, 195, 255), font=police(11))
    for k, (nom, arr) in enumerate(images.items()):
        cx = (k % cols) * (SIZE + 3) * Z
        cy = 40 + (k // cols) * ((SIZE + 3) * Z + 12)
        img.alpha_composite(Image.fromarray(arr, "RGB").convert("RGBA")
                            .resize((SIZE * Z, SIZE * Z), Image.NEAREST), (cx + 6, cy))
        d.text((cx + 6, cy + SIZE * Z + 1), nom.replace("_", " "),
               fill=(215, 215, 235, 255), font=police(10))
    img.save(path, optimize=True)


# Correspondance vers les noms d'émotion officiels de SpriteCollab, pour produire aussi une
# planche 200 × 320 déposable. Les expressions du brief qui n'ont pas d'équivalent officiel
# (Très heureux, Très en colère, Choqué, Effrayé, Confus, Pensif, Combatif, Fatigué, Endormi,
# Gêné, Embarrassé, Déçu) restent dans la planche de 20 mais n'entrent pas dans celle du dépôt.
VERS_OFFICIEL = {
    "Normal": "Normal", "Heureux": "Happy", "Triste": "Sad", "En_colere": "Angry",
    "Surpris": "Surprised", "Inquiet": "Worried", "Determine": "Determined",
    "Douleur": "Pain", "Tres_heureux": "Joyous", "Fatigue": "Sigh", "Choque": "Stunned",
    "Embarrasse": "Teary-Eyed", "Confus": "Dizzy", "Combatif": "Shouting",
    "Endormi": "Crying", "Gene": "Inspired",
}
ORDRE_SPRITEBOT = ["Normal", "Happy", "Pain", "Angry", "Worried",
                   "Sad", "Crying", "Shouting", "Teary-Eyed", "Determined",
                   "Joyous", "Inspired", "Surprised", "Dizzy", "Special0",
                   "Special1", "Sigh", "Stunned", "Special2", "Special3"]


def planche_spritebot(images: dict, path: Path) -> int:
    """Planche 200 × 320 au format du dépôt : émotions en haut, miroirs `^` en bas."""
    feuille = Image.new("RGBA", (5 * SIZE, 8 * SIZE), (0, 0, 0, 0))
    n = 0
    inverse = {v: k for k, v in VERS_OFFICIEL.items()}
    for i, officiel in enumerate(ORDRE_SPRITEBOT):
        interne = inverse.get(officiel)
        if interne is None or interne not in images:
            continue
        cx, cy = (i % 5) * SIZE, (i // 5) * SIZE
        img = Image.fromarray(images[interne], "RGB").convert("RGBA")
        feuille.alpha_composite(img, (cx, cy))
        feuille.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT), (cx, cy + 4 * SIZE))
        n += 1
    feuille.save(path, optimize=True)
    return n


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = load(REF / "Normal.png")
    palette = {tuple(int(v) for v in c) for c in base.reshape(-1, 3)}
    roles = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in ROLES.items()}
    hors = set(roles.values()) - palette
    assert not hors, f"couleurs hors palette du portrait officiel : {hors}"

    images, mesures = {}, {}
    for nom, dessin in EXPRESSIONS.items():
        arr = peindre(base, dessin, roles)
        # garde-fou : hors de la boîte de l'œil, l'image DOIT être identique à la base
        masque = np.ones((SIZE, SIZE), bool)
        masque[OEIL_Y:OEIL_Y + OEIL_H, OEIL_X:OEIL_X + OEIL_W] = False
        assert np.array_equal(arr[masque], base[masque]), f"{nom} : la base a bougé"
        couleurs = len({tuple(int(v) for v in c) for c in arr.reshape(-1, 3)})
        assert couleurs <= 15, f"{nom} : {couleurs} couleurs"
        Image.fromarray(arr, "RGB").convert("RGBA").save(OUT / f"{nom}.png", optimize=True)
        Image.fromarray(arr[:, ::-1], "RGB").convert("RGBA").save(OUT / f"{nom}^.png", optimize=True)
        images[nom] = arr
        mesures[nom] = {"couleurs": couleurs,
                        "pixels_modifies": int(np.any(arr != base, axis=2).sum())}

    planche_contact(images, OUT / "apercu.png")
    nb = planche_spritebot(images, OUT / "planche_spritebot.png")
    officiel = OUT / "format_spritecollab"
    officiel.mkdir(exist_ok=True)
    for interne, nom_off in VERS_OFFICIEL.items():
        arr = images[interne]
        Image.fromarray(arr, "RGB").convert("RGBA").save(officiel / f"{nom_off}.png", optimize=True)
        Image.fromarray(arr[:, ::-1], "RGB").convert("RGBA").save(
            officiel / f"{nom_off}^.png", optimize=True)
    (officiel / "credits.txt").write_text(
        ((REF / "credits.txt").read_text(encoding="utf-8").strip()
         if (REF / "credits.txt").is_file() else "") + "\n"
        + "2026-09-07 00:00:00.000000\tGuilde Treehouse — expressions à base verrouillée"
          "\tCUR\tUnspecified\t" + ",".join(sorted(VERS_OFFICIEL.values())) + "\n"
          "Seule la boîte de l'œil est redessinée ; la tête est celle du portrait officiel.\n"
          "Ni soumis ni approuvé sur SpriteCollab.\n", encoding="utf-8")
    print(f"   planche SpriteBot : {nb} émotions → {officiel.relative_to(ROOT)}")
    (OUT / "kit.json").write_text(json.dumps(
        {"pokemon": {"nom": "Terapagos Terastal", "numero": "1024", "forme": "0001"},
         "demarche": "base verrouillée : seule la boîte de l'œil est redessinée",
         "boite_oeil": {"x": OEIL_X, "y": OEIL_Y, "w": OEIL_W, "h": OEIL_H},
         "roles_de_couleur": ROLES, "palette_officielle": len(palette),
         "expressions": mesures}, ensure_ascii=False, indent=1), encoding="utf-8")
    origine = REF / "credits.txt"
    (OUT / "credits.txt").write_text(
        (origine.read_text(encoding="utf-8").strip() if origine.is_file() else "") + "\n"
        + "2026-09-07 00:00:00.000000\tGuilde Treehouse — 20 expressions à base verrouillée"
          "\tCUR\tUnspecified\t" + ",".join(EXPRESSIONS) + "\n"
          "Seule la boîte de l'œil est redessinée ; la tête est celle du portrait officiel.\n"
          "Ni soumis ni approuvé sur SpriteCollab.\n", encoding="utf-8")

    moy = sum(m["pixels_modifies"] for m in mesures.values()) / len(mesures)
    print(f"Terapagos Terastal : {len(images)} expressions (+ miroirs), "
          f"{moy:.0f} pixels modifiés en moyenne sur 1600 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
