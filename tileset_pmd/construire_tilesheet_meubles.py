from __future__ import annotations

"""Construit un tilesheet de meubles pour le cafe, a partir des assets du jeu.

SOURCES
-------
Les meubles ne sont pas dessines : ils sont **extraits des vrais tilesets**, ce
qui garantit la qualite d'un asset de jeu plutot que celle d'une generation.

  * `Minemaker0430/ExplorersOfSkyOrigins`, `SpindaCafe2.tile` — le calque
    d'objets du cafe Spinda, deja detoure. Mesure : 86 couleurs, 6,1 couleurs
    par tuile de 8x8, 100 % des tuiles sous 16 couleurs, 0 semi-transparent.
  * `Palikadude/Halcyon`, les quatre calques `Metano_Town_Cafe_Objects*` —
    comptoir, etagere a baies, tables-souches, plantes, caisses, tapis.

METHODE
-------
Chaque objet est isole par **composante connexe** sur le masque alpha, puis
recadre au pixel pres et aligne sur une grille de 8 px : chaque case du sheet
fait un nombre entier de cellules PMDO, donc les objets se posent sans decalage.

Le sheet est ecrit avec un fond **strictement transparent** (alpha binaire), et
un manifeste JSON donne pour chaque objet son nom, sa position dans le sheet et
sa taille en cellules.

Usage :
    python3 construire_tilesheet_meubles.py
"""

from collections import deque
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image

TILE = 8
MIN_PIXELS = 120          # en dessous : miette de detourage, pas un meuble
MARGE = 1                 # cellules vides entre deux objets dans le sheet

RACINE = Path(__file__).resolve().parent.parent / "interieur"


def composantes(a: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """Boites englobantes des groupes de pixels opaques connexes."""
    op = a[:, :, 3] > 128
    h, w = op.shape
    vu = np.zeros_like(op)
    out = []
    for sy in range(h):
        for sx in range(w):
            if not op[sy, sx] or vu[sy, sx]:
                continue
            q = deque([(sy, sx)])
            vu[sy, sx] = True
            ys, xs, n = [], [], 0
            while q:
                y, x = q.popleft()
                ys.append(y)
                xs.append(x)
                n += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and op[ny, nx] and not vu[ny, nx]:
                            vu[ny, nx] = True
                            q.append((ny, nx))
            if n >= MIN_PIXELS:
                out.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, n))
    return out


# Dans le calque EOS, les deux stands et les guirlandes forment une seule
# composante connexe (les fanions les relient). On la tranche a la main pour
# obtenir des elements reutilisables separement.
DECOUPES = {
    "spinda_cafe_eos_objets.png": {
        "stand_gauche": (180, 95, 330, 190),
        "stand_droit": (370, 95, 520, 190),
        "guirlande_gauche": (136, 63, 300, 140),
        "guirlande_droite": (400, 63, 560, 140),
        "panneaux_mur": (325, 95, 360, 125),
    },
}


def decouper(path: Path, prefixe: str) -> list[tuple[str, Image.Image]]:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    pieces = []

    # zones tranchees a la main : on les sort d'abord et on les efface du
    # masque pour qu'elles ne ressortent pas une seconde fois en bloc
    for nom, (x0, y0, x1, y1) in DECOUPES.get(path.name, {}).items():
        sous = a[y0:y1, x0:x1].copy()
        sous[:, :, 3] = np.where(sous[:, :, 3] > 128, 255, 0)
        if (sous[:, :, 3] > 128).sum() >= MIN_PIXELS:
            bb = Image.fromarray(sous, "RGBA").getbbox()
            pieces.append((f"{prefixe}_{nom}",
                           Image.fromarray(sous, "RGBA").crop(bb)))
        a[y0:y1, x0:x1, 3] = 0
    for i, (x0, y0, x1, y1, _) in enumerate(
            sorted(composantes(a), key=lambda t: (-(t[3] - t[1]) * (t[2] - t[0]))), 1):
        sous = a[y0:y1, x0:x1].copy()
        # tout ce qui n'appartient pas a l'objet est mis a plat transparent
        sous[:, :, 3] = np.where(sous[:, :, 3] > 128, 255, 0)
        pieces.append((f"{prefixe}_{i:02d}", Image.fromarray(sous, "RGBA")))
    return pieces


