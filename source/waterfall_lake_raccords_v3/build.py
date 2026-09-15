"""Integrated rock/water side wings; every approved pixel outside this repair is preserved."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];OLD=R/'renders/waterfall_lake_trois_v2';O=R/'renders/waterfall_lake_raccords_v3';S=O/'sprites';S.mkdir(parents=True,exist_ok=True);m0=json.loads((OLD/'manifest.json').read_text());W,H=m0['size'];N=m0['frames'];yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def full(im,xy):
 out=Image.new('RGBA',(W,H));out.alpha_composite(im,xy);return out
def cut(a,mask):
 b=a.copy();b[~mask]=0;return Image.fromarray(b)
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for n,im in ls:out.alpha_composite(im)
 return out
# Rocks AND flowing-water geometry are generated together, then split along their exact boundary.
raw=key(load(O/'bruts/massif_texture_gba_magenta.png')).resize((360,160),NN);a=np.array(full(raw,(72,-12)));a[:,208:296]=0
r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);flow=(a[:,:,3]>0)&(b>r*1.45)&(g>r*1.45);rock=(a[:,:,3]>0)&~flow
src=np.array(load(R/m0['source']));rr,gg,bb=src[:,:,:3].astype(float).transpose(2,0,1)
rockpal=np.unique(src[:100,120:336,:3][(rr[:100,120:336]>gg[:100,120:336]*1.08)&(bb[:100,120:336]<gg[:100,120:336]*.9)],axis=0)
_,ids=cKDTree(rockpal).query(a[:,:,:3]);rockrgb=a.copy();rockrgb[:,:,:3]=rockpal[ids]
cliffs=[('06b_falaise_arc_gauche',cut(rockrgb,rock&(xx<252))),('06c_falaise_arc_droite',cut(rockrgb,rock&(xx>=252)))]
for n,im in cliffs:im.save(S/(n+'.png'))
# Fine falling-water material comes from the new generated ribbons, fitted to the original GBA ramp.
refmat=np.array(load(R/'renders/waterfall_lake_fidele_v1/sprites/matiere_cascade_gba.png'));waterpal=np.unique(refmat[:,:,:3].reshape(-1,3),axis=0)
# Ordered brightness mapping avoids a global teal cast while retaining generated streak positions.
wp=waterpal[np.argsort(waterpal@np.array([.2126,.7152,.0722]))]
channels=[];textures=[]
for side in range(2):
 mask=flow&((xx<252) if side==0 else (xx>=252));labs,num=nd.label(mask,np.ones((3,3)));counts=np.bincount(labs.ravel());counts[0]=0;mask=labs==counts.argmax()
 ys,xs=np.where(mask);top,bottom=int(ys.min()),int(ys.max());centers={};widths={};rows=[]
 for y in range(top,bottom+1):
  cols=np.flatnonzero(mask[y]);assert len(cols)>0,(side,y);centers[y]=float((cols[0]+cols[-1])/2);widths[y]=int(cols[-1]-cols[0]+1)
  # Registered material row: follow the generated curving channel without borrowing dry rock pixels.
  sample=cols[np.minimum(len(cols)-1,np.floor(np.arange(24)*len(cols)/24).astype(int))];rows.append(a[y,sample,:3])
 rows=np.array(rows);lum=rows@np.array([.2126,.7152,.0722]);lo,hi=np.percentile(lum,[15,97]);ids=np.clip(np.floor((lum-lo)/max(hi-lo,1)*(len(wp)-1)+.5),0,len(wp)-1).astype(int);mapped=wp[ids]
 # A48-row material strip is the animation's periodic domain, derived only from the generated stream.
 body=mapped[-48:];assert len(body)==48;textures.append(body);Image.fromarray(body).save(S/f'matiere_cascade_generee_{side+1}.png')
 footx=round(np.mean(xs[ys>=bottom-2]));channels.append({'mask':mask,'top':top,'bottom':bottom,'foot':[footx,bottom+1],'centers':centers,'widths':widths})
# Existing static scene and all approved animations are reused unchanged except these six repair layers.
replaced=['06b_falaise_arc_gauche','06c_falaise_arc_droite','07_cascade_laterale_1','07_cascade_laterale_2','08_ecume_laterale_1','08_ecume_laterale_2']
static={n:load(OLD/f'jour/lake2_jour_{n}.png') for n in m0['static'] if n not in replaced};static.update(dict(cliffs))
falls=[];foams=[]
for p in range(N):
 ls=[]
 for side,ch in enumerate(channels):
  out=np.zeros((H,W,4),dtype='uint8');body=textures[side]
  for y in range(ch['top'],ch['bottom']+1):
   cols=np.flatnonzero(ch['mask'][y]);u=np.minimum(23,np.floor(np.arange(len(cols))*24/len(cols)).astype(int));out[y,cols,:3]=body[(y-ch['top']-2*p)%48,u];out[y,cols,3]=255
  ls.append((f'07_cascade_laterale_{side+1}',Image.fromarray(out)))
 falls.append(ls)
for p in range(3):
 ls=[]
 for side,ch in enumerate(channels):
  oldfoot=m0['side_channels'][side]['foot'];offset=(ch['foot'][0]-oldfoot[0],ch['foot'][1]-oldfoot[1]);im=full(load(OLD/f'jour/lake2_jour_08_ecume_laterale_{side+1}_{p:02}.png'),offset);arr=np.array(im);arr[rock]=0
  # Connect the lower wet pixels to the original GBA foam in pixel coordinates, keeping the footprint local.
  contact=nd.binary_dilation(ch['mask'],iterations=1)&(yy>=ch['bottom']-1)&(yy<=ch['bottom']+2)&~rock
  arr[contact]=[248,248,248,255];labels,count=nd.label(arr[:,:,3]>0,np.ones((3,3)));keep=np.unique(labels[contact]);keep=keep[keep>0];arr[~np.isin(labels,keep)]=0
  ls.append((f'08_ecume_laterale_{side+1}',Image.fromarray(arr)))
 foams.append(ls)
order=m0['layer_order'];animnames=m0['animated'];dur=m0['durations_ms']
def layers(p):
 generated=dict(falls[p]+foams[p%3]);ls=[]
 for n in order:
  im=generated[n] if n in generated else static[n] if n in static else load(OLD/f'jour/lake2_jour_{n}_{p:02}.png');ls.append((n,im))
 return ls
# Explicit repair mask proves no unwanted change to the approved lake, platforms or canopy outside it.
repair=np.zeros((H,W),bool)
for n in replaced:
 if n in m0['animated']:
  for p in range(N):repair|=np.array(load(OLD/f'jour/lake2_jour_{n}_{p:02}.png'))[:,:,3]>0
 else:repair|=np.array(load(OLD/f'jour/lake2_jour_{n}.png'))[:,:,3]>0
repair|=rock|flow
for ls in foams:
 for n,im in ls:repair|=np.array(im)[:,:,3]>0
Image.fromarray((repair*255).astype('uint8')).save(O/'MASQUE_REPRISE_LOCALE.png');Image.fromarray((rock*255).astype('uint8')).save(O/'MASQUE_ROCHE.png')
for k,ch in enumerate(channels):Image.fromarray((ch['mask']*255).astype('uint8')).save(O/f'MASQUE_CHUTE_{k+1}.png')
frames={}
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)]
  for n,im in ls:
   if n in animnames or p==0:im.save(P/(f'lake3_{mode}_{n}_{p:02}.png' if n in animnames else f'lake3_{mode}_{n}.png'))
  im=merge(ls);assert np.all(np.array(im)[:,:,3]==255);assert np.array_equal(np.array(im)[~repair],np.array(load(OLD/f'{mode}/lake2_{mode}_composition_{p:02}.png'))[~repair]);im.save(P/f'lake3_{mode}_composition_{p:02}.png');frames[mode].append(im)
  if p==0:
   im.save(P/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'lake3_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
m={**m0,'parent':'waterfall_lake_trois_v2','replaced_layers':replaced,'generation':'rocks and sidewater generated together, exact separation by pixel mask; registered generated material advected down each curving channel','rock_palette':'original GBA cliff colors','side_channels':[{'top':c['top'],'bottom':c['bottom'],'foot':c['foot'],'centers':c['centers'],'widths':c['widths']} for c in channels],'repair_pixel_count':int(repair.sum()),'approved_remainder_unchanged_all_frames':True,'runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
data={}
for mode in frames:
 P=O/mode;items=[{'name':'Composition harmonisée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')},{'name':'Avant · ajouts V2','src':uri((OLD/mode/'ANIMATION.webp').read_bytes(),'image/webp')}]
 for n in order:
  if n in animnames:
   ims=[load(P/f'lake3_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);srcuri=uri(b.getvalue(),'image/webp')
  else:srcuri=uri((P/f'lake3_{mode}_{n}.png').read_bytes())
  items.append({'name':n,'src':srcuri})
 data[mode]=items
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake · raccords roche/eau</title><style>body{background:#162a31;color:#edf1db;font:16px system-ui;max-width:1080px;margin:30px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#355863;color:white}</style><h1>Waterfall Lake · falaises et chutes intégrées</h1><p>Les deux ailes rocheuses et leurs cascades ont été dessinées ensemble, puis séparées en calques. Strates courbes raccordées, eau dans les canaux générés et écumes aux pieds réels. Le reste approuvé du lac est conservé.</p><select id="mode"><option value="jour">Jour</option><option value="nuit">Nuit</option></select><select id="sel"></select><br><img id="view" alt="Waterfall Lake harmonisé"><p>Reprise locale de la roche et des chutes ajoutées, pas une nouvelle génération du lac. Même animation des cercles et des plateformes. Rendus jour/nuit, aucun test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script>'''
(R/'apercu_waterfall_lake_raccords_v3.html').write_text(html)
print('Built integrated wings,',len(order),'layers. Channel feet:',[c['foot'] for c in channels])
