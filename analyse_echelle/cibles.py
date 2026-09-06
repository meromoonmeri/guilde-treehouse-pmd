# -*- coding: utf-8 -*-
"""
Calcule les dimensions cibles de chaque salle a partir des mesures comparees.

Principe : le kit actuel est dessine environ 1,55 x trop grand par rapport a un
sprite Pokemon PMDO (~20 x 22 px). On applique donc un facteur d'echelle global
de 0,65 puis on arrondit les toiles au multiple de 24 px (la case PMD).

Sortie : analyse_echelle/cibles.json + tableau texte.
"""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TILE = 24
FACTEUR = 0.65

# fourchettes de reference relevees dans les guildes de Halcyon (cases de 24 px)
REFERENCE = {
    'chambre':     {'sol_cases2': (50, 60),  'emprise': ((9, 13), (7, 14))},
    'salle':       {'sol_cases2': (75, 110), 'emprise': ((12, 16), (9, 12))},
    'hub':         {'sol_cases2': (150, 200), 'emprise': ((24, 33), (11, 14))},
    'couloir':     {'sol_cases2': (35, 65),  'emprise': ((15, 20), (8, 11))},
}

# 02 est le seul vrai hub de la guilde ; 03 reste une salle commune moyenne
TYPES = {
    '01': 'salle', '02': 'hub', '03': 'salle', '04': 'salle', '05': 'chambre',
    '06': 'chambre', '07': 'chambre', '08': 'chambre', '09': 'salle',
    '10': 'chambre', '11': 'chambre', '12': 'salle',
}


def arrondi(v, pas=TILE):
    return int(round(v / float(pas)) * pas)


def main():
    mes = json.load(io.open(os.path.join(HERE, 'mesures.json'), encoding='utf-8'))
    out = {'facteur_echelle': FACTEUR, 'case_px': TILE, 'reference': REFERENCE,
           'salles': []}
    print('%-26s %-13s %-9s %-13s %-9s %-8s %-13s %s' % (
        'salle', 'toile actuelle', 'sol act.', 'toile x0.65', 'sol cible',
        'type', 'toile ajustee', 'note'))
    for m in mes['projet']:
        w, h = m['carte_px']
        nw, nh = arrondi(w * FACTEUR), arrondi(h * FACTEUR)
        sol = m['aire_sol_cases24']
        cible = round(sol * FACTEUR ** 2, 0)
        t = TYPES[m['id']]
        lo, hi = REFERENCE[t]['sol_cases2']
        if cible < lo:
            ajust = round((lo / max(cible, 1.0)) ** 0.5, 2)
            note = 'elargir de x%.2f apres reduction (sol vise %d cases2)' % (ajust, lo)
            aw, ah = arrondi(nw * ajust), arrondi(nh * ajust)
        elif cible > hi:
            ajust = round((hi / cible) ** 0.5, 2)
            note = 'reduire encore de x%.2f (sol vise %d cases2)' % (ajust, hi)
            aw, ah = arrondi(nw * ajust), arrondi(nh * ajust)
        else:
            ajust, note, aw, ah = 1.0, 'dans la fourchette Halcyon', nw, nh
        out['salles'].append({
            'ajustement': ajust, 'note': note,
            'toile_ajustee_px': [aw, ah],
            'toile_ajustee_cases': [round(aw / TILE, 1), round(ah / TILE, 1)],
            'id': m['id'], 'nom': m['titre'], 'type': t,
            'toile_actuelle_px': [w, h],
            'toile_cible_px': [nw, nh],
            'toile_cible_cases': [round(nw / TILE, 1), round(nh / TILE, 1)],
            'sol_actuel_cases2': sol,
            'sol_cible_cases2': cible,
            'sol_reference_halcyon_cases2': REFERENCE[t]['sol_cases2'],
            'reduction_surface': round(FACTEUR ** 2, 3),
        })
        print('%-26s %-13s %-9s %-13s %-9s %-8s %-13s %s' % (
            m['titre'][:26], '%dx%d' % (w, h), '%.0f' % sol,
            '%dx%d' % (nw, nh), '%.0f' % cible, t, '%dx%d' % (aw, ah), note))
    dest = os.path.join(HERE, 'cibles.json')
    with io.open(dest, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print('\necrit', dest)


if __name__ == '__main__':
    main()
