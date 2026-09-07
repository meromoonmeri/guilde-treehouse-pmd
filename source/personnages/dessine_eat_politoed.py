#!/usr/bin/env python3
"""Politoed #0186 — un `Eat` **dessiné**, à la manière des artistes Chunsoft.

Les étapes précédentes déplaçaient des pixels existants. Ici on franchit le pas : on **dessine
des pixels neufs**, comme le fait un artiste de SpriteCollab. La règle n'est plus « ne rien
repeindre », mais « repeindre en respectant exactement la grammaire du sprite ».

────────────────────────────────────────────────────────────────────────────────
CE QUE FONT LES ARTISTES, RELEVÉ SUR L'`Eat` DE PICHU #0172
────────────────────────────────────────────────────────────────────────────────
Comparaison caractère par caractère du visage de Pichu au repos et pendant la bouchée
(`a` = noir, `b` = jaune clair, `c` = jaune moyen, `d` = ombre, `g` = rouge du museau) :

    repos                      bouchée
    ...acadbbbbbadca....       ..ahabbbbbbbaaaa....
    ...aeebbcgcbbeea....       ..aadbbbbbbbbca.....
    ...agebbgggbbega....       ..aebbbbbhabbca.....
    ....accbgegbcca.....       ..agaafbbadbbda.....
    ....aafcccccfaa.....       ...abbafbbeeca......
    ...acbcaaaaacbca....       ...acaccccegafa.....

Quatre règles s'en dégagent, et ce sont elles qu'on applique :

1. **La palette ne s'élargit jamais.** Pas une seule couleur nouvelle n'apparaît dans la
   bouchée : l'artiste repeint avec les teintes déjà présentes dans le sprite.
2. **Tout trait est cerné de noir.** La silhouette et les ouvertures gardent leur contour
   `(0,0,0)` — c'est la signature visuelle de la série.
3. **L'ombrage est ordonné.** Sous une surface claire on trouve la teinte moyenne, puis la
   sombre : jamais un clair collé à un sombre sans intermédiaire.
4. **Le changement est local et asymétrique.** Seule la zone concernée (ici la tête) est
   redessinée ; le reste de la case est repris tel quel, et l'artiste décale légèrement d'un
   côté pour éviter la symétrie mécanique.

────────────────────────────────────────────────────────────────────────────────
CE QUI EST DESSINÉ ICI
────────────────────────────────────────────────────────────────────────────────
Politoed a une **grande bouche fermée** : le trait noir de `y=16, x=9..13` dans la boîte de sa
case Idle, bordé de la lèvre jaune. Un Politoed qui mange ouvre grand cette bouche — c'est le
trait le plus caractéristique du personnage, et c'est exactement ce qu'un artiste dessinerait.

Trois états de bouche sont dessinés à la main, en pixel art, dans la palette du sprite :
`fermee` (l'original), `entrouverte`, `grande_ouverte` (avec langue et fond de gorge).
Les mains montent en même temps, avec le mécanisme de `build_animations_scenes.py`.

Sortie : `personnages/politoed/eat_dessine/`, dossier SpriteCollab complet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                                       # noqa: E402
from rebuild_kit import night                                # noqa: E402
from build_animations_scenes import HANDS_TO_MOUTH, move_limbs, physiology, step_limbs, Step  # noqa: E402

NUM = "0186"
REF = ROOT / "source" / "personnages" / "reference" / NUM
SKELETON = ROOT / "source" / "personnages" / "reference" / "0155"
OUT = ROOT / "personnages" / "politoed" / "eat_dessine"

# ---------------------------------------------------------------------------
# La palette de Politoed, relevée sur sa case Idle. Les noms sont ceux d'un artiste :
# on dessine avec des valeurs (clair / moyen / sombre), pas avec des codes hexadécimaux.
# ---------------------------------------------------------------------------
NOIR = (0, 0, 0)
PEAU_CLAIRE = (159, 207, 111)      # ventre, joues
PEAU = (95, 183, 39)               # corps
PEAU_OMBRE = (39, 135, 0)          # dessous, creux
LEVRE_CLAIRE = (255, 247, 0)       # lèvre jaune éclairée
LEVRE = (223, 183, 0)              # lèvre jaune moyenne
LEVRE_OMBRE = (167, 111, 0)        # lèvre jaune dans l'ombre
GORGE = (159, 0, 0)                # rouge sombre — déjà dans la palette (pupilles)
LANGUE = (215, 63, 0)              # rouge vif — déjà dans la palette (coins des yeux)
BLANC = (255, 255, 255)            # reflets

# Table des symboles utilisés dans les dessins ci-dessous.
ENCRE = {
    ".": None,               # transparent
    " ": "garder",           # ne pas toucher au pixel d'origine
    "a": NOIR,
    "b": PEAU_CLAIRE,
    "c": PEAU,
    "e": PEAU_OMBRE,
    "d": LEVRE_CLAIRE,
    "f": LEVRE,
    "i": LEVRE_OMBRE,
    "j": GORGE,
    "m": LANGUE,
    "h": BLANC,
}

# ---------------------------------------------------------------------------
# LES DESSINS
#
# Chaque bloc est posé dans la boîte de la case Idle, coin haut-gauche en (ORIGINE_X, ORIGINE_Y).
# Largeur 9 (x = 7..15), hauteur 7 (y = 14..20) : la zone de la bouche et du menton.
# L'espace « garder » laisse passer le pixel d'origine — on ne redessine que le nécessaire,
# comme le fait Chunsoft.
# ---------------------------------------------------------------------------
# La bouche fermée de Politoed est le trait noir de `y=16, x=9..13`, souligné par la lèvre
# jaune claire de `y=15, x=10..12`. La zone jaune en dessous est sa gorge/son ventre : c'est
# donc là que la bouche s'ouvre, ce qui est anatomiquement juste pour ce personnage.
# Les dessins sont posés à partir de (ORIGINE_X, ORIGINE_Y), sur 7 pixels de large.
ORIGINE_X, ORIGINE_Y = 8, 15

# État de repos : rien n'est redessiné, l'original passe tel quel (témoin du vérificateur).
BOUCHE_FERMEE = [
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
]

# Entrouverte : le trait de la bouche s'écarte d'un pixel. La lèvre supérieure garde son
# liseré clair, le fond de gorge apparaît en rouge sombre, la lèvre inférieure revient en
# jaune moyen. Contour noir sur tout le pourtour (règle 2).
BOUCHE_ENTROUVERTE = [
    " ifddfi",
    " aaaaaa",
    " ajjjja",
    " affffa",
    "  aaaa ",
]

# Grande ouverte : la mâchoire descend de deux pixels de plus, la gorge s'ouvre en profondeur
# et la langue apparaît au fond. Ombrage : lèvre claire en haut, gorge sombre, langue vive au
# centre, lèvre moyenne en bas (règle 3). La langue est décalée d'un pixel à gauche pour
# éviter la symétrie mécanique (règle 4).
BOUCHE_GRANDE_OUVERTE = [
    " ifddfi",
    "aaaaaaa",
    "ajjjjja",
    "ajmmjja",
    "aiffffa",
]

DESSINS = {
    "fermee": BOUCHE_FERMEE,
    "entrouverte": BOUCHE_ENTROUVERTE,
    "grande_ouverte": BOUCHE_GRANDE_OUVERTE,
}


def peindre(crop: np.ndarray, dessin: list[str]) -> np.ndarray:
    """Applique un dessin sur la boîte de la case. Aucune couleur hors palette n'est admise."""
    out = crop.copy()
    for j, ligne in enumerate(dessin):
        for i, sym in enumerate(ligne):
            y, x = ORIGINE_Y + j, ORIGINE_X + i
            if not (0 <= y < out.shape[0] and 0 <= x < out.shape[1]):
                continue
            if sym == " ":
                continue
            couleur = ENCRE[sym]
            if couleur is None:
                out[y, x] = (0, 0, 0, 0)
            else:
                out[y, x, :3] = couleur
                out[y, x, 3] = 255
    return out