def cellules(v: int) -> int:
    return (v + TILE - 1) // TILE


def construire(pieces: list[tuple[str, Image.Image]], sortie: Path,
               manifeste: Path, largeur_cellules: int = 64) -> None:
    # rangement par hauteur decroissante : etagere simple, peu de gachis
    pieces = sorted(pieces, key=lambda p: -p[1].size[1])

    x = y = ligne_h = 0
    place = []
    for nom, im in pieces:
        cw, ch = cellules(im.size[0]), cellules(im.size[1])
        if x + cw > largeur_cellules:
            x = 0
            y += ligne_h + MARGE
            ligne_h = 0
        place.append((nom, im, x, y, cw, ch))
        x += cw + MARGE
        ligne_h = max(ligne_h, ch)
    hauteur_cellules = y + ligne_h

    sheet = Image.new("RGBA",
                      (largeur_cellules * TILE, hauteur_cellules * TILE),
                      (0, 0, 0, 0))
    entrees = []
    for nom, im, cx, cy, cw, ch in place:
        sheet.paste(im, (cx * TILE, cy * TILE), im)
        entrees.append({
            "nom": nom,
            "cellule_x": cx, "cellule_y": cy,
            "cellules_w": cw, "cellules_h": ch,
            "px_x": cx * TILE, "px_y": cy * TILE,
            "px_w": im.size[0], "px_h": im.size[1],
        })

    sheet.save(sortie)
    manifeste.write_text(json.dumps(
        {"tile": TILE,
         "sheet": sortie.name,
         "cellules": [largeur_cellules, hauteur_cellules],
         "objets": entrees},
        indent=2, ensure_ascii=False))

    a = np.array(sheet)
    al = a[:, :, 3]
    op = al > 200
    par_tuile = []
    for yy in range(0, a.shape[0] - TILE + 1, TILE):
        for xx in range(0, a.shape[1] - TILE + 1, TILE):
            t = a[yy:yy + TILE, xx:xx + TILE]
            m = t[:, :, 3] > 200
            if m.sum() < 8:
                continue
            par_tuile.append(len(np.unique(t[:, :, :3][m], axis=0)))
    print(f"\n{sortie.name} : {sheet.size[0]}x{sheet.size[1]} px "
          f"= {largeur_cellules}x{hauteur_cellules} cellules")
    print(f"  objets            : {len(entrees)}")
    print(f"  couleurs          : {len(np.unique(a[:, :, :3][op], axis=0))}")
    print(f"  semi-transparents : {int(((al > 0) & (al < 255)).sum())}")
    if par_tuile:
        pt = np.array(par_tuile)
        print(f"  couleurs / tuile  : moyenne {pt.mean():.1f}  max {pt.max()}"
              f"   tuiles <=16 : {100 * (pt <= 16).mean():.1f}%")


def main() -> int:
    sources = [
        (RACINE / "reference" / "spinda_cafe_eos_objets.png", "spinda"),
        (RACINE / "reference" / "metano_cafe_objets.png", "metano"),
        (RACINE / "reference" / "decor_cafe_genere.png", "decor"),
    ]
    pieces: list[tuple[str, Image.Image]] = []
    for chemin, prefixe in sources:
        if not chemin.exists():
            print(f"absent : {chemin}", file=sys.stderr)
            continue
        p = decouper(chemin, prefixe)
        print(f"{chemin.name:38s} -> {len(p)} objets")
        pieces += p

    dossier = RACINE / "meubles"
    dossier.mkdir(exist_ok=True)
    construire(pieces, dossier / "meubles_cafe_tilesheet.png",
               dossier / "meubles_cafe_tilesheet.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
