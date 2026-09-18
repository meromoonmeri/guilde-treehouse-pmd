"""V11 : suite d'animation SUBTLE des boreales, generee, sur son propre layer transparent,
a poser sur NOTRE ciel de zone (V3).
- Planche generee : 8 poses dessinees (2x4), memes rubans aux memes positions, seuls
  les coeurs brillent/battent subtilement et un shimmer voyage (harmonise a notre ciel).
- Extraction : magenta de bord et panneau navy cuits retires ; seuls les rubans lumineux
  (satures/lumineux) restent, comme pour les etoiles V3 et l'effet canonique V10.
- Animation : 16 etapes = 8 poses + 8 fondus 50 %, 120 ms (1,92 s), boucle exacte.
- Scene : ciel+etoiles V3 -> calque V11 pose une fois -> glace V8 -> terrain V3. Pas de wrap."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/boreales_suite_generee_v11'
V8 = R / 'renders/boreales_ondulation_glace_v8/calques'
BRUT = O / 'bruts/boreal_suite_8.png'
POSES, T, MS = 8, 16, 120      # 16 x 120 ms = 1,92 s

def extraire_pose(cell):
    """Separation GEOMETRIQUE : le fond est la zone connexe aux bords de la case
    (magenta + panneau navy cuit). Les rubans magenta profonds ne sont pas touches
    par une distance de couleur, qui les confondrait avec le fond."""
    rgb = cell.astype(float)
    lum = rgb.mean(axis=2); sat = rgb.max(axis=2) - rgb.min(axis=2)
    d_mag = np.linalg.norm(rgb - np.array([255.0, 0.0, 255.0]), axis=2)
    magenta_like = d_mag < 130
    navy_like = (lum < 60) & (sat < 50)
    fond_candidat = magenta_like | navy_like
    # inondation depuis les quatre bords : tout ce qui est atteignable sans traverser
    # un ruban (rim turquoise clair) est du fond
    bord = np.zeros_like(fond_candidat)
    bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
    fond = ndimage.binary_propagation(bord & fond_candidat, mask=fond_candidat)
    contenu = ~fond
    lab, n = ndimage.label(contenu)
    if n:
        tailles = np.bincount(lab.ravel()); tailles[0] = 0
        contenu = np.isin(lab, np.where(tailles >= 12)[0])
    # trous interieurs : navy enferme par un ruban -> voile opaque ; fissures magenta
    # enfermees -> restent transparentes (c'est du fond vu entre les franges)
    trous = ndimage.binary_fill_holes(contenu) & ~contenu
    labt, nt = ndimage.label(trous)
    if nt:
        frac_mag = ndimage.mean(magenta_like.astype(float), labt, range(1, nt + 1))
        ids = np.array([k + 1 for k in range(nt) if frac_mag[k] > 0.4])
        trous_fond = np.isin(labt, ids)
        contenu = contenu | (trous & ~trous_fond)
    alpha = np.where(contenu, 255, 0).astype('uint8')
    return alpha

def demeler(rgb, alpha, fond=np.array([255.0, 0.0, 255.0])):
    """Bords durs apres separation geometrique : leger adoucissement 1 px contre le magenta."""
    a = (alpha / 255.0)[..., None]
    fg = (rgb - (1 - a) * fond) / np.maximum(a, 0.35)
    return np.clip(np.where(alpha[:, :, None] > 0, fg, rgb), 0, 255)

def charger_poses():
    brut = Image.open(BRUT).convert('RGB')
    W, H = brut.size; cw, ch = W // 2, H // 4
    poses, tailles = [], []
    for i in range(POSES):
        col, lig = i % 2, i // 2
        cell = np.array(brut.crop((col * cw + 6, lig * ch + 6, (col + 1) * cw - 6, (lig + 1) * ch - 6)))
        alpha = extraire_pose(cell)
        rgb = demeler(cell.astype(float), alpha)
        rgba = np.dstack([rgb, alpha]).astype('uint8')
        rgba[rgba[:, :, 3] == 0] = 0
        ys, xs = np.where(rgba[:, :, 3] > 0)
        boite = (max(0, xs.min() - 2), max(0, ys.min() - 2), min(rgba.shape[1], xs.max() + 3), min(rgba.shape[0], ys.max() + 3))
        rgba = rgba[boite[1]:boite[3], boite[0]:boite[2]]
        poses.append(rgba); tailles.append(rgba.shape)
        Image.fromarray(rgba, 'RGBA').save(O / 'poses' / f'pose_{i:02d}.png')
    return poses, tailles

def canevas_pose(rgba, W=768, H=300):
    """Pose centree horizontalement sur un calque 768x300, bords fondus."""
    h, w = rgba.shape[:2]
    x0 = (W - w) // 2
    canevas = np.zeros((H, W, 4), 'uint8')
    canevas[0:min(H, h), x0:x0 + w] = rgba[0:min(H, h)]
    im = Image.fromarray(canevas, 'RGBA')
    a = np.array(im).astype(float)
    fondu = np.ones(W)
    fondu[:x0 + 2] = 0.0; fondu[x0 + w - 2:] = 0.0
    a[:, :, 3] *= fondu[None, :]
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a.astype('uint8'), 'RGBA')

def frames_suite(poses_canevas):
    """16 etapes : pose k (pair) puis fondu 50 % k->k+1 (impair). Boucle exacte."""
    out = []
    for k in range(POSES):
        A = np.array(poses_canevas[k]).astype(float)
        B = np.array(poses_canevas[(k + 1) % POSES]).astype(float)
        out.append(Image.fromarray(A.astype('uint8'), 'RGBA'))
        mel = np.dstack([np.rint((A[:, :, :3] * A[:, :, 3:4] + B[:, :, :3] * B[:, :, 3:4]) / np.maximum(A[:, :, 3:4] + B[:, :, 3:4], 1e-6)).clip(0, 255),
                         np.rint((A[:, :, 3] + B[:, :, 3]) / 2)]).astype('uint8')
        mel[mel[:, :, 3] == 0] = 0
        out.append(Image.fromarray(mel, 'RGBA'))
    return out

def scene_composee(t, ciel_merged, couches, glace, terrain, pos=(0, 0)):
    s = ciel_merged.copy()
    s.alpha_composite(couches[t % T], pos)
    s.alpha_composite(glace, (0, 0))
    s.alpha_composite(terrain, (0, 0))
    return s

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def construire():
    for d in ['poses', 'couches', 'review', 'scene', 'contexte']:
        (O / d).mkdir(parents=True, exist_ok=True)
    poses, tailles = charger_poses()
    canevas = [canevas_pose(p) for p in poses]
    couches = frames_suite(canevas)
    for t, im in enumerate(couches):
        im.save(O / 'couches' / f'BorealeSuiteV11_frame_{t:02d}.png')
    couches[0].save(O / 'boreale_suite_16frames.webp', save_all=True, append_images=couches[1:], duration=MS, loop=0, lossless=True, method=4)
    planche = Image.new('RGBA', (384, 150 * 8), (12, 16, 30, 255))
    for t, im in enumerate(couches[::2]):
        planche.alpha_composite(im.resize((384, 150), Image.Resampling.NEAREST), (0, 150 * t))
    planche.convert('RGB').save(O / 'review/planche_poses.png')
    contexte = {'ciel_genere': V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': V8 / 'AreneLargeV3_00b_etoiles.png',
                'glace_laterale': V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': V8 / 'AreneLargeV3_02_sol_visible.png'}
    for nom, src in contexte.items():
        shutil.copy2(src, O / 'contexte' / f'{nom}.png')
    ciel_merged = Image.open(contexte['ciel_genere']).convert('RGBA')
    ciel_merged.alpha_composite(Image.open(contexte['etoiles']).convert('RGBA'))
    glace = Image.open(contexte['glace_laterale']).convert('RGBA')
    terrain = Image.open(contexte['terrain']).convert('RGBA')
    for t in (0, 4, 8, 12):
        scene_composee(t, ciel_merged, couches, glace, terrain).save(O / 'scene' / f'scene_{t:02d}.png')
    palette_image = Image.new('RGB', (384, 256 * 4))
    for i, t in enumerate((0, 4, 8, 12)):
        palette_image.paste(scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)), (0, 256 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)).quantize(palette=pal, dither=Image.Dither.NONE) for t in range(T)]
    gifs[0].save(O / 'review/scene_suite_gif.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fond_nuit = Image.new('RGBA', (384, 150), (10, 12, 26, 255))
    gs = []
    for t in range(T):
        g = Image.new('RGBA', (384, 150), (10, 12, 26, 255)); g.alpha_composite(couches[t].resize((384, 150), Image.Resampling.NEAREST)); gs.append(g.convert('RGB'))
    gs[0].save(O / 'review/suite_seule.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(ciel_merged), 'glace': uri(glace), 'terrain': uri(terrain), 'couches': [uri(im) for im in couches]}
    (R / 'apercu_boreale_suite_generee_v11.html').write_text(
        (R / 'source/boreales_suite_generee_v11/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'planche': {'brut_sha256': hashlib.sha256(BRUT.read_bytes()).hexdigest(),
                    'generee_avec': ['aurorepmdsky.png (texture canonique)', 'notre ciel V3 (harmonisation)'],
                    'poses_dessinees': POSES, 'grille_reelle': [2, 4]},
        'extraction': 'magenta de bord et panneau navy cuits retires ; rubans lumineux (sat/lum), petites composantes enlevees, demelage magenta, recadrage, calque 768x300 centre, bords fondus',
        'suite': {'etapes': T, 'poses': POSES, 'fondus': '50 % entre poses adjacentes (etapes impaires)', 'duree_ms': MS,
                  'cycle_s': round(T * MS / 1000, 2), 'subtilite': 'seuls coeurs/shimmer/franges varient ; positions de rubans identiques',
                  'boucle': 'exacte : 16 etapes periodiques, etape 16 = etape 0'},
        'pose_scena': 'calque pose une fois a (0,0) sur 768x512 entre ciel V3+etoiles et glace V8+terrain V3',
        'contexte': 'V3/V8 byte-identiques', 'wrap': False,
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cycle_officiel': 'INCONNU : suite dessinee et cadencee par nous'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
