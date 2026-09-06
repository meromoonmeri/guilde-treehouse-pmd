# Rebuild — Entrée de donjon « forêt avec chemin » (méthode spriter PMD)
# Pipeline : brut 1376x768 -> détourage magenta -> quantification médiane
# -> réduction par vote majoritaire (pixel art propre, grille 8 px)
# -> nettoyage des pixels parasites -> 3 calques -> PNG + Aseprite + nuit
# -> manifeste JSON -> contrôle qualité (identité PNG/calques/Aseprite).
from pathlib import Path
from PIL import Image
from scipy.ndimage import label
import numpy as np, json, struct, zlib

D = Path(__file__).resolve().parents[1]
SRC = D / 'source' / '_gen' / 'entree_foret_brut.png'
OUT = D / 'sprites' / 'entrees_donjon'
CAL = OUT / 'calques'
OUT.mkdir(parents=True, exist_ok=True)
CAL.mkdir(parents=True, exist_ok=True)

GRILLE = 8
MAX_COLORS = 28          # palette limitée, style GBA
NIGHT = ([.36, .34, .43], [9, 10, 19])   # formule du kit

# ---------------------------------------------------------------- helpers kit
def png(im, path):
    a = np.array(im.convert('RGBA'))
    colors, idx = np.unique(a.reshape(-1, 4), axis=0, return_inverse=True)
    if len(colors) <= 256:
        q = Image.fromarray(idx.reshape(a.shape[:2]).astype('uint8'), 'P')
        pal = np.zeros((256, 3), np.uint8); pal[:len(colors)] = colors[:, :3]
        q.putpalette(pal.ravel()); q.info['transparency'] = bytes(colors[:, 3])
        q.save(path, optimize=True)
    else:
        im.save(path, optimize=True)

def astr(s):
    b = s.encode(); return struct.pack('<H', len(b)) + b

def chunk(k, d):
    return struct.pack('<IH', len(d) + 6, k) + d

def ase(path, layers, size):
    """Écrivain .aseprite identique à source/rebuild_kit.py (calques, grille 8)."""
    w, h = size; chunks = []
    for n, im in layers:
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr(n)))
    for i, (n, im) in enumerate(layers):
        box = im.getbbox()
        if box:
            x, y, _, _ = box; q = im.crop(box)
        else:
            x = y = 0; q = Image.new('RGBA', (1, 1))
        chunks.append(chunk(0x2005, struct.pack('<HhhBHh', i, x, y, 255, 2, 0) + b'\0' * 5 +
                            struct.pack('<HH', q.width, q.height) + zlib.compress(q.tobytes(), 9)))
    data = b''.join(chunks)
    frame = struct.pack('<IHHH2sI', len(data) + 16, 0xF1FA, len(chunks), 100, b'\0\0', len(chunks)) + data
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, w, h, 32, 1, 100)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, GRILLE, GRILLE)
    path.write_bytes(header + frame)

# ---------------------------------------------------------------- 1. brut + détourage
raw = Image.open(SRC).convert('RGB')
a = np.array(raw).astype(int)
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
mag = (r > 185) & (g < 95) & (b > 185) & (r - g > 90) & (b - g > 90)
# décontamination des franges : les pixels opaques trop magenta sont neutralisés
fringe = (~mag) & (r - g > 55) & (b - g > 40) & (r > 110)
m = (r + g + b) / 3
a[:, :, 0] = np.where(fringe, m * 1.02, r); a[:, :, 1] = np.where(fringe, m, g); a[:, :, 2] = np.where(fringe, m * 0.98, b)
op = ~mag
ys, xs = np.where(op)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
pad = 6
y0 = max(0, y0 - pad); x0 = max(0, x0 - pad); y1 = min(a.shape[0], y1 + pad); x1 = min(a.shape[1], x1 + pad)
crop = a[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)
op = op[y0:y1, x0:x1]
print(f'brut {raw.size} -> crop {crop.shape[1]}x{crop.shape[0]}')

