from pathlib import Path
import sys,json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/corrections_spring_tours_v2';S=O/'sprites';S.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def load(p):return Image.open(p).convert('RGBA')
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def merge(ls,size):
 im=Image.new('RGBA',size)
 for n,l in ls:im.alpha_composite(l)
 return im
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(p,ls,size):
 root=ET.Element('image',w=str(size[0]),h=str(size[1]));stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(n,l) in reversed(list(enumerate(ls))):
   f=f'data/{i}.png';z.writestr(f,png(l));ET.SubElement(stack,'layer',name=n,src=f,x='0',y='0',opacity='1',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(merge(ls,size)))
manifest=[];report={}
# Luminous Spring: preserve the fixed-RGB pulse, remove the opaque cleaning plate underneath it.
V=R/'renders/soleil_spring_v1/spring';OLD=R/'renders/spring_pulsation_v2';P=O/'spring';P.mkdir(exist_ok=True);W=H=600;yy,xx=np.mgrid[:H,:W];mask=(xx>=275)&(xx<325)&(yy<201)
base=load(OLD/'01_decor_escalier.png');a=np.array(base);back=np.zeros_like(a)
for y in range(201):
 for x in range(275,325):
  # Hidden pixels cannot be recovered exactly: use native same-row grass/rock modules above the water,
  # and opposite-side basin samples for the depth rings below. Everything outside the beam is untouched.
  if y<112:back[y,x]=a[y,325+(x-275)%24]
  else:back[y,x]=a[min(399-y,287),x]
back[mask,3]=255;under=Image.fromarray(back);under.save(P/'fond_reconstruit_sous_spectre.png');dur=[83,83,84]*26;max_alpha=0
for mode in ['jour','nuit']:
 D=P/mode;D.mkdir(exist_ok=True);frames=[]
 for f in range(78):
  native=f//2;water=load(V/'02_cycle_3'/f'{native%3:02}.png');light=load(V/'03_cycle_13'/f'{native%13:02}.png');oldbeam=load(OLD/'colonne'/f'{f:02}.png');ar=np.array(oldbeam);original_alpha=ar[:,:,3].copy();ar[:,:,3]=np.rint(ar[:,:,3].astype(float)*.53).astype('uint8');beam=Image.fromarray(ar);max_alpha=max(max_alpha,int(ar[:,:,3].max()))
  assert np.array_equal(ar[:,:,:3],np.array(oldbeam)[:,:,:3]);assert np.all(ar[:,:,3][mask]<255)
  ls=[('01_decor_escalier',base),('02_eau_native',water),('03_lumiere_bassin_native',light),('04_decor_derriere_spectre',under),('05_spectre_translucide',beam)]
  before=merge(ls[:3]+[('ancien_fond',load(OLD/'02_colonne_nettoyee.png')),('ancien_spectre',oldbeam)],(W,H));after=merge(ls,(W,H));assert np.array_equal(np.array(before)[~mask],np.array(after)[~mask])
  if mode=='nuit':ls=[(n,night(im)) for n,im in ls]
  for n,im in ls:
   if f==0 or n in ['02_eau_native','03_lumiere_bassin_native','05_spectre_translucide']:im.save(D/(f'cs2_spring_{mode}_{n}_{f:02}.png' if n in ['02_eau_native','03_lumiere_bassin_native','05_spectre_translucide'] else f'cs2_spring_{mode}_{n}.png'))
  comp=merge(ls,(W,H));frames.append(comp)
  if f==39:comp.save(D/'COMPOSITION.png');ora(D/f'cs2_spring_{mode}.ora',ls,(W,H))
 frames[0].save(D/'ANIMATION.webp',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,minimize_size=True,method=0)
