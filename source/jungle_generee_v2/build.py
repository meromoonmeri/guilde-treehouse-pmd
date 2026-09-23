"""Jungle generee V2 — terrain strict sur magenta, 5 calques, echelle PMDO.

Bruts (art GENERE refere PMD, PAS natif) :
  bruts/terrain_strict.png    848x1264 : clairiere, 6 chutes coupees en haut, 2 bassins, palmiers cotes
  bruts/arbres_canoniques.png 1179x896 : 6 arbres jungle (troncs + canopees palmees)
  ../suite_generee_v1/bruts/jungle_cascades_sol.png : sol herbe plein cadre (reutilise)

Normalisation UNIFORME (jamais anisotrope) : terrain NEAREST x0.5 -> 424x632 pose a
(44,0) dans la scene 512x640 ; pixels nets, aucune interpolation. Scene = 64x80 cases
de 8px, prete import PNG to Tileset 8px (TexSize=1), proportions PMD Sky (arbre ~170px).

5 calques (recomposition exacte par construction, partition du terrain) :
  01_sol        : sol genere plein cadre (cover 0.833 LANCZOS + crop centre)
  02_paroi      : falaise + frange haute (opaque, y<290, hors chutes/eau)
  03_cascades   : 6 chutes, calque propre, 18 phases x 16px = boucle 288px exacte, 80ms
  04_bassins    : eau + ecume (masques eau dans 2 boites, colonnes masquees jusqu'en pleine ecume)
  05_vegetation : residu terrain (palmiers, herbe, chemin, buissons) + 2 arbres canoniques x0.45

Animation = roulement vertical, mouvement NOUVEAU, pas un cycle officiel.
"""
from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd

R = Path(__file__).resolve().parents[2]
SRC = R / 'source/jungle_generee_v2/bruts'
O = R / 'renders/jungle_generee_v2'
W, H = 512, 640
PREFIX = 'JungleG2'
PHASES, STEP, FRAME_MS = 18, 16, 80
FEET_Y = PHASES * STEP  # 288 : pieds en pleine ecume
assert FEET_Y == 288
OFFSETS = [0, 48, 96, 32, 128, 80]

# Bandes de chutes (scene 512x640, depuis detection x0.5 +44) ; pieds = FEET_Y
BANDS = [(123, 136), (163, 206), (229, 242), (269, 282), (306, 348), (375, 388)]
# Boites bassins (scene) ; eau gardee par masque colorimetrique, pas au rectangle brut
BASIN_BOXES = [(115, 270, 245, 375), (265, 270, 395, 375)]
WALL_BOTTOM = 290
TREES = [((13, 38, 390, 438), (0, 470)), ((798, 458, 1169, 883), (342, 465))]


def flood_magenta(rgb):
    """Alpha par inondation depuis les bords (magenta-like) + seuil serre global."""
    mg = (rgb[:, :, 0] > 200) & (rgb[:, :, 2] > 150) & (rgb[:, :, 1] < 120)
    h, w = mg.shape
    seed = np.zeros((h, w), bool)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    back = nd.binary_propagation(seed, mask=mg)
    cooked = (rgb[:, :, 0] > 180) & (rgb[:, :, 2] > 130) & (rgb[:, :, 1] < 140) & \
             (rgb[:, :, 0] > rgb[:, :, 1] + 60)
    # Liseres violets anti-aliases du generateur : min(R,B)-G eleve (surs pour cette palette)
    stain = (np.minimum(rgb[:, :, 0].astype(int), rgb[:, :, 2].astype(int)) -
             rgb[:, :, 1].astype(int) > 25)
    darkmag = (rgb[:, :, 0] > 30) & (rgb[:, :, 2] > 30) & (rgb[:, :, 1] < 35)
    return ~(back | cooked | stain | darkmag)


