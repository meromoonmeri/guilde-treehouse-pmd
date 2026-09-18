"""V14 : calques EXACTS de la reference + 15 frames de mouvement elegant de l'aurore.
- Meme decoupe que V13 mais les cristaux sombres de l'horizon (lum basse) vont au TERRAIN :
  l'aurore ne contient que les rubans lumineux satures. Recomposition = guide exact.
- 15 frames : la phase de la palette avance de 1/15 de cycle par frame, avec interpolation
  lineaire entre les arrets des rampes (cyan et magenta) -> changement de couleur doux et
  harmonieux, meme design, meme texture, geometrie jamais modifiee. Frame 0 = origine
  exacte ; frame 15 = frame 0 (cycle complet)."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/arene_guide_couches_v14'
GUIDE = R / 'source/ice_arena_aurora_v1/generation/layout_guide.png'
T, MS = 15, 120

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def extraire_calques():
    guide = np.array(Image.open(GUIDE).convert('RGB')).astype(float)
    H, W = guide.shape[:2]
    lum = guide.mean(axis=2); sat = guide.max(axis=2) - guide.min(axis=2)
    glace = (lum > 110) | ((sat < 45) & (lum > 95))
    bord = np.zeros((H, W), bool); bord[0, :] = True
    ciel_zone = ndimage.binary_propagation(bord & ~glace, mask=~glace)
    # aurore = rubans LUMINEUX satures uniquement ; cristaux sombres -> terrain
    aurore = ciel_zone & (sat > 80) & (lum > 55)
    lab, n = ndimage.label(aurore)
    if n:
        t = np.bincount(lab.ravel()); t[0] = 0
        aurore = np.isin(lab, np.where(t >= 40)[0])
    candidat = ciel_zone & ~aurore & (lum > 150) & (sat < 70)
    lab2, n2 = ndimage.label(candidat)
    etoiles = np.zeros((H, W), bool)
    if n2:
        t2 = np.bincount(lab2.ravel()); t2[0] = 0
        etoiles = np.isin(lab2, np.where((t2 >= 1) & (t2 <= 40))[0])
    ciel_masque = ciel_zone & ~aurore & ~etoiles
    def couche(m):
        out = np.zeros((H, W, 4), 'uint8')
        out[m, :3] = guide[m].astype('uint8')
        out[m, 3] = 255
        return out
    return guide, couche(ciel_masque), couche(etoiles), couche(~ciel_zone), couche(aurore), aurore

def frames_elegantes(aurore_rgba, aurore_masque):
    guide = aurore_rgba[:, :, :3].astype(float)
    masque = aurore_masque
    r, g, b = guide[:, :, 0], guide[:, :, 1], guide[:, :, 2]
    cyan_fam = masque & (g > r + 20)
    mag_fam = masque & ~cyan_fam
    idx = np.zeros(guide.shape[:2], 'int')
    rampes = {'cyan': [], 'magenta': []}
    for fam, base, cle in ((cyan_fam, 0, 'cyan'), (mag_fam, 4, 'magenta')):
        vals = guide[fam].mean(axis=1)
        qs = np.quantile(vals, [0.25, 0.5, 0.75])
        idx[fam] = base + np.searchsorted(qs, vals)
        for q in range(4):
            bm = fam & (idx == base + q)
            rampes[cle].append(np.array(guide[bm].mean(axis=0)) if bm.any() else np.zeros(3))
    CY, MG = rampes['cyan'], rampes['magenta']
    def couleur_decalee(rampe, base, f):
        """Couleur de chaque arret q pour la phase f/T : interpolation lineaire circulaire."""
        p = f / T * 4.0                      # un cycle complet sur T frames
        out = np.zeros((4, 3))
        for q in range(4):
            pos = (q + (3 if base == 0 else -3) * p / 4.0) % 4.0
            k, frac = int(pos), pos - int(pos)
            out[q] = rampe[k] * (1 - frac) + rampe[(k + 1) % 4] * frac
        return out
    frames = []
    for f in range(T):
        out = np.zeros_like(aurore_rgba)
        pal = np.vstack([couleur_decalee(CY, 0, f), couleur_decalee(MG, 4, f)])
        m = masque
        out[:, :, :3][m] = pal[idx[m]].astype('uint8')
        out[:, :, 3] = aurore_rgba[:, :, 3]
        if f == 0:                            # frame 0 = couleurs d'origine exactes
            out[:, :, :3] = aurore_rgba[:, :, :3]
        frames.append(Image.fromarray(out, 'RGBA'))
    return frames, [tuple(int(v) for v in c) for c in CY], [tuple(int(v) for v in c) for c in MG]

def construire():
    for d in ['couches/aurore', 'review', 'scene', 'guide']:
        (O / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(GUIDE, O / 'guide/layout_guide.png')
    guide, ciel, etoiles, terrain, aurore_rgba, masque = extraire_calques()
    Image.fromarray(ciel, 'RGBA').save(O / 'couches/ciel_fixe.png')
    Image.fromarray(etoiles, 'RGBA').save(O / 'couches/etoiles_fixes.png')
    Image.fromarray(terrain, 'RGBA').save(O / 'couches/terrain_fixe.png')
    frames, CY, MG = frames_elegantes(aurore_rgba, masque)
    for f, im in enumerate(frames):
        im.save(O / 'couches/aurore' / f'AuroreEleganteV14_frame_{f:02d}.png')
    frames[0].save(O / 'aurore_elegante_15frames.webp', save_all=True, append_images=frames[1:], duration=MS, loop=0, lossless=True, method=4)
    (O / 'palettes_15frames.json').write_text(json.dumps({
        'note': 'frame 0 = couleurs exactes du guide ; 15 frames = un cycle complet, interpolation lineaire entre arrets',
        'ramp_cyan': [list(c) for c in CY], 'ramp_magenta': [list(c) for c in MG]}, indent=2))
    def scene(f):
        s = Image.fromarray(ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(etoiles, 'RGBA'))
        s.alpha_composite(frames[f % T])
        s.alpha_composite(Image.fromarray(terrain, 'RGBA'))
        return s
    for f in (0, 5, 10):
        scene(f).save(O / 'scene' / f'scene_{f:02d}.png')
    palette_image = Image.new('RGB', (464, 576 * 3))
    for i, f in enumerate((0, 5, 10)):
        palette_image.paste(scene(f).convert('RGB').resize((464, 576)), (0, 576 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene(f).convert('RGB').resize((464, 576)).quantize(palette=pal, dither=Image.Dither.NONE) for f in range(T)]
    gifs[0].save(O / 'review/scene_15frames.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fond = Image.new('RGBA', (464, 576), (10, 12, 26, 255))
    gs = []
    for f in range(T):
        g2 = fond.copy(); g2.alpha_composite(frames[f].resize((464, 576), Image.Resampling.NEAREST)); gs.append(g2.convert('RGB'))
    gs[0].save(O / 'review/aurore_seule.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(Image.fromarray(ciel, 'RGBA')), 'etoiles': uri(Image.fromarray(etoiles, 'RGBA')),
               'terrain': uri(Image.fromarray(terrain, 'RGBA')), 'couches': [uri(im) for im in frames]}
    (R / 'apercu_arene_guide_couches_v14.html').write_text(
        (R / 'source/arene_guide_couches_v14/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'guide': {'sha256': hashlib.sha256(GUIDE.read_bytes()).hexdigest(), 'taille': [928, 1152]},
        'calques': {'ciel_fixe': 'navy sans aurore ni etoiles', 'etoiles_fixes': 'taches isolees',
                    'aurore': 'rubans lumineux satures uniquement (cristaux sombres au terrain)',
                    'terrain_fixe': 'murailles, cratere, chemin, cristaux d horizon'},
        'animation': {'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
                      'principe': 'changement de couleur harmonieux : phase 1/15 par frame, interpolation lineaire entre arrets des rampes ; meme design, meme texture, geometrie figee',
                      'frame0': 'couleurs exactes du guide', 'boucle': 'exacte : cycle complet en 15 frames'},
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