# ---------------------------------------------------------------- 2. quantification palette
def median_cut(pixels, n):
    """Découpe médiane récursive -> n couleurs représentatives."""
    buckets = [pixels]
    while len(buckets) < n:
        buckets.sort(key=len, reverse=True)
        px = buckets.pop(0)
        if len(px) < 2: buckets.append(px); break
        ch = int(np.argmax(px.max(0) - px.min(0)))
        px = px[np.argsort(px[:, ch])]
        mid = len(px) // 2
        buckets += [px[:mid], px[mid:]]
    return np.array([b.mean(0) for b in buckets])

cols = crop[op]
pal = median_cut(cols, MAX_COLORS * 2)
# fusion des couleurs trop proches (distance < 14)
merged = []
for c in pal:
    if not any(np.max(np.abs(c - d)) < 14 for d in merged):
        merged.append(c)
pal = np.array(merged)
assert len(pal) <= MAX_COLORS, len(pal)
d = np.abs(crop[:, :, None, :].astype(int) - pal[None, None, :, :]).sum(3)
idx = np.argmin(d, axis=2)
idx[~op] = -1
print(f'palette finale : {len(pal)} couleurs')

# ---------------------------------------------------------------- 3. réduction vote majoritaire
def target_dims(ch, cw):
    scale = min(160 / cw, 176 / ch, 8.0)
    tw = max(8, int(round(cw * scale / GRILLE)) * GRILLE)
    th = max(8, int(round(ch * scale / GRILLE)) * GRILLE)
    return tw, th

TW, TH = target_dims(crop.shape[0], crop.shape[1])
bh = max(1, round(crop.shape[0] / TH)); bw = max(1, round(crop.shape[1] / TW))
ph = -crop.shape[0] % bh; pw = -crop.shape[1] % bw
padv = np.full((ph, crop.shape[1]), -1); padh = np.full((TH and (crop.shape[0] + ph), pw), -1)
big = np.vstack([idx, padv]); big = np.hstack([big, padh])
rows, cols_ = big.shape[0] // bh, big.shape[1] // bw
blocks = big.reshape(rows, bh, cols_, bw).transpose(0, 2, 1, 3).reshape(rows, cols_, -1)
small = np.zeros((rows, cols_), int)
for i in range(rows):
    for j in range(cols_):
        blk = blocks[i, j]; blk = blk[blk >= 0]
        if len(blk) == 0: small[i, j] = -1
        else: small[i, j] = np.bincount(blk, minlength=len(pal)).argmax()
print(f'réduction : {TW}x{TH} (blocs {bh}x{bw}) — dims %8 : {TW % 8 == 0 and TH % 8 == 0}')

# ---------------------------------------------------------------- 4. nettoyage parasites
def denoise(ix, passes=2):
    for _ in range(passes):
        p = np.pad(ix, 1, constant_values=-1)
        nb = np.stack([p[0:-2, 0:-2], p[0:-2, 1:-1], p[0:-2, 2:], p[1:-1, 0:-2],
                       p[1:-1, 2:], p[2:, 0:-2], p[2:, 1:-1], p[2:, 2:]])
        out = ix.copy()
        for i in range(ix.shape[0]):
            for j in range(ix.shape[1]):
                c = ix[i, j]; n = nb[:, i, j]
                same = (n == c).sum(); val = n[n >= 0]
                if c >= 0 and same <= 2 and len(val) >= 5:
                    out[i, j] = np.bincount(val, minlength=len(pal)).argmax()
        ix = out
    return ix

small = denoise(small)

# recadre sur canvas final multiple de 8 : centré horizontalement, COLLÉ EN BAS
canvas = np.full((TH, TW), -1, int)
sy, sx = small.shape
oy = TH - sy; ox = (TW - sx) // 2
canvas[oy:oy + sy, ox:ox + sx] = small
final = canvas

