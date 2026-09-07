"""
generer.py — génère les calques de foulard pour toutes les lignées,
au format SpriteCollab, plus les aperçus animés et le manifeste.

    python3 generer.py            # tout
    python3 generer.py 0004 0006  # seulement ces Pokémon
"""

import os
import sys
import json
import shutil
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P
import foulard as F
import lignees as L

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOS_CALQUES = os.path.join(RACINE, "calques")
DOS_APERCUS = os.path.join(RACINE, "apercus")
FICH_REGLAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglages.json")


def reglage_pour(pid, reglages, dossier, anims):
    r = dict(reglages.get("_defaut", {}))
    r.update({k: v for k, v in reglages.get(pid, {}).items() if not k.startswith("_")})
    r.setdefault("largeur_cou", P.largeur_cou(dossier, anims))
    r.setdefault("rayon_tete", P.rayon_tete(dossier, anims))
    r.setdefault("biais", P.biais_direction(dossier, anims))
    return r


def gif_animation(dossier_src, dossier_cal, nom_anim, chemin, dirs=(0, 2, 4, 6),
                  echelle=3, fond=(38, 38, 48)):
    """Aperçu animé : sprite SpriteCollab + calque de foulard, plusieurs directions."""
    _, anims = P.lire_animdata(dossier_src)
    a = next((x for x in anims if x["nom"] == nom_anim and not x["copie_de"]), None)
    if a is None:
        return False
    base = np.array(Image.open(os.path.join(dossier_src, f"{nom_anim}-Anim.png")).convert("RGBA"))
    cal = np.array(Image.open(os.path.join(dossier_cal, f"{nom_anim}-Anim.png")).convert("RGBA"))
    w, h = a["w"], a["h"]
    cols, rows = base.shape[1] // w, base.shape[0] // h
    dd = [d for d in dirs if d < rows] if rows == 8 else [0]
    images = []
    for c in range(cols):
        vue = Image.new("RGBA", (w * len(dd), h), fond + (255,))
        for j, d in enumerate(dd):
            b = Image.fromarray(base[d * h:(d + 1) * h, c * w:(c + 1) * w])
            s = Image.fromarray(cal[d * h:(d + 1) * h, c * w:(c + 1) * w])
            vue.paste(Image.alpha_composite(b, s), (j * w, 0))
        images.append(vue.convert("P", palette=Image.ADAPTIVE, colors=255)
                      .resize((vue.size[0] * echelle, vue.size[1] * echelle), Image.NEAREST))
    durees = [max(40, int(round(d * 1000 / 60.0))) for d in a["durees"]][:len(images)]
    while len(durees) < len(images):
        durees.append(durees[-1] if durees else 100)
    images[0].save(chemin, save_all=True, append_images=images[1:],
                   duration=durees, loop=0, disposal=2, optimize=True)
    return True


def main(filtre=None):
    reglages = json.load(open(FICH_REGLAGES))
    palettes = L.attribuer_palettes()
    os.makedirs(DOS_CALQUES, exist_ok=True)
    os.makedirs(DOS_APERCUS, exist_ok=True)

    manifeste = {
        "format": "PMDCollab / SpriteCollab — calque de superposition",
        "source": "https://github.com/PMDCollab/SpriteCollab",
        "genere_le": time.strftime("%Y-%m-%d"),
        "principe": ("Chaque PNG est une planche de foulard seule, strictement "
                     "alignée sur le Anim.png correspondant de SpriteCollab : "
                     "mêmes dimensions, même grille, même ordre de directions. "
                     "Composer par-dessus le sprite d'origine, sans décalage."),
        "directions": F.NOMS_DIRECTIONS,
        "palettes": {k: "#%02X%02X%02X" % v for k, v in F.PALETTES.items()},
        "lignees": [],
    }

    t0 = time.time()
    total_cases = 0
    for lg in L.LIGNEES:
        nom_pal = palettes[lg["cle"]]
        pal = F.rampe(F.PALETTES[nom_pal])
        entree = {"cle": lg["cle"], "type": lg["type"], "palette": nom_pal,
                  "rampe": {k: "#%02X%02X%02X" % v for k, v in pal.items()},
                  "membres": []}
        for pid, en, fr in lg["membres"]:
            if filtre and pid not in filtre:
                continue
            src = os.path.join(P.DOS_SPRITE, pid)
            dst = os.path.join(DOS_CALQUES, f"{pid.replace('/', '-')}_{fr.replace(' ', '_')}")
            _, anims = P.lire_animdata(src)
            r = reglage_pour(pid, reglages, src, anims)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            info = P.generer_pokemon(pid, src, dst, pal, r, nom_pal, fr, en)
            info["dossier"] = os.path.relpath(dst, RACINE)
            total_cases += info["cases"]
            entree["membres"].append(info)
            print(f"  {pid} {fr:<12} {len(info['animations_rendues']):>3} anims  "
                  f"{info['cases']:>5} cases  ({nom_pal})")

            for an in ("Walk", "Idle", "Attack"):
                g = os.path.join(DOS_APERCUS, f"{pid.replace('/', '-')}_{fr.replace(' ', '_')}_{an}.gif")
                try:
                    gif_animation(src, dst, an, g)
                except Exception as e:
                    print(f"    ! aperçu {an} : {e}")
        if entree["membres"]:
            manifeste["lignees"].append(entree)

    manifeste["total_cases_rendues"] = total_cases
    manifeste["total_pokemon"] = sum(len(l["membres"]) for l in manifeste["lignees"])
    json.dump(manifeste, open(os.path.join(RACINE, "manifeste.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"\n{manifeste['total_pokemon']} Pokémon, {total_cases} cases rendues "
          f"en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
