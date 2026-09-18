"""V13 : rebase sur le layout_guide.png de la V1 - scene en plusieurs calques separes,
aurore animee INDEPENDANTE du ciel par palette cycling (rameaux = vraies couleurs du guide).
Calques : ciel (fixe) / etoiles (fixes) / aurore (8 frames palette cycling) / terrain (fixe).
Frame 0 = guide exact : composite(frame 0) == layout_guide.png (test exact)."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/arene_guide_couches_v13'
GUIDE = R / 'source/ice_arena_aurora_v1/generation/layout_guide.png'
T, MS = 8, 120

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def extraire_calques():
    guide = np.array(Image.open(GUIDE).convert('RGB')).astype(float)
    H, W = guide.shape[:2]
    lum = guide.mean(axis=2); sat = guide.max(axis=2) - guide.min(axis=2)
    r, g, b = guide[:, :, 0], guide[:, :, 1], guide[:, :, 2]
    # glace/glace-clair : traverse-pas pour l'inondation du ciel
    glace = (lum > 110) | ((sat < 45) & (lum > 95))
    bord = np.zeros((H, W), bool); bord[0, :] = True
    ciel_zone = ndimage.binary_propagation(bord & ~glace, mask=~glace)
    aurore = ciel_zone & (sat > 80)
    lab, n = ndimage.label(aurore)
    if n:
        t = np.bincount(lab.ravel()); t[0] = 0
        aurore = np.isin(lab, np.where(t >= 40)[0])
    # etoiles : petites taches claires peu saturees dans la zone ciel
    candidat = ciel_zone & ~aurore & (lum > 150) & (sat < 70)
    lab2, n2 = ndimage.label(candidat)
    etoiles = np.zeros((H, W), bool)
    if n2:
        t2 = np.bincount(lab2.ravel()); t2[0] = 0
        etoiles = np.isin(lab2, np.where((t2 >= 1) & (t2 <= 40))[0])
    ciel_masque = ciel_zone & ~aurore & ~etoiles
    # calques RGBA (couleurs d'origine)
    def couche(masque):
        out = np.zeros((H, W, 4), 'uint8')
        out[masque, :3] = guide[masque].astype('uint8')
        out[masque, 3] = 255
        return out
    ciel = couche(ciel_masque)
    et = couche(etoiles)
    terrain = couche(~ciel_zone)
    au_rgb = guide.copy(); au_rgb[~aurore] = 0
    aurore_rgba = np.dstack([au_rgb, aurore.astype('uint8') * 255])
    return guide, ciel, et, terrain, aurore_rgba.astype('uint8'), aurore

def frames_aurore(aurore_rgba, aurore_masque):
    """Palette cycling : indices par famille (magenta/cyan) et quartile de luminosite ;
    frame 0 = couleurs d'origine ; frames 1-7 = rotation des couleurs de rampe."""
    guide = aurore_rgba[:, :, :3].astype(float)
    masque = aurore_masque
    r, g, b = guide[:, :, 0], guide[:, :, 1], guide[:, :, 2]
    cyan_fam = masque & (g > r + 20)
    mag_fam = masque & ~cyan_fam
    idx = np.zeros(guide.shape[:2], 'uint8')
    rampes = {'cyan': [], 'magenta': []}
    for fam, base, cle in ((cyan_fam, 0, 'cyan'), (mag_fam, 4, 'magenta')):
        vals = guide[fam].mean(axis=1)
        qs = np.quantile(vals, [0.25, 0.5, 0.75])
        idx[fam] = base + np.searchsorted(qs, vals)
        for q in range(4):
            bin_m = fam & (idx == base + q)
            rampes[cle].append(tuple(int(v) for v in guide[bin_m].mean(axis=0)) if bin_m.any() else (0, 0, 0))
    CY, MG = [tuple(c) for c in rampes['cyan']], [tuple(c) for c in rampes['magenta']]
    frames = [Image.fromarray(aurore_rgba, 'RGBA')]           # frame 0 = origine exacte
    for f in range(1, T):
        pal = [CY[(i - f) % 4] for i in range(4)] + [MG[(i + f) % 4] for i in range(4)]
        p = np.array([pal[i] for i in range(8)], 'uint8')
        out = np.zeros_like(aurore_rgba)
        out[:, :, :3] = p[idx]
        out[:, :, 3] = aurore_rgba[:, :, 3]
        frames.append(Image.fromarray(out, 'RGBA'))
    return frames, CY, MG

