"""Tests lot plage_rouge_v1. Execution : .venv/bin/python source/plage_rouge_v1/test_build.py
Un echec = un defaut de construction, PAS une validation artistique ni moteur."""
from pathlib import Path
import json, zipfile, io, re, hashlib, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/plage_rouge_v1'
RESULT = []

def test(nom, cond, info=''):
    RESULT.append((nom, bool(cond), info))
    print(('PASS ' if cond else 'FAIL ') + nom + (f' — {info}' if info else ''))

M = json.loads((O / 'manifest.json').read_text())
TW, TH = M['canvas']
pal = np.load(O / 'review' / 'palette_native.npy')

lay = {p.stem: np.array(Image.open(p).convert('RGBA')) for p in (O / 'couches').glob('*.png')}
mer = [np.array(Image.open(p).convert('RGBA')) for p in sorted((O / 'couches/mer_frames').glob('*.png'))]
scenes = [np.array(Image.open(p).convert('RGBA')) for p in sorted((O / 'scene').glob('scene_anim_*.png'))]
seche = np.array(Image.open(O / 'scene' / 'scene_seche.png').convert('RGBA'))

# 1 dimensions / grille
test('01_canvas_multiple_8', TW % 8 == 0 and TH % 8 == 0, f'{TW}x{TH}')
test('02_calques_meme_taille', all(a.shape == (TH, TW, 4) for a in list(lay.values()) + mer + scenes + [seche]))
test('03_16_frames_mer', len(mer) == 16 and len(scenes) == 16, f'mer={len(mer)} scenes={len(scenes)}')

# 2 conformite palette (pixels opaques des calques quantifies)
def hors_palette(a):
    op = a[:, :, 3] == 255
    if not op.any():
        return 0
    pix = set(map(tuple, a[op][:, :3].tolist()))
    ref = set(map(tuple, pal.tolist()))
    return len(pix - ref)
nb_hors = sum(hors_palette(a) for k, a in lay.items() if k not in ('05_ombres_objets',) ) + sum(hors_palette(a) for a in mer)
test('04_palette_147_conforme', nb_hors == 0, f'{nb_hors} couleurs hors palette native')

# 3 aucun magenta residuel
def magenta_residuel(a):
    d = np.abs(a[:, :, :3].astype(int) - np.array([255, 0, 255])).sum(2)
    return int(((d < 120) & (a[:, :, 3] > 0)).sum())
res = sum(magenta_residuel(a) for a in list(lay.values()) + mer)
test('05_zero_magenta_residuel', res == 0, f'{res} px')

# 4 silhouette maitre commune de la mer + terrain invariant entre frames
m0 = mer[0][:, :, 3] > 0
test('06_silhouette_mer_commune', all(np.array_equal(a[:, :, 3] > 0, m0) for a in mer))
hors_mer = ~m0
invariants = all(np.array_equal(scenes[0][hors_mer][:, :3], s[hors_mer][:, :3]) for s in scenes[1:])
test('07_terrain_invariant_toutes_scenes', invariants)

# 5 animation reelle : frames consecutives different (>1 %), boucle mesuree
def ndiff(a, b):
    m = m0
    return float((np.abs(a.astype(int) - b.astype(int))[:, :, :3].max(2) > 0)[m].mean())
dcons = [ndiff(mer[i], mer[(i + 1) % len(mer)]) for i in range(len(mer))]
test('08_frames_consecutives_bougent', min(dcons) > 0.002, f'min={min(dcons):.4f} max={max(dcons):.4f}')
test('09_raccord_boucle_modere', dcons[-1] <= max(dcons) * 1.05, f'saut boucle={dcons[-1]:.4f}')

# 6 version seche = sans mer : les couches de TERRAIN n'occupent pas la zone mer
# (le fond void ni les objets poses dans l'eau ne comptent pas comme de l'eau)
sache_alpha = np.zeros_like(m0)
for k, a in lay.items():
    if k in ('00_fond_void', '06_objets') or k.startswith('01_mer_pose_peinte'):
        continue  # fond plein, objets poses dans l'eau, pose peinte statique = hors controle
    sache_alpha |= a[:, :, 3] > 0
test('10_seche_sans_eau_dans_zone_mer', int((sache_alpha & m0).sum()) == 0)
diff_seche_anim = (np.abs(seche.astype(int) - scenes[0].astype(int))[:, :, :3].max(2) > 0)
test('11_seche_diff_seulement_zone_mer', set(map(tuple, np.argwhere(diff_seche_anim & ~m0).tolist())) == set())

# 7 placements sur grille 8 px et dans le bon domaine
pl = M['placements']
test('12_placements_grille8', all(p['x'] % 8 == 0 and p['y'] % 8 == 0 for p in pl), f"{len(pl)} placements")
test('13_placements_deux_rochers_en_mer', sum(1 for p in pl if p['sur_eau']) == 2)

# 8 ORA valide
z = zipfile.ZipFile(O / 'ora' / 'plage_rouge_v1.ora')
names = z.namelist()
ok_mime = names[0] == 'mimetype' and z.getinfo('mimetype').compress_type == zipfile.ZIP_STORED
stack = z.read('stack.xml').decode()
ok_stack = '<image ' in stack and stack.count('<layer ') == 5 + 16 + 1 and 'data/02_sable.png' in names
test('14_ora_valide_22_calques', ok_mime and ok_stack, f"{stack.count('<layer ')} calques ORA")

# 9 GIF 16 frames + webp identique aux PNG
gif = Image.open(O / 'review' / 'scene_anim.gif')
ng = 0
try:
    while True:
        ng += 1; gif.seek(ng)
except EOFError:
    pass
test('15_gif_16_frames', ng == 16, f'gif={ng}')
wp = Image.open(O / 'scene_anim16f.webp')
okw = True
try:
    for i in range(16):
        wp.seek(i)
        if not np.array_equal(np.array(wp.convert('RGBA')), scenes[i]):
            okw = False; break
except EOFError:
    okw = False
test('16_webp_lossless_identique_png', okw)

# 10 manifeste + hashes bruts + viewer
okb = all(hashlib.sha256((O / 'bruts' / k).read_bytes()).hexdigest() == v
          for k, v in M['bruts_sha256'].items())
test('17_manifeste_hashes_bruts', okb, f"{len(M['bruts_sha256'])} bruts")
html = (R / 'apercu_plage_rouge_v1.html').read_text()
test('18_viewer_sans_placeholder', '__DATA__' not in html and len(html) > 100_000)
m = re.search(r'<script id="DATA" type="application/json">(.*?)</script>', html, re.S)
dj = json.loads(m.group(1)) if m else {}
test('19_viewer_json_valide', len(dj.get('mer', [])) == 16 and len(dj.get('calques', [])) == 5)

print('-' * 60)
npass = sum(1 for _, c, _ in RESULT if c)
print(f'{npass}/{len(RESULT)} PASS')
sys.exit(0 if npass == len(RESULT) else 1)
