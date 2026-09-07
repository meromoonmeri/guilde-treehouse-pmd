#!/usr/bin/env python3
"""`Eat` produits **avec le générateur d'images**, discipliné puis vérifié.

L'utilisateur a demandé d'employer le générateur d'images pour fabriquer les images de repas
plutôt que de tout dessiner à la main. C'est fait ici pour Gardevoir #0282, Pancham #0674 et
Slurpuff #0685 : le PNG du sprite officiel a été envoyé au générateur avec la consigne de
redessiner la **même** case en train de manger, et la sortie a été ramenée dans les contraintes
du format.

────────────────────────────────────────────────────────────────────────────────
CE QUE DONNE LE GÉNÉRATEUR, MESURÉ
────────────────────────────────────────────────────────────────────────────────
Cinq sprites entiers lui ont été soumis. Après rabattement sur la palette d'origine :

    Pancham    87,1 % des pixels conservés   → exploitable
    Slurpuff   87,0 %                        → exploitable
    Gardevoir  80,6 %                        → exploitable
    Hariyama   68,5 %                        → visage déformé, écarté
    Miltank    15,1 %                        → sprite détruit, écarté

Le contrôle visuel confirme le chiffre : sous ~80 % le personnage n'est plus lui-même. Les deux
recalés ne sont pas livrés — c'est le rôle d'un seuil de savoir dire non.

────────────────────────────────────────────────────────────────────────────────
LA DISCIPLINE (sans elle, rien n'est utilisable)
────────────────────────────────────────────────────────────────────────────────
1. **Grille exacte** par moyenne de bloc (`Image.BOX`), jamais `NEAREST` : le générateur dessine
   sa propre grille, légèrement décalée de la nôtre.
2. **Palette fermée** : chaque pixel est rabattu sur la couleur la plus proche de la palette du
   sprite officiel. Le générateur en sortait 178 à 471 ; la limite du SpriteBot est 15.
3. **Masque de zone** : seul le rectangle de la bouche est repris du générateur, tout le reste du
   sprite est remis à l'identique. C'est ce qui fait passer la conservation de ~87 % à 88-96 %.
4. **Zone choisie par la mesure** : pour Pancham, la zone repérée à la main donnait un écart de
   valeur de 612 entre pixels voisins, au-delà des 487 que s'autorise Chunsoft. Une recherche sur
   les rectangles possibles retient la plus grande zone qui reste dans les clous (442).

Résultat final : palette fermée, 88 à 96 % du sprite conservé, écart d'ombrage conforme, rien
de modifié hors de la zone de la bouche.
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
BRUTS = ROOT / "source" / "personnages" / "essais" / "generateur"

# num -> (dossier, label, zone de bouche (x0, y0, x1, y1), note)
# Les zones ne sont pas choisies à l'œil : pour chaque Pokémon, tous les rectangles plausibles
# ont été essayés, et on retient **le plus grand qui reste sous les 487 d'écart de valeur** que
# s'autorise Chunsoft. Choisir la zone à la main donnait 591 sur Gardevoir et 612 sur Pancham.
RETENUS = {
    "0282": ("gardevoir", "Gardevoir", (2, 9, 15, 16),
             "la bouche s'ouvre sous les yeux rouges, dans le blanc du visage"),
    "0674": ("pancham", "Pancham", (2, 13, 16, 20),
             "la bouche s'ouvre entre les taches noires des yeux"),
    "0685": ("slurpuff", "Slurpuff", (2, 12, 18, 19),
             "la grande bouche de Slurpuff s'ouvre dans la crème blanche"),
}

# Écartés après mesure : conservation trop basse, personnage méconnaissable.
ECARTES = {"0297": ("Hariyama", 68.5), "0241": ("Miltank", 15.1)}

PLAN = [
    {"bouche": False, "mains": False, "squash": 0},
    {"bouche": True, "mains": True, "squash": 1},
    {"bouche": False, "mains": False, "squash": 0},
    {"bouche": True, "mains": True, "squash": 1},
]


def discipliner(num: str, crop: np.ndarray, zone: tuple[int, int, int, int]) -> tuple[np.ndarray, dict]:
    """Ramène la sortie du générateur dans les contraintes du format SpriteCollab."""
    h, w = crop.shape[:2]
    masque = crop[:, :, 3] > 0
    palette = sorted({tuple(int(v) for v in c) for c in crop[masque][:, :3]})
    pal = np.array(palette)

    brut = Image.open(BRUTS / f"{num}_eat.png").convert("RGB")
    petit = np.array(brut.resize((w, h), Image.BOX)).astype(int)          # (1) grille exacte
    brutes = len({tuple(int(v) for v in c) for c in petit.reshape(-1, 3)})
    d = ((petit.reshape(-1, 3)[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    rabattu = pal[d.argmin(1)].reshape(h, w, 3)                            # (2) palette fermée

    x0, y0, x1, y1 = zone                                                  # (3) masque de zone
    z = np.zeros((h, w), bool)
    z[y0:y1, x0:x1] = True
    out = crop.copy()
    out[:, :, :3] = np.where((z & masque)[:, :, None], rabattu, crop[:, :, :3])

    identiques = int((out[masque][:, :3] == crop[masque][:, :3]).all(1).sum())
    modifies = int((np.any(out != crop, axis=2) & masque).sum())
    return out, {"couleurs_brutes": brutes, "conservation": round(100 * identiques / int(masque.sum()), 1),
                 "pixels_modifies": modifies, "zone": list(zone)}


def construire(num: str) -> tuple[P.Built, dict, int]:
    dossier, label, zone, note = RETENUS[num]
    ref = ROOT / "source" / "personnages" / "reference" / num
    shadow_size, anims = P.load_sprite(ref)
    _, skel = P.load_sprite(SKELETON)
    modele = skel["Eat"]
    idle = anims["Idle"]
    amp = physiology(idle.frames[0][0].bbox[3] - idle.frames[0][0].bbox[1] + 1)
    base_palette = {tuple(int(v) for v in c) for c in P.palette_of(anims)}

    f0 = idle.frames[0][0]
    x0, y0, x1, y1 = f0.bbox
    ax, ay = f0.anchor
    crop0 = f0.image[ay + y0:ay + y1 + 1, ax + x0:ax + x1 + 1].copy()
    bouchee, mesures = discipliner(num, crop0, zone)

    rows, n = modele.dirs, len(modele.durations)
    disp = [modele.frames[0][i].disp for i in range(n)]
    ext_x = ext_y = 0
    for dd in range(rows):
        bx0, by0, bx1, by1 = idle.frames[dd][0].bbox
        for i in range(n):
            ext_x = max(ext_x, abs(bx0 - 2) + abs(disp[i][0]), abs(bx1 + 2) + abs(disp[i][0]))
            ext_y = max(ext_y, abs(by0 - 2 + 4), abs(by1 + 2 - 4))
    fw = max(16, ((2 * (ext_x + 1) + 7) // 8) * 8)
    fh = max(16, ((2 * (ext_y + 5) + 7) // 8) * 8)

    built = P.Built("Eat", modele.index, fw, fh, list(modele.durations),
                    notes="bouche produite par générateur d'images, disciplinée ; cadence #0155")
    for dd in range(rows):
        cells, anchors = [], []
        for i, etape in enumerate(PLAN):
            f = idle.frames[dd][0]
            sax, say = f.anchor
            bx0, by0, bx1, by1 = f.bbox
            base = f.image[say + by0:say + by1 + 1, sax + bx0:sax + bx1 + 1].copy()
            # la bouche n'est visible que de face
            crop = bouchee.copy() if (dd == 0 and etape["bouche"]) else base
            if etape["mains"]:
                lbs = step_limbs(Step("Idle", 0, limbs=(HANDS_TO_MOUTH,)), amp)
                crop = move_limbs(crop, (-bx0, -by0), f.marks, lbs, f.bbox)

            cx, cy = fw // 2 + disp[i][0], fh // 2 + 4 + disp[i][1]
            cell = np.zeros((fh, fw, 4), np.uint8)
            offs = np.zeros((fh, fw, 4), np.uint8)
            shad = np.zeros((fh, fw, 4), np.uint8)
            hh, ww = crop.shape[:2]
            px = max(0, min(cx + bx0, fw - ww))
            py = max(0, min(cy + by0 + etape["squash"], fh - hh))
            bloc = cell[py:py + hh, px:px + ww]
            m = crop[:, :, 3] > 0
            bloc[m] = crop[m]
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
    assert not (used - base_palette), f"#{num} : couleurs inventées {used - base_palette}"
    assert len(used) <= 15, f"#{num} : {len(used)} couleurs"
    mesures["couleurs"] = len(used)
    mesures["palette_base"] = len(base_palette)
    return built, mesures, shadow_size


def police(t: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", t)
    except OSError:
        return ImageFont.load_default()


def planche(built: P.Built, num: str, m: dict, path: Path) -> None:
    dossier, label, zone, note = RETENUS[num]
    Z = 12
    w = built.fw * Z
    img = Image.new("RGBA", (2 * (w + 12) + 12, built.fh * Z + 88), (26, 26, 46, 255))
    d = ImageDraw.Draw(img)
    d.text((12, 10), f"{label.upper()} #{num} — BOUCHE PRODUITE PAR GÉNÉRATEUR D'IMAGES",
           fill=(240, 240, 240, 255), font=police(17))
    d.text((12, 34), note, fill=(170, 170, 200, 255), font=police(12))
    d.text((12, 52), f"sortie brute : {m['couleurs_brutes']} couleurs → rabattue sur la palette du sprite "
                     f"({m['couleurs']}) · {m['conservation']} % du sprite conservé · "
                     f"{m['pixels_modifies']} pixels modifiés",
           fill=(140, 140, 170, 255), font=police(11))
    for k, (i, nom) in enumerate([(0, "repos"), (1, "bouchée")]):
        cell = Image.fromarray(built.cells[0][i][0], "RGBA").resize((w, built.fh * Z), Image.NEAREST)
        tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
        tile.alpha_composite(cell)
        img.alpha_composite(tile, (12 + k * (w + 12), 72))
        d.text((12 + k * (w + 12) + 4, 72 + built.fh * Z + 2), nom,
               fill=(220, 220, 240, 255), font=police(12))
    img.save(path, optimize=True)


def parquet(size, zoom):
    src = ROOT / "salles" / "01_accueil" / "salle_jour.png"
    bg = Image.new("RGBA", size, (150, 104, 52, 255))
    if src.is_file():
        t = Image.open(src).convert("RGBA").crop((264, 252, 392, 316))
        a = np.array(t).astype(np.int16)
        a[:, :, :3] = (a[:, :, :3] * 0.72).clip(0, 255)
        t = Image.fromarray(a.astype(np.uint8), "RGBA")
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
    rapport = {"demarche": "images produites par un générateur d'images, puis disciplinées",
               "ecartes": {n: {"nom": l, "conservation": c} for n, (l, c) in ECARTES.items()},
               "retenus": {}}
    for num in RETENUS:
        dossier, label, zone, note = RETENUS[num]
        out = ROOT / "personnages" / dossier / "eat_generateur"
        out.mkdir(parents=True, exist_ok=True)
        (out / "nuit").mkdir(exist_ok=True)
        built, m, shadow_size = construire(num)
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            P.sheet(built, which).save(out / f"Eat-{kind}.png", optimize=True)
        night(P.sheet(built, 0)).save(out / "nuit" / "Eat-Anim.png", optimize=True)
        P.write_animdata(shadow_size, [built], out / "AnimData.xml")
        ase = P.write_aseprite([built], out / f"{dossier}_eat.aseprite")
        planche(built, num, m, out / "apercu_bouches.png")
        gif(built, out / "apercu_eat.gif")

        ref = ROOT / "source" / "personnages" / "reference" / num / "credits.txt"
        (out / "credits.txt").write_text(
            f"# {label} #{num} — Eat produit par générateur d'images, discipliné\n"
            + (ref.read_text(encoding="utf-8").strip() if ref.is_file() else "") + "\n"
            + "2026-09-07 00:00:00.000000\tGuilde Treehouse — bouche produite par générateur d'images"
              "\tCUR\tUnspecified\tEat\n"
              "Sortie rabattue sur la palette du sprite officiel et limitée à la zone de la bouche.\n"
              "Cadence : Bayleef #0155. Ce Eat n'a été ni soumis ni approuvé sur SpriteCollab.\n",
            encoding="utf-8")

        kit = {"pokemon": {"nom": label, "numero": num,
                           "source": f"https://sprites.pmdcollab.org/#/{num}?form=0"},
               "demarche": "générateur d'images + discipline (grille, palette, zone)",
               "trait_anime": note, "mesures": m, "plan": PLAN,
               "case": [built.fw, built.fh], "durees": built.durations, "creneau": built.index,
               "aseprite": ase}
        (out / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
        rapport["retenus"][num] = {"nom": label, **m}
        print(f"#{num} {label:10s} : {m['conservation']:5.1f} % conservé, "
              f"{m['couleurs_brutes']:3d} → {m['couleurs']} couleurs, "
              f"{m['pixels_modifies']:2d} pixels modifiés → {out.relative_to(ROOT)}")
    (BRUTS / "rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    for num, (label, c) in ECARTES.items():
        print(f"#{num} {label:10s} : ÉCARTÉ — {c} % de conservation, personnage méconnaissable")


if __name__ == "__main__":
    main()
