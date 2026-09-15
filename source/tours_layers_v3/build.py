from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
R=Path(__file__).resolve().parents[2];S=R/'source/tours_layers_v3';O=R/'renders/tours_layers_v3';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/tours_saisons_v1'));from common import load,night,merge,ora
W,H=640,480;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W];manifest=[]
def blank():return Image.new('RGBA',(W,H))
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);a[(r>90)&(b>80)&(g<110)&(r>g*1.8)&(b>g*1.8)]=0;return Image.fromarray(a)
def cut(im,mask):
 a=np.array(im);a[~mask]=0;return Image.fromarray(a)
def alpha_scale(im,factor):
 a=np.array(im);a[:,:,3]=np.rint(a[:,:,3].astype(float)*factor).clip(0,255).astype('uint8');return Image.fromarray(a)
def export(project,layers_by_mode,animated_by_mode):
 p=O/project['id'];p.mkdir(exist_ok=True);project['modes']={};project['layers']=[n for n,im in layers_by_mode['jour']]
 for mode,ls in layers_by_mode.items():
  d=p/mode;d.mkdir(exist_ok=True);prefix=f'tl3_{project["id"]}_{mode}';anims=animated_by_mode[mode];project['modes'][mode]={}
  for name,im in ls:
   frames=anims.get(name,[im]);paths=[]
   for f,img in enumerate(frames):
    path=d/(f'{prefix}_{name}_{f:03}.png' if name in anims else f'{prefix}_{name}.png');img.save(path);paths.append(str(path.relative_to(O)))
   project['modes'][mode][name]=dict(files=paths,frame_ms=125 if name in anims else 0)
   if name in anims:
    frames[0].save(d/f'{prefix}_{name}.webp',save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True,method=0)
  merge(ls).save(d/'COMPOSITION.png');ora(d/f'{prefix}.ora',ls)
  if project['kind']=='arene':merge(ls[:project['environment_count']]).save(d/'PANORAMA_SEUL.png')
 manifest.append(project)
