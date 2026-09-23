# -*- coding: utf-8 -*-
"""V4 = corrections sur la base V3 (layout conservé) :
  - paroi rocheuse élargie vers le bas/jusqu'aux coins du cadre (fin de l'effet « île dans le ciel »),
    en réutilisant les strates natives de la paroi (même palette, aucun collage étranger),
  - ciel re-dessiné plus riche (dégradé plus profond et lueur d'horizon plus lumineuse),
  - nuages remplacés par 6 formes variées (générées, découpées sur magenta) : bande lointaine + overlay + accents fixes,
  - brume basse ajoutée DEVANT le pied de la paroi.
Réutilise à l'identique : étoiles, filantes, lune, panorama, brume, plateau, herbe (layout de base V3).
Tous les pixels dessinés/générés, aucun natif certifié. Pas de test PMDO.
"""
from pathlib import Path
import json, io, zipfile, math, hashlib
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage
from PIL import Image, _webp

R = Path(__file__).resolve().parents[2]
O = R/'renders/sky_peak_prairie_v1'
V3 = O/'v3'
V  = O/'v4'
P3 = 'SkyPeakPrairieV3'
P  = 'SkyPeakPrairieV4'
W, H = 960, 864
SKY_H = 470
FULL = '--full' in __import__('sys').argv
sys = __import__('sys'); sys.path.insert(0, str(R/'source/cote_v4_abyss')); from night import night

def png(im):
    b = io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()
def L3(name):
    return Image.open(V3/'calques'/f'{P3}_{name}.png').convert('RGBA')

(V/'calques').mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20260922)

# ---------- 01 sky : gradient plus riche (couleurs issues du brut ciel généré), Bayer 4x4 ----------
yy, xx = np.mgrid[:H, :W].astype(float)
t = np.clip(yy/(H-1), 0, 1)
stops = [(0.00,(12,5,52)), (0.28,(17,9,64)), (0.52,(56,84,166)), (0.74,(118,168,204)), (0.90,(168,214,224)), (1.00,(196,228,232))]
def ramp(t):
    out = np.zeros((*t.shape, 3))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1); u = ((t-t0)/(t1-t0))[m]; u = u*u*(3-2*u)
        out[m] = np.array(c0)*(1-u[:,None]) + np.array(c1)*u[:,None]
    return out
rgb = ramp(t)
mx, my = 716+64, 48+64
glow = np.exp(-(((xx-mx)/210)**2 + ((yy-my)/160)**2))[:, :, None]*np.array([14,18,30])
rgb += glow
bayer = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])/16 - 0.5
rgb += bayer[np.arange(H)[:,None] % 4, np.arange(W)[None,:] % 4][:, :, None]*1.0
sky = Image.fromarray(np.dstack([np.clip(np.rint(rgb),0,255).astype('uint8'), np.full((H,W),255,'uint8')]))
sky.save(V/'calques'/f'{P}_01_ciel_profond.png')

# ---------- 02 étoiles & 02b filantes : réutilisées à l'identique (layout de base) ----------
star_frames = [Image.open(V3/'etoiles_frames'/f'{P3}_etoiles_{i:02d}.png').convert('RGBA') for i in range(64)]
meteor_frames = [Image.open(V3/'etoiles_filantes_frames'/f'{P3}_filante_{i:03d}.png').convert('RGBA') for i in range(360)]
(V/'etoiles_frames').mkdir(exist_ok=True); (V/'etoiles_filantes_frames').mkdir(exist_ok=True)
for i, f in enumerate(star_frames): f.save(V/'etoiles_frames'/f'{P}_etoiles_{i:02d}.png')
for i, f in enumerate(meteor_frames): f.save(V/'etoiles_filantes_frames'/f'{P}_filante_{i:03d}.png')
star_frames[0].save(V/'calques'/f'{P}_02_etoiles_phase0.png')
Image.new('RGBA',(W,H)).save(V/'calques'/f'{P}_02b_etoiles_filantes_vide.png')

