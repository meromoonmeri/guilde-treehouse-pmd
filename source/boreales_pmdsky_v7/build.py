"""Frames animees du ciel boreal de PMD Sky, a partir de l'image de reference elle-meme.
Aucun deplacement, aucun wrap, aucune rotation de teinte : seule la lumiere des rideaux
(variation proportionnelle de luminosite et de voile) change, subtilement, en boucle fermee.
Frame 0 = reference exacte. 24 frames x 120 ms = 2,88 s."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import json, hashlib, shutil, io, base64

R = Path(__file__).resolve().parents[2]
O = R / 'renders/boreales_pmdsky_v7'
V3 = R / 'renders/arene_glace_large_v3'
REF_PATH = R / 'aurorepmdsky.png'
T = 24
MS = 120
H_REGION = 157          # fin de la zone d'aurore (fondu 144 -> 157)
AMPLITUD_LUM = 0.075    # ±7,5 % de luminosite max sur les rideaux
AMPLITUD_ALPHA = 0.11   # ±11 % de voile max sur l'overlay

def extraire_aurore(ref):
    """Alpha du rideau : distance a un ciel de base estime par minimum local + lissage."""
    lum = ref.astype(float).mean(axis=2)
    base = ndimage.gaussian_filter(ndimage.minimum_filter(lum, size=31), 12)
    alpha = np.clip((lum - base - 6) * 3.2, 0, 255)
    coeur = alpha > 110
    plein = ndimage.binary_fill_holes(coeur)
    voile = plein & (alpha <= 110)
    alpha = np.where(voile, np.maximum(alpha, 64), alpha)
    fondu = np.ones(216)
    fondu[H_REGION-13:H_REGION] = np.linspace(1, 0, 13)
    fondu[H_REGION:] = 0
    alpha = alpha * fondu[:, None]
    lab, _ = ndimage.label(alpha > 40)
    tailles = np.bincount(lab.ravel())
    alpha[(tailles < 24)[lab]] = 0
    return np.clip(alpha, 0, 255).astype('uint8')

def champs_fixes():
    rng = np.random.default_rng(11)
    def champ(sigma, norme01=False):
        c = ndimage.gaussian_filter(rng.standard_normal((216, 264)), sigma)
        if norme01:
            return (c - c.min()) / (c.max() - c.min())
        return c / np.abs(c).max()
    return champ(4), champ(6), champ(9), champ(14, norme01=True)

def modulations():
    """mnob[t] dans [-1, ~0,6] ; chaque terme s'annule a t=0 et la somme est periodique."""
    U, V, W, G = champs_fixes()
    th = 2 * np.pi * np.arange(T) / T
    champs = []
    for t in range(T):
        m = (0.50 * U * (np.cos(th[t]) - 1.0)
             + 0.35 * V * (np.cos(2 * th[t] + 1.1) - np.cos(1.1))
             + 0.30 * W * (np.cos(3 * th[t] + 2.3) - np.cos(2.3))
             + 0.45 * G * (1 - np.cos(th[t])))
        champs.append(m)
    denom = max(max(np.abs(m).max() for m in champs), 1e-9)
    return [m / denom for m in champs]

def frames_ciel(ref, mnorm, protege):
    out = []
    for t in range(T):
        f = ref.astype(float) * (1.0 + AMPLITUD_LUM * mnorm[t])[..., None]
        f = np.rint(f).clip(0, 255).astype('uint8')
        f[protege] = ref[protege]
        out.append(Image.fromarray(f, 'RGB'))
    return out

def frames_overlay(alpha, mnorm, ref):
    out = []
    for t in range(T):
        a = np.rint(alpha.astype(float) * (1.0 + AMPLITUD_ALPHA * mnorm[t])).clip(0, 255).astype('uint8')
        rgb = ref.copy()
        rgb[a == 0] = 0
        out.append(Image.fromarray(np.dstack([rgb, a]), 'RGBA'))
    return out

def feather_bords(im, fx=24, fy=20):
    """Fondu doux des bords gauche/droit/bas pour poser l'overlay dans la scene large."""
    a = np.array(im).astype(float)
    h, w = a.shape[:2]
    x = np.ones(w); x[:fx] = np.linspace(0, 1, fx); x[-fx:] = np.linspace(1, 0, fx)
    y = np.ones(h); y[-fy:] = np.linspace(1, 0, fy)
    a[:, :, 3] *= np.minimum(x[None, :], y[:, None])
    a[:, :, 3] = np.rint(a[:, :, 3]).astype('uint8')
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a.astype('uint8'), 'RGBA')

def uri(im):
    b = io.BytesIO(); im.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def scene_composee(t, ciel_merged, terrain, ov_x2, pos=(120, 0)):
    s = ciel_merged.copy()
    s.alpha_composite(ov_x2[t % T], pos)
    s.alpha_composite(terrain, (0, 0))
    return s

