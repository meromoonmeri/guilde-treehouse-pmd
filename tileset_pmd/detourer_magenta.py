from __future__ import annotations

"""Detoure une generation faite sur fond magenta, en rendu pixel-art net.

Demander au generateur un fond magenta uni (#FF00FF) evite le damier de
transparence peint en dur, impossible a retirer proprement quand le sujet
contient lui aussi des gris. Le magenta pur est absent de la palette du cafe,
donc le detourage est franc.

Le generateur rend en ~1327x784 alors que la cible fait 425x251. Reduire en
LANCZOS **moyenne** les pixels : les bords deviennent flous et les couleurs se
delavent (les fioles du comptoir viraient au sepia). Mesures a l'appui :

    reference Halcyon    0 % de pixels semi-transparents, gradient moyen 15,3
    reduction LANCZOS    4,3 % de bords flous,            gradient moyen 10,2

Or la generation est dessinee sur une grille reguliere d'environ 3,1 px. On
reechantillonne donc par **couleur majoritaire** de chaque bloc : chaque pixel
de sortie reprend une teinte reellement presente dans la source, jamais une
moyenne. Les aplats restent purs, les bords restent tranches, l'alpha reste
binaire comme sur un vrai sprite.

Usage :
    python3 detourer_magenta.py <source.png> <generee.png> <sortie.png>
"""

from collections import Counter
from pathlib import Path
import sys

from PIL import Image, ImageFilter
import numpy as np


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
            # bloc majoritairement vide -> pixel transparent (alpha binaire)
            if len(vis) * 2 < len(blk):
                continue
            col = Counter(map(tuple, vis[:, :3])).most_common(1)[0][0]
            out[y, x] = (col[0], col[1], col[2], 255)
    return out


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    src_p, gen_p, out_p = (Path(a) for a in sys.argv[1:4])

    src = Image.open(src_p).convert("RGBA")
    gen = Image.open(gen_p).convert("RGB")
    print(f"Source  : {src.size}")
    print(f"Generee : {gen.size}")

    arr = np.array(gen)
    bg = magenta_mask(arr)
    print(f"Fond magenta : {int(bg.sum())} px ({100 * bg.mean():.1f}%)")

    # Dilate de 1 px pour manger le lisere de compression autour du sujet.
    m = Image.fromarray((bg * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
    bg = np.array(m) > 127

    rgba = np.dstack([arr, np.where(bg, 0, 255)]).astype(np.uint8)
    cut = Image.fromarray(rgba, "RGBA")
    box = cut.getbbox()
    if box is None:
        print("Image vide apres detourage.")
        return 1
    sub = np.array(cut.crop(box)).astype(int)
    print(f"Sujet   : {box[2] - box[0]}x{box[3] - box[1]} (bbox {box})")

    sbox = src.getbbox()
    tw, th = sbox[2] - sbox[0], sbox[3] - sbox[1]
    small = resample_mode(sub, tw, th)

    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    piece = Image.fromarray(small, "RGBA")
    out.paste(piece, (sbox[0], sbox[1]), piece)
    out.save(out_p)

    al = np.array(out)[:, :, 3]
    semi = int(((al > 8) & (al < 248)).sum())
    print(f"Sortie  : {out.size}  transparent={int((al == 0).sum())} px  "
          f"bords semi-transparents={semi}  -> {out_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
