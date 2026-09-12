# -*- coding: utf-8 -*-
"""Contrôle du tileset animé « Falaises » (comme verify_pmd.py : validation par code).

Vérifie, pour les 6 ambiances :
  - présence des fichiers (Aseprite, 4 planches, APNG, exemple) ;
  - parse de la feuille Aseprite : 4 frames, 192×72, 32 bits, grille 24, durée 150 ms ;
  - identité pixels des cels Aseprite et des planches PNG ;
  - tuiles statiques identiques sur les 4 frames, tuiles animées réellement animées ;
  - invariants d'alpha (parois opaques, flancs/ponst transparents où prévu) ;
  - raccord sans couture de face_roche (coût de couture comparé au coût interne) ;
  - ambiances distinctes, nuit la plus sombre ;
  - APNG 4 frames, exemple non vide, aperçu hors ligne sans ressource externe.
Écrit controle_falaises.json.
"""
from pathlib import Path
from PIL import Image
import numpy as np, json, struct, zlib

R = Path(__file__).resolve().parents[1]
M = json.loads((R / 'falaises' / 'falaises.json').read_text())
AMB = M['ambiances']
T = M['grille_tuile']
COLS, ROWS = M['planche']
FR = M['frames']
ANIM = {t['id'] for t in M['tuiles'] if t['anime']}
STAT = {t['id'] for t in M['tuiles'] if not t['anime']}
report = {'ambiances': {}, 'tuiles': len(M['tuiles']), 'frames': FR,
          'duree_ms': M['duree_ms'], 'grille_tuile': T}


