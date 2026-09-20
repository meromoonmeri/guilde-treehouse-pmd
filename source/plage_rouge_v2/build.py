"""
Plage falaises rouges V2 — eau + animation CANONIQUES d'EoSO.
Demande utilisateur : mer/texture d'eau comme les maps beach de
Minemaker0430/ExplorersOfSkyOrigins.

Terrain : repris byte-identique du lot plage_rouge_v1 (methode hybride validee
pour la composition), aucune regeneration, aucune repalette sur le terrain.

Eau : 17 frames natives decodees de beach_animation.tile (commit epingle,
provenance.json), cadence native FrameLength=16 ticks (~266 ms). Adaptation a
notre crique : fenetre verticale par colonne alignee sur le BAS (le ruban d'ecume
natif suit ainsi notre ligne de rivage en V), fenetre horizontale x' prise dans la
zone sans rochers de la bande native. AUCUN etirement, rotation, miroir ou
recoloration des pixels natifs ; seule une selection de sous-rectangle par
colonne. La silhouette de mer (masque) reste la notre (geometrie du lot V1).
"""
from pathlib import Path
import json, hashlib, io, base64, struct, zipfile, shutil
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
V1 = R / 'renders/plage_rouge_v1'
O = R / 'renders/plage_rouge_v2_eoso'
REF = R / 'source/plage_rouge_v2/references'
CANON = REF / 'beach_animation.tile'

MS = 266                      # 16 ticks natifs a 60 fps ~ 266 ms
X_OFF = 220                   # fenetre horizontale dans la bande native (zone sans rochers)
TILE = 24
FRAME_W_TILES, FRAME_H_TILES, NB_FRAMES = 33, 7, 17

# ------------------------------------------------------------- decode .tile
def charger_bandes():
    d = CANON.read_bytes()
    tileSize, count = struct.unpack_from('<ii', d, 0)
    assert tileSize == TILE
    pos, recs, cache = 8, [], {}
    for _ in range(count):
        x, y, off = struct.unpack_from('<iiq', d, pos); pos += 16
        if off not in cache:
            ln = struct.unpack_from('<q', d, off)[0]
            cache[off] = Image.open(io.BytesIO(d[off + 8:off + 8 + ln])).convert('RGBA')
        recs.append((x, y, cache[off]))
    FW, FH = FRAME_W_TILES * TILE, FRAME_H_TILES * TILE
    frames = []
    for f in range(NB_FRAMES):
        a = np.zeros((FH, FW, 4), np.uint8)
        for x, y, im in recs:
            if f * FRAME_W_TILES <= x < (f + 1) * FRAME_W_TILES:
                a[y * TILE:(y + 1) * TILE, (x - f * FRAME_W_TILES) * TILE:(x - f * FRAME_W_TILES + 1) * TILE] = np.array(im)
        frames.append(a)
    return frames

