"""Entree grotte Crooked/Halcyon/Sky Peak v1 : couches generees (G1b) + complement natif.

Canevas 848x1264 = brut G1b 1:1, sans resampling. Paroi/bouche/chemin = masques
matiere du brut genere (documentes GENERES). Sol/herbe, rochers, fleurs, arbres
= pixels natifs (translation seule). Fleurs : 4 phases natives @200ms.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import sys
import zipfile
import random

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from source.zones_relayout_v1.build import seam
from night import night

SRC = R / 'source/entree_crooked_v1'
OUT = R / 'renders/entree_crooked_v1'
W, H = 848, 1264
CX = 424
PFX = 'EntreeCrookedV1'

G1B = np.array(Image.open(SRC / 'bruts/G1b_paroi_bouche.png').convert('RGBA'))
GIF0 = np.array(Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGBA')).astype(float)
L3 = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png').convert('RGBA')
L4 = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png').convert('RGBA')
SH = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png').convert('RGBA')
OB = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png').convert('RGBA')
FLOWERS = []
for k in range(10):
    FLOWERS.append([Image.open(R / f'renders/applewoods_skygrass_v1/sprites/fleur_sky_{k:02}_phase_{i:02}.png').convert('RGBA') for i in range(4)])


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def grass_boxes():
    r, g, b = GIF0[..., 0], GIF0[..., 1], GIF0[..., 2]
    clean = (g > r + 8) & (g > b) & (r < 150)
    boxes = []
    for yy in range(150, 440, 8):
        for xx in range(40, 460, 8):
            z = clean[yy:yy + 16, xx:xx + 24]
            if z.shape == (16, 24) and z.mean() > 0.92:
                boxes.append((xx, yy, xx + 24, yy + 16))
    assert len(boxes) >= 60
    return boxes[:60]


def quilt(boxes, seed=31):
    rng = np.random.default_rng(seed)
    src = np.array(Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGBA'))
    out = np.zeros((H, W, 4), np.uint8)
    hh, ww, ov = 16, 24, 8
    for y in range(0, H, hh - ov):
        for x in range(0, W, ww - ov):
            h, w = min(hh, H - y), min(ww, W - x)
            old = out[y:y + h, x:x + w]
            occupied = old[:, :, 3] > 0
            best = None
            for idx in rng.permutation(len(boxes))[:24]:
                x0, y0, _, _ = boxes[idx]
                patch = src[y0:y0 + h, x0:x0 + w]
                cost = ((old[:, :, :3].astype(float) - patch[:, :, :3]) ** 2).sum(2)
                score = cost[occupied].mean() if occupied.any() else rng.random()
                if best is None or score < best[0]:
                    best = (score, patch, cost)
            _, patch, cost = best
            take = np.ones((h, w), bool)
            if x and w >= ov:
                take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
            if y and h >= ov:
                take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
            take |= old[:, :, 3] == 0
            old[take] = patch[take]
    return Image.fromarray(out)


def masks():
    lum = G1B[..., :3].mean(2)
    # bouche : plus grande composante sombre dans le rectangle de la gueule
    rect = np.zeros((H, W), bool)
    rect[340:640, 310:540] = True
    lab, _ = ndi.label((lum < 110) & rect)
    sizes = [[(lab == i).sum(), i] for i in range(1, lab.max() + 1)]
    bouche = lab == max(sizes)[1]
    # sable : lumineux, plus grande composante + fond sableux dans la gueule
    lab2, _ = ndi.label(lum > 175)
    sizes2 = [[(lab2 == i).sum(), i] for i in range(1, lab2.max() + 1)]
    sable = lab2 == max(sizes2)[1]
    inrect = np.zeros((H, W), bool)
    inrect[400:620, 330:520] = True
    sable |= (lum > 175) & inrect
    funnel = np.zeros((H, W), bool)
    funnel[600:700, 360:490] = True
    sable |= (lum > 85) & funnel  # sol ombrage de la gorge (entonnoir du chemin)
    # chemin : sable contenu dans l'entonnoir parvis + couloir
    yy, xx = np.mgrid[:H, :W].astype(float)
    t = np.clip((920 - yy) / 140.0, 0, 1)
    s = t * t * (3 - 2 * t)
    hw = np.where(yy <= 780, 424, np.where(yy >= 920, 48, 48 + 376 * s))
    wob = 10 * np.sin(yy / 47.0) + 6 * np.sin(yy / 23.0 + 1.7)
    hw = np.where(yy > 780, hw + wob, hw)
    chemin = sable & (np.abs(xx - CX) <= hw) & ~bouche  # la bouche garde priorite
    paroi = ~(sable | bouche)
    return dict(chemin=chemin, paroi=paroi, bouche=bouche)


def lay(mask, name):
    a = G1B.copy()
    a[~mask] = (0, 0, 0, 0)
    return Image.fromarray(a)


ROCKS = {'rocher_groupe_ouest': (53, 165, 133, 226), 'rocher_groupe_est': (186, 157, 266, 240),
         'petit_rocher_a': (26, 217, 62, 240), 'petit_rocher_b': (269, 218, 292, 236)}
ROCK_POS = {'rocher_groupe_ouest': (216, 648), 'rocher_groupe_est': (560, 640),
            'petit_rocher_a': (320, 720), 'petit_rocher_b': (512, 800)}
TREES = [(40, 880), (664, 920), (80, 1020), (640, 1060)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'bruts').mkdir(exist_ok=True)
    M = masks()
    layers = {}
    layers['01_sol_herbe'] = quilt(grass_boxes())
    layers['02_chemin_sable'] = lay(M['chemin'], 'chemin')
    layers['03_paroi'] = lay(M['paroi'], 'paroi')
    layers['04_bouche'] = lay(M['bouche'], 'bouche')
    rochers = Image.new('RGBA', (W, H))
    for n, box in ROCKS.items():
        m = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
        m.alpha_composite(SH.crop(box))
        m.alpha_composite(OB.crop(box))
        rochers.alpha_composite(m, ROCK_POS[n])
    layers['05_rochers'] = rochers
    # fleurs : sites en prairie (ni sable, ni paroi, ni bouche, ni arbres/rochers)
    meadow = ~(M['chemin'] | ~M['paroi'] & False)  # placeholder, recalcule ci-dessous
    meadow = np.ones((H, W), bool)
    meadow[M['chemin'] | M['bouche']] = False
    meadow[M['paroi'] & (np.array(layers['03_paroi'])[:, :, 3] > 0)] = False
    for x, y in TREES:
        meadow[y:y + 120, x:x + 144] = False
    for n, box in ROCKS.items():
        x, y = ROCK_POS[n]
        meadow[y:y + box[3] - box[1], x:x + box[2] - box[0]] = False
    rng = random.Random(11)
    sites = []
    tries = 0
    while len(sites) < 22 and tries < 4000:
        tries += 1
        x, y = rng.randrange(16, W - 48), rng.randrange(700, H - 48)
        if meadow[y:y + 24, x:x + 25].all() and all(
                abs(x - s['x']) > 28 or abs(y - s['y']) > 26 for s in sites):
            sites.append(dict(x=x, y=y, sprite=len(sites) % 10, off=rng.randrange(4)))
    assert len(sites) == 22, len(sites)
    phases = []
    for p in range(4):
        im = Image.new('RGBA', (W, H))
        for s in sites:
            im.alpha_composite(FLOWERS[s['sprite']][(p + s['off']) % 4], (s['x'], s['y']))
        phases.append(im)
    layers['06_fleurs'] = phases[0]
    troncs = Image.new('RGBA', (W, H))
    canopees = Image.new('RGBA', (W, H))
    for x, y in TREES:
        troncs.alpha_composite(L3.crop((72, 160, 120, 216)), (x + 56, y + 64))
        canopees.alpha_composite(L4.crop((16, 96, 160, 216)), (x, y))
    layers['07_troncs'] = troncs
    layers['08_canopees'] = canopees
    order = ['01_sol_herbe', '02_chemin_sable', '05_rochers', '06_fleurs',
             '03_paroi', '04_bouche', '07_troncs', '08_canopees']
    # NB : paroi/bouche APRES fleurs/rochers : la paroi ne chevauche que sable+prairie haute.
    for n, im in layers.items():
        im.save(OUT / f'{PFX}_{n}_jour.png')
        night(im).save(OUT / f'{PFX}_{n}_nuit.png')
    for p in range(1, 4):
        phases[p].save(OUT / f'{PFX}_06_fleurs_phase{p}_jour.png')
        night(phases[p]).save(OUT / f'{PFX}_06_fleurs_phase{p}_nuit.png')
    comp = Image.new('RGBA', (W, H))
    for n in order:
        comp.alpha_composite(layers[n])
    comp.save(OUT / 'composite_jour.png')
    compn = Image.new('RGBA', (W, H))
    for n in order:
        compn.alpha_composite(night(layers[n]))
    compn.save(OUT / 'composite_nuit.png')
    for p in range(4):
        c = Image.new('RGBA', (W, H))
        for n in order:
            c.alpha_composite(phases[p] if n == '06_fleurs' else layers[n])
        c.save(OUT / f'composite_phase{p}_jour.png')
    # ORA
    ora = io.BytesIO()
    with zipfile.ZipFile(ora, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', zipfile.ZIP_STORED)
        xml = ['<image w="%d" h="%d"><stack>' % (W, H)]
        blob = dict(layers)
        for p in range(1, 4):
            blob[f'06_fleurs_phase{p}'] = phases[p]
        for n, im in blob.items():
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            z.writestr(f'data/{n}.png', buf.getvalue())
            xml.append(f'<layer name="{n}" src="data/{n}.png" visible="%d"/>' % (0 if 'phase' in n else 1))
        xml.append('</stack></image>')
        z.writestr('stack.xml', ''.join(xml))
    (OUT / f'{PFX.lower()}.ora').write_bytes(ora.getvalue())
    man = dict(canevas=[W, H], orientation='SOUTH_TO_NORTH', entree=[CX, 610],
               plan='source/entree_crooked_v1/plan_zones.png (guide, aucun pixel final)',
               bruts={'G1b_paroi_bouche.png': dict(sha256=sha(SRC / 'bruts/G1b_paroi_bouche.png'),
                                                  statut='retenu (GENERE, style Crooked)',
                       usage='03_paroi + 04_bouche + 02_chemin par masques matiere, translation nulle'),
                      'rejetes/G1_paroi_double_rejetee.png': 'double paroi barrant le chemin'},
               couches={n: ('GENERE (G1b, masque)' if n in ('02_chemin_sable', '03_paroi', '04_bouche')
                            else 'NATIF (translation)') for n in order},
               masques={'04_bouche': 'lum<110, plus grande composante du rect (310,340,540,640)',
                        'sable': 'lum>175, plus grande composante + fond de gueule (330,400,520,620)',
                        'entonnoir': 'lum>85 dans (360,600,490,700) = sol ombrage de la gorge',
                        '02_chemin_sable': 'sable dans eventail (full->48px, smoothstep + oscillation), hors bouche',
                        '03_paroi': 'complement (ni sable ni bouche)'},
               ordre=order, fleurs=dict(sites=sites, phases=4, ms=200, natif='applewoods fleur_sky_*'),
               arbres=TREES, rochers={n: dict(box=list(b), pos=list(ROCK_POS[n])) for n, b in ROCKS.items()},
               nuit='Abyss exact, une fois par calque', runtime='NOT TESTED', art_approved=False)
    (OUT / 'manifest.json').write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print('couches:', {n: np.array(im)[:, :, 3].sum() // 255 for n, im in layers.items()})
    print('sites fleurs:', len(sites))


if __name__ == '__main__':
    main()
