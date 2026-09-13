from pathlib import Path
import json,io,base64
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/caps_terrasses_v4';SIZE=(820,328);SHARED=ROOT/'renders/caps_terrasses_v3'
BASE='https://github.com/meromoonmeri/guilde-treehouse-pmd/blob/arena/01a095e8-guilde-treehouse-pmd/renders/caps_terrasses_v4/'
def uri(im,format='WEBP'):
 b=io.BytesIO();im.save(b,format=format,**({'lossless':True,'exact':True} if format=='WEBP' else {}));return 'data:image/'+format.lower()+';base64,'+base64.b64encode(b.getvalue()).decode()
def view(p):
 im=Image.open(p).convert('RGBA')
 if '_terrain' in p.name:
  im.thumbnail(SIZE,Image.Resampling.NEAREST);canvas=Image.new('RGBA',SIZE);right=int(p.name[:2]) in [8,9,12,14,16];canvas.paste(im,(SIZE[0]-im.width if right else 0,SIZE[1]-im.height));return uri(canvas)
 return uri(im.resize(SIZE,Image.Resampling.NEAREST))
m=json.loads((OUT/'manifest.json').read_text());zones=[]
for z in m['zones']:
 zones.append({'title':z['title'],'status':z['visual_status'],'note':z['visual_note'],'day':view(OUT/z['terrain']),'night':view(OUT/z['night']),'link':BASE+z['terrain'],'nightLink':BASE+z['night'],'sceneLink':BASE+z['scene'],'sceneNightLink':BASE+z['scene'],'size':z['size']})
