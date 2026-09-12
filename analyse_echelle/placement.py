# -*- coding: utf-8 -*-
"""
Proposition de placement automatique du mobilier, a l'echelle cible.

Pour chaque salle : on part du sol reduit (calques_reduits/.../01_sol.png), on
calcule la bande de mobilier (1,5 case le long des murs) et la zone de
circulation, puis on pose le nombre de props recommande par le gabarit
(analyse_echelle/guides/NN_plan.json) :

  - les grandes pieces centrales (tapis, table de banquet) au centre,
  - le mobilier au plus pres des murs, le plus etale possible,
  - la vegetation pour combler,
  - les elements muraux sur le bandeau de mur, hors fenetres,
  - les suspensions en haut du bandeau.

Contraintes : pieds sur le sol, pas de chevauchement, 2 cases degagees devant
chaque passage, couverture visee 30-45 % du sol.

Sorties :
  analyse_echelle/placements/NN_placement.json
  analyse_echelle/placements/NN_apercu.png + planche_placements.png
  calques_reduits/<salle>/<jour|nuit>/06_decorations.png et 07_objets.png
  salles_reduites/<salle>_<jour|nuit>.png (recomposes)
"""
import io, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apercus as ap  # noqa: E402

REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'placements')
TILE = ap.TILE
BANDE = int(1.5 * TILE)
DEGAGEMENT_PASSAGE = 2 * TILE

PALETTES = {
    '01': ['panneau', 'coffre_feuille', 'plante_tonneau', 'lanterne',
           'banniere_accueil_gauche', 'banniere_accueil_droite'],
    '02': ['panneau', 'fanion', 'coffre_feuille', 'provisions', 'fontaine_bois',
           'table_etude', 'lanterne', 'plante_tonneau', 'embleme_feuille_bois',
           'lampe_suspendue', 'applique_bois', 'applique_bois'],
    '03': ['fontaine_bois', 'table_etude', 'coffre_feuille', 'lanterne',
           'plante_tonneau', 'fanion', 'applique_bois'],
    '04': ['table_banquet', 'etagere_boissons', 'seau_cantine', 'provisions',
           'coffre_feuille', 'applique_bois'],
    '05': ['nid_mousse', 'nid_ambre', 'coffre_feuille', 'table_etude',
           'lanterne', 'applique_bois'],
    '06': ['armoire_veilleur', 'nid_sauge', 'coffre_feuille', 'lanterne',
           'applique_bois'],
    '07': ['nid_menthe', 'nid_ambre', 'coffre_feuille', 'plante_tonneau',
           'applique_bois'],
    '08': ['nid_mousse', 'nid_menthe', 'nid_sauge', 'coffre_feuille', 'lanterne'],
    '09': ['nid_ambre', 'nid_menthe', 'nid_mousse', 'nid_sauge', 'coffre_feuille',
           'coffre_feuille', 'lampe_suspendue'],
    '10': ['nid_sauge', 'nid_ambre', 'nid_mousse', 'coffre_feuille', 'lanterne'],
    '11': ['nid_menthe', 'nid_mousse', 'coffre_feuille', 'table_etude',
           'applique_bois'],
    '12': ['tapis_maitre', 'table_etude', 'fanion', 'banniere_maitre_centrale',
           'banniere_maitre_rouge', 'banniere_maitre_verte',
           'embleme_oeuf_quatre_ailes', 'coffre_feuille'],
}

CALQUE = {'mural': '06_decorations', 'suspendu': '06_decorations',
          'sol': '07_objets', 'tapis': '07_objets'}


def charger_props():
    d = json.load(io.open(os.path.join(REPO, 'sprites_reduits', 'props.json'),
                          encoding='utf-8'))
    return {p['id']: p for p in d['props']}


def vegetation_pour(idx, n, props):
    veg = sorted(p for p in props if p.startswith('vegetation'))
    petites = [v for v in veg if props[v]['taille'][1] <= 40] or veg
    debut = (idx * 7) % len(petites)
    return [petites[(debut + k * 3) % len(petites)] for k in range(n)]


def masque_sol(dossier):
    """Sol praticable : pixels opaques du calque de sol, hors zones tres sombres
    (trou vers l'etage inferieur, cage d'escalier)."""
    p = os.path.join(REPO, 'calques_reduits', dossier, 'jour', '01_sol.png')
    a = np.array(Image.open(p).convert('RGBA'))
    plein = a[:, :, 3] > 8
    clair = a[:, :, :3].mean(2) > 70
    return plein & clair


