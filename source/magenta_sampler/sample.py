"""Echantillonneur de references -> configuration stricte du generateur magenta (V2).

Regles calibreessur sondages reels (voir dev) ; recouvrements possibles entre materiaux,
signales mais acceptes (l'audit compare brut et reference avec les MEMES regles).
Metriques par materiau : effectif, couverture, top12, mediane, plages HSV, grain
(run-length patch), dither (fraction de pixels differant du voisin droit >24).
Sorties : config JSON, planche palettes PNG, contraintes prompt TXT, audit bruts JSON.

Resultat marquant : Southern Jungle = ZERO marron (troncs verts sombres uniquement).
Aucun effet a l'import (garde __main__).
"""
from pathlib import Path
import json
import colorsys
import numpy as np
from PIL import Image, ImageDraw

R = Path(__file__).resolve().parents[2]
O = R / 'source/magenta_sampler/configs'


def rules_jungle(rgb):
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    s = r + g + b
    return {
        'chutes': (b > 110) & (b > r + 15) & (s >= 280) & (s < 560),
        'ecume': (s >= 620),
        'eau_bassins': (b > 40) & (b < 170) & (r < 130) & (s < 300) & (b > r + 5),
        'falaise': (r > 90) & (r < 200) & (r > g + 5) & (g > b - 10) & (s < 480),
        'herbe': (g > 90) & (g > r + 5) & (g > b + 5) & (s < 280),
        'chemin': (g > 120) & (r > 50) & (s >= 240) & (s < 420),
        'buisson': (g > 40) & (g <= 90) & (g > r) & (g > b),
        'rocher': (r > 100) & (abs(r - g) < 30) & (abs(g - b) < 40) & (s >= 330) & (s < 520),
    }


def rules_southern(rgb):
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    s = r + g + b
    return {
        # PAS de regle marron : echantillon = 0 px marron sur les 3 refs (troncs verts sombres).
        'canopee': (g > 50) & (g > r + 3) & (g > b + 3),
        'futs_verts_sombres': (s < 110) & (g >= r - 3) & (g > b - 8),
        'sol_sable': (r > 130) & (g > 120) & (b < 130) & (r > b + 20),
        'buisson_sombre': (g > 20) & (g <= 50) & (g >= r - 5) & (g >= b - 5),
    }


def grain(mask):
    diff = np.diff(mask.astype(np.int8), axis=1)
    starts = (diff == 1).sum()
    return round(float(mask.sum() / max(starts, 1)), 2)


def dither(rgb, m):
    d = np.abs(rgb[:, :-1].astype(int) - rgb[:, 1:].astype(int)).max(-1) > 24
    z = np.zeros_like(m)
    z[:, :-1] = d & m[:, :-1]
    return round(float(z[m].mean()) if m.sum() else 0.0, 4)


