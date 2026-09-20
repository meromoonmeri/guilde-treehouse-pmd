"""Plage Halcyon V1 — arène de plage (arenapmdskybeach.png) convertie aux critères
Halcyon/Palika par la méthode canonique : terrain généré plein cadre (bande magenta →
alpha par inondation), calques fixes empilés (fond / terrain / eau lumineuse), et un
calque d'eau animée indépendant : 5 poses générées + 5 fondus 50 % = 10 frames
768×256, posées sur la grille 8 px, boucle fermée par construction (la frame 10 est un
demi-pas de la frame 1). Les traînées lumineuses sont restreintes au masque d'eau
profonde du terrain : aucun scintillement sur le sable ni la roche."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/plage_halcyon_v1'
BRUT_T = O / 'bruts/terrain_plein_cadre.png'
BRUT_E = O / 'bruts/eau_ondulation_15cases.png'
L, H = 928, 1152
CASE_L, CASE_H = 928, 256       # pleine largeur : les bassins touchent les bords
POS_X = 0
T, MS = 10, 140                  # 10 × 140 ms = 1,4 s ; frame 10 = demi-pas → boucle
FOND = (39, 39, 55)              # même teinte que la crique sombre du terrain
POS_Y = None                     # fixé par construire() : meilleur multiple de 8

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def cases_planche_eau():
    """Découpe RÉELLE de la planche : gouttières magenta détectées, tailles jamais supposées."""
    w = np.array(Image.open(BRUT_E).convert('RGB')).astype(float)
    d = np.linalg.norm(w - np.array([255., 0., 255.]), axis=2)
    cand = d < 90
    def groupes(frac, min_frac=0.8):
        idx = np.where(frac > min_frac)[0]; g = []
        for i in idx:
            if g and i - g[-1][-1] == 1: g[-1].append(i)
            else: g.append([i])
        return [(x[0], x[-1] + 1) for x in g]
    gc = groupes(cand.mean(axis=0)); gr = groupes(cand.mean(axis=1))
    assert len(gc) >= 6 and len(gr) >= 4, f'grille inattendue: {len(gc)}x{len(gr)} goutieres'
    colsons, lig = [], []
    for i in range(len(gc) - 1):
        a, b = gc[i][1], gc[i + 1][0]
        if b - a > 60: colsons.append((a, b))
    for i in range(len(gr) - 1):
        a, b = gr[i][1], gr[i + 1][0]
        if b - a > 60: lig.append((a, b))
    assert len(colsons) == 5 and len(lig) == 3, f'grille {len(colsons)}x{len(lig)}'
    return [w[r0:r1, c0:c1].astype('uint8') for r0, r1 in lig for c0, c1 in colsons]

def pose_de_case(cell, eau_bande):
    """Case → pose 768×256 : hauteur ramenée à 256, tuilage [case|miroir|case] (raccords
    continus par symétrie), extraction des seules traînées lumineuses, croisées avec le
    masque d'eau du terrain. Aucun remplissage de trous (leçon V9)."""
    im = Image.fromarray(cell).resize((cell.shape[1], CASE_H), Image.Resampling.NEAREST)
    a = np.array(im)
    strip = np.concatenate([a, a[::-1], a, a[::-1]], axis=1)[:CASE_H, :CASE_L, :3].astype(float)
    d = np.linalg.norm(strip - np.array([255., 0., 255.]), axis=2)
    trail = (strip[:, :, 1] > 165) & (strip[:, :, 2] > 195) & (d > 60)
    out = np.zeros((CASE_H, CASE_L, 4), 'uint8')
    out[:, :, :3] = strip.astype('uint8')
    out[:, :, 3] = np.where(trail & eau_bande, 255, 0)
    return out

def fondu(A, B):
    """Fondu 50 % (précédent V11) : demi-alpha uniforme — les traînées d'une pose
    s'éteignent en douceur là où l'autre pose n'en a pas. A, B : images RGBA."""
    return Image.blend(B, A, 0.5)

