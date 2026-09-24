"""Cap canonique face mer v1 — falaise Metano stricte, eau native 4 phases.

Methode spriter pro:
- Modules natifs COMPLETS (dalles 64x48 face/retour, couronne/pied 64x16,
  herbe 128x128), poses a 1x sur grille 8px, sans rotation ni recoloration.
- Eau native: cols riviere BASE + 4 planches River_Animation + 4 frames
  cascade Animation_Tileset, FrameLength=10 (10 ticks ~ 167ms a 60Hz).
- Le generateur n'intervient pas: composition dessinee a la main (masques
  explicites ci-dessous), pixels 100% canoniques verifies.
"""
from pathlib import Path
import sys, json, io, hashlib, base64
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/zones_guidees'))
from native_tools import Bank, BASE, CLIFF, ANIM, RIVERS
import numpy as np
from PIL import Image

B = Bank()
W, H = 1024, 512
GW, GH = W // 8, H // 8
assert W % 8 == 0 and H % 8 == 0

# --- Composition (toutes les cotes en px, multiples de 8) ---
CROWN_Y, FACE_Y, FOOT_Y = 168, 184, 280   # paroi: couronne 16 + faces 96 + pied 16
WALL_END = 296
CX = 512                                   # axe du ruisseau / cascade
NECK_SX = 124                              # canal canonique 64px: cols 124..131
NECK_W = 8                                 # aligne pile sur la cascade 64px
FALL_W = 64                                # cascade native: 64 px de large
NOTCH = (60, 68)                           # cols du canal dans la paroi

O = R / 'renders/falaise_mer_canonique_v1'
P = O / 'cap_cascade'
P.mkdir(parents=True, exist_ok=True)

COMMIT = 'da6c2130d641507447e6386a5e47a296e8cb4c71'
REF = 'Palikadude/Halcyon'

def cell(sheet, sx, sy):
    """Tuile 8x8 canonique en alpha droit (depremultipliee pour l'edition)."""
    gid = B.get(sheet, sx, sy)
    return B.image(gid) if gid else None

def paste_cell(img, sheet, sx, sy, dx, dy):
    assert dx % 8 == 0 and dy % 8 == 0, (dx, dy)
    t = cell(sheet, sx, sy)
    if t is not None:
        img.paste(t, (dx, dy))
    return t is not None

