# -*- coding: utf-8 -*-
"""
Retouches du hall des missions (salle 02).

1. Passage ouest refait dans le langage des autres salles : ouverture ramenee a
   67 px (le gabarit des chambres), contour de piece restitue de part et d'autre
   et aretes marquees comme sur les passages lateraux.
2. Trou au pied du tronc : le plancher est perce sous l'arbre, borde de bois, et
   l'echelle descend dedans vers l'etage inferieur (principe du 2e etage de
   Halcyon).
3. Porte nord : arche de guilde en bois. La version posee est l'arche ouverte
   (ouverture sombre) ; la variante a battants sculptes est ecrite a cote sous
   05_porte_maitre_battants.png.

On edite les calques du jour, la nuit est recalculee avec la formule du pipeline
(rebuild_kit.py : rgb * [.36,.34,.43] + [9,10,19], le calque d'ombres restant
identique), puis composites, Aseprite et cartes Tiled de la salle 02 sont
regeneres.
"""
import io, json, os, struct, zlib
import numpy as np
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALLE = '02_hall_missions'
RID = '02'
LABELS = [
    ('00_exterieur', 'Paysage extérieur interchangeable'),
    ('01_sol', 'Sol et continuité des passages'),
    ('02_structure', 'Structure, murs et ouvertures'),
    ('03_cadres_fenetres', 'Cadres de fenêtres — sans paysage'),
    ('04_tableaux', 'Contenu des tableaux encastrés'),
    ('05_porte_maitre', 'Porte nord du bureau — hall uniquement'),
    ('06_decorations', 'Décorations — vide'),
    ('07_objets', 'Objets — vide'),
    ('08_ombres_acces', 'Ombres de contact des accès'),
    ('09_eclairage_fixe', 'Éclairage complémentaire — vide'),
    ('10_bordure_avant', 'Bordure avant interrompue aux passages'),
]

ZONE_Y = (238, 378)          # bande retravaillee a l'ouest
OUVERTURE_H = 67             # hauteur d'ouverture des autres salles
CENTRE_OUVERTURE = 303
TROU = {'rx': 96, 'ry': 46, 'cy': 261}
PORTE = {'x0': 1011, 'x1': 1103, 'y0': 78, 'y1': 217}


# ------------------------------------------------------------------ outils

ORIGINAL = os.path.join(REPO, 'source', 'hall_02_avant_retouche')


def charger(palette='jour'):
    """Les calques d'origine sont conserves a part : la retouche part toujours
    d'eux, elle est donc rejouable a l'identique."""
    src = os.path.join(REPO, 'calques', SALLE, palette)
    sauv = os.path.join(ORIGINAL, palette)
    if not os.path.isdir(sauv):
        os.makedirs(sauv)
        for n, _ in LABELS:
            Image.open(os.path.join(src, n + '.png')).save(os.path.join(sauv, n + '.png'))
    return {n: np.array(Image.open(os.path.join(sauv, n + '.png')).convert('RGBA'))
            for n, _ in LABELS}


def nuit(a):
    b = a.copy()
    b[:, :, :3] = np.rint(a[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype('uint8')
    b[a[:, :, 3] == 0] = 0
    return b


def png(im, path):
    a = np.array(im.convert('RGBA'))
    colors, idx = np.unique(a.reshape(-1, 4), axis=0, return_inverse=True)
    if len(colors) <= 256:
        q = Image.fromarray(idx.reshape(a.shape[:2]).astype('uint8'), 'P')
        pal = np.zeros((256, 3), np.uint8)
        pal[:len(colors)] = colors[:, :3]
        q.putpalette(pal.ravel())
        q.info['transparency'] = bytes(colors[:, 3])
        q.save(path, optimize=True)
    else:
        im.save(path, optimize=True)


def astr(s):
    b = s.encode()
    return struct.pack('<H', len(b)) + b


def chunk(k, d):
    return struct.pack('<IH', len(d) + 6, k) + d


def ase(path, layers, size):
    w, h = size
    chunks = []
    for n, im in layers:
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr(n)))
    for i, (n, im) in enumerate(layers):
        box = im.getbbox()
        if box:
            x, y, _, _ = box
            q = im.crop(box)
        else:
            x = y = 0
            q = Image.new('RGBA', (1, 1))
        chunks.append(chunk(0x2005, struct.pack('<HhhBHh', i, x, y, 255, 2, 0) + b'\0' * 5 +
                            struct.pack('<HH', q.width, q.height) + zlib.compress(q.tobytes(), 9)))
    data = b''.join(chunks)
    frame = struct.pack('<IHHH2sI', len(data) + 16, 0xF1FA, len(chunks), 100, b'\0\0', len(chunks)) + data
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, w, h, 32, 1, 100)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, 8, 8)
    open(path, 'wb').write(header + frame)


