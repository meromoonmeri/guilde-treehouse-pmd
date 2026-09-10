from __future__ import annotations

"""Remet une image generee au format exact de la source, fond transparent.

Le generateur renvoie un PNG agrandi et SANS canal alpha : le damier de
transparence de l'apercu est peint en dur, avec du bruit de compression. Le
detourer par la couleur laisse toujours un quadrillage residuel.

Methode retenue, bien plus fiable : l'image source possede deja un alpha
parfait, et la generation est cadree de la meme facon (verifie : ecart moyen
de 20/255 sur la zone opaque, 220/255 sur le fond). On reutilise donc l'alpha
de la source, en y ajoutant les zones ou la generation a legitimement ajoute
de la matiere en dehors du sujet d'origine (ici les festons de lumiere qui
debordent sous le seuil de la porte).

Usage :
    python3 nettoyer_sortie_generee.py <source.png> <generee.png> <sortie.png>
"""

from pathlib import Path
import sys

from PIL import Image, ImageFilter
import numpy as np


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    src_p, gen_p, out_p = (Path(a) for a in sys.argv[1:4])

    src = Image.open(src_p).convert("RGBA")
    gen = Image.open(gen_p).convert("RGB").resize(src.size, Image.LANCZOS)
    print(f"Source  : {src.size}")
    print(f"Generee : {Image.open(gen_p).size} -> recadree en {gen.size}")

    sa = np.array(src).astype(int)
    ga = np.array(gen).astype(int)
    r, g, b = ga[:, :, 0], ga[:, :, 1], ga[:, :, 2]

    # Le damier est strictement gris neutre. Tout ce qui est colore est du sujet.
    neutral = (abs(r - g) <= 10) & (abs(g - b) <= 10) & (abs(r - b) <= 10)

    src_alpha = sa[:, :, 3]
    keep = src_alpha > 8                      # le sujet d'origine

    # Matiere ajoutee par la generation en dehors du sujet : non neutre, donc
    # ni damier ni fond. C'est ce qui laisse passer les festons de lumiere.
    added = (~neutral) & (~keep)

    # On ne garde que les ajouts formant des amas francs, pour ecarter le
    # lisere de compression qui borde le sujet.
    amas = Image.fromarray((added * 255).astype(np.uint8), "L")
    amas = amas.filter(ImageFilter.MedianFilter(5))
    added = np.array(amas) > 127

    mask = keep | added

    out = np.zeros_like(sa, dtype=np.uint8)
    out[:, :, :3] = ga[:, :, :3]
    # Alpha : celui de la source la ou elle existe (bords antialiases
    # preserves), plein pour la matiere ajoutee.
    alpha = np.where(keep, src_alpha, 0)
    alpha = np.where(added, 255, alpha)
    out[:, :, 3] = alpha
    out[~mask] = (0, 0, 0, 0)

    im = Image.fromarray(out, "RGBA")
    im.save(out_p)

    print(f"Sujet source   : {int(keep.sum())} px")
    print(f"Matiere ajoutee: {int(added.sum())} px (festons sous le seuil)")
    print(f"Sortie  : {im.size}  transparent={int((alpha == 0).sum())} px"
          f"  -> {out_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
