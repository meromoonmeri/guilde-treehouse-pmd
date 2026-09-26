"""Entrée Waterfall Cave sud -> nord V2 (EWC2) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Retours sur EWC1 (26 septembre) : « il y a des petits traits blancs au bord des rives, fais une version sans ça, et
faut pas d'eau devant l'entrée de la grotte, et faut que la cascade soit en deux temps : la cascade qui prend tout et
après une animation où la cascade se fend pour ouvrir la grotte que tu as créée ».
Base : EWC1 (même branche). MÊMES BRUTS GÉNÉRÉS qu'EWC1 (source/entree_waterfall_cave_sud_nord_v1/bruts, hachés),
aucune nouvelle génération ; EWC1 reste intact.
Changements :
1. eau façon Métano SANS le liseré `clair` (tirets de 1 px posés contre chaque rive par water_phases) : ce sont les
   « petits traits blancs ». Couleurs restantes : surface, inter, accent, bande (Métano exactes) ;
2. plus d'eau devant la bouche : un couloir de sable (pixels du sol complet GÉNÉRÉ) remplace la partie centrale de la
   vasque, de la bouche au chemin central ; la vasque devient deux bassins latéraux ; berge de raccord = sable
   assombri au rapport mesuré berge/sable du décor ;
3. cascade en deux temps (calques d'état) :
   - « fermée » : le rideau recouvre toute la bouche (même texture périodique prolongée), bouillons au pied, 12 x 4 ;
   - « ouverture » : le rideau se fend depuis le haut et s'écarte jusqu'au contour de la bouche, bord d'eau clair,
     gerbes aux lèvres de la fente ; 24 x 4 ticks = 96 ticks, joué une fois ;
   - « ouverte » : le rideau contourne la bouche (état EWC1), 12 x 4.
Lancer : .venv/bin/python source/entree_waterfall_cave_sud_nord_v2/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


V1 = loadmod('ewc1_build', R / 'source/entree_waterfall_cave_sud_nord_v1/build.py')   # classifieur, poses, palettes
BM, JM = V1.BM, V1.JM
RAW, REF = V1.RAW, V1.REF
OUT = R / 'renders/entree_waterfall_cave_sud_nord_v2'
STAGE = R / '.cache/entree_waterfall_cave_sud_nord_v2/entree_waterfall_cave_v2'
NAMESPACE = 'entree_waterfall_cave_v2'
ASSET = 'ewc2_entree_waterfall_cave'
PFX = 'EWC2'
W, H, SRC = V1.W, V1.H, V1.SRC
PAL = BM.PAL
WATER_PHASES, WATER_TICKS = 4, 10
FALL_PHASES, FALL_TICKS, FALL_PERIOD = V1.FALL_PHASES, V1.FALL_TICKS, V1.FALL_PERIOD
FALL_BLEND, FALL_Y0, FALL_STEP = V1.FALL_BLEND, V1.FALL_Y0, V1.FALL_STEP
FOAM_PHASES, FOAM_TICKS = V1.FOAM_PHASES, V1.FOAM_TICKS
OPEN_PHASES = 24                      # ouverture : 24 x 4 = 96 ticks (1,6 s) ; multiple de 12 -> défilement continu
OPEN_TICKS = OPEN_PHASES * FALL_TICKS
LOOP_TICKS = 240                      # PPCM(4 x 10, 12 x 4)
# Couloir (pleine rés., mesuré sur le décor) : bas de la bouche y=283, sol de la bouche x 562-639 ; chemin central
# sous les bassins x 543-656 (y=426) ; la vasque dessinée s'étend jusqu'à y~372.
CORR_KNOTS = {'y': [277, 300, 330, 360, 392],        # bords du couloir, pleine rés. : palier au pied de la bouche,
              'gauche': [560, 563, 557, 548, 518],     # léger renflement, puis évasement vers la plage
              'droite': [640, 637, 644, 652, 684]}
SLIT_U, SLIT_V = 0.7, 0.3             # fente : temps d'ouverture = 0,7 x écart au centre + 0,3 x profondeur
REMOVED = 'clair'                     # couleur Métano du liseré retiré


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- eau façon Métano, sans liseré de rive
def water_phases(water, visible):
    """Copie de water_phases (lot Bristle, même graine 9) SANS la ligne
    a[(d <= 1) & (sin(...) > -0.35)] = PAL['clair'] : c'étaient les petits traits blancs contre les rives."""
    d = nd.distance_transform_edt(visible); yy, xx = np.mgrid[:H, :W]
    jag = nd.gaussian_filter(np.random.default_rng(9).random((H, W)), 1.0); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        n = 0.6 * np.sin(yy * 0.23 + xx * 0.08 - ph) + 0.4 * np.sin(yy * 0.09 - xx * 0.19 + 1.3 - ph)
        T = 4.5 + 1.1 * n; jr = np.roll(jag, t * 2, axis=0); fringe = T + 0.6 + 2.6 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['inter'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*PAL['accent'], 255)
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        a[~water] = 0; a[water & ~visible] = (*PAL['bande'], 255)
        frames.append(a)
    return frames, d


