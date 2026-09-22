#!/usr/bin/env python3
"""Loupe d'étude : recadrage agrandi d'une feuille native avec grille 8 px et index de tuiles.
Usage : etude.py FEUILLE x0 y0 x1 y1 zoom sortie.png   (coordonnées pixel, multiples de 8)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]

def loupe(sheet, x0, y0, x1, y1, zoom, out, grid=True):
    src = Image.open(ROOT / 'banque_canonique/atlas' / f'{sheet}.png').convert('RGBA')
    crop = src.crop((x0, y0, x1, y1))
    bg = Image.new('RGBA', crop.size, (255, 0, 255, 255))
    bg.alpha_composite(crop)
    big = bg.resize((crop.width * zoom, crop.height * zoom), Image.NEAREST)
    d = ImageDraw.Draw(big)
    if grid:
        for x in range(0, crop.width + 1, 8):
            c = (0, 0, 255) if ((x0 + x) // 8) % 4 == 0 else (0, 0, 0)
            d.line([(x * zoom, 0), (x * zoom, big.height)], fill=c, width=1)
        for y in range(0, crop.height + 1, 8):
            c = (0, 0, 255) if ((y0 + y) // 8) % 4 == 0 else (0, 0, 0)
            d.line([(0, y * zoom), (big.width, y * zoom)], fill=c, width=1)
        for x in range(0, crop.width, 32):
            d.text((x * zoom + 2, 1), str((x0 + x) // 8), fill=(255, 255, 255))
        for y in range(0, crop.height, 32):
            d.text((1, y * zoom + 2), str((y0 + y) // 8), fill=(255, 255, 255))
    big.convert('RGB').save(out)
    return out

if __name__ == '__main__':
    sheet, x0, y0, x1, y1, zoom, out = sys.argv[1:8]
    loupe(sheet, int(x0), int(y0), int(x1), int(y1), int(zoom), out)
