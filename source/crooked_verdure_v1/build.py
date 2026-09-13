from pathlib import Path
import json,math,random,base64,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/crooked_verdure_v1';A=R/'source/cote_v5_expeditions/audit';N=Image.Resampling.NEAREST;S=(320,240)
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def blank():return Image.new('RGBA',S)
def shift(im,xy):
 o=blank();o.alpha_composite(im,xy);return o
def gray(im):
 a=np.array(im);v=np.round(a[:,:,:3].astype(float)@np.array([.299,.587,.114]));a[:,:,:3]=np.stack([v*.91,v*.97,v],2).clip(0,255).astype('uint8');return Image.fromarray(a)
source=load(A/'Halcyon__crooked_cavern_entrance_layer_0.png');objects=load(A/'Halcyon__crooked_cavern_entrance_layer_1.png')
# Manual silhouette along the canonical wall/forecourt boundary, unchanged native scale.
ground=Image.new('L',S);d=ImageDraw.Draw(ground);d.polygon([(0,219),(17,211),(28,187),(48,176),(65,158),(88,150),(108,137),(123,126),(141,119),(166,118),(187,130),(204,143),(222,159),(243,176),(261,184),(280,205),(300,219),(320,231),(320,240),(0,240)],fill=255)
rock=gray(source);a=np.array(rock);a[:,:,3]=255-np.array(ground);rock=Image.fromarray(a)
wall=shift(rock,(8,0));wall.alpha_composite(rock.crop((0,0,8,240)),(0,0));save(wall,Path('calques/02_paroi_grise.png'))
# Native Spring grass underneath the canonical silhouette; retain canonical sandy path pixels.
spring=load(R/'source/soleil_spring_v1/references/LuminousSpring.png');patch=spring.crop((250,390,314,454));floor=blank()
for y in range(0,240,64):
 for x in range(0,320,64):floor.alpha_composite(patch,(x,y))