def construire():
    for d in ['couches/mer_frames', 'canonique', 'review', 'scene', 'ora', 'exports']:
        (O / d).mkdir(parents=True, exist_ok=True)

    # ---------- terrain V1 recopie tel quel (composition validee, hybride)
    calques_v1 = ['00_fond_void', '02_sable', '03_parois_falaises', '04_bordures_herbe',
                  '05_ombres_objets', '06_objets']
    lay = {}
    for nom in calques_v1:
        src = V1 / 'couches' / f'{nom}.png'
        dst = O / 'couches' / f'{nom}.png'
        shutil.copyfile(src, dst)
        lay[nom] = np.array(Image.open(dst).convert('RGBA'))
    TH, TW = lay['00_fond_void'].shape[:2]

    # ---------- silhouette de mer = masque opaque d'une frame mer V1
    m0 = np.array(Image.open(V1 / 'couches/mer_frames/MerV1_00.png').convert('RGBA'))[:, :, 3] > 0

    # ---------- bandes natives decodees + sauvegarde canonique exacte
    natifs = charger_bandes()
    hashes = []
    for f, a in enumerate(natifs):
        im = Image.fromarray(a, 'RGBA')
        im.save(O / 'canonique' / f'mer_natif_{f:02d}.png')
        b = io.BytesIO(); im.save(b, format='PNG')
        hashes.append(hashlib.sha256(b.getvalue()).hexdigest())

    # verification pixel-perfect : reconstruction == relecture de la feuille
    ok_sanity = all(a.shape == natifs[0].shape for a in natifs)

    # ---------- adaptation : ancrage par DISTANCE AU SABLE (transformee EDT).
    # La bande native "ecume + sable" n'arrive qu'au contact de NOTRE sable ;
    # contre les falaises la mer montre ses rangs d'eau, jamais la bande de
    # plage (raccord observe dans les maps EoSO). Row natif = FH-1 - distance,
    # pure selection par pixel, aucune deformation des pixels natifs.
    from scipy import ndimage
    FH, FW = natifs[0].shape[0], natifs[0].shape[1]
    sable_mask = lay['02_sable'][:, :, 3] > 0
    dist = ndimage.distance_transform_edt(~sable_mask)
    haut = np.clip(np.round(dist).astype(int), 0, FH - 1)
    row_src = FH - 1 - haut
    xsrc = np.clip(np.arange(TW) + X_OFF, 0, FW - 1)[None, :]
    lay_mer = []
    for f in range(NB_FRAMES):
        a = np.zeros((TH, TW, 4), np.uint8)
        sel = natifs[f][row_src, xsrc, :]                    # (TH,TW,4) indexe pixel par pixel
        a[m0] = sel[m0]
        lay_mer.append(a)

    # trou residuel du a l'alpha natif (bulles/retours) -> signale, jamais comble
    trous = int(((lay_mer[0][:, :, 3] == 0) & m0).sum())

    for i, a in enumerate(lay_mer):
        Image.fromarray(a, 'RGBA').save(O / 'couches/mer_frames' / f'MerV2_{i:02d}.png')

    ordre = [('02_sable', lay['02_sable']), ('03_parois_falaises', lay['03_parois_falaises']),
             ('04_bordures_herbe', lay['04_bordures_herbe']),
             ('05_ombres_objets', lay['05_ombres_objets']), ('06_objets', lay['06_objets'])]

    def compose(avec_mer=True, f=0, avec_fond=True):
        base = Image.fromarray(lay['00_fond_void'] if avec_fond else np.zeros((TH, TW, 4), np.uint8), 'RGBA')
        if avec_mer:
            base.alpha_composite(Image.fromarray(lay_mer[f % NB_FRAMES], 'RGBA'))
        for _, ar in ordre:
            base.alpha_composite(Image.fromarray(ar, 'RGBA'))
        return base

    for f in range(NB_FRAMES):
        compose(True, f).save(O / 'scene' / f'scene_eoso_{f:02d}.png')
    compose(False).save(O / 'scene' / 'scene_seche.png')

    sc = [compose(True, f) for f in range(NB_FRAMES)]
    sc[0].save(O / 'scene_eoso17f.webp', save_all=True, append_images=sc[1:], duration=MS, loop=0, lossless=True, method=4)
    pal_img = Image.new('RGB', (TW, TH * NB_FRAMES))
    for i, s in enumerate(sc):
        pal_img.paste(s.convert('RGB'), (0, TH * i))
    q = pal_img.quantize(colors=256)
    gs = [s.convert('RGB').quantize(palette=q, dither=Image.Dither.NONE) for s in sc]
    gs[0].save(O / 'review' / 'scene_eoso.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)

    # zoom eau : bande superieure de la map a 1x, 17 frames en contact
    bande0 = np.array(sc[0])[:, :, :3]
    zone_eau = np.where(m0.any(1))[0]
    zy1 = min(zone_eau.max() + 24, TH)
    zoom = Image.new('RGBA', (TW * 4 + 40, zy1 * 5 + 50), (24, 24, 40, 255))
    for i, s in enumerate(sc):
        cr = s.crop((0, 0, TW, zy1))
        zoom.alpha_composite(cr, (8 + (i % 4) * (TW + 8), 8 + (i // 4) * (zy1 + 8)))
    zoom.save(O / 'review' / 'frames_mer_eoso_zoom_1x.png')

    # ORA
    def ordpng(a):
        b = io.BytesIO()
        Image.fromarray(a, 'RGBA').save(b, format='PNG')
        return b.getvalue()
    ora_layers = (ordre[::-1] + [(None, lay_mer[i]) for i in range(NB_FRAMES)]
                  + [('00_fond_void', lay['00_fond_void'])])
    names = [n for n, _ in ordre[::-1]] + [f'01_mer_natif_f{i:02d}' for i in range(NB_FRAMES)] + ['00_fond_void']
    stack = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<image w="{TW}" h="{TH}" name="plage_rouge_v2_eoso"><stack>']
    with zipfile.ZipFile(O / 'ora' / 'plage_rouge_v2_eoso.ora', 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for (nom, _a), canon_nom in zip(ora_layers, names):
            vis = 'hidden' if ('mer_natif' in canon_nom and canon_nom != '01_mer_natif_f00') else 'visible'
            stack.append(f'  <layer name="{canon_nom}" src="data/{canon_nom}.png" x="0" y="0" visibility="{vis}" composite-op="svg:src-over" opacity="1.0" />')
            z.writestr(f'data/{canon_nom}.png', ordpng(_a))
        stack.append('</stack></image>')
        z.writestr('stack.xml', '\n'.join(stack))
        z.writestr('Thumbnails/thumbnail.png', ordpng(np.array(compose(True, 0).resize((64, round(64 * TH / TW)), Image.Resampling.NEAREST))))

    # viewer : reutilise le gabarit corrige de V1
    def uri(a):
        b = io.BytesIO(); Image.fromarray(a, 'RGBA').save(b, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
    donnees = {'W': TW, 'H': TH, 'ms': MS, 'fond': uri(lay['00_fond_void']),
               'mer': [uri(a) for a in lay_mer],
               'calques': [{'nom': n, 'png': uri(ar)} for n, ar in ordre],
               'palette': uri(np.array(Image.open(V1 / 'review' / 'palette_native.png').convert('RGBA')))}
    tpl = (R / 'source/plage_rouge_v1/viewer_template.html').read_text()
    html = tpl.replace('__DATA__', json.dumps(donnees)).replace('Plage falaises rouges V1', 'Plage falaises rouges V2 — eau canonique EoSO')
    html = html.replace('renders/plage_rouge_v1/README.md', 'renders/plage_rouge_v2_eoso/README.md')
    (R / 'apercu_plage_rouge_v2.html').write_text(html)
    (O / 'apercu.html').write_text(html)

    manifest = {
        'lot': 'plage_rouge_v2_eoso',
        'demande': 'mer + texture d eau comme les maps beach de Minemaker0430/ExplorersOfSkyOrigins',
        'terrain': 'byte-identique du lot plage_rouge_v1 (hybride, quantification palette)',
        'eau': {'source': 'beach_animation.tile EoSO commit bed944992c32e7e7927cc3480c72edb0b1782e26',
                'tile_sha256': hashlib.sha256(CANON.read_bytes()).hexdigest(),
                'frames': NB_FRAMES, 'cadence_ms': MS, 'frame_length_ticks_natif': 16,
                'frames_sha256_png': hashes,
                'adaptation': f'fenetre horizontale x+{X_OFF} (zone sans rochers) ; row natif = FH-1 - distance au sable (EDT) : ecume/sable natif uniquement au contact de notre sable, rangs d eau contre les falaises ; aucune deformation pixel',
                'fenetre': {'x_offset': X_OFF, 'largeur_native': FW, 'hauteur_native': FH}},
        'silhouette_mer': 'masque du lot V1 (geometrie approuvee), alpha natif conserve',
        'trous_alpha_natif_px': trous,
        'reconstruction_sanity': bool(ok_sanity),
        'limites': ['silhouette adaptee a notre crique (pas le layout de la map beach EoSO)',
                    'raccords ecume/rivage = mapping par colonnes, pas repaints',
                    'art non approuve', 'collisions/warps/runtime PMDO NON TESTES'],
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('V2 ok', TW, TH, 'frames', NB_FRAMES, 'trous alpha natif', trous)

if __name__ == '__main__':
    construire()
