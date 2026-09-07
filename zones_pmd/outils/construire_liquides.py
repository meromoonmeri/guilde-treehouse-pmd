"""Construit les jeux de tuiles de liquide animés, pour Tiled et Aseprite."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "foulards_pmd", "outils"))
from PIL import Image
import liquides as L
import dpla as DPLA

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(RACINE, "sources_ia", "tuiles_liquides.png")
DUREE_MS = 100          # 6 tics à 60 Hz


def main():
    for d in ("tuiles", "tiled", "aseprite", "apercus"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)

    brutes = L.decouper(SRC)
    if len(brutes) < 2:
        raise SystemExit("découpe insuffisante")
    moitie = len(brutes) // 2
    lots = {"eau": brutes[:moitie], "lave": brutes[moitie:]}

    resume = {}
    for nom, tuiles in lots.items():
        tuiles = [L.rendre_raccordable(t) for t in tuiles]
        cartes, rampe = L.indexer_sur_rampe(tuiles, n_couleurs=12)
        suites, table = L.images_dpla(cartes, rampe, n_images=12)
        planche, n_img, n_tuiles = L.planche_animee(suites)

        img_rel = f"../tuiles/{nom}_anim.png"
        planche.save(os.path.join(RACINE, "tuiles", f"{nom}_anim.png"),
                     optimize=True)
        L.ecrire_tsx(os.path.join(RACINE, "tiled", f"{nom}.tsx"),
                     f"pmd_{nom}", img_rel, n_img, n_tuiles, DUREE_MS,
                     planche.size[0], planche.size[1])
        L.ecrire_aseprite(os.path.join(RACINE, "aseprite", f"{nom}.aseprite"),
                          suites, DUREE_MS)
        table.ecrire_json(os.path.join(RACINE, "tuiles", f"{nom}_dpla.json"))

        # aperçu : nappe 6 x 4 tuiles, animée
        cadres = []
        for k in range(n_img):
            nappe = Image.new("RGB", (6 * L.T, 4 * L.T))
            for y in range(4):
                for x in range(6):
                    nappe.paste(suites[(x + y) % n_tuiles][k], (x * L.T, y * L.T))
            cadres.append(nappe.resize((6 * L.T * 3, 4 * L.T * 3), Image.NEAREST)
                          .convert("P", palette=Image.ADAPTIVE, colors=64))
        cadres[0].save(os.path.join(RACINE, "apercus", f"liquide_{nom}.gif"),
                       save_all=True, append_images=cadres[1:],
                       duration=DUREE_MS, loop=0, disposal=2, optimize=True)

        resume[nom] = {"tuiles": n_tuiles, "images": n_img,
                       "rampe": ["#%02X%02X%02X" % c for c in rampe],
                       "periode_tics": table.periode(0),
                       "planche": f"tuiles/{nom}_anim.png",
                       "tiled": f"tiled/{nom}.tsx",
                       "aseprite": f"aseprite/{nom}.aseprite",
                       "table_dpla": f"tuiles/{nom}_dpla.json"}
        print(f"  {nom}: {n_tuiles} tuiles x {n_img} images, "
              f"rampe de {len(rampe)} couleurs, période {table.periode(0)} tics")

    json.dump(resume, open(os.path.join(RACINE, "tuiles", "liquides.json"), "w"),
              indent=1, ensure_ascii=False)
    print("\nempaqueté pour Tiled et Aseprite")


if __name__ == "__main__":
    main()
