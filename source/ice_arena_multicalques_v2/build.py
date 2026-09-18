"""Ice arena V1 layout guide -> 5-layer export + animated aurora (generator-guided).

The user asked to run the zone through the generator to decompose the map into
several layouts whose composite equals the reference: terrain / bordure / cliff /
sky / boreal. The generator produced a flat semantic mask
(`generation/layer_masks_guide.png`); this script uses it to assign every
*reference* pixel to a layer, so the recomposition is exactly the reference
(geometry and pixels preserved, never regenerated). The sky/aurora split at the
top is done programmatically (clean saturated-aurora detection); the ice region
is split terrain/bordure/cliff by the generator mask.

The aurora (boréal) is its own animated layer: hue cycle + slight transverse
undulation, loop-closed, frame 0 == the reference aurora. Generated-art
animation, not the official game cycle.
"""
from pathlib import Path
import json, colorsys, hashlib, base64, io, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]; SRC = Path(__file__).parent
GUIDE = ROOT/'source/ice_arena_aurora_v1/generation/layout_guide.png'
MASK = SRC/'generation/layer_masks_guide.png'
OUT = ROOT/'exports/ice_arena_multicalques_v2'

T = 24; FPS_MS = 120; HUE_TURNS = 1; WAVE_AMP = 2; WAVE_K = 2
IDX = {'terrain': (255, 0, 0), 'bordure': (0, 255, 0), 'cliff': (0, 0, 255),
       'ciel': (0, 0, 0), 'boreal': (255, 0, 255)}


def segment(src, mask):
    r, g, b = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    ice = (b > 110) & (g > 95) & (r > 70)
    lab, n = nd.label(~ice)
    top = set(lab[0, :].tolist()) - {0}
    terrain_region = ~np.isin(lab, list(top))
    # quantize generator mask to nearest index color
    m = mask.astype(int)
    keys = list(IDX)
    stack = np.stack([m - np.array(IDX[k]) for k in keys], axis=0)  # (5,H,W,3)
    dist = (stack**2).sum(-1)
    lab_idx = np.argmin(dist, axis=0)
    lbl = np.array(keys)[lab_idx]
    # top region: programmatic sky/boreal
    green = (g > r + 30) & (g > b + 10)
    magenta = (r > 100) & (b > 100) & (g < r - 40) & (g < b - 20)
    boreal = ~terrain_region & (green | magenta)
    ciel = ~terrain_region & ~boreal
    terrain = terrain_region & (lbl == 'terrain')
    bordure = terrain_region & (lbl == 'bordure')
    cliff = terrain_region & ~terrain & ~bordure  # blue + any spire-tip mislabels
    return {'ciel': ciel, 'boreal': boreal, 'terrain': terrain,
            'bordure': bordure, 'cliff': cliff}


def rgba(src, mask):
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[:, :, :3] = src
    out[:, :, 3] = (mask * 255).astype(np.uint8)
    return out


def hue_shift(layer, theta):
    if theta == 0:
        return layer
    a = layer[:, :, 3] > 0
    rgb = layer[:, :, :3][a].astype(float) / 255.0
    out = np.empty_like(rgb)
    for i, (rr, gg, bb) in enumerate(rgb):
        h, l, s = colorsys.rgb_to_hls(rr, gg, bb)
        out[i] = colorsys.hls_to_rgb((h + theta) % 1.0, l, s)
    res = layer.copy()
    res[:, :, :3][a] = np.round(out * 255).astype(np.uint8)
    return res


