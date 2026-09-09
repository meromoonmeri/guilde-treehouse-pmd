#!/usr/bin/env python3
"""Aperçus du dossier sprite/ : planche de toutes les espèces (Walk, image 1, face) et GIF de quelques espèces
en marche + attente, plus le tableau `sprite/README.md`. Fond transparent partout : on montre les sprites, rien d'autre.

Usage : python3 source/sprite/apercu.py [--gif dex ...]
"""
from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from build_dynamax import OUT_ROOT, paste, save_png  # noqa: E402
from build_vfx import label  # noqa: E402

GIF_DEFAULT = ["0025", "0006", "0094", "0143", "0297", "0448", "0700", "0870"]


def anim_info(folder: Path, name: str) -> tuple[int, int, list[int], int | None, int | None] | None:
    root = ET.parse(folder / "AnimData.xml").getroot()
    for a in root.find("Anims").iter("Anim"):
        if a.find("Name").text == name and a.find("FrameWidth") is not None:
            durs = [int(d.text) for d in a.find("Durations").iter("Duration")]
            return int(a.find("FrameWidth").text), int(a.find("FrameHeight").text), durs, None, None
    return None


def cell(folder: Path, name: str, d: int, i: int) -> np.ndarray | None:
    info = anim_info(folder, name)
    if info is None:
        return None
    fw, fh, durs, _, _ = info
    sheet = np.array(Image.open(folder / f"{name}-Anim.png").convert("RGBA"))
    rows = sheet.shape[0] // fh
    d = d if d < rows else 0
    return sheet[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]


