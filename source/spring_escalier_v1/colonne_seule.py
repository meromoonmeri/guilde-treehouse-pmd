from pathlib import Path
import json,re,base64
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/spring_colonne_irisee_v1';V=R/'renders/soleil_spring_v1/spring';T=R/'renders/spring_escalier_v1';O.mkdir(parents=True,exist_ok=True)
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def uri(im):
 import io
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
base=load(V/'01_decor.png');relief=load(T/'calques/02_petit_relief.png');stairs=load(T/'calques/03_escalier.png');save(base,Path('calques/01_decor_turquoise.png'));save(relief,Path('calques/02_relief.png'));save(stairs,Path('calques/03_escalier.png'))
y,x=np.mgrid[:600,:600];mask=(x>=275)&(x<325)&(y<201);frames=[];columns=[];anim=[[],[],[]];checks=[]
for f in range(78):
 native=f//2;src=np.array(load(V/'frames'/f'{native:02}.png'));rgb=src[:,:,:3].astype(float)
 hue=((x-275)/50*.8-f/78)%1
 spectral=np.stack([.5+.5*np.cos(2*np.pi*(hue-j/3)) for j in range(3)],axis=2);spectral=.45+.55*spectral
 lum=rgb.max(axis=2);target=spectral*(lum[:,:,None]*.95+10)
 strength=.68*(1-np.clip((lum-205)/50,0,1)*.9)
 # Only the beam, with a very small soft edge. Keep bright white core nearly white.
 strength*=np.minimum(np.clip((x-274)/4,0,1),np.clip((325-x)/4,0,1))
 colored=np.clip(rgb*(1-strength[:,:,None])+target*strength[:,:,None],0,255).astype('uint8')
 a=np.zeros_like(src);a[mask,:3]=colored[mask];a[mask,3]=255;column=Image.fromarray(a);save(column,Path('colonne')/f'{f:02}.png');columns.append(column)
 water=load(V/'02_cycle_3'/f'{native%3:02}.png');light=load(V/'03_cycle_13'/f'{native%13:02}.png')
 comp=base.copy();comp.alpha_composite(relief);comp.alpha_composite(stairs);comp.alpha_composite(water);comp.alpha_composite(light)
 original=comp.copy();comp.alpha_composite(column)
 assert np.array_equal(np.array(comp)[~mask],np.array(original)[~mask]);frames.append(comp)
 for arr,im in zip(anim,[water,light,column]):arr.append(uri(im))
save(frames[0],Path('composition.png'));frames[0].save(O/'animation.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*26,loop=0,lossless=True)
sheet=Image.new('RGBA',(10*100,8*210))
for f,im in enumerate(columns):sheet.alpha_composite(im.crop((250,0,350,210)),(f%10*100,f//10*210))
save(sheet,Path('planche_colonne_78.png'))
# Keep the previously delivered viewer controls and before/after terrain toggle.
html=(R/'apercu_spring_escalier_v1.html').read_text();d={'static':[uri(base),uri(relief),uri(stairs)],'anim':anim}
html=re.sub(r'const D=.*?;function image',lambda _: 'const D='+json.dumps(d)+';function image',html,count=1,flags=re.S)
html=html.replace('time*6/1000)%39','time*12/1000)%78').replace("+'/39 · boucle", "+'/78 · boucle")
html=html.replace('Luminous Spring · petite montée rocheuse','Luminous Spring · colonne irisée uniquement').replace('Lumière arc-en-ciel et cascades inchangées.','Bassin et halo turquoise d’origine. Seule la colonne reçoit des reflets multicolores subtils.').replace("'Halo arc-en-ciel','Faisceau'","'Lumière native du bassin','Colonne irisée'")
html=html.replace('sur les 39 phases','sur les 78 phases').replace('Décor, relief, escalier, eau, halo et faisceau restent séparés.','Décor, relief, escalier, eau, lumière native et colonne irisée restent séparés. Désactiver « Colonne irisée » restitue le faisceau turquoise original.')
(R/'apercu_spring_colonne_irisee_v1.html').write_text(html)
(O/'verification.json').write_text(json.dumps({'frames':78,'period_ms':6500,'outside_column_exact_against_turquoise_version_all_frames':True,'column_box':[275,0,325,201],'terrain_layers_unchanged':True,'native_motion':'Original 39 phases, chaque phase dure deux frames nouvelles','runtime_validated':False},indent=2))
print('78 frames verified: only column changed; approved terrain preserved')
