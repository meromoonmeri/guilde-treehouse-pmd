"""Galerie autonome : fleurs 4x200ms, etoiles 64x80ms, wraps defilants en continu."""
from pathlib import Path
import json, base64
R = Path(__file__).resolve().parents[2]
O = R / 'renders/sommet_sky_nuit_v1'
P = O / 'sommet_nuit'

def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()

data = {
    'ciel': uri(P / 'sky_01_ciel.png'),
    'etoiles': [uri(P / 'etoiles' / f'{i:02}.png') for i in range(64)],
    'far': uri(P / 'sky_03_nuages_lointains_wrap.png'),
    'mont': uri(P / 'sky_04_montagnes.png'),
    'fore': uri(P / 'sky_06_foret.png'),
    'near': uri(P / 'sky_05_nuages_proches_wrap.png'),
    'mist': uri(P / 'sky_07_brume_wrap.png'),
    'pra': uri(P / 'sky_08_prairie.png'),
    'rel': uri(P / 'sky_09_reliefs.png'),
    'floin': [uri(P / f'sky_10_fleurs_loin_nuit_ph{i}.png') for i in range(4)],
    'fpro': [uri(P / f'sky_11_fleurs_proche_nuit_ph{i}.png') for i in range(4)],
    'labels': ['01_ciel', '02_etoiles', '03_nuages_lointains', '04_montagnes', '06_foret',
               '05_nuages_proches', '07_brume', '08_prairie', '09_reliefs', '10_fleurs_loin', '11_fleurs_proche'],
}
html = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Sommet Sky Peak de nuit — vista multicouche</title>
<style>
body{background:#0d1420;color:#dfe9dc;font-family:sans-serif;margin:0;padding:16px}
h1{font-size:20px;color:#e6d493;margin:0 0 4px}.sub{color:#9db3a1;font-size:13px;margin-bottom:12px}
#wrap{display:flex;gap:16px;flex-wrap:wrap}#panel{background:#16202e;padding:12px;border-radius:8px;min-width:260px}
#panel h3{margin:10px 0 6px;font-size:13px;color:#a3dae3}label{display:block;font-size:13px;margin:3px 0}
canvas{image-rendering:pixelated;background:#000;border:1px solid #33463c}
button{background:#2a3d33;color:#e6d493;border:1px solid #4a6156;border-radius:4px;padding:4px 10px;margin:2px;cursor:pointer}
button:hover{background:#3a5245}.note{font-size:12px;color:#9db3a1;max-width:660px}a{color:#a3dae3}
</style></head><body>
<h1>Sommet Sky Peak de nuit — vista 960×600</h1>
<div class="sub">Prairie/fleurs natives + nuit Abyss · etoiles 64×80ms · wraps seamless · vitesses PMDO : far −4, near −8, brume −3 px/s</div>
<div id="wrap"><div><canvas id="cv" width="960" height="600"></canvas></div>
<div id="panel"><h3>Calques</h3><div id="layers"></div>
<h3>Animation</h3><div><button id="play">Pause</button>
vitesse wraps <button data-s="1">1×</button><button data-s="8">8×</button><button data-s="60">60×</button></div>
<h3>Affichage</h3><label><input id="grid" type="checkbox"> grille 8px</label>
<div>Zoom <button data-z="1">1×</button><button data-z="2">2×</button></div>
<h3>Exports</h3><div><button id="exp">Telecharger la vue PNG</button></div><div id="dl"></div>
<p class="note">Fleurs 4×200ms, etoiles 64×80ms, nuages/brume en wrap continu sans coupure.
Vitesses reelles quasi-statiques : le selecteur accelere la demo (defaut 8×).
Fichiers natifs : renders/sommet_sky_nuit_v1/ (ORA 13 calques, phases wrap, ZIP).</p>
</div></div>
<script>
const D=__DATA__,cv=document.getElementById('cv'),cx=cv.getContext('2d');cx.imageSmoothingEnabled=false;
const I={};let nd=0;const keys=['ciel','far','mont','fore','near','mist','pra','rel'];
function mk(s,cb){const i=new Image();i.onload=()=>{cb(i);if(++nd===12+64+8)draw();};i.src=s;}
keys.forEach(k=>mk(D[k],i=>I[k]=i));I.etoiles=[];D.etoiles.forEach(s=>mk(s,i=>I.etoiles.push(i)));
I.floin=[];I.fpro=[];D.floin.forEach(s=>mk(s,i=>I.floin.push(i)));D.fpro.forEach(s=>mk(s,i=>I.fpro.push(i)));
const vis=new Array(11).fill(true);let playing=true,speed=8,t0=performance.now(),frozen=0,off={far:0,near:0,mist:0},last=performance.now();
const box=document.getElementById('layers');
D.labels.forEach((n,k)=>{const l=document.createElement('label'),c=document.createElement('input');
c.type='checkbox';c.checked=true;c.onchange=()=>vis[k]=c.checked;l.append(c,' '+n);box.append(l);});
[['01_ciel',()=>D.ciel],['04_montagnes',()=>D.mont],['06_foret',()=>D.fore],['08_prairie',()=>D.pra],['09_reliefs',()=>D.rel]].forEach(([n,f])=>{const a=document.createElement('a');a.textContent='↓ '+n;a.style.display='block';a.style.fontSize='12px';a.href=f();a.download=n+'.png';document.getElementById('dl').append(a);});
function frame(t){return{fph:Math.floor(t/200)%4,sph:Math.floor(t/80)%64};}
function wrap(img,x){cx.drawImage(img,x,0);cx.drawImage(img,x+960,0);}
function draw(){const now=performance.now();
 if(playing){const dt=(now-last)/1000;off.far=(off.far+dt*4*speed)%960;off.near=(off.near+dt*8*speed)%960;off.mist=(off.mist+dt*3*speed)%960;}
 last=now;const t=playing?now-t0:frozen,F=frame(t);cx.clearRect(0,0,960,600);
 if(vis[0])cx.drawImage(I.ciel,0,0);if(vis[1]&&I.etoiles[F.sph])cx.drawImage(I.etoiles[F.sph],0,0);
 if(vis[2])wrap(I.far,-off.far);if(vis[3])cx.drawImage(I.mont,0,0);if(vis[4])cx.drawImage(I.fore,0,0);
 if(vis[5])wrap(I.near,-off.near);if(vis[6])wrap(I.mist,-off.mist);
 if(vis[7])cx.drawImage(I.pra,0,0);if(vis[8])cx.drawImage(I.rel,0,0);
 if(vis[9]&&I.floin[F.fph])cx.drawImage(I.floin[F.fph],0,0);if(vis[10]&&I.fpro[F.fph])cx.drawImage(I.fpro[F.fph],0,0);
 if(document.getElementById('grid').checked){cx.strokeStyle='rgba(255,255,255,.16)';cx.lineWidth=1;cx.beginPath();
 for(let x=0;x<=960;x+=8){cx.moveTo(x+.5,0);cx.lineTo(x+.5,600);}for(let y=0;y<=600;y+=8){cx.moveTo(0,y+.5);cx.lineTo(960,y+.5);}cx.stroke();}}
setInterval(()=>{if(playing)draw();},50);
document.getElementById('play').onclick=e=>{playing=!playing;e.target.textContent=playing?'Pause':'Lecture';
 if(playing){t0=performance.now()-frozen;last=performance.now();}else frozen=performance.now()-t0;draw();};
document.querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>{speed=+b.dataset.s;});
document.getElementById('grid').onchange=draw;
document.querySelectorAll('[data-z]').forEach(b=>b.onclick=()=>{cv.style.width=(960*+b.dataset.z)+'px';cv.style.height=(600*+b.dataset.z)+'px';});
document.getElementById('exp').onclick=()=>{const g=document.getElementById('grid').checked;
 document.getElementById('grid').checked=false;draw();const a=document.createElement('a');
 a.download='sommet_sky_nuit_vue.png';a.href=cv.toDataURL('image/png');a.click();
 document.getElementById('grid').checked=g;draw();};
</script></body></html>"""
html = html.replace('__DATA__', json.dumps(data))
(R / 'apercu_sommet_sky_nuit_v1.html').write_text(html)
print('galerie OK')
