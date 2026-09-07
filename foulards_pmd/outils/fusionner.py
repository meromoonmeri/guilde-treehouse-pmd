"""
fusionner.py — produit des planches « Pokémon + foulard » prêtes à l'emploi
en composant le calque par-dessus le sprite SpriteCollab d'origine.

    python3 fusionner.py                 # tout, vers ../fusionnes/
    python3 fusionner.py 0004 0006       # seulement ces Pokémon
"""
import os, sys, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAL = os.path.join(RACINE, "calques")
OUT = os.path.join(RACINE, "fusionnes")


def main(filtre=None):
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for d in sorted(os.listdir(CAL)):
        pid = d.split("_")[0]
        if filtre and pid not in filtre:
            continue
        src = os.path.join(P.DOS_SPRITE, pid)
        dst = os.path.join(OUT, d)
        os.makedirs(dst, exist_ok=True)
        shutil.copy(os.path.join(CAL, d, "AnimData.xml"), dst)
        for f in sorted(os.listdir(os.path.join(CAL, d))):
            if not f.endswith("-Anim.png"):
                continue
            nom = f[:-len("-Anim.png")]
            base = Image.open(os.path.join(src, f)).convert("RGBA")
            haut = Image.open(os.path.join(CAL, d, f)).convert("RGBA")
            Image.alpha_composite(base, haut).save(os.path.join(dst, f), optimize=True)
            # les offsets et les ombres sont inchangés : on les reprend tels quels
            for suf in ("-Offsets.png", "-Shadow.png"):
                s = os.path.join(src, nom + suf)
                if os.path.isfile(s):
                    shutil.copy(s, dst)
            n += 1
        shutil.copy(os.path.join(src, "credits.txt"), dst)
    print(f"{n} planches fusionnées dans {OUT}")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
