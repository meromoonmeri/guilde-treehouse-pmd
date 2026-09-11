"""Reconstruit la scène extérieure indépendante, sans modifier le kit des salles."""
from pathlib import Path
from PIL import Image, ImageDraw
import cv2
import json
import numpy as np
from exterior_animation import export_variant, stars_spec

R = Path(__file__).resolve().parents[1]
S = R / 'source/falaise'
OUT = R / 'falaise'
W, H = 480, 408
FRAMES, DURATION = 480, 250  # 1 px par image ; tour complet de 120 secondes.
MODES = ['jour', 'nuit', 'crepuscule', 'aube', 'soir', 'orageux']
LAYERS = [
    ('00_ciel', 'Ciel', False),
    ('01_astres', 'Lune fixe et étoiles scintillantes', True),
    ('02_nuages', 'Nuages — défilement en boucle', True),
    ('03_reliefs', 'Reliefs rocheux et forêt lointaine', False),
    ('04_falaise', 'Falaise, plateau libre et escalier', False),
    ('05_vegetation', 'Décor additionnel — vide', False),
]
SPECS = {
    'jour': ((98, 176, 229), (198, 231, 213), (1, 1, 1), (0, 0, 0), 1),
    'nuit': ((16, 24, 53), (68, 86, 113), (.40, .42, .58), (4, 8, 15), .80),
    'crepuscule': ((50, 46, 89), (200, 134, 130), (.64, .58, .79), (7, 6, 14), .75),
    'aube': ((113, 126, 178), (249, 202, 150), (.84, .80, .93), (14, 8, 13), .78),
    'soir': ((125, 123, 172), (254, 182, 106), (1.03, .77, .53), (10, 8, 9), .82),
    'orageux': ((45, 60, 77), (128, 151, 150), (.57, .65, .77), (5, 9, 15), .55),
}


def key(im):
    a = np.array(im.convert('RGBA'))
    r, g, b = [a[:, :, i].astype(int) for i in range(3)]
    mask = (r-g > 65) & (b-g > 50) & (r > 125) & (b > 100)
    near = cv2.dilate(mask.astype('uint8'), np.ones((3, 3), np.uint8)) > 0
    mask |= near & (r-g > 25) & (b-g > 12) & (b > r*.42)
    a[mask] = 0
    return Image.fromarray(a)


def grade(im, mul, add, sat=1):
    a = np.array(im.convert('RGBA'))
    v = a[:, :, :3].astype(float)
    lum = (v @ np.array([.2126, .7152, .0722]))[:, :, None]
    v = (lum*(1-sat) + v*sat)*np.array(mul) + np.array(add)
    a[:, :, :3] = np.rint(v).clip(0, 255).astype('uint8')
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def png(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # RGBA explicite pour les importeurs ne gérant pas les PNG indexés transparents.
    im.convert('RGBA').save(path, optimize=True)


def sky(top, bottom):
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.repeat(np.rint(np.array(top)*(1-y) + np.array(bottom)*y).astype('uint8'), W, axis=1)
    return Image.fromarray(a).convert('RGBA')


def sky_variant(mode, day, night):
    if mode == 'jour':
        return day.copy()
    if mode == 'nuit':
        return night.copy()
    # Les quatre autres ambiances gardent leur palette, avec le grain du nouveau ciel.
    top, bottom, *_ = SPECS[mode]
    source = np.array(day)[:, :, :3].astype(np.float32)
    detail = source-cv2.GaussianBlur(source, (0, 0), 2)
    a = np.array(sky(top, bottom))
    a[:, :, :3] = np.rint(a[:, :, :3].astype(float)+detail*.45).clip(0, 255).astype('uint8')
    return Image.fromarray(a)


def build():
    rules = json.loads((S / 'regles.json').read_text(encoding='utf-8'))
    terrain = Image.open(S / 'falaise_native.png').convert('RGBA')
    relief = key(Image.open(S / 'reliefs_native.png'))
    vegetation = Image.open(S / 'vegetation_native.png').convert('RGBA')
    assert vegetation.getbbox() is None
    clouds = Image.open(S / 'nuages_native.png').convert('RGBA')
    stars = Image.open(S / 'astres_nuit_native.png').convert('RGBA')
    day_sky = Image.open(S / 'ciel_jour_native.png').convert('RGBA')
    night_sky = Image.open(S / 'ciel_nuit_native.png').convert('RGBA')
    definitions = [{'id': n, 'nom': label, 'anime': anim} for n, label, anim in LAYERS]
    manifest = {'version': 2, 'id': 'falaise', 'titre': 'Falaise — prairie de la guilde',
                'dimensions': [W, H], 'grille_px': 8, 'cellules': [60, 51], 'base_start': 4,
                'animation': {'frames': FRAMES, 'duree_image_ms': DURATION, 'duree_boucle_ms': FRAMES*DURATION},
                'ambiances': MODES, 'calques': definitions, 'regles': rules, 'fichiers': {}}
    markers = [{'nom': 'Accès sud', 'rectangle_px': [208, 380, 64, 28]},
               {'nom': 'Plateau', 'rectangle_px': [154, 144, 172, 176]}]
    star_animation = stars_spec(stars, OUT)
    for mode in MODES:
        _, _, mul, add, saturation = SPECS[mode]
        astres = Image.new('RGBA', (W, H))
        if mode in ['nuit', 'crepuscule']:
            astres = stars.copy()
            if mode == 'crepuscule':
                astres.putalpha(astres.getchannel('A').point(lambda p: round(p*.40)))
        if mode in ['aube', 'soir']:
            d = ImageDraw.Draw(astres)
            x = 399 if mode == 'aube' else 82
            d.ellipse((x-7, 66, x+7, 80), fill=(255, 231, 163, 255))
        aa = np.array(astres)
        aa[aa[:, :, 3] == 0] = 0
        astres = Image.fromarray(aa)
        body = [sky_variant(mode, day_sky, night_sky), astres, grade(clouds, mul, add, saturation),
                grade(relief, mul, add, saturation), grade(terrain, mul, add, saturation), vegetation]
        specs = {'02_nuages': {'kind': 'scroll', 'period': W, 'prefix': 'nuages'}}
        if mode == 'nuit':
            specs['01_astres'] = star_animation
        manifest['fichiers'][mode] = export_variant(OUT, mode, definitions, body, specs,
                                                   (W, H), FRAMES, 4, markers)
        print('Falaise', mode, '— nuages variés ; prairie fixe ; scintillement nocturne', flush=True)
    (OUT / 'kit.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    build()