# ---------- nuages variés : découpe du sheet généré (6 formes) ----------
sheet = np.array(Image.open(R/'source/sky_peak_prairie_v1/gen_v4/raw_nuages_varies.png').convert('RGB')).astype(int)
mag = (sheet[...,0] > 180) & (sheet[...,1] < 80) & (sheet[...,2] > 180)
lab, n = ndimage.label(~mag)
cutouts = []
for i in range(1, n+1):
    ys, xs = np.nonzero(lab == i)
    x0, x1, y0, y1 = xs.min(), xs.max()+1, ys.min(), ys.max()+1
    sub = sheet[y0:y1, x0:x1].copy()
    sub[~np.where(lab[y0:y1, x0:x1] == i, True, False)] = (255, 0, 255)
    cutouts.append(Image.fromarray(sub.astype('uint8')).convert('RGB'))
cutouts.sort(key=lambda im: -im.width)

def night_tint(arr):
    a = arr[:, :, :3].astype(float); lum = (a @ np.array([.2126,.7152,.0722]))[:, :, None]
    out = np.rint((lum*.20 + a*.80)*np.array([.44,.50,.62]) + [5,9,16]).clip(0,255).astype('uint8')
    return out

def cut_rgba(im, scale):
    im = im.convert('RGB').resize((max(1,round(im.width*scale)), max(1,round(im.height*scale))), Image.NEAREST)
    a = np.array(im).astype(int)
    mask = ~((a[...,0] > 180) & (a[...,1] < 80) & (a[...,2] > 180))
    rgba = np.dstack([night_tint(a), (mask*255).astype('uint8')])
    return Image.fromarray(rgba)

def mk_strip(items, hh):
    st = Image.new('RGBA', (1440, hh))
    for im, xpos, y in items:
        st.alpha_composite(im, (int(xpos), int(y)))
    return st

# far strip (haut, petites formes, rapide lente, alpha .8) : formes 3,2,6,5
far_items = []
cw = cutouts
cols = [(2, 0.55), (5, 0.5), (3, 0.6), (1, 0.28), (2, 0.5), (4, 0.22)]
st = Image.new('RGBA', (1440, 120))
for k, (idx, sc) in enumerate(cols):
    im = cut_rgba(cw[idx], sc)
    x = int(80 + k*235); y = int(118 - im.height - rng.integers(0, 10))
    st.alpha_composite(im, (x, y))
st.save(V/'calques'/f'{P}_bande_nuages_lointains_1440.png')

# overlay strip (grandes formes près de l'horizon, plus rapide) : 1 (gros cumulus), 4 (tour), 5, 6
st = Image.new('RGBA', (1440, 100))
for k, (idx, sc) in enumerate([(1, 0.5), (3, 0.9), (4, 0.6), (5, 0.8), (2, 0.7)]):
    im = cut_rgba(cw[idx], sc)
    x = int(140 + k*300); y = int(98 - im.height)
    st.alpha_composite(im, (x, y))
st.save(V/'calques'/f'{P}_bande_nuages_overlay_1440.png')

# accents statiques (04b)
acc = Image.new('RGBA', (W, H))
acc.alpha_composite(cut_rgba(cw[3], 0.7), (40, 84))
acc.alpha_composite(cut_rgba(cw[0], 0.42), (430, 120))
acc.alpha_composite(cut_rgba(cw[4], 0.5), (150, 46))
acc.save(V/'calques'/f'{P}_04b_nuages_accents.png')

# ---------- panneau + brume + lune + plateau réutilisés ----------
reuse = ['03_lune_generee', '04_nuages_lointains', '05_panorama_skypeak_foret_montagnes',
         '05b_brume_overlay', '06_nuages_overlay', '07_plateau_herbe', '08_paroi_rocheuse']
static = {n: L3(n) for n in reuse}
for n in ['bande_brume_0_1440', 'bande_brume_1_1440', 'bande_brume_2_1440', 'lune_sprite']:
    Image.open(V3/'calques'/f'{P3}_{n}.png').save(V/'calques'/f'{P}_{n}.png')

