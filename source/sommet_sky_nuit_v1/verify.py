"""Verification independante — re-derive tout depuis GIF + bruts + ref_v2."""
from pathlib import Path
import sys, json, io, hashlib, zipfile, xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night
O = R / 'renders/sommet_sky_nuit_v1'
P = O / 'sommet_nuit'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['taille']
checks = {}
NN = Image.Resampling.NEAREST

def load(n): return Image.open(P / n).convert('RGBA')
# 1. dimensions
for f in list(P.glob('sky_*.png')) + [P / 'COMPOSITION.png']:
    assert Image.open(f).size == (W, H), f
assert W % 8 == 0 and H % 8 == 0
checks['dimensions_960x600_grille8'] = True
# 2. prairie native re-derivee
refs = [np.array(Image.open(R / f'source/sky_peak_v1/gif_{i}.png').convert('RGBA')) for i in range(4)]
pet = []
for fr in refs:
    r, g, b = (fr[:, :, i].astype(float) for i in range(3))
    pet.append((r > 190) & (r > g * 1.04) & (r > b * 1.08))
union = np.logical_or.reduce(pet)
clean = refs[0].copy(); need = union.copy()
for i, fr in enumerate(refs):
    fill = need & (~pet[i]); clean[fill] = fr[fill]; need &= pet[i]
rr = clean[:, :, 0].astype(float); gr = clean[:, :, 1].astype(float); bb = clean[:, :, 2].astype(float)
gmask = (gr > rr * 1.05) & (gr > bb * 1.05)
med = np.median(clean[gmask & ~union][:, :3], axis=0).astype('uint8')
clean[need] = (*med, 255)
band = clean[328:504]
mir = np.concatenate([band[:, 0:228][:, ::-1], band, band[:, 503:275:-1]], axis=1)
day = np.array(Image.open(O / 'controle_bande_prairie_jour.png').convert('RGBA'))
assert np.array_equal(day, mir), 'bande jour non native'
checks['prairie_jour_native_exacte'] = True
nm = np.array(night(Image.fromarray(mir)))
gm = mir[:, :, 1].astype(float) > mir[:, :, 0].astype(float) * 1.05
gm &= mir[:, :, 1].astype(float) > mir[:, :, 2].astype(float) * 1.05
l08 = np.array(load('sky_08_prairie.png'))[424:600]
l09 = np.array(load('sky_09_reliefs.png'))[424:600]
assert np.array_equal(l08[gm], nm[gm]) and (l08[~gm][:, 3] == 0).all()
assert np.array_equal(l09[~gm], nm[~gm]) and (l09[gm][:, 3] == 0).all()
checks['prairie_nuit_abyss_split'] = True
# 3. fleurs : re-extraction + re-rendu
lab, _ = nd.label(union, np.ones((3, 3)))
cands = []
for k, sl in enumerate(nd.find_objects(lab), 1):
    if sl is None: continue
    gy, gx = sl; h, w = gy.stop - gy.start, gx.stop - gx.start
    if not (7 <= w <= 30 and 7 <= h <= 28) or gx.start < 2 or gy.stop > 502: continue
    mk = lab == k
    ims = []
    for i, fr in enumerate(refs):
        vis = nd.binary_fill_holes(pet[i] & mk)
        out = fr[gy, gx].copy(); out[~vis[gy, gx]] = 0
        ims.append(out)
    def hb(a):
        q = io.BytesIO(); Image.fromarray(a).save(q, format='PNG'); return q.getvalue()
    if len({hb(a) for a in ims}) < 3: continue
    cands.append((gx.start, gy.start, ims))
