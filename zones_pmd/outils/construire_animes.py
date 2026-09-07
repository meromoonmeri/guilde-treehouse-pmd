"""
construire_animes.py — jeux de tuiles animés au format Chunsoft.

Deux palettes animées, comme dans le jeu :
  palette 10  les liquides — toute la rampe miroite
  palette 11  les lueurs — seuls les crans clairs bougent, la pierre reste fixe

Sortie : planches de tuiles, `.tsx` Tiled avec blocs <animation>, `.aseprite`
multi-images avec tag, tables `dpla.json`, et cartes `.tmx` de démonstration.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "foulards_pmd", "outils"))
from PIL import Image
import liquides as L
import dpla as DPLA

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DUREE_MS = 100

# nom, planche source, tranche, palette DPLA visée, premier cran animé
JEUX = [
    ("eau",       "tuiles_liquides.png", (0, 4),  10, 0),
    ("lave",      "tuiles_liquides.png", (4, 8),  10, 0),
    ("lueurs",    "tuiles_animees.png",  (0, 4),  11, 6),
    # Chaque surface a sa propre gamme : les indexer sur une rampe commune
    # mélangeait les teintes et détruisait les quatre textures d'un coup.
    ("cascade",   "tuiles_animees.png",  (4, 5),  10, 2),
    ("marais",    "tuiles_animees.png",  (5, 6),  10, 2),
    ("sable",     "tuiles_animees.png",  (6, 7),  10, 6),
    ("rune",      "tuiles_animees.png",  (7, 8),  11, 5),
]


def main():
    for d in ("tuiles", "tiled", "aseprite", "apercus"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)
    cache = {}
    resume = {}
    for nom, src, (a, b), pal_cible, depuis in JEUX:
        if src not in cache:
            cache[src] = L.decouper(os.path.join(RACINE, "sources_ia", src))
        brutes = cache[src][a:b]
        if not brutes:
            print(f"  {nom}: aucune tuile"); continue
        # les surfaces et liquides doivent se raccorder, pas les objets posés
        tuiles = [L.rendre_raccordable(t) for t in brutes] if depuis < 6 else list(brutes)
        cartes, rampe = L.indexer_sur_rampe(tuiles, n_couleurs=12)
        table = DPLA.table_depuis_rampe(rampe, depuis=depuis)
        suites = []
        import numpy as np
        periode = table.periode(0) or 12
        pas = max(1, periode // 12)
        for carte in cartes:
            imgs = []
            for k in range(12):
                p = table.palette_a_l_image(0, k * pas)
                tab = np.array([p[i] if i < len(p) else rampe[min(i, len(rampe) - 1)]
                                for i in range(len(rampe))], dtype=np.uint8)
                # les crans laissés fixes gardent leur couleur d'origine
                for i in range(min(depuis, len(rampe))):
                    tab[i] = rampe[i]
                imgs.append(Image.fromarray(tab[np.clip(carte, 0, len(tab) - 1)], "RGB"))
            suites.append(imgs)

        planche, n_img, n_t = L.planche_animee(suites)
        planche.save(os.path.join(RACINE, "tuiles", f"{nom}_anim.png"), optimize=True)
        L.ecrire_tsx(os.path.join(RACINE, "tiled", f"{nom}.tsx"), f"pmd_{nom}",
                     f"../tuiles/{nom}_anim.png", n_img, n_t, DUREE_MS,
                     planche.size[0], planche.size[1])
        L.ecrire_aseprite(os.path.join(RACINE, "aseprite", f"{nom}.aseprite"),
                          suites, DUREE_MS)
        table.ecrire_json(os.path.join(RACINE, "tuiles", f"{nom}_dpla.json"))
        L.ecrire_tmx_demo(os.path.join(RACINE, "tiled", f"demo_{nom}.tmx"),
                          f"{nom}.tsx", nom, n_img=n_img, n_tuiles=n_t)

        cadres = []
        for k in range(n_img):
            nappe = Image.new("RGB", (6 * L.T, 4 * L.T))
            for y in range(4):
                for x in range(6):
                    nappe.paste(suites[(x + y) % n_t][k], (x * L.T, y * L.T))
            cadres.append(nappe.resize((6 * L.T * 3, 4 * L.T * 3), Image.NEAREST)
                          .convert("P", palette=Image.ADAPTIVE, colors=64))
        cadres[0].save(os.path.join(RACINE, "apercus", f"anim_{nom}.gif"),
                       save_all=True, append_images=cadres[1:], duration=DUREE_MS,
                       loop=0, disposal=2, optimize=True)

        animes = sum(1 for e in table.emplacements if e["images"])
        resume[nom] = {"tuiles": n_t, "images": n_img, "palette_dpla": pal_cible,
                       "crans_animes": animes, "premier_cran_anime": depuis,
                       "periode_tics": table.periode(0),
                       "rampe": ["#%02X%02X%02X" % c for c in rampe]}
        print(f"  {nom:9} {n_t} tuiles x {n_img} images | palette {pal_cible} | "
              f"{animes} crans animés à partir du cran {depuis}")

    json.dump(resume, open(os.path.join(RACINE, "tuiles", "animes.json"), "w"),
              indent=1, ensure_ascii=False)
    print("\nempaqueté : planches, .tsx Tiled, .aseprite, tables DPLA, .tmx de démo")


if __name__ == "__main__":
    main()