# ---------------------------------------------------------------------------
# Le plan de l'animation : quatre images, cadence Chunsoft 6/8/6/8.
#   0 — repos, bouche fermée, mains basses
#   1 — la bouche s'ouvre en grand, les mains arrivent : la bouchée
#   2 — retour au repos (la nourriture est avalée)
#   3 — deuxième bouchée, bouche entrouverte : l'artiste ne répète jamais deux fois
#       la même image, il varie l'amplitude pour que le cycle respire
# ---------------------------------------------------------------------------
PLAN = [
    {"bouche": "fermee", "mains": False, "squash": 0},
    {"bouche": "grande_ouverte", "mains": True, "squash": 1},
    {"bouche": "fermee", "mains": False, "squash": 0},
    {"bouche": "entrouverte", "mains": True, "squash": 1},
]


def construire() -> tuple[P.Built, dict]:
    shadow_size, anims = P.load_sprite(REF)
    _, skel = P.load_sprite(SKELETON)
    modele = skel["Eat"]
    amp = physiology(anims["Idle"].frames[0][0].bbox[3] - anims["Idle"].frames[0][0].bbox[1] + 1)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(anims)}

    rows = modele.dirs
    n = len(modele.durations)
    disp = [modele.frames[0][i].disp for i in range(n)]

    dessins_par_image = []
    ext_x = ext_y = 0
    for d in range(rows):
        for i, etape in enumerate(PLAN):
            f = anims["Idle"].frames[min(d, len(anims["Idle"].frames) - 1)][0]
            x0, y0, x1, y1 = f.bbox
            ext_x = max(ext_x, abs(x0 - 2) + abs(disp[i][0]), abs(x1 + 2) + abs(disp[i][0]))
            ext_y = max(ext_y, abs(y0 - 2 + 4), abs(y1 + 2 - 4))
    fw = max(16, ((2 * (ext_x + 1) + 7) // 8) * 8)
    fh = max(16, ((2 * (ext_y + 5) + 7) // 8) * 8)

    built = P.Built("Eat", modele.index, fw, fh, list(modele.durations),
                    notes="bouche dessinée à la main dans la palette du sprite ; cadence #0155")
    for d in range(rows):
        cells, anchors = [], []
        for i, etape in enumerate(PLAN):
            f = anims["Idle"].frames[d][0]
            ax_src, ay_src = f.anchor
            x0, y0, x1, y1 = f.bbox
            crop = f.image[ay_src + y0:ay_src + y1 + 1, ax_src + x0:ax_src + x1 + 1].copy()

            # 1. la bouche est dessinée — uniquement sur la vue de face, seule où elle est visible
            if d == 0 and etape["bouche"] != "fermee":
                crop = peindre(crop, DESSINS[etape["bouche"]])
                dessins_par_image.append((i, etape["bouche"]))
            # 2. les mains montent, avec le mécanisme déjà éprouvé
            if etape["mains"]:
                lbs = step_limbs(Step("Idle", 0, limbs=(HANDS_TO_MOUTH,)), amp)
                crop = move_limbs(crop, (-x0, -y0), f.marks, lbs, f.bbox)

            cx, cy = fw // 2 + disp[i][0], fh // 2 + 4 + disp[i][1]
            cell = np.zeros((fh, fw, 4), np.uint8)
            offs = np.zeros((fh, fw, 4), np.uint8)
            shad = np.zeros((fh, fw, 4), np.uint8)
            h, w = crop.shape[:2]
            px, py = cx + x0, cy + y0 + etape["squash"]
            px, py = max(0, min(px, fw - w)), max(0, min(py, fh - h))
            block = cell[py:py + h, px:px + w]
            mask = crop[:, :, 3] > 0
            block[mask] = crop[mask]

            for key, (mx, my) in f.marks.items():
                x, y = cx + mx, cy + my
                if 0 <= x < fw and 0 <= y < fh:
                    offs[y, x, :3] = np.maximum(offs[y, x, :3], P.MARK_COLOURS[key])
                    offs[y, x, 3] = 255
            gx0, gy0, _, _ = f.shadow_box
            g = f.shadow
            if g.size:
                sx, sy = cx + gx0, cy + gy0
                gh, gw = g.shape[:2]
                if 0 <= sx and sx + gw <= fw and 0 <= sy and sy + gh <= fh:
                    sb = shad[sy:sy + gh, sx:sx + gw]
                    sm = g[:, :, 3] > 0
                    sb[sm] = g[sm]
            shad[cy, cx] = (255, 255, 255, 255)
            cells.append((cell, offs, shad))
            anchors.append((cx, cy))
        built.cells.append(cells)
        built.anchors.append(anchors)

    used: set = set()
    for row in built.cells:
        for c in row:
            used |= {tuple(int(v) for v in p) for p in c[0][c[0][:, :, 3] > 0][:, :3]}
    hors = used - base_palette
    assert not hors, f"couleurs hors palette du sprite : {hors}"
    return built, {"palette_base": len(base_palette), "couleurs_utilisees": len(used)}


def police(taille: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", taille)
    except OSError:
        return ImageFont.load_default()


def planche_dessin(built: P.Built, path: Path) -> None:
    """Planche pédagogique : les trois bouches dessinées, en grand, côte à côte."""
    Z = 16
    cases = [(nom, i) for i, nom in enumerate(["fermee", "grande_ouverte", "entrouverte"])]
    idx = {"fermee": 0, "grande_ouverte": 1, "entrouverte": 3}
    w = built.fw * Z
    img = Image.new("RGBA", (3 * (w + 12) + 12, built.fh * Z + 70), (26, 26, 46, 255))
    d = ImageDraw.Draw(img)
    d.text((12, 10), "POLITOED — LA BOUCHE DESSINÉE À LA MAIN, DANS LA PALETTE DU SPRITE",
           fill=(240, 240, 240, 255), font=police(19))
    d.text((12, 34), "Trois états dessinés en pixel art : contour noir, ombrage clair → moyen → sombre, "
                     "aucune couleur nouvelle.", fill=(170, 170, 200, 255), font=police(12))
    for k, (nom, _) in enumerate(cases):
        cell = Image.fromarray(built.cells[0][idx[nom]][0], "RGBA").resize((w, built.fh * Z), Image.NEAREST)
        tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
        tile.alpha_composite(cell)
        img.alpha_composite(tile, (12 + k * (w + 12), 56))
        d.text((12 + k * (w + 12) + 4, 56 + built.fh * Z + 2), nom, fill=(220, 220, 240, 255), font=police(13))
    img.save(path, optimize=True)


def parquet(size, zoom):
    src = ROOT / "salles" / "01_accueil" / "salle_jour.png"
    bg = Image.new("RGBA", size, (150, 104, 52, 255))
    if src.is_file():
        t = Image.open(src).convert("RGBA").crop((264, 252, 392, 316))
        arr = np.array(t).astype(np.int16)
        arr[:, :, :3] = (arr[:, :, :3] * 0.72).clip(0, 255)
        t = Image.fromarray(arr.astype(np.uint8), "RGBA")
        t = t.resize((t.width * zoom, t.height * zoom), Image.NEAREST)
        for y in range(0, size[1], t.height):
            for x in range(0, size[0], t.width):
                bg.alpha_composite(t, (x, y))
    return bg


def gif(built: P.Built, path: Path, zoom: int = 5) -> None:
    cw, ch = built.fw * zoom + 8, built.fh * zoom + 8
    bg = parquet((cw, ch), zoom)
    frames, durs = [], []
    for i, dv in enumerate(built.durations):
        img = bg.copy()
        cell = Image.fromarray(built.cells[0][i][0], "RGBA").resize((built.fw * zoom, built.fh * zoom), Image.NEAREST)
        img.alpha_composite(cell, (4, 4))
        frames.append(img.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
        durs.append(int(round(dv * 1000 / 60)))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nuit").mkdir(exist_ok=True)
    built, info = construire()
    shadow_size, _ = P.load_sprite(REF)

    for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
        P.sheet(built, which).save(OUT / f"Eat-{kind}.png", optimize=True)
    night(P.sheet(built, 0)).save(OUT / "nuit" / "Eat-Anim.png", optimize=True)
    P.write_animdata(shadow_size, [built], OUT / "AnimData.xml")
    ase = P.write_aseprite([built], OUT / "politoed_eat.aseprite")
    planche_dessin(built, OUT / "apercu_bouches.png")
    gif(built, OUT / "apercu_eat.gif")

    (OUT / "credits.txt").write_text(
        "# Politoed #0186 — Eat dessiné à la main\n"
        + (REF / "credits.txt").read_text(encoding="utf-8").strip() + "\n"
        + "2026-09-07 00:00:00.000000\tGuilde Treehouse — bouche dessinée dans la palette du sprite"
          "\tCUR\tUnspecified\tEat\n"
          "Sprite d'origine : CHUNSOFT. Technique relevée sur l'Eat de Pichu #0172 et Riolu #0447.\n"
          "Cadence : Bayleef #0155. Ce Eat n'a été ni soumis ni approuvé sur SpriteCollab.\n",
        encoding="utf-8")

    kit = {
        "pokemon": {"nom": "Politoed", "numero": NUM,
                    "source": f"https://sprites.pmdcollab.org/#/{NUM}?form=0"},
        "demarche": "pixels dessinés à la main, à la manière des artistes Chunsoft",
        "regles_relevees_sur_0172_et_0447": [
            "la palette ne s'élargit jamais : on repeint avec les teintes déjà présentes",
            "tout trait est cerné de noir (0,0,0)",
            "l'ombrage va du clair au sombre par la teinte moyenne, jamais de saut",
            "le changement est local et légèrement asymétrique",
        ],
        "bouches_dessinees": list(DESSINS),
        "plan": PLAN,
        "case": [built.fw, built.fh], "durees": built.durations, "creneau": built.index,
        "palette_du_sprite": info["palette_base"], "couleurs_employees": info["couleurs_utilisees"],
        "aseprite": ase,
    }
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Politoed Eat dessiné : case {built.fw} × {built.fh}, {len(built.durations)} images, "
          f"{info['couleurs_utilisees']} couleurs (palette du sprite : {info['palette_base']}) → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