# ---------- 08 paroi : élargie en épaulement de montagne jusqu'en bas du cadre (fin de l'île) ----------
wall = np.array(L3('08_paroi_rocheuse')).copy()
wa = wall[..., 3] > 0
rtop = np.full(W, 999)
for x in range(W):
    ys = np.nonzero(wa[:, x])[0]
    if len(ys): rtop[x] = ys.min()
# Épaulement de montagne UNIQUEMENT sur les flancs (x<179 et x>780) : le centre (plateau +
# paroi d'origine) reste rigoureusement identique au layout de base, seule la paroi est prolongée
# sur les côtés pour rejoindre les coins du cadre et casser l'effet « île dans le ciel ».
def Ltop(x):
    if x < 179:      return 566.0 + (706.0-566.0)*(179-x)/179.0
    if x > 780:      return 566.0 + (706.0-566.0)*(x-780)/(959.0-780)
    return 999.0
L = np.clip(np.array([Ltop(x) for x in range(W)]), 0, H)
delta = np.zeros((H, W), bool)
for x in range(W):
    if L[x] >= H: continue
    delta[int(L[x]):H, x] = True
delta &= ~wa
# remplissage par continuation des strates rocheuses natives (colonnes denses sans vert)
SRC = [196, 236, 268, 324, 356, 404, 532, 596, 676, 748]
def rock_rows(col):
    a = col[:, :3]; return (a[:, 1] > 180) & (a[:, 0] < 150)
fill = np.zeros((H, W, 4), 'uint8')
for x in range(W):
    if not delta[:, x].any(): continue
    dst = np.abs(np.array(SRC)-x); src_x = SRC[int(dst.argmin())]
    col = wall[:, src_x]
    op = np.nonzero(col[..., 3] > 0)[0]
    op = op[~rock_rows(col[op])]
    if len(op) < 6: op = np.nonzero(wall[:, src_x, 3] > 0)[0]
    if len(op) == 0: continue
    # strates médianes (on écarte les 6 lignes du haut et du bas, trop sombres/vertes)
    lo, hi = op[6], op[-7]
    span = wall[lo:hi+1, src_x][:, :3]
    if len(span) == 0: continue
    ys = np.nonzero(delta[:, x])[0]; top = ys.min(); k = np.arange(top, H)
    off = (x*(len(span)-1))//W if W>1 else 0
    idx = (k - top + off) % len(span)
    fill[k, x, :3] = span[idx]; fill[k, x, 3] = 255
wall_new = wall.copy(); wall_new[delta] = fill[delta]
# ombre de pied : assombrir progressivement sous y=720
yy = np.arange(H)[:, None]
shade = np.clip(1.0 - 0.28*(yy-700)/164.0, 0, 1)
base = (yy > 700)
zone = base & delta
shadeB = np.broadcast_to(shade, (H, W))
vals = wall_new[..., :3][zone].astype(int) * shadeB[zone][:, None]
wall_new[..., :3][zone] = np.clip(vals, 0, 255)
# liseré sombre sur le haut de la zone élargie (contour roche)
edge = np.zeros((H, W), bool); edge[:-1] = delta[1:] & ~delta[:-1]
for c in range(3): wall_new[edge, c] = np.clip(wall_new[edge, c].astype(int)*0.7, 0, 255)
Image.fromarray(wall_new).save(V/'calques'/f'{P}_08_paroi_rocheuse.png')
static['08_paroi_rocheuse'] = Image.fromarray(wall_new)   # compose utilise la V4, pas la V3

# ---------- 08b brume avant (pied de paroi) ----------
band2 = Image.open(V3/'calques'/f'{P3}_bande_brume_2_1440.png').convert('RGBA')
fb = Image.new('RGBA', (W, H))
for x in range(-(0 % 1440), W, 1440): fb.alpha_composite(band2, (x, 770))
a = np.array(fb); a[:, :, 3] = (a[:, :, 3]*0.85).astype('uint8'); fb = Image.fromarray(a)
fb.save(V/'calques'/f'{P}_08b_brume_avant.png')

