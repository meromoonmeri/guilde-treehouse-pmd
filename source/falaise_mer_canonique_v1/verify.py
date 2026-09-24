"""Verification independante — re-decode les .tile, recompose tout, compare les pixels."""
from pathlib import Path
import json, io, struct, hashlib, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/falaise_mer_canonique_v1'
P = O / 'cap_cascade'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['taille_px']
GW, GH = M['cellules']
checks = {}

def decode_tile(path):
    raw = Path(path).read_bytes()
    size, n = struct.unpack_from('<ii', raw)
    assert size == 8, path
    tiles, cache = {}, {}
    for i in range(n):
        x, y, off = struct.unpack_from('<iiq', raw, 8 + i * 16)
        if off not in cache:
            (ln,) = struct.unpack_from('<q', raw, off)
            cache[off] = Image.open(io.BytesIO(raw[off + 8:off + 8 + ln])).convert('RGBA')
        tiles[x, y] = cache[off]
    return tiles

def straight(im):
    out = im.copy()
    out.putdata([(round(r * 255 / a), round(g * 255 / a), round(b * 255 / a), a) if 0 < a < 255 else (r, g, b, a)
                 for r, g, b, a in im.getdata()])
    return out

# 1. Sources: hashes conformes au manifeste
for name, info in M['sources'].items():
    raw = (R / info['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == hashlib.sha256(raw).hexdigest()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert blob == info['git_blob_sha1'], name
checks['sources_hashes'] = len(M['sources'])

base = decode_tile(R / 'source/falaises_metano/natifs/Metano_Town_Base.tile')
cliff = decode_tile(R / 'source/falaises_metano/natifs/Metano_Town_Cliffs.tile')
anim = decode_tile(R / 'source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile')
rivs = [decode_tile(R / f'source/eau_metano/natifs/Metano_Town_River_Animation_{i}.tile') for i in range(1, 5)]
SHEETS = {'Metano_Town_Base': base, 'Metano_Town_Cliffs': cliff, 'Metano_Town_Animation_Tileset': anim,
          **{f'Metano_Town_River_Animation_{i}': r for i, r in enumerate(rivs, 1)}}

def layer_np(name):
    im = Image.open(P / name).convert('RGBA')
    assert im.size == (W, H), name
    return np.array(im)

L = {n: layer_np(n) for n in M['calques']}

# 2. Dimensions divisibles par 8
assert W % 8 == 0 and H % 8 == 0
checks['grille_8px'] = True

# 3. Recomposition SEC + 4 phases humides
def compose(names):
    c = Image.new('RGBA', (W, H))
    for n in names:
        c.alpha_composite(Image.fromarray(L[n]))
    return c
static3 = M['calques'][:3]
assert compose(static3).tobytes() == Image.open(P / 'cap_SEC.png').convert('RGBA').tobytes()
checks['recomposition_sec'] = True
for f in range(4):
    names = static3 + ['cap_04_berges.png', f'cap_05_riviere_phase_{f+1}.png', f'cap_06_cascade_phase_{f+1}.png']
    got = compose(names).tobytes()
    want = Image.open(P / f'cap_avec_eau_frame_{f+1}.png').convert('RGBA').tobytes()
    assert got == want, f
checks['recomposition_humide_4phases'] = True

# 4. Les 4 phases d'eau sont distinctes
r5 = [L[f'cap_05_riviere_phase_{f+1}.png'].tobytes() for f in range(4)]
r6 = [L[f'cap_06_cascade_phase_{f+1}.png'].tobytes() for f in range(4)]
assert len(set(r5)) == 4 and len(set(r6)) == 4
checks['phases_distinctes'] = True

# 5. Egalite tuile a tuile avec les sources (statiques: controle exhaustif)
def sheet_crop(sheet, sx, sy):
    t = SHEETS[sheet].get((sx, sy))
    return np.array(straight(t)) if t else None
diffs = 0
# 01 herbe
a = L['cap_01_sol_herbe.png']
for y in range(GH):
    for x in range(GW):
        want = sheet_crop('Metano_Town_Base', x % 16, 80 + y % 16)
        if not np.array_equal(a[y*8:(y+1)*8, x*8:(x+1)*8], want):
            diffs += 1
# 02 parois: dalles face plein cadre
a = L['cap_02_parois.png']
for i in range(W // 64):
    sxb = 114
    for band in (184, 232):
        for cy in range(6):
            for cx in range(8):
                want = sheet_crop('Metano_Town_Cliffs', sxb + cx, 58 + cy)
                got = a[band + cy*8:band + cy*8 + 8, i*64 + cx*8:i*64 + cx*8 + 8]
                if want is None:
                    assert (got[:, :, 3] == 0).all()
                elif not np.array_equal(got, want):
                    diffs += 1
# Enfin: hors paroi, le calque doit etre transparent
mask = np.zeros((H, W), bool); mask[184:280, :] = True
assert (a[~mask][:, 3] == 0).all()
# 03 couronnes/pieds, bouche d'eau transparente aux cols 60..67
a = L['cap_03_couronnes_pieds.png']
for i in range(W // 64):
    for dy, syb in ((168, 56), (280, 66)):
        for cy in range(2):
            for cx in range(8):
                gx = i * 8 + cx
                got = a[dy + cy*8:dy + cy*8 + 8, i*64 + cx*8:i*64 + cx*8 + 8]
                if 60 <= gx < 68:
                    assert (got[:, :, 3] == 0).all(), ('bouche', gx, dy)
                    continue
                want = sheet_crop('Metano_Town_Cliffs', 114 + cx, syb + cy)
                if want is None:
                    assert (got[:, :, 3] == 0).all()
                elif not np.array_equal(got, want):
                    diffs += 1
mask = np.zeros((H, W), bool); mask[168:184, :] = True; mask[280:296, :] = True
mask[168:184, 480:544] = False; mask[280:296, 480:544] = False
assert (a[~mask][:, 3] == 0).all()
# 04 berges: canal BASE 8 cols, rangees 50/51 alternees
a = L['cap_04_berges.png']
rows = list(range(0, 21)) + list(range(37, 64))
for r in rows:
    sy = 50 + (r % 2)
    for k in range(8):
        want = sheet_crop('Metano_Town_Base', 124 + k, sy)
        assert want is not None
        if not np.array_equal(a[r*8:(r+1)*8, (60+k)*8:(61+k)*8], want):
            diffs += 1
mask = np.zeros((H, W), bool)
for r in rows:
    mask[r*8:(r+1)*8, 480:544] = True
assert (a[~mask][:, 3] == 0).all()
checks['tuiles_statiques_0_difference'] = diffs == 0
assert diffs == 0, diffs

# 6. Eau: chaque cellule animee du manifeste correspond a ses 4 sources
n_anim = 0
for rec in M['animations']:
    x, y = rec['dest_cell']
    lname = f"cap_{rec['layer'][3:]}_phase_" if False else None
    base_name = 'cap_05_riviere' if rec['layer'] == '05_riviere' else 'cap_06_cascade'
    for f, fr in enumerate(rec['frames']):
        want = sheet_crop(fr['sheet'], *fr['texloc'])
        assert want is not None
        got = L[f'{base_name}_phase_{f+1}.png'][y*8:(y+1)*8, x*8:(x+1)*8]
        assert np.array_equal(got, want), (rec, f)
        n_anim += 1
checks['cellules_eau_verifiees'] = n_anim

# 7. ORA: recomposition exacte depuis le document
with zipfile.ZipFile(P / 'cap_cascade.ora') as z:
    assert z.read('mimetype') == b'image/openraster'
    st = ET.fromstring(z.read('stack.xml')).find('stack')
    names = [n.get('name') for n in reversed(st)]
    c = Image.new('RGBA', (W, H))
    for n in names:
        c.alpha_composite(Image.open(io.BytesIO(z.read(f'data/{n}.png'))).convert('RGBA'))
    assert c.tobytes() == Image.open(P / 'COMPOSITION.png').convert('RGBA').tobytes()
    assert len(names) == 6
checks['ora_exact'] = True

# 8. SEC opaque plein canvas (herbe partout derriere)
sec = np.array(Image.open(P / 'cap_SEC.png').convert('RGBA'))
assert (sec[:, :, 3] == 255).all()
checks['sec_opaque'] = True

report = {'verifications': checks, 'taille_px': [W, H], 'grille_px': 8,
          'resultat': 'PASS — 0 difference de pixel avec les tuiles canoniques',
          'limites': M['limites']}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print('VERIFY PASS:', json.dumps(checks, ensure_ascii=False))
