#!/usr/bin/env python3
"""Extrait le kit de modules natifs 'Falaises Métano' (voir kit/modules.json).

Sorties (source/reverie_town_v1/kit/) :
  REVERIE_KIT_Falaises_Metano_jour.png / _nuit.png : planche importable (grille 8 px, fond transparent,
      modules séparés de 8 px, mêmes positions jour/nuit), pixels natifs non modifiés.
  REVERIE_KIT_Falaises_Metano_planche.png : planche de contrôle 2x avec fond magenta et étiquettes.
  kit_index.json : position de chaque module dans la planche + rectangle source.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ATLAS = ROOT / 'banque_canonique/atlas'
T = 8


def load(sheet):
    return Image.open(ATLAS / f'{sheet}.png').convert('RGBA')


def main():
    spec = json.loads((HERE / 'kit/modules.json').read_text())
    day, night = load(spec['sheet_day']), load(spec['sheet_night'])
    assert day.size == night.size
    entries = list(spec['modules'].items()) + [(k, v) for k, v in spec['macros'].items()]
    # Disposition : lignes de modules, largeur max 120 tuiles.
    x, y, row_h, maxw = 1, 1, 0, 120
    index = {}
    for name, m in entries:
        if x + m['w'] + 1 > maxw:
            x, y, row_h = 1, y + row_h + 1, 0
        index[name] = {'kit_tx': x, 'kit_ty': y, **m}
        x += m['w'] + 1
        row_h = max(row_h, m['h'])
    W, H = maxw * T, (y + row_h + 1) * T
    out_day, out_night = Image.new('RGBA', (W, H)), Image.new('RGBA', (W, H))
    for name, e in index.items():
        box = (e['tx'] * T, e['ty'] * T, (e['tx'] + e['w']) * T, (e['ty'] + e['h']) * T)
        pos = (e['kit_tx'] * T, e['kit_ty'] * T)
        out_day.paste(day.crop(box), pos)
        out_night.paste(night.crop(box), pos)
    out_day.save(HERE / 'kit/REVERIE_KIT_Falaises_Metano_jour.png')
    out_night.save(HERE / 'kit/REVERIE_KIT_Falaises_Metano_nuit.png')
    # Planche de contrôle 2x
    z = 2
    bg = Image.new('RGBA', out_day.size, (255, 0, 255, 255))
    bg.alpha_composite(out_day)
    big = bg.resize((W * z, H * z), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for name, e in index.items():
        x0, y0 = e['kit_tx'] * T * z, e['kit_ty'] * T * z
        x1, y1 = (e['kit_tx'] + e['w']) * T * z, (e['kit_ty'] + e['h']) * T * z
        d.rectangle([x0 - 1, y0 - 1, x1, y1], outline=(0, 0, 255), width=1)
        if e.get('crown_rel') is not None:
            cy = y0 + (e['crown_rel'] * T + 5) * z
            d.line([(x0, cy), (x1, cy)], fill=(255, 255, 0), width=1)
        d.text((x0 + 2, y0 - 12), name, fill=(255, 255, 255))
    big.convert('RGB').save(HERE / 'kit/REVERIE_KIT_Falaises_Metano_planche.png')
    (HERE / 'kit/kit_index.json').write_text(json.dumps(
        {'sheet_day': spec['sheet_day'], 'sheet_night': spec['sheet_night'], 'tile_px': T,
         'kit_size_px': [W, H], 'modules': index}, indent=1, ensure_ascii=False))
    # Vérification : chaque tuile du kit est identique à sa tuile source (jour et nuit).
    for name, e in index.items():
        for dy in range(e['h']):
            for dx in range(e['w']):
                for src, out in ((day, out_day), (night, out_night)):
                    a = src.crop(((e['tx'] + dx) * T, (e['ty'] + dy) * T, (e['tx'] + dx + 1) * T, (e['ty'] + dy + 1) * T))
                    b = out.crop(((e['kit_tx'] + dx) * T, (e['kit_ty'] + dy) * T, (e['kit_tx'] + dx + 1) * T, (e['kit_ty'] + dy + 1) * T))
                    assert a.tobytes() == b.tobytes(), (name, dx, dy)
    print(f'kit: {len(index)} modules, planche {W}x{H} px, vérification tuile à tuile OK')


if __name__ == '__main__':
    main()
