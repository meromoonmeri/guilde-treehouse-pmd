"""Construit `apercu_beach_pmdsky_v1.html` depuis renders/beach_pmdsky_v1/.

Usage : python source/build_beach_pmdsky_preview.py
"""
from pathlib import Path
import json, base64

R = Path(__file__).resolve().parents[1]
D = R / 'renders/beach_pmdsky_v1'
M = json.loads((D / 'manifest.json').read_text())

for l in M['layouts']:
    p = D / l['fichier']
    assert p.exists(), f'{p} manquant'
    l['data'] = 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()

HTML = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plage PMD Sky — six propositions de layout</title>
<style>
:root{color-scheme:dark;--gold:#e1ce8e;--muted:#aebfa6;--line:#49593f}
*{box-sizing:border-box}body{margin:0;background:#18251e;color:#efe9d4;font:14px/1.5 system-ui}
main{max-width:1450px;margin:auto;padding:28px 22px}
.eyebrow{color:var(--gold);font-size:11px;letter-spacing:3px}
h1{font-size:31px;line-height:1.2;margin:12px 0}p{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:22px;margin-top:24px}
figure{margin:0;background:#111b16;border:1px solid var(--line);border-radius:10px;overflow:hidden;cursor:zoom-in}
figure img{display:block;width:100%;image-rendering:pixelated;background:#0a0f0c}
figcaption{padding:12px 14px}
figcaption b{color:var(--gold);font-size:16px}
figcaption .num{color:var(--muted);margin-right:8px}
figcaption p{margin:6px 0 0;font-size:13px}
.note{padding:14px 18px;background:#293926;border-left:3px solid var(--gold);margin:20px 0}
#lb{position:fixed;inset:0;background:rgba(5,8,6,.9);display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px;padding:20px}
#lb.on{display:flex}
#lb img{max-width:96vw;max-height:86vh;image-rendering:pixelated;border:1px solid var(--line)}
#lb .cap{color:var(--gold)}
#lb .close{position:absolute;top:14px;right:18px;background:#2e402a;border:1px solid var(--line);color:#efe9d4;padding:8px 14px;border-radius:6px;cursor:pointer}
</style></head><body><main>
<div class="eyebrow">PLAGE / PMD SKY · PROPOSITIONS DE LAYOUT</div>
<h1>Six compositions de plage dans la DA d'Explorers of Sky</h1>
<p>Falaises rouges à touffes vertes, sable crème ondulé, eau turquoise ourlée d'écume, palmiers.<br>Cliquer une carte pour l'inspecter en grand.</p>
<div class="note"><b>Statut :</b> propositions générées dans la DA PMD Sky, ancrées sur les références de plage du jeu (<code>arenapmdskybeach.png</code>, planche TSR « Beach &amp; Path to Beach »). Ce ne sont pas des tilesets natifs certifiés : après choix d'un layout, la reconstruction en tuiles 8 px et calques (méthode Spriter Pro / PMDO) reste à faire si la carte doit entrer dans le moteur.</div>
<div class="grid" id="grid"></div>
</main>
<div id="lb"><button class="close" onclick="closeLb()">Fermer ✕</button><img alt=""><div class="cap"></div></div>
<script>
const DATA=__DATA__;
const grid=document.getElementById('grid');
DATA.layouts.forEach((l,i)=>{
  const f=document.createElement('figure');
  f.innerHTML=`<img alt="${l.nom}"><figcaption><span class="num">0${i+1}</span><b>${l.nom}</b><p>${l.description}</p></figcaption>`;
  f.querySelector('img').src=l.data;
  f.onclick=()=>{const lb=document.getElementById('lb');lb.classList.add('on');lb.querySelector('img').src=l.data;lb.querySelector('.cap').textContent=`0${i+1} · ${l.nom}`;};
  grid.append(f);
});
function closeLb(){document.getElementById('lb').classList.remove('on')}
document.getElementById('lb').addEventListener('click',e=>{if(e.target.id==='lb')closeLb()});
addEventListener('keydown',e=>{if(e.key==='Escape')closeLb()});
</script></body></html>"""

(R / 'apercu_beach_pmdsky_v1.html').write_text(HTML.replace('__DATA__', json.dumps(M, ensure_ascii=False)))
print('apercu_beach_pmdsky_v1.html écrit :', len(M['layouts']), 'propositions')
