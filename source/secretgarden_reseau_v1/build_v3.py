"""Secret Garden network V3: per-zone multilayer sol/chemin/arbres/buissons/rochers/fleurs/jungle/acces.

V3 scheme per room: 01_sol, 02_chemin (geometric center band of the path polygon),
03_arbres (light canopy + trunks, all depths), 04_buissons (dark undergrowth),
05_rochers, 06_fleurs (+4 anim frames 200ms), 07_bordure_jungle (Southern Jungle
style frame, port windows cleared by script), 08_acces_X per port.
Partitions 01..06 disjoint and == cut terrain exactly. Border/ports are extras.
"""
from pathlib import Path
import json, hashlib, shutil, zipfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
REF = R / 'secretgarden.png'
JUNGLE_REF = R / 'Southern_Jungle_entrance_S.png'
SIZE = (512, 512)
PATCH_BOX = (190, 240, 222, 272)
OPAQUE_DEPTH = 24
STRIP_DEPTH = 32
WIN_W, WIN_D = 104, 88
CHEMIN_ERODE = 15


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
    ('couloir_ns', 'Couloir nord-sud fleuri', 'couloir_ns', 'brut_ns', ['N', 'S'],
     [(221, 0), (288, 0), (288, 106), (407, 121), (406, 425), (325, 452), (325, 512), (191, 512), (191, 449), (93, 425), (93, 124), (221, 106)]),
    ('couloir_ew', 'Couloir est-ouest fleuri', 'couloir_ew', 'brut_ew', ['E', 'W'],
     [(0, 216), (73, 192), (439, 192), (512, 216), (512, 332), (433, 370), (80, 370), (0, 332)]),
    ('couloir_t', 'Jonction en T', 'couloir_t', 'brut_t', ['N', 'E', 'W'],
     [(210, 0), (300, 0), (300, 122), (359, 170), (413, 200), (512, 200), (512, 340), (389, 340), (321, 436), (219, 436), (120, 340), (0, 340), (0, 200), (135, 200), (171, 170), (210, 122)]),
    ('salle_traversee', 'Salle traversante', 'salle_traversee', 'brut_traversee', ['N', 'S'],
     [(224, 0), (288, 0), (288, 149), (381, 174), (435, 262), (428, 355), (324, 445), (324, 512), (192, 512), (192, 445), (90, 355), (81, 262), (129, 174), (224, 149)]),
    ('salle_laterale', 'Salle laterale', 'salle_laterale', 'brut_laterale', ['W', 'S'],
     [(103, 184), (381, 184), (454, 263), (446, 351), (324, 449), (324, 512), (192, 512), (192, 445), (75, 355), (0, 312), (0, 236), (75, 236)]),
    ('salle_carrefour', 'Salle carrefour', 'salle_carrefour', 'brut_carrefour', ['N', 'S', 'E', 'W'],
     [(224, 0), (288, 0), (288, 135), (381, 168), (423, 230), (512, 230), (512, 298), (423, 298), (388, 361), (322, 444), (322, 512), (190, 512), (190, 444), (121, 361), (82, 298), (0, 298), (0, 230), (82, 230), (130, 168), (224, 135)]),
    ('carrefour_clairiere', 'Carrefour de la clairiere', 'carrefour_clairiere', 'brut_clairiere', ['N', 'S', 'E', 'W'],
     [(224, 0), (288, 0), (288, 135), (381, 168), (423, 230), (512, 230), (512, 298), (423, 298), (388, 361), (322, 444), (322, 512), (190, 512), (190, 444), (121, 361), (82, 298), (0, 298), (0, 230), (82, 230), (130, 168), (224, 135)]),
]

ref_sha = hashlib.sha256(REF.read_bytes()).hexdigest()
jungle_sha = hashlib.sha256(JUNGLE_REF.read_bytes()).hexdigest()
patch = load(REF).crop(PATCH_BOX)
save(patch, O / 'materiaux/sol_raccord_natif.png')
p = np.array(patch.resize((64, 64), Image.Resampling.NEAREST))
fade = np.array([255] * OPAQUE_DEPTH + [round(255 * (31 - y) / 8) for y in range(OPAQUE_DEPTH, 32)], dtype='uint8')
stripe = p[:32].copy()
stripe[:, :, 3] = np.minimum(stripe[:, :, 3], fade[:, None])

