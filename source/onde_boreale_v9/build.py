"""V9 : 10 frames de l'aurore, chacune sur son propre calque, animées par une vraie
logique d'onde transversale : la matière ne bouge que VERTICALEMENT, la phase de l'onde
voyage horizontalement le long du rideau (comme une corde qui ondule).
- Deux trains d'ondes : principal 2 longueurs d'onde sur la largeur (amplitude 12 px),
  secondaire 5 longueurs d'onde (amplitude 5 px) — nombres entiers => cohérence bord à bord.
- Chaque train effectue exactement 1 (resp. 5) cycle(s) temporel(s) sur les 10 frames :
  frame 10 = frame 0, boucle fermée exacte.
- Méthode habituelle : dessin maître généré fond magenta/blanc -> extraction alpha ->
  calques séparés -> scène 768x512 (ciel V3 + glace V8 + aurore + terrain V3) -> tests -> ZIP."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/onde_boreale_v9'
V8 = R / 'renders/boreales_ondulation_glace_v8/calques'
V3 = R / 'renders/arene_glace_large_v3'
BRUT = O / 'bruts/rideau_maitre.png'
T = 10
MS = 160                      # 10 x 160 ms = 1,6 s
W, H = 768, 256
AMP1, L1 = 12.0, 2            # amplitude et nombre de longueurs d'onde (train principal)
AMP2, L2, PH2 = 5.0, 5, 0.35  # train secondaire

def phase(x, t):
    """Phase de l'onde au point x, frame t : la phase voyage vers les x croissants."""
    u = x / W
    return (2 * np.pi * (L1 * u - t / T), 2 * np.pi * (L2 * u - t / T + PH2 / (2 * np.pi)))

def amplitude(x):
    """Enveloppe : onde amortie sur les 48 px de chaque bord pour ne pas cisailler les bords."""
    return np.minimum(1.0, np.minimum(x / 48.0, (W - 1 - x) / 48.0).clip(0, 1))

def decalage(x, t):
    d1 = AMP1 * np.sin(2 * np.pi * (L1 * x / W - t / T))
    d2 = AMP2 * np.sin(2 * np.pi * (L2 * x / W - t / T) + PH2)
    return d1 + d2

