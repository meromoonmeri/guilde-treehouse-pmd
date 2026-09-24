"""Galerie autonome: calques, 4 phases eau native, grille 8px, zoom, export PNG."""
from pathlib import Path
import json, base64
R = Path(__file__).resolve().parents[2]
O = R / 'renders/falaise_mer_canonique_v1'
P = O / 'cap_cascade'

def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()

static_names = ['cap_01_sol_herbe.png', 'cap_02_parois.png', 'cap_03_couronnes_pieds.png', 'cap_04_berges.png']
data = {'static': [uri(P / n) for n in static_names],
        'river': [uri(P / f'cap_05_riviere_phase_{f+1}.png') for f in range(4)],
        'fall': [uri(P / f'cap_06_cascade_phase_{f+1}.png') for f in range(4)],
        'labels': ['01_sol_herbe', '02_parois', '03_couronnes_pieds', '04_berges', '05_riviere', '06_cascade'],
        'files': static_names + [f'cap_05_riviere_phase_{f+1}.png' for f in range(4)] + [f'cap_06_cascade_phase_{f+1}.png' for f in range(4)]}

html = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Cap canonique face mer v1 — falaise Metano stricte, eau native</title>
<style>
body{background:#101a15;color:#dfe9dc;font-family:sans-serif;margin:0;padding:16px}
h1{font-size:20px;color:#e6d493;margin:0 0 4px} .sub{color:#9db3a1;font-size:13px;margin-bottom:12px}
#wrap{display:flex;gap:16px;flex-wrap:wrap} #panel{background:#182420;padding:12px;border-radius:8px;min-width:250px}
#panel h3{margin:10px 0 6px;font-size:13px;color:#a3dae3} label{display:block;font-size:13px;margin:3px 0}
canvas{image-rendering:pixelated;background:#000;border:1px solid #33463c}
button{background:#2a3d33;color:#e6d493;border:1px solid #4a6156;border-radius:4px;padding:4px 10px;margin:2px;cursor:pointer}
button:hover{background:#3a5245} input[type=range]{width:100%}
.note{font-size:12px;color:#9db3a1;max-width:640px} a{color:#a3dae3}
</style></head><body>
<h1>Cap canonique face mer v1</h1>
<div class="sub">1024×512 natif · grille 8px · tuiles Halcyon non modifiees · eau native 4 phases @167ms · jour</div>
<div id="wrap"><div><canvas id="cv" width="1024" height="512"></canvas></div>
<div id="panel">
<h3>Calques</h3><div id="layers"></div>
<h3>Phase eau (0–3)</h3>
<input id="phase" type="range" min="0" max="3" step="1" value="0">
<div><button id="play">Lecture</button><button id="sec">Sec seul</button><button id="wet">Tout</button></div>
<h3>Affichage</h3>
<label><input id="grid" type="checkbox"> grille 8px</label>
<div>Zoom <button data-z="1">1×</button><button data-z="2">2×</button><button data-z="3">3×</button></div>
<h3>Exports</h3>
<div><button id="exp">Telecharger la vue PNG</button></div>
<div id="dl"></div>
<p class="note">Recomposition exacte des 6 calques (phase 0 pour l'eau arretee).
Les PNG telecharges sont les calques natifs sans grille.
Voir <b>renders/falaise_mer_canonique_v1/</b> : ORA, WebP anime, manifeste, ZIP.</p>
</div></div>
<script>
const D=__DATA__;
const cv=document.getElementById('cv'),cx=cv.getContext('2d');cx.imageSmoothingEnabled=false;
const imgs={};let loaded=0;const total=12;
function mk(src,cb){const i=new Image();i.onload=()=>{cb(i);if(++loaded===total)draw();};i.src=src;}
const L={s:[],r:[],f:[]};
D.static.forEach((s,k)=>mk(s,i=>L.s[k]=i));D.river.forEach((s,k)=>mk(s,i=>L.r[k]=i));D.fall.forEach((s,k)=>mk(s,i=>L.f[k]=i));
const vis=[true,true,true,true,true,true];let phase=0,playing=false,timer=null,zoom=1;
const box=document.getElementById('layers');
D.labels.forEach((n,k)=>{const l=document.createElement('label');const c=document.createElement('input');
c.type='checkbox';c.checked=true;c.onchange=()=>{vis[k]=c.checked;draw();};l.append(c,' '+n);box.append(l);});
const dl=document.getElementById('dl');
D.labels.forEach((n,k)=>{const a=document.createElement('a');a.textContent='↓ '+n;a.style.display='block';a.style.fontSize='12px';
a.href=k<4?D.static[k]:(k===4?D.river[0]:D.fall[0]);a.download=n+'_phase0.png';dl.append(a);});
function draw(){cx.clearRect(0,0,1024,512);
 if(vis[0])cx.drawImage(L.s[0],0,0);if(vis[1])cx.drawImage(L.s[1],0,0);if(vis[2])cx.drawImage(L.s[2],0,0);
 if(vis[3])cx.drawImage(L.s[3],0,0);if(vis[4])cx.drawImage(L.r[phase],0,0);if(vis[5])cx.drawImage(L.f[phase],0,0);
 if(document.getElementById('grid').checked){cx.strokeStyle='rgba(255,255,255,.18)';cx.lineWidth=1;cx.beginPath();
  for(let x=0;x<=1024;x+=8){cx.moveTo(x+.5,0);cx.lineTo(x+.5,512);}for(let y=0;y<=512;y+=8){cx.moveTo(0,y+.5);cx.lineTo(1024,y+.5);}cx.stroke();}
 cv.style.width=(1024*zoom)+'px';cv.style.height=(512*zoom)+'px';}
document.getElementById('phase').oninput=e=>{phase=+e.target.value;draw();};
document.getElementById('grid').onchange=draw;
document.querySelectorAll('[data-z]').forEach(b=>b.onclick=()=>{zoom=+b.dataset.z;draw();});
document.getElementById('sec').onclick=()=>{vis[3]=vis[4]=vis[5]=false;sync();};
document.getElementById('wet').onclick=()=>{for(let k=0;k<6;k++)vis[k]=true;sync();};
function sync(){[...box.querySelectorAll('input')].forEach((c,k)=>c.checked=vis[k]);draw();}
document.getElementById('play').onclick=e=>{playing=!playing;e.target.textContent=playing?'Pause':'Lecture';
 if(playing){timer=setInterval(()=>{phase=(phase+1)%4;document.getElementById('phase').value=phase;draw();},167);}else clearInterval(timer);};
document.getElementById('exp').onclick=()=>{const g=document.getElementById('grid').checked;
 document.getElementById('grid').checked=false;draw();const a=document.createElement('a');
 a.download='cap_cascade_vue.png';a.href=cv.toDataURL('image/png');a.click();
 document.getElementById('grid').checked=g;draw();};
</script></body></html>"""
html = html.replace('__DATA__', json.dumps(data))
(R / 'apercu_falaise_mer_canonique_v1.html').write_text(html)
print('galerie:', R / 'apercu_falaise_mer_canonique_v1.html')
