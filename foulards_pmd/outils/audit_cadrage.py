"""
audit_cadrage.py — auto-audit géométrique des foulards.

Mesure, pour chaque Pokémon et chaque direction, si le col est bien cadré :
hauteur relative dans la silhouette, largeur relative, débordement hors du
corps, traînée sous les pieds, écart au port de tête. Écrit un JSON et
affiche les cas hors tolérance.
"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P, foulard as F, lignees as L

# tolérances : (min, max)
TOL = {
    "releve_epaule": (-0.02, 0.26),  # (épaules - col) / taille du corps
    "largeur_rel_f": (0.28, 0.80),   # col / largeur du corps, vues de face/dos
    "largeur_rel_d": (0.18, 0.64),   # idem, vues diagonales
    "largeur_rel_p": (0.10, 0.46),   # idem, vues de profil
    "hors_corps":    (0.00, 0.16),   # part du bandeau hors silhouette
    "sous_pieds":    (-99.0, 1.5),   # dépassement sous les pieds, en px
    "ecart_tete":    (0.00, 0.30),   # |col_x - tete_x| / largeur du corps
}


def mesurer(pid, nom_fr, pal, reglage, anim_nom="Idle"):  # noqa: C901
    src = f"{P.DOS_SPRITE}/{pid}"
    _, anims = P.lire_animdata(src)
    a = next(x for x in anims if x["nom"] == anim_nom and not x["copie_de"])
    anim, off = P.charger_planche(src, anim_nom)
    w, h = a["w"], a["h"]
    cols, rows = anim.shape[1] // w, anim.shape[0] // h
    tc = P.taille_corps(anim, w, h, cols, rows)
    out = []
    for d in (range(8) if rows == 8 else [0]):
        masque = anim[d * h:(d + 1) * h, 0:w, 3] > 0
        if not masque.any():
            continue
        mk = F.marqueurs_case(off, 0, d * h, w, h)
        infos = {}
        px = F.dessiner_foulard(masque, mk, d, 0.0, F.energie(anim_nom),
                                pal, reglage, tc, infos=infos)
        alpha = px[..., 3] > 0
        if not alpha.any() or "bx" not in infos:
            continue
        ys = np.nonzero(masque.any(axis=1))[0]
        xs = np.nonzero(masque.any(axis=0))[0]
        haut, bas = float(ys[0]), float(ys[-1])
        lcorps = float(xs[-1] - xs[0] + 1)

        # bandeau : pixels réellement posés en couche « col » (z >= 3)
        bande = infos.get("bandeau")
        if bande is None or not bande.any():
            continue
        nb = int(bande.sum())
        hors = float((bande & ~masque).sum()) / nb if nb else 0.0

        bxs = np.nonzero(bande.any(axis=0))[0]
        larg = float(bxs[-1] - bxs[0] + 1) if len(bxs) else 0.0
        col_x = float((bxs[0] + bxs[-1]) / 2) if len(bxs) else infos["bx"]

        sys_ = np.nonzero(alpha.any(axis=1))[0]
        sous = float(sys_[-1] - bas)

        # le décentrage se mesure par rapport à l'axe du corps, pas au museau :
        # le marqueur de tête est projeté en avant sur les vues de profil.
        bi = reglage.get("biais") or [(0.0, 0.0)] * 8
        tete_x = (mk["tete"][0] - bi[d][0]) if mk["tete"] else col_x
        profil = abs(F.DIRECTIONS[d][0]) > 0.9
        diag = 0.3 < abs(F.DIRECTIONS[d][0]) < 0.9

        if mk["main_g"] and mk["main_d"]:
            ep_y = (mk["main_g"][1] + mk["main_d"][1]) / 2.0
            releve = (ep_y - infos["ny"]) / max(tc, 1)
        else:
            releve = 0.10
        out.append({
            "dir": F.NOMS_DIRECTIONS[d], "profil": profil, "diag": diag,
            "releve_epaule": round(releve, 3),
            "hauteur_rel": round((infos["ny"] - haut) / max(bas - haut, 1), 3),
            "largeur_rel": round(larg / max(lcorps, 1), 3),
            "hors_corps": round(hors, 3),
            "sous_pieds": round(sous, 1),
            "ecart_tete": round(abs(col_x - tete_x) / max(lcorps, 1), 3),
        })
    return out


def verdict(m):
    d = []
    lo, hi = TOL["releve_epaule"]
    if not lo <= m["releve_epaule"] <= hi:
        d.append(f"hauteur {m['releve_epaule']}")
    cls = "largeur_rel_p" if m["profil"] else ("largeur_rel_d" if m.get("diag") else "largeur_rel_f")
    lo, hi = TOL[cls]
    if not lo <= m["largeur_rel"] <= hi:
        d.append(f"largeur {m['largeur_rel']}")
    if m["hors_corps"] > TOL["hors_corps"][1]:
        d.append(f"hors-corps {m['hors_corps']}")
    if m["sous_pieds"] > TOL["sous_pieds"][1]:
        d.append(f"sous-pieds {m['sous_pieds']}")
    if m["ecart_tete"] > TOL["ecart_tete"][1]:
        d.append(f"decentre {m['ecart_tete']}")
    return d


def main():
    reglages = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "reglages.json")))
    pals = L.attribuer_palettes()
    rap = {"tolerances": TOL, "pokemon": {}}
    tot = ko = 0
    par_defaut = {}
    for lg in L.LIGNEES:
        pal = F.rampe(F.PALETTES[pals[lg["cle"]]])
        for pid, en, fr in lg["membres"]:
            src = f"{P.DOS_SPRITE}/{pid}"
            _, anims = P.lire_animdata(src)
            r = dict(reglages.get("_defaut", {}))
            r.update({k: v for k, v in reglages.get(pid, {}).items()
                      if not k.startswith("_")})
            r.setdefault("largeur_cou", P.largeur_cou(src, anims))
            r.setdefault("rayon_tete", P.rayon_tete(src, anims))
            r.setdefault("biais", P.biais_direction(src, anims))
            ms = mesurer(pid, fr, pal, r)
            defs = []
            for m in ms:
                v = verdict(m)
                m["defauts"] = v
                tot += 1
                if v:
                    ko += 1
                    defs.append(f"{m['dir']}: " + ", ".join(v))
                    for x in v:
                        par_defaut[x.split()[0]] = par_defaut.get(x.split()[0], 0) + 1
            rap["pokemon"][pid] = {"nom": fr, "mesures": ms}
            if defs:
                print(f"{pid} {fr:<12} " + " | ".join(defs))
    rap["resume"] = {"vues": tot, "hors_tolerance": ko,
                     "taux_conforme": round(100 * (tot - ko) / tot, 1),
                     "par_defaut": par_defaut}
    json.dump(rap, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "audit_cadrage.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"\n{tot - ko}/{tot} vues conformes ({rap['resume']['taux_conforme']} %)")
    print("défauts :", par_defaut)


if __name__ == "__main__":
    main()