cands.sort(key=lambda c: (c[1] // 30, c[0]))
# compare aux sprites archives (ordre du build : find_objects stride)
sp = sorted((P / 'sprites').glob('fleur_native_*_phase_0.png'))
assert len(sp) == M['fleurs']['sprites_natifs'] == 10
ok = 0
for f in sp:
    a = np.array(Image.open(f).convert('RGBA'))
    if any(np.array_equal(a, c[2][0]) for c in cands):
        ok += 1
assert ok == 10, ok
checks['fleurs_sprites_natifs'] = ok
for gname, gid in (('loin', '10'), ('proche', '11')):
    for ph in range(4):
        im = Image.new('RGBA', (W, H))
        for s in M['fleurs']['sites_detail']:
            if (s['center'][1] < 515) != (gname == 'loin'): continue
            im.alpha_composite(Image.open(P / 'sprites' / f"fleur_native_{s['sprite']:02}_phase_{(ph + s['phase_offset']) % 4}.png").convert('RGBA'), tuple(s['origin']))
        assert im.tobytes() == load(f'sky_{gid}_fleurs_{gname}_native_ph{ph}.png').tobytes(), (gname, ph)
        assert night(im).tobytes() == load(f'sky_{gid}_fleurs_{gname}_nuit_ph{ph}.png').tobytes(), (gname, ph, 'nuit')
checks['fleurs_groupes_recomposes'] = True
# 4. etoiles : octets ref_v2
src = sorted((R / 'renders/references_calques_v2/etoiles').glob('*.png'))
dst = sorted((P / 'etoiles').glob('*.png'))
assert len(dst) == 64 == len(src)
for a, b in zip(src, dst):
    assert a.read_bytes() == b.read_bytes(), b.name
assert [hashlib.sha256(f.read_bytes()).hexdigest() for f in dst] == M['etoiles']['hashes']
checks['etoiles_64_octets'] = True
# 5. ciel
sk = np.array(load('sky_01_ciel.png'))
assert (sk[0, 480, :3] == [8, 17, 49]).all() and (sk[300, 100, :3] == [54, 74, 122]).all()
assert (sk[:, :, 3] == 255).all()
checks['ciel_echantillonne'] = True
# 6. pano split : re-key independant
brut = np.array(Image.open(O / 'bruts/panorama.png').convert('RGBA'))
r, g, b = (brut[:, :, i].astype(int) for i in range(3))
strong = (r > 35) & (b > 35) & (r > g * 1.8) & (b > g * 1.8)
brut[strong] = 0
tr = brut[:, :, 3] == 0
edge = nd.binary_dilation(tr, iterations=1) & ~tr
brut[edge & (r > 90) & (b > 90) & (r > g * 1.35) & (b > g * 1.35)] = 0
keyed = Image.fromarray(brut).resize((W, M['panorama_genere']['hauteur_redim']), NN)
ka = np.array(keyed)
m = np.array(load('sky_04_montagnes.png'))[63:63 + ka.shape[0]]
f = np.array(load('sky_06_foret.png'))[63:63 + ka.shape[0]]
comp = Image.alpha_composite(Image.fromarray(m), Image.fromarray(f))
assert np.array_equal(np.array(comp), ka), 'split pano'
assert not ((m[:, :, 3] > 0) & (f[:, :, 3] > 0)).any(), 'chevauchement split'
checks['pano_split_exact'] = True
# 7. wraps : marges + phases + identite
for lname, dname, n in (('sky_03_nuages_lointains_wrap.png', 'nuages_lointains_phases', 32),
                        ('sky_05_nuages_proches_wrap.png', 'nuages_proches_phases', 24),
                        ('sky_07_brume_wrap.png', 'brume_phases', 16)):
    st = np.array(load(lname))
    if 'brume' not in lname:
        assert not st[:, :32, 3].any() and not st[:, -32:, 3].any(), lname
    phs = sorted((P / dname).glob('*.png'))
    assert len(phs) == n, (lname, len(phs))
    for i, pf in enumerate(phs):
        assert np.array_equal(np.array(Image.open(pf).convert('RGBA')), np.roll(st, -i * W // n, axis=1)), (lname, i)
    assert np.array_equal(np.roll(st, -W, axis=1), st)
    def wrapped(off):
        return st[:, (np.arange(W) + off) % W]
    assert np.array_equal(wrapped(0), wrapped(W)) and np.array_equal(wrapped(1), wrapped(W + 1))
    assert np.array_equal(wrapped(W - 1)[:, 1:], wrapped(W)[:, :-1])
checks['wraps_seamless'] = True
mist = np.array(load('sky_07_brume_wrap.png'))
assert np.array_equal(mist[:, :W // 2], mist[:, W // 2:][:, ::-1]), 'miroir brume'
checks['brume_miroir'] = True
# 8. ORA : 14 calques, visibles recomposent COMPOSITION
with zipfile.ZipFile(P / 'sommet_nuit.ora') as z:
    assert z.read('mimetype') == b'image/openraster'
    nodes = list(ET.fromstring(z.read('stack.xml')).find('stack'))
    assert len(nodes) == 13, len(nodes)
    c = Image.new('RGBA', (W, H))
    for nd_ in reversed(nodes):
        if nd_.get('visibility') == 'hidden':
            continue
        c.alpha_composite(Image.open(io.BytesIO(z.read(nd_.get('src')))).convert('RGBA'))
    assert c.tobytes() == load('COMPOSITION.png').tobytes()
checks["ora_13_recompose"] = True
# 9. webp 8 frames
w = Image.open(P / 'ANIMATION_FLORA_STELLA.webp')
assert getattr(w, 'n_frames', 1) == 8
checks['webp_8f'] = True
rep = {'verifications': checks, 'taille': [W, H], 'resultat': 'PASS',
       'limites': M['limites'] + ['Decor verifie zero-entite par inspection visuelle (bruts archives)']}
(O / 'verification.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2))
print('VERIFY PASS:', json.dumps(checks, ensure_ascii=False))