# ---------- bandes de nuages (déjà sauvées), re-strip overlay pour index ----------
def wrap_img(strip, off, y, alpha):
    im = Image.new('RGBA', (W, H))
    for x in range(-(int(off) % 1440), W, 1440): im.alpha_composite(strip, (x, y))
    if alpha < 1:
        a = np.array(im); a[:, :, 3] = (a[:, :, 3]*alpha).astype('uint8'); im = Image.fromarray(a)
    return im

FAR = dict(y=30, speed=-2, alpha=0.8)
NEAR = dict(y=300, speed=-6, alpha=1.0)
MIST = [dict(y=505, speed_px_s=-4, breath_period_s=9.0, phase=0.0),
        dict(y=625, speed_px_s=-7, breath_period_s=7.0, phase=2.0),
        dict(y=755, speed_px_s=-11, breath_period_s=5.5, phase=4.0)]
FOG  = dict(y=770, speed_px_s=-3, breath_period_s=8.0, phase=1.0)

def mist_layer(t):
    im = Image.new('RGBA', (W, H))
    strips = [Image.open(V/'calques'/f'{P}_bande_brume_{k}_1440.png').convert('RGBA') for k in range(3)]
    for b, st in zip(MIST, strips):
        breath = 0.65 + 0.35*(0.5 + 0.5*math.sin(2*math.pi*(t/b['breath_period_s']) + b['phase']))
        im.alpha_composite(wrap_img(st, -b['speed_px_s']*t, b['y'], breath))
    return im

def fog_layer(t):
    im = Image.new('RGBA', (W, H))
    breath = 0.65 + 0.35*(0.5 + 0.5*math.sin(2*math.pi*(t/FOG['breath_period_s']) + FOG['phase']))
    im.alpha_composite(wrap_img(band2, -FOG['speed_px_s']*t, FOG['y'], breath))
    return im

FPS_STARS = 8; FPS_METEOR = 30
L4_STARS = Image.open(V/'calques'/f'{P}_02_etoiles_phase0.png').convert('RGBA')
far_strip = Image.open(V/'calques'/f'{P}_bande_nuages_lointains_1440.png').convert('RGBA')
near_strip = Image.open(V/'calques'/f'{P}_bande_nuages_overlay_1440.png').convert('RGBA')

def compose(t, mode='jour'):
    out = sky.copy()
    out.alpha_composite(star_frames[int(t*FPS_STARS) % 64])
    out.alpha_composite(meteor_frames[int(t*FPS_METEOR) % 360])
    order = ['03_lune_generee', '04_nuages_lointains', '04b_nuages_accents',
             '05_panorama_skypeak_foret_montagnes', '05b_brume_overlay', '06_nuages_overlay',
             '07_plateau_herbe', '08_paroi_rocheuse', '08b_brume_avant']
    dyn = {
        '04_nuages_lointains': wrap_img(far_strip, -FAR['speed']*t, FAR['y'], FAR['alpha']),
        '06_nuages_overlay': wrap_img(near_strip, 700-NEAR['speed']*t, NEAR['y'], NEAR['alpha']),
        '05b_brume_overlay': mist_layer(t),
        '08b_brume_avant': fog_layer(t),
    }
    for n in order:
        im = dyn.get(n) or static.get(n) or Image.open(V/'calques'/f'{P}_{n}.png').convert('RGBA')
        if mode == 'nuit' and n not in ('03_lune_generee', '08b_brume_avant'):
            im = night(im)
        out.alpha_composite(im)
    return out

comp = compose(0)
comp.save(V/f'{P}_composition_nuit.png')
compose(0, 'nuit').save(V/f'{P}_composition_nuit_abyss.png')

