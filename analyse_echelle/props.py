# -*- coding: utf-8 -*-
"""
Banc de props ramene a l'echelle PMD.

Regle : facteur global 0,65 (celui de l'analyse d'echelle), puis plafonds par
famille pour rester dans les tailles relevees chez Halcyon
(mobilier courant 24-56 px, gros meuble <= 150 px, plante <= 2 cases,
banniere murale <= 2,7 cases).

Sorties :
  sprites_reduits/jour/<id>.png, sprites_reduits/nuit/<id>.png
  sprites_reduits/props.json
"""
import io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, 'sprites_reduits')
TILE = 24
FACTEUR = 0.65

# plafonds (largeur, hauteur) en px apres reduction, par famille
PLAFOND = {
    'vegetation': (56, 48),      # une plante ne depasse pas 2 cases
    'couchages': (64, 44),       # un nid = ~2,5 x 1,8 cases
    'mobilier': (120, 80),
    'textiles': (72, 64),
    'lampes': (40, 56),
    'ornements': (72, 56),
    'portes': (56, 56),
}
# exceptions : les grandes pieces centrales
PLAFOND_ID = {
    'table_banquet': (150, 72),
    'tapis_maitre': (150, 72),
    'table_etude': (72, 64),
    'panneau': (48, 72),
}

# ou se pose le prop : sol, mural (accroche au mur), suspendu (au plafond)
FAMILLE_POSE = {
    'vegetation': 'sol', 'couchages': 'sol', 'mobilier': 'sol',
    'lampes': 'sol', 'textiles': 'mural', 'ornements': 'mural',
    'portes': 'mural',
}
POSE_ID = {
    'lampe_suspendue': 'suspendu', 'applique_bois': 'mural',
    'tapis_maitre': 'tapis', 'fanion': 'sol',
}


def cible(sprite):
    w, h = sprite['taille_originale']
    nw, nh = w * FACTEUR, h * FACTEUR
    pw, ph = PLAFOND_ID.get(sprite['id'], PLAFOND.get(sprite['groupe'], (120, 96)))
    k = min(1.0, pw / nw, ph / nh)
    return max(8, int(round(nw * k))), max(8, int(round(nh * k)))


def main():
    d = json.load(io.open(os.path.join(REPO, 'sprites', 'decorations.json'),
                          encoding='utf-8'))
    atlas = {p: Image.open(os.path.join(REPO, 'sprites', 'decorations_%s.png' % p)).convert('RGBA')
             for p in ('jour', 'nuit')}
    for p in ('jour', 'nuit'):
        os.makedirs(os.path.join(OUT, p), exist_ok=True)

    props = []
    for s in d['sprites']:
        x, y, w, h = s['rect']
        ow, oh = s['taille_originale']
        nw, nh = cible(s)
        for p in ('jour', 'nuit'):
            im = atlas[p].crop((x, y, x + w, y + h))
            bb = im.getbbox() or (0, 0, w, h)
            im = im.crop(bb).resize((nw, nh), Image.LANCZOS)
            im.save(os.path.join(OUT, p, s['id'] + '.png'), optimize=True)
        props.append({
            'id': s['id'], 'groupe': s['groupe'],
            'pose': POSE_ID.get(s['id'], FAMILLE_POSE.get(s['groupe'], 'sol')),
            'taille_avant': [ow, oh], 'taille': [nw, nh],
            'taille_cases': [round(nw / TILE, 2), round(nh / TILE, 2)],
            'facteur': round(nw / float(ow), 3),
            'pivot': [nw / 2.0, nh],          # pieds au centre bas
        })
    with io.open(os.path.join(OUT, 'props.json'), 'w', encoding='utf-8') as f:
        json.dump({'facteur_base': FACTEUR, 'case_px': TILE,
                   'plafonds': PLAFOND, 'plafonds_id': PLAFOND_ID,
                   'props': props}, f, indent=2, ensure_ascii=False)

    gros = sorted(props, key=lambda p: -p['taille'][0] * p['taille'][1])[:14]
    print('%-28s %-11s %-11s %-9s %s' % ('id', 'avant', 'apres', 'cases', 'pose'))
    for p in gros:
        print('%-28s %-11s %-11s %-9s %s' % (
            p['id'], '%dx%d' % tuple(p['taille_avant']), '%dx%d' % tuple(p['taille']),
            '%.1fx%.1f' % tuple(p['taille_cases']), p['pose']))
    print('\n%d props ecrits dans %s' % (len(props), OUT))


if __name__ == '__main__':
    main()
