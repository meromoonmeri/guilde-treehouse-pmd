from pathlib import Path
import json,base64
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];O=R/'renders/spring_escalier_v1';V=R/'renders/spring_arc_en_ciel_v1';N=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
base=load(V/'01_source_centrale/01_decor_sans_lumiere.png');raw=load(O/'bruts/source_surelevee.png').resize((600,600),N)
mask=Image.new('L',(600,600));d=ImageDraw.Draw(mask);d.polygon([(137,250),(152,265),(187,285),(233,292),(270,296),(301,286),(336,294),(380,288),(423,268),(452,249),(463,270),(457,329),(434,358),(393,378),(377,406),(365,428),(229,429),(217,414),(223,390),(190,378),(164,359),(141,327)],fill=255)
# Soft edge only within the local edit; all other original pixels remain untouched.
ma=np.array(mask.filter(ImageFilter.GaussianBlur(1)));a=np.array(raw);a[:,:,3]=ma
# Never bake the rainbow light or original animated streams into the new terrain.
protected=np.zeros((600,600),bool)
for name in ['faisceau','halo_bassin','eau_cascades']:
 for f in range(39):protected|=np.array(load(V/'commun'/name/f'{f:02}.png'))[:,:,3]>0
a[protected]=0
y,x=np.mgrid[:600,:600];stairs=(x>=224)&(x<=377)&(y>=317)&(y<=433)
b=a.copy();b[stairs]=0;c=a.copy();c[~stairs]=0
relief=Image.fromarray(b);stair=Image.fromarray(c);save(base,Path('calques/01_decor_original.png'));save(relief,Path('calques/02_petit_relief.png'));save(stair,Path('calques/03_escalier.png'));save(Image.fromarray(a[:,:,3]),Path('masque_modification.png'))
frames=[];originals=[]
for f in range(39):
 orig=base.copy();im=base.copy();im.alpha_composite(relief);im.alpha_composite(stair)
 for name in ['eau_cascades','halo_bassin','faisceau']:
  layer=load(V/'commun'/name/f'{f:02}.png');im.alpha_composite(layer);orig.alpha_composite(layer)
  if f==0:save(layer,Path('calques')/({'eau_cascades':'04_eau_cascades','halo_bassin':'05_halo_arc_en_ciel','faisceau':'06_faisceau_arc_en_ciel'}[name]+'.png'))
 assert np.array_equal(np.array(im)[a[:,:,3]==0],np.array(orig)[a[:,:,3]==0])
 frames.append(im);originals.append(orig)
save(frames[0],Path('composition.png'));frames[0].save(O/'animation.webp',save_all=True,append_images=frames[1:],duration=[167,167,166]*13,loop=0,lossless=True)
board=Image.new('RGB',(1200,628),'#18353a');board.paste(originals[0],(0,28));board.paste(frames[0],(600,28));d=ImageDraw.Draw(board);d.text((12,8),'AVANT : disposition centrale conservee',fill='white');d.text((612,8),'APRES : petite montee et escalier gris-vert',fill='white');save(board,Path('AVANT_APRES.png'))
manifest={'canvas':[600,600],'frames':39,'period_ms':6500,'reference':'spring_arc_en_ciel_v1/01_source_centrale','edit':'Relief rocheux bas et escalier central ; aucun déplacement du bassin ou de la forêt','animation_source':'../spring_arc_en_ciel_v1/commun/{eau_cascades,halo_bassin,faisceau}/00..38.png','native':False,'palette':'Roche générée guidée par la roche gris-vert locale, pas des tuiles natives identiques'}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'verification.json').write_text(json.dumps({'outside_edit_pixel_exact_all_39_frames':True,'changed_area_max_pixels':int((a[:,:,3]>0).sum()),'protected_animation_pixels':int(protected.sum()),'runtime_validated':False},indent=2))
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
data={'static':[uri(O/'calques'/n) for n in ['01_decor_original.png','02_petit_relief.png','03_escalier.png']], 'anim':[[uri(V/'commun'/n/f'{f:02}.png') for f in range(39)] for n in ['eau_cascades','halo_bassin','faisceau']]}
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spring · petit relief et escalier</title><style>body{background:#132a30;color:#edf8ee;font:16px system-ui;max-width:1080px;margin:auto;padding:24px}h1{font-size:27px}p{color:#b9d5cb;line-height:1.6}.view{display:flex;gap:22px}canvas{width:70%;image-rendering:pixelated;background:#223c40}label{display:block;margin:18px 0}button{background:#31575b;color:white;padding:10px;border:1px solid #7fa59b;border-radius:6px}@media(max-width:700px){.view{display:block}canvas{width:100%}}</style><h1>Luminous Spring · petite montée rocheuse</h1><p>Disposition centrale conservée. Bassin à sa place, relief bas gris-vert et escalier central. Lumière arc-en-ciel et cascades inchangées.</p><button id="pause">Pause</button> <button id="before">Voir avant</button> <button id="png">Exporter PNG</button><p id="clock"></p><div class="view"><canvas id="view" width="600" height="600"></canvas><aside id="layers"></aside></div><p>Décor, relief, escalier, eau, halo et faisceau restent séparés. Les pixels hors de la zone de retouche sont conservés exactement sur les 39 phases. La nouvelle roche est générée à partir de la référence locale, pas reconstruite en tuiles natives.</p><script>const D=__DATA__;function image(s){const i=new Image();i.src=s;return i}const fixed=D.static.map(image),anim=D.anim.map(a=>a.map(image)),visible=[true,true,true,true,true,true];let time=0,last=null,running=true,before=false;const c=document.getElementById('view'),ctx=c.getContext('2d');['Décor original','Petit relief','Escalier','Eau / cascades','Halo arc-en-ciel','Faisceau'].forEach((name,j)=>{const l=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=()=>visible[j]=ch.checked;l.append(ch,document.createTextNode(name));document.getElementById('layers').append(l)});document.getElementById('pause').onclick=e=>{running=!running;e.target.textContent=running?'Pause':'Reprendre'};document.getElementById('before').onclick=e=>{before=!before;e.target.textContent=before?'Voir après':'Voir avant'};document.getElementById('png').onclick=()=>{const a=document.createElement('a');a.href=c.toDataURL();a.download='spring_escalier.png';a.click()};function draw(im){if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0)}function frame(t){if(last!==null&&running)time+=t-last;last=t;const f=Math.floor(time*6/1000)%39;ctx.clearRect(0,0,600,600);fixed.forEach((im,j)=>{if(visible[j]&&(!before||j===0))draw(im)});anim.forEach((ims,j)=>{if(visible[j+3])draw(ims[f])});document.getElementById('clock').textContent='Phase '+(f+1)+'/39 · boucle 6,5 s';requestAnimationFrame(frame)}requestAnimationFrame(frame);</script></html>'''
(R/'apercu_spring_escalier_v1.html').write_text(html.replace('__DATA__',json.dumps(data)),encoding='utf8');print('Local edit verified on 39 phases; gallery ready')
