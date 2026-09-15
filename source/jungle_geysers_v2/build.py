from pathlib import Path
import sys,json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/jungle_geysers_v2';S=O/'sprites';S.mkdir(parents=True,exist_ok=True);W,H=648,504;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
def load(p):return Image.open(p).convert('RGBA')
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def full(im,xy):
 a=Image.new('RGBA',(W,H));a.alpha_composite(im,xy);return a
def merge(ls):
 a=Image.new('RGBA',(W,H))
 for n,im in ls:a.alpha_composite(im)
 return a
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(p,ls):
 root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(n,im) in reversed(list(enumerate(ls))):
   f=f'data/{i}.png';z.writestr(f,png(im));ET.SubElement(stack,'layer',name=n,src=f,x='0',y='0',opacity='1',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(merge(ls)))
# Generated four-pose plume sheet, fixed shared canvas; drop drawn nozzle stubs, removed by same crop in every pose.
raw=key(load(O/'bruts/geyser_4poses_magenta.png'));rw,rh=raw.size;plumes=[]
for p in range(4):
 im=raw.crop((p*rw//4,0,(p+1)*rw//4,round(rh*.935))).resize((96,184),NN);a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);jet=(g>r*1.12)&(g>100)&(a[:,:,3]>0);vapor=(a[:,:,3]>0)&~jet
 ls=[cut(a,jet),cut(a,vapor)];plumes.append(ls)
 for typ,l in zip(['jet','vapeur'],ls):l.save(S/f'geyser_gen_{typ}_{p}.png')
# Canonical Southern Jungle side frames, no scaling/recoloring; only ground-colored transparency removed.
native=np.array(load(R/'Southern_Jungle_entrance_S.png'));ground=native[100,native.shape[1]//2,:3].astype(int);remove=np.max(abs(native[:,:,:3].astype(int)-ground),axis=2)<=5;native[remove]=0;left=Image.fromarray(native[:,:180]);right=Image.fromarray(native[:,-180:]);left.save(S/'southern_jungle_cadre_gauche_natif.png');right.save(S/'southern_jungle_cadre_droit_natif.png')
# Elliptical extraction bounds measured on generated layout; actual impact anchors, not prompt coordinates.
settings={
 'clairiere':[(324,255,(271,215,377,296)),(170,171,(135,149,204,200)),(486,171,(452,149,522,200)),(171,350,(140,329,206,379)),(483,350,(451,326,518,380))],
 'clairiere_grotte':[(324,254,(284,224,367,291)),(201,195,(183,181,218,212)),(449,195,(432,181,467,212)),(201,333,(183,318,219,351)),(449,333,(431,318,468,351))]}
dur=[333,334,333]*4;seq=[0,0,0,1,1,2,2,2,3,3,1,0];entries=[]
for zone,points in settings.items():
 P=O/zone;P.mkdir(exist_ok=True);original=load(O/'bruts'/f'{zone}.png').resize((W,H),NN);a=np.array(original);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);ventmasks=[]
 for x,y,box in points:
  l,t,rr,bb=box;cx=(l+rr)/2;cy=(t+bb)/2;ellipse=((xx-cx)/((rr-l)/2))**2+((yy-cy)/((bb-t)/2))**2<=1.05;ventmasks.append(ellipse&(r>g*.86)&(b<g*.93))
 vents=np.logical_or.reduce(ventmasks);cave=np.zeros((H,W),bool)
 if zone.endswith('grotte'):
  cave=(yy<155)&(xx>143)&(xx<511)&(r>g*.84)&(b<g*.94)
 veg=nd.binary_fill_holes(nd.binary_closing(((g>r*1.25)&(g<133))|((r<35)&(g<60)),iterations=1));veg&=~(vents|cave)
 path=(r>95)&(g>100)&(b<g*.85)&~(veg|vents|cave)
 # Reconstruct hidden ground from nearest visible original ground pixels, not transparent holes.
 hidden=veg|path|vents|cave;idx=nd.distance_transform_edt(hidden,return_distances=False,return_indices=True);ground_a=a.copy();ground_a[hidden]=a[idx[0][hidden],idx[1][hidden]]
 static=[('01_sol_reconstitue',Image.fromarray(ground_a)),('02_chemins_assortis',cut(a,path)),('03_roche_grotte',cut(a,cave))]
 for name,mask in [('04_vegetation_fond',veg&(yy<180)),('05_vegetation_gauche',veg&(yy>=180)&(xx<W//2)),('06_vegetation_droite',veg&(yy>=180)&(xx>=W//2))]:static.append((name,cut(a,mask)))
 base_no_native=static+[(f'vent_{i}',cut(a,mask)) for i,mask in enumerate(ventmasks)];assert np.array_equal(np.array(merge(base_no_native)),a)
 # Native frame behind independent vent/effect layers; clip only where access and vent clearance require it.
 keep=~nd.binary_dilation(vents|path,iterations=3)
 for n,im,pos in [('07_cadre_pmd_natif_gauche',left,(0,H-left.height)),('08_cadre_pmd_natif_droit',right,(W-right.width,H-right.height))]:
  arr=np.array(full(im,pos));arr[~keep]=0
  # Taper only the added top edge to avoid a rectangular cut across the generated canopy. Native RGB unchanged.
  ramp=np.clip((yy-pos[1])/32,0,1);arr[:,:,3]=np.rint(arr[:,:,3]*ramp).astype('uint8');arr[arr[:,:,3]==0]=0;static.append((n,Image.fromarray(arr)))
 nozzles=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(nozzles)
 for i,(x,y,box) in enumerate(points):
  radius=7 if i==0 else 3;draw.ellipse((x-radius,y-3,x+radius,y+3),fill=(37,43,31,255))
 static.append(('08b_orifices_emission',nozzles))
 front=[]
 for i,((x,y,box),mask) in enumerate(zip(points,ventmasks)):
  static.append((f'09_bouche_geyser_{i}',cut(a,mask&(yy<y+5))));front.append((f'12_rebord_avant_{i}',cut(a,mask&(yy>=y+5))))
 for n,im in static+front:im.save(S/f'{zone}_{n}.png')
 frames={};offsets=[0,2,7,4,9];order=[]
 for mode in ['jour','nuit']:
  D=P/mode;D.mkdir(exist_ok=True);frames[mode]=[]
  for p in range(12):
   ls=static.copy()
   for i,(x,y,box) in enumerate(points):
    pose=seq[(p+offsets[i])%12];scale=1 if i==0 else (.48 if zone=='clairiere' else .38)
    for typ,im in zip(['10_jet','11_vapeur'],plumes[pose]):
     im=im.resize((round(96*scale),round(184*scale)),NN);ls.append((f'{typ}_{i}',full(im,(x-im.width//2,y-im.height+2))))
   ls+=front
   if mode=='nuit':ls=[(n,night(im)) for n,im in ls]
   for n,im in ls:
    if p==0 or n.startswith(('10_','11_')):im.save(D/(f'jgv2_{zone}_{mode}_{n}_{p:02}.png' if n.startswith(('10_','11_')) else f'jgv2_{zone}_{mode}_{n}.png'))
   comp=merge(ls);assert np.all(np.array(comp)[:,:,3]==255);comp.save(D/f'jgv2_{zone}_{mode}_composition_{p:02}.png');frames[mode].append(comp)
   if p==0:comp.save(D/'COMPOSITION.png');ora(D/f'jgv2_{zone}_{mode}.ora',ls);order=[n for n,im in ls]
  frames[mode][0].save(D/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,loop=0,lossless=True)
 # Verify exact per-layer night; compositing partial alpha can differ from filtering a flattened scene.
 for f in (P/'jour').glob('jgv2_*.png'):
  if 'composition_' not in f.name:assert np.array_equal(np.array(load(P/'nuit'/f.name.replace('_jour_','_nuit_'))),np.array(night(load(f))))
 entry=dict(id=zone,size=[W,H],frames=12,durations_ms=dur,layer_order=order,animated=[n for n in order if n.startswith(('10_','11_'))],points=points,pose_sequence=seq,phase_offsets=offsets,original_partition_exact=True,native_frames='Southern_Jungle_entrance_S.png; native RGB at1:1, ground key/clearance clipping and32px top alpha transition',generated='background/layout, vent geometry and four jet/vapor poses',runtime_validated=False);entries.append(entry);(P/'manifest.json').write_text(json.dumps(entry,indent=2));print(zone,len(order),'layers,5geysers')
(O/'manifest.json').write_text(json.dumps(entries,indent=2))