def sample_material(rgb, m):
    px = rgb[m]
    n = len(px)
    if n == 0:
        return dict(pixels=0)
    colors, counts = np.unique(px.reshape(-1, 3), axis=0, return_counts=True)
    top = np.argsort(-counts)[:12]
    pal = [[int(c) for c in colors[i]] + [int(counts[i])] for i in top]
    med = [int(v) for v in np.median(px, axis=0)]
    sub = px[::max(1, n // 4000)]
    hsv = np.array([colorsys.rgb_to_hsv(*(p / 255 for p in q)) for q in sub])
    return dict(pixels=int(n), couverture=round(n / rgb.shape[0] / rgb.shape[1], 4),
                couleurs_distinctes=int(len(colors)), grain_px=grain(m), dither=dither(rgb, m),
                mediane_rgb=med, top12_rgb_effectif=pal,
                hsv_p10=np.percentile(hsv, 10, axis=0).round(3).tolist(),
                hsv_p90=np.percentile(hsv, 90, axis=0).round(3).tolist())


def sample(ref, rules):
    im = Image.open(R / ref).convert('RGB')
    rgb = np.array(im)
    return dict(reference=ref, taille=list(im.size),
                materiaux={mat: sample_material(rgb, m) for mat, m in rules(rgb).items()})


def sheet(cfg, dest):
    mats = list(cfg['materiaux'].items())
    W, H = 980, 46 + 64 * len(mats)
    im = Image.new('RGB', (W, H), (24, 24, 24))
    d = ImageDraw.Draw(im)
    d.text((10, 10), f"{cfg['reference']} — {cfg['taille'][0]}x{cfg['taille'][1]}", fill=(255, 255, 255))
    y = 40
    for mat, s in mats:
        if s.get('pixels', 0) == 0:
            d.text((10, y + 20), f'{mat} : 0 px', fill=(255, 120, 120))
            y += 64
            continue
        d.text((10, y + 20), f"{mat} {s['couverture'] * 100:.1f}% dith{s['dither']}",
               fill=(255, 255, 255))
        for i, (r, g, b, c) in enumerate(s['top12_rgb_effectif']):
            d.rectangle((330 + i * 48, y + 8, 330 + i * 48 + 44, y + 56), fill=(r, g, b))
        d.text((330 + 12 * 48 + 10, y + 20), 'med #%02x%02x%02x' % tuple(s['mediane_rgb']),
               fill=(200, 200, 200))
        y += 64
    im.save(dest)


def prompt_constraints(cfg, extra=()):
    L = [f"Contraintes echantillonnees de {cfg['reference']} ({cfg['taille'][0]}x{cfg['taille'][1]}) :"]
    for mat, s in cfg['materiaux'].items():
        if s.get('pixels', 0) == 0:
            continue
        top3 = ['#%02x%02x%02x' % tuple(c[:3]) for c in s['top12_rgb_effectif'][:3]]
        L.append(f"- {mat} : {s['couverture'] * 100:.1f}%, mediane #{'%02x%02x%02x' % tuple(s['mediane_rgb'])}, "
                 f"refs {', '.join(top3)}, dither {s['dither']}, {s['couleurs_distinctes']} couleurs.")
    L.extend(extra)
    return '\n'.join(L) + '\n'


def audit_brut(brut_path, cfg, rules):
    rgb = np.array(Image.open(brut_path).convert('RGB'))
    rep = {}
    for mat, m in rules(rgb).items():
        ref = cfg['materiaux'].get(mat, {})
        if not ref.get('pixels'):
            continue
        cov = m.sum() / rgb.shape[0] / rgb.shape[1]
        if m.sum() == 0:
            rep[mat] = dict(couverture_brut=0.0, ecart_couverture=round(ref['couverture'], 4),
                            distance_mediane=None)
            continue
        dist = float(np.linalg.norm(np.median(rgb[m], axis=0) - np.array(ref['mediane_rgb'])))
        rep[mat] = dict(couverture_brut=round(float(cov), 4),
                        ecart_couverture=round(float(abs(cov - ref['couverture'])), 4),
                        distance_mediane=round(dist, 1))
    return rep


def main():
    O.mkdir(parents=True, exist_ok=True)
    cfgs = {'jungle': sample('junglewaterfallzonepmdsky.png', rules_jungle),
            'southern': sample('Southern_Jungle_exit_2_S.png', rules_southern)}
    extra = {'jungle': [], 'southern': ['- INTERDIT marron : 0 px marron echantillonne (troncs verts sombres).']}
    bruts = {'jungle': ['source/jungle_generee_v2/bruts/terrain_strict.png'],
             'southern': ['source/jungle_generee_v2/bruts/arbres_canoniques.png']}
    rules = {'jungle': rules_jungle, 'southern': rules_southern}
    for name, cfg in cfgs.items():
        (O / f'{name}_config.json').write_text(json.dumps(cfg, indent=1), encoding='utf-8')
        sheet(cfg, O / f'{name}_palette.png')
        (O / f'{name}_contraintes.txt').write_text(prompt_constraints(cfg, extra[name]), encoding='utf-8')
        audit = {b: audit_brut(R / b, cfg, rules[name]) for b in bruts[name]}
        (O / f'{name}_audit_bruts.json').write_text(json.dumps(audit, indent=1), encoding='utf-8')
    print('OK sampler v2 :', sorted(p.name for p in O.iterdir()))


if __name__ == '__main__':
    main()
