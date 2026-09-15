"""Generated references -> keyed independent reconstructed depth planes -> aligned arena layers.
No runtime assumptions. Original arena layers untouched; illumination is optional.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'source/tours_saisons_v1'));from common import load,merge,ora,night
O=R/'renders/panoramas_tours_v2';O.mkdir(parents=True,exist_ok=True)
W,H=640,480;yy,xx=np.mgrid[:H,:W];rng=np.random.default_rng(241)
oldmanifest=json.loads((R/'renders/tours_hooh_v1/manifest.json').read_text());manifest=[]
def image(rgb,alpha=255):
 a=np.zeros((H,W,4),dtype='uint8');a[:,:,:3]=np.asarray(rgb).clip(0,255).astype('uint8');a[:,:,3]=np.asarray(alpha).clip(0,255).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a)
def curve(points):return np.rint(np.interp(np.arange(W),[x for x,y in points],[y for x,y in points])).astype(int)
def keyed(im,path):
 # Magenta is only an intermediate matte, never a final opaque backdrop.
 a=np.array(im);key=a.copy();key[a[:,:,3]==0]=[255,0,255,255];Image.fromarray(key).save(path);b=key.copy();b[(b[:,:,0]==255)&(b[:,:,1]==0)&(b[:,:,2]==255)]=0;assert np.array_equal(b,a);return Image.fromarray(b)
def split_light(im):
 a=np.array(im);rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);lum=rgb@np.array([.299,.587,.114]);warm=np.clip((r-b+35)/140,0,1);amount=(.06+.26*(lum/255)**1.5)*warm
 color=np.array([255.,194.,114.]);amount=np.minimum(amount,np.min(rgb/color,axis=2)*.6);amount=np.floor(amount*255)/255;amount[a[:,:,3]==0]=0
 base=(rgb-amount[:,:,None]*color)/(1-amount[:,:,None]);out=image(base,a[:,:,3]);light=image(color,np.rint(amount*255));return out,light
profiles={
'carillon':[
[(0,81),(9,85),(32,73),(65,57),(94,81),(108,77),(144,108),(164,103),(190,92),(248,129),(274,126),(320,141),(361,122),(384,127),(426,113),(462,83),(490,91),(529,83),(575,57),(600,83),(618,74),(639,85)],
[(0,138),(50,123),(89,145),(120,143),(172,121),(228,157),(282,175),(320,181),(354,171),(391,154),(446,171),(476,140),(520,143),(573,112),(610,126),(639,119)],
[(0,184),(25,177),(70,206),(93,189),(125,183),(176,171),(226,203),(274,222),(320,234),(357,226),(411,211),(463,189),(501,175),(554,159),(603,143),(639,159)],
[(0,240),(60,253),(114,262),(170,261),(227,242),(281,225),(320,238),(380,215),(435,217),(475,238),(525,242),(575,216),(639,199)],
[(0,290),(50,289),(105,302),(155,286),(207,281),(258,272),(310,277),(375,276),(416,301),(470,317),(512,299),(560,291),(609,278),(639,270)],
[(0,376),(60,400),(121,422),(175,433),(217,450),(263,420),(324,423),(370,438),(419,420),(476,429),(535,400),(590,369),(639,381)]],
'cendree':[
[(0,131),(13,125),(30,131),(78,87),(101,120),(117,117),(145,149),(163,144),(181,124),(202,145),(213,169),(251,195),(273,176),(305,198),(338,198),(359,177),(387,184),(414,190),(445,171),(467,133),(487,118),(513,139),(525,126),(563,140),(593,111),(624,80),(639,100)],
[(0,174),(24,191),(62,170),(92,193),(120,203),(155,190),(184,214),(210,212),(256,255),(286,272),(316,281),(350,259),(386,249),(420,227),(463,190),(496,174),(521,194),(562,175),(591,169),(619,143),(639,160)],
[(0,221),(26,247),(48,222),(83,251),(125,245),(154,278),(187,287),(220,306),(263,326),(307,343),(348,321),(389,314),(435,290),(480,269),(530,281),(557,254),(593,248),(639,222)],
[(0,280),(60,304),(112,301),(160,323),(210,327),(260,320),(310,322),(355,335),(410,318),(470,326),(520,313),(580,308),(639,295)],
[(0,343),(48,367),(100,352),(149,365),(200,356),(250,370),(302,366),(356,367),(410,357),(470,374),(510,356),(560,344),(609,350),(639,342)],
[(0,400),(45,402),(90,442),(145,431),(189,444),(231,435),(274,427),(320,445),(360,433),(407,449),(450,436),(500,419),(550,429),(599,411),(639,422)]]}
for tower in ['carillon','cendree']:
 P=O/tower;P.mkdir(exist_ok=True);K=P/'intermediaires_magenta';K.mkdir(exist_ok=True)
 src=np.array(load(R/f'source/panoramas_tours_v2/references/{tower}_guide_640.png'));bounds=[curve(p) for p in profiles[tower]]
 # Snap the first contour to the generated mountain/sky chromatic edge near its authored guide.
 for x in range(W):
  expected=bounds[0][x];column=src[max(0,expected-12):expected+15,x,:3].astype(float);r,g,b=column.T;hits=np.where((b>g+3)&(r>g*1.1))[0]
  if len(hits):bounds[0][x]=max(0,expected-12)+hits[0]
 for j in range(1,6):bounds[j]=np.maximum(bounds[j],bounds[j-1]+8)
 if tower=='carillon':sy=[0,70,145,245,365,479];dy=[0,85,149,201,310,479];sunx,suny,radius=320,112,60
 else:sy=[0,90,200,290,400,479];dy=[0,60,142,215,355,479];sunx,suny,radius=322,105,65
 warp=np.rint(np.interp(np.arange(H),dy,sy)).astype(int);a=src[warp];bounds=[np.rint(np.interp(b,sy,dy)).astype(int) for b in bounds];bounds.append(np.full(W,H))
 np.savez_compressed(P/'profils_profondeur.npz',**{f'plan_{j}':v for j,v in enumerate(bounds)})
 # Dusk sky is reconstructed, not a flat crop hiding an inseparable sun.
 stops=[(0,[52,43,78]),(65,[106,65,88]),(130,[202,116,77]),(210,[243,173,88]),(479,[163,107,110])];rgb=np.stack([np.interp(yy//3*3,[s[0] for s in stops],[s[1][c] for s in stops]) for c in range(3)],axis=2)
 sky=image(rgb);dist=np.sqrt((xx-sunx)**2+(yy-suny)**2);halo=image([255,190,77],np.floor(np.clip(1-dist/155,0,1)**2*100/4)*4)
 sycolor=np.clip((yy-(suny-radius))/(2*radius),0,1);sunrgb=np.stack([np.full_like(yy,255),226-70*sycolor,141-82*sycolor],axis=2);sun=image(sunrgb,(dist<=radius)*255)
 moonrgb=np.zeros((H,W,3),float)+[225,231,224];craters=np.zeros((H,W),bool)
 for cx,cy,r in [(sunx-19,suny-20,11),(sunx+18,suny+10,16),(sunx-16,suny+27,8),(sunx+30,suny-24,7)]:craters|=(xx-cx)**2+(yy-cy)**2<r*r
 moonrgb[craters]=[190,204,207];moon=image(moonrgb,(dist<=radius)*255)
 stars=Image.new('RGBA',(W,H));d=ImageDraw.Draw(stars)
 for i in range(75):
  x=int(rng.integers(W));y=int(rng.integers(175))
  if (x-sunx)**2+(y-suny)**2<(radius+14)**2:continue
  d.point((x,y),fill=(224,233,248,int(rng.integers(95,235))))
 layers=[('01_ciel',sky),('02_lueur_astre_ciel',halo),('03_astre',sun),('04_etoiles',Image.new('RGBA',(W,H)))];light_names=['02_lueur_astre_ciel'];base_names=[]
 # Six complete depth planes. Hidden lower extensions are reconstructed from each plane's own visible band.
 names=['montagnes_horizon','montagnes_intermediaires','reliefs_proches','foret_lointaine','foret_vallee','foret_contrebas']
 for j,name in enumerate(names):
  top,following=bounds[j],bounds[j+1];mask=yy>=top[None,:];ar=a.copy();hidden=yy>=following[None,:]
  for x in range(W):
   if following[x]>=H:continue
   band=a[top[x]:following[x],x,:3];color=np.median(band,axis=0);n=H-following[x];grain=((np.arange(n)*13+x*7)%7-3)[:,None];ar[following[x]:,x,:3]=np.clip(color+grain,0,255).astype('uint8')
  ar[~mask]=0;im=keyed(Image.fromarray(ar),K/f'{j:02}_{name}.png');base,light=split_light(im);bn=f'{10+j:02}_{name}';ln=bn+'_lumiere';layers.extend([(bn,base),(ln,light)]);base_names.append(bn);light_names.append(ln)
 # Original cloud planes and exact 64-second wrapping speeds remain independent.
 clouds=[];old=next(m for m in oldmanifest if m['id']==tower+'_boss')
 for i,(name,multiplier) in enumerate(zip(old['animated'],old['multipliers'])):
  im=load(R/f'renders/tours_hooh_v1/{tower}_boss/jour/th1_{tower}_boss_jour_{name}.png');base,light=split_light(im);bn=f'20_nuages_{i}';ln=bn+'_lumiere';layers.extend([(bn,base),(ln,light)]);clouds.extend([dict(name=bn,multiplier=multiplier),dict(name=ln,multiplier=multiplier)]);light_names.append(ln)
 environment_count=len(layers)
 architecture=[]
 for name in old['layers']:
  if int(name[:2])<10:continue
  im=load(R/f'renders/tours_hooh_v1/{tower}_boss/jour/th1_{tower}_boss_jour_{name}.png');ar=np.array(im);alpha=ar[:,:,3].astype(float)/255;lum=ar[:,:,:3].astype(float)@np.array([.299,.587,.114]);inside=alpha>0;edge=inside&~binary_erosion(inside,iterations=2)
  exposure=np.clip(1-abs(xx-sunx)/380,0,1)*(.4+.6*np.clip(lum/150,0,1));strength=(10+24*exposure+edge*19)*alpha
  if 'plancher' in name or 'acces' in name:
   cone=np.clip(1-abs(xx-sunx)/(48+np.maximum(yy-180,0)*.44),0,1);strength=(8+43*cone)*alpha*np.clip((yy-170)/80,0,1)
  light=image([255,194,112],strength);bn='30_'+name;ln=bn+'_lumiere';layers.extend([(bn,im),(ln,light)]);architecture.append(dict(name=bn,source=f'renders/tours_hooh_v1/{tower}_boss/jour/th1_{tower}_boss_jour_{name}.png'));light_names.append(ln)
 # Night substitutes moon, stars, and cold light source colors, THEN applies the exact Abyss filter to every layer.
 for mode in ['jour','nuit']:
  D=P/mode;D.mkdir(exist_ok=True);actual=[];ungraded=[]
  for name,im in layers:
   pre=im.copy()
   if mode=='nuit':
    if name=='03_astre':pre=moon
    elif name=='04_etoiles':pre=stars
    elif name in light_names:
     ar=np.array(pre);ar[ar[:,:,3]>0,:3]=[224,232,245];pre=Image.fromarray(ar)
    ungraded.append((name,pre));im=night(pre)
   actual.append((name,im));im.save(D/f'pt2_{tower}_{mode}_{name}.png')
  merge(actual).save(D/'COMPOSITION.png');merge(actual[:environment_count]).save(D/'PANORAMA_SEUL.png');ora(D/f'pt2_{tower}_{mode}.ora',actual)
  # Lossless audit sources allow the exact night formula to be checked independently even for moon/light substitutions.
  if mode=='nuit':
   import zipfile,io
   with zipfile.ZipFile(P/'sources_nuit_avant_filtre.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name,im in ungraded:
     b=io.BytesIO();im.save(b,format='PNG');z.writestr(name+'.png',b.getvalue())
 manifest.append(dict(id=tower,size=[W,H],layers=[n for n,im in layers],environment_count=environment_count,lights=light_names,architecture=architecture,clouds=clouds,loop_ms=64000,cloud_period_px=640,source_generated=f'source/panoramas_tours_v2/references/{tower}_guide.png',sun=dict(center=[sunx,suny],radius=radius),night='moon and neutral light alternatives, then exact Abyss per layer',hidden_extensions='reconstructed beneath the next foreground plane',reference_vertical_adaptation=dict(source_y=sy,target_y=dy)))
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print([(m['id'],len(m['layers'])) for m in manifest])