# ---------------------------------------------------------------- 5. reconstruction RGBA
rgba = np.zeros((TH, TW, 4), np.uint8)
m = final >= 0
rgba[:, :, :3][m] = pal[final[m]].astype(np.uint8)
rgba[:, :, 3][m] = 255
jour = Image.fromarray(rgba, 'RGBA')
png(jour, OUT / 'entree_foret_chemin_jour.png')

def night(im):
    q = np.array(im.convert('RGBA')).astype(int)
    q[:, :, :3] = np.rint(q[:, :, :3] * NIGHT[0] + NIGHT[1]).clip(0, 255).astype('uint8')
    q[q[:, :, 3] == 0] = 0          # transparent reste (0,0,0,0), comme le kit
    return Image.fromarray(q.astype('uint8'), 'RGBA')

nuit = night(jour)
png(nuit, OUT / 'entree_foret_chemin_nuit.png')

# ---------------------------------------------------------------- 6. calques
pc = pal.astype(int)
mean = pc.mean(1); rr, gg, bb = pc[:, 0], pc[:, 1], pc[:, 2]
grass = (gg > 70) & (gg - rr > 20) & (gg - bb > 10) & (mean > 70)   # verts de pré, ombres comprises
tan = (rr > gg) & (gg > bb) & (rr > 120) & (gg > 95)               # chemin sable
pebble = (np.abs(rr - gg) < 14) & (np.abs(gg - bb) < 14) & (mean > 90)
ground_cls = grass | tan | pebble
dark_cls = (mean < 78) & (bb >= gg - 4)                             # cavité bleu-violet
gm = ground_cls[final.clip(0)] & m
lab, n = label(gm)
touch = set(lab[-1, :][lab[-1, :] > 0]) | set(lab[:, 0][lab[:, 0] > 0]) | set(lab[:, -1][lab[:, -1] > 0])
ground = m & np.isin(lab, list(touch))
dm = dark_cls[final.clip(0)] & m & ~ground
lab2, n2 = label(dm)
keep = [i for i in range(1, n2 + 1) if (dm[lab2 == i].sum() >= 10) and (np.where(lab2 == i)[0].mean() < TH * 0.75)]
cavity = m & np.isin(lab2, keep)
structure = m & ~ground & ~cavity

names = [('00_sol_chemin', ground), ('01_ouverture_sombre', cavity), ('02_massif_foret', structure)]
assert (ground | cavity | structure).sum() == m.sum(), 'partition calques non exacte'
for mode, base in [('jour', jour), ('nuit', nuit)]:
    barr = np.array(base)
    for name, mask in names:
        layer = np.zeros_like(barr); layer[mask] = barr[mask]
        png(Image.fromarray(layer, 'RGBA'), CAL / f'{name}_{mode}.png')
    layers = []
    for name, mask in names:
        layer = np.zeros_like(barr); layer[mask] = barr[mask]
        layers.append((name, Image.fromarray(layer, 'RGBA')))
    ase(OUT / f'entree_foret_chemin_{mode}.aseprite', layers, (TW, TH))

# (la génération brute reste dans source/_gen/entree_foret_brut.png — voir METHODE_SPRITER.md)