def build():
    O.mkdir(parents=True, exist_ok=True)
    # ---- terrain normalise x0.5 NEAREST pose a (44,0) ----
    terr = Image.open(SRC / 'terrain_strict.png').convert('RGB').resize((424, 632), Image.NEAREST)
    ta = np.array(terr).astype(int)
    scene = np.zeros((H, W, 3), np.uint8)
    scene[0:632, 44:468] = np.array(terr)
    alpha = np.zeros((H, W), bool)
    alpha[0:632, 44:468] = flood_magenta(ta)
    rgb = scene.astype(int)

    blue = (rgb[:, :, 2] > 90) & (rgb[:, :, 2] > rgb[:, :, 0] - 10)
    bright = rgb.sum(2) > 520
    water_like = blue | bright
    band = np.zeros((H, W), bool)
    for x0, x1 in BANDS:
        band[0:FEET_Y, x0:x1] = True
    box = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in BASIN_BOXES:
        box[y0:y1, x0:x1] = True

    falls_m = alpha & band
    basin_m = alpha & box & water_like & ~(band & (np.arange(H)[:, None] < FEET_Y))
    wall_m = alpha & (np.arange(H)[:, None] < WALL_BOTTOM) & ~falls_m & ~basin_m
    resid_m = alpha & ~falls_m & ~basin_m & ~wall_m

    layers = {}
    # 01 sol plein cadre
    sol = Image.open(R / 'source/suite_generee_v1/bruts/jungle_cascades_sol.png').convert('RGB')
    sw, sh = sol.size
    f = max(W / sw, H / sh)
    sol = sol.resize((int(sw * f + 0.5), int(sh * f + 0.5)), Image.LANCZOS)
    x0 = (sol.width - W) // 2
    y0 = (sol.height - H) // 2
    layers['01_sol'] = np.array(sol.crop((x0, y0, x0 + W, y0 + H))).astype(np.uint8)

    def grab(m):
        out = np.zeros((H, W, 4), np.uint8)
        out[m, :3] = scene[m]
        out[m, 3] = 255
        return out

    layers['02_paroi'] = grab(wall_m)
    layers['04_bassins'] = grab(basin_m)
    veg = grab(resid_m)
    # arbres canoniques x0.45 par-dessus le residu
    tr = np.array(Image.open(SRC / 'arbres_canoniques.png').convert('RGB'))
    tops = []
    for (tx0, ty0, tx1, ty1), (px, py) in TREES:
        cut = tr[ty0:ty1, tx0:tx1].copy()
        m = flood_magenta(cut)
        # Decontamination : propager les couleurs opaques sous le transparent (anti-halo magenta)
        fill = cut.copy()
        cur = m.copy()
        for _ in range(10):
            nxt = nd.binary_dilation(cur) & ~cur
            if not nxt.any():
                break
            for c in range(3):
                ch = fill[:, :, c].astype(float)
                tot = nd.uniform_filter(ch * cur, 3, mode='nearest')
                cnt = nd.uniform_filter(cur.astype(float), 3, mode='nearest')
                fill[nxt, c] = (tot[nxt] / np.maximum(cnt[nxt], 1e-6)).clip(0, 255)
            cur |= nxt
        rgba = np.zeros((cut.shape[0], cut.shape[1], 4), np.uint8)
        rgba[:, :, :3] = fill
        rgba[m, 3] = 255
        im = Image.fromarray(rgba)
        nw, nh = int(im.width * 0.45), int(im.height * 0.45)
        im = im.resize((nw, nh), Image.LANCZOS)
        r, g, b, al = im.split()  # alpha binaire style PMD : tue la frange semi-transparente
        al = al.point(lambda a: 255 if a >= 128 else 0)
        im = Image.merge('RGBA', (r, g, b, al))
        px = min(px, W - nw)
        py = min(py, H - nh)
        base = Image.fromarray(veg)
        base.alpha_composite(im, (px, py))
        veg = np.array(base)
        tops.append(dict(src=[tx0, ty0, tx1, ty1], echelle=0.45, taille=[nw, nh], position=[px, py]))
    layers['05_vegetation'] = veg

    for n, a in layers.items():
        if n != '01_sol':
            assert a.shape == (H, W, 4)
    assert (layers['01_sol'].shape == (H, W, 3))

    # ---- 03 cascades : 18 phases, roulement pleine hauteur ----
    base = np.zeros((H, W, 4), np.uint8)
    base[falls_m, :3] = scene[falls_m]
    base[falls_m, 3] = 255
    fdir = O / 'cascades_phases'
    fdir.mkdir(exist_ok=True)
    for x0, x1 in BANDS:  # remontee au bord haut (chutes coupees, pas de ciel)
        col = base[0:FEET_Y, x0:x1]
        rows = np.where((col[:, :, 3] > 0).any(1))[0]
        if len(rows) and rows[0] > 0:
            col[0:rows[0]] = col[rows[0]]
    cols = []
    for x0, x1 in BANDS:
        cols.append(base[0:FEET_Y, x0:x1].copy())
    for p in range(PHASES):
        rgba = np.zeros((H, W, 4), np.uint8)
        for (x0, x1), col, off in zip(BANDS, cols, OFFSETS):
            rgba[0:FEET_Y, x0:x1] = np.roll(col, off + p * STEP, axis=0)
        Image.fromarray(rgba).save(fdir / f'{PREFIX}_03_cascades_phase_{p:02d}.png')
    Image.open(fdir / f'{PREFIX}_03_cascades_phase_00.png').save(O / f'{PREFIX}_03_cascades.png')

    # ---- exports ----
    for n in ('01_sol', '02_paroi', '04_bassins', '05_vegetation'):
        a = layers[n]
        im = Image.fromarray(a) if a.shape[2] == 4 else Image.fromarray(a, 'RGB').convert('RGBA')
        im.save(O / f'{PREFIX}_{n}.png')
        root = ET.Element('tileset', version='1.10', name=f'{PREFIX}_{n}', tilewidth='8',
                          tileheight='8', columns=str(W // 8), tilecount=str(W // 8 * (H // 8)))
        ET.SubElement(root, 'image', source=f'{PREFIX}_{n}.png', width=str(W), height=str(H))
        ET.ElementTree(root).write(O / f'{PREFIX}_{n}.tsx', encoding='utf-8', xml_declaration=True)
    root = ET.Element('tileset', version='1.10', name=f'{PREFIX}_03_cascades', tilewidth='8',
                      tileheight='8', columns=str(W // 8), tilecount=str(W // 8 * (H // 8)))
    ET.SubElement(root, 'image', source=f'{PREFIX}_03_cascades.png', width=str(W), height=str(H))
    ET.ElementTree(root).write(O / f'{PREFIX}_03_cascades.tsx', encoding='utf-8', xml_declaration=True)

    bottom = Image.open(O / f'{PREFIX}_01_sol.png').convert('RGBA')
    bottom.alpha_composite(Image.open(O / f'{PREFIX}_02_paroi.png').convert('RGBA'))
    top = Image.open(O / f'{PREFIX}_04_bassins.png').convert('RGBA')
    top.alpha_composite(Image.open(O / f'{PREFIX}_05_vegetation.png').convert('RGBA'))
    frames = []
    for p in range(PHASES):
        c = bottom.copy()
        c.alpha_composite(Image.open(fdir / f'{PREFIX}_03_cascades_phase_{p:02d}.png'))
        c.alpha_composite(top)
        if p == 0:
            c.save(O / f'{PREFIX}_composite_phase_00.png')
        frames.append(c.convert('RGB'))
    frames[0].save(O / f'{PREFIX}_animation.gif', save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0)
    tw, th = 128, 160
    sheet = Image.new('RGB', (tw * 9, th * 2), (255, 0, 255))
    for p, fr in enumerate(frames):
        sheet.paste(fr.resize((tw, th), Image.NEAREST), ((p % 9) * tw, (p // 9) * th))
    sheet.save(O / f'{PREFIX}_planche_18_phases.png')

    names = ['01_sol', '02_paroi', '03_cascades', '04_bassins', '05_vegetation']
    zp = O / f'{PREFIX}_5_calques.ora'
    if zp.exists():
        zp.unlink()
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('mimetype', 'image/openraster')
        img = ET.Element('image', w=str(W), h=str(H))
        st = ET.SubElement(img, 'stack', name='racine')
        for i, n in enumerate(names):
            ET.SubElement(st, 'layer', name=n, src=f'data/{i}.png')
            z.write(O / f'{PREFIX}_{n}.png', f'data/{i}.png')
        z.writestr('stack.xml', ET.tostring(img, encoding='utf-8', xml_declaration=True))
        z.write(O / f'{PREFIX}_composite_phase_00.png', 'mergedimage.png')

    manifest = dict(
        id='jungle_generee_v2', title='Jungle generee V2 — terrain strict magenta, 5 calques',
        methode='generee_magenta', natif=False, size=[W, H], orientation='SOUTH_TO_NORTH',
        pmdo_scale=dict(cases_8px=[W // 8, H // 8], texsize=1, importe='PNG to Tileset 8px, sans reechantillonnage',
                        note='proportions PMD Sky : arbre ~170px ; normalisation uniforme x0.5 NEAREST (terrain), x0.45 (arbres)'),
        bruts=['source/jungle_generee_v2/bruts/terrain_strict.png',
               'source/jungle_generee_v2/bruts/arbres_canoniques.png',
               'source/suite_generee_v1/bruts/jungle_cascades_sol.png'],
        layers=[dict(id=n, file=f'{PREFIX}_{n}.png') for n in
               ['01_sol', '02_paroi', '03_cascades', '04_bassins', '05_vegetation']],
        partition=dict(bandes_chutes=BANDS, pieds_y=FEET_Y, boites_bassins=BASIN_BOXES,
                       bas_paroi_y=WALL_BOTTOM, arbres_annexes=tops),
        animation=dict(layer='03_cascades', phases=PHASES, step_px=STEP,
                       frame_ms=FRAME_MS, loop_ms=PHASES * FRAME_MS, offsets=OFFSETS,
                       method='generated pixels vertical roll over full 288px height, 18x16 loop exact, NEW movement'),
        operations=[dict(op='normalisation terrain x0.5 NEAREST a (44,0)', magenta='inondation bords + seuil serre'),
                    dict(op='partition terrain en 4 masques + sol genere + 2 arbres x0.45')],
        runtime='NOT TESTED', art_approved=False,
        notes=['Art GENERE refere PMD, pas natif : aucune revendication pixel-exact canonique.',
               'Chutes coupees au bord haut, pieds en pleine ecume, calque propre anime.',
               'Recomposition exacte par construction (partition sans recouvrement ni trou).'])
    (O / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    man = build()
    print('OK', man['id'], len(man['layers']), 'layers,', man['animation']['phases'], 'phases')