# Generator produced the architecture, ground, and tree sheet separately.
sheet=key(load(S/'references/arbres_automne_gen.png'));trees=[];sp=O/'sprites';sp.mkdir(exist_ok=True)
for k in range(4):
 w,h=sheet.size;im=sheet.crop((k%2*w//2,k//2*h//2,(k%2+1)*w//2,(k//2+1)*h//2));im=im.crop(im.getbbox()).resize((88,92),NN);im.save(sp/f'tl3_arbre_genere_{k}.png');trees.append(im)
# Tiny authored leaves: 2-3 pixels, measured against a native 17x21 visible Bulbasaur sprite.
leaf_colors=[(234,169,58,255),(186,90,37,255),(241,204,104,255),(140,70,38,255)]
def leaf_sprite(phase,color):
 im=Image.new('RGBA',(3,3));d=ImageDraw.Draw(im)
 if phase%4==0:d.point((0,0),fill=color);d.line((1,0,1,2),fill=color);d.point((2,1),fill=color)
 elif phase%4==1:d.line((1,0,1,2),fill=color)
 elif phase%4==2:d.line((0,1,2,1),fill=color);d.point((1,0),fill=color)
 else:d.line((0,0,1,1),fill=color);d.point((1,2),fill=color)
 return im
for k,c in enumerate(leaf_colors):
 for f in range(4):leaf_sprite(f,c).save(sp/f'tl3_feuille_{k}_{f}.png')
for ti,t in enumerate(['carillon','cendree']):
 raw=load(S/f'references/{t}_sol_gen.png').resize((W,H),NN);a=np.array(raw);rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);soil=(r>g*1.12)&(g>b*1.12)&(r>185)&(g>115)&(b>65)&(abs(xx-320)<175);components,n=label(soil);counts=np.bincount(components.ravel());counts[0]=0;soil=components==counts.argmax()
 # Rebuild a fully independent grass plate under the extracted path, including its colored fringe.
 clear=binary_dilation(soil,iterations=24);ground=a.copy()
 for y in range(H):
  for x in np.where(clear[y])[0]:ground[y,x]=a[y,144+(x%32)]
 path=blank();pa=np.zeros_like(a);corridor=np.zeros((H,W),bool)
 for y in range(H):
  ids=np.where(soil[y])[0]
  if len(ids)<5:continue
  left=max(0,ids[0]-16);right=min(W,ids[-1]+17);width=round(106+28*(1-y/H)+4*math.sin(y/45));center=round(320+4*math.sin(y/75));dest_left=center-width//2
  strip=raw.crop((left,y,right,y+1)).resize((width,1),NN);pa[y,dest_left:dest_left+width]=np.array(strip)[0];corridor[y,dest_left:dest_left+width]=True
 pa[yy<300]=0;corridor[yy<300]=False;path=Image.fromarray(pa)
 building=key(load(S/f'references/{t}_architecture_gen.png')).resize((W,H),NN);ba=np.array(building);arch=ba[:,:,3]>0
 shadow=blank();shift=blank();shift.alpha_composite(building,(4,8));sa=np.array(shift);sa[:,:,:3]=[12,23,18];sa[:,:,3]=np.rint(sa[:,:,3]*.28).astype('uint8');shadow=Image.fromarray(sa)
 tree_layers=[];placements=[];tree_shadow=blank();sd=ImageDraw.Draw(tree_shadow);rng=np.random.default_rng(811+ti)
 for row,root in enumerate([66,144,226,312,399,491]):
  for col,x0 in enumerate([14,99,541,626]):
   x=x0+int(rng.integers(-7,8));y=root+int(rng.integers(-7,8));k=(row+col+ti)%4;im=blank();im.alpha_composite(trees[k],(x-44,y-92));im=cut(im,~arch&~binary_dilation(corridor,iterations=4));name=f'20_arbre_{row*4+col:02}';tree_layers.append((name,im));placements.append(dict(name=name,variant=k,xy=[x-44,y-92]));sd.ellipse((x-25,y-8,x+24,y+5),fill=(18,31,20,65))
 # Geometric/color-guided architecture partitions: they reassemble the generated sprite exactly.
 partitions=[];claimed=np.zeros((H,W),bool)
 roof=arch&(yy<(162 if t=='carillon' else 162));partitions.append(('30_toitures',roof));claimed|=roof
 stairs=arch&(yy>=(247 if t=='carillon' else 279))&(abs(xx-320)<64);partitions.append(('32_escalier',stairs));claimed|=stairs
 door=arch&(xx>=275)&(xx<=369)&(yy>=162)&(yy<247);partitions.append(('33_porte',door&~claimed));claimed|=door
 posts=arch&(((xx>=218)&(xx<252))|((xx>385)&(xx<420)))&~claimed;partitions.append(('34_poutres',posts));claimed|=posts
 partitions.append(('31_facade_socle',arch&~claimed));architecture=[(name,cut(building,mask)) for name,mask in partitions]
 test=merge(architecture);assert np.array_equal(np.array(test),ba)
 # Two transparent particle planes, with a mathematically periodic 16-second motion.
 params=[]
 for plane,count in [('10_feuilles_arriere',24),('40_feuilles_avant',20)]:
  ps=[dict(x=int(rng.integers(W)),y=int(rng.integers(H)),sway=int(rng.integers(6,18)),phase=float(rng.random()*math.tau),color=int(rng.integers(4)),flutter=int(rng.integers(4))) for _ in range(count)];params.append(dict(name=plane,particles=ps))
 def leaves(group,f):
  im=blank();u=(f%128)/128
  for particle in group['particles']:
   x=round(particle['x']+particle['sway']*math.sin(math.tau*u+particle['phase']))%W;y=round(particle['y']+H*u)%H;sprite=leaf_sprite(f//4+particle['flutter'],leaf_colors[particle['color']])
   for dx in [0,-W]:
    for dy in [0,-H]:im.alpha_composite(sprite,(x+dx,y+dy))
  return im
 animations={p['name']:[leaves(p,f) for f in range(128)] for p in params}
 for p in params:assert np.array_equal(np.array(leaves(p,0)),np.array(leaves(p,128)))
 litter=blank();ld=ImageDraw.Draw(litter)
 for i in range(65):
  x=int(rng.integers(W));y=int(rng.integers(270,H))
  if not arch[y,x]:litter.alpha_composite(leaf_sprite(i,leaf_colors[i%4]),(x,y))
 ls=[('01_herbe',Image.fromarray(ground)),('02_chemin',path),('03_ombres_arbres',tree_shadow),('04_feuilles_sol',litter),('05_ombre_tour',shadow),('10_feuilles_arriere',animations['10_feuilles_arriere'][0])]+tree_layers[:12]+architecture+tree_layers[12:]+[('40_feuilles_avant',animations['40_feuilles_avant'][0])]
 modes={'jour':ls,'nuit':[(n,night(im)) for n,im in ls]};anims={'jour':animations,'nuit':{n:[night(im) for im in frames] for n,frames in animations.items()}}
 proj=dict(id=t+'_entree',title='Tour '+('Carillon' if ti==0 else 'Cendrée')+' · Entrée',kind='entree',size=[W,H],environment_count=0,lights=[],clouds=[],leaf_size_max_px=3,leaf_loop_ms=16000,leaf_parameters=params,trees=placements,architecture_generated=True,architecture_parts=[n for n,im in architecture],generated_references=[str((S/f'references/{t}_architecture_gen.png').relative_to(R)),str((S/f'references/{t}_sol_gen.png').relative_to(R)),str((S/'references/arbres_automne_gen.png').relative_to(R))])
 p=O/proj['id'];p.mkdir(exist_ok=True);building.save(p/'ARCHITECTURE_GENEREE_DETOUREE.png');Image.fromarray((corridor*255).astype('uint8')).save(p/'MASQUE_CHEMIN.png');export(proj,modes,anims)
# Arenas: retain all independent panorama/forest/architecture layers. Replace moon and animate solar disk separately.
V=R/'renders/panoramas_tours_v2';old=json.loads((V/'manifest.json').read_text());moon_source=load(R/'renders/references_calques_v2/astres/lune.png');moon_crop=moon_source.crop(moon_source.getbbox());halo_box=(660,75,840,255)
for m in old:
 t=m['id'];cx,cy=m['sun']['center'];diam=2*m['sun']['radius']+1;moon=blank();moon.alpha_composite(moon_crop.resize((diam,diam),NN),(cx-diam//2,cy-diam//2));halo_size=round(180*diam/108)
 modes={};anims={}
 for mode in ['jour','nuit']:
  ls=[];an={}
  for name in m['layers']:
   im=load(V/t/mode/f'pt2_{t}_{mode}_{name}.png')
   if name=='03_astre':
    if mode=='jour':
     frames=[alpha_scale(im,(239.5+15.5*math.cos(math.tau*f/64))/255) for f in range(64)];ls.append(('03_soleil',frames[0]));an['03_soleil']=frames;ls.append(('03_lune',blank()))
    else:ls.extend([('03_soleil',blank()),('03_lune',moon)])
    continue
   if name=='02_lueur_astre_ciel':
    if mode=='jour':frames=[alpha_scale(im,.80+.20*math.cos(math.tau*f/64)) for f in range(64)]
    else:
     frames=[]
     for f in range(64):
      native=load(R/f'renders/references_calques_v2/astres/halo/{f:02}.png').crop(halo_box).resize((halo_size,halo_size),NN);frame=blank();frame.alpha_composite(native,(cx-halo_size//2,cy-halo_size//2));frames.append(frame)
    an[name]=frames;im=frames[0]
   ls.append((name,im))
  modes[mode]=ls;anims[mode]=an
 proj=dict(id=t+'_arene',title='Tour '+('Carillon' if t=='carillon' else 'Cendrée')+' · Arène',kind='arene',size=[W,H],environment_count=m['environment_count']+1,lights=m['lights'],clouds=m['clouds'],loop_ms=64000,solar_loop_ms=8000,sun=m['sun'],astro_diameter_px=diam,moon_source='renders/references_calques_v2/astres/lune.png',moon_native_crop=list(moon_source.getbbox()),moon_resize='nearest, RGB and texture preserved; no second night filter',night_emissive_exceptions=['03_lune','02_lueur_astre_ciel'],previous_panorama='renders/panoramas_tours_v2/'+t,architecture=m['architecture'])
 export(proj,modes,anims)
# Native-scale comparison, not a guessed Pokemon silhouette; this sprite is reference-only.
poke=load(S/'references/bulbasaur_idle_1x.png');scale=Image.new('RGBA',(224,72),(25,31,30,255));d=ImageDraw.Draw(scale);d.text((6,4),'Bulbizarre natif / feuilles 1x',fill='white');scale.alpha_composite(poke,(20,25))
for i in range(8):scale.alpha_composite(leaf_sprite(i,leaf_colors[i%4]),(75+i*16,43))
scale.save(O/'ECHELLE_FEUILLES_1X.png');scale.resize((896,288),NN).save(O/'ECHELLE_FEUILLES_4X.png')
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print([(m['id'],len(m['layers'])) for m in manifest])
