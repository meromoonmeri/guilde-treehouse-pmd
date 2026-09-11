"""Six silhouettes générées, placement natif et palette maîtrisée, sans nouveau dessin."""
from pathlib import Path
from PIL import Image
import numpy as np

R = Path(__file__).resolve().parents[1]
BOXES = [(193, 18, 66, 38), (29, 39, 121, 20), (332, 73, 124, 39),
         (271, 27, 83, 22), (81, 91, 73, 23), (189, 80, 95, 25)]


def prepare():
    sheet = Image.open(R / 'source/exterieurs/nuages_six_formes.png').convert('RGBA')
    assert sheet.size == (720, 432)
    out = Image.new('RGBA', (480, 408))
    for i, (x, y, w, h) in enumerate(BOXES):
        tile = sheet.crop(((i % 2)*360, (i//2)*144, (i % 2+1)*360, (i//2+1)*144))
        tile = tile.crop(tile.getbbox()).resize((w, h), Image.Resampling.NEAREST)
        out.alpha_composite(tile, (x, y))
    # Une palette de 96 tons suffit pour six nuages et évite des milliers de
    # couleurs quasi identiques dans les 480/504 cels de déplacement.
    alpha = out.getchannel('A')
    reduced = out.convert('RGB').quantize(colors=96, dither=Image.Dither.NONE).convert('RGBA')
    reduced.putalpha(alpha)
    a = np.array(reduced)
    a[a[:, :, 3] == 0] = 0
    assert not a[:, [0, -1], 3].any()
    Image.fromarray(a).save(R / 'source/falaise/nuages_native.png', optimize=True)
    print('Six familles de nuages, palette 96 tons, transparence et positions conservées.')


if __name__ == '__main__':
    prepare()
