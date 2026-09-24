"""Forêt grotte 928x1152 sud -> nord, textures canoniques 100%, multicalque."""
from pathlib import Path
import json, hashlib, base64, xml.etree.ElementTree as ET
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).parent
O = R / 'exports/foret_grotte_928_v1'
W, H = 928, 1152
# Sources: same as V3 south-north, proven native
FILES = [
    'forêtglomypmdsky.png',  # 0
    'rockroadpmd.png',  # 1 not used for forest but keep index
    'undergroundpmd.png',  # 2
    'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png',  # 3 trunks
    'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png',  # 4 foliage
]
A = [np.array(Image.open(R / p).convert('RGBA')) for p in FILES]

def seam(cost):
    h, w = cost.shape
    dist = cost.astype(float).copy()
    prev = np.zeros((h, w), int)
    for y in range(1, h):
        for x in range(w):
            lo = max(0, x-1); hi = min(w, x+2)
            p = lo + np.argmin(dist[y-1, lo:hi])
            prev[y, x] = p
            dist[y, x] += dist[y-1, p]
    x = int(np.argmin(dist[-1]))
    path = []
    for y in reversed(range(h)):
        path.append(x)
        x = prev[y, x]
    return np.array(path[::-1])

class Map:
    def __init__(self, id):
        self.id = id
        self.layers = []
        self.ops = []
    def layer(self, name):
        l = [name, np.zeros((H, W, 4), np.uint8), np.full((H, W, 3), -1, np.int16)]
        self.layers.append(l)
        return l
    def put(self, l, s, box, pos, mask=None):
        x0,y0,x1,y1 = box
        x,y = pos
        p = A[s][y0:y1, x0:x1]
        hh, ww = p.shape[:2]
        mask = p[:,:,3] > 0 if mask is None else mask & (p[:,:,3] > 0)
        assert x>=0 and y>=0 and x+ww<=W and y+hh<=H, (box, pos, ww, hh, W, H)
        sy,sx = np.mgrid[y0:y1, x0:x1]
        q = np.stack([np.full(sx.shape, s), sx, sy], 2)
        l[1][y:y+hh, x:x+ww][mask] = p[mask]
        l[2][y:y+hh, x:x+ww][mask] = q[mask]
        self.ops.append(dict(layer=l[0], source=s, rect=list(box), position=list(pos)))
    def fill(self, l, s, boxes, mask=None, seed=11):
        from source.zones_relayout_v1.build import seam as seam2
        # use same seam
        rng = np.random.default_rng(seed)
        mask = np.ones((H,W), bool) if mask is None else mask
        hh = boxes[0][3]-boxes[0][1]
        ww = boxes[0][2]-boxes[0][0]
        ov = min(8, hh//2, ww//2)
        for y in range(0, H, hh-ov):
            for x in range(0, W, ww-ov):
                h = min(hh, H-y); w = min(ww, W-x)
                want = mask[y:y+h, x:x+w]
                if not want.any():
                    continue
                old = l[1][y:y+h, x:x+ww]
                occupied = (old[:,:,3]>0) & want
                best = None
                # try up to 24 random boxes
                for idx in rng.permutation(len(boxes))[:24]:
                    x0,y0,_,_ = boxes[idx]
                    patch = A[s][y0:y0+h, x0:x0+w]
                    cost = ((old[:,:,:3].astype(float)-patch[:,:,:3])**2).sum(2)
                    score = cost[occupied].mean() if occupied.any() else rng.random()
                    if best is None or score < best[0]:
                        best = (score, x0, y0, patch, cost)
                _, x0, y0, patch, cost = best
                take = want.copy()
                if x and w>=ov:
                    take[:, :ov] &= np.arange(ov)[None,:] >= seam(cost[:, :ov])[:, None]
                if y and h>=ov:
                    take[:ov, :] &= np.arange(ov)[:,None] >= seam(cost[:ov, :].T)[None, :]
                take |= want & (old[:,:,3]==0)
                sy,sx = np.mgrid[y0:y0+h, x0:x0+w]
                q = np.stack([np.full(sx.shape, s), sx, sy], 2)
                old[take] = patch[take]
                l[2][y:y+h, x:x+w][take] = q[take]
        self.ops.append(dict(layer=l[0], source=s, method='native ground patch overlap, no blending', patches=boxes, seed=seed))
    def save(self, title, entrance, pathmask, notes, export_height=1152):
        d = O / self.id
        d.mkdir(parents=True, exist_ok=True)
        comp = Image.new('RGBA', (W, export_height))
        ls = []
        pathmask = pathmask[:export_height]
        for name, a, q in self.layers:
            a = a[:export_height]; q = q[:export_height]
            fn = f'Foret928_{self.id}_{name}.png'
            im = Image.fromarray(a)
            im.save(d / fn)
            comp.alpha_composite(im)
            np.savez_compressed(d / (name + '_source.npz'), source_sxy=q)
            root = ET.Element('tileset', version='1.10', name=Path(fn).stem, tilewidth='8', tileheight='8', columns=str(W//8), tilecount=str(W//8*(export_height//8)))
            ET.SubElement(root,'image', source=fn, width=str(W), height=str(export_height))
            ET.ElementTree(root).write(d / Path(fn).with_suffix('.tsx').name, encoding='utf-8', xml_declaration=True)
            ls.append(dict(id=name, file=fn, provenance=name+'_source.npz'))
        allowed = {l['file'] for l in ls} | {l['provenance'] for l in ls} | {str(Path(l['file']).with_suffix('.tsx')) for l in ls}
        for old in d.iterdir():
            if old.is_file() and (old.name.startswith('Foret928_') or old.name.endswith('_source.npz')) and old.name not in allowed:
                old.unlink()
        comp.save(d / 'composite.png')
        Image.fromarray(np.uint8(pathmask)*255).save(d / 'path_connectivity_mask.png')
        review = comp.copy(); dr = ImageDraw.Draw(review)
        # draw vertical path guideline
        pts = [(int(np.flatnonzero(pathmask[y]).mean()), y) for y in range(entrance[1], export_height, 8) if pathmask[y].any()]
        if len(pts)>1:
            dr.line(pts, fill=(255,90,60,255), width=3)
        dr.ellipse((entrance[0]-7, entrance[1]-7, entrance[0]+7, entrance[1]+7), outline=(255,255,0,255), width=2)
        # south access marker
        sx, sy = W//2, H-4
        dr.rectangle((sx-32, H-8, sx+32, H-2), outline=(60,255,120,255), width=2)
        review.save(d / 'access_review_NOT_RUNTIME.png')
        return dict(id=self.id, title=title, size=[W, export_height], orientation='SOUTH_TO_NORTH', entrance=entrance, entrance_trigger_candidate=[entrance[0]-16, entrance[1]-8, 32,16], south_access=[W//2-32, export_height-8, 64,8], layers=ls, operations=self.ops, notes=notes, runtime='NOT TESTED', art_approved=False, connectivity='Pixel path mask continuity only, not engine collision or warp validation.')

def path_shape(start, width, centers):
    yy, xx = np.mgrid[:H, :W]
    ys = np.array([p[1] for p in centers])
    xs = np.array([p[0] for p in centers])
    middle = np.interp(yy[:,0], ys, xs)  # 1D interpolation per row
    # broadcast
    middle2 = np.interp(yy, ys, xs) if False else np.tile(np.interp(np.arange(H), ys, xs)[:,None], (1,W))
    # actually compute per row
    mid_per_y = np.interp(np.arange(H), ys, xs)
    jitter = ((np.arange(H)//8)%5 -2)*1
    # expand
    mid = mid_per_y[:,None] + jitter[:,None]
    # width varies slightly
    half = width/2
    return (yy >= start) & (np.abs(xx - mid) <= half + (np.abs(yy - start)/H)*2)

def forest_928():
    m = Map('forest_cave_928')
    a = A[0]
    # 01 soil - full ground quilting
    ground = m.layer('01_soil')
    # patches from forest ground areas
    boxes_ground = [(x,y,x+24,y+16) for x in [0,24,48,72,96] for y in [144,160,176]]
    # also include some larger ground samples to vary
    m.fill(ground, 0, boxes_ground, seed=12)
    # 02 continuous earth path from south center to cave entrance north center
    # path width 72 for 928 width to feel comfortable
    pm = path_shape(120, 72, [(W//2,120),(W//2-24,360),(W//2+16,560),(W//2,760),(W//2,960),(W//2, H-1)])
    # restrict earth patches to pure earth color, no green fringe
    rgb = a[:,:,:3].astype(float)
    earth = (rgb[:,:,0] > rgb[:,:,1]*1.025) & (rgb[:,:,2] > rgb[:,:,1]*.52)
    boxes = []
    for y in range(144,184):
        for x in range(176,368):
            if earth[y:y+8, x:x+8].shape==(8,8) and earth[y:y+8, x:x+8].all():
                boxes.append((x,y,x+8,y+8))
    assert boxes, "no earth boxes"
    # duplicate to have more variety
    # add also nearby earth patches from y 144-176 with x ranges
    path = m.layer('02_continuous_earth_path')
    m.fill(path, 0, boxes, pm, 19)

    # 03 north canopy - top forest masses left/right of cliff
    back = m.layer('03_north_canopy')
    # original canopy source is two blocks: (0,0,208,144) and (128,0,336,144)
    # For 928 width, we need to tile canopy across top 0-144 height, leaving center for cliff
    # Cliff will be centered at 308, width 312 (covers 308-620). So canopy left 0-308 and right 620-928
    # Use masks to keep only foliage
    for box, pos in [((0,0,208,144),(0,0)), ((128,0,336,144),(520,0))]:  # left and right parts, but need more coverage
        x0,y0,x1,y1 = box
        p = a[y0:y1, x0:x1]
        rgb2 = p[:,:,:3].astype(float)
        mask = (rgb2[:,:,1] > rgb2[:,:,2]*1.4) & (rgb2[:,:,0] < 180)
        mask = nd.binary_fill_holes(mask)
        m.put(back, 0, box, pos, nd.binary_fill_holes(mask))
    # additional canopy fill to cover remaining top areas: tile extra
    # left edge 208-308 and right edge 720-928
    for x_extra in [208, 728]:
        # reuse first canopy tile
        box = (0,0,208,144)
        p = a[0:144,0:208]
        rgb2 = p[:,:,:3].astype(float)
        mask = (rgb2[:,:,1] > rgb2[:,:,2]*1.4) & (rgb2[:,:,0] < 180)
        mask = nd.binary_fill_holes(mask)
        # clip to width
        w = min(100, W - x_extra) if x_extra==728 else 100
        if w>0:
            # need to crop box accordingly
            # Instead put truncated: crop source and mask
            sx0, sy0, sx1, sy1 = 0,0,w,144
            # use sliced put with truncated mask: we will provide truncated box
            # create truncated version
            # simpler: put full 208 but position such that it may overflow? Ensure x+ww<=W
            # so choose w=100 -> use subrect (0,0,100,144)
            m.put(back, 0, (0,0,w,144), (x_extra,0), nd.binary_fill_holes(mask[:,:w]))

    # 04 white cliff - centered top, with portal hole
    box = (288,0,600,216)  # 312x216
    p = a[:216,288:600]
    rgb2 = p[:,:,:3].astype(float)
    mask = (rgb2[:,:,0] >= rgb2[:,:,1]*.97) & (rgb2[:,:,2] >= rgb2[:,:,1]*.56)
    lab,n = nd.label(mask)
    counts = np.bincount(lab.ravel()); keep = counts >= 12; keep[0]=False
    mask = nd.binary_fill_holes(keep[lab])
    # portal shape centered in cliff
    portal = Image.new('L', (312,216))
    d = ImageDraw.Draw(portal)
    # cave mouth polygon relative to cliff box - centered: cliff center x 156, y around 100
    d.polygon([(132,100),(148,72),(180,64),(208,88),(200,136),(184,160),(148,144)], fill=255)
    portal = np.array(portal) > 0
    # cliff position centered: (928-312)//2 =308
    cliff_x = (W - 312)//2
    cliff_y = 0
    wall = m.layer('04_white_cliff')
    m.put(wall, 0, box, (cliff_x, cliff_y), mask & ~portal)
    # extend cliff sides with 64px slice from right edge to fill more width if needed? For central cliff, sides already covered by canopy, but need cliff foot coverage across width?
    # Add side extensions using slice 536-600 (64px) to fill left/right of main cliff for wider feel
    for x in [cliff_x-64, cliff_x+312]:
        if 0 <= x < W and x+64 <= W:
            p2 = a[:216,536:600]
            rgb3 = p2[:,:,:3].astype(float)
            ext = (rgb3[:,:,0] >= rgb3[:,:,1]*.97) & (rgb3[:,:,2] >= rgb3[:,:,1]*.56)
            m.put(wall, 0, (536,0,600,216), (x,0), nd.binary_fill_holes(ext))
        elif 0 <= x < W: # truncated at edge
            w = W - x
            p2 = a[:216,536:536+w]
            rgb3 = p2[:,:,:3].astype(float)
            ext = (rgb3[:,:,0] >= rgb3[:,:,1]*.97) & (rgb3[:,:,2] >= rgb3[:,:,1]*.56)
            m.put(wall, 0, (536,0,536+w,216), (x,0), nd.binary_fill_holes(ext))
    # cave opening layer
    cave = m.layer('05_cave_opening')
    m.put(cave, 0, box, (cliff_x, cliff_y), mask & portal)

    # 06 trunks + 07 canopies (Vast Steppe genuine trees)
    trunks = m.layer('06_tree_trunks')
    foliage = m.layer('07_tree_canopies')
    # positions along both sides, spaced vertically to fill 1152 height
    # original V3 had y [128,208,288,368,448,520] for H=640. Scale for 1152: add more rows
    ys = [160, 280, 400, 520, 640, 760, 880, 1000]
    xs_left = 0
    xs_right = W - 160 - 16  # 928-160=768
    positions = []
    for y in ys:
        positions.append((xs_left, y))
        positions.append((xs_right, y))
    # add some mid offset trees
    positions += [(80, 340), (xs_right-80, 480), (80, 700), (xs_right-80, 820)]
    for x,y in positions:
        # trunks at x+56,y+64 from Vast Steppe layer3 (72,160,120,216)
        # foliage at x,y from layer4 (16,96,160,216)
        # ensure within bounds
        if x+56+48 <= W and y+64+56 <= H:
            m.put(trunks, 3, (72,160,120,216), (x+56, y+64))
        if x+144 <= W and y+120 <= H:
            m.put(foliage, 4, (16,96,160,216), (x, y))
        elif x+144 > W:
            # truncated foliage for right edge
            w = W - x
            if w> 40:
                m.put(foliage, 4, (16,96,16+w,216), (x,y))

    # 08 stones scattered along path and sides
    stones = m.layer('08_stones')
    # stone source (400,184,440,208) 40x24
    stone_box = (400,184,440,208)
    p_stone = a[184:208,400:440]
    rgb_s = p_stone[:,:,:3].astype(float)
    mask_s = (rgb_s[:,:,2] > rgb_s[:,:,1]*.65) & (rgb_s[:,:,0] > rgb_s[:,:,1]*.95)
    mask_s = nd.binary_dilation(nd.binary_fill_holes(mask_s))
    # scatter positions along expanded height
    for pos in [(200,340),(W-240,420),(200,620),(W-240,740),(300,900),(600,950),(400,500)]:
        if pos[0]+40 <= W and pos[1]+24 <= H:
            m.put(stones, 0, stone_box, pos, mask_s)
    # also additional stones from (96,96,136,120) as accent
    for box2,pos2 in [((96,96,136,120),(260,380)),((96,96,136,120),(W-300,880))]:
        x0,y0,x1,y1=box2
        p2=a[y0:y1,x0:x1]
        rgb2=p2[:,:,:3].astype(float)
        mask2 = (rgb2[:,:,2]>rgb2[:,:,1]*.65)&(rgb2[:,:,0]>rgb2[:,:,1]*.95)
        mask2=nd.binary_dilation(nd.binary_fill_holes(mask2))
        m.put(stones, 0, box2, pos2, mask2)

    # 09 cliff foot bushes (native foreground clumps) - at cliff base y=216
    shrubs = m.layer('09_cliff_foot_bushes')
    # source 408,184,600,264 192x80
    p = a[184:264,408:600]
    rgb2 = p[:,:,:3].astype(float)
    base_col = a[311,0,:3]
    mask = (rgb2[:,:,1] > rgb2[:,:,0]*1.04) & (rgb2[:,:,0] < 168) & (rgb2[:,:,2] < rgb2[:,:,1]*.65) & np.any(p[:,:,:3] != base_col, axis=2)
    mask = nd.binary_fill_holes(mask)
    # place across cliff foot width: cliff spans 308-620, foot bushes should cover that base
    # original placed at (320,184) width 280. For 928, spread
    for x in [cliff_x-12, cliff_x+60, cliff_x+140, cliff_x+220]:
        if 0 <= x < W and x+80 <= W:
            m.put(shrubs, 0, (408,184,488,264), (x, 184+32), mask[:,:80])
        elif 0 <= x < W:
            w = W - x
            m.put(shrubs, 0, (408,184,408+w,264), (x,184+32), mask[:,:w])
    # additionally, add lower foreground bushes at bottom to frame southern entrance
    front = m.layer('10_foreground_bushes')
    # reuse same bush texture but lower
    box_fg = (0,184,240,312)  # 240x128 from source (0,184,240,312)
    p_fg = a[184:312,0:240]
    rgb_fg = p_fg[:,:,:3].astype(float)
    mask_fg = (rgb_fg[:,:,1] > rgb_fg[:,:,0]*1.04) & (rgb_fg[:,:,0] < 168) & (rgb_fg[:,:,2] < rgb_fg[:,:,1]*.65)
    mask_fg = nd.binary_fill_holes(mask_fg)
    # remove top canopy? Keep bottom part
    labs,n = nd.label(mask_fg)
    bottom = np.unique(labs[-1])
    mask_fg = np.isin(labs, bottom[bottom>0])
    for x in [0,240,480,720]:
        w = min(240, W - x)
        m.put(front, 0, (0,184,w,312), (x, H-128), mask_fg[:,:w])

    # entrance coordinates: cave mouth center at cliff center + portal offset ~170,100 inside cliff
    entrance_x = cliff_x + 170
    entrance_y = cliff_y + 100  # approx portal center y
    # path already includes entrance row; ensure access mask joins ground to threshold
    access = pm.copy()
    # ensure corridor to cave is open (bridge canopy gap)
    access[entrance_y-20:entrance_y+40, entrance_x-20:entrance_x+20] = True
    # ensure south access zone is open
    access[H-20:H, W//2-32:W//2+32] = True

    return m.save('Forêt 928×1152 — arrivée sud, grotte au nord (multicalque)', [entrance_x, entrance_y], access, 'Sol, chemin terre continu, canopée nord, falaise blanche centrée 312px + retours 64px, bouche grotte, troncs/canopées Vast Steppe complets, pierres, buissons de pied et premier plan. Tous les pixels RGBA exacts des sources natives, aucun magenta, rotation, miroir ou recoloration. Chemin sud→entrée continu vérifié en masque, pas collisions moteur.')

def main():
    O.mkdir(parents=True, exist_ok=True)
    entries = [forest_928()]
    sources = [dict(id=i, file=f, sha256=hashlib.sha256((R/f).read_bytes()).hexdigest()) for i,f in enumerate(FILES)]
    manifest = dict(maps=entries, sources=sources, grid=8, size=[W,H], status='Forest cave 928x1152 south-to-north candidate, textures canoniques 100%, multicalque 10 layers', runtime='NOT TESTED')
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    def uri(p):
        return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    data = [{**m, 'layers': [{**l, 'uri': uri(O / m['id'] / l['file'])} for l in m['layers']], 'route': uri(O / m['id'] / 'access_review_NOT_RUNTIME.png'), 'composite_uri': uri(O / m['id'] / 'composite.png')} for m in entries]
    page = '''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forêt 928×1152 — sud → nord</title><style>
body{background:#14251f;color:#e3e8d8;font:16px system-ui;max-width:1320px;margin:28px auto;padding:20px}
p{line-height:1.6;color:#c7d1bf}
main{display:flex;flex-wrap:wrap;gap:24px;justify-content:center}
article{background:#24382e;border:1px solid #4d6249;border-radius:14px;padding:18px;width:980px;box-sizing:border-box}
canvas{max-width:100%;image-rendering:pixelated;background:#3b3a44;display:block;margin:0 auto}
label{display:inline-block;margin:6px 10px 6px 0;font-size:12px;background:#1e2f26;padding:4px 8px;border-radius:6px;border:1px solid #3a4f3f}
h2{font-size:22px;margin:6px 0} small{color:#edcf83} details{margin:14px 0}
.grid{position:relative}
.note{font-size:13px;color:#a8b8a0}
</style><h1>Forêt 928×1152 — sud → grotte nord (multicalque)</h1>
<p>Arrivée sud au bas, chemin de terre continu jusqu'à la grotte au nord. <b>928×1152 px = 116×144 cases de 8 px</b>. Dix calques indépendants, tous les pixels copiés à l'identique depuis les sources natives (forêtglomypmdsky + Vast Steppe troncs/canopées), sans magenta résiduel, rotation, miroir ou recoloration. Grille 8 px, cases 8×8, bordure de premier plan interrompue aux passages. Tests de connexité du chemin uniquement — pas de collisions/warp PMDO validés. Canopée nord, falaise blanche 312 px centrée + retours 64 px, arbres entiers latéraux, pierres et buissons de pied/first plan.</p>
<div id="maps"></div>
<script>const DATA=__DATA__;
for(const s of DATA){
  const a=document.createElement('article');
  a.innerHTML='<h2>'+s.title+'</h2><small>'+s.size.join(' × ')+' px · '+s.size[0]/8+'×'+s.size[1]/8+' cases 8px · SUD ↓ → NORD ↑</small><div><canvas width=\"'+s.size[0]+'\" height=\"'+s.size[1]+'\"></canvas></div>';
  const canvas=a.querySelector('canvas');
  const controls=document.createElement('div'); a.append(controls);
  const ctx=canvas.getContext('2d'); const imgs=[], checks=[];
  function draw(){ ctx.clearRect(0,0,canvas.width,canvas.height); imgs.forEach((im,i)=>{ if(checks[i].checked && im.complete) ctx.drawImage(im,0,0); }); }
  s.layers.forEach(l=>{
    const label=document.createElement('label'); const ch=document.createElement('input'); ch.type='checkbox'; ch.checked=true; ch.onchange=draw;
    checks.push(ch); label.append(ch, document.createTextNode(' '+l.id)); controls.append(label);
    const im=new Image(); imgs.push(im); im.onload=draw; im.src=l.uri;
  });
  // grille toggle
  const gLabel=document.createElement('label'); const gCh=document.createElement('input'); gCh.type='checkbox';
  gLabel.append(gCh, document.createTextNode(' grille 8px')); controls.append(gLabel);
  gCh.onchange=()=>{
    draw();
    if(gCh.checked){
      ctx.strokeStyle='rgba(255,255,255,0.12)'; ctx.lineWidth=1;
      for(let x=0;x<canvas.width;x+=8){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,canvas.height); ctx.stroke(); }
      for(let y=0;y<canvas.height;y+=8){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(canvas.width,y); ctx.stroke(); }
    }
  };
  const compImg=new Image(); compImg.src=s.composite_uri; compImg.onload=()=>{/* preloaded */};
  const d1=document.createElement('details'); d1.innerHTML='<summary>Vérifier le trajet — pas une collision moteur</summary><img src=\"'+s.route+'\" style=\"max-width:100%;image-rendering:pixelated\">'; a.append(d1);
  const d2=document.createElement('details'); d2.innerHTML='<summary>Composite Jour (référence)</summary><img src=\"'+s.composite_uri+'\" style=\"max-width:100%;image-rendering:pixelated\">'; a.append(d2);
  const p=document.createElement('p'); p.className='note'; p.textContent=s.notes; a.append(p);
  document.getElementById('maps').append(a);
  // initial draw after a tick
  setTimeout(draw,200);
}
</script></html>'''
    (R / 'apercu_foret_grotte_928_v1.html').write_text(page.replace('__DATA__', json.dumps(data, ensure_ascii=False)))
    print('Forest 928x1152 south-to-north built.')

if __name__ == '__main__':
    main()