# ---------- calques statiques exportés pour ORA/gallerie ----------
layers = [('01_ciel_profond', sky), ('02_etoiles_phase0', L4_STARS), ('02b_etoiles_filantes_vide', meteor_frames[0]),
          ('03_lune_generee', static['03_lune_generee']),
          ('04_nuages_lointains', wrap_img(far_strip, 0, FAR['y'], FAR['alpha'])),
          ('04b_nuages_accents', Image.open(V/'calques'/f'{P}_04b_nuages_accents.png').convert('RGBA')),
          ('05_panorama_skypeak_foret_montagnes', static['05_panorama_skypeak_foret_montagnes']),
          ('05b_brume_overlay', mist_layer(0)),
          ('06_nuages_overlay', wrap_img(near_strip, 700, NEAR['y'], NEAR['alpha'])),
          ('07_plateau_herbe', static['07_plateau_herbe']),
          ('08_paroi_rocheuse', Image.open(V/'calques'/f'{P}_08_paroi_rocheuse.png').convert('RGBA')),
          ('08b_brume_avant', fog_layer(0))]
for n, im in layers: im.save(V/'calques'/f'{P}_{n}.png')

# ---------- ORA ----------
root = ET.Element('image', w=str(W), h=str(H), version='0.0.3'); stack = ET.SubElement(root, 'stack')
with zipfile.ZipFile(V/f'{P}_editable.ora', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
    for i, (name, im) in enumerate(reversed(layers)):
        ET.SubElement(stack, 'layer', name=name, src=f'data/{i}.png', x='0', y='0', opacity='1.0', visibility='visible')
        z.writestr(f'data/{i}.png', png(im))
    z.writestr('stack.xml', ET.tostring(root)); z.writestr('mergedimage.png', png(comp))

# ---------- webp ----------
def webp(path, frames_iter, count, fps, size=(W, H)):
    enc = _webp.WebPAnimEncoder(size, 0, 0, False, 9, 17, False, False)
    for i, f in enumerate(frames_iter): enc.add(f.getim(), round(i*1000/fps), True, 80, 100, 4)
    enc.add(None, round(count*1000/fps), True, 80, 100, 0); path.write_bytes(enc.assemble('', '', ''))

if FULL:
    for mode, tag in [('jour', 'nuit'), ('nuit', 'nuit_abyss')]:
        webp(V/f'{P}_extrait_24s_{tag}.webp', (compose(i/15, mode) for i in range(360)), 360, 15)

# ---------- manifest ----------
wcols = [dict(component=int(k), scale=float(sc)) for k, sc in cols]
manifest = dict(size=[W, H], version='v4', base_layout='V3 conserved (stars, meteors, moon, panorama, mist bands 0-2, plateau grass, wall tops)',
    corrections=dict(paroi="élargie jusqu'aux coins du cadre (L(x)=haut de paroi au centre, 824 sur les flancs), remplissage par continuation des strates natives, liseré sombre",
                     ciel='dégradé plus riche (6 paliers) issu du brut généré, lueur lunaire renforcée',
                     nuages='6 formes variées générées sur fond magenta : bande lointaine (6 blocs) + overlay (5 blocs) + 3 accents fixes (04b)',
                     brume='3 bandes V3 conservées + brume avant (08b, y=770) sur le pied de la paroi'),
    sky=dict(kind='authored gradient richer', stops=stops, dither='Bayer 4x4 ±0.5', moon_glow_centre=[mx, my]),
    clouds=dict(far=FAR, overlay=NEAR, wrap_px=1440, cutouts=['raw_nuages_varies.png'], static_accents='04b_nuages_accents'),
    mist=dict(bands=MIST, fog=FOG),
    reused_from_v3=['etoiles_frames', 'etoiles_filantes_frames', '03_lune_generee', '05_panorama_skypeak_foret_montagnes', '05b_brume_overlay(bands 0-2)', '07_plateau_herbe'],
    wall_fill=dict(delta_px=int(delta.sum()), method='vertical continuation of native strata', edge_outline=True),
    all_pixels_generated_or_authored=True, runtime_validated=False)
(V/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('OK v4', 'wall fill px', int(delta.sum()))