# ---------------------------------------------------------------- 7. manifeste
manifest = {
    'titre': 'Entrée de donjon — forêt avec chemin (style PMD Sky / Rescue Team)',
    'grille': GRILLE, 'animation': False,
    'methode': ['références PMD (Spriters Resource)', 'génération brute', 'détourage magenta',
                'palette médiane <=28 couleurs', 'réduction vote majoritaire', 'nettoyage parasites',
                '3 calques', 'PNG + Aseprite', 'nuit = formule du kit'],
    'sprites': [{
        'id': 'entree_foret_chemin', 'nom': 'Entrée de forêt avec chemin',
        'groupe': 'entree_donjon', 'taille': [TW, TH], 'pivot': [TW / 2, TH],
        'calques': [n for n, _ in names],
        'fichiers': {mo: {'png': f'sprites/entrees_donjon/entree_foret_chemin_{mo}.png',
                          'aseprite': f'sprites/entrees_donjon/entree_foret_chemin_{mo}.aseprite',
                          'calques': [f'sprites/entrees_donjon/calques/{n}_{mo}.png' for n, _ in names]}
                     for mo in ['jour', 'nuit']},
        'source': 'source/_gen/entree_foret_brut.png'
    }]
}
(OUT / 'entrees.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------- 8. contrôle qualité
rep = {'taille': [TW, TH], 'palette': int(len(pal)), 'grille': GRILLE}
assert TW % 8 == 0 and TH % 8 == 0
# chemin collé au bord bas (continuité de sol, règle du kit)
bottom = ground[-1, TW * 2 // 5: TW * 3 // 5]
rep['chemin_bord_bas'] = f'{bottom.mean() * 100:.0f}%'
assert bottom.mean() >= 0.8, 'le chemin doit toucher le bord bas'
# ouverture sombre présente en haut
rep['ouverture_haut'] = f'{cavity[:TH // 3].mean() * 100:.0f}%'
assert cavity[:TH // 3].sum() > 40
# identité PNG == calques == Aseprite, jour et nuit
for mode in ['jour', 'nuit']:
    target = np.array(Image.open(OUT / f'entree_foret_chemin_{mode}.png').convert('RGBA'))
    comp = np.zeros_like(target)
    for name, _ in names:
        comp = np.maximum(comp, np.array(Image.open(CAL / f'{name}_{mode}.png').convert('RGBA')))
    assert np.array_equal(comp, target), f'calques != png ({mode})'
    data = (OUT / f'entree_foret_chemin_{mode}.aseprite').read_bytes()
    size, magic, nf, w0, h0, depth, _flags = struct.unpack_from('<IHHHHHI', data)
    assert magic == 0xA5E0 and (w0, h0) == (TW, TH) and depth == 32 and nf == 1
    assert struct.unpack_from('<hhHH', data, 36) == (0, 0, 8, 8)
    fs, fm, nc, dt = struct.unpack_from('<IHHH', data, 128); assert fm == 0xF1FA
    pos = 144; cel = {}; nl = 0
    while pos < len(data):
        ln, kind = struct.unpack_from('<IH', data, pos); p = data[pos + 6:pos + ln]
        if kind == 0x2004: nl += 1
        if kind == 0x2005:
            k, x, y, opq, typ, zi = struct.unpack_from('<HhhBHh', p)
            cw, ch = struct.unpack_from('<HH', p, 16)
            cel[k] = (x, y, Image.frombytes('RGBA', (cw, ch), zlib.decompress(p[20:])))
        pos += ln
    assert nl == 3
    c = np.zeros_like(target)
    for _, (x, y, q) in sorted(cel.items()):
        cc = np.zeros_like(target); cc[y:y + q.height, x:x + q.width] = np.array(q); c = np.maximum(c, cc)
    assert np.array_equal(c, target), f'aseprite != png ({mode})'
# nuit = formule exacte du kit
jn = np.array(Image.open(OUT / 'entree_foret_chemin_jour.png').convert('RGBA')).astype(int)
nn = np.array(Image.open(OUT / 'entree_foret_chemin_nuit.png').convert('RGBA')).astype(int)
exp = np.rint(jn[:, :, :3] * NIGHT[0] + NIGHT[1]).clip(0, 255).astype(int)
assert np.array_equal(np.where(jn[:, :, 3:4] > 0, exp, 0), nn[:, :, :3] * (nn[:, :, 3:4] > 0)), 'formule nuit'
rep['verifications'] = {'calques_identiques': True, 'aseprite_identique': True, 'nuit_formule_kit': True,
                        'palette_28_max': len(pal) <= 28}
(D / 'controle_entree_foret.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2))
print('PASS —', json.dumps(rep, ensure_ascii=False))
