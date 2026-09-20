"""Spriter Pro v1 — construction du pack `sprites/spriter_pro_v1/`.

Six cartes composées EXCLUSIVEMENT de tuiles canoniques Métano (8x8) :
aucun dessin généré, aucune recoloration, aucune transformation des textures.
Usage :  python source/build_spriter_pro.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, base64, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spriter_pro import engine
from spriter_pro.layouts import LAYOUTS, PACK

R = engine.R
O = R / PACK['directory']
O.mkdir(parents=True, exist_ok=True)
SHEET = PACK['sheet']

source, source_info = engine.load_sources()
studio = engine.Studio(source, source_info)

records, layers_by_map = [], {}
for cfg in LAYOUTS:
    problems = engine.validate_layout(cfg)
    assert not problems, f'{cfg["id"]}: ' + ' ; '.join(problems)
    p = O / cfg['id']
    p.mkdir(exist_ok=True)
    layers, record = engine.compile_layout(studio, cfg)
    g, cliffs, banks, water = layers
    grass_png = studio.render(g)
    cliff_png = studio.render(cliffs)
    bank_png = studio.render(banks)
    grass_png.save(p / 'herbe.png')
    cliff_png.save(p / 'falaises_bordures.png')
    bank_png.save(p / 'berges_eau.png')
    dry = Image.alpha_composite(grass_png, cliff_png)
    dry.save(p / 'sans_eau_sans_chemins.png')
    wet_base = Image.alpha_composite(dry, bank_png)
    for f in range(4):
        w = studio.render(water, f)
        w.save(p / f'eau_frame_{f + 1}.png')
        Image.alpha_composite(wet_base, w).save(p / f'avec_eau_frame_{f + 1}.png')
    (p / 'layout.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
    engine.write_tiled(p, record, layers, SHEET)
    records.append(record)
    layers_by_map[cfg['id']] = layers
    print(cfg['id'], '·', len(record['waterfalls']), 'chutes ·',
          len(cfg.get('lakes', [])), 'bassins ·', len(studio.tiles), 'tuiles source au total')

count = engine.write_atlas(studio, O, SHEET)
engine.write_provenance(O, studio, source_info, records, SHEET, count, engine.RULES)
print('Atlas', SHEET, ':', len(studio.tiles), 'entrées utilisées /', count,
      '·', len(studio.animations), 'animations natives')

# Planche de présentation (réduite) — explicitement hors assets de jeu.
fp = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(fp, 24)
small = ImageFont.truetype(fp, 15)
board = Image.new('RGB', (1600, 132 + 616 * len(records)), '#1b2a23')
d = ImageDraw.Draw(board)
d.text((28, 22), 'SPRITER PRO — CARTES CANONIQUES MÉTANO', font=font, fill='#e6d493')
d.text((28, 62), f'{len(records)} layouts · 2048 × 1536 px chacun · grille 8 px · '
                 'aucun chemin, aucune maison', font=small, fill='#b6c6ae')
d.text((28, 96), 'SANS EAU — falaises, herbe et bordures', font=small, fill='#e6d493')
d.text((816, 96), 'AVEC EAU — 4 frames natives, calques séparés', font=small, fill='#a3dae3')
for i, m in enumerate(records):
    y = 132 + i * 616
    for j, file in enumerate(['sans_eau_sans_chemins.png', 'avec_eau_frame_1.png']):
        im = Image.open(O / m['id'] / file).resize((768, 576), Image.Resampling.NEAREST)
        board.paste(im, (24 + j * 792, y))
    d.text((28, y + 586), f'{m["id"][:2]} · {m["name"]}', font=small, fill='#e6d493')
board.save(O / 'apercu_comparatif.png')

# Aperçu HTML autonome.
def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()

view = []
for m in records:
    p = O / m['id']
    view.append({**m, 'dry': uri(p / 'sans_eau_sans_chemins.png'),
                 'banks': uri(p / 'berges_eau.png'),
                 'water': [uri(p / f'eau_frame_{i}.png') for i in range(1, 5)]})
(R / 'apercu_spriter_pro_v1.html').write_text(
    (R / 'source/spriter_pro/viewer.html').read_text()
    .replace('__DATA__', json.dumps(view, ensure_ascii=False)))
print('Aperçu :', 'apercu_spriter_pro_v1.html')
print('Done:', len(records), 'cartes,', len(studio.tiles), 'tuiles canoniques,',
      len(studio.animations), 'animations natives.')
