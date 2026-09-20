"""Tests lot plage_rouge_v2_eoso (eau canonique EoSO + terrain V1 byte-identique).
Execution : .venv/bin/python source/plage_rouge_v2/test_build.py
Niveau : controle fichiers/pixels. PAS validation artistique ni moteur."""
from pathlib import Path
import json, zipfile, io, re, hashlib, struct, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/plage_rouge_v2_eoso'
V1 = R / 'renders/plage_rouge_v1'
REF = R / 'source/plage_rouge_v2/references'
RESULT = []

def test(nom, cond, info=''):
    RESULT.append((nom, bool(cond), info))
    print(('PASS ' if cond else 'FAIL ') + nom + (f' — {info}' if info else ''))

M = json.loads((O / 'manifest.json').read_text())
NB = M['eau']['frames']
MS = M['eau']['cadence_ms']
lay = {p.stem: np.array(Image.open(p).convert('RGBA')) for p in (O / 'couches').glob('*.png')}
mer = [np.array(Image.open(p).convert('RGBA')) for p in sorted((O / 'couches/mer_frames').glob('*.png'))]
canon = [np.array(Image.open(p).convert('RGBA')) for p in sorted((O / 'canonique').glob('*.png'))]
scenes = [np.array(Image.open(p).convert('RGBA')) for p in sorted((O / 'scene').glob('scene_eoso_*.png'))]
seche = np.array(Image.open(O / 'scene' / 'scene_seche.png').convert('RGBA'))
TW, TH = mer[0].shape[1], mer[0].shape[0]

test('01_17_frames_mer', len(mer) == 17 and len(scenes) == 17 and len(canon) == 17, f'{len(mer)}/{len(scenes)}/{len(canon)}')
test('02_canvas_multiple_8', TW % 8 == 0 and TH % 8 == 0, f'{TW}x{TH}')
test('03_tailles_uniformes', all(a.shape == (TH, TW, 4) for a in mer + scenes) and all(a.shape == canon[0].shape for a in canon))

# 4 terrain byte-identique au lot V1
okv1 = True
for nom in ['00_fond_void', '02_sable', '03_parois_falaises', '04_bordures_herbe', '05_ombres_objets', '06_objets']:
    a = hashlib.sha256((O / 'couches' / f'{nom}.png').read_bytes()).hexdigest()
    b = hashlib.sha256((V1 / 'couches' / f'{nom}.png').read_bytes()).hexdigest()
    okv1 &= (a == b)
test('04_terrain_byte_identique_V1', okv1)

# 5 provenance : redecodage du .tile == canonique/ == mapping du manifeste
d = (REF / 'beach_animation.tile').read_bytes()
test('05_tile_sha256_manifeste', hashlib.sha256(d).hexdigest() == M['eau']['tile_sha256'])
tileSize, count = struct.unpack_from('<ii', d, 0)
pos, cache, recs = 8, {}, []
for _ in range(count):
    x, y, off = struct.unpack_from('<iiq', d, pos); pos += 16
    if off not in cache:
        ln = struct.unpack_from('<q', d, off)[0]
        cache[off] = np.array(Image.open(io.BytesIO(d[off + 8:off + 8 + ln])).convert('RGBA'))
    recs.append((x, y, cache[off]))
okrec = True
for f in range(17):
    a = np.zeros_like(canon[0])
    for x, y, im in recs:
        if f * 33 <= x < (f + 1) * 33:
            a[y * tileSize:(y + 1) * tileSize, (x - f * 33) * tileSize:(x - f * 33 + 1) * tileSize] = im
    okrec &= np.array_equal(a, canon[f])
test('06_canonique_pixel_exact_du_tile', okrec)

# 6 mer natif sans magenta et pixels natifs (echantillon croise)
mag = 0
for a in mer:
    dmag = np.abs(a[:, :, :3].astype(int) - np.array([255, 0, 255])).sum(2)
    mag += int(((dmag < 60) & (a[:, :, 3] > 0)).sum())
test('07_mer_zero_magenta', mag == 0, f'{mag} px')

# 7 silhouette : opaques uniquement dans la zone mer V1, couverture >= 97 %
m0 = np.array(Image.open(V1 / 'couches/mer_frames/MerV1_00.png').convert('RGBA'))[:, :, 3] > 0
cont = 0; hors = 0
for a in mer:
    op = a[:, :, 3] > 0
    hors += int((op & ~m0).sum())
    cont += int((op & m0).sum())
couverture = cont / (m0.sum() * 17)
test('08_mer_dans_silhouette_et_couvre', hors == 0 and couverture >= 0.97, f'hors={hors} couverture={couverture:.4f}')

# 8 animation reelle et cadence documentee
d0 = np.abs(mer[0].astype(int) - mer[1].astype(int))[:, :, :3].max(2)
test('09_animation_reelle', (d0 > 0).sum() > 500, f'{(d0 > 0).sum()} px')
test('10_cadence_native_266ms', MS == 266 and M['eau']['frame_length_ticks_natif'] == 16)

# 9 terrain invariant toutes scenes + seche sans mer
hors_mer = ~m0
okinv = all(np.array_equal(scenes[0][hors_mer][:, :3], s[hors_mer][:, :3]) for s in scenes[1:])
test('11_terrain_invariant_scenes', okinv)
alpha_sec = np.zeros((TH, TW), bool)
for k, a in lay.items():
    if k in ('00_fond_void', '06_objets'):
        continue
    alpha_sec |= a[:, :, 3] > 0
test('12_seche_sans_eau_dans_zone_mer', int((alpha_sec & m0).sum()) == 0)

# 10 GIF/WebP/ORA/manifeste/viewer
gif = Image.open(O / 'review' / 'scene_eoso.gif'); ng = 0
try:
    while True:
        ng += 1; gif.seek(ng)
except EOFError:
    pass
test('13_gif_17_frames', ng == 17, f'gif={ng}')
wp = Image.open(O / 'scene_eoso17f.webp'); okw = True
for i in range(17):
    wp.seek(i)
    if not np.array_equal(np.array(wp.convert('RGBA')), scenes[i]):
        okw = False; break
test('14_webp_lossless_identique', okw)
z = zipfile.ZipFile(O / 'ora' / 'plage_rouge_v2_eoso.ora')
stack = z.read('stack.xml').decode()
test('15_ora_23_calques', stack.count('<layer ') == 23 and z.namelist()[0] == 'mimetype',
     f"{stack.count('<layer ')} calques")
html = (R / 'apercu_plage_rouge_v2.html').read_text()
mm = re.search(r'<script id="DATA" type="application/json">(.*?)</script>', html, re.S)
dj = json.loads(mm.group(1)) if mm else {}
test('16_viewer_17_frames', '__DATA__' not in html and len(dj.get('mer', [])) == 17)
test('17_apercu_copie_renders', (O / 'apercu.html').exists() and (O / 'apercu.html').read_text() == html)
prov = json.loads((REF / 'provenance.json').read_text())
test('18_provenance_commit_epingle', prov['commit'] == 'bed944992c32e7e7927cc3480c72edb0b1782e26')

print('-' * 60)
npass = sum(1 for _, c, _ in RESULT if c)
print(f'{npass}/{len(RESULT)} PASS')
sys.exit(0 if npass == len(RESULT) else 1)