def construire():
    for d in ['couches/eau', 'review', 'scene']:
        (O / d).mkdir(parents=True, exist_ok=True)
    # --- terrain : nearest 928×1152 AVANT inondation (méthode canonique V15/V16) ---
    raw = Image.open(BRUT_T).convert('RGB')
    tn = np.array(raw.resize((L, H), Image.Resampling.NEAREST)).astype(float)
    d = np.linalg.norm(tn - np.array([255., 0., 255.]), axis=2)
    cand = d < 130
    bord = np.zeros_like(cand); bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
    masque_fond = ndimage.binary_propagation(bord & cand, mask=cand)
    assert (cand & ~masque_fond).sum() == 0, 'magenta cuit interieur au terrain'
    terrain = np.dstack([tn.astype('uint8'), np.where(masque_fond, 0, 255).astype('uint8')])
    Image.fromarray(terrain, 'RGBA').save(O / 'couches/terrain_fixe.png')
    # --- masque d'eau profonde (composants >= 200 px) ---
    r_, g_, b_ = tn[:, :, 0], tn[:, :, 1], tn[:, :, 2]
    eau = (r_ < 80) & (g_ > 40) & (g_ < 175) & (b_ > 105) & (b_ < 220) & (b_ > r_ + 70)
    lab, n = ndimage.label(ndimage.binary_opening(eau, iterations=1))
    tailles = ndimage.sum(eau, lab, range(1, n + 1))
    masque_eau = np.isin(lab, [i + 1 for i, s in enumerate(tailles) if s >= 200])
    # --- bande 256 : meilleur y multiple de 8 pour couvrir les grands bassins ---
    couvs = [(masque_eau[y:y + CASE_H].sum(), y) for y in range(352, 512, 8)]
    _, y0 = max(couvs)
    assert y0 % 8 == 0
    global POS_Y
    POS_Y = y0
    eau_bande = masque_eau[POS_Y:POS_Y + CASE_H, POS_X:POS_X + CASE_L]
    couverture = eau_bande.sum() / max(1, masque_eau.sum())
    # --- fond (teinte crique) ---
    fond = np.zeros((H, L, 4), 'uint8'); fond[:, :, :3] = FOND; fond[:, :, 3] = 255
    Image.fromarray(fond, 'RGBA').save(O / 'couches/fond_fixe.png')
    # --- 5 poses + 5 fondus = 10 frames ---
    cases = cases_planche_eau()
    poses = [pose_de_case(c, eau_bande) for c in cases]
    mp = [p[:, :, 3] > 128 for p in poses]
    # 5 poses réparties (k-centre glouton depuis la pose médiane) puis chemin circulaire min-max
    def sd(a, b): return float(np.mean(a ^ b))
    centre = int(np.argmax([m.sum() for m in mp]))
    choisies = [centre]
    while len(choisies) < 5:
        nxt = max([i for i in range(len(poses)) if i not in choisies],
                  key=lambda i: min(sd(mp[i], mp[j]) for j in choisies))
        choisies.append(nxt)
    meilleur = None
    for depart in choisies:
        chemin = [depart]; restants = [i for i in choisies if i != depart]
        while restants:
            last = chemin[-1]
            nxt = min(restants, key=lambda i: max(sd(mp[last], mp[i]),
                                                  sd(mp[i], mp[chemin[0]])))
            chemin.append(nxt); restants.remove(nxt)
        sauts = [sd(mp[chemin[i]], mp[chemin[(i + 1) % 5]]) for i in range(5)]
        if meilleur is None or max(sauts) < meilleur[0]: meilleur = (max(sauts), chemin, sauts)
    _, chemin, sauts = meilleur
    P = [poses[i] for i in chemin]
    frames = []
    for i in range(5):
        frames.append(Image.fromarray(P[i], 'RGBA'))
        frames.append(fondu(Image.fromarray(P[(i + 1) % 5], 'RGBA'), Image.fromarray(P[i], 'RGBA')))
    # frames = [P0, f(P1,P0), P1, f(P2,P1), ..., P4, f(P0,P4)] → la 10e est un demi-pas de la 1re
    for f, im in enumerate(frames):
        im.save(O / 'couches/eau' / f'EauLumiereV1_{f:02d}.png')
    frames[0].save(O / 'eau_scintillement_10frames.webp', save_all=True,
                   append_images=frames[1:], duration=MS, loop=0, lossless=True, method=4)
    # --- scènes et revues ---
    def scene(f):
        s = Image.fromarray(fond, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(terrain, 'RGBA'))
        s.alpha_composite(frames[f % T], (POS_X, POS_Y))
        return s
    for f in (0, 3, 6, 9):
        scene(f).save(O / 'scene' / f'scene_{f:02d}.png')
    palette_image = Image.new('RGB', (464, 576 * 4))
    for i, f in enumerate((0, 3, 6, 9)):
        palette_image.paste(scene(f).convert('RGB').resize((464, 576)), (0, 576 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene(f).convert('RGB').resize((464, 576)).quantize(palette=pal, dither=Image.Dither.NONE) for f in range(T)]
    gifs[0].save(O / 'review/scene_scintillement.gif', save_all=True, append_images=gifs[1:],
                 duration=MS, loop=0, disposal=1, optimize=False)
    fondn = Image.new('RGBA', (384, 128), (30, 62, 141, 255))
    gs = []
    for f in range(T):
        g2 = fondn.copy(); g2.alpha_composite(frames[f].resize((384, 128), Image.Resampling.NEAREST)); gs.append(g2.convert('RGB'))
    gs[0].save(O / 'review/eau_seule.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    # --- viewer ---
    donnees = {'fond': uri(Image.fromarray(fond, 'RGBA')), 'terrain': uri(Image.fromarray(terrain, 'RGBA')),
               'couches': [uri(im) for im in frames], 'pos': [POS_X, POS_Y], 'ms': MS}
    (R / 'apercu_plage_halcyon_v1.html').write_text(
        (R / 'source/plage_halcyon_v1/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    # --- manifeste ---
    (O / 'manifest.json').write_text(json.dumps({
        'halcyon': {'grille_px': 8, 'eau_position': [POS_X, POS_Y], 'position_multiple_de_8': POS_X % 8 == 0 and POS_Y % 8 == 0,
                    'frames_nommage_uniforme': 'EauLumiereV1_00..09.png', 'frames_taille_uniforme': [CASE_L, CASE_H],
                    'duree_ms_uniforme': MS, 'boucle': 'frame 10 = demi-pas de frame 1 (fondu 50 %)',
                    'ordre_des_calques': ['fond_fixe', 'terrain_fixe', 'eau (10 frames)'],
                    'pas_de_wrap': True},
        'methode': 'canonique : terrain genere plein cadre (bande magenta -> alpha par inondation) ; '
                   'planche d eau generee -> 15 cases detectees -> 5 poses + 5 fondus 50 % = 10 frames ; '
                   'trainees lumineuses restreintes au masque d eau profonde (composants >= 200 px)',
        'bande_eau': {'y': POS_Y, 'couverture_eau_totale': round(float(couverture), 3),
                      'hors_bande': 'crique haute (y~168-300) et petites poches basses : statiques en V1'},
        'bruts_sha256': {'terrain': hashlib.sha256(BRUT_T.read_bytes()).hexdigest(),
                         'eau': hashlib.sha256(BRUT_E.read_bytes()).hexdigest()},
        'chemin_poses': chemin, 'sauts_entre_poses': [round(s, 3) for s in sauts],
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cycle_officiel': 'INCONNU : poses et cadence choisis'}, indent=2, ensure_ascii=False) + '\n')
    print('POS_Y =', POS_Y, '| couverture eau =', round(float(couverture), 3),
          '| chemin poses =', chemin, '| sauts =', [round(s, 3) for s in sauts])

if __name__ == '__main__':
    construire()