def extraire_master():
    rgb = np.array(Image.open(BRUT).convert('RGB')).astype(float)
    # fonds possibles : blanc, magenta, et lavande tres pale (le generateur a varye le bas)
    lum = rgb.mean(axis=2); sat = rgb.max(axis=2) - rgb.min(axis=2)
    clair_pale = (lum > 183) & (sat < 62)
    lab, n = ndimage.label(clair_pale)
    fonds = np.zeros(lum.shape, bool)
    if n:
        tailles = np.bincount(lab.ravel()); tailles[0] = 0
        grandes = np.where(tailles >= 1500)[0]
        fonds = np.isin(lab, grandes)
    # alpha brut : distance aux fonds ; coeur sombre/sature rempli par fermeture de voile
    dist = np.linalg.norm(rgb - np.where(fonds[..., None], rgb.mean(axis=2)[..., None], rgb), axis=2) if False else None
    d = np.stack([np.linalg.norm(rgb - bgc, axis=2) for bgc in (np.array([255., 255., 255.]), np.array([255., 0., 255.]), np.array([210., 180., 235.]))], 0).min(0)
    alpha = np.clip((d - 60) * 3.0, 0, 255)
    alpha[fonds] = 0
    contenu = alpha > 60
    lab2, n2 = ndimage.label(contenu)
    if n2 > 1:
        tailles2 = np.bincount(lab2.ravel()); tailles2[0] = 0
        contenu = lab2 == tailles2.argmax()
    plein = ndimage.binary_fill_holes(contenu) & ~fonds & (d >= 60)
    alpha = np.where(plein & (alpha < 90), np.maximum(alpha, 160), alpha)
    alpha = np.where(~plein, 0, alpha)
    alpha = ndimage.binary_propagation(plein, mask=alpha > 0) * alpha if False else alpha
    # demelange : fond le plus proche (blanc / magenta / lavande) par transformee de distance
    a = alpha / 255.0
    _, idx = ndimage.distance_transform_edt(~fonds, return_indices=True)
    B = rgb[idx[0], idx[1]]
    bord = (a > 0) & (a < 0.98)
    with np.errstate(invalid='ignore', divide='ignore'):
        fg = np.where(bord[..., None] & (a[..., None] > 0.02), (rgb - (1 - a[..., None]) * B) / np.maximum(a[..., None], 0.02), rgb)
    rgba = np.dstack([np.clip(fg, 0, 255), alpha]).astype('uint8')
    rgba[rgba[:, :, 3] == 0] = 0
    # cadrage vertical du rideau, puis reduction x0,5 et placement dans 768x256
    lignes = np.where((rgba[:, :, 3] > 0).any(axis=1))[0]
    haut, bas = max(0, lignes.min() - 16), min(rgba.shape[0], lignes.max() + 17)
    im = Image.fromarray(rgba, 'RGBA').crop((0, haut, 1536, bas))
    im = im.resize((W, min(H, round(im.height * W / im.width))), Image.Resampling.NEAREST)
    canevas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canevas.alpha_composite(im, (0, (H - im.height) // 2))
    return canevas

def couche_deplacee(master, t):
    """Deplace chaque colonne verticalement de round(decalage) : onde transversale pure."""
    m = np.array(master)
    out = np.zeros_like(m)
    for x in range(W):
        d = int(round(decalage(x, t) * amplitude(x)))
        col = m[:, x, :].copy()
        if d > 0:
            out[d:, x, :] = col[:H - d]
        elif d < 0:
            out[:H + d, x, :] = col[-d:]
        else:
            out[:, x, :] = col
    return Image.fromarray(out, 'RGBA')

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
    for d in ['couches', 'review', 'scene', 'contexte']:
        (O / d).mkdir(parents=True, exist_ok=True)
    master = extraire_master()
    master.save(O / 'rideau_master_extrait.png')
    couches = [couche_deplacee(master, t) for t in range(T)]
    for t, im in enumerate(couches):
        im.save(O / 'couches' / f'OndeBorealeV9_frame_{t:02d}.png')
    couches[0].save(O / 'onde_boreale_10frames.webp', save_all=True, append_images=couches[1:], duration=MS, loop=0, lossless=True, method=4)
    planche = Image.new('RGBA', (W // 2, (H // 2) * T), (12, 16, 30, 255))
    for t, im in enumerate(couches):
        petit = im.resize((W // 2, H // 2), Image.Resampling.NEAREST)
        planche.alpha_composite(petit, (0, (H // 2) * t))
    planche.convert('RGB').save(O / 'review/planche_10_couches.png')
    contexte = {'ciel_genere': V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': V8 / 'AreneLargeV3_00b_etoiles.png',
                'glace_laterale': V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': V8 / 'AreneLargeV3_02_sol_visible.png'}
    for nom, src in contexte.items():
        shutil.copy2(src, O / 'contexte' / f'{nom}.png')
    ciel_merged = Image.open(V8 / 'AreneLargeV3_00_ciel_genere.png').convert('RGBA')
    ciel_merged.alpha_composite(Image.open(V8 / 'AreneLargeV3_00b_etoiles.png').convert('RGBA'))
    glace = Image.open(V8 / 'V8_glace_laterale_arriere_plan.png').convert('RGBA')
    terrain = Image.open(V8 / 'AreneLargeV3_02_sol_visible.png').convert('RGBA')
    for t in (0, 3, 6, 9):
        scene_composee(t, ciel_merged, couches, glace, terrain).save(O / 'scene' / f'scene_{t:02d}.png')
    palette_image = Image.new('RGB', (384, 256 * 4))
    for i, t in enumerate((0, 3, 6, 9)):
        palette_image.paste(scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)), (0, 256 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)).quantize(palette=pal, dither=Image.Dither.NONE) for t in range(T)]
    gifs[0].save(O / 'review/scene_onde_gif.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fond_nuit = Image.new('RGBA', (W // 2, H // 2), (10, 12, 26, 255))
    gifs_au = [fond_nuit.copy() for _ in range(T)]
    for t, im in enumerate(couches):
        gifs_au[t].alpha_composite(im.resize((W // 2, H // 2), Image.Resampling.NEAREST))
    gifs_au[0].convert('RGB').save(O / 'review/aurore_seule.gif', save_all=True, append_images=[g.convert('RGB') for g in gifs_au[1:]], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(ciel_merged), 'glace': uri(glace), 'terrain': uri(terrain),
               'couches': [uri(im) for im in couches]}
    (R / 'apercu_onde_boreale_v9.html').write_text(
        (R / 'source/onde_boreale_v9/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'master': {'brut_sha256': hashlib.sha256(BRUT.read_bytes()).hexdigest(), 'extrait': 'rideau_master_extrait.png (768x256, plus grande composante, voile interieur rempli, fonds blanc/magenta/lavande retires par composantes, bords demeles contre le fond le plus proche)'},
        'onde': {'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
                 'physique': 'onde transversale : deplacement STRICTEMENT vertical de chaque colonne, phase voyageant horizontalement ; train principal 2 longueurs d\'onde (amplitude 12 px) + secondaire 5 longueurs d\'onde (5 px), enveloppe de bord 48 px',
                 'boucle': 'phases a periodes entieres en x et t : frame 10 = frame 0 exactement',
                 'layers': 'chaque frame est un calque independant couches/OndeBorealeV9_frame_XX.png (768x256 RGBA)'},
        'contexte': {'ciel': 'V3+V8 byte-identique', 'glace': 'V8 byte-identique', 'terrain': 'V3 (AreneLargeV3_02_sol_visible) byte-identique'},
        'wrap': False, 'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cycle_officiel': 'INCONNU : onde dessinee et cadencee par nous, pas le cycle du jeu'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