def paste_slab(img, sheet, src_rect, dx, dy, exclude_grass=False):
    """Dalle rectangulaire native complete, sans transformation."""
    sx0, sy0, sx1, sy1 = src_rect
    assert dx % 8 == 0 and dy % 8 == 0
    assert (sx1 - sx0) % 8 == 0 and (sy1 - sy0) % 8 == 0
    for sy in range(sy0 // 8, sy1 // 8):
        for sx in range(sx0 // 8, sx1 // 8):
            if exclude_grass:
                # Les pixels d'herbe inclus dans la couronne rocheuse sont exclus
                # pour ne pas creer de marche verte (methode V4 documentee).
                t = B.sources[sheet].get((sx, sy))
                if t is None:
                    continue
            paste_cell(img, sheet, sx, sy, dx + (sx - sx0 // 8) * 8, dy + (sy - sy0 // 8) * 8)

# --- Calque 01: sol d'herbe plein canvas ---
sol = Image.new('RGBA', (W, H))
for y in range(GH):
    for x in range(GW):
        assert paste_cell(sol, BASE, x % 16, 80 + y % 16, x * 8, y * 8)

# --- Calque 02: parois (faces plein cadre, contacts W/E nets) ---
parois = Image.new('RGBA', (W, H))
FACE = (912, 464, 976, 512)
for i in range(W // 64):
    paste_slab(parois, CLIFF, FACE, i * 64, FACE_Y)
    paste_slab(parois, CLIFF, FACE, i * 64, FACE_Y + 48)

# --- Calque 03: couronnes + pieds ---
bordures = Image.new('RGBA', (W, H))
CROWN = (912, 448, 976, 464)
FOOT = (912, 528, 976, 544)
for i in range(W // 64):
    paste_slab(bordures, CLIFF, CROWN, i * 64, CROWN_Y)
    paste_slab(bordures, CLIFF, FOOT, i * 64, FOOT_Y)
# Le canal traverse couronne et pied: pas de barre rocheuse sur l'eau.
ba = np.array(bordures)
ba[CROWN_Y:CROWN_Y + 16, NOTCH[0] * 8:NOTCH[1] * 8] = 0
ba[FOOT_Y:FOOT_Y + 16, NOTCH[0] * 8:NOTCH[1] * 8] = 0
bordures = Image.fromarray(ba)

# --- Ruisseau nord (plateau) + sud (premier plan, vers la mer) ---
berges = Image.new('RGBA', (W, H))
riv = [Image.new('RGBA', (W, H)) for _ in range(4)]
x0 = CX // 8 - NECK_W // 2  # 59 -> cols 59..68, centre 512
stream_rows = list(range(0, CROWN_Y // 8)) + list(range(WALL_END // 8, GH))
animations = []
for r in stream_rows:
    sy = 50 + (r % 2)
    for k in range(NECK_W):
        sx = NECK_SX + k
        assert paste_cell(berges, BASE, sx, sy, (x0 + k) * 8, r * 8), (sx, sy)
        present = [(s, sx, sy) for s in RIVERS if (sx, sy) in B.sources[s]]
        if len(present) == 4:
            for f in range(4):
                paste_cell(riv[f], RIVERS[f], sx, sy, (x0 + k) * 8, r * 8)
            animations.append({'dest_cell': [x0 + k, r], 'layer': '05_riviere',
                               'frames': [{'sheet': s, 'texloc': [sx, sy]} for s, _, _ in present],
                               'frameLength': 10})
        else:
            assert not present, f'cellule riviere partielle {(sx, sy)}'

# --- Cascade 64px dans l'axe, du haut de paroi au pied ---
casc = [Image.new('RGBA', (W, H)) for _ in range(4)]
fall_rows = (WALL_END - CROWN_Y) // 8  # 16 rangees
assert fall_rows >= 10
# Rangees source 15-16 entierement transparentes: chute mappee sur 0..14 opaques.
def src_row(j):
    if j < 6:
        return j                      # couronne de chute conservee (0..5)
    if j >= fall_rows - 3:
        return 12 + (j - (fall_rows - 3))  # pied de chute conserve (12..14)
    return 6 + (j - 6) % 6             # milieu: rangees natives repetees (6..11)
fall_anims = 0
for j in range(fall_rows):
    sy = src_row(j)
    for dx in range(8):
        present = [(f, 1 + 9 * f + dx, 62 + sy) for f in range(4)
                   if (1 + 9 * f + dx, 62 + sy) in B.sources[ANIM]]
        if len(present) == 4:
            for f, ax, ay in present:
                paste_cell(casc[f], ANIM, ax, ay, CX - FALL_W // 2 + dx * 8, CROWN_Y + j * 8)
            fall_anims += 1
            animations.append({'dest_cell': [CX // 8 - 4 + dx, CROWN_Y // 8 + j],
                               'layer': '06_cascade',
                               'frames': [{'sheet': ANIM, 'texloc': [ax, ay]} for _, ax, ay in present],
                               'frameLength': 10})
        else:
            assert not present, f'cellule cascade partielle {(dx, sy)}'

# --- Compositions ---
sec = Image.alpha_composite(Image.alpha_composite(sol, parois), bordures)
wets = []
for f in range(4):
    w = Image.alpha_composite(sec, berges)
    w = Image.alpha_composite(w, riv[f])
    w = Image.alpha_composite(w, casc[f])
    wets.append(w)

# --- Ecriture ---
sol.save(P / 'cap_01_sol_herbe.png', optimize=True)
parois.save(P / 'cap_02_parois.png', optimize=True)
bordures.save(P / 'cap_03_couronnes_pieds.png', optimize=True)
berges.save(P / 'cap_04_berges.png', optimize=True)
for f in range(4):
    riv[f].save(P / f'cap_05_riviere_phase_{f+1}.png', optimize=True)
    casc[f].save(P / f'cap_06_cascade_phase_{f+1}.png', optimize=True)
    wets[f].save(P / f'cap_avec_eau_frame_{f+1}.png', optimize=True)
sec.save(P / 'cap_SEC.png', optimize=True)
wets[0].save(P / 'COMPOSITION.png', optimize=True)

# WebP anime (repli APNG puis GIF si webp indisponible)
anim_name = 'ANIMATION_COMPLETE.webp'
try:
    wets[0].save(P / anim_name, save_all=True, append_images=wets[1:], duration=167, loop=0, lossless=True)
except Exception:
    try:
        anim_name = 'ANIMATION_COMPLETE.apng'
        wets[0].save(P / anim_name, save_all=True, append_images=wets[1:], duration=167, loop=0)
    except Exception:
        anim_name = 'ANIMATION_COMPLETE.gif'
        wets[0].save(P / anim_name, save_all=True, append_images=wets[1:], duration=167, loop=0)

# --- OpenRaster (phase 0, ordre bas->haut pour la recomposition) ---
import zipfile, xml.etree.ElementTree as ET
layers_bottom_up = [('01_sol_herbe', sol), ('02_parois', parois), ('03_couronnes_pieds', bordures),
                    ('04_berges', berges), ('05_riviere_phase_1', riv[0]), ('06_cascade_phase_1', casc[0])]
def png_bytes(im):
    b = io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()
root = ET.Element('image', w=str(W), h=str(H))
stack = ET.SubElement(root, 'stack')
for name, im in reversed(layers_bottom_up):  # stack.xml: premier = dessus
    ET.SubElement(stack, 'layer', name=name, src=f'data/{name}.png')
with zipfile.ZipFile(P / 'cap_cascade.ora', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
    z.writestr('stack.xml', ET.tostring(root))
    z.writestr('mergedimage.png', png_bytes(wets[0]))
    for name, im in layers_bottom_up:
        z.writestr(f'data/{name}.png', png_bytes(im))

# --- Planche de controle 2x (presentation, NE PAS IMPORTER) ---
from PIL import ImageDraw
crops = [('jonction_couronne', 448, 152, 576, 216), ('chute_haute', 464, 168, 560, 264),
         ('bouche_basse', 440, 248, 584, 344), ('ruisseau_sud', 440, 296, 584, 424),
         ('contact_ouest', 0, 152, 144, 312)]
cells = []
for label, x0c, y0c, x1c, y1c in crops:
    crop = wets[0].crop((x0c, y0c, x1c, y1c))
    crop = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.NEAREST)
    cells.append((label, crop))
coly = [64, 64]
positions = []
for i, (label, crop) in enumerate(cells):
    col = i % 2
    positions.append((16 + col * 312, coly[col], label, crop))
    coly[col] += crop.height + 30
board = Image.new('RGB', (640, max(coly) + 16), '#15231c')
d = ImageDraw.Draw(board)
d.text((16, 12), 'CAP CANONIQUE FACE MER v1 — coupes 2x (presentation)', fill='#e6d493')
d.text((16, 34), '1024x512 natif, grille 8px, tuiles Halcyon non modifiees', fill='#b6c6ae')
for ox, oy, label, crop in positions:
    d.text((ox, oy), label, fill='#a3dae3')
    board.paste(crop, (ox, oy + 18))
board.save(O / 'PLANCHE_COUPES_2X_NE_PAS_IMPORTER.png')

# --- Manifeste ---
def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = {
    'titre': 'Cap canonique face mer v1 — falaise Metano stricte, eau native',
    'taille_px': [W, H], 'cellules': [GW, GH], 'grille_px': 8,
    'reference': REF, 'commit': COMMIT,
    'sources': B.source_info,
    'modules': {
        'herbe': {'feuille': BASE, 'rect_px': [0, 640, 128, 768]},
        'face': {'feuille': CLIFF, 'rect_px': list(FACE)},
        'couronne': {'feuille': CLIFF, 'rect_px': list(CROWN)},
        'pied': {'feuille': CLIFF, 'rect_px': list(FOOT)},
        'canal': {'feuilles': [BASE] + RIVERS, 'cols': [NECK_SX, NECK_SX + NECK_W - 1], 'rangees': [50, 51]},
        'cascade': {'feuille': ANIM, 'largeur_px': FALL_W, 'rangees_source': sorted({src_row(j) for j in range(fall_rows)}),
                    'rangees_omises': [r for r in range(17) if r not in {src_row(j) for j in range(fall_rows)}]},
    },
    'composition': {'mur': {'couronne_y': CROWN_Y, 'faces_y': [FACE_Y, FACE_Y + 96], 'pied_y': FOOT_Y, 'fin_y': WALL_END,
                              'bouche_eau_cols': list(NOTCH), 'parois': 'faces 64x48 plein cadre, contacts W/E'},
                    'ruisseau_centre_x': CX, 'largeur_canal_px': NECK_W * 8,
                    'chute': {'x': CX - FALL_W // 2, 'haut_y': CROWN_Y, 'bas_y': WALL_END}},
    'calques': ['cap_01_sol_herbe.png', 'cap_02_parois.png', 'cap_03_couronnes_pieds.png', 'cap_04_berges.png']
               + [f'cap_05_riviere_phase_{f+1}.png' for f in range(4)]
               + [f'cap_06_cascade_phase_{f+1}.png' for f in range(4)],
    'animation': {'phases': 4, 'frameLength_ticks': 10, 'duree_phase_ms': 167, 'boucle_ms': 668,
                  'fichier': anim_name, 'cellules_animees': len(animations)},
    'animations': animations,
    'limites': ['Ciel et mer non peints (hors-champ transparent: seul le terrain est strict)',
                'Raccords canal/chute approximatifs aux deux bouches, a apprecier a 1x',
                'Pas de test PMDO/GPU, collisions ou transitions'],
}
(O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(f'OK: {W}x{H}, {len(animations)} cellules animees ({fall_anims} cascade), anim={anim_name}')