manifest.append(dict(id='spring',size=[600,600],frames=78,durations_ms=dur,still_phase=39,layers=[n for n,im in ls],animated=['02_eau_native','03_lumiere_bassin_native','05_spectre_translucide'],alpha_max=max_alpha,alpha_max_fraction=max_alpha/255,rgb_unchanged=True,reconstructed_background=True))
report['spring']=dict(outside_column_identical_all78frames=True,spectral_rgb_unchanged=True,alpha_max=max_alpha,opaque_plate_replaced=True)
# Apple Woods native material and native tree pixels; recolor foliage only for autumn.
W,H=640,480;yy,xx=np.mgrid[:H,:W];native=np.array(load(R/'Apple_Woods_entrance_TDS.png'))
samples=json.loads((R/'source/corrections_spring_tours_v2/references/pure_materials.json').read_text());grassboxes=samples['grass'];sandboxes=samples['sand']
def tileplate(boxes):
 out=np.zeros((H,W,4),dtype='uint8');rng=np.random.default_rng(109)
 for y in range(0,H,24):
  for x in range(0,W,24):
   sx,sy=boxes[int(rng.integers(len(boxes)))];h=min(24,H-y);w=min(24,W-x);out[y:y+h,x:x+w]=native[sy:sy+h,sx:sx+w]
 return out
grass=tileplate(grassboxes);sand=tileplate(sandboxes)
for i,(x,y) in enumerate(grassboxes):Image.fromarray(native[y:y+24,x:x+24]).save(S/f'apple_herbe_native_{i}.png')
for i,(x,y) in enumerate(sandboxes):Image.fromarray(native[y:y+24,x:x+24]).save(S/f'apple_chemin_natif_{i}.png')
ramp=np.array([[57,43,26],[96,59,29],[145,80,32],[183,111,40],[217,152,55],[245,193,82],[255,222,127]])
trees=[];treeproof=[]
for k,box in enumerate([(74,211,180,316),(362,199,467,304)]):
 x0,y0,x1,y1=box;a=native[y0:y1,x0:x1].copy();h,w=a.shape[:2];ty,tx=np.mgrid[:h,:w];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);cx=[59,49][k];cy=[43,45][k];ellipse=((tx-cx)/39)**2+((ty-cy)/39)**2<1
 leaf=(g>r*.92)&(b<g*.38)&ellipse;leaf=nd.binary_fill_holes(nd.binary_closing(leaf,iterations=1))&ellipse
 trunk=(r>g*1.08)&(b<g*.85)&(ty>65)&(abs(tx-cx)<22);shape=leaf|trunk;a[~shape]=0;original=a.copy();lum=r*.2126+g*.7152+b*.0722
 tree_ramp=ramp if k==0 else np.array([[55,30,27],[89,40,29],[131,57,31],[173,79,37],[214,114,49],[242,150,64],[253,190,97]])
 for c in range(3):a[:,:,c][leaf]=np.rint(np.interp(lum[leaf],[20,55,85,115,150,185,225],tree_ramp[:,c])).astype('uint8')
 assert np.array_equal(a[~leaf],original[~leaf]);im=Image.fromarray(a);im.save(S/f'pommier_automne_{k}.png');Image.fromarray(original).save(S/f'pommier_natif_{k}.png');trees.append(im);treeproof.append(dict(source_box=box,shape='native-pixel foliage/trunk mask',no_resize=True,only_foliage_rgb_changed=True))
def polygon(pts):
 im=Image.new('L',(W,H));ImageDraw.Draw(im).polygon(pts,fill=255);return np.array(im)>0