def construire():
    for d in ['couches/aurore', 'review', 'scene', 'guide']:
        (O / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(GUIDE, O / 'guide/layout_guide.png')
    guide, ciel, etoiles, terrain, aurore_rgba, masque_au = extraire_calques()
    Image.fromarray(ciel, 'RGBA').save(O / 'couches/ciel_fixe.png')
    Image.fromarray(etoiles, 'RGBA').save(O / 'couches/etoiles_fixes.png')
    Image.fromarray(terrain, 'RGBA').save(O / 'couches/terrain_fixe.png')
    frames, CY, MG = frames_aurore(aurore_rgba, masque_au)
    for f, im in enumerate(frames):
        im.save(O / 'couches/aurore' / f'AuroreGuideV13_frame_{f:02d}.png')
    frames[0].save(O / 'aurore_palette_cycle_8frames.webp', save_all=True, append_images=frames[1:], duration=MS, loop=0, lossless=True, method=4)
    (O / 'palettes_8frames.json').write_text(json.dumps({
        'frames': [[list(c) for c in ([CY[(i - f) % 4] for i in range(4)] + [MG[(i + f) % 4] for i in range(4)])] for f in range(T)],
        'note': 'frame 0 = couleurs d origine exactes du guide ; rampes derivees des vraies couleurs ; +1 cyan, -1 magenta', 'period': 4}, indent=2))
    # scene : ciel -> etoiles -> aurore(t) -> terrain
    def scene(f):
        s = Image.fromarray(ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(etoiles, 'RGBA'))
        s.alpha_composite(frames[f % T])
        s.alpha_composite(Image.fromarray(terrain, 'RGBA'))
        return s
    for f in (0, 2, 4, 6):
        scene(f).save(O / 'scene' / f'scene_{f:02d}.png')
    palette_image = Image.new('RGB', (464, 576 * 4))
    for i, f in enumerate((0, 2, 4, 6)):
        palette_image.paste(scene(f).convert('RGB').resize((464, 576)), (0, 576 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene(f).convert('RGB').resize((464, 576)).quantize(palette=pal, dither=Image.Dither.NONE) for f in range(T)]
    gifs[0].save(O / 'review/scene_guide_animee.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fond = Image.new('RGBA', (464, 576), (10, 12, 26, 255))
    gs = []
    for f in range(T):
        g2 = fond.copy(); g2.alpha_composite(frames[f].resize((464, 576), Image.Resampling.NEAREST)); gs.append(g2.convert('RGB'))
    gs[0].save(O / 'review/aurore_seule.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(Image.fromarray(ciel, 'RGBA')), 'etoiles': uri(Image.fromarray(etoiles, 'RGBA')),
               'terrain': uri(Image.fromarray(terrain, 'RGBA')), 'couches': [uri(im) for im in frames]}
    (R / 'apercu_arene_guide_couches_v13.html').write_text(
        (R / 'source/arene_guide_couches_v13/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'guide': {'source': 'source/ice_arena_aurora_v1/generation/layout_guide.png', 'taille': [928, 1152],
                  'sha256': hashlib.sha256(GUIDE.read_bytes()).hexdigest()},
        'calques': {'ciel_fixe': 'navy inonde depuis le haut, sans aurore ni etoiles',
                    'etoiles_fixes': 'petites taches claires isolees (1-40 px)',
                    'aurore': 'pixels satures de la zone ciel ; 8 frames palette cycling ; frame 0 = origine exacte',
                    'terrain_fixe': 'tout le reste (murailles, cratere, chemin)'},
        'animation': {'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
                      'principe': 'aurore independante du ciel : palette cycling des rampes (cyan +1, magenta -1) ; ciel/etoiles/terrain figes',
                      'boucle': 'exacte (periode 4 | 8)'},
        'frame0_egale_guide': True, 'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