# ---------------------------------------------------------------- couloir de sable devant la bouche (pleine rés.)
def corridor(shape):
    yy, xx = np.mgrid[:shape[0], :shape[1]]; y = np.arange(shape[0]); K = CORR_KNOTS
    xl = np.interp(y, K['y'], K['gauche']) + 2.5 * np.sin(y * 0.13 + 0.7) + 1.5 * np.sin(y * 0.051 + 2.1)
    xr = np.interp(y, K['y'], K['droite']) + 2.5 * np.sin(y * 0.12 + 2.9) + 1.5 * np.sin(y * 0.047 + 0.4)
    return (yy >= K['y'][0]) & (yy <= K['y'][-1]) & (xx >= xl[:, None]) & (xx <= xr[:, None])


def reshape_front(a, f, m):
    """Décor et classes modifiés : couloir = sable du sol complet généré ; lisière d'écume irrégulière (les blancs
    de l'écume dessinée à <= 5 px du bord restent de l'écume) ; berge de raccord le long des bassins."""
    ratio = a[m['berge']].mean(0) / a[m['sable']].mean(0)           # rapport mesuré berge / sable du décor
    corr = corridor(a.shape[:2]) & ~m['entree_sombre']
    sat = (a.max(2) - a.min(2)) * 255 / np.maximum(a.max(2), 1)
    ragged = corr & (nd.distance_transform_edt(corr) <= 5) & m['ecume_pied'] & (a.min(2) > 205) & (sat < 60)
    corr &= ~ragged
    a2 = a.copy(); a2[corr] = f[corr]
    m2 = {k: (v & ~corr) for k, v in m.items()}
    m2['sable'] = m2['sable'] | corr
    dw = nd.distance_transform_edt(~m2['water'])              # le long de l'écume : pas de berge (traits bruns)
    b1, b2 = corr & (dw <= 1.5), corr & (dw > 1.5) & (dw <= 3.0)
    a2[b1] = np.round(a2[b1] * ratio); a2[b2] = np.round(a2[b2] * (1 + ratio) / 2)
    m2['berge'] = m2['berge'] | b1 | b2; m2['sable'] &= ~(b1 | b2)
    return a2, m2, corr, {'rapport_berge_sable': [round(float(v), 3) for v in ratio], 'pixels_couloir': int(corr.sum()),
                          'lisiere_ecume_px': int(ragged.sum()),
                          'eau_retiree_px': int((m['water'] & corr).sum()), 'ecume_retiree_px': int((m['ecume_pied'] & corr).sum())}