T=R/'renders/tours_hooh_v1'
for tower in ['carillon','cendree']:
 P=O/f'{tower}_applewoods';P.mkdir(exist_ok=True);a=np.array(load(T/f'{tower}_entree/jour/COMPOSITION.png'))
 if tower=='carillon':arch=polygon([(123,0),(517,0),(522,160),(498,175),(498,285),(419,285),(419,321),(216,321),(216,285),(147,285),(147,174),(120,160)])
 else:
  arch=polygon([(115,0),(526,0),(532,183),(505,184),(505,306),(369,306),(369,341),(260,341),(260,306),(130,306),(130,184),(112,181)])
  r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);arch&=~((((yy<115)&(xx>226)&(xx<432))|(yy<32))&(r>90)&(g>85)&(b<r*.95))
 r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);arch&=~((g>r*.98)&(b<g*.7)&(r<150)&(g>75))
 # Preserve the actual tower pixels. Remove only background pixels caught in the old broad terrain partition.
 architecture=[];covered=np.zeros((H,W),bool)
 for n in ['03_facade','04_porte_escalier','05_poutres_rouge_fonce','06_tuiles_toitures']:
  im=np.array(load(T/f'{tower}_entree/jour'/f'th1_{tower}_entree_jour_{n}.png'));mask=(im[:,:,3]>0)&arch;covered|=mask;architecture.append((n,cut(im,mask)))
 # Keep architectural pieces missed by the original semantic split but inside the new silhouette.
 architecture.append(('06b_socle_complement',cut(a,arch&~covered)))
 center=320+7*np.sin((yy-305)/62);width=np.interp(yy,[0,305,350,480],[140,140,110,92]);path=(abs(xx-center)<width/2)&(yy>=292);path|=arch&(yy>275)&(abs(xx-320)<80)
 groundlayer=Image.fromarray(grass);pathlayer=cut(sand,path);tree_layers=[];clear=nd.binary_dilation(path,iterations=5)
 placements=[]
 for row,root in enumerate([83,175,267,365,463,548]):
  for col,x in enumerate([9,106,535,632]):
   k=(row+col)%2;im=trees[k];ox=x-im.width//2;oy=root-im.height;layer=Image.new('RGBA',(W,H));layer.alpha_composite(im,(ox,oy));ar=np.array(layer);ar[clear]=0;name=f'10_pommier_{row*4+col:02}';tree_layers.append((name,Image.fromarray(ar)));placements.append(dict(name=name,variant=k,xy=[ox,oy]))
 litter=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(litter);rng=np.random.default_rng(14)
 for i in range(130):
  x=int(rng.integers(0,W));y=int(rng.integers(280,H))
  if arch[y,x]:continue
  color=tuple(map(int,ramp[int(rng.integers(2,7))]))+(255,);draw.polygon([(x-2,y),(x,y-1),(x+2,y),(x,y+1)],fill=color)
 # Trees are sorted by depth, with the unchanged tower in front of rear orchard trees.
 rear=tree_layers[:12];front=tree_layers[12:];ls=[('01_herbe_applewoods',groundlayer),('02_chemin_applewoods',pathlayer),('09_feuilles_tombees',litter)]+rear+architecture+front
 # Keep foreground branches away from architecture: all building RGB remains unchanged in the final scene.
 for i,(n,im) in enumerate(ls):
  if n.startswith('10_'):
   ar=np.array(im);ar[arch]=0;ls[i]=(n,Image.fromarray(ar))
 comp=np.array(merge(ls,(W,H)));assert np.array_equal(comp[arch],a[arch])
 Image.fromarray((path*255).astype('uint8')).save(P/'MASQUE_CHEMIN.png');Image.fromarray((arch*255).astype('uint8')).save(P/'MASQUE_ARCHITECTURE_PRESERVEE.png')
 for mode in ['jour','nuit']:
  D=P/mode;D.mkdir(exist_ok=True);layers=[(n,night(im) if mode=='nuit' else im) for n,im in ls]
  for n,im in layers:im.save(D/f'cs2_{tower}_{mode}_{n}.png')
  merge(layers,(W,H)).save(D/'COMPOSITION.png');ora(D/f'cs2_{tower}_{mode}.ora',layers,(W,H))
 manifest.append(dict(id=f'{tower}_applewoods',prefix=f'cs2_{tower}',size=[W,H],frames=1,layers=[n for n,im in ls],animated=[],architecture_pixels_identical=True,trees=placements,native_source='Apple_Woods_entrance_TDS.png',grass_samples=grassboxes,path_samples=sandboxes,tree_provenance=treeproof))
 report[tower]=dict(architecture_identical=True,native_grass_and_path_rgb=True,tree_native_geometry_no_resize=True,autumn_foliage_recolored=True,layer_count=len(ls))
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));(O/'verification_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
