"""Galerie autonome : calques, jour/nuit, fleurs animees 4x200ms."""
from pathlib import Path
import base64
import json

R = Path(__file__).resolve().parents[2]
OUT = R / 'renders/entree_crooked_v1'
PFX = 'EntreeCrookedV1'


def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()


def main():
    man = json.loads((OUT / 'manifest.json').read_text())
    layers = []
    for n in man['ordre']:
        e = dict(id=n, jour=uri(OUT / f'{PFX}_{n}_jour.png'), nuit=uri(OUT / f'{PFX}_{n}_nuit.png'))
        if n == '06_fleurs':
            e['phases_jour'] = [e['jour']] + [uri(OUT / f'{PFX}_{n}_phase{p}_jour.png') for p in (1, 2, 3)]
            e['phases_nuit'] = [e['nuit']] + [uri(OUT / f'{PFX}_{n}_phase{p}_nuit.png') for p in (1, 2, 3)]
        layers.append(e)
    data = dict(size=man['canevas'], ordre=man['ordre'], couches=man['couches'], layers=layers)
    html = """<!doctype html><html lang="fr"><meta charset="utf-8">""" \
        """<title>Entree grotte Crooked/Halcyon/Sky Peak v1</title><style>""" \
        """body{background:#1c1a14;color:#e8e2d2;font:16px system-ui;max-width:1000px;""" \
        """margin:28px auto;padding:20px}p{line-height:1.6;color:#cfc8b2}""" \
        """canvas{image-rendering:pixelated;max-width:100%;background:#333}""" \
        """label{display:inline-block;margin:6px;font-size:13px}""" \
        """button{margin:6px;padding:6px 14px;border-radius:8px;border:1px solid #6a6250;""" \
        """background:#3a3428;color:#e8e2d2;cursor:pointer}small{color:#edcf83}</style>""" \
        """<h1>Entree grotte — Crooked x Halcyon x Sky Peak</h1>""" \
        """<p>Paroi/bouche/chemin <b>generes</b> (brut G1b, style Crooked) ; herbe Sky Peak, """ \
        """rochers Crooked, arbres Halcyon et fleurs Sky Peak <b>natifs</b> (translation seule). """ \
        """Fleurs : 4 phases natives a 200 ms. Nuit Abyss exacte.</p>""" \
        """<div><button id="mode">Passer en nuit</button>""" \
        """<button id="play">Pause fleurs</button>""" \
        """<span id="lbl"><small>phase 1/4 · 200 ms</small></span></div>""" \
        """<div id="ctl"></div><canvas id="cv"></canvas>""" \
        """<script>const D=""" + json.dumps(data, ensure_ascii=False) + """;""" \
        """const cv=document.getElementById('cv');cv.width=D.size[0];cv.height=D.size[1];""" \
        """const ctx=cv.getContext('2d');let mode='jour',ph=0,playing=true;""" \
        """const cache={},checks=[];""" \
        """function img(u){if(!cache[u]){const i=new Image();i.onload=draw;i.src=u;cache[u]=i}""" \
        """return cache[u]}""" \
        """function draw(){ctx.clearRect(0,0,cv.width,cv.height);D.layers.forEach((l,i)=>{""" \
        """if(!checks[i].checked)return;let u=l[mode];""" \
        """if(l.id==='06_fleurs')u=l['phases_'+mode][ph];""" \
        """const im=img(u);if(im.complete&&im.width)ctx.drawImage(im,0,0)})}""" \
        """D.layers.forEach(l=>{const lb=document.createElement('label'),c=""" \
        """document.createElement('input');c.type='checkbox';c.checked=true;""" \
        """c.onchange=draw;checks.push(c);""" \
        """lb.append(c,document.createTextNode(l.id+' '+(D.couches[l.id][0]==='G'?'(gen)':'(natif)')));""" \
        """document.getElementById('ctl').append(lb)});""" \
        """document.getElementById('mode').onclick=e=>{mode=mode==='jour'?'nuit':'jour';""" \
        """e.target.textContent=mode==='jour'?'Passer en nuit':'Passer en jour';draw()};""" \
        """document.getElementById('play').onclick=e=>{playing=!playing;""" \
        """e.target.textContent=playing?'Pause fleurs':'Reprendre fleurs'};""" \
        """setInterval(()=>{if(!playing)return;ph=(ph+1)%4;""" \
        """document.getElementById('lbl').innerHTML='<small>phase '+(ph+1)+'/4 · 200 ms</small>';""" \
        """draw()},200);draw()</script></html>"""
    (R / 'apercu_entree_crooked_v1.html').write_text(html)
    print('galerie écrite', len(html) // 1024, 'Ko')


if __name__ == '__main__':
    main()
