"""
aseprite.py — écriture de fichiers .aseprite multi-calques.

Reprend le format binaire déjà utilisé dans source/rebuild_kit.py de ce dépôt
(en-tête ASE + une frame + un chunk Layer et un chunk Cel par calque), pour
que les planches produites soient directement éditables dans Aseprite.
"""

import struct
import zlib
from PIL import Image


def _astr(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _chunk(kind, data):
    return struct.pack("<IH", len(data) + 6, kind) + data


def ecrire(chemin, calques, taille):
    """
    calques : liste de (nom, image RGBA de la taille de la planche)
    taille  : (largeur, hauteur) de la planche
    """
    w, h = taille
    chunks = []
    for nom, _ in calques:
        chunks.append(_chunk(0x2004,
                             struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255)
                             + b"\0" * 3 + _astr(nom)))
    for i, (nom, im) in enumerate(calques):
        box = im.getbbox()
        if box:
            x, y, _, _ = box
            q = im.crop(box)
        else:
            x = y = 0
            q = Image.new("RGBA", (1, 1))
        chunks.append(_chunk(0x2005,
                             struct.pack("<HhhBHh", i, x, y, 255, 2, 0)
                             + b"\0" * 5
                             + struct.pack("<HH", q.width, q.height)
                             + zlib.compress(q.tobytes(), 9)))
    data = b"".join(chunks)
    frame = struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA, len(chunks), 100,
                        b"\0\0", len(chunks)) + data
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(frame) + 128, 0xA5E0, 1,
                     w, h, 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    with open(chemin, "wb") as f:
        f.write(bytes(header) + frame)
