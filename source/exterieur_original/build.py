#!/usr/bin/env python3
"""Paysage PMD original : cinq sources IA indépendantes sur chroma #FF00FF."""
from __future__ import annotations
import base64, hashlib, io, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from animation import AnimatedLayer, compose, export_variant, save_png

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GEN, OUT, PREVIEW, README = HERE / "generation", ROOT / "exterieur_original", ROOT / "apercu_exterieur_original.html", HERE / "README.md"
SIZE, SOURCE_SIZE, MAGENTA = (688, 384), (1376, 768), np.array((255, 0, 255), np.uint8)
CLOUD_PERIOD, SEA_PERIOD, FRAMES, DURATION = 344, 24, math.lcm(344, 24), 250
LAYERS = (("00_ciel", "Ciel ouvert sans nuage", False, "00_ciel_genere.png"),
          ("01_nuages_wrap", "Nuages — wrap horizontal parfait", True, "02_nuages_genere.png"),
          ("02_mer_palette", "Mer — cycle de palette", True, "01_mer_generee.png"),
          ("03_plateaux_reliefs", "Plateaux et reliefs naturels", False, "03_plateaux_reliefs_generes.png"),
          ("04_falaise", "Falaise côtière naturelle", False, "04_falaise_generee.png"))


def load_generated(name: str) -> Image.Image:
    path = GEN / name
    assert path.is_file(), f"Source IA manquante : {path}"
    with Image.open(path) as raw: image = raw.convert("RGB")
    # Le générateur peut retourner 1 306×816 plutôt que le canvas demandé ;
    # ce rendu reste une source IA autonome. On le normalise ici en pixels
    # entiers, sans jamais emprunter une référence ou un template externe.
    assert image.size in {SOURCE_SIZE, (1306, 816)}, f"Dimension inattendue : {path} = {image.size}"
    return image.resize(SIZE, Image.Resampling.NEAREST)


def normalize_key(image: Image.Image) -> Image.Image:
    """Replace the IA's fuchsia fringe connected to the outer chroma field.

    The generated sprites sometimes use several purple shades along a requested
    fuchsia cut-out.  A border flood-fill removes only that *outside* fringe;
    internal violet flowers and rock shading do not become transparent.
    """
    a = np.asarray(image.convert("RGB")).copy()
    r, g, b = (a[:, :, i] for i in range(3))
    candidate = (r > 90) & (b > 90) & (g < np.minimum(r, b) * .75)
    h, w = candidate.shape
    outside = np.zeros_like(candidate, dtype=bool)
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h) or outside[y, x] or not candidate[y, x]:
            continue
        outside[y, x] = True
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    a[outside] = MAGENTA
    return Image.fromarray(a, "RGB")


def keyed_rgba(image: Image.Image) -> Image.Image:
    a = np.asarray(image.convert("RGB")).copy(); alpha = np.full(a.shape[:2], 255, np.uint8)
    key = np.all(a == MAGENTA, axis=2); a[key] = 0; alpha[key] = 0
    return Image.fromarray(np.dstack((a, alpha)), "RGBA")


def magenta_rgb(image: Image.Image) -> Image.Image:
    a = np.asarray(image.convert("RGBA")); rgb = a[:,:,:3].copy(); rgb[a[:,:,3] == 0] = MAGENTA
    return Image.fromarray(rgb, "RGB")


def periodic_clouds(image: Image.Image) -> Image.Image:
    """Une tuile IA de 344 px répétée deux fois, couture #FF00FF transparente."""
    a = np.asarray(image.convert("RGB")).copy(); start = (SIZE[0] - CLOUD_PERIOD) // 2
    tile = a[:, start:start + CLOUD_PERIOD].copy(); tile[:, :12] = MAGENTA; tile[:, -12:] = MAGENTA
    return Image.fromarray(np.concatenate((tile, tile), axis=1), "RGB")


