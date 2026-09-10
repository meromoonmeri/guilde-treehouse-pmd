from __future__ import annotations

"""Met les calques d'interieur au format PMDO de Metano Town.

Reference mesuree dans `Palikadude/Halcyon` : l'interieur du cafe de Metano
(`Data/Ground/metano_cafe.rsground`) fait **456 x 320 px**, soit 57 x 40
cellules de 8 px. C'est le viewport d'une salle interieure PMDO.

Le generateur d'image rend en ~1160 x 894, sur fond magenta uni. Ce script :
  1. detoure le fond magenta (dilate de 1 px pour absorber la compression),
  2. recadre sur la salle,
  3. la reduit pour tenir dans 456 x 320 en gardant ses proportions,
  4. la centre dans un cadre de 456 x 320 exactement.

La reduction se fait par **couleur dominante** de chaque bloc, comme pour la
facade : un filtre classique moyennerait les pixels et rendrait les bords flous.

Usage :
    python3 mettre_interieur_echelle_pmdo.py <fichier.png> [...]
"""

from collections import Counter
from pathlib import Path
import sys

from PIL import Image, ImageFilter
import numpy as np

# Interieur du cafe de Metano Town, mesure sur les assets de Halcyon.
CIBLE_W, CIBLE_H = 456, 320
TILE = 8


def magenta_mask(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(int)
    g = rgb[:, :, 1].astype(int)
    b = rgb[:, :, 2].astype(int)
    return (r > 140) & (b > 140) & (g < 110) & ((r - g) > 60) & ((b - g) > 60)


def resample_mode(sub: np.ndarray, tw: int, th: int) -> np.ndarray:
    """Reduit en gardant, pour chaque bloc, sa couleur dominante."""
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


def traiter(path: Path) -> None:
    im = Image.open(path)
    src_size = im.size

    if im.mode != "RGBA" or np.array(im)[:, :, 3].min() == 255:
        # sortie brute du generateur : fond magenta a retirer
        rgb = np.array(im.convert("RGB"))
        bg = magenta_mask(rgb)
        m = Image.fromarray((bg * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
        bg = np.array(m) > 127
        rgba = np.dstack([rgb, np.where(bg, 0, 255)]).astype(np.uint8)
        im = Image.fromarray(rgba, "RGBA")
    else:
        im = im.convert("RGBA")

    box = im.getbbox()
    if box is None:
        print(f"{path.name} : image vide")
        return
    sub = np.array(im.crop(box)).astype(int)
    sh, sw = sub.shape[0], sub.shape[1]

    # tient dans le viewport sans deformer
    facteur = min(CIBLE_W / sw, CIBLE_H / sh)
    nw, nh = max(1, round(sw * facteur)), max(1, round(sh * facteur))
    petit = resample_mode(sub, nw, nh)

    cadre = Image.new("RGBA", (CIBLE_W, CIBLE_H), (0, 0, 0, 0))
    piece = Image.fromarray(petit, "RGBA")
    cadre.paste(piece, ((CIBLE_W - nw) // 2, (CIBLE_H - nh) // 2), piece)
    cadre.save(path)

    al = np.array(cadre)[:, :, 3]
    semi = int(((al > 8) & (al < 248)).sum())
    print(f"{path.name:34s} {str(src_size):12s} -> {CIBLE_W}x{CIBLE_H}"
          f"  salle {nw}x{nh}  facteur {facteur:.3f}  semi={semi}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    print(f"Viewport PMDO : {CIBLE_W} x {CIBLE_H} px "
          f"= {CIBLE_W // TILE} x {CIBLE_H // TILE} cellules de {TILE} px\n")
    for a in args:
        traiter(Path(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
