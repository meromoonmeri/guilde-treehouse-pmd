#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aides du lot « Cristal boréal — couches animées multiples ».

Le lot part de ce que la zone `cristal_boreal` du lot magenta V1 contient déjà : les cinq calques
statiques, la séquence native protégée de douze poses, les masques du biome cristal, et l'onde
boréale indexée du lot V12. Aucune couleur n'est inventée : chaque pixel livré est soit recopié d'un
de ces fichiers, soit re-coloré avec une palette qui y figure déjà (rotation d'indices), soit posé à
une autre rangée de son propre plan. Les règles de `source/layouts_magenta_v1/palette.py` sont
réutilisées telles quelles, pas réécrites.
"""
from pathlib import Path
import io
import json
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/layouts_magenta_v1'))
from palette import key, tint                                     # noqa: E402  (règles du lot V1)

NN = Image.Resampling.NEAREST
ZONE = 'cristal_boreal'
ZD = R / 'renders/layouts_magenta_v1/zones/cristal_boreal'
MD = R / 'renders/layouts_magenta_v1/masques/cristal'
SRC = R / 'source/layouts_magenta_v1'
V12 = R / 'renders/boreales_palette_cycling_v12'
OUT = R / 'renders/cristal_boreal_layers_animees_v1'
GRILLE = 8
VOILE = 96                                                        # opacité du calque de lueur, comme V13


def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def charger(p, mode='RGBA', taille=None):
    im = Image.open(p).convert(mode)
    return im.resize(taille, NN) if taille else im


def clip(a, masque):
    out = a.copy()
    out[~masque] = 0
    return out


def poses_native(gif):
    """Les poses de la séquence native, dans l'ordre, avec leur durée lue dans le GIF lui-même."""
    out, dures = [], []
    with Image.open(R / gif) as g:
        for i in range(g.n_frames):
            g.seek(i)
            out.append(np.array(g.convert('RGBA')).copy())
            dures.append(int(g.info.get('duration', 100) or 100))
    return out, dures


def palette_replay(indexee, alpha, palette):
    """Rejoue une frame du palette cycling V12 : image indexée + palette de cette frame + alpha."""
    idx = np.array(indexee.convert('P'))
    rgb = np.array(palette, dtype='uint8')[idx]
    a = np.array(alpha)
    out = np.dstack([rgb, a])
    out[a == 0] = 0
    return out


def redimensionner_indexes(indexee, alpha, taille):
    """Un plan d'indices et son alpha, agrandis/rétrilis au plus proche voisin : les indices restent
    exacts, aucun niveau d'alpha intermédiaire n'apparaît (le NEAREST ne mélange pas)."""
    return (np.array(indexee.convert('P').resize(taille, NN)),
            np.array(alpha.resize(taille, NN)))


def classes_eclat(rgb, alpha, nb=4):
    """Rampes de luminance d'un calque, bornées sur ses propres couleurs : renvoie la carte des
    classes (0..nb-1) et la liste des couleurs représentantes, toutes présentes dans le calque."""
    op = alpha > 0
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(float)
    lum[~op] = np.nan
    bornes = np.nanpercentile(lum, np.linspace(0, 100, nb + 1)[1:-1])
    carte = np.digitize(lum, bornes).astype(np.uint8)
    carte[~op] = 0
    couleurs = []
    for k in range(nb):
        m = op & (carte == k)
        if not m.any():
            m = op & (carte == max(0, min(nb - 1, k - 1)))
        # le représentant est LA couleur du calque la plus fréquente de la classe, jamais une moyenne
        palettes, compte = np.unique(rgb[m], axis=0, return_counts=True)
        couleurs.append([int(v) for v in palettes[int(np.argmax(compte))]])
    return carte, np.array(couleurs, dtype='uint8')


def boucle(frames, chemin, duree_ms, perte=True):
    """WebP en boucle, sans perte, durées uniformes déclarées."""
    o = dict(save_all=True, append_images=frames[1:], duration=duree_ms, loop=0)
    o.update(dict(lossless=True, method=4) if perte else dict(quality=100, method=6, exact=True))
    frames[0].save(chemin, format='WEBP', **o)


def ora(chemin, couches, aplatie):
    """OpenRaster au format du lot magenta V1 (mimetype magasiné, pile du bas vers le haut).

    `couches` = [(nom, PIL.Image, visible), ...] du BAS vers le HAUT ; un calque non visible est la
    frame d'une animation dont seule la première pose est affichée.
    """
    racine = ET.Element('image', {'w': str(aplatie.width), 'h': str(aplatie.height),
                                  'name': Path(chemin).stem})
    pile = ET.SubElement(racine, 'stack')
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (nom, im, visible) in reversed(list(enumerate(couches))):
            nom_fichier = 'data/layer%d.png' % i
            ET.SubElement(pile, 'layer', {'name': nom, 'src': nom_fichier, 'x': '0', 'y': '0',
                                         'opacity': '1.0',
                                         'visibility': 'visible' if visible else 'hidden',
                                         'composite-op': 'svg:src-over'})
            b = io.BytesIO()
            im.save(b, format='PNG')
            z.writestr(nom_fichier, b.getvalue())
        z.writestr('stack.xml', ET.tostring(racine, encoding='UTF-8', xml_declaration=True))
        b = io.BytesIO()
        aplatie.save(b, format='PNG')
        z.writestr('mergedimage.png', b.getvalue())
    octets = bio.getvalue()
    Path(chemin).write_bytes(octets)
    return octets


def lire_ora(chemin):
    """(liste [(nom, PNG, visible)], image fusionnée) — pour que les contrôles relisent le fichier."""
    out = []
    with zipfile.ZipFile(chemin) as z:
        racine = ET.fromstring(z.read('stack.xml').decode())
        for el in racine.find('stack'):
            src = el.get('src')
            out.append((el.get('name'), z.read(src), el.get('visibility') == 'visible'))
        return out, z.read('mergedimage.png')


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, format='PNG')
    return b.getvalue()


def webp_uri(im, demi=False):
    import base64
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    if demi:
        im = im.resize((max(1, im.width // 2), max(1, im.height // 2)), NN)
    b = io.BytesIO()
    im.save(b, format='WEBP', save_all=True, lossless=True, exact=True, method=4)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()


def empile(base, couches):
    """Recomposition dans l'ordre déclaré, avec les mêmes opérations PIL que la génération."""
    fond = base.copy()
    for im in couches:
        fond.alpha_composite(im)
    return fond


def masque(op):
    return np.uint8(op) * 255
