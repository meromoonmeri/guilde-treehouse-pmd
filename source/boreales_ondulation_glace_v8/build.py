"""V8 : arene de glace avec aurore ONDULANTE generee + glace laterale derriere l'arene.
Methode habituelle : planches generees avec fond magenta -> extraction alpha -> calques separes
(ciel V3 / aurore animee / glace / terrain V3) -> scene 768x512 sans wrap -> tests -> ZIP.
Aurore : 8 poses dessinees generees (2x4 cases), 32 etapes par fondus, ondulation verticale
des cretes sans translation horizontale. Glace : panneau genere (parois laterales + plaine
du fond) pose derriere le terrain pour remplir les zones grises des cotes."""
from pathlib import Path
import numpy as np
from PIL import Image
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/boreales_ondulation_glace_v8'
V3 = R / 'renders/arene_glace_large_v3'
BRUT_AURORE = O / 'bruts/aurore_ondulations_8_haut.png'
SOURCE_INITIALE = O / 'bruts/aurore_ondulations_8.png'
BRUT_GLACE = O / 'bruts/glace_laterale.png'
GRILLE = (1, 8)          # extraction en colonne unique : les cases debordent horizontalement dans la planche 2x4
BANDE_H = 305            # fenetre verticale extraite par pose (la vague traverse la case a des hauteurs differentes)
POSES = 8
SOUS = 4                 # etapes de fondu par paire de poses
T = POSES * SOUS         # 32 frames
MS = 125                 # 32 x 125 ms = 4,0 s

def alpha_depuis_magenta(rgb, seuil=60.0, montee=3.0):
    r = rgb[:, :, 0].astype(float); g = rgb[:, :, 1].astype(float); b = rgb[:, :, 2].astype(float)
    d = np.sqrt((r - 255) ** 2 + g ** 2 + (b - 255) ** 2)
    a = np.clip((d - seuil) * montee, 0, 255)
    return a

def defringe(rgba):
    """Sur les pixels de bord semi-transparents, supprime la frange rose (r = min(r, b))."""
    a = rgba[:, :, 3].astype(float)
    bord = (a > 0) & (a < 250)
    rgba[:, :, 0] = np.where(bord, np.minimum(rgba[:, :, 0], rgba[:, :, 2]), rgba[:, :, 0])
    return rgba

