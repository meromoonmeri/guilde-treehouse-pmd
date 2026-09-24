"""Sommet Sky Peak de nuit — vista multicouche 960x600.

- Prairie d'avant-plan : pixels NATIFS du GIF Sky Peak (bande basse,
  miroir documente pour 960), fleurs retirees/reanimees separement.
- Nuit : filtre Abyss etabli (canonique v1) sur prairie/fleurs.
- Fleurs : groupes natifs extraits des 4 frames, repositionnes, natifs + nuit.
- Etoiles : 64 phases ref_v2 reutilisees a l'octet.
- Panorama/foret/montagnes + nuages : generations guidees (zero entite),
  magenta detoure, split foret/montagnes, wraps à marges transparentes.
- Brume : procedeural, carrelage miroir garanti seamless.
"""
from pathlib import Path
import sys, json, io, hashlib, shutil
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageFilter
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/sommet_sky_nuit_v1'
P = O / 'sommet_nuit'
P.mkdir(parents=True, exist_ok=True)
(SP := P / 'sprites').mkdir(exist_ok=True)
W, H = 960, 600
NN = Image.Resampling.NEAREST

def load(p): return Image.open(p).convert('RGBA')
def sha(b): return hashlib.sha256(b).hexdigest()

# ---------- magenta key + defringe ----------
def key(im):
    a = np.array(im)
    r, g, b = (a[:, :, i].astype(int) for i in range(3))
    strong = (r > 35) & (b > 35) & (r > g * 1.8) & (b > g * 1.8)
    a[strong] = 0
    # frange: teinte magenta adjacente au transparent
    tr = a[:, :, 3] == 0
    edge = nd.binary_dilation(tr, iterations=1) & ~tr
    fringe = edge & (r > 90) & (b > 90) & (r > g * 1.35) & (b > g * 1.35)
    a[fringe] = 0
    return Image.fromarray(a)

# ---------- 1. PRAIRIE CANONIQUE ----------
refs = [np.array(load(R / f'source/sky_peak_v1/gif_{i}.png')) for i in range(4)]
petals = []
for fr in refs:
    r, g, b = (fr[:, :, i].astype(float) for i in range(3))
    petals.append((r > 190) & (r > g * 1.04) & (r > b * 1.08))
union = np.logical_or.reduce(petals)
clean = refs[0].copy()
need = union.copy()
for i, fr in enumerate(refs):
    fill = need & (~petals[i])
    clean[fill] = fr[fill]
    need &= petals[i]
gr = clean[:, :, 1].astype(float); rr = clean[:, :, 0].astype(float); bb = clean[:, :, 2].astype(float)
grass_all = (gr > rr * 1.05) & (gr > bb * 1.05)
native_green = np.median(clean[grass_all & ~union][:, :3], axis=0).astype('uint8')
clean[need] = (*native_green, 255)
YB0, YB1 = 328, 504  # bande 504x176 -> y 424..600
band = clean[YB0:YB1]  # day, sans fleurs
mir = np.concatenate([band[:, 0:228][:, ::-1], band, band[:, 503:275:-1]], axis=1)
assert mir.shape[1] == 960
day_meadow = Image.fromarray(mir)
day_meadow.save(O / 'controle_bande_prairie_jour.png')
night_meadow = night(day_meadow)
gm = mir[:, :, 1].astype(float); rm = mir[:, :, 0].astype(float); bm = mir[:, :, 2].astype(float)
grass_m = (gm > rm * 1.05) & (gm > bm * 1.05)
nm = np.array(night_meadow)
prairie = nm.copy(); prairie[~grass_m] = 0
reliefs = nm.copy(); reliefs[grass_m] = 0
L08 = Image.new('RGBA', (W, H)); L08.alpha_composite(Image.fromarray(prairie), (0, 424))
L09 = Image.new('RGBA', (W, H)); L09.alpha_composite(Image.fromarray(reliefs), (0, 424))
L08.save(P / 'sky_08_prairie.png'); L09.save(P / 'sky_09_reliefs.png')

