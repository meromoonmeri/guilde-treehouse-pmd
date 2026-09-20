"""Contrôle indépendant des cartes plage canoniques (sprites/beach_canonique_v1).

Ne réimporte pas le build : relit les feuilles natives, les pins, les PNG de
calques et les .tmj. Vérifie :
1. hashes + blobs Git des trois feuilles EoSO ;
2. chaque cellule 24 px de chaque calque est la copie exacte d'une tuile native
   de sa feuille (back->layer1, eau->beach_animation, front->layer2) ;
3. l'eau rejoue le cycle natif : frame f = TexLoc + 33*f de la frame 0 ;
4. 17 frames d'eau distinctes ;
5. recomposition des calques depuis carte.tmj = PNG livrés.
Usage : python source/verify_beach_canonique.py
"""
from pathlib import Path
from PIL import Image
import json, hashlib, struct, io

R = Path(__file__).resolve().parents[1]
O = R / 'sprites/beach_canonique_v1'
M = json.loads((O / 'provenance.json').read_text())
P = json.loads((R / 'source/beach_eoso/sources_eoso.json').read_text())
assert P['commit'] == M['commit']
T, FRAMES, STRIDE = M['tile_px'], M['frames'], M['stride']
L1, L2, BA = 'D01P11A_layer1', 'D01P11A_layer2', 'beach_animation'


def read_native(name):
    p = R / 'source/beach_eoso/natifs' / f'{name}.tile'
    raw = p.read_bytes()
    info = P['sources'][name]
    assert hashlib.sha256(raw).hexdigest() == info['sha256']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == info['git_blob_sha1']
    size, n = struct.unpack_from('<II', raw)
    assert size == T
    tiles = {}
    for i in range(n):
        x, y, off = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
        length = struct.unpack_from('<q', raw, off)[0]
        im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
        tiles[x, y] = im
    return tiles


sheets = {name: read_native(name) for name in (L1, L2, BA)}
BYTES = {name: {t.tobytes(): (x, y) for (x, y), t in sheets[name].items()} for name in (L1, L2, BA)}
COLW = {name: max(x for x, y in sheets[name]) + 1 for name in (L1, L2, BA)}

reports = []
for rec in M['maps']:
    d = O / rec['id']
    GW, GH = rec['cellules']
    back = Image.open(d / 'calques/back.png').convert('RGBA')
    front = Image.open(d / 'calques/front.png').convert('RGBA')
    waters = [Image.open(d / 'calques' / f'eau_{f + 1:02d}.png').convert('RGBA') for f in range(FRAMES)]

    def cells(im):
        for y in range(GH):
            for x in range(GW):
                yield x, y, im.crop((x * T, y * T, x * T + T, y * T + T))

    for x, y, c in cells(back):
        assert c.tobytes() in BYTES[L1], f'{rec["id"]} back ({x},{y}) non natif'
    for x, y, c in cells(front):
        assert c.getbbox() is None or c.tobytes() in BYTES[L2], f'{rec["id"]} front ({x},{y}) non natif'

    # Toutes les frames d'abord : nativité simple.
    cell_bytes = [[None] * GW for _ in range(GH)]
    hashes = set()
    for f, w in enumerate(waters):
        hashes.add(hashlib.sha256(w.tobytes()).hexdigest())
        for x, y, c in cells(w):
            if c.getbbox() is None:
                continue
            b = c.tobytes()
            assert b in BYTES[BA], f'{rec["id"]} eau f{f} ({x},{y}) non natif'
            if f == 0:
                cell_bytes[y][x] = b
    # Puis cycle natif : la séquence de chaque cellule doit être l'un des
    # 33 cycles de colonnes (pas +33 par frame), tuiles identiques comprises.
    ALL = {}
    for (sx, row), t in sheets[BA].items():
        ALL.setdefault(t.tobytes(), []).append((sx, row))
    for y in range(GH):
        for x in range(GW):
            b0 = cell_bytes[y][x]
            if b0 is None:
                continue
            seq = []
            for f in range(1, FRAMES):
                c = waters[f].crop((x * T, y * T, x * T + T, y * T + T)).tobytes()
                seq.append(c)
            ok = False
            for sx, row in ALL[b0]:
                if all(sheets[BA].get((sx + STRIDE * f, row)) is not None and
                       sheets[BA][(sx + STRIDE * f, row)].tobytes() == seq[f - 1]
                       for f in range(1, FRAMES)):
                    ok = True
                    break
            assert ok, f'{rec["id"]} eau ({x},{y}) : séquence hors cycles natifs'
    assert len(hashes) == FRAMES

    # Recomposition tmj -> PNG.
    tm = json.loads((d / 'carte.tmj').read_text())
    assert (tm['width'], tm['height'], tm['tilewidth'], tm['tileheight']) == (GW, GH, T, T)
    tsj_imgs = {}
    for tsr in tm['tilesets']:
        name = tsr['source'][3:-4]
        img = Image.open(O / f'{name}.png').convert('RGBA')
        tsj_imgs[tsr['firstgid']] = (name, img, json.loads((O / f'{name}.tsj').read_text()))
    for layer, png in zip(tm['layers'], ['back.png', 'eau_01.png', 'front.png']):
        firstgids = [g for g in sorted(tsj_imgs, reverse=True)]
        out = Image.new('RGBA', (GW * T, GH * T))
        for i, gid in enumerate(layer['data']):
            if not gid:
                continue
            fg = max(g for g in firstgids if g <= gid)
            name, img, tsj = tsj_imgs[fg]
            tid = gid - fg
            cols = tsj['columns']
            out.paste(img.crop(((tid % cols) * T, (tid // cols) * T,
                                (tid % cols) * T + T, (tid // cols) * T + T)),
                      ((i % GW) * T, (i // GW) * T))
        assert out.tobytes() == Image.open(d / 'calques' / png).convert('RGBA').tobytes(), \
            f'{rec["id"]} tmj != {png}'
    reports.append({'layout': rec['id'], 'native_px': [GW * T, GH * T], 'cells': [GW, GH],
                    'water_frames': FRAMES, 'frame_ticks': M['frame_ticks'],
                    'non_native_cells': 0, 'tmj_recomposition_differences': 0})

report = {'status': 'OK', 'repository': P['repository'], 'commit': P['commit'],
          'source_blobs_verified': len(sheets), 'layouts': reports,
          'not_verified': ['PMDO runtime import', 'Collisions/transitions',
                           'Continuité artistique des nouveaux raccords']}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=1))
