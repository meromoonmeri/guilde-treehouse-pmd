#!/usr/bin/env python3
"""`Eat` dessiné à la main pour plusieurs Pokémon, à la manière des artistes Chunsoft.

Généralisation de `dessine_eat_politoed.py`. La leçon du § 13 était que la bouche de Politoed ne
se transpose pas : chaque personnage a une anatomie propre, qu'il faut relever puis dessiner.
C'est fait ici pour quatre Pokémon de plus, chacun avec son trait caractéristique.

────────────────────────────────────────────────────────────────────────────────
LES QUATRE RÈGLES, RELEVÉES SUR L'`Eat` DE PICHU #0172 ET RIOLU #0447
────────────────────────────────────────────────────────────────────────────────
1. **Palette fermée** : pas une couleur nouvelle, on repeint avec les teintes déjà là.
2. **Cerne noir** : toute ouverture est bordée de `(0,0,0)`.
3. **Ombrage ordonné** : clair → moyen → sombre, jamais de saut de valeur.
4. **Changement local et asymétrique** : seule la zone concernée bouge, sans symétrie mécanique.

────────────────────────────────────────────────────────────────────────────────
CE QUI EST DESSINÉ, PAR PERSONNAGE
────────────────────────────────────────────────────────────────────────────────
Relevé en dumpant chaque case `Idle` en ASCII, puis en repérant le trait à animer :

  Ambipom #0424  bouche souriante en dents (`y=17`, `x=11..18`, teintes `k`/`e`) : elle s'ouvre
                 en rond, dents écartées, gorge sombre au fond.
  Gible   #0443  grande gueule rouge (`y=15..18`, `x=6..15`, `l`=rouge vif, `h`/`j`=rouge sombre) :
                 la mâchoire s'écarte et la gorge s'assombrit — le trait le plus marquant du
                 personnage.
  Pawmot  #0923  petit museau (`y=11..13`) : la bouche s'ouvre en ovale sous le nez.
  Dedenne #0702  museau minuscule sur un sprite de 17 px : ouverture de 2 pixels seulement,
                 c'est tout ce que la taille permet sans bouillie.

Chaque dessin est une grille de caractères, lisible et modifiable ; l'espace signifie « garder
le pixel d'origine ». Les couleurs sont désignées par leur rôle (`gorge`, `dent`, `levre`…) et
résolues dans la palette du sprite concerné, jamais en dur.

Sortie : `personnages/<nom>/eat_dessine/`, dossiers SpriteCollab complets.
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
import pmd_sprite as P                                                    # noqa: E402
from rebuild_kit import night                                            # noqa: E402
from build_animations_scenes import HANDS_TO_MOUTH, move_limbs, physiology, step_limbs, Step  # noqa: E402

SKELETON = ROOT / "source" / "personnages" / "reference" / "0155"


class Dessin:
    """Un jeu de bouches dessinées pour un Pokémon, avec le rôle de chaque couleur.

    `roles` associe un symbole de la grille à une couleur **de la palette du sprite**, donnée
    en hexadécimal relevé sur la case Idle. Rien n'est inventé : le vérificateur refuse toute
    teinte absente du sprite d'origine.
    """

    def __init__(self, num: str, dossier: str, label: str, origine: tuple[int, int],
                 roles: dict[str, str], bouches: dict[str, list[str]], note: str):
        self.num, self.dossier, self.label = num, dossier, label
        self.ox, self.oy = origine
        self.roles = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in roles.items()}
        self.bouches = bouches
        self.note = note


# ---------------------------------------------------------------------------
# AMBIPOM #0424 — la bouche souriante en dents s'ouvre en rond.
# Original y17 : `..adcda...aaekkkkeaa...adcda..`  (k = blanc des dents, e = ocre des lèvres)
# ---------------------------------------------------------------------------
AMBIPOM = Dessin(
    "0424", "ambipom", "Ambipom", (10, 17),
    {"a": "#000000", "d": "#af6fb7", "e": "#bf7727", "i": "#dfaf67", "j": "#ffe79f",
     "k": "#ffffff", "f": "#d73f00", "c": "#873f87"},
    {
        "fermee": ["         ", "         ", "         "],  # l'original passe tel quel
        # entrouverte : les dents s'écartent, un liseré sombre apparaît entre elles
        "entrouverte": [
            " ajjjjja ",
            " aiddia  ",
            "  aiia   ",
        ],
        # grande ouverte : dents blanches en haut, liseré ocre, puis gorge sombre.
        # L'ocre `e` s'intercale entre le blanc `k` et le violet sombre `c` : sans lui les
        # deux valeurs extrêmes se toucheraient, ce que ne fait aucun sprite officiel.
        "grande_ouverte": [
            " ajjjja  ",
            " aiddia  ",
            " aaiiaa  ",
        ],
    },
    "la bouche en dents d'Ambipom s'ouvre en rond, les dents restant visibles en haut",
)

# ---------------------------------------------------------------------------
# GIBLE #0443 — la grande gueule rouge, trait le plus caractéristique du personnage.
# Original y16 : `agfgaahjlllljhhaagfga` (l = rouge vif, h/j = rouge sombre)
# ---------------------------------------------------------------------------
# Gueule relevée sur les lignes 15 à 18 de la boîte, colonnes 5 à 15 :
#   15 `ahlmaaakhha`   16 `ahjlllljhha`   17 `ajlllljhaee`   18 `eajlljhaefe`
# m = dent blanche, l = rouge vif, j/h = rouges sombres. La grille fait 11 colonnes.
GIBLE = Dessin(
    "0443", "gible", "Gible", (5, 15),
    {"a": "#000000", "h": "#971f00", "j": "#cf471f", "l": "#ff7737", "m": "#ffffff"},
    {
        "fermee": ["           ", "           ", "           ", "           "],
        # entrouverte : la gueule s'écarte d'un cran, le fond s'assombrit
        "entrouverte": [
            "ajjaaaaajja",
            "ajlllllllja",
            "ajjlllljjja",
            "aajjjjjjjaa",
        ],
        # grande ouverte : gueule béante, dents blanches en haut, gorge très sombre au fond
        "grande_ouverte": [
            "ajmmaaammja",
            "ajjlllljjja",
            "ajjjhhhjjja",
            "aajjjjjjjaa",
        ],
    },
    "la grande gueule de Gible s'ouvre en grand, dents blanches et gorge sombre",
)

# ---------------------------------------------------------------------------
# PAWMOT #0923 — petit museau sous le nez.
# Original y12 : `.......ahgfiaifgha.......`
# ---------------------------------------------------------------------------
PAWMOT = Dessin(
    "0923", "pawmot", "Pawmot", (10, 11),
    {"a": "#000000", "c": "#763a29", "d": "#d1a76a", "e": "#d35723", "f": "#f9d39b",
     "h": "#ffcc00", "i": "#ffecc9"},
    {
        "fermee": ["     ", "     "],
        "entrouverte": [
            " aea ",
            " afa ",
        ],
        "grande_ouverte": [
            "aeea ",
            "aeca ",
        ],
    },
    "le museau de Pawmot s'ouvre en ovale sous le nez",
)

# ---------------------------------------------------------------------------
# DEDENNE #0702 — sprite de 17 px : l'ouverture ne peut faire que deux pixels.
# ---------------------------------------------------------------------------
# Palette relevée sur la case : h #c85663 (lèvre), m #ffffff (dent), f #b71a03 (gorge sombre),
# k #f74228 (gorge vive), j #e8b43f (joue). La bouche fermée est le `hmh` de la ligne 11.
DEDENNE = Dessin(
    "0702", "dedenne", "Dedenne", (7, 11),
    {"a": "#000000", "h": "#c85663", "m": "#ffffff", "f": "#b71a03", "k": "#f74228",
     "j": "#e8b43f"},
    {
        "fermee": ["   ", "   "],
        "entrouverte": [
            "hhh",
            "afa",
        ],
        "grande_ouverte": [
            "afa",
            "aka",
        ],
    },
    "à 17 pixels de haut, la bouche de Dedenne ne peut s'ouvrir que de deux pixels",
)

DESSINS = [AMBIPOM, GIBLE, PAWMOT, DEDENNE]

# Cycle : repos, grande bouchée, repos, petite bouchée — l'artiste ne répète jamais
# deux fois la même image, il varie l'amplitude pour que le cycle respire.
PLAN = [
    {"bouche": "fermee", "mains": False, "squash": 0},
    {"bouche": "grande_ouverte", "mains": True, "squash": 1},
    {"bouche": "fermee", "mains": False, "squash": 0},
    {"bouche": "entrouverte", "mains": True, "squash": 1},
]


def peindre(crop: np.ndarray, d: Dessin, nom: str) -> np.ndarray:
    out = crop.copy()
    for j, ligne in enumerate(d.bouches[nom]):
        for i, sym in enumerate(ligne):
            y, x = d.oy + j, d.ox + i
            if sym == " " or not (0 <= y < out.shape[0] and 0 <= x < out.shape[1]):
                continue
            out[y, x, :3] = d.roles[sym]
            out[y, x, 3] = 255
    return out


def construire(d: Dessin) -> tuple[P.Built, dict, int]:
    ref = ROOT / "source" / "personnages" / "reference" / d.num
    shadow_size, anims = P.load_sprite(ref)
    _, skel = P.load_sprite(SKELETON)
    modele = skel["Eat"]
    idle = anims["Idle"]
    amp = physiology(idle.frames[0][0].bbox[3] - idle.frames[0][0].bbox[1] + 1)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(anims)}

    hors = {c for c in d.roles.values()} - base_palette
    assert not hors, f"#{d.num} : couleurs hors palette du sprite : {hors}"

    rows, n = modele.dirs, len(modele.durations)
    disp = [modele.frames[0][i].disp for i in range(n)]
    ext_x = ext_y = 0
    for dd in range(rows):
        f = idle.frames[dd][0]
        x0, y0, x1, y1 = f.bbox
        for i in range(n):
            ext_x = max(ext_x, abs(x0 - 2) + abs(disp[i][0]), abs(x1 + 2) + abs(disp[i][0]))
            ext_y = max(ext_y, abs(y0 - 2 + 4), abs(y1 + 2 - 4))
    fw = max(16, ((2 * (ext_x + 1) + 7) // 8) * 8)
    fh = max(16, ((2 * (ext_y + 5) + 7) // 8) * 8)

    built = P.Built("Eat", modele.index, fw, fh, list(modele.durations),
                    notes="bouche dessinée à la main dans la palette du sprite ; cadence #0155")
    dessinees = 0
    for dd in range(rows):
        cells, anchors = [], []
        for i, etape in enumerate(PLAN):
            f = idle.frames[dd][0]
            ax_src, ay_src = f.anchor
            x0, y0, x1, y1 = f.bbox
            crop = f.image[ay_src + y0:ay_src + y1 + 1, ax_src + x0:ax_src + x1 + 1].copy()
            # la bouche n'est visible que de face : on ne la dessine que sur la ligne Bas
            if dd == 0 and etape["bouche"] != "fermee":
                crop = peindre(crop, d, etape["bouche"])
                dessinees += 1
            if etape["mains"]:
                lbs = step_limbs(Step("Idle", 0, limbs=(HANDS_TO_MOUTH,)), amp)
                crop = move_limbs(crop, (-x0, -y0), f.marks, lbs, f.bbox)

            cx, cy = fw // 2 + disp[i][0], fh // 2 + 4 + disp[i][1]
            cell = np.zeros((fh, fw, 4), np.uint8)
            offs = np.zeros((fh, fw, 4), np.uint8)
            shad = np.zeros((fh, fw, 4), np.uint8)
            h, w = crop.shape[:2]
            px, py = max(0, min(cx + x0, fw - w)), max(0, min(cy + y0 + etape["squash"], fh - h))
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
    assert not (used - base_palette), f"#{d.num} : couleurs inventées {used - base_palette}"
    assert len(used) <= 15, f"#{d.num} : {len(used)} couleurs"
    return built, {"palette_base": len(base_palette), "couleurs": len(used)}, shadow_size


def police(taille: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", taille)
    except OSError:
        return ImageFont.load_default()


def planche(built: P.Built, d: Dessin, path: Path) -> None:
    Z = 12
    idx = {"fermee": 0, "grande_ouverte": 1, "entrouverte": 3}
    w = built.fw * Z
    img = Image.new("RGBA", (3 * (w + 12) + 12, built.fh * Z + 74), (26, 26, 46, 255))
    dr = ImageDraw.Draw(img)
    dr.text((12, 10), f"{d.label.upper()} #{d.num} — BOUCHE DESSINÉE À LA MAIN",
            fill=(240, 240, 240, 255), font=police(18))
    dr.text((12, 34), d.note, fill=(170, 170, 200, 255), font=police(12))
    dr.text((12, 50), "palette du sprite uniquement · contour noir · ombrage clair → moyen → sombre",
            fill=(140, 140, 170, 255), font=police(11))
    for k, nom in enumerate(["fermee", "grande_ouverte", "entrouverte"]):
        cell = Image.fromarray(built.cells[0][idx[nom]][0], "RGBA").resize((w, built.fh * Z), Image.NEAREST)
        tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
        tile.alpha_composite(cell)
        img.alpha_composite(tile, (12 + k * (w + 12), 68))
        dr.text((12 + k * (w + 12) + 4, 68 + built.fh * Z + 2), nom,
                fill=(220, 220, 240, 255), font=police(12))
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
        cell = Image.fromarray(built.cells[0][i][0], "RGBA").resize(
            (built.fw * zoom, built.fh * zoom), Image.NEAREST)
        img.alpha_composite(cell, (4, 4))
        frames.append(img.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
        durs.append(int(round(dv * 1000 / 60)))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


def main() -> None:
    for d in DESSINS:
        out = ROOT / "personnages" / d.dossier / "eat_dessine"
        out.mkdir(parents=True, exist_ok=True)
        (out / "nuit").mkdir(exist_ok=True)
        built, info, shadow_size = construire(d)
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            P.sheet(built, which).save(out / f"Eat-{kind}.png", optimize=True)
        night(P.sheet(built, 0)).save(out / "nuit" / "Eat-Anim.png", optimize=True)
        P.write_animdata(shadow_size, [built], out / "AnimData.xml")
        ase = P.write_aseprite([built], out / f"{d.dossier}_eat.aseprite")
        planche(built, d, out / "apercu_bouches.png")
        gif(built, out / "apercu_eat.gif")

        ref = ROOT / "source" / "personnages" / "reference" / d.num / "credits.txt"
        (out / "credits.txt").write_text(
            f"# {d.label} #{d.num} — Eat dessiné à la main\n"
            + (ref.read_text(encoding="utf-8").strip() if ref.is_file() else "") + "\n"
            + "2026-09-07 00:00:00.000000\tGuilde Treehouse — bouche dessinée dans la palette du sprite"
              "\tCUR\tUnspecified\tEat\n"
              "Technique relevée sur les Eat de Pichu #0172 et Riolu #0447. Cadence : Bayleef #0155.\n"
              "Ce Eat n'a été ni soumis ni approuvé sur SpriteCollab.\n", encoding="utf-8")

        kit = {
            "pokemon": {"nom": d.label, "numero": d.num,
                        "source": f"https://sprites.pmdcollab.org/#/{d.num}?form=0"},
            "demarche": "pixels dessinés à la main, à la manière des artistes Chunsoft",
            "trait_anime": d.note,
            "origine_du_dessin": [d.ox, d.oy],
            "roles_de_couleur": {k: "#%02x%02x%02x" % v for k, v in d.roles.items()},
            "bouches": {k: v for k, v in d.bouches.items()},
            "plan": PLAN,
            "case": [built.fw, built.fh], "durees": built.durations, "creneau": built.index,
            "palette_du_sprite": info["palette_base"], "couleurs_employees": info["couleurs"],
            "aseprite": ase,
        }
        (out / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"#{d.num} {d.label:9s} : Eat dessiné, case {built.fw} × {built.fh}, "
              f"{info['couleurs']} couleurs (palette : {info['palette_base']}) → "
              f"{out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
