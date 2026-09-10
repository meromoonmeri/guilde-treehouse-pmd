from __future__ import annotations

"""Cale un calque d'interieur sur la grille 8 px de PMDO.

Le cadre fait deja 456 x 320 px = 57 x 40 cellules (viewport de l'interieur du
cafe de Metano Town). Mais la salle elle-meme y est posee a l'offset x=20 pour
une largeur de 415 px : ni l'un ni l'autre n'est un multiple de 8, donc les
bords de la salle tombent au milieu des tuiles et le decoupage en `.tile` serait
decale.

Ce script recadre la salle sur des frontieres de cellules :
  1. recadre au contenu reel,
  2. arrondit largeur et hauteur au multiple de 8 superieur,
  3. repositionne a un offset multiple de 8, au plus pres du centre,
  4. produit en plus un apercu avec la grille en surimpression.

Usage :
    python3 caler_grille8_interieur.py <fichier.png> [...]
"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw
import numpy as np

TILE = 8
CADRE_W, CADRE_H = 456, 320


def snap(valeur: int, pas: int = TILE) -> int:
    """Arrondit au multiple de `pas` le plus proche."""
    return int(round(valeur / pas)) * pas


def traiter(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    box = im.getbbox()
    if box is None:
        print(f"{path.name} : image vide")
        return

    salle = im.crop(box)
    sw, sh = salle.size

    # dimensions arrondies au multiple de 8 superieur
    gw = (sw + TILE - 1) // TILE * TILE
    gh = (sh + TILE - 1) // TILE * TILE

    # la salle est centree dans son bloc de cellules
    bloc = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    bloc.paste(salle, ((gw - sw) // 2, gh - sh), salle)

    # offset dans le cadre, ramene sur la grille
    ox = max(0, min(CADRE_W - gw, snap((CADRE_W - gw) // 2)))
    oy = max(0, min(CADRE_H - gh, snap((CADRE_H - gh) // 2)))

    cadre = Image.new("RGBA", (CADRE_W, CADRE_H), (0, 0, 0, 0))
    cadre.paste(bloc, (ox, oy), bloc)

    out = path.with_name(path.stem + "_grille8.png")
    cadre.save(out)

    al = np.array(cadre)[:, :, 3]
    semi = int(((al > 8) & (al < 248)).sum())
    print(f"{path.name:34s} salle {sw}x{sh} -> bloc {gw}x{gh}"
          f" = {gw // TILE}x{gh // TILE} cellules"
          f"  offset ({ox},{oy})  semi={semi}")
    print(f"    -> {out.name}")

    # apercu avec la grille, pour verifier le calage a l'oeil
    zoom = 2
    ap = cadre.resize((CADRE_W * zoom, CADRE_H * zoom), Image.NEAREST)
    fond = Image.new("RGBA", ap.size, (26, 26, 32, 255))
    fond.alpha_composite(ap)
    d = ImageDraw.Draw(fond)
    for x in range(0, CADRE_W + 1, TILE):
        clair = (x % (TILE * 8) == 0)
        d.line([(x * zoom, 0), (x * zoom, fond.height)],
               fill=(255, 120, 120, 190) if clair else (120, 200, 255, 70))
    for y in range(0, CADRE_H + 1, TILE):
        clair = (y % (TILE * 8) == 0)
        d.line([(0, y * zoom), (fond.width, y * zoom)],
               fill=(255, 120, 120, 190) if clair else (120, 200, 255, 70))
    apercu = path.with_name(path.stem + "_grille8_apercu.png")
    fond.convert("RGB").save(apercu)
    print(f"    -> {apercu.name} (apercu grille)")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    print(f"Grille PMDO : cellules de {TILE} px, "
          f"cadre {CADRE_W}x{CADRE_H} = {CADRE_W // TILE}x{CADRE_H // TILE} cellules\n")
    for a in args:
        traiter(Path(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
