"""Galerie autonome : 8 calques decomposes de FINALE_map.png, jour/nuit Abyss."""
from pathlib import Path
import base64
import json

R = Path(__file__).resolve().parents[2]
OUT = R / 'renders/entree_crooked_finale'
PFX = 'EntreeCrookedFinale'


def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()


def main():
    man = json.loads((OUT / 'manifest.json').read_text())
    layers = [dict(id=n, jour=uri(OUT / f'{PFX}_{n}_jour.png'),
                   nuit=uri(OUT / f'{PFX}_{n}_nuit.png')) for n in man['ordre']]
    data = dict(size=man['canevas'], layers=layers)
    html = """<!doctype html><html lang="fr"><meta charset="utf-8">""" \
        """<title>Entree Crooked — map FINALE decomposee</title><style>""" \
        """body{background:#1c1a14;color:#e8e2d2;font:16px system-ui;max-width:1000px;""" \
        """margin:28px auto;padding:20px}p{line-height:1.6;color:#cfc8b2}""" \
        """canvas{image-rendering:pixelated;max-width:100%;background:#333}""" \
        """label{display:inline-block;margin:6px;font-size:13px}""" \
        """button{margin:6px;padding:6px 14px;border-radius:8px;border:1px solid #6a6250;""" \
        """background:#3a3428;color:#e8e2d2;cursor:pointer}</style>""" \
        """<h1>Entree Crooked — map FINALE (decomposition)</h1>""" \
        """<p>Map finale generee d'un bloc (guide V1 + refs canoniques Halcyon/EoSO/DumpAsset), """ \
        """puis <b>decomposee en 8 calques</b> (partition exacte, composite == brut). """ \
        """65 fleurs, 4 arbres, 6 rochers. Nuit Abyss exacte.</p>""" \
        """<div><button id="mode">Passer en nuit</button></div>""" \
        """<div id="ctl"></div><canvas id="cv"></canvas>""" \
        """<script>const D=""" + json.dumps(data, ensure_ascii=False) + """;""" \
        """const cv=document.getElementById('cv');cv.width=D.size[0];cv.height=D.size[1];""" \
        """const ctx=cv.getContext('2d');let mode='jour';""" \
        """const cache={},checks=[];""" \
        """function img(u){if(!cache[u]){const i=new Image();i.onload=draw;i.src=u;cache[u]=i}""" \
        """return cache[u]}""" \
        """function draw(){ctx.clearRect(0,0,cv.width,cv.height);D.layers.forEach((l,i)=>{""" \
        """if(!checks[i].checked)return;""" \
        """const im=img(l[mode]);if(im.complete&&im.width)ctx.drawImage(im,0,0)})}""" \
        """D.layers.forEach(l=>{const lb=document.createElement('label'),c=""" \
        """document.createElement('input');c.type='checkbox';c.checked=true;""" \
        """c.onchange=draw;checks.push(c);""" \
        """lb.append(c,document.createTextNode(l.id));""" \
        """document.getElementById('ctl').append(lb)});""" \
        """document.getElementById('mode').onclick=e=>{mode=mode==='jour'?'nuit':'jour';""" \
        """e.target.textContent=mode==='jour'?'Passer en nuit':'Passer en jour';draw()};</script>"""
    out = R / 'apercu_entree_crooked_finale.html'
    out.write_text(html)
    print('galerie:', out, f'{out.stat().st_size / 1024:.0f} Ko')


if __name__ == '__main__':
    main()