manifest = {'reference': 'secretgarden.png (user commit)', 'version': 3,
            'reference_sha256': ref_sha, 'jungle_reference': 'Southern_Jungle_entrance_S.png',
            'jungle_reference_sha256': jungle_sha, 'patch_box': list(PATCH_BOX),
            'size': list(SIZE), 'port_width': 64,
            'opaque_depth': OPAQUE_DEPTH, 'strip_depth': STRIP_DEPTH,
            'chemin': {'method': 'geometric center band: binary erosion of path polygon, 15px', 'note': 'sol = verges of the polygon, chemin = main track; both from generated pixels, exact partition'},
            'flowers': {'frames': 4, 'frame_ms': 200, 'loop_ms': 800,
                        'motion': 'sway dx=[0,+1,0,-1]px, brightness=[1.00,1.06,1.00,0.94]',
                        'note': 'new animation in Sky Peak cadence, not a recovered native cycle'},
            'runtime_validated': False, 'rooms': []}
portspec = {'N': ((224, 0), (256, 8)), 'S': ((224, 480), (256, 504)),
            'W': ((0, 224), (8, 256)), 'E': ((480, 224), (504, 256))}


def border_layer(raw_border, dirs):
    im = load(O / 'bordures_jungle' / f'{raw_border}.png')
    w, h = im.size
    if w != h:
        s = max(w, h)
        sq = Image.new('RGBA', (s, s), (255, 0, 255, 255))
        sq.alpha_composite(im, ((s - w) // 2, (s - h) // 2))
        im = sq
    b = cut(im.resize(SIZE, Image.Resampling.NEAREST))
    a = np.array(b)
    cx0, cx1 = 256 - WIN_W // 2, 256 + WIN_W // 2
    if 'N' in dirs:
        a[0:WIN_D, cx0:cx1] = 0
    if 'S' in dirs:
        a[512 - WIN_D:512, cx0:cx1] = 0
    if 'W' in dirs:
        a[cx0:cx1, 0:WIN_D] = 0
    if 'E' in dirs:
        a[cx0:cx1, 512 - WIN_D:512] = 0
    return Image.fromarray(a)


def flower_frames(f0):
    a = np.array(f0)
    out = []
    for dx, br in [(0, 1.0), (1, 1.06), (0, 1.0), (-1, 0.94)]:
        f = a.copy()
        if dx > 0:
            f[:, dx:] = a[:, :-dx]
            f[:, :dx] = 0
        elif dx < 0:
            f[:, :dx] = a[:, -dx:]
            f[:, dx:] = 0
        rgb = np.clip(f[:, :, :3].astype(float) * br, 0, 255).astype('uint8')
        f[:, :, :3] = rgb
        out.append(Image.fromarray(f))
    return out


for slug, title, raw, raw_border, dirs, polygon in specs:
    out = O / slug
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    scene = cut(load(O / 'bruts' / f'{raw}.png').resize(SIZE, Image.Resampling.NEAREST))
    a = np.array(scene)
    R_, G_, B_ = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    opaque = a[:, :, 3] > 0
    pathpoly = poly(polygon)
    flowers = opaque & (((R_ > 200) & (G_ > 180) & (B_ > 150)) |
                        ((R_ > 200) & (G_ > 170) & (B_ < 140)) |
                        ((R_ > 190) & (G_ < 175) & (B_ > 130)))
    brown = opaque & ~flowers & (R_ > B_ + 15) & (R_ > 90) & (R_ < 220) & (G_ < R_) & (G_ > 30)
    lab, n = ndimage.label(brown)
    sizes = ndimage.sum(brown, lab, range(1, n + 1)) if n else []
    near_path = ndimage.binary_dilation(pathpoly, iterations=12)
    rocks = np.zeros_like(opaque)
    for i, s in enumerate(sizes, 1):
        comp = lab == i
        if s > 120 or (comp & near_path).any():
            rocks |= comp
    rocks &= brown
    trunks = brown & ~rocks
    rest = opaque & ~flowers & ~brown
    ground = pathpoly & rest
    center = ndimage.binary_erosion(pathpoly, iterations=CHEMIN_ERODE) & rest
    assert center.any(), (slug, 'empty chemin')
    sol = ground & ~center
    veg = rest & ~ground
    arbres = (veg & (G_ >= 115)) | trunks
    buissons = veg & (G_ < 115)
    masks = {'01_sol': sol, '02_chemin': center, '03_arbres': arbres,
             '04_buissons': buissons, '05_rochers': rocks, '06_fleurs': flowers}
    layers = {n: part(scene, m) for n, m in masks.items()}
    frames = flower_frames(layers['06_fleurs'])
    fdir = out / 'fleurs'
    for i, f in enumerate(frames):
        save(f, fdir / f'06_fleurs_f{i}.png')
    layers['07_bordure_jungle'] = border_layer(raw_border, dirs)
    entries = []
    for d in dirs:
        arr = stripe if d == 'N' else stripe[::-1] if d == 'S' else np.transpose(stripe, (1, 0, 2)) if d == 'W' else np.transpose(stripe, (1, 0, 2))[:, ::-1]
        pos, point = portspec[d]
        port = Image.new('RGBA', SIZE)
        port.alpha_composite(Image.fromarray(arr.copy()), pos)
        layers['08_acces_' + d] = port
        entries.append({'direction': d, 'xy': list(point), 'width': 64, 'layer': '08_acces_' + d + '.png'})
    for n, im in layers.items():
        save(im, out / (n + '.png'))
    recomposed = Image.new('RGBA', SIZE)
    for n in masks:
        recomposed.alpha_composite(layers[n])
    assert np.array_equal(np.array(recomposed), a), slug
    base = recomposed.copy()
    base.alpha_composite(layers['07_bordure_jungle'])
    for n, im in layers.items():
        if n.startswith('08_acces'):
            base.alpha_composite(im)
    save(base, out / 'composition.png')
    save(scene, out / 'terrain_detoure.png')
    still = Image.new('RGBA', SIZE)
    for n in ['01_sol', '02_chemin', '03_arbres', '04_buissons', '05_rochers']:
        still.alpha_composite(layers[n])
    still.alpha_composite(layers['07_bordure_jungle'])
    for n, im in layers.items():
        if n.startswith('08_acces'):
            still.alpha_composite(im)
    gif_frames = []
    for f in frames:
        c = still.copy()
        c.alpha_composite(f)
        gif_frames.append(c.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))
    gif_frames[0].save(out / 'composition_animee.gif', save_all=True, append_images=gif_frames[1:],
                       duration=200, loop=0)
    ora_path = out / (slug + '.ora')
    order = ['01_sol', '02_chemin', '03_arbres', '04_buissons', '05_rochers', '06_fleurs',
             '07_bordure_jungle'] + ['08_acces_' + d for d in dirs]
    stack = ''.join(f'<layer name="{n}" src="data/{n}.png" x="0" y="0"/>' for n in order)
    stack_xml = f'<?xml version="1.0"?><image w="512" h="512"><stack name="root">{stack}</stack></image>'
    with zipfile.ZipFile(ora_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster')
        z.writestr('stack.xml', stack_xml)
        for n in order:
            z.write(out / (n + '.png'), f'data/{n}.png')
        z.write(out / 'composition.png', 'merged.png')
    schema = Image.new('RGB', SIZE, '#1d3320')
    sd = ImageDraw.Draw(schema)
    sd.polygon(polygon, fill='#7fae4e')
    sd.polygon(polygon, outline='#e8f3c8')
    for e in entries:
        x, y = e['xy']
        sd.ellipse((x - 13, y - 13, x + 13, y + 13), fill='#e8f3c8')
        sd.text((max(5, x - 4), max(20, min(482, y - 5))), e['direction'], fill='black')
    sd.text((12, 12), title, fill='white')
    save(schema, out / 'schema.png')
    arr = np.array(base)
    for d in dirs:
        band = arr[0:OPAQUE_DEPTH, 224:288] if d == 'N' else arr[-OPAQUE_DEPTH:, 224:288] if d == 'S' else arr[224:288, 0:OPAQUE_DEPTH] if d == 'W' else arr[224:288, -OPAQUE_DEPTH:]
        assert np.all(band[:, :, 3] == 255), (slug, d, 'opaque band')
    manifest['rooms'].append({'id': slug, 'title': title, 'raw': raw + '.png',
                              'border': 'bordures_jungle/' + raw_border + '.png', 'ports': entries,
                              'layers': list(layers), 'optional': [],
                              'flower_px': int(flowers.sum()), 'chemin_px': int(center.sum()),
                              'checks': {'partitions_exact': True, 'ports_opaque_band': True}})

(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
board = Image.new('RGB', (1400, 840), '#1d3320')
d = ImageDraw.Draw(board)
for i, e in enumerate(manifest['rooms']):
    im = load(O / e['id'] / 'composition.png').resize((336, 336), Image.Resampling.NEAREST)
    x, y = (i % 4) * 350, (i // 4) * 420
    board.paste(im, (x, y + 24), im)
    d.text((x + 8, y + 5), e['title'], fill='white')
save(board, O / 'PLANCHE.png')
nports = sum(len(e['ports']) for e in manifest['rooms'])
nlayers = sum(len(e['layers']) for e in manifest['rooms'])
print(f'V3: 7 rooms; {nlayers} layers; {nports} ports; sol/chemin/arbres/buissons/rochers/fleurs/jungle/acces')
