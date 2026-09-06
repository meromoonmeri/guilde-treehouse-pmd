# -*- coding: utf-8 -*-
"""
Guides de recadrage salle par salle.

Pour chaque salle du kit :
  - toile cible (analyse_echelle/cibles.json, facteur global 0,65 puis ajustement
    au type de salle),
  - masque du sol ramene a cette toile,
  - zone de mobilier a remplir (bande de 1,5 case le long des murs),
  - zone de circulation a garder libre,
  - ilot central suggere quand une poche de vide depasse 6 cases,
  - passages ramenes a 2 cases,
  - sprites Pokemon poses a 1:1 et cadre du viewport 320 x 240.

Sorties :
  analyse_echelle/guides/NN_gabarit.png   (exactement a la taille cible)
  analyse_echelle/guides/NN_plan.json     (chiffres et rectangles, en cases)
  analyse_echelle/guides/planche_gabarits.png
"""
import io, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apercus as ap  # noqa: E402

REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'guides')
TILE = ap.TILE
VIEW = ap.VIEW

BANDE_MOBILIER = 1.5 * TILE      # profondeur de la bande de meubles le long des murs
PASSAGE_CIBLE = 2 * TILE         # largeur de passage visee
VIDE_MAX_CASES = 6               # diametre de poche vide tolere hors hub
VIDE_MAX_HUB = 8
PROP_PAR_CASES2 = 7              # 1 prop pour ~7 cases2 de sol

try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    FONT_S = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
except OSError:                                     # pragma: no cover
    FONT = FONT_S = ImageFont.load_default()

COUL = {
    'sol': (255, 214, 92, 255),
    'mobilier': (236, 106, 176, 255),
    'circulation': (110, 200, 255, 255),
    'ilot': (150, 245, 150, 255),
    'passage': (120, 255, 140, 255),
    'mur': (255, 150, 80, 255),
}


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


def hachures(size, mask, couleur, pas=6, sens=1):
    """Remplissage hachure d'un masque."""
    h, w = mask.shape
    ov = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for k in range(-h, w + h, pas):
        if sens > 0:
            d.line([(k, 0), (k + h, h)], fill=couleur[:3] + (110,))
        else:
            d.line([(k, h), (k + h, 0)], fill=couleur[:3] + (110,))
    arr = np.array(ov)
    arr[~mask] = 0
    return Image.fromarray(arr)


def contour(mask):
    er = ndimage.binary_erosion(mask, np.ones((3, 3), bool))
    return mask & ~er


def peindre(img, mask, couleur):
    arr = np.zeros((mask.shape[0], mask.shape[1], 4), np.uint8)
    arr[mask] = couleur
    img.alpha_composite(Image.fromarray(arr))


def texte(d, xy, s, couleur=(255, 255, 255, 255), font=None):
    x, y = xy
    font = font or FONT_S
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), s, fill=(0, 0, 0, 255), font=font)
    d.text((x, y), s, fill=couleur, font=font)


def bandeau(img, hauteur, en_bas=False):
    ov = Image.new('RGBA', (img.width, hauteur), (0, 0, 0, 165))
    img.alpha_composite(ov, (0, img.height - hauteur if en_bas else 0))


