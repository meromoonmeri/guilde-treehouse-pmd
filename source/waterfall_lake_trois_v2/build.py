from pathlib import Path
import io,json,sys,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];OLD=R/'renders/waterfall_lake_fidele_v1';O=R/'renders/waterfall_lake_trois_v2';S=O/'sprites';S.mkdir(exist_ok=True);W,H=504,360;N=24;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
m0=json.loads((OLD/'manifest.json').read_text());source=Image.open(R/m0['source']).convert('RGBA');src=np.array(source)
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def full(im,xy):
 out=Image.new('RGBA',(W,H));out.alpha_composite(im,xy);return out
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for n,im in ls:out.alpha_composite(im)
 return out
old_static={n:load(OLD/f'jour/lake_jour_{n}.png') for n in m0['static']};originalwater=np.array(old_static.pop('01_eau_profondeurs_originales'))
terrainnames=[n for n in old_static if n.startswith(('02','03','04','05','06'))];platformnames=[n for n in old_static if n.startswith(('10','11'))]
platformmask=np.maximum.reduce([np.array(old_static[n])[:,:,3] for n in platformnames])>0
# Two small generated wing sections only. Original central fall and its surrounding cliff stay visible.
addon=key(load(O/'bruts/falaises_arc_magenta.png')).resize((360,200),NN);a=np.array(full(addon,(72,0)));a[:,196:308]=0
r,g,b=src[:,:,:3].astype(float).transpose(2,0,1);palette=np.unique(src[:100,120:336,:3][(r[:100,120:336]>g[:100,120:336]*1.08)&(b[:100,120:336]<g[:100,120:336]*.9)],axis=0)
_,ids=cKDTree(palette).query(a[:,:,:3]);a[:,:,:3]=palette[ids];a[a[:,:,3]==0]=0
addmask=a[:,:,3]>0;cliffs=[('06b_falaise_arc_gauche',cut(a,xx<252)),('06c_falaise_arc_droite',cut(a,xx>=252))]
# Two continuous outlet channels are fitted to the new cliff slots, preserving the central opening.
channels=[]
for side in [0,1]:
 mask=np.zeros((H,W),bool);centers=[]
 for y in range(108):
  desired=float(np.interp(y,[0,20,40,108],[150,156,177,177]));desired=desired if side==0 else 504-desired
  lo,hi=(140,196) if side==0 else (308,364);free=~addmask[y,lo:hi];labs,num=nd.label(free);xs=np.flatnonzero(free)+lo;assert len(xs)>0
  anchor=int(xs[np.argmin(abs(xs-desired))]);run=np.flatnonzero(labs==labs[anchor-lo])+lo;width=min(24,len(run));left=int(np.clip(round(desired)-width//2,run[0],run[-1]+1-width));mask[y,left:left+width]=True;centers.append(left+width//2)
 assert mask.sum()>1800
 channels.append({'mask':mask,'centers':centers,'foot':[centers[-1],108]})
material=np.array(load(OLD/'sprites/matiere_cascade_gba.png'))
# Subtle palette modulation only: fixed ring geometry and no lateral movement of the depth bands.
r,g,b=originalwater[:,:,:3].astype(float).transpose(2,0,1);ellipse=((xx-252)/160)**2+((yy-207)/87)**2
ring=(ellipse<1.02)&(r<50)&(g<160)&(b>140)&~platformmask
Image.fromarray((ring*255).astype('uint8')).save(O/'MASQUE_ANNEAUX.png')
waterpalette=np.unique(src[:,:,:3][(src[:,:,0]<70)&(src[:,:,2]>130)],axis=0);wtree=cKDTree(waterpalette)
# Match platform water colors to the local GBA lake depth, retain all native8key alpha shapes.
contacts=[n for n in m0['animated'] if n.startswith('12_')];reflect=[]
for p in range(8):
 ls=[]
 for n in contacts:
  aa=np.array(load(OLD/f'jour/lake_jour_{n}_{p:02}.png'));visible=aa[:,:,3]>0;lum=aa[:,:,:3]@np.array([.2126,.7152,.0722]);level=np.clip((lum-70)/95,0,1)
  target=originalwater[:,:,:3].astype(float)*(.73+.27*level[:,:,None])+np.array([0,24,32])*level[:,:,None]
  _,idx=wtree.query(target);aa[:,:,:3]=waterpalette[idx];aa[~visible]=0;ls.append((n,Image.fromarray(aa)))
 reflect.append(ls)
sidefalls=[];sidefoams=[]
for p in range(N):
 ls=[]
 for k,ch in enumerate(channels):
  centers=np.array(ch['centers']+[ch['centers'][-1]]*(H-108));u=xx-centers[:,None];a=np.zeros((H,W,4),dtype='uint8');mask=ch['mask'];tx=np.clip(u+38,0,75);a[mask]=material[(yy[mask]-2*p)%48,tx[mask]];ls.append((f'07_cascade_laterale_{k+1}',Image.fromarray(a)))
 sidefalls.append(ls)
for p in range(3):
 oldfoam=load(OLD/f'jour/lake_jour_08_ecume_impact_{p:02}.png').crop((200,64,296,97)).resize((42,18),NN);ls=[]
 for k,ch in enumerate(channels):
  x,y=ch['foot'];a=np.array(full(oldfoam,(x-21,y-5)));a[addmask]=0;ls.append((f'08_ecume_laterale_{k+1}',Image.fromarray(a)))
 sidefoams.append(ls)
static=[(n,old_static[n]) for n in terrainnames]+cliffs+[(n,old_static[n]) for n in platformnames]
def animated(p):
 a=originalwater.copy();shift=[0,1,0,-1][p%4];mod=np.rint(np.cos(ellipse*22)*shift).astype(int)
 for j,amplitude in [(1,2),(2,3)]:a[:,:,j][ring]=np.clip(a[:,:,j][ring].astype(int)+mod[ring]*amplitude,0,255).astype('uint8')
 return [('01_eau_anneaux',Image.fromarray(a)),('07_cascade_descendante',load(OLD/f'jour/lake_jour_07_cascade_descendante_{p:02}.png')),('08_ecume_impact',load(OLD/f'jour/lake_jour_08_ecume_impact_{p:02}.png'))]+sidefalls[p]+sidefoams[p%3]+reflect[p%8]
def layers(p):
 an=dict(animated(p));return [('01_eau_anneaux',an['01_eau_anneaux'])]+[(n,old_static[n]) for n in terrainnames]+cliffs+[(n,im) for n,im in animated(p) if n!='01_eau_anneaux']+[(n,old_static[n]) for n in platformnames]
frames={};dur=m0['durations_ms'];order=[n for n,_ in layers(0)];animnames=[n for n,_ in animated(0)]
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)]
  for n,im in ls:
   if p==0 or n in animnames:im.save(P/(f'lake2_{mode}_{n}_{p:02}.png' if n in animnames else f'lake2_{mode}_{n}.png'))
  im=merge(ls);assert np.all(np.array(im)[:,:,3]==255);im.save(P/f'lake2_{mode}_composition_{p:02}.png');frames[mode].append(im)
  if p==0:
   im.save(P/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'lake2_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
m={'size':[W,H],'frames':N,'durations_ms':dur,'loop_ms':4000,'static':[n for n,_ in static],'animated':animnames,'layer_order':order,'parent':'waterfall_lake_fidele_v1','source':m0['source'],'cascade_count':3,'side_channels':[{'foot':c['foot'],'centers':c['centers']} for c in channels],'circle_rgb_modulation_max':[0,2,3],'platform_water':'native8key alpha preserved; RGB fitted to local depth using original GBA water palette','cliffs':'two generated arc wings, mapped to original cliff colors; central native fall/cliff protected','runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
for k,c in enumerate(channels):Image.fromarray((c['mask']*255).astype('uint8')).save(O/f'MASQUE_CASCADE_{k+1}.png')
Image.fromarray((addmask*255).astype('uint8')).save(O/'MASQUE_FALAISES_AJOUTEES.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
data={}
for mode in frames:
 P=O/mode;items=[{'name':'Composition animée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')}]
 for n in order:
  if n in animnames:
   ims=[load(P/f'lake2_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);srcuri=uri(b.getvalue(),'image/webp')
  else:srcuri=uri((P/f'lake2_{mode}_{n}.png').read_bytes())
  items.append({'name':n,'src':srcuri})
 data[mode]=items
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake · trois cascades</title><style>body{background:#162a31;color:#edf1db;font:16px system-ui;max-width:1080px;margin:30px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#355863;color:white}</style><h1>Waterfall Lake · trois cascades</h1><p>Deux ailes rocheuses en demi-cercle, cascade centrale conservée et deux chutes latérales utilisant la même matière GBA. Cercles de profondeur fixes, variation de couleur très légère. Reflets des plateformes assortis aux bleus du lac, cycle natif conservé.</p><select id="mode"><option value="jour">Jour</option><option value="nuit">Nuit</option></select><select id="sel"></select><br><img id="view" alt="Waterfall Lake trois cascades"><p>Ajouts rocheux générés et adaptés ; animations reconstruites à partir de la référence statique, sauf le cycle natif des plateformes. Aucun test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script>'''
(R/'apercu_waterfall_lake_trois_v2.html').write_text(html)
print('Built',len(order),'layers,3falls,day/night')