# ------------------------------------------------- 1. passage ouest standard

def couleurs_arete(L, avant):
    """3 couleurs de dessous de mur et 3 couleurs de rebord avant, prises dans
    le decor existant du hall."""
    sol = avant['01_sol'][:, :, 3] > 8
    st = avant['02_structure']
    bo = avant['10_bordure_avant']
    x = 300
    ys = np.nonzero(sol[:, x])[0]
    yf = int(ys.min())
    planche = avant['01_sol'][yf + 40, x].astype(float)
    # dessous de mur : le plancher assombri, du plus sombre au plus clair
    haut = [np.rint(np.append(planche[:3] * f, 255)).astype('uint8')
            for f in (0.42, 0.58, 0.78)]
    ys = np.nonzero(bo[:, x, 3] > 8)[0]
    yb = int(ys.min())
    bas = [bo[yb + k, x].copy() for k in (0, 1, 2)]
    return haut, bas


def passage_ouest(L):
    H, W = L['01_sol'].shape[:2]
    y0z, y1z = ZONE_Y
    avant = {n: L[n].copy() for n, _ in LABELS}
    haut, bas = couleurs_arete(L, avant)

    plancher = avant['01_sol'][:, :, 3] > 8

    y0 = CENTRE_OUVERTURE - OUVERTURE_H // 2
    y1 = y0 + OUVERTURE_H - 1

    # bord gauche theorique du plancher = miroir du bord droit, intact
    bord = {}
    for y in range(y0z, y1z):
        xs = np.nonzero(plancher[y])[0]
        bord[y] = int(W - 1 - xs.max()) if len(xs) else 0

    st, bo, sol = L['02_structure'], L['10_bordure_avant'], L['01_sol']

    for y in range(y0z, y1z):
        limite = bord[y]
        if y0 <= y <= y1:
            # ouverture : la langue de plancher traverse, le contour est efface
            sol[y, 0:limite + 14] = avant['01_sol'][y, 0:limite + 14]
            st[y, 0:limite + 14, 3] = 0
            bo[y, 0:limite + 14, 3] = 0
        else:
            # ailleurs : hors du plancher, on restitue le contour en miroir
            for n in ('01_sol', '02_structure', '10_bordure_avant'):
                L[n][y, 0:limite] = avant[n][y, W - limite:W][::-1]

    # aretes du couloir : dessous de mur au nord, rebord avant au sud
    for k in (1, 2, 3):
        yh, yb = y0 - k, y1 + k
        lim_h = bord.get(yh, 0) + 8
        lim_b = bord.get(yb, 0) + 8
        st[yh, 0:lim_h] = haut[3 - k]
        bo[yh, 0:lim_h, 3] = 0
        sol[yh, 0:lim_h, 3] = 0
        bo[yb, 0:lim_b] = bas[k - 1]
        st[yb, 0:lim_b, 3] = 0
        sol[yb, 0:lim_b, 3] = 0

    # joues sombres a la coupe du contour
    for y in (y0 - 1, y0 - 2, y1 + 1, y1 + 2):
        x = bord.get(y, 0) + 8
        for n in ('02_structure', '10_bordure_avant'):
            px = L[n][y, x:x + 4]
            m = px[:, 3] > 8
            px[m, :3] = np.rint(px[m, :3] * 0.62).astype('uint8')

    # ombre de contact recadree sur la nouvelle ouverture
    om = L['08_ombres_acces']
    om[y0z:max(y0z, y0 - 8), 0:210, 3] = 0
    om[min(y1z, y1 + 9):y1z, 0:210, 3] = 0
    return y0, y1


# ---------------------------------------------------- 2. trou sous le tronc

def bornes_tronc(L):
    st = L['02_structure']
    bande = st[150:205, :, 3] > 8
    xs = np.nonzero(bande.any(0))[0]
    xs = xs[(xs > 520) & (xs < 780)]
    return int(xs.min()), int(xs.max())


