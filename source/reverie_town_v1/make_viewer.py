#!/usr/bin/env python3
"""Génère exports/reverie_town_v1/index.html : aperçu des deux cartes (jour/nuit, phases animées, calques)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/reverie_town_v1'
maps = {}
for slug in ('NE', 'NO'):
    prov = json.loads((OUT / f'RVT_{slug}/RVT_{slug}_provenance.json').read_text())
    maps[slug] = {'layers': prov['layers'], 'files': prov['files'], 'size': prov['size_tiles']}
html = r"""<!doctype html><html lang=fr><meta charset=utf-8><title>Reverie Town v1 - aperçu</title>
<style>body{font-family:sans-serif;background:#222;color:#eee;margin:12px}canvas{image-rendering:pixelated;border:1px solid #555;max-width:100%}
label{margin-right:10px}.bar{margin:8px 0}</style>
<h1>Reverie Town v1 — tuiles natives Métano (kit falaises)</h1>
<div class=bar>Carte <select id=map><option value=NE>Nord-Est (RVT_NE)</option><option value=NO>Nord-Ouest (RVT_NO)</option></select>
<select id=mode><option value=jour>jour</option><option value=nuit>nuit</option></select>
<label><input type=checkbox id=anim checked> animation (4 phases, 10 ticks)</label>
<label><input type=range id=zoom min=1 max=3 value=1> zoom</label> <span id=layers></span></div>
<canvas id=c></canvas>
<p>Calques PNG 8 px : <code>RVT_&lt;carte&gt;_NN_&lt;calque&gt;[_pN]_&lt;jour|nuit&gt;.png</code> — import « PNG to Tileset » dans PMDO Dev.
Paquet natif : <code>paquet_natif/Data/Ground/*.rsground</code> + <code>Content/Tile/*.tile</code> (voir README).</p>
<script>
const MAPS=__MAPS__;const c=document.getElementById('c'),ctx=c.getContext('2d');let imgs={},phase=0;
function key(m,l,p,mode){const f=MAPS[m].files[l];const re=new RegExp('_p'+(p+1)+'_'+mode+'[.]png$');
 return f.find(x=>re.test(x))||f.find(x=>x.endsWith('_'+mode+'.png'));}
function load(src){if(imgs[src])return imgs[src];const i=new Image();i.src=src;imgs[src]=i;return i;}
function draw(){const m=document.getElementById('map').value,mode=document.getElementById('mode').value,z=+document.getElementById('zoom').value;
 const [w,h]=MAPS[m].size;c.width=w*8;c.height=h*8;c.style.width=(w*8*z)+'px';ctx.fillStyle='#000';ctx.fillRect(0,0,c.width,c.height);
 for(const l of MAPS[m].layers){const cb=document.getElementById('l_'+l);if(cb&&!cb.checked)continue;
  const im=load('RVT_'+m+'/'+key(m,l,phase,mode));if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0);else im.onload=draw;}}
function ui(){const m=document.getElementById('map').value;document.getElementById('layers').innerHTML=MAPS[m].layers.map(l=>'<label><input type=checkbox checked id="l_'+l+'" onchange="draw()"> '+l+'</label>').join('');draw();}
document.getElementById('map').onchange=ui;document.getElementById('mode').onchange=draw;document.getElementById('zoom').oninput=draw;
setInterval(()=>{if(document.getElementById('anim').checked){phase=(phase+1)%4;draw();}},1000/6*10);ui();
</script>"""
(OUT / 'index.html').write_text(html.replace('__MAPS__', json.dumps(maps)), encoding='utf-8')
print('viewer ->', OUT / 'index.html')