def sheet_all(index: dict, path: Path, per_row: int = 24) -> None:
    """Toutes les espèces, Walk image 1 de face, à l'échelle 1 (donc × 3 du dessin), fond transparent."""
    species = [r for r in index["especes"].values() if "erreur" not in r]
    cw, ch = 120, 150
    tiles = []
    for r in species:
        folder = OUT_ROOT / r["dossier"]
        c = cell(folder, "Walk", 0, 0)
        if c is None:
            continue
        ys, xs = np.nonzero(c[:, :, 3])
        if len(xs) == 0:
            continue
        crop = c[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        h, w = crop.shape[:2]
        if w > cw or h > ch - 14:                                          # trop grand pour la vignette : réduit en entier
            f = max(math.ceil(w / cw), math.ceil(h / (ch - 14)))
            crop = crop[::f, ::f]
            h, w = crop.shape[:2]
        tile = np.zeros((ch, cw, 4), np.uint8)
        paste(tile, crop, (cw - w) // 2, ch - 14 - h)
        paste(tile, label(r["dex"]), 2, ch - 13)
        tiles.append(tile)
    rows = math.ceil(len(tiles) / per_row)
    out = np.zeros((rows * ch + 24, per_row * cw, 4), np.uint8)
    paste(out, label(f"sprite/ — {len(tiles)} espèces Dynamax (Walk, image 1, de face, échelle 1 = × 3 du dessin SpriteCollab)"), 4, 4)
    for k, t in enumerate(tiles):
        paste(out, t, (k % per_row) * cw, 24 + (k // per_row) * ch)
    save_png(out, path)


def gif_frames_of(folder: Path, name: str, d: int) -> list[tuple[np.ndarray, int]]:
    info = anim_info(folder, name)
    if info is None:
        return []
    fw, fh, durs, _, _ = info
    return [(cell(folder, name, d, i), dur) for i, dur in enumerate(durs)]


def gif_species(index: dict, dexes: list[str], path: Path) -> None:
    """Marche (face puis droite) et attente de quelques espèces côte à côte, fond transparent, 4 s en boucle."""
    cols = []
    for dex in dexes:
        r = index["especes"].get(dex)
        if not r or "erreur" in r:
            continue
        folder = OUT_ROOT / r["dossier"]
        seq = gif_frames_of(folder, "Walk", 0) * 2 + gif_frames_of(folder, "Walk", 2) * 2 + gif_frames_of(folder, "Idle", 0)
        if seq:
            cols.append(seq)
    if not cols:
        return
    cw = max(max(c.shape[1] for c, _ in seq) for seq in cols) + 8
    ch = max(max(c.shape[0] for c, _ in seq) for seq in cols) + 8
    span = 240
    events = set()
    timelines = []
    for seq in cols:
        tl, t = [], 0
        while t < span:
            for c, dur in seq:
                tl.append((t, c))
                t += dur
        timelines.append(tl)
        events |= {t for t, _ in tl if t < span}
    events = sorted(events | {0})
    palette_imgs, durs = [], []
    for k, t in enumerate(events):
        nxt = events[k + 1] if k + 1 < len(events) else span
        img = np.zeros((ch, len(cols) * cw, 4), np.uint8)
        for col, tl in enumerate(timelines):
            c = [c for tt, c in tl if tt <= t][-1]
            paste(img, c, col * cw + (cw - c.shape[1]) // 2, ch - 4 - c.shape[0])
        im = Image.fromarray(img, "RGBA")
        q = im.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        # index 255 réservé au transparent
        arr = np.array(q)
        arr[img[:, :, 3] == 0] = 255
        pal = q.getpalette()[:255 * 3] + [0, 0, 0]
        p = Image.fromarray(arr, "P")
        p.putpalette(pal)
        palette_imgs.append(p)
        durs.append(int(round((nxt - t) * 1000 / 60)))
    palette_imgs[0].save(path, save_all=True, append_images=palette_imgs[1:], duration=durs, loop=0, transparency=255, disposal=2)


def write_readme(index: dict, path: Path) -> None:
    species = sorted((r for r in index["especes"].values() if "erreur" not in r), key=lambda r: r["dex"])
    errors = sorted((r for r in index["especes"].values() if "erreur" in r), key=lambda r: r["dex"])
    src = index["source"]
    total_cells = sum(r["cases"] for r in species)
    total_mb = sum(r["octets"] for r in species) / 1e6
    lic: dict[str, int] = {}
    for r in species:
        for one in r["licence"].split("+"):
            lic[one] = lic.get(one, 0) + 1
    rows = "\n".join(f"| `{r['dossier']}/` | {r['nom']} | {r['animations']} | {r['cases']} | {r['couleurs']} | {'M' if r['petits_nuages'] else 'L'} | {r['licence']} |"
                     for r in species)
    err_rows = "\n".join(f"| {r['dex']} | {r['erreur']} |" for r in errors) or "| — | — |"
    text = f"""# sprite/ — sprites Dynamax de tous les Pokémon animés de SpriteCollab

![Toutes les espèces](apercu.png)

![Quelques espèces en marche et en attente](apercu.gif)

**{len(species)} espèces**, {total_cells:,} cases, {total_mb:.0f} Mo — toutes celles dont le dossier `sprite/<dex>/` du dépôt
[PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab) (commit `{src['commit'][:12]}`) contient un
`AnimData.xml` (forme de base, apparence normale ; le gabarit `0000` Missingno est laissé de côté), plus Falinks
(escouade) et Zarude de ce dépôt (`personnages/`), absents de SpriteCollab. Pour chacune, **toutes ses animations**
sont reprises (noms, index, `CopyOf`, durées, `RushFrame` / `HitFrame` / `ReturnFrame`, déplacements de l'ancre) et
transformées en version Dynamax :

1. **agrandissement × {src['echelle']}** au plus proche voisin — aucun pixel du Pokémon redessiné ;
2. **aura rouge animée** collée à la silhouette (anneau plein + anneau tramé dont le motif remonte à chaque image
   + langues extérieures) — deux couleurs ajoutées, (232, 40, 72) et (255, 144, 128) ;
3. **trois nuages-cyclones rouges** qui tournent au-dessus de la tête (un tiers de tour par cycle d'animation : la
   boucle est continue ; volute à trois phases ; la moitié arrière de l'anneau passe derrière le corps ; ils suivent
   le point le plus haut de chaque image, donc les sauts et le sommeil) — contour = couleur la plus sombre du sprite ;
   petits nuages (gabarit **M**) si le corps fait moins de 24 px de large ou de 20 px de haut à l'échelle 1, grands (**L**) sinon ;
4. repères d'Offsets et ancre de Shadow replacés à l'échelle, gabarit d'ombre agrandi, `ShadowSize` 2 ;
5. cases élargies par pas de 8, ancre au repos en (largeur / 2, hauteur / 2 + 4).

Chaque dossier `sprite/<dex>_<slug>/` (slug = nom français) contient `AnimData.xml`, `<Anim>-Anim.png` /
`-Offsets.png` / `-Shadow.png` (PNG indexés, mêmes pixels qu'en RGBA) et `credits.txt` (crédits SpriteCollab repris
tels quels + ligne Dynamax). `index.json` résume tout (nom, animations, cases, couleurs, gabarit, licence, taille).

## La transformation : `vfx/`

L'**animation de transformation** est un VFX à part, **sans personnage ni fond**, dessiné image par image
(12 images, 1 s) en deux gabarits : [`vfx/`](vfx/README.md). En jeu : `Transformation-<gabarit>` à l'ancre du sprite
normal → image 3 : masquer le sprite normal → image 9 (`HitFrame`) : afficher le sprite Dynamax de ce dossier (il
porte déjà aura et nuages) → image 12 : fin du VFX. Le gabarit d'une espèce est dans `index.json` (`petits_nuages`
= M).

## Reproduire, vérifier

```
python3 source/sprite/build_dynamax.py --tous            # clone SpriteCollab en sparse dans /tmp/spritecollab, ~1 h sur 2 cœurs
python3 source/sprite/build_dynamax.py 0025 0297         # quelques espèces
python3 source/sprite/build_vfx.py                       # le VFX de transformation
python3 source/sprite/verify_dynamax.py --tous           # contrôles (règles SpriteBot + chaque pixel source retrouvé × 3)
python3 source/sprite/apercu.py                          # cette planche, le GIF, ce README
```

Le vérificateur rejoue les contrôles du SpriteBot (index, `CopyOf`, tailles de feuilles, 1 ou 8 lignes, colonnes =
durées, alpha binaire, un blanc par case, un pixel par repère) et vérifie que chaque pixel de l'origine se retrouve
agrandi à sa place (seuls les pixels recouverts par un nuage de premier plan diffèrent : moins de 8 % du corps sur
l'espèce, jamais plus de 35 % sur une image ; avertissement au-delà de 20 % — ailes déployées, sommeil à plat), que
l'ancre et les repères sont ceux de l'origine × {src['echelle']}, que durées, index et `CopyOf` sont identiques, et que la palette
= palette d'origine + aura. Résumé dans `controle_qualite.json`.

## Licences

Les sprites dérivent de SpriteCollab et cumulent les licences des contributions en vigueur de leur original
(reprises ligne à ligne dans `credits.txt` ; colonne « Licence » de `especes.md`, « + » = plusieurs auteurs) :
{', '.join(f'{k} : {v}' for k, v in sorted(lic.items(), key=lambda kv: -kv[1]))}. « Unspecified » = sprite original des
jeux (CHUNSOFT / Spike Chunsoft), usage de fan non commercial uniquement ; PMDCollab_1 / PMDCollab_2 / CC BY-NC 4.0 =
usage non commercial avec crédit des auteurs (politique de SpriteCollab : CC BY-NC 4.0). Les formes Dynamax ne sont pas
des formes officielles acceptées par SpriteCollab : ces sprites n'y ont été ni soumis ni approuvés.

## Espèces

La liste complète (dossier, nom, animations, cases, couleurs, gabarit, licence) est dans [`especes.md`](especes.md) ;
la même chose en données dans `index.json`.
"""
    path.write_text(text, encoding="utf-8")
    table = f"""# sprite/ — les {len(species)} espèces

Gabarit M = petits nuages (corps < 24 px de large à l'échelle 1) → VFX `Transformation-M` ; L → `Transformation-L`.
Licence : celle(s) des contributions en vigueur du sprite d'origine (« + » = plusieurs auteurs), voir `credits.txt`.

| Dossier | Pokémon | Animations | Cases | Couleurs | Gabarit | Licence |
| --- | --- | --- | --- | --- | --- | --- |
{rows}

Espèces non produites :

| Dex | Raison |
| --- | --- |
{err_rows}
"""
    (path.parent / "especes.md").write_text(table, encoding="utf-8")


def main(argv: list[str]) -> None:
    index = json.loads((OUT_ROOT / "index.json").read_text(encoding="utf-8"))
    dexes = GIF_DEFAULT
    if "--gif" in argv:
        dexes = [a.zfill(4) for a in argv[argv.index("--gif") + 1:]] or dexes
    sheet_all(index, OUT_ROOT / "apercu.png")
    gif_species(index, dexes, OUT_ROOT / "apercu.gif")
    write_readme(index, OUT_ROOT / "README.md")
    n = sum(1 for r in index["especes"].values() if "erreur" not in r)
    print(f"aperçus : {n} espèces → sprite/apercu.png, sprite/apercu.gif, sprite/README.md, sprite/especes.md")


if __name__ == "__main__":
    main(sys.argv[1:])