def undulate(layer, t):
    H, W = layer.shape[:2]
    off = np.round(WAVE_AMP * np.sin(2*np.pi*t/T) * np.sin(2*np.pi*WAVE_K*np.arange(W)/W)).astype(int)
    out = np.zeros_like(layer)
    for x in range(W):
        d = off[x]
        if d == 0:
            out[:, x] = layer[:, x]
        elif d > 0:
            out[d:, x] = layer[:-d, x]
        else:
            out[:d, x] = layer[-d:, x]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src = np.array(Image.open(GUIDE).convert('RGB'))
    mask = np.array(Image.open(MASK).convert('RGB').resize((src.shape[1], src.shape[0]), Image.NEAREST))
    masks = segment(src, mask)
    (OUT/'layers').mkdir(exist_ok=True)
    L = {}
    for name in ['ciel', 'boreal', 'terrain', 'bordure', 'cliff']:
        L[name] = rgba(src, masks[name])
        Image.fromarray(L[name]).save(OUT/'layers'/f'{name}.png')

    frames = []
    for t in range(T):
        f = undulate(L['boreal'], t)
        f = hue_shift(f, HUE_TURNS * t / T)
        frames.append(f)
    (OUT/'aurora_frames').mkdir(exist_ok=True)
    for i, f in enumerate(frames):
        Image.fromarray(f).save(OUT/'aurora_frames'/f'frame_{i:02d}.png')
    imgs = [Image.fromarray(f) for f in frames]
    imgs[0].save(OUT/'boreal_anime.webp', save_all=True, append_images=imgs[1:], duration=FPS_MS, loop=0, lossless=True)
    imgs[0].save(OUT/'boreal_anime.gif', save_all=True, append_images=imgs[1:], duration=FPS_MS, loop=0, disposal=2)

    ORDER = ['ciel', 'boreal', 'terrain', 'bordure', 'cliff']
    scene = []
    for f in frames:
        c = np.zeros((*f.shape[:2], 4), np.uint8)
        for lay in [L['ciel'], f, L['terrain'], L['bordure'], L['cliff']]:
            c = np.where(lay[:, :, 3:4] > 0, lay, c)
        scene.append(c)
    simgs = [Image.fromarray(s) for s in scene]
    simgs[0].save(OUT/'scene_animee.gif', save_all=True, append_images=simgs[1:], duration=FPS_MS, loop=0, disposal=2)

    comp = np.zeros((*src.shape[:2], 4), np.uint8)
    for lay in [L['ciel'], frames[0], L['terrain'], L['bordure'], L['cliff']]:
        comp = np.where(lay[:, :, 3:4] > 0, lay, comp)
    reconstruct = bool(np.array_equal(comp[:, :, :3], src))

    report = {'scope': 'Generator-guided decomposition of the V1 guide into 5 layers (terrain/bordure/cliff/ciel/boreal); composite equals the reference. Aurora animated (hue cycle + slight undulation). Geometry not regenerated.',
              'source': str(GUIDE.relative_to(ROOT)), 'source_sha256': hashlib.sha256(GUIDE.read_bytes()).hexdigest(),
              'mask': str(MASK.relative_to(ROOT)), 'layers': ORDER, 'frames': T, 'frame_ms': FPS_MS,
              'hue_turns': HUE_TURNS, 'wave_amplitude_px': WAVE_AMP, 'wave_periods': WAVE_K,
              'layer_pixel_counts': {k: int(masks[k].sum()) for k in ORDER},
              'reconstruction_exact': reconstruct, 'art_approved': False, 'runtime_PMDO': 'NOT TESTED'}
    (OUT/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    viewer(report, L, frames)
    pack_zip()
    print('reconstruct:', reconstruct, {k: int(masks[k].sum()) for k in ORDER})


def viewer(report, L, frames):
    SC = 0.5
    def b64(arr):
        buf = io.BytesIO()
        Image.fromarray(arr).resize((int(arr.shape[1]*SC), int(arr.shape[0]*SC)), Image.NEAREST).save(buf, 'png')
        return base64.b64encode(buf.getvalue()).decode()
    data = {k: b64(v) for k, v in L.items()}
    afr = [b64(f) for f in frames]
    names = {'ciel': 'Ciel/étoiles', 'boreal': 'Boréal (animé)', 'terrain': 'Terrain neige', 'bordure': 'Bordure rochers', 'cliff': 'Falaises/glaces'}
    boxes = ''.join(f'<label><input type="checkbox" id="c_{k}" checked> {names[k]}</label>' for k in ['ciel', 'boreal', 'terrain', 'bordure', 'cliff'])
    html = '''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arène de glace · 5 calques + boréal animé</title><style>body{font:16px system-ui;max-width:1000px;margin:24px auto;padding:0 16px;background:#10161f;color:#e8f1f8}label{margin-right:12px;user-select:none}canvas{image-rendering:pixelated;max-width:100%;background:#000;border-radius:8px}.note{border-left:3px solid #f4c477;padding:12px;background:#1c2530}</style><h1>Arène de glace — 5 calques & boréal animé</h1><p class="note">Le guide V1 est décomposé (via carte sémantique du générateur) en 5 calques : terrain / bordure / cliff / ciel / boréal. Le composite recompose exactement la référence. Le boréal change de couleur avec une légère ondulation ; frame 0 = référence. Art généré, pas le cycle officiel ; runtime PMDO non testé.</p><p>''' + boxes + '''<label><input type="checkbox" id="c_anim" checked> Animer</label></p><canvas id="cv" width="464" height="576"></canvas><script>
const L=''' + json.dumps(data) + ''';const A=''' + json.dumps(afr) + ''';
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');const img={};
function load(k,s){return new Promise(r=>{const i=new Image();i.onload=()=>{img[k]=i;r()};i.src=s})}
Promise.all([...Object.entries(L).map(([k,s])=>load(k,s)),...A.map((s,i)=>load('a'+i,s))]).then(()=>{let f=0;
function draw(){ctx.clearRect(0,0,cv.width,cv.height);
if(document.getElementById('c_ciel').checked)ctx.drawImage(img.ciel,0,0);
if(document.getElementById('c_boreal').checked)ctx.drawImage(img['a'+f],0,0);
if(document.getElementById('c_terrain').checked)ctx.drawImage(img.terrain,0,0);
if(document.getElementById('c_bordure').checked)ctx.drawImage(img.bordure,0,0);
if(document.getElementById('c_cliff').checked)ctx.drawImage(img.cliff,0,0);}
setInterval(()=>{if(document.getElementById('c_anim').checked)f=(f+1)%A.length;draw()},120);draw();});
</script></html>'''
    (ROOT/'apercu_arene_glace_calques_v2.html').write_text(html)


def pack_zip():
    z = OUT/'ice_arena_multicalques_v2.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        files = sorted(OUT.rglob('*.png')) + sorted(OUT.rglob('*.webp')) + sorted(OUT.rglob('*.gif')) + [OUT/'verification.json']
        for p in files:
            zf.write(p, p.relative_to(OUT.parent))


if __name__ == '__main__':
    main()