def zones_passages(mask):
    """Rectangles a laisser libres devant chaque ouverture."""
    H, W = mask.shape
    zones = np.zeros_like(mask)

    def runs(v):
        out, s = [], None
        for i, x in enumerate(v):
            if x and s is None:
                s = i
            elif not x and s is not None:
                out.append((s, i)); s = None
        if s is not None:
            out.append((s, len(v)))
        return out
    for a, b in runs(mask[0]):
        zones[0:DEGAGEMENT_PASSAGE, max(0, a - TILE):b + TILE] = True
    for a, b in runs(mask[-1]):
        zones[H - DEGAGEMENT_PASSAGE:, max(0, a - TILE):b + TILE] = True
    for a, b in runs(mask[:, 0]):
        zones[max(0, a - TILE):b + TILE, 0:DEGAGEMENT_PASSAGE] = True
    for a, b in runs(mask[:, -1]):
        zones[max(0, a - TILE):b + TILE, W - DEGAGEMENT_PASSAGE:] = True
    return zones


def poser(salle, plan, props, images):
    dossier = salle['dossier']
    mask = masque_sol(dossier)
    H, W = mask.shape
    dist = ndimage.distance_transform_edt(mask)
    interdit = zones_passages(mask)
    occupe = np.zeros_like(mask)

    ys, xs = np.nonzero(mask)
    haut_sol, bas_sol = int(ys.min()), int(ys.max())
    cx_sol, cy_sol = int(xs.mean()), int(ys.mean())

    n = plan['props_a_poser']
    palette = list(PALETTES[salle['id']])
    idx = int(salle['id'])
    palette += vegetation_pour(idx, max(0, n - len(palette)), props)
    palette = palette[:n]

    ordre = {'tapis': 0, 'sol': 1, 'mural': 2, 'suspendu': 3}
    palette.sort(key=lambda pid: (ordre[props[pid]['pose']],
                                  -props[pid]['taille'][0] * props[pid]['taille'][1]))

    poses = []

    def libre(x0, y0, w, h, marge=4):
        a, b = max(0, x0 - marge), max(0, y0 - marge)
        c, d = min(W, x0 + w + marge), min(H, y0 + h + marge)
        return not occupe[b:d, a:c].any()

    def marquer(x0, y0, w, h):
        occupe[max(0, y0):y0 + h, max(0, x0):x0 + w] = True

    # --- fenetres a ne pas masquer (rect du kit ramenes a l'echelle)
    fen = []
    fx = W / float(salle['dimensions'][0])
    fy = H / float(salle['dimensions'][1])
    for r in salle.get('fenetres', []) or []:
        fen.append((int(r[0] * fx), int(r[1] * fy), int(r[2] * fx), int(r[3] * fy)))

    for pid in palette:
        pr = props[pid]
        w, h = pr['taille']
        pose = pr['pose']
        place = None

        if pose == 'tapis':
            place = (cx_sol - w // 2, cy_sol - h // 2)

        elif pose == 'sol':
            # candidats : pieds dans la bande le long des murs, sinon partout
            cand = (mask & (dist >= 5) & (dist <= BANDE) & ~interdit)
            if not cand.any():
                cand = mask & (dist >= 5) & ~interdit
            cys, cxs = np.nonzero(cand)
            pas = max(1, len(cxs) // 900)
            cys, cxs = cys[::pas], cxs[::pas]
            deja = np.array([[p['pieds'][0], p['pieds'][1]] for p in poses
                             if p['pose'] in ('sol', 'tapis')], dtype=float)
            meilleur, score_max = None, -1e9
            for px, py in zip(cxs, cys):
                x0, y0 = int(px - w / 2), int(py - h)
                if x0 < 0 or y0 < -h // 2 or x0 + w > W or py > bas_sol:
                    continue
                if not mask[max(0, py - 6):py + 1, max(0, x0 + 2):x0 + w - 2].all():
                    continue
                if not libre(x0, max(0, y0), w, h):
                    continue
                if deja.size:
                    d2 = np.hypot(deja[:, 0] - px, deja[:, 1] - py).min()
                else:
                    d2 = 400.0
                score = min(d2, 220) - 1.4 * dist[py, px]
                if score > score_max:
                    score_max, meilleur = score, (x0, y0, px, py)
            if meilleur:
                x0, y0, px, py = meilleur
                place = (x0, y0)

        elif pose == 'mural':
            y0 = max(0, haut_sol - h - 6)
            deja = [p for p in poses if p['pose'] == 'mural']
            meilleur, score_max = None, -1e9
            for x0 in range(TILE, W - w - TILE, 8):
                if not mask[haut_sol:min(H, haut_sol + 8), x0:x0 + w].any():
                    continue
                if any(not (x0 + w < a or x0 > c) for (a, b, c, d) in fen):
                    continue
                if not libre(x0, y0, w, h, 6):
                    continue
                d2 = min([abs(x0 - p['x']) for p in deja], default=400)
                score = min(d2, 260) - abs(x0 + w / 2 - W / 2) * 0.05
                if score > score_max:
                    score_max, meilleur = score, x0
            if meilleur is not None:
                place = (meilleur, y0)

        elif pose == 'suspendu':
            y0 = max(0, haut_sol - h - 3 * TILE)
            x0 = int(W / 2 - w / 2)
            for k in range(0, W // 2, 12):
                for cx in (x0 - k, x0 + k):
                    if 0 <= cx <= W - w and libre(cx, y0, w, h, 6):
                        place = (cx, y0)
                        break
                if place:
                    break

        if not place:
            continue
        x0, y0 = int(place[0]), int(place[1])
        marquer(x0, max(0, y0), w, h)
        poses.append({'sprite': pid, 'pose': pose, 'calque': CALQUE[pose],
                      'x': x0, 'y': y0, 'w': w, 'h': h,
                      'pieds': [x0 + w // 2, y0 + h],
                      'case': [round(x0 / TILE, 2), round(y0 / TILE, 2)]})

    # --- couverture obtenue
    couv = np.zeros_like(mask)
    for p in poses:
        couv[max(0, p['y']):p['y'] + p['h'], max(0, p['x']):p['x'] + p['w']] = True
    taux = 100.0 * (couv & mask).sum() / max(1, mask.sum())

    plan_out = {
        'id': salle['id'], 'nom': salle['nom'], 'toile_px': [W, H],
        'props_demandes': n, 'props_poses': len(poses),
        'couverture_du_sol_pct': round(taux, 1),
        'cible_couverture_pct': [30, 45],
        'placements': poses,
    }

    # --- ecriture des calques 06 / 07 et recomposition
    for palette_nuit in ('jour', 'nuit'):
        for calque in ('06_decorations', '07_objets'):
            im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for p in poses:
                if p['calque'] != calque:
                    continue
                spr = images[palette_nuit][p['sprite']]
                im.alpha_composite(spr, (p['x'], max(0, p['y'])))
            im.save(os.path.join(REPO, 'calques_reduits', dossier, palette_nuit,
                                 calque + '.png'), optimize=True)
        comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for c in ['01_sol', '02_structure', '03_cadres_fenetres', '04_tableaux',
                  '05_porte_maitre', '06_decorations', '07_objets',
                  '08_ombres_acces', '09_eclairage_fixe', '10_bordure_avant']:
            p = os.path.join(REPO, 'calques_reduits', dossier, palette_nuit, c + '.png')
            if os.path.exists(p):
                comp.alpha_composite(Image.open(p).convert('RGBA'))
        comp.save(os.path.join(REPO, 'salles_reduites',
                               '%s_%s.png' % (dossier, palette_nuit)), optimize=True)

    apercu = Image.new('RGBA', (W, H), ap.VOID)
    apercu.alpha_composite(Image.open(os.path.join(
        REPO, 'salles_reduites', '%s_jour.png' % dossier)).convert('RGBA'))
    for i, (px, py) in enumerate(ap.spread_points(mask & ~couv, 4)):
        ap.put_sprite(apercu, ap.SPRITES[i % len(ap.SPRITES)], px, py)
    ap.annotate(apercu, '%s %s\n%d props, %.0f %% du sol couvert (cible 30-45 %%)' % (
        salle['id'], salle['nom'], len(poses), taux))
    return plan_out, apercu


def main():
    os.makedirs(OUT, exist_ok=True)
    ap.SPRITES = ap.load_sprites()
    props = charger_props()
    images = {p: {pid: Image.open(os.path.join(REPO, 'sprites_reduits', p, pid + '.png'))
                  .convert('RGBA') for pid in props} for p in ('jour', 'nuit')}
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))

    planche, tout = [], []
    for s in kit['salles']:
        plan = json.load(io.open(os.path.join(HERE, 'guides', '%s_plan.json' % s['id']),
                                 encoding='utf-8'))
        res, apercu = poser(s, plan, props, images)
        with io.open(os.path.join(OUT, '%s_placement.json' % s['id']), 'w',
                     encoding='utf-8') as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        apercu.convert('RGB').save(os.path.join(OUT, '%s_apercu.png' % s['id']))
        planche.append(apercu)
        tout.append(res)
        print('%s %-26s %2d/%2d props  couverture %4.1f %%' % (
            res['id'], res['nom'][:26], res['props_poses'], res['props_demandes'],
            res['couverture_du_sol_pct']))
    ap.contact_sheet(planche, 3, os.path.join(OUT, 'planche_placements.png'))
    with io.open(os.path.join(OUT, 'placements.json'), 'w', encoding='utf-8') as f:
        json.dump(tout, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