def echelle_bornes(L):
    st = L['02_structure']
    tx0, tx1 = bornes_tronc(L)
    bande = st[150:200, tx0:tx1 + 1]
    lum = bande[:, :, :3].mean(2) * (bande[:, :, 3] > 8)
    profil = lum.mean(0)
    seuil = profil.mean() + profil.std() * 0.5
    xs = np.nonzero(profil > seuil)[0]
    if len(xs) < 4:
        c = (tx1 + tx0) // 2
        return c - 20, c + 20
    return tx0 + int(xs.min()), tx0 + int(xs.max())


def trou_sous_tronc(L):
    """Perce le plancher au pied du tronc et fait descendre l'echelle dedans."""
    sol, st = L['01_sol'], L['02_structure']
    H, W = sol.shape[:2]
    tx0, tx1 = bornes_tronc(L)
    cx = (tx0 + tx1) // 2
    cy, rx, ry = TROU['cy'], TROU['rx'], TROU['ry']

    bois = st[172, tx0 + 8][:3].astype(float)

    yy, xx = np.mgrid[0:H, 0:W]
    e = np.sqrt(((xx - cx) / float(rx)) ** 2 + ((yy - cy) / float(ry)) ** 2)
    interieur = e <= 1.0
    lisiere = (e > 1.0) & (e <= 1.10)      # chant du plancher, garde son grain
    lippe = (e > 1.10) & (e <= 1.17)

    # --- le puits : degrade sombre, plus profond en haut
    t = np.clip((yy - (cy - ry)) / float(2 * ry), 0, 1)[:, :, None]
    fond = np.array([13, 9, 7]) * (1 - t) + np.array([48, 32, 21]) * t
    sol[interieur, :3] = fond[interieur].astype('uint8')
    sol[interieur, 3] = 255

    # paroi arriere : bois du tronc, eclaire par l'ouverture
    dv = np.clip(((cy + ry * 0.15) - yy) / (ry * 1.15), 0, 1)[:, :, None]
    paroi = (bois * 0.55 + np.array([16, 10, 7]))
    melange = fond * (1 - dv) + paroi * dv
    haut = interieur & (yy < cy + ry * 0.15)
    sol[haut, :3] = np.clip(melange, 0, 255)[haut].astype('uint8')

    # ombre portee de la levre nord
    ombre = np.clip(((cy - ry * 0.25) - yy) / (ry * 0.8), 0, 1)[:, :, None]
    f = (1 - 0.45 * ombre)
    sol[interieur, :3] = np.rint(sol[interieur, :3] * f[interieur]).astype('uint8')

    # --- l'echelle plonge dans le trou
    lx0, lx1 = echelle_bornes(L)
    # on ne garde que le coeur de l'echelle : les bords du tronc feraient des trainees
    milieu = (lx0 + lx1) // 2
    demi = max(18, int((lx1 - lx0) * 0.34))
    lx0, lx1 = milieu - demi, milieu + demi
    strip = st[150:200, lx0:lx1 + 1].copy().astype(float)
    if strip.size:
        lum = strip[:, :, :3].mean(2)
        garde = (lum >= np.percentile(lum[strip[:, :, 3] > 8], 60)) & (strip[:, :, 3] > 8)
        motif = strip.copy()
        motif[~garde] = 0
        lignes = np.nonzero(garde.any(1))[0]
        if len(lignes) > 12:
            h0 = int(lignes[0])
            motif = motif[h0:h0 + 24]
        hauteur = int(ry * 1.85)
        y_depart = cy - ry + 3
        tuile = np.tile(motif, (hauteur // max(1, motif.shape[0]) + 2, 1, 1))[:hauteur]
        prof = np.linspace(0.95, 0.42, hauteur)[:, None, None]
        rgba = np.concatenate([prof, prof, prof, np.ones_like(prof)], axis=2)
        tuile = (tuile * rgba).astype('uint8')
        zone = sol[y_depart:y_depart + hauteur, lx0:lx1 + 1]
        dedans = interieur[y_depart:y_depart + hauteur, lx0:lx1 + 1] & (tuile[:, :, 3] > 8)
        zone[dedans, :3] = tuile[dedans, :3]
        zone[dedans, 3] = 255

    # --- chant du plancher : on garde le grain des planches, on le nuance
    nord = lisiere & (yy < cy)
    sud = lisiere & (yy >= cy)
    sol[nord, :3] = np.rint(sol[nord, :3] * 0.45).astype('uint8')
    sol[sud, :3] = np.clip(np.rint(sol[sud, :3] * 0.92 + 12), 0, 255).astype('uint8')
    lp_sud = lippe & (yy > cy + ry * 0.2)
    sol[lp_sud, :3] = np.clip(np.rint(sol[lp_sud, :3] * 1.06 + 8), 0, 255).astype('uint8')
    lp_nord = lippe & (yy < cy - ry * 0.2)
    sol[lp_nord, :3] = np.rint(sol[lp_nord, :3] * 0.82).astype('uint8')
    # trait sombre a l'aplomb de l'ouverture : donne la profondeur
    bord_noir = (e > 0.965) & (e <= 1.0)
    sol[bord_noir, :3] = np.rint(sol[bord_noir, :3] * 0.30).astype('uint8')

    # --- ombre de contact autour du trou
    om = L['08_ombres_acces']
    halo = (e > 1.17) & (e <= 1.55) & (yy > cy - ry * 0.3)
    a = np.rint(np.clip((1.55 - e) / 0.38, 0, 1) * 40)[halo].astype('uint8')
    om[halo, 3] = np.maximum(om[halo, 3], a)
    om[halo, :3] = 0
    return cx, cy


# --------------------------------------------------------- 3. porte / arche

def mur_derriere_porte(L):
    """Rebouche le trou laisse par l'ancienne porte : interpolation horizontale
    entre le mur de gauche et celui de droite, ligne par ligne. Pas de motif
    recopie, donc pas de poutre dupliquee ; l'arche recouvre la quasi-totalite."""
    st = L['02_structure']
    x0, x1 = PORTE['x0'], PORTE['x1']
    y0, y1 = 46, 236
    largeur = x1 - x0
    t = (np.arange(largeur) / float(largeur - 1))[None, :, None]
    g = st[y0:y1, x0 - 3:x0 - 2].astype(float)
    d = st[y0:y1, x1 + 2:x1 + 3].astype(float)
    melange = g * (1 - t) + d * t
    plein = (g[:, :, 3] > 8) & (d[:, :, 3] > 8)
    zone = st[y0:y1, x0:x1]
    zone[plein[:, 0]] = np.rint(melange[plein[:, 0]]).astype('uint8')


def arche(taille, ouverte=True, embleme=None):
    """Arche de guilde : le battant cintre du banc de props sert d'encadrement.

    Version ouverte : l'interieur est evide en arc plein cintre et assombri.
    Version fermee : les battants sculptes restent en place.
    """
    w, h = taille
    src = Image.open(os.path.join(REPO, 'sprites', 'individuels',
                                  'porte_double_arrondie.png')).convert('RGBA')
    a = np.array(src.resize((w, h), Image.LANCZOS))
    a[a[:, :, 3] <= 96] = 0

    if ouverte:
        ep = max(10, w // 8)                     # epaisseur de l'encadrement
        yy, xx = np.mgrid[0:h, 0:w]
        r = (w - 2 * ep) / 2.0
        cxa, cya = w / 2.0, ep + r
        dedans = (((yy >= cya) & (xx >= ep) & (xx < w - ep) & (yy < h - max(5, ep // 2))) |
                  (((xx - cxa) ** 2 + (yy - cya) ** 2 <= r * r) & (yy < cya)))
        t = np.clip((yy - ep) / float(max(1, h - ep)), 0, 1)[:, :, None]
        noir = np.array([9, 6, 6]) * (1 - t) + np.array([38, 25, 17]) * t
        a[dedans, :3] = noir[dedans].astype('uint8')
        a[dedans, 3] = 255
        from scipy import ndimage
        liseré = ndimage.binary_dilation(dedans, np.ones((3, 3), bool)) & ~dedans & (a[:, :, 3] > 0)
        a[liseré, :3] = np.rint(a[liseré, :3] * 0.5).astype('uint8')
        seuil = dedans & (yy >= h - max(5, ep // 2) - 3)
        a[seuil, :3] = np.rint(np.array([150, 104, 50])).astype('uint8')
        a[seuil, 3] = 255

    if embleme is not None:
        lw = max(22, int(w * 0.30))
        em = embleme.resize((lw, max(10, int(lw * embleme.height / embleme.width))),
                            Image.LANCZOS)
        ea = np.array(em)
        ox = (w - em.width) // 2
        oy = max(0, int(h * 0.085))
        zone = a[oy:oy + em.height, ox:ox + em.width]
        m = ea[:, :, 3] > 110
        if zone.shape[:2] == m.shape:
            zone[m] = ea[m]
    return a


def porte(L):
    st = L['02_structure']
    x0, x1, y0, y1 = PORTE['x0'], PORTE['x1'], PORTE['y0'], PORTE['y1']
    mur_derriere_porte(L)
    embleme = Image.open(os.path.join(REPO, 'sprites', 'individuels',
                                      'embleme_feuille_bois.png')).convert('RGBA')
    for ouverte, nom in ((True, '05_porte_maitre'), (False, '05_porte_maitre_battants')):
        couche = np.zeros_like(st)
        couche[y0:y1, x0:x1] = arche((x1 - x0, y1 - y0), ouverte=ouverte, embleme=embleme)
        L[nom] = couche


# ------------------------------------------------------------------- sortie

def ecrire(L, palette):
    d = os.path.join(REPO, 'calques', SALLE, palette)
    for n, _ in LABELS:
        png(Image.fromarray(L[n], 'RGBA'), os.path.join(d, n + '.png'))
    png(Image.fromarray(L['05_porte_maitre_battants'], 'RGBA'),
        os.path.join(d, '05_porte_maitre_battants.png'))

    fd = os.path.join(REPO, 'salles', SALLE)
    H, W = L['01_sol'].shape[:2]
    comp = Image.new('RGBA', (W, H))
    base = Image.new('RGBA', (W, H))
    export = []
    for n, label in LABELS:
        q = Image.fromarray(L[n], 'RGBA')
        comp.alpha_composite(q)
        if n != '00_exterieur':
            base.alpha_composite(q)
        export.append((label, q))
    png(comp, os.path.join(fd, 'salle_%s.png' % palette))
    png(base, os.path.join(fd, 'base_%s_transparente.png' % palette))
    chroma = Image.new('RGBA', (W, H), (255, 0, 255, 255))
    chroma.alpha_composite(base)
    png(chroma, os.path.join(fd, 'base_%s_magenta.png' % palette))
    ase(os.path.join(fd, '%s_%s.aseprite' % (RID, palette)), export, (W, H))

    cols, rows = W // 8, H // 8
    count = cols * rows
    sets, tls = [], []
    for i, (n, label) in enumerate(LABELS):
        occ = L[n][:, :, 3].reshape(rows, 8, cols, 8).max((1, 3)) > 0
        first = 1 + i * count
        data = np.arange(first, first + count, dtype=np.uint32).reshape(rows, cols)
        data[~occ] = 0
        sets.append({'firstgid': first, 'name': n, 'tilewidth': 8, 'tileheight': 8,
                     'tilecount': count, 'columns': cols,
                     'image': '../calques/%s/%s/%s.png' % (SALLE, palette, n),
                     'imagewidth': W, 'imageheight': H, 'margin': 0, 'spacing': 0})
        tls.append({'id': i + 1, 'name': label, 'type': 'tilelayer', 'width': cols,
                    'height': rows, 'x': 0, 'y': 0, 'opacity': 1, 'visible': True,
                    'data': data.ravel().tolist()})
    tm = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0',
          'orientation': 'orthogonal', 'renderorder': 'right-down', 'tilewidth': 8,
          'tileheight': 8, 'width': cols, 'height': rows, 'infinite': False,
          'nextlayerid': len(LABELS) + 1, 'nextobjectid': 1, 'layers': tls, 'tilesets': sets}
    with io.open(os.path.join(REPO, 'tiled', '%s_%s.tmj' % (RID, palette)), 'w',
                 encoding='utf-8') as f:
        json.dump(tm, f, ensure_ascii=False, separators=(',', ':'))


def main():
    J = charger('jour')
    y0, y1 = passage_ouest(J)
    cx, cy = trou_sous_tronc(J)
    porte(J)
    print('ouverture ouest y=%d..%d (%d px)' % (y0, y1, y1 - y0 + 1))
    print('trou centre sur x=%d y=%d (%d x %d px)' % (cx, cy, TROU['rx'] * 2, TROU['ry'] * 2))

    N = {}
    for n in J:
        N[n] = J[n].copy() if n == '08_ombres_acces' else nuit(J[n])
    N['00_exterieur'] = charger('nuit')['00_exterieur']

    ecrire(J, 'jour')
    ecrire(N, 'nuit')
    print('salle 02 regeneree : calques, composites, aseprite, tiled')


if __name__ == '__main__':
    main()