def tuile(arr, i):
    ox, oy = (i % COLS) * T, (i // COLS) * T
    return arr[oy:oy + T, ox:ox + T]


moyennes = {}
for amb in AMB:
    d = R / 'falaises' / amb
    rec = {}
    # --- fichiers
    fa = d / f'tileset_falaises_{amb}.aseprite'
    planches = [np.array(Image.open(d / f'planche_f{i + 1}.png').convert('RGBA')) for i in range(FR)]
    assert all(p.shape == (ROWS * T, COLS * T, 4) for p in planches), 'Taille de planche'
    assert (d / 'animation.png').exists() and (R / M['fichiers'][amb]['exemple']).exists()
    # --- Aseprite
    data = fa.read_bytes()
    size, magic, n, w, h, depth, flags, speed = struct.unpack_from('<IHHHHHIH', data)
    assert size == len(data) and magic == 0xA5E0 and n == FR and (w, h) == (COLS * T, ROWS * T) and depth == 32
    assert struct.unpack_from('<hhHH', data, 36) == (0, 0, T, T), 'Grille Aseprite 24 px'
    fs, fm, nc, dt = struct.unpack_from('<IHHH', data, 128)
    assert fm == 0xF1FA and dt == M['duree_ms'], 'Durée de frame 150 ms'
    pos, cels, couches = 128, [], 0
    for _ in range(FR):
        flen, fmag, fnc, fdur = struct.unpack_from('<IHHH', data, pos)
        assert fmag == 0xF1FA and fdur == M['duree_ms']
        p = pos + 16
        for _ in range(fnc):
            clen, kind = struct.unpack_from('<IH', data, p)
            q = data[p + 6:p + clen]
            if kind == 0x2004:
                couches += 1
            if kind == 0x2005:
                li, x, y, op, typ, zi = struct.unpack_from('<HhhBHh', q)
                cw, ch = struct.unpack_from('<HH', q, 16)
                assert typ == 2 and op == 255 and (x, y) == (0, 0)
                cels.append(Image.frombytes('RGBA', (cw, ch), zlib.decompress(q[20:])))
            p += clen
        pos += flen
    assert pos == len(data) and couches == 1 and len(cels) == FR, 'Structure Aseprite'
    for cel, ref in zip(cels, planches):
        assert np.array_equal(np.array(cel), ref), 'Cel Aseprite != planche PNG'
    rec['aseprite'] = {'frames': FR, 'dimensions': [w, h], 'grille': T, 'duree_ms': dt,
                       'cels_identiques_aux_png': True}
    # --- animation : statique figé, animé vivant
    for i in sorted(STAT):
        ref = tuile(planches[0], i)
        for p in planches[1:]:
            assert np.array_equal(tuile(p, i), ref), f'Tuile statique {i} animée par erreur'
    vivantes = 0
    for i in sorted(ANIM):
        distinct = {tuile(p, i).tobytes() for p in planches}
        assert len(distinct) >= 2, f'Tuile animée {i} immobile'
        vivantes += 1
    rec['tuiles_animees'] = vivantes
    rec['tuiles_statiques'] = len(STAT)
    # --- invariants d'alpha
    a0 = tuile(planches[0], 0)
    assert (a0[:, :, 3] == 255).all(), 'face_roche doit être opaque'
    a4 = tuile(planches[0], 4)
    assert (a4[:, :, 3] == 255).all(), 'plateau_herbe doit être opaque'
    a8 = tuile(planches[0], 8)
    assert (a8[:, 0, 3] == 0).all(), 'bord_gauche : colonne 0 transparente'
    a9 = tuile(planches[0], 9)
    assert (a9[:, -1, 3] == 0).all(), 'bord_droit : dernière colonne transparente'
    a14 = tuile(planches[0], 14)
    assert (a14[0, :, 3] == 0).all(), 'pont_corde : haut transparent'
    a3 = tuile(planches[0], 3)
    assert (a3[0, :, 3] > 0).any() and (a3[-1, :, 3] == 255).all(), 'sommet_herbe : roche pleine en bas'
    # --- raccord sans couture de la paroi
    f = a0.astype(int)
    inter_x = np.abs(f[:, 1:] - f[:, :-1]).mean()
    inter_y = np.abs(f[1:, :] - f[:-1, :]).mean()
    cout_x = np.abs(f[:, 0] - f[:, -1]).mean()
    cout_y = np.abs(f[0, :] - f[-1, :]).mean()
    assert cout_x <= inter_x * 2.5 + 2 and cout_y <= inter_y * 2.5 + 2, 'Couture visible sur face_roche'
    rec['raccord_sans_couture'] = {'couture_x': round(float(cout_x), 2), 'couture_y': round(float(cout_y), 2),
                                   'interne_x': round(float(inter_x), 2), 'interne_y': round(float(inter_y), 2)}
    # --- APNG et exemple
    ap = Image.open(d / 'animation.png')
    assert getattr(ap, 'n_frames', 1) == FR, 'APNG 4 frames'
    ex = np.array(Image.open(R / M['fichiers'][amb]['exemple']).convert('RGBA'))
    assert ex.shape == (240, 480, 4) and (ex[:, :, 3] > 0).mean() > 0.2, 'Exemple trop vide'
    rec['apng_frames'] = ap.n_frames
    rec['exemple'] = {'dimensions': [480, 240], 'rempli': round(float((ex[:, :, 3] > 0).mean()), 3)}
    moyennes[amb] = tuple(round(float(v), 1) for v in ex[ex[:, :, 3] > 0][:, :3].mean(0))
    report['ambiances'][amb] = rec

# --- ambiances distinctes, nuit la plus sombre
vals = {a: sum(v) / 3 for a, v in moyennes.items()}
assert len(set(moyennes[a] for a in AMB)) == len(AMB), 'Ambiances identiques'
assert min(vals, key=vals.get) == 'nuit', 'La nuit doit être l’ambiance la plus sombre'
assert max(vals, key=vals.get) == 'jour', 'Le jour doit être l’ambiance la plus claire'
report['moyennes_rgb'] = {a: list(v) for a, v in moyennes.items()}

# --- aperçu hors ligne
html = (R / 'apercu_falaises.html').read_text()
assert 'http://' not in html and 'https://' not in html, 'Aperçu non hors ligne'
for amb in AMB:
    assert html.count(f'"{amb}":') >= 1 or f'"{amb}"' in html
report['apercu_hors_ligne'] = True

(R / 'controle_falaises.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"PASS : {len(M['tuiles'])} tuiles × {FR} frames × {len(AMB)} ambiances — "
      f"Aseprite/PNG identiques, {len(ANIM)} tuiles animées, raccords sans couture, aperçu hors ligne.")