# ---------------------------------------------------------------- rideau : texture périodique (code EWC1 scindé)
def fall_texture(layer, mask, cave):
    ys, xs = np.nonzero(mask); x0, x1 = int(xs.min()), int(xs.max()) + 1
    src = layer[..., :3].astype(float); n = FALL_PERIOD + FALL_BLEND
    strip = np.zeros((n, x1 - x0, 3)); valid = np.zeros((n, x1 - x0), bool); src_row = np.full(x1 - x0, -1)
    for x in range(x0, x1):
        cands = [(mask[b0:b0 + n, x].mean(), b0) for b0 in (FALL_Y0, FALL_Y0 + FALL_PERIOD)
                 if b0 + n <= H and not cave[b0:b0 + n, x].any()]
        if cands and max(cands)[0] >= 0.6:
            b0 = max(cands)[1]; i = x - x0
            strip[:, i] = src[b0:b0 + n, x]; valid[:, i] = mask[b0:b0 + n, x]; src_row[i] = b0
    assert (src_row >= 0).mean() > 0.6, 'rideau trop court pour la période'
    holes = int((~valid).sum())
    for r_ in range(n):
        ok, miss = np.flatnonzero(valid[r_]), np.flatnonzero(~valid[r_])
        if len(miss):
            strip[r_, miss] = strip[r_, ok[np.abs(ok[None] - miss[:, None]).argmin(1)]]
    T = strip[:FALL_PERIOD].copy()
    for k in range(FALL_BLEND):
        w = k / FALL_BLEND; T[k] = (1 - w) * strip[FALL_PERIOD + k] + w * strip[k]
    pal = np.unique(layer[mask][:, :3], axis=0).astype(float)
    Tq = pal[((T[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)].astype('uint8')
    return (Tq, x0, x1, pal), {'x_range': [x0, x1], 'bandes_source': {str(b): int((src_row == b).sum()) for b in (FALL_Y0, FALL_Y0 + FALL_PERIOD)},
                               'colonnes_sans_bande': int((src_row < 0).sum()), 'pixels_bouches': holes, 'palette_colors': int(len(pal))}


def fall_frame(tex, t, mask):
    Tq, x0, x1, _ = tex; rows = np.arange(H)
    f = np.zeros((H, W, 4), 'uint8')
    f[:, x0:x1, :3] = Tq[(rows - FALL_Y0 - t * FALL_STEP) % FALL_PERIOD]
    f[..., 3] = 255; f[~mask] = 0
    return f


def opening_time(cave):
    """Temps d'ouverture normalisé [0, 1] de chaque pixel de la bouche : la fente naît en haut au centre, descend
    et s'élargit jusqu'au contour (u = écart au centre rapporté à la demi-largeur de la rangée, v = profondeur)."""
    ys, xs = np.nonzero(cave); ytop, ybot = ys.min(), ys.max(); xc = (xs.min() + xs.max()) / 2
    t = np.full(cave.shape, np.inf)
    for y in range(ytop, ybot + 1):
        row = np.flatnonzero(cave[y])
        if not len(row):
            continue
        hl, hr = max(xc - row.min(), 1.0), max(row.max() - xc, 1.0)
        u = np.where(row < xc, (xc - row) / hl, (row - xc) / hr)
        t[y, row] = SLIT_U * u + SLIT_V * (y - ytop) / max(ybot - ytop, 1)
    t[cave] /= t[cave].max()
    return t


def smooth(k, n):
    u = k / (n - 1); return (u * u * (3 - 2 * u)) * (1 + 1e-6)


def door_region(cas, cave, keep_visible):
    """Zone couverte seulement quand la cascade est fermée : la bouche + les éclats de rebord rocheux autour d'elle
    (dans la boîte de la bouche +/- 8 px : tout ce qui n'est ni rideau, ni arbre, ni eau, ni écume, ni sable praticable,
    ni couloir). Sans cela ils flottent sur le rideau fermé ou dépassent sous son pied."""
    ys, xs = np.nonzero(cave); box = np.zeros_like(cave)
    box[max(0, ys.min() - 8):ys.max() + 9, max(0, xs.min() - 8):xs.max() + 9] = True
    extra = box & ~cas & ~cave & ~keep_visible
    lab, n = nd.label(extra); near = nd.binary_dilation(cave, iterations=3)
    keep = [l for l in range(1, n + 1) if (near & (lab == l)).any()]
    return cave | np.isin(lab, keep)


def cascade_states(tex, cas, door):
    pal = tex[3]; lum = pal @ [.299, .587, .114]; white = pal[lum.argmax()].astype('uint8')
    closed, opened = cas | door, cas
    fermee = [fall_frame(tex, t, closed) for t in range(FALL_PHASES)]
    ouverte = [fall_frame(tex, t, opened) for t in range(FALL_PHASES)]
    tmap = opening_time(door); ouverture, opens = [], []
    for k in range(OPEN_PHASES):
        op = door & (tmap < smooth(k, OPEN_PHASES)); opens.append(op)
        f = fall_frame(tex, k % FALL_PHASES, cas | (door & ~op))
        d1 = nd.binary_dilation(op) & ~op & door                          # lèvres de la fente, dans la porte seulement
        d2 = nd.binary_dilation(op, iterations=2) & ~op & ~d1 & door       # -> aucune lèvre une fois ouverte
        f[d1, :3] = white
        if d2.any():
            c = (f[d2, :3].astype(float) + 255) / 2
            f[d2, :3] = pal[((c[:, None] - pal[None]) ** 2).sum(-1).argmin(-1)].astype('uint8')
        ouverture.append(f)
    return fermee, ouverture, ouverte, opens, tmap


def paste(frame, spr, cx, cy):
    hh, ww = spr.shape[:2]; y0, x0 = cy - hh // 2, cx - ww // 2
    assert 0 <= y0 and y0 + hh <= H and 0 <= x0 and x0 + ww <= W
    m = spr[..., 3] > 0; frame[y0:y0 + hh, x0:x0 + ww][m] = spr[m]


def door_foam(puffs, sprays, cave, closed, walk, opens):
    """Écume de la porte : bouillons au pied du rideau fermé ; pendant l'ouverture ils s'éteignent quand la fente
    atteint leur colonne, et des gerbes jaillissent aux lèvres basses de la fente."""
    ys, xs = np.nonzero(cave); ybot, cx0, cx1 = int(ys.max()), int(xs.min()), int(xs.max())
    yy, xx = np.mgrid[:H, :W]
    clip = (closed | (walk & (yy <= ybot + 12))) & (xx >= cx0 - 6) & (xx <= cx1 + 6)
    em = [(int(round(x)), ybot - 4, (i * 5 + 2) % FOAM_PHASES) for i, x in enumerate(np.linspace(cx0 + 9, cx1 - 9, 4))]
    fermee = [np.zeros((H, W, 4), 'uint8') for _ in range(FOAM_PHASES)]
    for t in range(FOAM_PHASES):
        for x, y, off in em:
            p = V1.PUFF_SEQ[(t + off) % FOAM_PHASES]
            if p >= 0:
                paste(fermee[t], puffs[p], x, y)
        fermee[t][~clip] = 0
    ouverture, low = [], ybot - 3
    for k, op in enumerate(opens):
        f = np.zeros((H, W, 4), 'uint8'); t = k % FOAM_PHASES
        for x, y, off in em:
            p = V1.PUFF_SEQ[(t + off) % FOAM_PHASES]
            if p >= 0 and not op[low - 2:low + 1, max(0, x - 3):x + 4].any():   # la fente n'a pas atteint ce bouillon
                paste(f, puffs[p], x, y)
        bottom = np.flatnonzero(op[low - 2:low + 1].any(0))
        s = smooth(k, OPEN_PHASES)
        if len(bottom) and s < 0.97:                                        # gerbes aux lèvres de la fente
            for x in (int(bottom.min()) - 3, int(bottom.max()) + 3):
                paste(f, sprays[k % len(sprays)], x, ybot - 4)
        f[~clip] = 0; ouverture.append(f)
    return fermee, ouverture, {'emetteurs_bouillons': [list(e) for e in em], 'clip_y_max': ybot + 12}


# ---------------------------------------------------------------- ORA (visibilité par calque)
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Waterfall Cave sud-nord V2 (EWC2), cascade fermee')
    stack = ET.SubElement(root, 'stack'); comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (name, a, vis) in reversed(list(enumerate(layers))):
            fn = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', name=name, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible' if vis else 'hidden', **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); Image.fromarray(a).save(b, format='PNG'); z.writestr(fn, b.getvalue())
        for _, a, vis in layers:
            if vis:
                comp.alpha_composite(Image.fromarray(a))
        b = io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); b = io.BytesIO(); th.save(b, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


# ---------------------------------------------------------------- Ground PMDO 0.8.12
def ground_project(stack, blocked, entry_px, threshold_px, gfx, tools):
    """stack : (titre, frames, ticks, etat) du bas vers le haut ; visibles au chargement : etat None ou fermee."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    for i, (title, frames, ticks, etat) in enumerate(stack):
        vis = etat in (None, 'fermee')
        bank = gfx.TileBank(f'{PFX}_{i:02d}_{title.split()[0].upper()}')
        bank.ids[bytes(256)] = (0, 0); bank.data[(0, 0)] = bytes(256)

        def cell(x, y, frames=frames, bank=bank):
            fs = []
            for a in frames:
                f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
                fs.append(f if f else {'Sheet': bank.name, 'TexLoc': {'X': 0, 'Y': 0}})
            if all(f['TexLoc'] == {'X': 0, 'Y': 0} for f in fs):
                return []
            return [fs[0]] if all(f == fs[0] for f in fs) else fs
        lay = gfx.layer(f'{i:02d} {title}', gw, gh, cell, ticks); lay['Visible'] = bool(vis)
        layers.append(lay); banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Waterfall Cave V2 - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Waterfall Cave (entrancecascade.png), V2 : '
                     'eau facon Metano sans liseré de rive, couloir de sable jusqu a la bouche, cascade en deux temps '
                     '(calques d etat fermee / ouverture / ouverte, script init.lua NON TESTE). Collisions a verifier.')
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': int(blocked[y, x])}
                       for y in range(gh)] for x in range(gw)]
    mk = lambda n, p: {'EntName': n, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                       'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [], 'Spawners': [],
                      'Markers': [mk('entrance', entry_px), mk('donjon_seuil', threshold_px)]}]
    o['Decorations'] = [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}]
    tpl['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground', json.dumps(tpl, ensure_ascii=False, separators=(',', ':')).encode())
    etats = {e: [i for i, st in enumerate(stack) if st[3] == e] for e in ('fermee', 'ouverture', 'ouverte')}
    lua = f'''-- {ASSET} : base d edition, aucun warp.
-- Cascade en deux temps. Au chargement, le rideau est ferme (calques {etats['fermee']} visibles).
-- {ASSET}.ouvrir_cascade() : passe a l ouverture (calques {etats['ouverture']}, {OPEN_PHASES} phases x {FALL_TICKS} ticks
-- = {OPEN_TICKS} ticks), puis a l etat ouvert (calques {etats['ouverte']}). A appeler depuis une coroutine (cinematique).
-- NON TESTE DANS PMDO : l acces Lua a Layers[i].Visible et le calage de la phase 0 du calque d ouverture sur
-- l horloge d animation du moteur restent a verifier.
local {ASSET} = {{}}
local ETATS = {{ fermee = {{{', '.join(map(str, etats['fermee']))}}}, ouverture = {{{', '.join(map(str, etats['ouverture']))}}}, ouverte = {{{', '.join(map(str, etats['ouverte']))}}} }}
local function montrer(etat, visible)
  local carte = GAME:GetCurrentGround()
  for _, i in ipairs(ETATS[etat]) do carte.Layers[i].Visible = visible end
end
function {ASSET}.ouvrir_cascade()
  montrer('fermee', false); montrer('ouverture', true)
  GAME:WaitFrames({OPEN_TICKS})
  montrer('ouverture', false); montrer('ouverte', true)
end
return {ASSET}
'''
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua', lua.encode())
    nodes = {}
    for p in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with p.open('rb') as f:
            nodes[p.stem] = tools.read_node(f)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entree Waterfall Cave V2 sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de Waterfall Cave V2 au format 4:3 (ref. rip entrancecascade), couloir de sable jusqu'a la grotte, cascade en deux temps (fermee puis qui se fend). Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    script = (R / 'source/pmdo_cote/INSTALLER.py').read_text()
    needle = '            relative = src.relative_to(source)\n'
    assert needle in script
    script = script.replace(needle, needle + "            if relative.as_posix() == 'Content/Tile/index.idx':\n                continue\n")
    (STAGE / 'INSTALLER.py').write_text(script)
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    return {b.name: len(b.data) for b in banks}, etats


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['eau', 'scintillements', 'cascade_fermee', 'cascade_ouverture', 'cascade_ouverte', 'ecume',
             'ecume_porte_fermee', 'ecume_porte_ouverture', 'embruns']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{a}' for a in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a0 = V1.rgb(RAW / 'decor_magenta.png'); f = V1.rgb(RAW / 'sol_complet.png'); ref = V1.rgb(REF)
    m0 = V1.classify(a0)
    a, m, corr_full, corr_info = reshape_front(a0, f, m0)
    order = ['water', 'cascade', 'ecume_pied', 'entree_sombre', 'sable', 'cailloux', 'touffes', 'plateaux', 'berge',
             'falaises', 'arbres']
    ex, cols = V1.down_class(a, m, order)
    water = ex['water']
    static = ['sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres', 'entree_sombre']
    layers = {'sol_complet': V1.rgba(V1.down_full(f), ~water)}
    for k in static + ['cascade', 'ecume_pied']:
        layers[k] = V1.rgba(cols[k], ex[k])
    q = {}
    for keys, n in V1.PALETTE_GROUPS.values():
        q.update(V1.quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    corr = V1.resize_plane(corr_full.astype(np.float32)) > 0.5
    for k, v in list(ex.items()) + [('couloir', corr)]:
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in static + ['cascade', 'ecume_pied']:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(water, visible)
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in V1.place(visible & (dist > 4), (hh, ww), 4, 41 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Cascade en deux temps : même texture générée périodique, trois masques d'état.
    cave, cas = ex['entree_sombre'], ex['cascade']
    tex, fall_info = fall_texture(layers['cascade'], cas, cave)
    walk_px = layers['sable'][..., 3] == 255
    door = door_region(cas, cave, ex['arbres'] | ex['water'] | ex['ecume_pied'] | walk_px | nd.binary_dilation(corr))
    Image.fromarray((door * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_porte.png')
    c_fermee, c_ouverture, c_ouverte, opens, tmap = cascade_states(tex, cas, door)
    foam_pal = np.unique(layers['ecume_pied'][ex['ecume_pied']][:, :3], axis=0).astype(float)
    grid = (4, 4)
    puffs = V1.sheet_poses(RAW / 'ecume_poses.png', grid, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)], foam_pal)
    sprays = V1.sheet_poses(RAW / 'ecume_poses.png', grid, [(3, 3), (3, 0), (3, 1), (3, 2)], foam_pal)
    for i, p in enumerate(puffs):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_bouillon_{i}.png')
    for i, p in enumerate(sprays):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_embrun_{i}.png')
    cy_, cx_ = np.nonzero(cave); cave_x = (int(cx_.min()), int(cx_.max()))
    fy, fx = np.nonzero(ex['ecume_pied']); foot_y = int(np.median(fy))
    xs_c = np.nonzero(cas.any(0))[0]
    puff_em = [(x, foot_y, (i * 5) % FOAM_PHASES) for i, x in enumerate(range(int(xs_c.min()) + 12, int(xs_c.max()) - 11, 13))
               if not (cave_x[0] - 8 <= x <= cave_x[1] + 8)]
    pool_y = foot_y + 18
    basin = np.flatnonzero(visible[pool_y] & (np.arange(W) >= xs_c.min() - 20) & (np.arange(W) <= xs_c.max() + 20))
    left, right = basin[basin < cave_x[0]], basin[basin > cave_x[1]]
    spray_em = [(int(np.percentile(s_, p_)), pool_y, off) for s_, p_, off in
                ((left, 30, 0), (left, 75, 3), (right, 25, 6), (right, 70, 9))]
    clip = (ex['water'] | ex['ecume_pied'] | cas) & ~cave
    ecume = V1.sprite_frames(puffs, puff_em, V1.PUFF_SEQ, clip)
    embruns = V1.sprite_frames(sprays, spray_em, V1.SPRAY_SEQ, clip & ~cas)
    d_fermee, d_ouverture, door_info = door_foam(puffs, sprays, door, cas | door, walk_px, opens)
    door_info['porte_px'] = int(door.sum()); door_info['eclats_rebord_px'] = int((door & ~cave).sum())
    # Exports
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'cascade_fermee': (c_fermee, FALL_TICKS),
            'cascade_ouverture': (c_ouverture, FALL_TICKS), 'cascade_ouverte': (c_ouverte, FALL_TICKS),
            'ecume': (ecume, FOAM_TICKS), 'ecume_porte_fermee': (d_fermee, FOAM_TICKS),
            'ecume_porte_ouverture': (d_ouverture, FOAM_TICKS), 'embruns': (embruns, FOAM_TICKS)}
    state_of = {'cascade_fermee': 'fermee', 'ecume_porte_fermee': 'fermee', 'cascade_ouverture': 'ouverture',
                'ecume_porte_ouverture': 'ouverture', 'cascade_ouverte': 'ouverte'}
    order_names = ['eau', 'scintillements', 'sol_complet'] + static + ['cascade_fermee', 'cascade_ouverture', 'cascade_ouverte',
                                                                    'ecume_pied', 'ecume', 'ecume_porte_fermee',
                                                                    'ecume_porte_ouverture', 'embruns']
    stack_named, layer_list = [], []
    for i, nm in enumerate(order_names):
        etat = state_of.get(nm)
        if nm in anim:
            frames, ticks = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': len(frames), 'ticks': ticks,
                               'etat': etat, 'boucle': etat != 'ouverture'})
        else:
            frames, ticks = [layers[nm]], 60
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60, 'etat': None, 'boucle': True})
        stack_named.append((nm, frames, ticks, etat))
    # Collisions : sable relié au sud (couloir compris), cailloux, touffes enclavées.
    ground = (layers['sable'][..., 3] == 255) | (layers['cailloux'][..., 3] == 255)
    walk = ground | ((layers['touffes'][..., 3] == 255) & nd.binary_fill_holes(ground))
    blocked = V1.cell_grid(~walk); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    ccx = (cave_x[0] + cave_x[1]) // 2
    north = int(np.nonzero(walk[:, ccx])[0].min())                     # haut du couloir, au pied de la bouche
    threshold_px = [ccx // 8 * 8 - 8, north // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick, state, since=0):
        im = Image.new('RGBA', (W, H))
        for nm, frames, ticks, etat in stack_named:
            if etat is not None and etat != state:
                continue
            idx = min((tick - since) // ticks, len(frames) - 1) if etat == 'ouverture' else (tick // ticks) % len(frames)
            im.alpha_composite(Image.fromarray(frames[idx]))
        return im
    closed0, open0 = scene(0, 'fermee'), scene(0, 'ouverte')
    closed0.save(OUT / 'review' / f'{PFX}_scene_fermee_t000.png'); open0.save(OUT / 'review' / f'{PFX}_scene_ouverte_t000.png')
    step, seq = 4, []
    for t in range(0, 96, step):
        seq.append(scene(t, 'fermee'))
    for t in range(96, 96 + OPEN_TICKS, step):
        seq.append(scene(t, 'ouverture', since=96))
    for t in range(96 + OPEN_TICKS, 96 + OPEN_TICKS + 144, step):
        seq.append(scene(t, 'ouverte'))
    seq[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=seq[1:],
                duration=round(step * 1000 / 60), loop=0, lossless=True)
    ys_, xs_ = np.nonzero(cas | cave); bx0, bx1 = max(0, cave_x[0] - 70), min(W, cave_x[1] + 70)
    by0, by1 = max(0, int(cy_.min()) - 50), min(H, int(cy_.max()) + 50)
    picks = [0, 4, 7, 10, 13, 16, 19, 23]; bw, bh = (bx1 - bx0) * 2, (by1 - by0) * 2
    planche = Image.new('RGBA', (4 * (bw + 8) + 8, 2 * (bh + 8) + 8), (13, 26, 34, 255))
    for j, k in enumerate(picks):
        im = scene(96 + k * FALL_TICKS, 'ouverture', since=96).crop((bx0, by0, bx1, by1)).resize((bw, bh), Image.Resampling.NEAREST)
        planche.alpha_composite(im, (8 + (j % 4) * (bw + 8), 8 + (j // 4) * (bh + 8)))
    planche.save(OUT / 'review' / f'{PFX}_ouverture_planche_x2.png')
    col = open0.copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    # Avant / après du liseré de rive (EWC1 à gauche, EWC2 à droite), zoom x4 sur la rive nord du bassin gauche.
    v1s = R / 'renders/entree_waterfall_cave_sud_nord_v1/review/EWC1_scene_t000.png'
    if v1s.exists():
        box = (150, 228, 290, 298)
        A = Image.open(v1s).convert('RGBA').crop(box); B = open0.crop(box)
        cmp_ = Image.new('RGBA', (A.width * 8 + 12, A.height * 4), (13, 26, 34, 255))
        cmp_.alpha_composite(A.resize((A.width * 4, A.height * 4), Image.Resampling.NEAREST), (0, 0))
        cmp_.alpha_composite(B.resize((B.width * 4, B.height * 4), Image.Resampling.NEAREST), (A.width * 4 + 12, 0))
        cmp_.save(OUT / 'review' / f'{PFX}_rive_avant_apres_x4.png')
    write_ora(OUT / f'{PFX}_entree_waterfall_cave_calques.ora',
              [(f'{i:02d}_{nm}' + ('_f00' if len(fr) > 1 else ''), fr[0], etat in (None, 'fermee'))
               for i, (nm, fr, _, etat) in enumerate(stack_named)])
    counts, etats = ground_project([(nm.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk, etat)
                                    for nm, fr, tk, etat in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = V1.fidelity(a0, ref, m0['cascade'])
    final_fid = {}
    for k, nm in (('sable', 'sable'), ('roche', 'falaises'), ('feuillage', 'arbres'), ('rideau', 'cascade')):
        lay = layers[nm] if nm != 'cascade' else c_ouverte[0]
        px = lay[lay[..., 3] == 255][:, :3].astype(float)
        if nm == 'arbres':
            px = px[(px[:, 1] > px[:, 0] + 8) & (px[:, 1] > px[:, 2] + 20)]
        final_fid[k] = {'calque': nm if nm != 'cascade' else 'cascade_ouverte', 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    gv1 = json.loads((R / 'renders/entree_waterfall_cave_sud_nord_v1/manifest.json').read_text())['generation']
    manifest = {
        'lot': 'entree_waterfall_cave_sud_nord_v2', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'EWC1 (meme branche) ; memes bruts generes, aucune nouvelle generation',
        'demande': 'petits traits blancs au bord des rives -> version sans ; pas d eau devant l entree de la grotte ; '
                   'cascade en deux temps : la cascade qui prend tout puis une animation ou elle se fend pour ouvrir la grotte',
        'method': 'textures canoniques = rendu genere REFERENCE (bruts EWC1 : decor sur magenta, sol complet, planche d ecume)',
        'reference_da': {'file': 'entrancecascade.png', 'sha256': sha(REF), 'titre': 'Entree cascade (Waterfall Cave, PMD Explorers)'},
        'generation': gv1,
        'raw_inputs': [{'file': f'source/entree_waterfall_cave_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in gv1],
        'changements_v2': {
            'liseré_de_rive': {'retire': REMOVED, 'rgb': list(PAL[REMOVED]),
                               'avant': 'water_phases posait des tirets de 1 px couleur clair contre chaque rive',
                               'apres': 'bande sombre directement contre la rive ; couleurs restantes surface, inter, accent, bande'},
            'couloir': dict(corr_info, bords_pleine_res=CORR_KNOTS,
                            pixels='sol complet GENERE ; berge de raccord = ce sable assombri au rapport mesure berge/sable '
                                   '(<= 3 px de l eau) ; lisiere : blancs de l ecume dessinee gardes a <= 5 px du bord'),
            'cascade_deux_temps': {'fermee': 'rideau sur la porte = bouche entiere + eclats de rebord enclaves (meme texture '
                                             'periodique prolongee) + bouillons au pied',
                                   'ouverture': f'{OPEN_PHASES} phases x {FALL_TICKS} ticks = {OPEN_TICKS} ticks, jouee une fois ; '
                                                f'temps d ouverture = {SLIT_U} x ecart au centre + {SLIT_V} x profondeur, lissage '
                                                'smoothstep ; levres de la fente = blanc du rideau (1 px) + eclairci (1 px), dans la bouche seulement ; '
                                                'gerbes generees aux levres basses',
                                   'ouverte': 'rideau qui contourne la bouche (masque EWC1)',
                                   'origine': 'pixels GENERES du rideau et de l ecume ; masques, fente et chronologie crees par nous, '
                                              'pas une animation officielle'}},
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur sur le rip et sur le brut (rideau : boite '
                                    'x 150-355, y 0-180 du rip contre rideau segmente) ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in V1.PALETTE_GROUPS.items()}},
        'layers': layer_list,
        'etats': {'defaut': 'fermee', 'sequence': ['fermee', 'ouverture', 'ouverte'], 'ouverture_ticks': OPEN_TICKS,
                  'calage': f'lancer l ouverture sur un tick multiple de {FALL_PHASES * FALL_TICKS} (phase 0 du rideau) '
                            'pour un defilement continu', 'pmdo_calques': etats},
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'couleurs': {k: list(v) for k, v in PAL.items() if k != REMOVED},
                  'modele': 'structure et cadence riviere Metano, couleurs Metano EXACTES, sans liseré de rive',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'cascade': dict(fall_info, phases=FALL_PHASES, frame_length_ticks=FALL_TICKS, period_px=FALL_PERIOD,
                        blend_px=FALL_BLEND, step_px=FALL_STEP, ouverture_phases=OPEN_PHASES,
                        origine='pixels GENERES du rideau du decor, rendus periodiques par fondu puis ramenes a la palette '
                                'du rideau ; defilement cree par nous, pas une animation officielle'),
        'foam': {'brut': 'source/entree_waterfall_cave_sud_nord_v1/bruts/ecume_poses.png', 'grille_rendue': list(grid),
                 'bouillon': {'cases': [[0, c] for c in range(4)] + [[1, c] for c in range(4)], 'sequence': V1.PUFF_SEQ,
                              'emetteurs': [list(e) for e in puff_em]},
                 'embruns': {'cases': [[3, 3], [3, 0], [3, 1], [3, 2]], 'sequence': V1.SPRAY_SEQ, 'emetteurs': [list(e) for e in spray_em]},
                 'porte': door_info,
                 'reduction': f'fenetre {V1.FCELL * V1.FK} px -> {V1.FCELL} px (x1/{V1.FK}) centree, palette = couleurs de l ecume du pied',
                 'phases': FOAM_PHASES, 'frame_length_ticks': FOAM_TICKS,
                 'origine': 'dessin GENERE, emetteurs et chronologie crees ; pas une animation officielle'},
        'shadows': 'aucun calque d ombres : le rendu genere ne contient pas d ombre portee separable',
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sable praticable/cailloux/touffes enclavees',
                   'seuil': 'haut du couloir de sable, au pied de la bouche (visible une fois la cascade ouverte)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun', 'script': 'init.lua : ouvrir_cascade(), NON TESTE'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'cells': int(blocked.size), 'couloir': corr_info, 'spray': spray_em, 'door': door_info,
                      'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'etats': etats,
                      'tiles': sum(counts.values())}, indent=1))


if __name__ == '__main__':
    build()