def extraire_poses():
    brut = Image.open(BRUT_AURORE).convert('RGB')
    W, H = brut.size; cw, ch = W // 2, H // 4
    poses = []
    (O / 'aurore/poses').mkdir(parents=True, exist_ok=True)
    for i in range(POSES):
        col, lig = i % 2, i // 2
        x0 = 30 if col == 0 else cw + 30
        # decoupe verticale centree sur la vague : scan du centroid magenta->aurore par case
        cell_full = brut.crop((x0, lig * ch + 3, x0 + cw - 60, (lig + 1) * ch - 3))
        rgb_full = np.array(cell_full)
        a_full = alpha_depuis_magenta(rgb_full)
        ys = np.where((a_full > 128).any(axis=1))[0]
        cy = int(ys.mean()) if ys.size else rgb_full.shape[0] // 2
        top = max(0, min(rgb_full.shape[0] - BANDE_H, cy - BANDE_H // 2))
        rgb = rgb_full[top:top + BANDE_H]
        a = a_full[top:top + BANDE_H]
        rgba = np.dstack([rgb, np.rint(a).astype('uint8')]).astype('uint8')
        rgba = defringe(rgba)
        rgba[rgba[:, :, 3] == 0] = 0
        im = Image.fromarray(rgba, 'RGBA').resize((768, 256), Image.Resampling.NEAREST)
        arr = np.array(im)
        arr[:, 0, 3] = 0; arr[:, -1, 3] = 0
        Image.fromarray(arr, 'RGBA').save(O / 'aurore/poses' / f'pose_{i:02d}.png')
        poses.append(arr)
    return poses

def frames_ondulation(poses):
    """32 etapes : 4 fondus premultiplies entre poses adjacentes ; frame 32 = frame 0."""
    out = []
    for k in range(POSES):
        A = poses[k].astype(float); B = poses[(k + 1) % POSES].astype(float)
        for s in range(SOUS):
            t = s / SOUS
            a = (1 - t) * A[:, :, 3] + t * B[:, :, 3]
            rgb = ((1 - t) * A[:, :, :3] * A[:, :, 3:4] + t * B[:, :, :3] * B[:, :, 3:4]) / np.maximum(a[:, :, None], 1e-6)
            rgba = np.rint(np.dstack([rgb, a])).clip(0, 255).astype('uint8')
            rgba[rgba[:, :, 3] == 0] = 0
            out.append(rgba)
    return out

def couche_glace():
    brut = Image.open(BRUT_GLACE).convert('RGB')
    rgb = np.array(brut)
    a = alpha_depuis_magenta(rgb, seuil=80.0, montee=4.0)
    rgba = np.dstack([rgb, np.rint(a).astype('uint8')]).astype('uint8')
    rgba = defringe(rgba)
    rgba[rgba[:, :, 3] == 0] = 0
    im = Image.fromarray(rgba, 'RGBA').resize((768, 515), Image.Resampling.NEAREST)
    im = im.crop((0, 0, 768, 512))
    im.save(O / 'calques' / 'V8_glace_laterale_arriere_plan.png')
    return im

def scene_composee(t, ciel_merged, aurores, glace, terrain):
    s = ciel_merged.copy()
    s.alpha_composite(aurores[t % T], (0, 0))
    s.alpha_composite(glace, (0, 0))
    s.alpha_composite(terrain, (0, 0))
    return s

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def construire():
    for d in ['aurore/poses', 'aurore/frames', 'review', 'calques']:
        (O / d).mkdir(parents=True, exist_ok=True)
    poses = extraire_poses()
    rgba_frames = frames_ondulation(poses)
    aurores = [Image.fromarray(f, 'RGBA') for f in rgba_frames]
    for t, im in enumerate(aurores):
        im.save(O / 'aurore/frames' / f'AuroreOndulationV8_{t:03d}.png')
    aurores[0].save(O / 'aurore/ondulation_32frames.webp', save_all=True, append_images=aurores[1:], duration=MS, loop=0, lossless=True, method=4)
    glace = couche_glace()
    for p in (V3 / 'calques').glob('*.png'):
        shutil.copy2(p, O / 'calques' / p.name)
    ciel_merged = Image.open(V3 / 'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA')
    ciel_merged.alpha_composite(Image.open(V3 / 'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'))
    terrain = Image.open(V3 / 'review/terrain_detoure.png').convert('RGBA')
    for t in (0, 8, 16, 24):
        scene_composee(t, ciel_merged, aurores, glace, terrain).save(O / 'review' / f'scene_{t:03d}.png')
    # GIF de scene en demi-resolution, palette partagee (methode habituelle)
    palette_image = Image.new('RGB', (384, 256 * 4))
    for i, t in enumerate((0, 8, 16, 24)):
        palette_image.paste(scene_composee(t, ciel_merged, aurores, glace, terrain).convert('RGB').resize((384, 256)), (0, 256 * i))
    pal = palette_image.quantize(colors=256)
    gifs = []
    for t in range(T):
        im = scene_composee(t, ciel_merged, aurores, glace, terrain).convert('RGB').resize((384, 256))
        gifs.append(im.quantize(palette=pal, dither=Image.Dither.NONE))
    gifs[0].save(O / 'review/scene_ondulation_glace.gif', save_all=True, append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    planche = Image.new('RGB', (384 * 4, 128 * 2), (10, 12, 24))
    for i, p in enumerate(poses):
        im = Image.fromarray(p, 'RGBA').resize((384, 128), Image.Resampling.NEAREST)
        fond = Image.new('RGBA', im.size, (10, 12, 24, 255)); fond.alpha_composite(im)
        planche.paste(fond.convert('RGB'), ((i % 4) * 384, (i // 4) * 128))
    planche.save(O / 'review/planche_poses.png')
    donnees = {'ciel': uri(ciel_merged), 'glace': uri(glace), 'terrain': uri(terrain),
               'aurore': [uri(im) for im in aurores]}
    (R / 'apercu_arene_ondulation_glace_v8.html').write_text(
        (R / 'source/boreales_ondulation_glace_v8/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'aurore': {'poses_dessinees_generees': POSES, 'etapes': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
                   'methode': '8 dessins generes (planche 2x4, fond magenta) -> alpha -> 4 fondus premultiplies par paire ; ondulation verticale des cretes, pas de translation horizontale, pas de wrap',
                   'brut_sha256': hashlib.sha256(BRUT_AURORE.read_bytes()).hexdigest()},
        'glace': {'role': 'parois laterales + plaine du fond derriere le terrain ; remplit les zones grises des cotes',
                  'position': '0,0 sur 768x512, statique, entre aurore et terrain',
                  'brut_sha256': hashlib.sha256(BRUT_GLACE.read_bytes()).hexdigest()},
        'calques_V3': 'copies byte-identiques', 'wrap': False,
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes',
        'cycle_officiel': 'INCONNU : dessins et rythme choisis, pas le cycle du jeu'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
