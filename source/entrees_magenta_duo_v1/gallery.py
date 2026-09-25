import json, base64
from pathlib import Path
R=Path(__file__).resolve().parents[2]
OUT=R/'renders'/'entrees_magenta_duo_v1'
CFG=json.loads((Path(__file__).parent/'references'/'config.json').read_text())
MAN=json.loads((OUT/'manifest.json').read_text())

def uri(p):
    import base64
    return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()

html=['<!doctype html><html lang="fr"><meta charset="utf-8"><title>Entrées duo — magenta multicouche</title>']
html.append('<style>body{background:#0f1411;color:#dbe6d3;font:15px system-ui;max-width:1280px;margin:24px auto;padding:16px}h1{font-size:26px}h2{font-size:19px;margin:14px 0 6px}article{background:#1a2220;border:1px solid #2d3a2f;border-radius:12px;padding:16px;margin:18px 0}canvas{image-rendering:pixelated;border:1px solid #2d3a2f;background:#242e2a}img{image-rendering:pixelated;max-width:100%}small{color:#9ab0a0}label{font-size:13px;margin:4px 8px;display:inline-block}details{margin:10px 0}</style>')
html.append('<h1>Entrées donjon — fond duo canonique, layout légèrement modifié</h1>')
html.append('<p>Pipeline : <b>magenta #FF00FF → key(alpha) → duo fonds + multicouche → animation selon composition</b>. 3 entrées ×2 palettes =6 scènes. Grille 8 px, TSX, ORA, WebP. Sources canoniques affichées à l’échelle, hashes conservés. Aucune texture jour recolorée arbitrairement ; palettes cohérentes par biome. Animation : forêt statique, volcan 6×120 ms, vapeur 8×130 ms. PMDO non testé.</p>')
for conf in CFG:
    html.append(f"<section><h2>Source canonique — {conf['title']} ({conf['size'][0]}×{conf['size'][1]})</h2><small>{conf['source']} — duo : {conf['duo']} — {conf['layout_note']}</small>")
    # embed source thumbnail (optional)
    try:
        sp=R/conf['source']
        if sp.exists():
            html.append(f"<div><img src='{uri(sp)}' style='max-width:600px;border:1px solid #333'></div>")
    except: pass
    html.append("</section>")

html.append('<hr><h2>Scènes générées (2 palettes / entrée)</h2>')
for scene in MAN['scenes']:
    zdir=OUT/'zones'/scene['id']
    # collect layers
    layers=[{"name": lf['name'], "uri": uri(zdir/lf['file'])} for lf in scene['layers']]
    comp_uri=uri(zdir/'COMPOSITION.png')
    anim_uri=None
    if scene['animation'] and scene['animation']['files']:
        # embed first anim frame as preview
        anim_uri=uri(zdir/scene['animation']['files'][0])
        # also embed all frames as data for JS cycling
        frames=[uri(zdir/f) for f in scene['animation']['files']]
    else:
        frames=[]
    # masque preview
    html.append(f"<article id='{scene['id']}'><h2>{scene['title']} — <small>{scene['id']} · {scene['size'][0]}×{scene['size'][1]} · duo {scene['duo']}</small></h2>")
    html.append(f"<p><small>Source {scene['source']} — {scene['layout_note']}</small></p>")
    html.append(f"<canvas id='c_{scene['id']}' width='{scene['size'][0]}' height='{scene['size'][1]}'></canvas><br>")
    html.append(f"<div id='ctrl_{scene['id']}'></div>")
    html.append(f"<details><summary>Composition</summary><img src='{comp_uri}'></details>")
    if frames:
        html.append(f"<details><summary>Animation {len(frames)} frames — {scene['animation']['cycle_ms']} ms</summary>")
        for f in frames:
            html.append(f"<img src='{f}' style='width:160px;margin:4px;border:1px solid #333'>")
        html.append("</details>")
    # JS per scene
    html.append(f"""<script>
    (function(){{
        const layers={json.dumps(layers, ensure_ascii=False)};
        const canvas=document.getElementById('c_{scene['id']}');
        const ctx=canvas.getContext('2d');
        const ctrl=document.getElementById('ctrl_{scene['id']}');
        const imgs=[];
        layers.forEach((l,i)=>{{
            const label=document.createElement('label');
            const cb=document.createElement('input'); cb.type='checkbox'; cb.checked=true;
            label.append(cb, document.createTextNode(' '+l.name));
            ctrl.append(label);
            const im=new Image(); im.src=l.uri; imgs.push({{im, cb}});
            cb.onchange=draw; im.onload=draw;
        }});
        function draw(){{
            ctx.clearRect(0,0,canvas.width,canvas.height);
            imgs.forEach(o=>{{ if(o.cb.checked && o.im.complete) ctx.drawImage(o.im,0,0); }});
        }}
    }})();</script>""")
    html.append("</article>")

html.append('<hr><p><small>Grille 8 px, TSX 8×8, ORA éditables, manifest.json, verification.json. Pack PMDO à venir : TexSize 1, projet 6 Ground. Reproduction : python3 source/entrees_magenta_duo_v1/build.py && verify.py && gallery.py</small></p></html>')
(R/'apercu_entrees_magenta_duo_v1.html').write_text(''.join(html), encoding='utf-8')
print("gallery -> apercu_entrees_magenta_duo_v1.html")