def sea_frames(sea: Image.Image) -> tuple[list[Image.Image], dict]:
    base = np.asarray(sea).copy(); wet = base[:,:,3] > 0; frames = []
    for f in range(SEA_PERIOD):
        # Variation de palette uniquement : alpha et coordonnées ne bougent jamais.
        force = math.sin(math.pi * f / SEA_PERIOD); a = base.copy(); rgb = a[:,:,:3].astype(np.int16)
        rgb[:,:,0][wet] += round(5*force); rgb[:,:,1][wet] += round(15*force); rgb[:,:,2][wet] += round(8*force)
        a[:,:,:3] = np.clip(rgb, 0, 255).astype(np.uint8); frames.append(Image.fromarray(a, "RGBA"))
    assert np.array_equal(np.asarray(frames[0])[:,:,3], np.asarray(frames[12])[:,:,3])
    assert not np.array_equal(np.asarray(frames[0]), np.asarray(frames[12]))
    atlas = Image.new("RGBA", (SIZE[0]*6, SIZE[1]*4))
    for i, frame in enumerate(frames): atlas.alpha_composite(frame, ((i%6)*SIZE[0], (i//6)*SIZE[1]))
    return frames, {"kind":"frames", "period":SEA_PERIOD, "prefix":"mer_palette", "source_atlas":"animations/source_mer_palette.png", "source_frame_size":list(SIZE), "source_columns":6, "palette_only":True}


def uri(image: Image.Image) -> str:
    b=io.BytesIO(); image.save(b, format="WEBP", lossless=True, method=4)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()


def preview(layers: list[Image.Image], sea_atlas: Image.Image) -> str:
    data, atlas, names = json.dumps([uri(x) for x in layers]), json.dumps(uri(sea_atlas)), json.dumps([x[1] for x in LAYERS], ensure_ascii=False)
    return f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Falaise PMD — layers originaux</title><style>body{{margin:0;background:#101522;color:#f7efd7;font:16px system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:20px}}#stage{{padding:14px;background:#070b12;border:1px solid #5b6b80;border-radius:12px;overflow:auto}}canvas{{display:block;margin:auto;image-rendering:pixelated;max-width:none}}button,label{{margin:5px;padding:8px;border:1px solid #71829d;border-radius:7px;background:#263147;color:inherit}}button{{cursor:pointer}}label{{display:inline-flex;gap:6px}}small,p{{color:#cbd3da}}</style><main><h1>Falaise côtière PMD — layers IA sur fond magenta</h1><p>Les PNG sources ont un fond <b>#FF00FF</b>. L’aperçu le traite comme transparence. Grille <b>8 × 8 px</b> visible par défaut.</p><button id="pause">❚❚ Pause</button><button id="grid">Grille 8 px : visible</button><span id="time"></span><section id="stage"><canvas id="c" width="688" height="384"></canvas></section><div id="layers"></div><small>Nuages : translation horizontale 1 px/image, wrap bit-identique après 344 images. Mer : 24 états de palette, aucune translation de pixels.</small><script>'use strict';const S=[688,384],L={data},A={atlas},N={names},P=document.querySelector('#pause'),G=document.querySelector('#grid'),C=document.querySelector('#c'),X=C.getContext('2d'),cache={{}},O=document.createElement('canvas'),Q=O.getContext('2d');let on=N.map(()=>true),f=0,play=true,g=true,last=performance.now();function load(u){{if(cache[u])return Promise.resolve(cache[u]);return new Promise((y,n)=>{{let i=new Image();i.onload=()=>{{cache[u]=i;y(i)}};i.onerror=n;i.src=u}})}}function key(im,sx=0,sy=0){{O.width=S[0];O.height=S[1];Q.clearRect(0,0,...S);Q.drawImage(im,sx,sy,...S,0,0,...S);let d=Q.getImageData(0,0,...S);for(let i=0;i<d.data.length;i+=4)if(d.data[i]>240&&d.data[i+1]<24&&d.data[i+2]>240)d.data[i+3]=0;Q.putImageData(d,0,0);return O}}async function draw(){{await Promise.all(L.concat([A]).map(load));X.clearRect(0,0,...S);for(let i=0;i<L.length;i++)if(on[i]){{if(i===1){{let d=-(f%344);X.drawImage(key(cache[L[i]]),d,0);X.drawImage(key(cache[L[i]]),d+688,0)}}else if(i===2){{let k=f%24;X.drawImage(key(cache[A],(k%6)*688,Math.floor(k/6)*384),0,0)}}else X.drawImage(key(cache[L[i]]),0,0)}}if(g){{X.strokeStyle='rgba(255,230,140,.35)';X.beginPath();for(let x=0;x<=688;x+=8){{X.moveTo(x+.5,0);X.lineTo(x+.5,384)}}for(let y=0;y<=384;y+=8){{X.moveTo(0,y+.5);X.lineTo(688,y+.5)}}X.stroke()}}document.querySelector('#time').textContent='Image '+(f+1)+' / {FRAMES} · mer '+(f%24+1)+' / 24'}}function controls(){{let d=document.querySelector('#layers');d.replaceChildren();N.forEach((n,i)=>{{let l=document.createElement('label'),q=document.createElement('input');q.type='checkbox';q.checked=on[i];q.onchange=()=>{{on[i]=q.checked;draw()}};l.append(q,document.createTextNode(n));d.append(l)}});G.textContent=g?'Grille 8 px : visible':'Grille 8 px : masquée';}}P.onclick=()=>{{play=!play;P.textContent=play?'❚❚ Pause':'▶ Animer';last=performance.now()}};G.onclick=()=>{{g=!g;controls();draw()}};function tick(t){{if(play&&t-last>=250){{f=(f+Math.floor((t-last)/250))%{FRAMES};last=t;draw()}}requestAnimationFrame(tick)}}controls();draw();requestAnimationFrame(tick);</script></main>'''


def build() -> None:
    if OUT.exists(): shutil.rmtree(OUT)
    keyed = []
    for id, _label, _moving, filename in LAYERS:
        image = load_generated(filename)
        image = image if id == "00_ciel" else normalize_key(image)
        keyed.append(periodic_clouds(image) if id == "01_nuages_wrap" else image)
    rgba = [x.convert("RGBA") if i == 0 else keyed_rgba(x) for i,x in enumerate(keyed)]
    frames, sea_spec = sea_frames(rgba[2]); source_atlas = Image.new("RGBA", (SIZE[0]*6, SIZE[1]*4))
    for i, frame in enumerate(frames): source_atlas.alpha_composite(frame, ((i%6)*SIZE[0], (i//6)*SIZE[1]))
    save_png(source_atlas, OUT / "animations/source_mer_palette.png")
    defs=[{"id":x[0],"nom":x[1],"anime":x[2]} for x in LAYERS]
    specs={"01_nuages_wrap":{"kind":"scroll","period":CLOUD_PERIOD,"prefix":"nuages_wrap","vitesse_px_par_image":-1,"wrap_horizontal_parfait":True},"02_mer_palette":sea_spec}
    files=export_variant(OUT, "original", defs, rgba, specs, SIZE, FRAMES, 3, [], "falaise_originale")
    for definition, image in zip(defs,keyed):
        path=OUT/"calques_magentas/original"/(definition["id"]+".png"); path.parent.mkdir(parents=True,exist_ok=True); image.save(path, optimize=True)
    cycle=[]
    for i, frame in enumerate(frames):
        path=OUT/f"cycles_magentas/mer_palette/mer_palette_{i:02d}.png"; path.parent.mkdir(parents=True,exist_ok=True); magenta_rgb(frame).save(path, optimize=True); cycle.append(str(path.relative_to(OUT)))
    composition=compose([AnimatedLayer(x,specs.get(d["id"]),OUT) for d,x in zip(defs,rgba)],SIZE,0)
    manifest={"id":"falaise_originale","dimensions":list(SIZE),"grille_px":8,"fond_chroma_key":"#FF00FF","creation":"Cinq layers IA séparés; falaise et mer générées avec le placement/trait PMD demandé.","animation":{"frames":FRAMES,"duree_image_ms":DURATION,"nuages_wrap_px":CLOUD_PERIOD,"mer_palette_frames":SEA_PERIOD},"calques":defs,"fichiers":{"original":{**files,"calques_magentas":{d["id"]: f"calques_magentas/original/{d['id']}.png" for d in defs},"cycle_mer_magentas":cycle}},"sources":{d[3]: hashlib.sha256((GEN/d[3]).read_bytes()).hexdigest() for d in LAYERS}}
    (OUT/"kit.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    assert README.is_file(), f"Documentation manquante : {README}"
    shutil.copy2(README, OUT / "README.md")
    PREVIEW.write_text(preview(keyed,source_atlas))
    print(f"OK : {len(defs)} layers IA, fond magenta, {FRAMES} frames, grille 8 px.")
if __name__=="__main__": build()