def guide(salle, cible, sprites):
    dossier = salle['dossier']
    src = Image.open(os.path.join(REPO, salle['fichiers']['jour']['png'])).convert('RGBA')
    mask0 = ap.projet_floor(dossier)
    W, H = cible['toile_ajustee_px']
    fx, fy = W / float(src.width), H / float(src.height)

    art = src.resize((W, H), Image.LANCZOS)
    mask = np.array(Image.fromarray(mask0.astype(np.uint8) * 255)
                    .resize((W, H), Image.NEAREST)) > 127

    dist = ndimage.distance_transform_edt(mask)
    mobilier = mask & (dist <= BANDE_MOBILIER)
    circulation = mask & (dist > BANDE_MOBILIER)
    vide_max = 2 * float(dist.max()) / TILE
    limite = VIDE_MAX_HUB if cible['type'] == 'hub' else VIDE_MAX_CASES

    # ilot central si la piece reste trop ouverte
    ilot = None
    if vide_max > limite:
        cy, cx = np.unravel_index(int(np.argmax(dist)), dist.shape)
        iw, ih = 3 * TILE, 2 * TILE
        ilot = (int(cx - iw / 2), int(cy - ih / 2), iw, ih)

    # passages : ce qui touche le bord de la toile
    passages = []
    for cote, ligne in (('N', mask[0]), ('S', mask[-1]),
                        ('O', mask[:, 0]), ('E', mask[:, -1])):
        for a, b in runs(ligne):
            if b - a >= 16:
                passages.append({'cote': cote, 'debut_px': int(a), 'largeur_px': int(b - a),
                                 'largeur_cases': round((b - a) / TILE, 1),
                                 'cible_px': PASSAGE_CIBLE})

    # ---------------------------------------------------------------- rendu
    img = Image.new('RGBA', (W, H), (18, 16, 22, 255))
    img.alpha_composite(Image.blend(Image.new('RGBA', (W, H), (18, 16, 22, 255)), art, 0.55))

    d = ImageDraw.Draw(img)
    for x in range(0, W, TILE):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 28))
    for y in range(0, H, TILE):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 28))
    for x in range(0, W, 4 * TILE):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 60))
    for y in range(0, H, 4 * TILE):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 60))

    img.alpha_composite(hachures((W, H), mobilier, COUL['mobilier'], 6, 1))
    peindre(img, circulation, COUL['circulation'][:3] + (34,))
    peindre(img, contour(mask), COUL['sol'])

    d = ImageDraw.Draw(img)
    if ilot:
        x, y, iw, ih = ilot
        d.rectangle([x, y, x + iw, y + ih], outline=COUL['ilot'], width=2)
        texte(d, (x + 3, y + 3), 'ilot', COUL['ilot'])

    for p in passages:
        a, larg = p['debut_px'], p['largeur_px']
        centre = a + larg / 2
        x0, x1 = int(centre - PASSAGE_CIBLE / 2), int(centre + PASSAGE_CIBLE / 2)
        if p['cote'] in 'NS':
            y = 2 if p['cote'] == 'N' else H - 4
            d.rectangle([a, y - 2, a + larg, y + 2], outline=(255, 90, 90, 200))
            d.rectangle([x0, y - 2, x1, y + 2], fill=COUL['passage'])
        else:
            x = 2 if p['cote'] == 'O' else W - 4
            d.rectangle([x - 2, a, x + 2, a + larg], outline=(255, 90, 90, 200))
            d.rectangle([x - 2, x0, x + 2, x1], fill=COUL['passage'])

    # hauteur de mur visee : 4 cases au-dessus de la ligne haute du sol
    ys, xs = np.nonzero(mask)
    haut_sol = int(ys.min())
    mur_cible = max(0, haut_sol - 4 * TILE)
    d.line([(0, haut_sol), (W, haut_sol)], fill=COUL['sol'][:3] + (120,))

    for i, (px, py) in enumerate(ap.spread_points(mask, 4)):
        ap.put_sprite(img, sprites[i % len(sprites)], px, py)

    cx, cy = W // 2, H // 2
    d.rectangle([cx - VIEW[0] // 2, cy - VIEW[1] // 2,
                 cx + VIEW[0] // 2, cy + VIEW[1] // 2],
                outline=(110, 190, 255, 230), width=2)

    sol_c2 = mask.sum() / float(TILE * TILE)
    props = int(round(sol_c2 / PROP_PAR_CASES2))
    lignes = [
        '%s %s  [%s]' % (salle['id'], salle['nom'], cible['type']),
        'toile %d x %d px = %.1f x %.1f cases  (avant %d x %d)' % (
            W, H, W / TILE, H / TILE, src.width, src.height),
        'sol %.0f cases2 (Halcyon %d-%d)  vide max %.1f cases (max %d)' % (
            sol_c2, cible['sol_reference_halcyon_cases2'][0],
            cible['sol_reference_halcyon_cases2'][1], vide_max, limite),
        'mobilier a poser : %d props, bande rose 1,5 case le long des murs' % props,
    ]
    bandeau(img, 13 * len(lignes) + 6)
    d = ImageDraw.Draw(img)
    for i, s in enumerate(lignes):
        texte(d, (5, 4 + 13 * i), s, font=FONT if i == 0 else FONT_S)

    d.line([(0, mur_cible), (W, mur_cible)], fill=COUL['mur'], width=2)
    texte(d, (W - 150, mur_cible + 3), 'haut de mur vise (4 cases)', COUL['mur'])

    legende = [(COUL['sol'], 'contour du sol praticable'),
               (COUL['mobilier'], 'bande mobilier 1,5 case (30-45 % du sol)'),
               (COUL['circulation'], 'circulation a garder libre'),
               (COUL['passage'], 'passage ramene a 2 cases'),
               (COUL['mur'], 'hauteur de mur visee'),
               ((110, 190, 255, 255), 'viewport 320 x 240')]
    bandeau(img, 12 * len(legende) + 6, en_bas=True)
    d = ImageDraw.Draw(img)
    y0 = img.height - (12 * len(legende) + 3)
    for i, (c, lab) in enumerate(legende):
        d.rectangle([5, y0 + 12 * i + 2, 13, y0 + 12 * i + 9], fill=c[:3] + (255,))
        texte(d, (18, y0 + 12 * i), lab)

    plan = {
        'id': salle['id'], 'nom': salle['nom'], 'type': cible['type'],
        'toile_px': [W, H], 'toile_cases': [round(W / TILE, 1), round(H / TILE, 1)],
        'facteur': [round(fx, 3), round(fy, 3)],
        'sol_cases2': round(sol_c2, 1),
        'sol_reference_halcyon_cases2': cible['sol_reference_halcyon_cases2'],
        'vide_max_cases': round(vide_max, 1), 'vide_max_tolere': limite,
        'bande_mobilier_cases': 1.5,
        'props_a_poser': props,
        'ilot_central_px': list(ilot) if ilot else None,
        'passages': passages,
        'hauteur_mur_visee_px': 4 * TILE,
        'ligne_haute_du_sol_px': haut_sol,
    }
    return img, plan


def main():
    os.makedirs(OUT, exist_ok=True)
    sprites = ap.load_sprites()
    ap.SPRITES = sprites
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    cibles = {c['id']: c for c in json.load(
        io.open(os.path.join(HERE, 'cibles.json'), encoding='utf-8'))['salles']}

    planche, plans = [], []
    for s in kit['salles']:
        img, plan = guide(s, cibles[s['id']], sprites)
        img.convert('RGB').save(os.path.join(OUT, '%s_gabarit.png' % s['id']))
        with io.open(os.path.join(OUT, '%s_plan.json' % s['id']), 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        plans.append(plan)
        planche.append(img)
        print('%s %-26s %4d x %-4d  sol %5.1f cases2  %2d props  passages %s' % (
            plan['id'], plan['nom'][:26], plan['toile_px'][0], plan['toile_px'][1],
            plan['sol_cases2'], plan['props_a_poser'],
            ','.join('%s:%.1fc' % (p['cote'], p['largeur_cases']) for p in plan['passages']) or '-'))

    ap.contact_sheet(planche, 3, os.path.join(OUT, 'planche_gabarits.png'))
    with io.open(os.path.join(OUT, 'plans.json'), 'w', encoding='utf-8') as f:
        json.dump(plans, f, indent=2, ensure_ascii=False)
    print('->', OUT)


if __name__ == '__main__':
    main()