# ---------- 2. FLEURS CANONIQUES ----------
lab, nlab = nd.label(union, np.ones((3, 3)))
cands = []
for k, sl in enumerate(nd.find_objects(lab), 1):
    if sl is None: continue
    gy, gx = sl; h, w = gy.stop - gy.start, gx.stop - gx.start
    if not (7 <= w <= 30 and 7 <= h <= 28): continue
    if gx.start < 2 or gy.stop > 502: continue
    mask = lab == k
    ims = []
    for i, fr in enumerate(refs):
        vis = nd.binary_fill_holes(petals[i] & mask)
        out = fr[gy, gx].copy(); out[~vis[gy, gx]] = 0
        ims.append(Image.fromarray(out))
    def pngb(im):
        q = io.BytesIO(); im.save(q, format='PNG'); return q.getvalue()
    if len({pngb(im) for im in ims}) < 3: continue
    cands.append({'bbox': [gx.start, gy.start, gx.stop, gy.stop], 'images': ims})
assert len(cands) >= 8, len(cands)
flowers = cands[::max(1, len(cands) // 10)][:10]
for k, f in enumerate(flowers):
    for i, im in enumerate(f['images']):
        im.save(SP / f'fleur_native_{k:02}_phase_{i}.png')
# sites sur herbe (jour), 2 groupes de profondeur
gfull = np.zeros((H, W), bool); gfull[424:600] = grass_m
yy, xx = np.mgrid[:H, :W]
rng = np.random.default_rng(7)
order = rng.permutation(((yy - 515) ** 2 + (xx - 480) ** 2).size)
sites = []
for idx in order:
    y, x = int(idx // W), int(idx % W)
    if not (436 <= y <= 592 and 8 <= x <= 952): continue
    if any((x - s['center'][0]) ** 2 + (y - s['center'][1]) ** 2 < 26 ** 2 for s in sites): continue
    k = len(sites) % len(flowers)
    fw, fh = flowers[k]['images'][0].size
    tx, ty = x - fw // 2, y - fh
    if tx < 0 or ty < 424 or tx + fw > W or ty + fh > H: continue
    if not gfull[y - 2, x]: continue
    sites.append({'center': [x, y], 'origin': [tx, ty], 'sprite': k, 'phase_offset': len(sites) % 4})
    if len(sites) == 34: break
assert len(sites) >= 20, len(sites)
groups = {'loin': [s for s in sites if s['center'][1] < 515], 'proche': [s for s in sites if s['center'][1] >= 515]}
flayers = {}
for gname, gsites in groups.items():
    for variant in ('native', 'nuit'):
        for ph in range(4):
            im = Image.new('RGBA', (W, H))
            for s in gsites:
                im.alpha_composite(flowers[s['sprite']]['images'][(ph + s['phase_offset']) % 4], tuple(s['origin']))
            if variant == 'nuit':
                im = night(im)
            flayers[(gname, variant, ph)] = im
            im.save(P / f'sky_{"10" if gname == "loin" else "11"}_fleurs_{gname}_{variant}_ph{ph}.png')

# ---------- 3. CIEL (degrade echantillonne nuit canonique) ----------
top = np.array([8, 17, 49]); bot = np.array([54, 74, 122])
u = np.clip(np.arange(H) / 200, 0, 1)[:, None, None]
sky = np.zeros((H, W, 4), 'uint8'); sky[:, :, :3] = top * (1 - u) + bot * u; sky[:, :, 3] = 255
L01 = Image.fromarray(sky); L01.save(P / 'sky_01_ciel.png')

# ---------- 4. ETOILES (ref_v2, octets conserves) ----------
SDIR = R / 'renders/references_calques_v2/etoiles'
star_files = sorted(SDIR.glob('*.png'))
assert len(star_files) == 64, len(star_files)
(PS := P / 'etoiles').mkdir(exist_ok=True)
star_hash = []
for f in star_files:
    b = f.read_bytes()
    assert Image.open(io.BytesIO(b)).size == (W, H)
    (PS / f.name).write_bytes(b)
    star_hash.append(sha(b))
L02 = load(PS / '00.png')

# ---------- 5. PANORAMA : montagnes / foret ----------
pano = key(load(O / 'bruts/panorama.png'))
pw, ph = pano.size
nh = round(ph * W / pw)
pano = pano.resize((W, nh), NN)
pa = np.array(pano)
opaque = pa[:, :, 3] > 0
r, g, b = (pa[:, :, i].astype(int) for i in range(3))
is_forest = opaque & (g >= b) & (b < 170)
treeline = np.full(W, nh)
for x in range(W):
    col = np.flatnonzero(is_forest[:, x])
    if len(col):
        treeline[x] = int(np.median(col[col > 40][:8])) if (col > 40).any() else int(col[0])
treeline = nd.median_filter(treeline, size=25)
treeline = np.clip(treeline, 300 * nh // 672, 400 * nh // 672)
Y0 = 63  # placement pano : y 63..63+nh
m_mask = np.zeros((nh, W), bool); f_mask = np.zeros((nh, W), bool)
for x in range(W):
    t = int(treeline[x])
    m_mask[:t, x] = True; f_mask[t:, x] = True
m_arr = pa.copy(); m_arr[~m_mask] = 0
f_arr = pa.copy(); f_arr[~f_mask] = 0
L04 = Image.new('RGBA', (W, H)); L04.alpha_composite(Image.fromarray(m_arr), (0, Y0))
L06 = Image.new('RGBA', (W, H)); L06.alpha_composite(Image.fromarray(f_arr), (0, Y0))
L04.save(P / 'sky_04_montagnes.png'); L06.save(P / 'sky_06_foret.png')
Image.fromarray((np.stack([treeline] * 20, 0).astype('uint8') * 0 + 255)).save(O / 'controle_treeline.png')

# ---------- 6. NUAGES : 2 wraps a marges transparentes ----------
sheet = np.array(key(load(O / 'bruts/nuages.png')))
lab, nlab = nd.label(sheet[:, :, 3] > 0, np.ones((3, 3)))
puffs = []
for k, sl in enumerate(nd.find_objects(lab), 1):
    if sl is None: continue
    gy, gx = sl; h, w = gy.stop - gy.start, gx.stop - gx.start
    if w * h < 800: continue
    puffs.append(Image.fromarray(sheet[gy, gx]))
puffs.sort(key=lambda im: im.height)
far_p = [p for p in puffs if p.height < 110]
near_p = [p for p in puffs if p.height >= 110]
print('puffs: far', len(far_p), 'near', len(near_p), [p.size for p in puffs])
assert len(far_p) >= 4 and len(near_p) >= 3
def strip(spec, band_y):
    st = Image.new('RGBA', (W, H))
    for img, tw, x, y in spec:
        w2 = tw; h2 = round(img.height * tw / img.width)
        st.alpha_composite(img.resize((w2, h2), NN), (x, y))
    return st
far_spec = [(far_p[i % len(far_p)], w, x, 66 + (i % 2) * 26) for i, (x, w) in
            enumerate([(40, 150), (225, 160), (410, 150), (595, 160), (770, 150)])]
near_spec = [(near_p[i % len(near_p)], w, x, 240 + (i % 2) * 16) for i, (x, w) in
             enumerate([(130, 180), (430, 190), (710, 180)])]
S_far, S_near = strip(far_spec, None), strip(near_spec, None)
for name, st in (('far', S_far), ('near', S_near)):
    a = np.array(st)
    assert not a[:, :32, 3].any() and not a[:, -32:, 3].any(), name
S_far.save(P / 'sky_03_nuages_lointains_wrap.png')
S_near.save(P / 'sky_05_nuages_proches_wrap.png')
def phases(st, n, out):
    arr = np.array(st)
    outs = []
    for i in range(n):
        sh = i * W // n
        outs.append(Image.fromarray(np.roll(arr, -sh, axis=1)))
    gn = (P / out); gn.mkdir(exist_ok=True)
    for i, im in enumerate(outs):
        im.save(gn / f'ph{i:02}.png')
    return outs
ph_far = phases(S_far, 32, 'nuages_lointains_phases')
ph_near = phases(S_near, 24, 'nuages_proches_phases')

# ---------- 7. BRUME (procedural, miroir seamless) ----------
mrng = np.random.default_rng(21)
half = mrng.random((120, W // 2)).astype('float32')
half = np.array(Image.fromarray((half * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(9))).astype(float) / 255
full = np.concatenate([half, half[:, ::-1]], axis=1)
band_m = np.zeros((H, W, 4), 'uint8')
yy = np.linspace(0, 1, 120)[:, None]
env = np.sin(np.pi * np.clip(yy, 0, 1)) ** 0.7
alpha = (full * env * 64).astype('uint8')
band_m[350:470, :, 0] = 150; band_m[350:470, :, 1] = 180; band_m[350:470, :, 2] = 230
band_m[350:470, :, 3] = alpha
S_mist = Image.fromarray(band_m)
S_mist.save(P / 'sky_07_brume_wrap.png')
ph_mist = phases(S_mist, 16, 'brume_phases')

# ---------- 8. COMPOSITIONS + WEBP + ORA ----------
order = [('01_ciel', L01), ('02_etoiles', L02), ('03_nuages_lointains', S_far), ('04_montagnes', L04),
         ('06_foret', L06), ('05_nuages_proches', S_near), ('07_brume', S_mist), ('08_prairie', L08),
         ('09_reliefs', L09), ('10_fleurs_loin_nuit', flayers[('loin', 'nuit', 0)]),
         ('11_fleurs_proche_nuit', flayers[('proche', 'nuit', 0)])]
def compose(layers):
    c = Image.new('RGBA', (W, H))
    for _, im in layers:
        c.alpha_composite(im)
    return c
comp0 = compose(order)
comp0.save(P / 'COMPOSITION.png')
static = [l for l in order if not l[0].startswith(('02_', '10_', '11_'))]
frames = []
for f in range(8):
    fl = static + [(f'02_etoiles_ph{f*8}', load(PS / f'{f*8:02}.png')),
                   ('10', flayers[('loin', 'nuit', (f // 2) % 4)]),
                   ('11', flayers[('proche', 'nuit', (f // 2) % 4)])]
    frames.append(compose(fl))
frames[0].save(P / 'ANIMATION_FLORA_STELLA.webp', save_all=True, append_images=frames[1:], duration=100, loop=0, lossless=True)
# ORA (natifs masques)
import zipfile, xml.etree.ElementTree as ET
def pngb(im):
    q = io.BytesIO(); im.save(q, format='PNG'); return q.getvalue()
ora_layers = order + [('10_fleurs_loin_native', flayers[('loin', 'native', 0)]), ('11_fleurs_proche_native', flayers[('proche', 'native', 0)])]
root = ET.Element('image', w=str(W), h=str(H)); stack = ET.SubElement(root, 'stack')
for name, _ in reversed(ora_layers):
    attrs = {'name': name, 'src': f'data/{name}.png'}
    if name.endswith('native'):
        attrs['visibility'] = 'hidden'
    ET.SubElement(stack, 'layer', **attrs)
with zipfile.ZipFile(P / 'sommet_nuit.ora', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
    z.writestr('stack.xml', ET.tostring(root))
    z.writestr('mergedimage.png', pngb(comp0))
    for name, im in ora_layers:
        z.writestr(f'data/{name}.png', pngb(im))

# ---------- 9. MANIFESTE ----------
manifest = {
    'titre': 'Sommet Sky Peak de nuit — vista multicouche',
    'taille': [W, H], 'grille_px': 8,
    'prairie_canonique': {'source': 'source/sky_peak_v1/gif_0..3.png (504x504)', 'bande_native': [0, YB0, 504, YB1],
                          'miroir': 'cols [227..0]+[0..503]+[503..276] -> 960, coutures a x=228/732',
                          'fleurs_retirees': int(union[YB0:YB1].sum()), 'vert_complement_median': native_green.tolist(),
                          'nuit': 'filtre Abyss source/cote_v4_abyss/night.py (pipeline canonique v1)'},
    'fleurs': {'sprites_natifs': len(flowers), 'sites': len(sites), 'groupes': {k: len(v) for k, v in groups.items()},
               'phases': 4, 'phase_ms': 200, 'boucle_ms': 800, 'variantes': ['native', 'nuit'],
               'sprites': [{'bbox': f['bbox']} for f in flowers], 'sites_detail': sites},
    'etoiles': {'source': 'renders/references_calques_v2/etoiles (64 phases)', 'phase_ms': 80, 'boucle_ms': 5120,
                'hashes': star_hash},
    'ciel': {'haut': top.tolist(), 'bas': bot.tolist(), 'source_couleurs': 'renders/sky_peak_canonique_v1/nuit/01_ciel.png'},
    'panorama_genere': {'brut': 'bruts/panorama.png (1584x672, zero entite)', 'placement_y': Y0, 'hauteur_redim': nh,
                        'split': 'treeline par colonne, mediane glissante 25, borne [300,400]*nh/672'},
    'wraps': {'far': {'phases': 32, 'pas_px': W // 32, 'phase_ms': 100, 'vitesse_pmdo_px_s': -4},
              'near': {'phases': 24, 'pas_px': W // 24, 'phase_ms': 100, 'vitesse_pmdo_px_s': -8},
              'brume': {'phases': 16, 'pas_px': W // 16, 'phase_ms': 150, 'vitesse_pmdo_px_s': -3},
              'marges_transparentes_px': 32, 'periode_px': W,
              'mode_pmdo': '2 copies a x et x+960, x=-floor(t*v) mod 960'},
    'limites': ['Panorama et nuages generes (DA Sky), pas des tuiles natives',
                'Prairie/fleurs natives + filtre nuit Abyss (pipeline canonique v1)',
                'WebP = fleurs+etoiles echantillonnees, nuages fixes ; galerie anime tout en continu',
                'Pas de test PMDO/GPU, collisions, transitions'],
}
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
# planche de presentation (NE PAS IMPORTER)
from PIL import ImageDraw
board = Image.new('RGB', (980, 300 + 26 + 240 + 16), '#101a24')
dr = ImageDraw.Draw(board)
dr.text((14, 8), 'SOMMET SKY NUIT v1 — 960x600, prairie/fleurs natives + nuit Abyss', fill='#e6d493')
dr.text((14, 28), 'panorama/nuages generes zero-entite · etoiles ref_v2 64ph · wraps seamless', fill='#9db3a1')
board.paste(comp0.resize((480, 300), NN), (14, 52))
board.paste(comp0.crop((148, 424, 308, 544)).resize((320, 240), NN), (506, 52 + 30))
board.paste(comp0.crop((380, 230, 700, 350)).resize((320, 120), NN), (506, 52 + 30 + 240 + 8 - 120))
dr.text((506, 52 + 12), 'prairie native 2x', fill='#a3dae3')
board.save(O / 'PLANCHE_VISTA_NE_PAS_IMPORTER.png')
print('OK prairie native, fleurs', len(flowers), 'sprites /', len(sites), 'sites, pano', (W, nh), 'treeline', int(treeline.min()), int(treeline.max()))
