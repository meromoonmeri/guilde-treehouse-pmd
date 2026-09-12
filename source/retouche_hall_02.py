# -*- coding: utf-8 -*-
"""
Retouches du hall des missions (salle 02).

1. Passage ouest : ouverture ramenee aux 67 px des autres salles, mais avec une
   veritable epaisseur de mur — linteau sombre au nord, seuil eclaire au sud —
   et non trois ranges de couleur plate. Un cadre feuillu (branches + feuillages
   du banc de props) enrobe l'ouverture et se rattache au contour de bois qui
   borde l'extremite de la piece.
2. Trou sous le tronc : le plancher est perfore EXACTEMENT dans la largeur du
   tronc (le tronc est la seule matiere dessinee au-dessus du toit, ses bords y
   sont donc lisibles). L'ouverture demarre sous la silhouette du tronc : elle
   en est la continuation vers le bas, l'echelle y plonge. La levre est en
   ecorce cote tronc et en chant de planche cote salle.
3. Porte nord : arche de guilde en bois, ouverte ; la variante a battants est
   ecrite a cote sous 05_porte_maitre_battants.png.

On edite les calques du jour, la nuit est recalculee avec la formule du pipeline
(rebuild_kit.py : rgb * [.36,.34,.43] + [9,10,19], le calque d'ombres restant
identique), puis composites, Aseprite et cartes Tiled de la salle 02 sont
regeneres.

Le script part toujours des calques d'origine conserves dans
source/hall_02_avant_retouche : il est donc rejouable a l'identique.
"""
import io, json, os, struct, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageOps

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
LINTEAU = 11                 # epaisseur de mur visible au-dessus du passage
SEUIL = 9                    # et en dessous
PORTE = {'x0': 1011, 'x1': 1103, 'y0': 78, 'y1': 217}

TRONC_BANDE = (2, 28)        # lignes ou le tronc est seul dessine (au-dessus du toit)
TROU_RY = 52                 # profondeur du puits sous le tronc


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


BOIS_SOMBRE = np.array([72, 30, 9], float)


def ambiance(rgb, f):
    """Feuillage du banc de props ramene a l'ombre du rebord : le vert reste
    lisible mais se marie au contour de bois, les rehauts sont ecretes."""
    r = rgb * f
    r = r * 0.84 + BOIS_SOMBRE * 0.16
    return 255.0 * np.clip(r / 255.0, 0, 1) ** 1.12


def teinte(im, facteur):
    a = np.array(im).astype(float)
    a[:, :, :3] = np.clip(ambiance(a[:, :, :3], facteur), 0, 255)
    return Image.fromarray(a.astype('uint8'), 'RGBA')


