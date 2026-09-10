from __future__ import annotations

"""Met un calque de decoration au meme cadre que la salle, sans le recadrer.

Le calque de deco est genere a partir du calque decore deja au format PMDO
(456 x 320), sur fond magenta uni. Le generateur le rend agrandi, mais il
conserve le CADRE ENTIER : la sortie est donc simplement le cadre 456 x 320
mis a l'echelle. On ne doit surtout pas recadrer sur le contenu (`getbbox`),
sinon le calque se recentre sur les meubles et ne se superpose plus a la salle.

La marche a suivre est donc :
  1. detourer le magenta,
  2. reduire l'image ENTIERE a 456 x 320, par couleur dominante de bloc,
  3. appliquer le meme decalage que `caler_grille8_interieur.py` a inflige a
     la salle, mesure en comparant la salle avant et apres calage.

Le decalage est lu sur les fichiers de la salle, jamais suppose : le calque
suit exactement le meme mouvement que le decor qu'il habille.

Usage :
    python3 caler_calque_deco.py <deco_brut.png> <salle_avant.png> <salle_grille8.png> <sortie.png>
"""

from collections import Counter
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageFilter

CIBLE_W, CIBLE_H = 456, 320


def magenta_mask(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(int)
    g = rgb[:, :, 1].astype(int)
    b = rgb[:, :, 2].astype(int)
    return (r > 140) & (b > 140) & (g < 110) & ((r - g) > 60) & ((b - g) > 60)


def resample_mode(sub: np.ndarray, tw: int, th: int) -> np.ndarray:
    h, w, _ = sub.shape
    out = np.zeros((th, tw, 4), dtype=np.uint8)
    for y in range(th):
        y0 = int(y * h / th)
        y1 = max(y0 + 1, int((y + 1) * h / th))
        for x in range(tw):
            x0 = int(x * w / tw)
            x1 = max(x0 + 1, int((x + 1) * w / tw))
            blk = sub[y0:y1, x0:x1].reshape(-1, 4)
            vis = blk[blk[:, 3] > 128]
            if len(vis) * 2 < len(blk):
                continue
            col = Counter(map(tuple, vis[:, :3])).most_common(1)[0][0]
            out[y, x] = (col[0], col[1], col[2], 255)
    return out


def detourer(path: Path) -> Image.Image:
    im = Image.open(path)
    arr = np.array(im)
    if im.mode != "RGBA" or arr[:, :, 3].min() == 255:
        rgb = np.array(im.convert("RGB"))
        bg = magenta_mask(rgb)
        m = Image.fromarray((bg * 255).astype(np.uint8), "L")
        bg = np.array(m.filter(ImageFilter.MaxFilter(3))) > 127
        rgba = np.dstack([rgb, np.where(bg, 0, 255)]).astype(np.uint8)
        return Image.fromarray(rgba, "RGBA")
    return im.convert("RGBA")


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__)
        return 1
    brut, avant, apres, sortie = (Path(p) for p in sys.argv[1:])

    # decalage subi par la salle lors du calage sur la grille de 8 px
    b_av = Image.open(avant).convert("RGBA").getbbox()
    b_ap = Image.open(apres).convert("RGBA").getbbox()
    dx, dy = b_ap[0] - b_av[0], b_ap[1] - b_av[1]

    im = detourer(brut)
    petit = resample_mode(np.array(im).astype(int), CIBLE_W, CIBLE_H)

    cadre = Image.new("RGBA", (CIBLE_W, CIBLE_H), (0, 0, 0, 0))
    piece = Image.fromarray(petit, "RGBA")
    cadre.paste(piece, (dx, dy), piece)
    cadre.save(sortie)

    al = np.array(cadre)[:, :, 3]
    semi = int(((al > 8) & (al < 248)).sum())
    visibles = int((al > 128).sum())
    print(f"{sortie.name:36s} {CIBLE_W}x{CIBLE_H}  decalage ({dx},{dy})"
          f"  {visibles} px visibles  semi={semi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
