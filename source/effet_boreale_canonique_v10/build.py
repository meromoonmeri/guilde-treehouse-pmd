"""V10 : effet onde boreale CANONIQUE, sur son propre layer, sans ciel derriere.
- La texture est recuperee depuis la reference canonique aurorepmdsky.png (ciel boreal PMD Sky
  fourni) : extraction des rubans LUMINEUX uniquement, comme pour les etoiles V3.
  Le ciel sombre (lum~21, sat~63) est retire, les etoiles (petites taches) sont exclues :
  aucun ciel bake dans le calque, uniquement l'effet lumineux boreal.
- Animation : onde transversale pure (deplacement vertical par colonne, phase voyageant
  horizontalement, periodes entieres 2+5, boucle exacte en 10 frames de 160 ms).
- Methode habituelle : calques separes (ciel+etoiles V3 / EFFET boreal anime / glace V8 /
  terrain V3), scene 768x512 sans wrap, tests, ZIP."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/effet_boreale_canonique_v10'
CANONIQUE = R / 'aurorepmdsky.png'
V8 = R / 'renders/boreales_ondulation_glace_v8/calques'
T = 10
MS = 160                       # 10 x 160 ms = 1,6 s
CUT = 144                      # fin de la zone boreale (nuages/pics exclus)
FADE = 10                      # fondu bas CUT-FADE -> CUT
LARG, HAUT = 528, 288          # 264x144 x2 nearest
AMP1, L1 = 8.0, 2              # onde principale : 2 longueurs d'onde, amplitude 8 px (affichage)
AMP2, L2, PH2 = 4.0, 5, 0.4    # secondaire : 5 longueurs d'onde, 4 px
ENV = 40.0                     # enveloppe de bord en px affichage

def decalage(x, t):
    return AMP1 * np.sin(2 * np.pi * (L1 * x / LARG - t / T)) + AMP2 * np.sin(2 * np.pi * (L2 * x / LARG - t / T) + PH2)

def enveloppe(x):
    return np.clip(np.minimum(x / ENV, (LARG - 1 - x) / ENV), 0, 1)

def extraire_effet():
    """Rubans lumineux de la texture canonique, ciel retire, etoiles exclues."""
    ref = np.array(Image.open(CANONIQUE).convert('RGB')).astype(float)
    lum = ref.mean(axis=2); sat = ref.max(axis=2) - ref.min(axis=2)
    alpha = np.clip((sat - 75) * 3.0, 0, 255) + np.clip((lum - 105) * 2.0, 0, 255)
    alpha = np.clip(alpha, 0, 255)
    alpha[:CUT - FADE][alpha[:CUT - FADE] < 34] = 0
    fondu = np.ones(216); fondu[CUT - FADE:CUT] = np.linspace(1, 0, FADE); fondu[CUT:] = 0
    alpha = alpha * fondu[:, None]
    masque = alpha > 0
    lab, n = ndimage.label(masque)
    if n:
        tailles = np.bincount(lab.ravel()); tailles[0] = 0
        alpha[(tailles < 6)[lab]] = 0          # etoiles et poussieres isolees
        # les rubans boreaux sont tres satures (sat canonique ~150-190) ; toute
        # composante restante peu saturee et petite est une etoile : exclue
        restant = alpha > 0
        lab2, n2 = ndimage.label(restant)
        if n2:
            sumsat = ndimage.mean(sat, lab2, range(1, n2 + 1))
            sizes = np.bincount(lab2.ravel()); sizes[0] = 0
            etoiles = np.array([k + 1 for k in range(n2) if sumsat[k] < 70 and sizes[k + 1] < 40])
            alpha[np.isin(lab2, etoiles)] = 0
    # passe finale : les etoiles residuelles sont des points visibles peu satures,
    # lies au rideau seulement par un halo tres faible -> distance au ruban sature
    noyau = (alpha >= 100) & (sat >= 70)
    dist_ruban = ndimage.distance_transform_edt(~noyau)
    alpha[(alpha >= 100) & (sat < 50) & (dist_ruban > 10)] = 0
    rgb = ref.copy()
    rgba = np.dstack([rgb, alpha]).astype('uint8')
    rgba[rgba[:, :, 3] == 0] = 0
    im = Image.fromarray(rgba, 'RGBA').crop((0, 0, 264, CUT)).resize((LARG, HAUT), Image.Resampling.NEAREST)
    a = np.array(im); a[:, 0, 3] = 0; a[:, -1, 3] = 0
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a, 'RGBA')

def couche_deplacee(effet, t):
    m = np.array(effet)
    out = np.zeros_like(m)
    for x in range(LARG):
        d = int(round(decalage(x, t) * enveloppe(x)))
        col = m[:, x, :].copy()
        if d > 0:
            out[d:, x, :] = col[:HAUT - d]
        elif d < 0:
            out[:HAUT + d, x, :] = col[-d:]
        else:
            out[:, x, :] = col
    return Image.fromarray(out, 'RGBA')

def scene_composee(t, ciel_merged, couches, glace, terrain, pos=(120, 0)):
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
    effet = extraire_effet()
    effet.save(O / 'effet_canonique_extrait.png')
    couches = [couche_deplacee(effet, t) for t in range(T)]
    for t, im in enumerate(couches):
        im.save(O / 'couches' / f'EffetBorealeV10_frame_{t:02d}.png')
    couches[0].save(O / 'effet_boreale_canonique_10frames.webp', save_all=True, append_images=couches[1:], duration=MS, loop=0, lossless=True, method=4)
    planche = Image.new('RGBA', (LARG // 2, (HAUT // 2) * T), (12, 16, 30, 255))
    for t, im in enumerate(couches):
        planche.alpha_composite(im.resize((LARG // 2, HAUT // 2), Image.Resampling.NEAREST), (0, (HAUT // 2) * t))
    planche.convert('RGB').save(O / 'review/planche_10_couches.png')
    contexte = {'ciel_genere': V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': V8 / 'AreneLargeV3_00b_etoiles.png',
                'glace_laterale': V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': V8 / 'AreneLargeV3_02_sol_visible.png'}
    for nom, src in contexte.items():
        shutil.copy2(src, O / 'contexte' / f'{nom}.png')
    ciel_merged = Image.open(contexte['ciel_genere']).convert('RGBA')
    ciel_merged.alpha_composite(Image.open(contexte['etoiles']).convert('RGBA'))
    glace = Image.open(contexte['glace_laterale']).convert('RGBA')
    terrain = Image.open(contexte['terrain']).convert('RGBA')
    for t in (0, 3, 6, 9):
        scene_composee(t, ciel_merged, couches, glace, terrain).save(O / 'scene' / f'scene_{t:02d}.png')
    palette_image = Image.new('RGB', (384, 256 * 4))
    for i, t in enumerate((0, 3, 6, 9)):
        palette_image.paste(scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)), (0, 256 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene_composee(t, ciel_merged, couches, glace, terrain).convert('RGB').resize((384, 256)).quantize(palette=pal, dither=Image.Dither.NONE) for t in range(T)]
    gifs[0].save(O / 'review/scene_effet_gif.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fond_nuit = Image.new('RGBA', (LARG // 2, HAUT // 2), (10, 12, 26, 255))
    gs = []
    for t in range(T):
        g = fond_nuit.copy(); g.alpha_composite(couches[t].resize((LARG // 2, HAUT // 2), Image.Resampling.NEAREST)); gs.append(g.convert('RGB'))
    gs[0].save(O / 'review/effet_seul.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(ciel_merged), 'glace': uri(glace), 'terrain': uri(terrain), 'couches': [uri(im) for im in couches]}
    (R / 'apercu_effet_boreale_canonique_v10.html').write_text(
        (R / 'source/effet_boreale_canonique_v10/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'texture': {'source': 'aurorepmdsky.png : texture canonique du ciel boreal PMD Sky, recuperee telle quelle',
                    'sha256': hashlib.sha256(CANONIQUE.read_bytes()).hexdigest(),
                    'extraction': 'rubans lumineux via luminosite+saturation, ciel sombre retire (lum~21/sat~63 non retenu), etoiles isolees exclues, zone nuages/pics (y>=144) hors calque, fondu bas 134->144, x2 nearest, bords lateraux a zero'},
        'onde': {'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
                 'physique': 'onde transversale : deplacement STRICTEMENT vertical par colonne, phase voyageant horizontalement, 2+5 longueurs d\'onde entieres, enveloppe 40 px, boucle exacte frame 10 = frame 0',
                 'layers': 'chaque frame est un calque independant couches/EffetBorealeV10_frame_XX.png (528x288 RGBA), pose une fois a (120,0)'},
        'contexte': {'ciel_etoiles': 'V3 byte-identiques', 'glace': 'V8 byte-identique', 'terrain': 'V3 byte-identique'},
        'wrap': False, 'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cadence': 'choisie par nous, pas le cycle officiel du jeu (non recupere)'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