def construire():
    for d in ['ciel/frames', 'overlay/frames', 'review', 'calques']:
        (O / d).mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(REF_PATH).convert('RGB'))
    alpha = extraire_aurore(ref)
    Image.fromarray(np.dstack([ref, alpha]), 'RGBA').crop((0, 0, 264, H_REGION)).save(O / 'overlay/overlay_source_frame0.png')
    mnorm = modulations()
    lum = ref.astype(float).mean(axis=2)
    sat = ref.max(axis=2) - ref.min(axis=2)
    etoiles = (sat < 40) & (lum > 170)
    protege = np.zeros((216, 264), bool)
    protege[H_REGION:, :] = True
    protege |= etoiles
    ciel = frames_ciel(ref, mnorm, protege)
    for t, im in enumerate(ciel):
        im.save(O / 'ciel/frames' / f'CielPmdskyV7_{t:03d}.png')
    ov_native = frames_overlay(alpha, mnorm, ref)
    ov_x2 = [feather_bords(im.crop((0, 0, 264, H_REGION)).resize((528, H_REGION * 2), Image.Resampling.NEAREST)) for im in ov_native]
    for t, im in enumerate(ov_x2):
        im.save(O / 'overlay/frames' / f'OverlayPmdskyV7_{t:03d}.png')
    ciel[0].save(O / 'ciel/ciel_boreal_anime.webp', save_all=True, append_images=ciel[1:], duration=MS, loop=0, lossless=True, method=4)
    ov_x2[0].save(O / 'overlay/overlay_anime.webp', save_all=True, append_images=ov_x2[1:], duration=MS, loop=0, lossless=True, method=4)
    echantillon = [ciel[i].convert('RGB') for i in (0, 6, 12, 18)]
    bandeau = Image.new('RGB', (264, 216 * 4))
    for i, im in enumerate(echantillon):
        bandeau.paste(im, (0, 216 * i))
    pal = bandeau.quantize(colors=256)
    q = [im.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE) for im in ciel]
    q[0].save(O / 'review/ciel_anime.gif', save_all=True, append_images=q[1:], duration=MS, loop=0, disposal=1, optimize=False)
    for p in (V3 / 'calques').glob('*.png'):
        shutil.copy2(p, O / 'calques' / p.name)
    ciel_merged = Image.open(V3 / 'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA')
    ciel_merged.alpha_composite(Image.open(V3 / 'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'))
    terrain = Image.open(V3 / 'review/terrain_detoure.png').convert('RGBA')
    for t in (0, 8, 16):
        scene_composee(t, ciel_merged, terrain, ov_x2).save(O / 'review' / f'scene_{t:03d}.png')
    planche = Image.new('RGB', (264 * 4, 216), (12, 14, 26))
    for i, t in enumerate((0, 6, 12, 18)):
        planche.paste(ciel[t].convert('RGB'), (264 * i, 0))
    planche.save(O / 'review/planche_frames_x1.png')
    donnees = {'reference': uri(Image.open(REF_PATH).convert('RGB')),
               'ciel': [uri(im) for im in ciel],
               'overlay': [uri(im) for im in ov_x2],
               'cielV3': uri(ciel_merged), 'terrain': uri(terrain)}
    (R / 'apercu_ciel_boreal_pmdsky_v7.html').write_text(
        (R / 'source/boreales_pmdsky_v7/viewer.html').read_text().replace('__DATA__', json.dumps(donnees)))
    (O / 'manifest.json').write_text(json.dumps({
        'source': 'aurorepmdsky.png (reference PMD Sky fournie)',
        'reference_sha256': hashlib.sha256(REF_PATH.read_bytes()).hexdigest(),
        'frames': T, 'duree_ms': MS, 'cycle_s': round(T * MS / 1000, 2),
        'methode': "L'image de reference elle-meme, annee par frame : variation proportionnelle de luminosite (max ±7,5 %) sur les pixels du rideau et de voile (max ±11 %) sur l'overlay. Aucun deplacement, aucun warp, aucun wrap, aucune rotation de teinte.",
        'frame0': 'reference exacte, difference nulle',
        'protege': 'pics de glace, nuages d horizon et etoiles non modulates',
        'overlay': 'extraction alpha de la reference, voile interieur rempli (alpha 64), petites composantes enlevees, bords fondus pour la scene 768x512 (pose fixe x=120,y=0)',
        'boucle': 'toutes les modulations sont des cosinus a periodes entieres : frame 24 = frame 0',
        'cycle_officiel': 'INCONNU : timings et amplitudes choisis, subtils ; pas le cycle extrait du jeu',
        'terrain_ciel_V3': 'copies byte-identiques',
        'runtime_PMDO': 'NON TESTE', 'autres_zones': 'ouvertes'}, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    construire()
