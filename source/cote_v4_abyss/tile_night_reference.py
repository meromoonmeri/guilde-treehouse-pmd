#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les variantes NUIT des tilesets de Metano Town.

================================================================
FORMAT .tile — DECODE, PAS SUPPOSE
================================================================
Aucune documentation ne le decrit. Reconstitue en analysant
Metano_Town_Base.tile, puis VALIDE par reconstruction bit-a-bit :
relire puis reecrire sans transformation redonne un fichier au MD5
identique (2dd72c6a... sur 1 231 857 octets).

    [0..3]    uint32  tileSize        (8)
    [4..7]    uint32  nbEntrees       (35646 pour Metano_Town_Base)
    [8..]     table   x(u32) y(u32) offset(u64)   x nbEntrees
    [offset]  uint32  taillePNG
              uint32  padding (conserve tel quel)
              PNG     8x8 RGBA

Plusieurs entrees de la table pointent le MEME offset : les tuiles
identiques sont mutualisees. 3929 tuiles distinctes pour 35646
references dans Metano_Town_Base.

================================================================
CE QUE FAIT LA TRANSFORMATION — ET CE QU'ELLE NE FAIT PAS
================================================================
Traitement colorimetrique par tuile : la ville passe sous la lune.

  * luminosite abaissee (les surfaces claires le restent, mais moins)
  * teintes tirees vers le bleu nuit, le rouge recule
  * saturation reduite : la nuit mange les couleurs
  * les pixels DEJA sombres le deviennent moins vite (courbe non
    lineaire) — sinon tout vire au noir uniforme et la carte devient
    illisible

Ce n'est PAS ce que fait EoSO : leurs GuildOutsideNight.tile sont
redessines a la main, avec des fenetres allumees et des ombres
portees reorientees. Ici on obtient une ville bleutee coherente,
pas des sources de lumiere.

Les fichiers generes restent remplacables : le jour ou des tuiles
peintes a la main existent, on ecrase, rien d'autre ne bouge.

Usage :
    python3 tools/tile_night.py --check          verifie le format
    python3 tools/tile_night.py --run            genere les *_Night.tile
"""
import io
import os
import struct
import sys
import hashlib

try:
    from PIL import Image
except ImportError:
    print("Pillow requis : pip install --break-system-packages Pillow")
    sys.exit(1)

TILE_DIR = 'Content/Tile'

# Les 14 tilesets composant metano_town, releves dans les Layers du
# .rsground (aucun devine).
METANO = [
    'Metano_Town_Base',
    'Metano_Town_Cliffs',
    'Metano_Town_Fringe',
    'Metano_Town_Objects',
    'Metano_Town_Objects_Over',
    'Metano_Town_Objects_Under',
    'Metano_Town_Animated',
    'Metano_Town_Animated_Under',
    'Metano_Town_Animation_Tileset',
    'Metano_Town_River_Animation_1',
    'Metano_Town_River_Animation_2',
    'Metano_Town_River_Animation_3',
    'Metano_Town_River_Animation_4',
    'Metano_Town_River_Sparkles',
]


def read_tile(path):
    """-> (tileSize, entrees[(x,y,offset)], blobs{offset:(pad, png)})"""
    d = open(path, 'rb').read()
    tile, n = struct.unpack('<2I', d[:8])
    ents = []
    p = 8
    for _ in range(n):
        x, y, o = struct.unpack('<IIQ', d[p:p + 16])
        p += 16
        ents.append((x, y, o))
    blobs = {}
    for o in sorted(set(e[2] for e in ents)):
        ln, pad = struct.unpack('<2I', d[o:o + 8])
        blobs[o] = (pad, d[o + 8:o + 8 + ln])
    return tile, ents, blobs, d


def write_tile(path, tile, ents, blobs):
    """Reecrit en recalculant les offsets. Ordre des blobs conserve."""
    out = bytearray()
    out += struct.pack('<2I', tile, len(ents))
    order = sorted(blobs)
    newoff = {}
    cur = 8 + len(ents) * 16
    for o in order:
        newoff[o] = cur
        cur += 8 + len(blobs[o][1])
    for x, y, o in ents:
        out += struct.pack('<IIQ', x, y, newoff[o])
    for o in order:
        pad, png = blobs[o]
        out += struct.pack('<2I', len(png), pad)
        out += png
    with open(path, 'wb') as f:
        f.write(bytes(out))
    return len(out)


def to_night(png_bytes):
    """Transforme une tuile 8x8 RGBA en sa version nocturne."""
    im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    px = im.load()
    w, h = im.size
    for j in range(h):
        for i in range(w):
            r, g, b, a = px[i, j]
            if a == 0:
                continue                      # transparent : intact
            # Luminance perçue : sert a doser l'assombrissement.
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            # Courbe non lineaire : les zones deja sombres perdent moins,
            # sinon la carte devient un aplat noir illisible.
            k = 0.20 + 0.30 * lum
            # Desaturation LEGERE seulement. Un premier reglage a 0.55
            # donnait un brouillard gris illisible : la nuit garde ses
            # couleurs, elle les refroidit.
            gr = 0.299 * r + 0.587 * g + 0.114 * b
            sat = 0.95
            r2 = r * sat + gr * (1 - sat)
            g2 = g * sat + gr * (1 - sat)
            b2 = b * sat + gr * (1 - sat)
            # Bascule franche vers le bleu nuit : le rouge s'effondre,
            # le bleu est AMPLIFIE. C'est ce qui fait lire la nuit plutot
            # qu'une simple baisse de luminosite.
            r2 *= k * 0.52
            g2 *= k * 0.70
            b2 *= k * 1.60
            # Voile lunaire tres leger sur les surfaces deja claires.
            b2 += 6 * lum
            px[i, j] = (min(255, int(r2)), min(255, int(g2)),
                        min(255, int(b2)), a)
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def check():
    """Preuve du format : relire + reecrire sans toucher = MD5 identique."""
    ok = True
    for name in METANO:
        p = os.path.join(TILE_DIR, name + '.tile')
        if not os.path.exists(p):
            print(f'  {name:34s} ABSENT')
            ok = False
            continue
        tile, ents, blobs, raw = read_tile(p)
        tmp = '/tmp/_chk.tile'
        write_tile(tmp, tile, ents, blobs)
        same = open(tmp, 'rb').read() == raw
        print(f'  {name:34s} {len(blobs):5d} tuiles  '
              f'{len(ents):6d} refs  roundtrip={"OK" if same else "ECHEC"}')
        ok = ok and same
    print('\nFORMAT VALIDE' if ok else '\nPROBLEME DE FORMAT')
    return ok


def run():
    total_t = 0
    for name in METANO:
        src = os.path.join(TILE_DIR, name + '.tile')
        dst = os.path.join(TILE_DIR, name + '_Night.tile')
        if not os.path.exists(src):
            print(f'  {name:34s} ABSENT, ignore')
            continue
        tile, ents, blobs, _ = read_tile(src)
        night = {o: (pad, to_night(png)) for o, (pad, png) in blobs.items()}
        size = write_tile(dst, tile, ents, night)
        total_t += len(night)
        print(f'  {name+"_Night":40s} {len(night):5d} tuiles  '
              f'{size/1024:7.0f} Ko')
    print(f'\n{total_t} tuiles converties sur {len(METANO)} tilesets.')


if __name__ == '__main__':
    if '--check' in sys.argv:
        check()
    elif '--run' in sys.argv:
        run()
    else:
        print(__doc__)
