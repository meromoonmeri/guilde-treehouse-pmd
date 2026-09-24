"""Controles entree_crooked_v1 : partition generee, natifs exacts, recomposition, chemin."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as ndi
from night import night

SRC = R / 'source/entree_crooked_v1'
OUT = R / 'renders/entree_crooked_v1'
W, H = 848, 1264
PFX = 'EntreeCrookedV1'
ok = []


def check(name, cond, detail=''):
    assert cond, f'FAIL {name} {detail}'
    ok.append(name)
    print(f'PASS {name} {detail}')


def main():
    man = json.loads((OUT / 'manifest.json').read_text())
    check('manifeste', man['canevas'] == [W, H] and len(man['ordre']) == 8)
    check('brut-sha', hashlib.sha256((SRC / 'bruts/G1b_paroi_bouche.png').read_bytes()).hexdigest()
          == man['bruts']['G1b_paroi_bouche.png']['sha256'])
    G = np.array(Image.open(SRC / 'bruts/G1b_paroi_bouche.png').convert('RGBA'))
    L = {}
    for n in man['ordre']:
        im = Image.open(OUT / f'{PFX}_{n}_jour.png').convert('RGBA')
        check(n + '-taille', im.size == (W, H))
        L[n] = np.array(im)
        check(n + '-nuit-abyss-x1', (np.array(night(im)) ==
              np.array(Image.open(OUT / f'{PFX}_{n}_nuit.png').convert('RGBA'))).all())
    # couches generees : sous-ensemble exact du brut, partition du canevas
    m2, m3, m4 = (L['02_chemin_sable'][:, :, 3] > 0), (L['03_paroi'][:, :, 3] > 0), (L['04_bouche'][:, :, 3] > 0)
    check('gen-disjoints', not ((m2 & m3).any() or (m2 & m4).any() or (m3 & m4).any()))
    lumG = G[..., :3].mean(2)
    funnel = np.zeros((H, W), bool)
    funnel[600:700, 360:490] = True
    allowed = (lumG > 175) | (funnel & (lumG > 85))
    check('gen-chemin-matiere', allowed[m2].all())
    check('gen-couvrent-non-sable', ((m3 | m4) | allowed).all())
    for n, m in (('02_chemin_sable', m2), ('03_paroi', m3), ('04_bouche', m4)):
        check(n + '-pixels-G1b', (L[n][m] == G[m]).all(), f'{m.sum()} px')
    # natifs : arbres, rochers, fleurs exacts
    L3 = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png')
    L4 = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png')
    SH = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png')
    OB = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png')
    tr, ca = Image.fromarray(L['07_troncs']), Image.fromarray(L['08_canopees'])
    for i, (x, y) in enumerate(man['arbres']):
        check(f'arbre{i}-tronc', list(tr.crop((x + 56, y + 64, x + 104, y + 120)).getdata())
              == list(L3.crop((72, 160, 120, 216)).getdata()))
        check(f'arbre{i}-canopee', list(ca.crop((x, y, x + 144, y + 120)).getdata())
              == list(L4.crop((16, 96, 160, 216)).getdata()))
    ro = Image.fromarray(L['05_rochers'])
    for n, r in man['rochers'].items():
        b, (x, y) = r['box'], r['pos']
        ref = Image.new('RGBA', (b[2] - b[0], b[3] - b[1]))
        ref.alpha_composite(SH.crop(tuple(b)))
        ref.alpha_composite(OB.crop(tuple(b)))
        check(n + '-natif', list(ro.crop((x, y, x + ref.width, y + ref.height)).getdata()) == list(ref.getdata()))
    fl = [Image.open(OUT / (f'{PFX}_06_fleurs' + (f'_phase{p}_jour.png' if p else '_jour.png'))).convert('RGBA')
          for p in range(4)]
    for s in man['fleurs']['sites']:
        for p in range(4):
            ref = Image.open(R / f"renders/applewoods_skygrass_v1/sprites/fleur_sky_{s['sprite']:02}_phase_{(p + s['off']) % 4:02}.png").convert('RGBA')
            got = fl[p].crop((s['x'], s['y'], s['x'] + ref.width, s['y'] + ref.height))
            assert list(got.getdata()) == list(ref.getdata()), (s, p)
    check('fleurs-4phases-natives', True, f"{len(man['fleurs']['sites'])} sites x4")
    # herbe : opaque + couleurs dans la palette du GIF natif
    gif = np.array(Image.open(R / 'source/sky_peak_v1/gif_0.png').convert('RGB'))
    pal = set(map(tuple, gif.reshape(-1, 3)[::7].tolist()))
    herb = L['01_sol_herbe']
    check('herbe-opaque', (herb[:, :, 3] > 0).all())
    samp = herb[::16, ::16, :3].reshape(-1, 3)
    check('herbe-palette-gif', all(tuple(px) in pal for px in samp), f'{len(samp)} echantillons')
    # recompositions
    for m in ('jour', 'nuit'):
        comp = Image.new('RGBA', (W, H))
        for n in man['ordre']:
            comp.alpha_composite(Image.open(OUT / f'{PFX}_{n}_{m}.png').convert('RGBA'))
        check('recomposition-' + m, ImageChops.difference(
            comp, Image.open(OUT / f'composite_{m}.png').convert('RGBA')).getbbox() is None)
    for p in range(4):
        comp = Image.new('RGBA', (W, H))
        for n in man['ordre']:
            f = f'{PFX}_06_fleurs_phase{p}_jour.png' if (n == '06_fleurs' and p) else f'{PFX}_{n}_jour.png'
            comp.alpha_composite(Image.open(OUT / f).convert('RGBA'))
        check(f'recomposition-phase{p}', ImageChops.difference(
            comp, Image.open(OUT / f'composite_phase{p}_jour.png').convert('RGBA')).getbbox() is None)
    # chemin sud -> bouche
    walk = m2 | m4
    lab, _ = ndi.label(walk)
    bottom = set(lab[H - 1][walk[H - 1]])
    check('chemin-sud-nord', lab[610, 424] in bottom and lab[610, 424] > 0)
    # ORA
    z = zipfile.ZipFile(OUT / f'{PFX.lower()}.ora')
    names = z.namelist()
    check('ora', 'stack.xml' in names and sum(n.startswith('data/') for n in names) == 11, f'{len(names)} entrees')
    (OUT / 'verification.json').write_text(json.dumps(dict(all_pass=True, checks=ok), indent=1, ensure_ascii=False))
    print(f'{len(ok)} controles PASS')


if __name__ == '__main__':
    main()
