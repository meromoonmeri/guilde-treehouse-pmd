from __future__ import annotations

"""Detoure une generation faite sur fond magenta et la remet au format source.

Demander au generateur un fond magenta uni (#FF00FF) evite le damier de
transparence peint en dur, impossible a retirer proprement quand le sujet
contient lui aussi des gris. Le magenta pur est absent de la palette du cafe,
donc le detourage est net.

Etapes :
  1. masque magenta (teinte rouge+bleu forts, vert faible), dilate pour manger
     le lisere de compression,
  2. recadrage sur le sujet,
  3. reprojection dans la bbox exacte de la source, pour garder taille et
     position au pixel pres.

Usage :
    python3 detourer_magenta.py <source.png> <generee.png> <sortie.png>
"""

from pathlib import Path
import sys

from PIL import Image, ImageFilter
import numpy as np


def magenta_mask(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(int)
    g = rgb[:, :, 1].astype(int)
    b = rgb[:, :, 2].astype(int)
    # Magenta : rouge et bleu eleves, vert nettement plus bas.
    return (r > 140) & (b > 140) & (g < 110) & ((r - g) > 60) & ((b - g) > 60)


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
    print(f"Fond magenta detecte : {int(bg.sum())} px "
          f"({100 * bg.mean():.1f}% de l'image)")

    # Le bord du sujet garde un lisere magenta du a la compression : on etend
    # legerement le fond pour l'absorber.
    m = Image.fromarray((bg * 255).astype(np.uint8), "L")
    m = m.filter(ImageFilter.MaxFilter(3))
    bg = np.array(m) > 127

    rgba = np.dstack([arr, np.where(bg, 0, 255).astype(np.uint8)])
    cut = Image.fromarray(rgba, "RGBA")

    box = cut.getbbox()
    if box is None:
        print("Image vide apres detourage.")
        return 1
    subject = cut.crop(box)
    print(f"Sujet   : {subject.size} (bbox {box})")

    sbox = src.getbbox()
    tw, th = sbox[2] - sbox[0], sbox[3] - sbox[1]
    scaled = subject.resize((tw, th), Image.LANCZOS)

    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out.paste(scaled, (sbox[0], sbox[1]), scaled)
    out.save(out_p)

    a = np.array(out)
    print(f"Sortie  : {out.size}  transparent={int((a[:, :, 3] == 0).sum())} px"
          f"  -> {out_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