sea=Image.open(SHARED/'ocean/jour_00.png') # actual palette indices, never RGB luminance
import numpy as np
indices=Image.fromarray(np.array(sea)).resize(SIZE,Image.Resampling.NEAREST)
alpha=list(sea.info['transparency']);active=int(np.array(sea).max())+1
pal={mode:[Image.open(SHARED/'ocean'/f'{mode}_{i:02d}.png').getpalette()[:active*3] for i in range(64)] for mode in ['jour','nuit']}
data={'zones':zones,'indices':uri(indices,'PNG'),'alpha':alpha,'palettes':pal,'sky':{'jour':view(SHARED/'fonds/ciel.png'),'nuit':view(SHARED/'fonds/ciel_nuit.png')},'clouds':{'jour':view(SHARED/'fonds/nuages.png'),'nuit':view(SHARED/'fonds/nuages_nuit.png')}}
page='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Caps et terrasses · face à la mer</title><style>
*{box-sizing:border-box}body{margin:0;background:#102530;color:#ecf0de;font:16px/1.5 system-ui}header,main,footer{padding:24px 4%}header{border-bottom:1px solid #385462}h1{font-size:30px;margin:5px 0}small{color:#b8cccb}p{max-width:1100px}a{color:#c4e7aa}select,button{font:inherit;background:#294854;color:#edf1df;padding:9px 14px;border:1px solid #54747e;border-radius:5px;cursor:pointer}.controls{display:flex;flex-wrap:wrap;gap:18px;align-items:center;margin:16px 0}canvas{display:block;width:100%;image-rendering:pixelated;background:repeating-conic-gradient(#27404a 0% 25%,#38525a 0% 50%) 0/24px 24px;border:1px solid #506971}.pill{background:#254634;border-radius:5px;padding:10px 15px}.note{color:#c1cdcb}label{cursor:pointer}@media(max-width:650px){h1{font-size:23px}.controls{gap:12px}}
</style><header><small>ROCHE & HERBE MÉTANO · PRÉSENTATION CAP V2 / TERRASSE V2</small><h1>Dix propositions auditées · huit retenues, deux à reprendre</h1><p>Nouvelles générations avec références Métano renforcées, puis correction vers 328 couleurs natives vérifiées. Huit dessins retenus après inspection ; 07 et 11 restent à régénérer. Une palette correcte ne prouve pas un dessin canonique.</p></header><main><p class="pill" id="audit-status"></p><div class="controls"><select id="zone" aria-label="Falaise"></select><label><input id="night" type="checkbox"> Nuit Abyss</label><button id="play">Pause</button></div><canvas id="view" width="820" height="328" aria-label="Aperçu des calques de falaise et océan"></canvas><div class="controls"><label><input id="terrain" type="checkbox" checked> Falaise</label><label><input id="sea" type="checkbox" checked> Océan</label><label><input id="sky" type="checkbox" checked> Ciel</label><label><input id="cloud" type="checkbox" checked> Nuages fixes</label></div><div class="controls"><label>Cycle <select id="cycle"><option value="smooth">Nouveau · 64 phases · boucle 3,2 s</option><option value="old">Ancien aperçu V2 · 8 phases · boucle 1,28 s</option></select></label><span class="pill" id="state"></span></div><p><a id="png">PNG terrain complet</a> · <a id="scene">Composition PNG (jour)</a> · <a href="__BASE__README.md">Tous les PNG et les 64 phases océan</a></p><p class="note" id="size"></p><p class="note">Le terrain conserve sa résolution d’origine dans les fichiers ; cet aperçu est réduit. Roche et herbe générées puis couleurs corrigées en CIELAB vers la palette native. Zéro couleur hors palette dans le terrain jour ; motifs non certifiés pixel-identiques aux tuiles. Le plan de terrain regroupe sol, parois et bordures.</p><p class="note">Océan : indices et alpha fixes, seules les couleurs de palette évoluent. 64 phases à 50 ms donnent une boucle plus lente, avec des changements plus petits et plus fréquents. Ces exports et cet aperçu ne modifient pas le mod PMDO existant.</p></main><footer><small>Originaux Cap V2 et Terrasse V2 conservés. Les fonds de démonstration sont ajustés au cadrage ; aucun redimensionnement des PNG de terrain livrés.</small></footer><script>
const DATA=__DATA__;
const $=id=>document.getElementById(id),canvas=$('view'),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
const W=820,H=328,water=document.createElement('canvas');water.width=W;water.height=H;const wc=water.getContext('2d');
let running=true,elapsed=0,last=0,lastPhase=-1,lastMode='',dirty=true,assets;
function phaseAt(ms,old){return old?Math.floor(ms/160)%8*8:Math.floor(ms/50)%64}
function load(src){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src=src})}
function controls(){dirty=true;const z=DATA.zones[+$('zone').value];$('audit-status').textContent=(z.status==='A_REGENERER'?'NON RETENU — ':'INSPECTÉ — ')+z.note;$('png').href=$('night').checked?z.nightLink:z.link;$('scene').href=$('night').checked?z.sceneNightLink:z.sceneLink;$('size').textContent=z.size.join(' × ')+' px · PNG RGBA · palette native verrouillée · aperçu proportionnel dans 820 × 328'}
for(const [i,z] of DATA.zones.entries())$('zone').add(new Option((z.status==='A_REGENERER'?'À REPRENDRE · ':'')+z.title,i));
$('zone').value='1';
for(const id of ['zone','night','terrain','sea','sky','cloud','cycle'])$(id).addEventListener('change',controls);
$('play').onclick=()=>{running=!running;$('play').textContent=running?'Pause':'Lecture';dirty=true};controls();
async function start(){
 assets={zones:await Promise.all(DATA.zones.map(async z=>({jour:await load(z.day),nuit:await load(z.night)}))),sky:{jour:await load(DATA.sky.jour),nuit:await load(DATA.sky.nuit)},clouds:{jour:await load(DATA.clouds.jour),nuit:await load(DATA.clouds.nuit)}};
 const idx=await load(DATA.indices);wc.drawImage(idx,0,0);const raw=wc.getImageData(0,0,W,H).data,index=new Uint8Array(W*H);for(let p=0;p<index.length;p++)index[p]=raw[p*4];const frame=wc.createImageData(W,H);
 function tick(now){if(last&&running)elapsed+=now-last;last=now;const old=$('cycle').value==='old',phase=phaseAt(elapsed,old),mode=$('night').checked?'nuit':'jour';
 if(phase!==lastPhase||mode!==lastMode){const pal=DATA.palettes[mode][phase],a=frame.data;for(let p=0;p<index.length;p++){const k=index[p],o=p*4;a[o]=pal[k*3];a[o+1]=pal[k*3+1];a[o+2]=pal[k*3+2];a[o+3]=k<DATA.alpha.length?DATA.alpha[k]:255}wc.putImageData(frame,0,0);lastPhase=phase;lastMode=mode;dirty=true}
 if(dirty){ctx.clearRect(0,0,W,H);if($('sky').checked)ctx.drawImage(assets.sky[mode],0,0);if($('cloud').checked)ctx.drawImage(assets.clouds[mode],0,0);if($('sea').checked)ctx.drawImage(water,0,0);if($('terrain').checked)ctx.drawImage(assets.zones[+$('zone').value][mode],0,0);$('state').textContent=(old?'8 phases · 1,28 s':'64 phases · 3,2 s')+' · '+(running?'lecture':'pause');dirty=false}requestAnimationFrame(tick)}
 requestAnimationFrame(tick)
}start().catch(e=>{$('state').textContent='Erreur de chargement des aperçus : '+e.message});
</script></html>'''.replace('__BASE__',BASE).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')))
(ROOT/'apercu_caps_terrasses_v4.html').write_text(page)
print('Standalone layered viewer:',round(len(page)/2**20,2),'MiB')
