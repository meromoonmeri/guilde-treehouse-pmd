"""V16 : zone SANS TROU (sol continu) + aurores de la REFERENCE en 10 frames, boucle parfaite par la methode canonique (terrain plein cadre + magenta) et
convertie aux criteres Halcyon/Palika : calques fixes empiles, frames d'aurore a taille
identique et nommage uniforme (AuroreV16_00..09.png), duree uniforme, position sur
grille 8 px, manifeste complet. Ondulations boréales : 8 poses generees."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/arene_halcyon_v16'
BRUT_T = O / 'bruts/terrain_sans_trou.png'
BRUT_B = O / 'bruts/boreale_ref_10.png'
ETOILES = R / 'renders/arene_guide_couches_v14/couches/etoiles_fixes.png'
L, H = 928, 1152
CASE_L, CASE_H = 768, 256
POS_X, POS_Y = 80, 24          # grille 8 px (80=8x10, 24=8x3)
T, MS = 10, 130                 # 10 x 130 ms = 1,3 s, boucle naturelle (frame 10 ≈ frame 0)

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def flood_fond_magenta(rgb, seuil=130.0):
    d = np.linalg.norm(rgb.astype(float) - np.array([255.0, 0.0, 255.0]), axis=2)
    cand = d < seuil
    bord = np.zeros_like(cand); bord[0, :] = True
    fond = ndimage.binary_propagation(bord & cand, mask=cand)
    return fond

def extraire_frames_boreale():
    """Extraction pleine case : magenta cuit retire par (a) seuil SERRE global — le fond
    plat est a distance <40 de (255,0,255), le coeur des rubans a ~72 — et (b) inondation
    large depuis les bords pour les halos. AUCUN remplissage de trous (lecon V9)."""
    brut = Image.open(BRUT_B).convert('RGB')
    W, Hb = brut.size; cw, ch = W // 2, Hb // 5
    frames = []
    for i in range(T):
        col, lig = i % 2, i // 2
        cell = np.array(brut.crop((col * cw + 5, lig * ch + 5, (col + 1) * cw - 5, (lig + 1) * ch - 5)))
        d = np.linalg.norm(cell.astype(float) - np.array([255.0, 0.0, 255.0]), axis=2)
        cand = d < 140
        bord = np.zeros_like(cand); bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
        fond_inonde = ndimage.binary_propagation(bord & cand, mask=cand)
        fond = fond_inonde | (d < 40)
        rgba = np.dstack([cell, np.where(fond, 0, 255).astype('uint8')])
        im = Image.fromarray(rgba, 'RGBA').resize((CASE_L, CASE_H), Image.Resampling.NEAREST)
        a = np.array(im); a[a[:, :, 3] == 0] = 0
        frames.append(Image.fromarray(a, 'RGBA'))
    return frames

def construire():
    for d in ['couches/aurore', 'review', 'scene']:
        (O / d).mkdir(parents=True, exist_ok=True)
    # --- terrain (methode canonique) ---
    brut_t = np.array(Image.open(BRUT_T).convert('RGB'))
    fond = flood_fond_magenta(brut_t)
    ciel_masque = ndimage.binary_fill_holes(fond)
    terrain = np.dstack([brut_t, np.where(ciel_masque, 0, 255).astype('uint8')])
    Image.fromarray(terrain, 'RGBA').save(O / 'couches/terrain_fixe.png')
    # --- ciel et etoiles (fixes) ---
    ciel = np.zeros((H, L, 4), 'uint8')
    ciel[:, :, :3] = (6, 12, 75)
    ciel[:, :, 3] = 255
    Image.fromarray(ciel, 'RGBA').save(O / 'couches/ciel_fixe.png')
    et = np.array(Image.open(ETOILES).convert('RGBA'))
    Image.fromarray(et, 'RGBA').save(O / 'couches/etoiles_fixes.png')
    # --- aurore : 8 frames uniformes ---
    frames = extraire_frames_boreale()
    for f, im in enumerate(frames):
        im.save(O / 'couches/aurore' / f'AuroreV16_{f:02d}.png')
    frames[0].save(O / 'aurore_ondulation_10frames.webp', save_all=True, append_images=frames[1:], duration=MS, loop=0, lossless=True, method=4)
    # --- scenes ---
    def scene(f):
        s = Image.fromarray(ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(et, 'RGBA'))
        s.alpha_composite(frames[f % T], (POS_X, POS_Y))
        s.alpha_composite(Image.fromarray(terrain, 'RGBA'))
        return s
    for f in (0, 3, 6, 9):
        scene(f).save(O / 'scene' / f'scene_{f:02d}.png')
    palette_image = Image.new('RGB', (464, 576 * 4))
    for i, f in enumerate((0, 3, 6, 9)):
        palette_image.paste(scene(f).convert('RGB').resize((464, 576)), (0, 576 * i))
    pal = palette_image.quantize(colors=256)
    gifs = [scene(f).convert('RGB').resize((464, 576)).quantize(palette=pal, dither=Image.Dither.NONE) for f in range(T)]
    gifs[0].save(O / 'review/scene_ondulation.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    fondn = Image.new('RGBA', (384, 128), (10, 12, 26, 255))
    gs = []
    for f in range(T):
        g2 = fondn.copy(); g2.alpha_composite(frames[f].resize((384, 128), Image.Resampling.NEAREST)); gs.append(g2.convert('RGB'))
    gs[0].save(O / 'review/aurore_seule.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    donnees = {'ciel': uri(Image.fromarray(ciel, 'RGBA')), 'etoiles': uri(Image.fromarray(et, 'RGBA')),
               'terrain': uri(Image.fromarray(terrain, 'RGBA')), 'couches': [uri(im) for im in frames]}
    (R / 'apercu_arene_halcyon_v16.html').write_text(
        (R / 'source/arene_halcyon_v15/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'halcyon': {'grille_px': 8, 'aurore_position': [POS_X, POS_Y], 'position_multiple_de_8': POS_X % 8 == 0 and POS_Y % 8 == 0,
                    'frames_nommage_uniforme': 'AuroreV16_00..09.png', 'frames_taille_uniforme': [CASE_L, CASE_H],
                    'duree_ms_uniforme': MS, 'boucle': 'frame 10 ≈ frame 0 (poses naturelle du cycle)', 'ordre_des_calques': ['ciel_fixe', 'etoiles_fixes', 'aurore (8 frames)', 'terrain_fixe'],
                    'pas_de_wrap': True},
        'methode': 'canonique : terrain genere plein cadre avec bande magenta -> alpha par inondation ; planche 2x4 generee pour les ondulations -> 8 frames 768x256',
        'bruts_sha256': {'terrain': hashlib.sha256(BRUT_T.read_bytes()).hexdigest(), 'boreale': hashlib.sha256(BRUT_B.read_bytes()).hexdigest()},
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cycle_officiel': 'INCONNU : poses et cadence choisis'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