path=Image.new('L',S);d=ImageDraw.Draw(path);d.polygon([(157,113),(179,113),(180,144),(163,175),(166,204),(187,240),(111,240),(130,205),(133,174),(153,145)],fill=255)
# Follow entrance displacement by eight pixels, preserve all original dirt texture.
dirt=shift(source,(8,0));floor=Image.composite(dirt,floor,path);save(floor,Path('calques/01_sol_herbe_chemin.png'))
obj=blank();obj.alpha_composite(gray(objects.crop((27,158,128,240))), (19,158));obj.alpha_composite(gray(objects.crop((184,153,304,240))), (191,147));save(obj,Path('calques/03_rochers_gris.png'))
raw=load(O/'bruts/vegetation.png');ar=np.array(raw);rr,gg,bb=[ar[:,:,i].astype(int) for i in range(3)];ar[(rr>145)&(bb>125)&(gg<120)&(rr>gg*1.6)&(bb>gg*1.6)]=0;raw=Image.fromarray(ar);w,h=raw.size;veg=blank()
positions=[(14,193),(46,167),(252,183),(278,211),(74,216),(227,210)]
for i,xy in enumerate(positions):
 c=raw.crop((i%3*w//3,i//3*h//2,(i%3+1)*w//3,(i//3+1)*h//2));c=c.crop(c.getbbox());width=24 if i in [1,2] else 30;c=c.resize((width,round(c.height*width/c.width)),N);veg.alpha_composite(c,xy)
save(veg,Path('calques/04_vegetation.png'));static=[floor,wall,obj,veg];frames=[];fxs=[];rng=random.Random(64);motes=[(rng.randrange(35,285),rng.randrange(125,229),rng.random()*math.tau) for i in range(16)]
for f in range(48):
 fx=blank();d=ImageDraw.Draw(fx)
 for x,y,p in motes:
  phase=math.tau*f/48+p;alpha=round(20+60*(math.sin(phase)+1)/2);yy=y+round(2*math.sin(phase));d.point((x,yy),fill=(213,233,161,alpha))
 save(fx,Path('animation/particules')/f'{f:02}.png');fxs.append(fx);comp=blank()
 for im in static+[fx]:comp.alpha_composite(im)
 frames.append(comp)
save(frames[0],Path('composition.png'));save(frames[0].resize((960,720),N),Path('composition_x3.png'));frames[0].save(O/'animation.webp',save_all=True,append_images=frames[1:],duration=80,loop=0,lossless=True)
# GIFs use a shared palette for stable colors rather than per-frame palette changes.
def gif(ims,p,duration):
 sample=Image.new('RGB',(ims[0].width*4,ims[0].height))
 for i,f in enumerate([0,len(ims)//4,len(ims)//2,len(ims)*3//4]):sample.paste(ims[f].convert('RGB'),(i*ims[0].width,0))
 pal=sample.quantize(colors=256);qs=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in ims];qs[0].save(p,save_all=True,append_images=qs[1:],duration=duration,loop=0,optimize=False,disposal=2)
gif(frames,O/'animation.gif',80)
with Image.open(R/'renders/spring_colonne_irisee_v1/animation.webp') as im:
 springs=[]
 for f in range(im.n_frames):im.seek(f);springs.append(im.convert('RGBA'))
gif(springs,O/'spring_colonne_irisee.gif',[80,80,90]*26)
manifest={'canvas':list(S),'layout':'Entrée déplacée de +8px, blocs latéraux repositionnés, approche herbeuse et chemin central','rock':'Dessin canonique conservé à échelle1 ; RGB remappés en gris légèrement froid selon luminance. Pas texture rocheuse générée.','grass':'Patch natif LuminousSpring 250,390,314,454, répété au sol','vegetation':'Six petites touffes générées, distinctes des matériaux natifs','animation':{'type':'Particules ambiantes ajoutées ; source Crooked Cavern statique','frames':48,'frame_ms':80,'period_ms':3840},'spring_gif':{'frames':78,'period_ms':6500,'note':'Copie GIF 256 couleurs de l’animation WebP publiée, couleur légèrement quantifiée'},'layers':['01_sol_herbe_chemin.png','02_paroi_grise.png','03_rochers_gris.png','04_vegetation.png'],'runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Native gray cliff + verdant floor +48 overlay phases; Spring GIF78')
def uri(im):
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
data={'layers':[uri(im) for im in static],'fx':[uri(im) for im in fxs],'spring':'data:image/gif;base64,'+base64.b64encode((O/'spring_colonne_irisee.gif').read_bytes()).decode()}
h='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Crooked Cavern · verdure et roche grise</title><style>body{background:#15231f;color:#e8eee3;font:16px system-ui;max-width:1100px;margin:auto;padding:24px}h1{font-size:26px}p{color:#b9cbb8;line-height:1.6}button{padding:10px;background:#344b3b;color:white;border:1px solid #799079;border-radius:6px}.view{display:flex;gap:20px;margin-top:20px}canvas{width:75%;image-rendering:pixelated;background:#273728}label{display:block;margin:14px 0}#spring{max-width:600px;width:100%;display:none;image-rendering:pixelated}@media(max-width:700px){.view{display:block}canvas{width:100%}}</style><h1>Crooked Cavern · verdure & roche grise</h1><p>Dessin rocheux canonique conservé, entrée légèrement décalée, sol herbeux et passage dégagé. Animation d’ambiance indépendante, pas de déformation des parois.</p><button id="cave">Voir Crooked Cavern</button> <button id="springbtn">Voir le Spring animé</button> <button id="pause">Pause cavern</button><div class="view" id="cavern"><canvas id="view" width="320" height="240"></canvas><aside id="layers"></aside></div><img id="spring" alt="Animation de la colonne irisée du Spring"><p id="clock"></p><p>Le Spring ci-dessus est un GIF de 78 images. Les particules de Crooked Cavern sont un ajout : sa carte Halcyon source est fixe. Les fleurs et fougères ajoutées sont générées, contrairement au dessin natif de la roche.</p><script>const D=__DATA__;function image(s){let i=new Image();i.src=s;return i}const layers=D.layers.map(image),fx=D.fx.map(image),visible=[true,true,true,true,true];let time=0,last=null,running=true;const c=document.getElementById('view'),ctx=c.getContext('2d');document.getElementById('spring').src=D.spring;['Sol / chemin','Paroi canonique grise','Rochers','Végétation','Particules animées'].forEach((n,j)=>{const l=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=()=>visible[j]=ch.checked;l.append(ch,document.createTextNode(n));document.getElementById('layers').append(l)});document.getElementById('springbtn').onclick=()=>{document.getElementById('spring').style.display='block';document.getElementById('cavern').style.display='none'};document.getElementById('cave').onclick=()=>{document.getElementById('spring').style.display='none';document.getElementById('cavern').style.display='flex'};document.getElementById('pause').onclick=e=>{running=!running;e.target.textContent=running?'Pause cavern':'Reprendre cavern'};function draw(im){if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0)}function frame(t){if(last!==null&&running)time+=t-last;last=t;const f=Math.floor(time/80)%48;ctx.clearRect(0,0,320,240);layers.forEach((im,j)=>{if(visible[j])draw(im)});if(visible[4])draw(fx[f]);document.getElementById('clock').textContent='Crooked Cavern : phase '+(f+1)+'/48 · 3,84 s';requestAnimationFrame(frame)}requestAnimationFrame(frame);</script></html>'''
(R/'apercu_crooked_verdure_v1.html').write_text(h.replace('__DATA__',json.dumps(data)),encoding='utf8')
