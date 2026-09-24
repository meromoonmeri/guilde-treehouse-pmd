"""Secret Garden network (Ledian style): 6 connectable garden pieces, 512x512.

Method: generated terrain on magenta guided by secretgarden.png -> cut -> partition
into path/fond/left/right/foreground + one native-grass connector strip per 64px port.
See source/secretgarden_reseau_v1/GENERATION_LOG.md for the deferred T-junction.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
REF = R / 'secretgarden.png'
SIZE = (512, 512)
PATCH_BOX = (190, 240, 222, 272)  # clean flat path grass in secretgarden.png
# Strip: fully opaque 24px at the edge (bridges <=22px gaps), fade 24..32 inward.
OPAQUE_DEPTH = 24
STRIP_DEPTH = 32


def load(p):
    return Image.open(p).convert('RGBA')


def save(im, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def cut(im):
    a = np.array(im)
    f = a[:, :, :3].astype(float)
    m = (f[:, :, 0] > f[:, :, 1] * 1.4) & (f[:, :, 2] > f[:, :, 1] * 1.4) & (f[:, :, 2] > 35)
    a[m] = 0
    return Image.fromarray(a)


def part(im, m):
    a = np.array(im)
    a[~m] = 0
    return Image.fromarray(a)


def poly(points):
    im = Image.new('L', SIZE)
    ImageDraw.Draw(im).polygon(points, fill=255)
    return np.array(im) > 0


specs = [
    ('couloir_ns', 'Couloir nord-sud fleuri', 'couloir_ns', ['N', 'S'],
     [(221, 0), (288, 0), (288, 106), (407, 121), (406, 425), (325, 452), (325, 512), (191, 512), (191, 449), (93, 425), (93, 124), (221, 106)]),
    ('couloir_ew', 'Couloir est-ouest fleuri', 'couloir_ew', ['E', 'W'],
     [(0, 216), (73, 192), (439, 192), (512, 216), (512, 332), (433, 370), (80, 370), (0, 332)]),
    ('salle_traversee', 'Salle traversante', 'salle_traversee', ['N', 'S'],
     [(224, 0), (288, 0), (288, 149), (381, 174), (435, 262), (428, 355), (324, 445), (324, 512), (192, 512), (192, 445), (90, 355), (81, 262), (129, 174), (224, 149)]),
    ('salle_laterale', 'Salle laterale', 'salle_laterale', ['W', 'S'],
     [(103, 184), (381, 184), (454, 263), (446, 351), (324, 449), (324, 512), (192, 512), (192, 445), (75, 355), (0, 312), (0, 236), (75, 236)]),
    ('salle_carrefour', 'Salle carrefour', 'salle_carrefour', ['N', 'S', 'E', 'W'],
     [(224, 0), (288, 0), (288, 135), (381, 168), (423, 230), (512, 230), (512, 298), (423, 298), (388, 361), (322, 444), (322, 512), (190, 512), (190, 444), (121, 361), (82, 298), (0, 298), (0, 230), (82, 230), (130, 168), (224, 135)]),
    ('carrefour_clairiere', 'Carrefour de la clairiere', 'carrefour_clairiere', ['N', 'S', 'E', 'W'],
     [(224, 0), (288, 0), (288, 135), (381, 168), (423, 230), (512, 230), (512, 298), (423, 298), (388, 361), (322, 444), (322, 512), (190, 512), (190, 444), (121, 361), (82, 298), (0, 298), (0, 230), (82, 230), (130, 168), (224, 135)]),
]

ref_sha = hashlib.sha256(REF.read_bytes()).hexdigest()
patch = load(REF).crop(PATCH_BOX)
save(patch, O / 'materiaux/sol_raccord_natif.png')
p = np.array(patch.resize((64, 64), Image.Resampling.NEAREST))
fade = np.array([255] * OPAQUE_DEPTH + [round(255 * (31 - y) / 8) for y in range(OPAQUE_DEPTH, 32)], dtype='uint8')
stripe = p[:32].copy()
stripe[:, :, 3] = np.minimum(stripe[:, :, 3], fade[:, None])

manifest = {'reference': 'secretgarden.png (user commit)',
            'reference_sha256': ref_sha, 'patch_box': list(PATCH_BOX),
            'size': list(SIZE), 'port_width': 64,
            'opaque_depth': OPAQUE_DEPTH, 'strip_depth': STRIP_DEPTH,
            'deferred': ['couloir_t (T-junction N/E/W, bottom closed) — image limit reached, next turn'],
            'runtime_validated': False, 'rooms': []}
yy, xx = np.mgrid[:512, :512]
portspec = {'N': ((224, 0), (256, 8)), 'S': ((224, 480), (256, 504)),
            'W': ((0, 224), (8, 256)), 'E': ((480, 224), (504, 256))}

for slug, title, raw, dirs, polygon in specs:
    scene = cut(load(O / 'bruts' / f'{raw}.png').resize(SIZE, Image.Resampling.NEAREST))
    a = np.array(scene)
    opaque = a[:, :, 3] > 0
    fm = poly(polygon) & opaque
    other = opaque & ~fm
    masks = {'01_sol_chemin': fm,
             '02_vegetation_fond': other & (yy < 200),
             '03_massif_gauche': other & (yy >= 200) & (xx < 256) & (yy < 400),
             '04_massif_droit': other & (yy >= 200) & (xx >= 256) & (yy < 400),
             '05_vegetation_premier_plan': other & (yy >= 400)}
    layers = {n: part(scene, m) for n, m in masks.items()}
    entries = []
    for d in dirs:
        arr = stripe if d == 'N' else stripe[::-1] if d == 'S' else np.transpose(stripe, (1, 0, 2)) if d == 'W' else np.transpose(stripe, (1, 0, 2))[:, ::-1]
        pos, point = portspec[d]
        port = Image.new('RGBA', SIZE)
        port.alpha_composite(Image.fromarray(arr.copy()), pos)
        layers['06_acces_' + d] = port
        entries.append({'direction': d, 'xy': list(point), 'width': 64, 'layer': '06_acces_' + d + '.png'})
    out = O / slug
    out.mkdir(exist_ok=True)
    for n, im in layers.items():
        save(im, out / (n + '.png'))
    recomposed = Image.new('RGBA', SIZE)
    for n in masks:
        recomposed.alpha_composite(layers[n])
    assert np.array_equal(np.array(recomposed), a), slug
    comp = recomposed.copy()
    for n, im in layers.items():
        if n.startswith('06'):
            comp.alpha_composite(im)
    save(comp, out / 'composition.png')
    save(scene, out / 'terrain_detoure.png')
    schema = Image.new('RGB', SIZE, '#1d3320')
    sd = ImageDraw.Draw(schema)
    sd.polygon(polygon, fill='#7fae4e')
    for e in entries:
        x, y = e['xy']
        sd.ellipse((x - 13, y - 13, x + 13, y + 13), fill='#e8f3c8')
        sd.text((max(5, x - 4), max(20, min(482, y - 5))), e['direction'], fill='black')
    sd.text((12, 12), title, fill='white')
    save(schema, out / 'schema.png')
    arr = np.array(comp)
    for d in dirs:
        band = arr[0:OPAQUE_DEPTH, 224:288] if d == 'N' else arr[-OPAQUE_DEPTH:, 224:288] if d == 'S' else arr[224:288, 0:OPAQUE_DEPTH] if d == 'W' else arr[224:288, -OPAQUE_DEPTH:]
        assert np.all(band[:, :, 3] == 255), (slug, d, 'opaque band')
        edge = band[0] if d in 'NS' else band[:, 0]
        if d == 'N':
            assert np.array_equal(edge, p[0]), (slug, d, 'shared connector')
    manifest['rooms'].append({'id': slug, 'title': title, 'raw': raw + '.png',
                              'ports': entries, 'layers': list(layers), 'optional': [],
                              'checks': {'partitions_exact': True, 'ports_opaque_band': True}})

(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1200, 840), '#1d3320')
d = ImageDraw.Draw(board)
for i, e in enumerate(manifest['rooms']):
    im = load(O / e['id'] / 'composition.png').resize((392, 392), Image.Resampling.NEAREST)
    x, y = i % 3 * 400, i // 3 * 420
    board.paste(im, (x, y + 24), im)
    d.text((x + 8, y + 5), e['title'], fill='white')
save(board, O / 'PLANCHE.png')
nports = sum(len(e['ports']) for e in manifest['rooms'])
print(f'6 rooms; exact terrain partitions; {nports} opaque-64px matching ports (band {OPAQUE_DEPTH}px); native grass connector')