def coller(canvas, im, x, y):
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + im.width), min(canvas.height, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    canvas.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


# ------------------------------------------- 1. passage ouest + cadre feuillu

# Feuillages du banc de props,poses autour de l'ouverture ouest.
# (fichier, x, y, echelle, miroir, angle, facteur de teinte)
CADRE_FEUILLES = [
    # massif haut : accroche sur le rebord, retombe vers l'ouverture
    ('vegetation_06_10.png',  -6, 178, 1.20, False,   0, 0.84),
    ('vegetation_05_11.png',  10, 196, 1.00, True,    6, 0.90),
    ('vegetation_06_03.png', -10, 222, 1.00, False,  -8, 0.80),
    ('vegetation_04_15.png',  44, 234, 1.10, True,   -6, 0.88),
    ('vegetation_03_13.png',  70, 232, 0.90, False,  10, 0.86),
    # massif bas : reprend le rebord au sud de l'ouverture
    ('vegetation_04_13.png',  14, 328, 1.15, False,   0, 0.84),
    ('vegetation_03_12.png', -10, 342, 1.25, False,  -5, 0.80),
    ('vegetation_05_02.png',  32, 340, 1.00, False,   0, 0.90),
    ('vegetation_02_08.png',  -4, 356, 1.00, True,    0, 0.78),
    # retombees sur l'angle gauche, au bord du bois
    ('vegetation_03_08.png', -16, 256, 1.00, False,  12, 0.82),
    ('vegetation_04_08.png',  -2, 300, 1.30, True,  -12, 0.78),
]


def couleurs_bois(L, avant):
    """Couleurs locales du rebord ouest : plancher, dos du mur, chant de bois."""
    sol = avant['01_sol'][:, :, 3] > 8
    ys = np.nonzero(sol[:, 300])[0]
    yf = int(ys.min())
    planche = avant['01_sol'][yf + 40, 300].astype(float)
    bo = avant['10_bordure_avant']
    ys = np.nonzero(bo[:, 300, 3] > 8)[0]
    chant = bo[int(ys.min()) + 1, 300].astype(float)
    return planche, chant


def passage_ouest(L):
    H, W = L['01_sol'].shape[:2]
    y0z, y1z = ZONE_Y
    avant = {n: L[n].copy() for n, _ in LABELS}

    plancher = avant['01_sol'][:, :, 3] > 8
    y0 = CENTRE_OUVERTURE - OUVERTURE_H // 2
    y1 = y0 + OUVERTURE_H - 1

    # bord gauche theorique du plancher = miroir du bord droit, intact
    bord = {}
    for y in range(y0z, y1z):
        xs = np.nonzero(plancher[y])[0]
        bord[y] = int(W - 1 - xs.max()) if len(xs) else 0

    st, bo, sol = L['02_structure'], L['10_bordure_avant'], L['01_sol']

    # --- 1. contour restaure : le rebord droit, mis en miroir a gauche
    for y in range(y0z, y1z):
        limite = bord[y]
        if y0 <= y <= y1:
            # ouverture : la langue de plancher traverse, le contour est efface
            sol[y, 0:limite + 14] = avant['01_sol'][y, 0:limite + 14]
            st[y, 0:limite + 14, 3] = 0
            bo[y, 0:limite + 14, 3] = 0
        else:
            for n in ('01_sol', '02_structure', '10_bordure_avant'):
                L[n][y, 0:limite] = avant[n][y, W - limite:W][::-1]

    # --- 2. epaisseur du mur : linteau au nord, seuil au sud
    # Le linteau est le dessous du mur : il s'assombrit jusqu'a l'ouverture et
    # montre le bout des planches. Le seuil est le dessus du rebord : son
    # arete accroche la lumiere.
    planche, chant = couleurs_bois(L, avant)
    ombre_froide = np.array([26, 9, 3], float)

    for k in range(1, LINTEAU + 1):
        y = y0 - k
        limite = min(bord.get(y, 0) + 8, 140)
        if limite <= 0:
            continue
        f = 0.20 + 0.62 * ((k - 1) / float(LINTEAU - 1)) ** 0.65
        bande = L['02_structure'][y, 0:limite].astype(float)
        m = bande[:, 3:4] > 8
        bande[:, :3] = bande[:, :3] * f + ombre_froide * (1 - f)
        L['02_structure'][y, 0:limite] = np.where(
            m, np.clip(bande, 0, 255), L['02_structure'][y, 0:limite]).astype('uint8')
        bo[y, 0:limite, 3] = 0

    # bout des planches : un joint vertical sombre toutes les 13 px
    for x in range(0, 140, 13):
        zone = L['02_structure'][y0 - LINTEAU:y0, x:x + 1].astype(float)
        m = zone[:, :, 3:4] > 8
        zone[:, :3] = zone[:, :3] * 0.70
        L['02_structure'][y0 - LINTEAU:y0, x:x + 1] = np.where(
            m, np.clip(zone, 0, 255), L['02_structure'][y0 - LINTEAU:y0, x:x + 1]).astype('uint8')

    for k in range(1, SEUIL + 1):
        y = y1 + k
        limite = min(bord.get(y, 0) + 8, 140)
        if limite <= 0:
            continue
        f = 1.0 + 0.26 * (1 - (k - 1) / float(SEUIL - 1)) ** 2
        bande = L['02_structure'][y, 0:limite].astype(float)
        m = bande[:, 3:4] > 8
        bande[:, :3] = bande[:, :3] * f + np.array([18, 9, 3], float) * (f - 1)
        if k <= 2:                       # arete du seuil, face au jour
            t = 0.45 if k == 1 else 0.22
            bande[:, :3] = bande[:, :3] * (1 - t) + np.array(
                [planche[0] * 1.18, planche[1] * 1.10, planche[2] * 1.05]) * t
        L['02_structure'][y, 0:limite] = np.where(
            m, np.clip(bande, 0, 255), L['02_structure'][y, 0:limite]).astype('uint8')
        bo[y, 0:limite, 3] = 0

    # --- 2 bis. on bouche les jours entre le contour rendu et le plancher :
    # le rebord doit etre continu, sans trou laissant voir le vide
    for y in range(y0z, y1z):
        if y0 <= y <= y1:
            continue
        plein = np.nonzero(L['02_structure'][y, 0:170, 3] > 8)[0]
        planche = np.nonzero(L['01_sol'][y, 0:170, 3] > 8)[0]
        if not len(plein) or not len(planche):
            continue
        fin = int(plein.max())
        debut = int(planche.min())
        if debut > fin + 1:
            coul = L['02_structure'][y, max(0, fin - 2)].astype(float)
            coul[:3] = coul[:3] * 0.86
            L['02_structure'][y, fin + 1:debut] = np.clip(coul, 0, 255).astype('uint8')

    # --- 3. cadre feuillu
    cadre_feuillu(L, avant, y0, y1)

    # --- 4. ombres de contact recadrees sur la nouvelle ouverture
    om = L['08_ombres_acces']
    om[y0z:y0, 0:210, 3] = 0
    om[y1 + 1:y1z, 0:210, 3] = 0
    # portee du linteau sur le passage
    for k in range(0, 16):
        y = y0 + k
        a = int(round(74 * (1 - k / 15.0) ** 1.6))
        if a <= 0:
            break
        ligne = om[y, 0:150]
        m = plancher[y, 0:150]
        ligne[m, 3] = np.maximum(ligne[m, 3], a)
        ligne[m, :3] = 0
    return y0, y1


def cadre_feuillu(L, avant, y0, y1):
    """Branches et feuillages enrobant l'ouverture ouest.

    Les feuillages viennent du banc de props, ils sont assombris pour se
    marier au contour de bois. Une branche est tracee le long du rebord : elle
    sert d'ossature et depasse sous les feuilles, donc le massif garde le meme
    trait sombre que l'extremite de la piece.
    """
    H, W = L['01_sol'].shape[:2]
    plancher = avant['01_sol'][:, :, 3] > 8

    # ou planter : jamais sur le sol marchable, sauf 8 px de debord ; et jamais
    # plus de 28 px hors de la silhouette de la piece, sinon le feuillage
    # flotterait dans le vide au lieu de border le rebord
    from scipy import ndimage
    interieur = ndimage.binary_erosion(plancher, np.ones((17, 17), bool))
    libre = ~interieur
    libre[:, 142:] = False                # le cadre reste a l'extremite ouest
    silo = np.zeros((H, W), bool)
    for n, _ in LABELS:
        silo |= avant[n][:, :, 3] > 8
    libre &= ndimage.distance_transform_edt(~silo) <= 28

    masse = Image.new('RGBA', (W, H))      # branches, volume, contour
    feuilles = Image.new('RGBA', (W, H))   # feuillages du banc de props
    d = ImageDraw.Draw(masse)

    # branche : elle suit le rebord exterieur, au-dessus et au-dessous du passage
    trait = (72, 26, 5, 240)
    for y_debut, y_fin in ((y0 - LINTEAU, y0 - LINTEAU - 96), (y1 + SEUIL, y1 + SEUIL + 60)):
        pas = -1 if y_fin < y_debut else 1
        points = []
        for y in range(y_debut, y_fin, pas):
            xs = np.nonzero(L['02_structure'][y, 0:145, 3] > 8)[0]
            if len(xs):
                points.append((int(xs.min()) + 3, y))
            elif points:
                break
        if len(points) > 3:
            d.line(points, fill=trait, width=8, joint='curve')
            d.line([(p[0] + 1, p[1] + 1) for p in points], fill=(108, 51, 14, 160), width=3)

    # deux petites crosses qui referment le cadre sur l'angle du passage
    d.arc((-30, y0 - 28, 34, y0 + 32), 200, 340, fill=trait, width=7)
    d.arc((-30, y1 - 32, 34, y1 + 28), 20, 160, fill=trait, width=7)

    # feuillages
    dossier = os.path.join(REPO, 'sprites', 'individuels')
    for nom, x, y, echelle, miroir, angle, f in CADRE_FEUILLES:
        im = Image.open(os.path.join(dossier, nom)).convert('RGBA')
        if echelle != 1.0:
            im = im.resize((max(1, round(im.width * echelle)),
                            max(1, round(im.height * echelle))), Image.LANCZOS)
        if miroir:
            im = ImageOps.mirror(im)
        if angle:
            im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
        coller(feuilles, teinte(im, f), x, y)

    # le feuillage fait masse : on comble les jours entre les feuilles, ce qui
    # donne un buisson plein et non des feuilles eparses
    a = np.array(feuilles)
    sil = ndimage.binary_closing(a[:, :, 3] > 48, np.ones((9, 9), bool))
    sil = ndimage.binary_dilation(sil, np.ones((5, 5), bool))
    sil &= libre
    creux = sil & (a[:, :, 3] <= 48)
    yy = np.arange(H)[:, None]
    u = np.clip((yy - 170) / 240.0, 0, 1)
    vert = (np.array([74, 96, 32], float)[None, None, :] * (1 - u[:, :, None]) +
            np.array([38, 52, 19], float)[None, None, :] * u[:, :, None])
    vert = ambiance(vert, 1.0)
    rgb = np.zeros((H, W, 4), 'uint8')
    rgb[..., :3] = np.clip(vert, 0, 255)
    rgb[..., 3] = 238
    rgb[~creux] = 0
    masse.alpha_composite(Image.fromarray(rgb, 'RGBA'))

    # contour du massif : le meme trait sombre que l'extremite de la piece
    contour = ndimage.binary_dilation(sil, np.ones((5, 5), bool)) & ~sil
    contour &= (np.arange(W)[None, :] < 138)
    rgb = np.zeros((H, W, 4), 'uint8')
    rgb[..., :3] = (56, 20, 4)
    rgb[..., 3] = 232
    rgb[~contour] = 0
    masse.alpha_composite(Image.fromarray(rgb, 'RGBA'))

    masse.alpha_composite(feuilles)

    a = np.array(masse)
    a[~libre] = 0                          # le passage reste franchissable
    base = Image.fromarray(L['02_structure'], 'RGBA')
    base.alpha_composite(Image.fromarray(a, 'RGBA'))
    L['02_structure'] = np.array(base)


# ---------------------------------------------------- 2. trou sous le tronc

def bornes_tronc(L):
    """Le tronc est la seule matiere dessinee au-dessus du toit : ses bords y
    sont lisibles directement. C'est son diametre qui regle le trou."""
    st = L['02_structure']
    bande = st[TRONC_BANDE[0]:TRONC_BANDE[1], :, 3] > 8
    xs = np.nonzero(bande.any(0))[0]
    return int(xs.min()), int(xs.max())


def pied_tronc(L, x0, x1):
    """Ligne de plancher ou le tronc pose : on descend le long du tronc depuis
    la hauteur du mur, en tolerant les petits jours entre les montants."""
    st = L['02_structure'][:, :, 3] > 8
    pieds = []
    for x in range(x0 + 8, x1 - 7):
        col = st[:, x]
        y = 110
        while y < 420 and not col[y]:
            y += 1
        if y >= 420:
            continue
        bas = y
        while y < 420:
            if col[y]:
                bas = y
            elif not col[y:y + 9].any():
                break
            y += 1
        pieds.append(bas)
    return int(np.median(pieds)) if pieds else 218


def echelle_bornes(L, x0, x1):
    """Montants de l'echelle : deux pics clairs au coeur du tronc."""
    g0, g1 = x0 + 24, x1 - 24
    bande = L['02_structure'][120:210, g0:g1].astype(float)
    prof = (bande[:, :, :3].mean(2) * (bande[:, :, 3] > 8)).mean(0)
    lisse = np.convolve(prof, np.ones(5) / 5.0, 'same')
    milieu = len(lisse) // 2
    a = int(np.argmax(lisse[:milieu - 4]))
    b = int(np.argmax(lisse[milieu + 4:])) + milieu + 4
    return g0 + a, g0 + b


def trou_sous_tronc(L):
    """Perfore le plancher dans le diametre du tronc : le trou en est la
    continuation vers le bas, l'echelle y descend."""
    sol = L['01_sol']
    H, W = sol.shape[:2]
    avant_sol = sol.copy()
    tx0, tx1 = bornes_tronc(L)
    cx = (tx0 + tx1) / 2.0
    rx = (tx1 - tx0) / 2.0
    cy = float(pied_tronc(L, tx0, tx1))
    ry = float(TROU_RY)

    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    e = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    dedans = e <= 1.0
    visible = dedans & (yy >= cy)          # le haut est sous le tronc

    # --- le puits : paroi du fond a peine eclairee, puis le noir
    u = np.clip((yy - cy) / ry, 0, 1)[:, :, None]
    fond = np.array([64, 43, 27], float) * (1 - u) ** 1.4 + np.array([9, 6, 5], float) * u
    fond = fond * (1 - 0.28 * np.clip(e, 0, 1)[:, :, None] ** 2)
    sol[dedans, :3] = np.clip(fond, 0, 255)[dedans].astype('uint8')
    sol[dedans, 3] = 255
    # le tronc masque le haut du puits : ombre portee, mais la paroi du fond
    # reste lisible — c'est elle qui dit que le tronc continue en bas
    franche = visible & (yy < cy + 6)
    f = np.clip((cy + 6 - yy) / 6.0, 0, 1)[franche][:, None]
    cible = sol[franche].astype(float)
    cible[:, :3] = cible[:, :3] * (1 - 0.42 * f) + np.array([18, 11, 7], float) * (0.42 * f)
    sol[franche] = np.clip(cible, 0, 255).astype('uint8')

    # --- l'echelle plonge dans le trou
    lx0, lx1 = echelle_bornes(L, tx0, tx1)
    epaisseur = 5
    profondeur = int(ry * 0.82)
    motif = L['02_structure'][int(cy) - 62:int(cy) - 42, lx0:lx1 + 1].astype(float)
    m = motif[:, :, 3] > 8
    bois = motif[m][:, :3].mean(0) if m.any() else np.array([152, 86, 34], float)

    haut = np.arange(int(cy), int(cy) + profondeur + 6)[:, None, None]
    clair = np.clip(1.18 - 0.80 * np.clip((haut - cy) / float(profondeur), 0, 1), 0.30, 1.25)

    # montants
    for xa, xb in ((lx0, lx0 + epaisseur), (lx1 - epaisseur, lx1)):
        masque = visible[int(cy):int(cy) + profondeur + 6, xa:xb]
        rgb = np.broadcast_to(np.clip(bois[None, None, :] * 1.05 * clair, 0, 255),
                              (clair.shape[0], xb - xa, 3))
        cible = sol[int(cy):int(cy) + profondeur + 6, xa:xb].astype(float)
        cible[masque, :3] = rgb[masque, :]
        sol[int(cy):int(cy) + profondeur + 6, xa:xb] = cible.astype('uint8')

    # barreaux : l'echelle s'enfonce, les echelons se resserrent
    y, pas = cy + 7.0, 11.0
    while y < cy + profondeur:
        yb = int(round(y))
        f = float(np.clip(1.18 - 0.80 * ((y - cy) / float(profondeur)), 0.30, 1.25))
        for ligne in (yb, yb + 1, yb + 2):
            if ligne >= H:
                continue
            masque = visible[ligne, lx0 + 1:lx1 - 1]
            cible = sol[ligne, lx0 + 1:lx1 - 1].astype(float)
            cible[masque, :3] = np.clip(bois * 1.22 * f, 0, 255)
            sol[ligne, lx0 + 1:lx1 - 1] = cible.astype('uint8')
        y += pas
        pas = max(4.0, pas - 1.2)

    # --- levre et collets d'ecorce, dessines sur la structure
    # Le tronc recouvre le haut de l'ellipse : la levre ne se trace donc qu'a
    # partir du pied du tronc, ou elle prend le relais de l'ecorce.
    st = Image.fromarray(L['02_structure'], 'RGBA')
    canvas = Image.new('RGBA', (W, H))
    levre = (e > 1.0) & (e <= 1.10) & (yy >= cy)
    t = np.clip((yy - cy - ry * 0.05) / (ry * 0.95), 0, 1)[:, :, None]
    ecorce = np.array([94, 47, 16], float)
    chant = np.clip(avant_sol[:, :, :3].astype(float) * 0.58 + np.array([24, 11, 4]), 0, 255)
    # haut de levre en ecorce (cote tronc), bas en chant de planche (cote salle)
    coul = ecorce * (1 - t) + chant * t
    rgb = np.zeros((H, W, 4), 'uint8')
    rgb[..., :3] = np.clip(coul, 0, 255)
    rgb[..., 3] = 255
    rgb[~levre] = 0
    canvas.alpha_composite(Image.fromarray(rgb, 'RGBA'))

    # collets : deux contreforts d'ecorce qui enracinent le tronc
    d = ImageDraw.Draw(canvas)
    for s in (-1, 1):
        xb = cx + s * (rx - 2)
        d.polygon([(xb - s * 2, cy - 12), (xb + s * 15, cy - 2),
                   (xb + s * 19, cy + 10), (xb - s * 1, cy + 8)],
                  fill=(int(ecorce[0] * 1.06), int(ecorce[1] * 1.06), int(ecorce[2]), 255))
        for k in (4, 9):
            d.line([(xb + s * 2, cy + k - 1), (xb + s * 15, cy + k + 1)],
                   fill=(int(ecorce[0] * 0.62), int(ecorce[1] * 0.62), int(ecorce[2] * 0.7), 200),
                   width=2)
    st.alpha_composite(canvas)
    L['02_structure'] = np.array(st)

    # --- arete du chant, cote salle : la tranche des planches accroche le jour
    arete = (e > 1.10) & (e <= 1.19) & (yy > cy + ry * 0.35)
    f = np.clip((1.19 - e) / 0.09, 0, 1)[:, :, None]
    cible = sol[arete].astype(float)
    cible[:, :3] = cible[:, :3] * (1 - 0.34 * f[arete]) + np.array([248, 186, 92], float) * (0.34 * f[arete])
    sol[arete] = np.clip(cible, 0, 255).astype('uint8')

    # --- le plancher s'assombrit autour du trou, puis l'ombre de contact
    halo = (e > 1.19) & (e <= 1.46) & (yy >= cy - 2)
    f = np.clip((1.46 - e) / 0.27, 0, 1)[:, :, None]
    cible = sol[halo].astype(float)
    cible[:, :3] = cible[:, :3] * (1 - 0.42 * f[halo]) + np.array([38, 13, 3], float) * (0.42 * f[halo])
    sol[halo] = np.clip(cible, 0, 255).astype('uint8')

    om = L['08_ombres_acces']
    halo = (e > 1.10) & (e <= 1.66) & (yy >= cy - 1)
    a = np.rint(np.clip((1.66 - e) / 0.56, 0, 1) ** 1.4 * 58)[halo].astype('uint8')
    om[halo, 3] = np.maximum(om[halo, 3], a)
    om[halo, :3] = 0
    return int(cx), int(cy), int(round(2 * rx)), int(ry)


# --------------------------------------------------------- 3. porte / arche

def mur_derriere_porte(L):
    """Rebouche le trou laisse par l'ancienne porte : interpolation horizontale
    entre le mur de gauche et celui de droite, ligne par ligne."""
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
    """Arche de guilde : le battant cintre du banc de props sert d'encadrement."""
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
        lisere = ndimage.binary_dilation(dedans, np.ones((3, 3), bool)) & ~dedans & (a[:, :, 3] > 0)
        a[lisere, :3] = np.rint(a[lisere, :3] * 0.5).astype('uint8')
        seul = dedans & (yy >= h - max(5, ep // 2) - 3)
        a[seul, :3] = 150, 104, 50
        a[seul, 3] = 255

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
    x0, x1, y0, y1 = PORTE['x0'], PORTE['x1'], PORTE['y0'], PORTE['y1']
    mur_derriere_porte(L)
    embleme = Image.open(os.path.join(REPO, 'sprites', 'individuels',
                                      'embleme_feuille_bois.png')).convert('RGBA')
    for ouverte, nom in ((True, '05_porte_maitre'), (False, '05_porte_maitre_battants')):
        couche = np.zeros_like(L['02_structure'])
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
    cx, cy, largeur, profondeur = trou_sous_tronc(J)
    porte(J)
    print('ouverture ouest y=%d..%d (%d px), linteau %d px, seuil %d px'
          % (y0, y1, y1 - y0 + 1, LINTEAU, SEUIL))
    print('trou centre x=%d y=%d : %d px de large (diametre du tronc) x %d px de profondeur'
          % (cx, cy, largeur, profondeur))

    N = {}
    for n in J:
        N[n] = J[n].copy() if n == '08_ombres_acces' else nuit(J[n])
    N['00_exterieur'] = charger('nuit')['00_exterieur']

    ecrire(J, 'jour')
    ecrire(N, 'nuit')
    print('salle 02 regeneree : calques, composites, aseprite, tiled')


if __name__ == '__main__':
    main()
