"""V12 : palette cycling Halcyon - planche generee 2x4, meme ruban, couleurs avancees d'un pas par frame.
Extraction : fond magenta par inondation depuis les bords. 8 calques 768x256, GIF + WebP + viewer."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/boreales_palette_cycling_v12'
BRUT = O / 'bruts/palette_cycle_8.png'
V8 = R / 'renders/boreales_ondulation_glace_v8/calques'
T, MS = 8, 120

def extraire(cell):
    rgb = cell.astype(float)
    d = np.linalg.norm(rgb - np.array([255.0, 0.0, 255.0]), axis=2)
    fond_c = d < 140
    bord = np.zeros_like(fond_c)
    bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
    fond = ndimage.binary_propagation(bord & fond_c, mask=fond_c)
    alpha = np.where(~fond, 255, 0).astype('uint8')
    lab, n = ndimage.label(alpha > 0)
    if n:
        t = np.bincount(lab.ravel()); t[0] = 0
        alpha = np.isin(lab, np.where(t >= 60)[0]).astype('uint8') * 255
    fg = np.clip((rgb - (1 - (alpha[..., None] / 255.0)) * np.array([255.0, 0.0, 255.0])) / np.maximum(alpha[..., None] / 255.0, 0.35), 0, 255)
    rgba = np.dstack([fg, alpha]).astype('uint8')
    rgba[rgba[:, :, 3] == 0] = 0
    return rgba

def aligner(frames):
    """Palette cycling exige une geometrie identique : aligne chaque frame sur la frame 0
    par recherche du decalage vertical minimisant la difference des masques alpha."""
    ref = (np.array(frames[0])[:, :, 3] > 128)
    out = [frames[0]]
    for im in frames[1:]:
        a = np.array(im)[:, :, 3] > 128
        meilleur, dy_min = None, 0
        for dy in range(-60, 61):
            decale = np.roll(a, dy, axis=0)
            d = np.count_nonzero(decale ^ ref)
            if meilleur is None or d < meilleur:
                meilleur, dy_min = d, dy
        arr = np.roll(np.array(im), dy_min, axis=0)
        if dy_min > 0:
            arr[:dy_min] = 0
        elif dy_min < 0:
            arr[dy_min:] = 0
        out.append(Image.fromarray(arr, 'RGBA'))
    return out

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def construire():
    for d in ['couches', 'review', 'scene', 'contexte']:
        (O / d).mkdir(parents=True, exist_ok=True)
    brut = Image.open(BRUT).convert('RGB')
    W, H = brut.size; cw, ch = W // 2, H // 4
    cell0 = np.array(brut.crop((6, 6, cw - 6, ch - 6)))
    rgba0 = Image.fromarray(extraire(cell0), 'RGBA').resize((768, 256), Image.Resampling.NEAREST)
    # --- vrai palette cycling : UNE image indexee, la palette tourne ---
    rgb = np.array(rgba0).astype(int)
    alpha = np.array(rgba0)[:, :, 3]
    masque = alpha > 128
    cyan_fam = masque & (rgb[:, :, 1] > rgb[:, :, 0] + 40)
    mag_fam = masque & ~cyan_fam
    CY = [(16, 96, 100), (24, 168, 168), (62, 226, 208), (176, 250, 242)]
    MG = [(64, 26, 100), (138, 30, 170), (212, 36, 210), (248, 120, 230)]
    SOMBRE = (18, 14, 52)
    idx = np.full(rgb.shape[:2], 8, 'uint8')          # 8 = corps sombre fixe
    for fam, base in ((cyan_fam, 0), (mag_fam, 4)):
        for x in range(768):
            ys = np.where(fam[:, x])[0]
            if not ys.size:
                continue
            rang = np.searchsorted(np.quantile(ys, [0.25, 0.5, 0.75]), ys)
            idx[ys, x] = base + rang                   # rampe ordonnee le long du ruban
    idx[masque & (masque.sum(0)[None, :] == 0)] = 8
    platte0 = CY + MG + [SOMBRE]
    def rendu(pal):
        p = np.array(pal, 'uint8')
        out = np.zeros((256, 768, 4), 'uint8')
        out[:, :, :3] = p[idx]
        out[:, :, 3] = alpha
        out[out[:, :, 3] == 0] = 0
        return out
    frames_img = []
    for f in range(T):
        pal = [CY[(i - f) % 4] for i in range(4)] + [MG[(i + f) % 4] for i in range(4)] + [SOMBRE]
        frames_img.append(Image.fromarray(rendu(pal), 'RGBA'))
    # asset indexe consommable (mode P + transparence par alpha separé) + palettes JSON
    pim = Image.new('P', (768, 256))
    pim.putpalette([v for c in platte0 for v in c] + [0] * (3 * (256 - len(platte0))))
    pim.putdata(idx.ravel().tolist())
    pim.save(O / 'onde_indexee.png')
    Image.fromarray(alpha, 'L').save(O / 'onde_alpha.png')
    (O / 'palettes_8frames.json').write_text(json.dumps({
        'frames': [[list(c) for c in ([CY[(i - f) % 4] for i in range(4)] + [MG[(i + f) % 4] for i in range(4)] + [SOMBRE])] for f in range(T)],
        'ramp_cyan': 'indices 0-3, +1/frame', 'ramp_magenta': 'indices 4-7, -1/frame (contre-courant)',
        'fixe': {'8': 'corps sombre'}, 'period': 4}, indent=2))
    frames = frames_img
    frames = aligner(frames)
    for i, im in enumerate(frames):
        im.save(O / 'couches' / f'PaletteCycleV12_frame_{i:02d}.png')
    frames[0].save(O / 'palette_cycling_8frames.webp', save_all=True, append_images=frames[1:], duration=MS, loop=0, lossless=True, method=4)
    fond = Image.new('RGBA', (768, 256), (14, 12, 34, 255))
    gs = []
    for f in range(T):
        g = fond.copy(); g.alpha_composite(frames[f]); gs.append(g.convert('RGB'))
    gs[0].save(O / 'review/palette_cycling.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    planche = Image.new('RGB', (384, 128 * T), (12, 16, 30))
    for f in range(T):
        planche.paste(gs[f].resize((384, 128), Image.Resampling.NEAREST), (0, 128 * f))
    planche.save(O / 'review/planche_8_frames.png')
    contexte = {'ciel_genere': V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': V8 / 'AreneLargeV3_00b_etoiles.png',
                'glace_laterale': V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': V8 / 'AreneLargeV3_02_sol_visible.png'}
    for nom, src in contexte.items():
        shutil.copy2(src, O / 'contexte' / f'{nom}.png')
    ciel = Image.open(contexte['ciel_genere']).convert('RGBA')
    ciel.alpha_composite(Image.open(contexte['etoiles']).convert('RGBA'))
    glace = Image.open(contexte['glace_laterale']).convert('RGBA')
    terrain = Image.open(contexte['terrain']).convert('RGBA')
    def scene(f):
        s = ciel.copy(); s.alpha_composite(frames[f], (0, 0)); s.alpha_composite(glace); s.alpha_composite(terrain)
        return s
    for f in (0, 2, 4, 6):
        scene(f).save(O / 'scene' / f'scene_{f:02d}.png')
    donnees = {'ciel': uri(ciel), 'glace': uri(glace), 'terrain': uri(terrain), 'couches': [uri(im) for im in frames]}
    (R / 'apercu_palette_cycling_v12.html').write_text(
        (R / 'source/boreales_palette_cycling_v12/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'style': 'palette cycling Halcyon authentique : une seule image indexee, rotation des rampes cyan/magenta, silhouette identique',
        'brut_sha256': hashlib.sha256(BRUT.read_bytes()).hexdigest(),
        'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
        'sans_ciel': True, 'wrap': False, 'contexte': 'V3/V8 byte-identiques',
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
