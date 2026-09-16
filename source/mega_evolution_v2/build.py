"""Generated keyframes -> registered RGBA cycles -> optical-flow inbetweens -> GIFs.
No procedural redraw of energy/shell/emblem. No PMDO import claim.
"""
from pathlib import Path
import json, math, hashlib, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
import cv2
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent;OUT=ROOT/'renders/mega_evolution_v2'
for p in [OUT,OUT/'cycles',OUT/'atlases',OUT/'gifs',OUT/'keyframes']:p.mkdir(parents=True,exist_ok=True)
W,H=240,256;GROUND=(120,198);CENTER=(120,186);N=192;SUB=6
rng=np.random.default_rng(564)
def key(im):
 a=np.array(im.convert('RGBA'));r,g,b=[a[:,:,i].astype(float) for i in range(3)]
 mask=(r>160)&(b>160)&(g<85)&(r>2*g)&(b>2*g)
 a[mask]=0
 return Image.fromarray(a)
def blank(size=(W,H)):return Image.new('RGBA',size)
def alpha(im,value):
 im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:round(a*max(0,min(1,value)))));return im
def extract(file,kind):
 im=Image.open(SRC/'generation'/file);cw,ch=im.width//4,im.height//2;frames=[]
 for i in range(8):
  # Generated energy/sphere sheets contain unwanted grid lines; remove the 3px gutters.
  tile=key(im.crop(((i%4)*cw+3,(i//4)*ch+3,(i%4+1)*cw-3,(i//4+1)*ch-3)))
  c=blank((160,160))
  if kind=='sphere':
   box=tile.getbbox();tile=tile.crop(box).resize((80,80),Image.Resampling.NEAREST);c.alpha_composite(tile,(40,40))
  elif kind=='emblem':
   # Use a common cell transform, NOT per-frame particle bounding-box recentering.
   tile=tile.resize((32,48),Image.Resampling.NEAREST);c.alpha_composite(tile,(64,56))
  elif kind=='break':
   # First generated intact sphere has ~92% of cell diameter. Same geometry for every key.
   size=88;tile=tile.resize((size,size),Image.Resampling.NEAREST);c.alpha_composite(tile,((160-size)//2,(160-size)//2))
  else:
   tile=tile.resize((156,156),Image.Resampling.NEAREST);c.alpha_composite(tile,(2,2))
  frames.append(c)
 sheet=blank((160*8,160))
 for i,tile in enumerate(frames):sheet.paste(tile,(160*i,0))
 sheet.save(OUT/'keyframes'/f'MEGAGEN_V2_{kind}_keys.png');return frames

def interpolate(a,b,t,flow_ab,flow_ba):
 aa=np.array(a).astype(np.float32)/255;bb=np.array(b).astype(np.float32)/255
 # Premultiplied alpha prevents a magenta/black matte being blended into the light.
 aa[:,:,:3]*=aa[:,:,3,None];bb[:,:,:3]*=bb[:,:,3,None]
 yy,xx=np.mgrid[:aa.shape[0],:aa.shape[1]].astype(np.float32)
 wa=cv2.remap(aa,xx-flow_ab[:,:,0]*t,yy-flow_ab[:,:,1]*t,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
 wb=cv2.remap(bb,xx-flow_ba[:,:,0]*(1-t),yy-flow_ba[:,:,1]*(1-t),cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
 mix=wa*(1-t)+wb*t;den=np.maximum(mix[:,:,3,None],1/255);mix[:,:,:3]/=den
 return Image.fromarray(np.uint8(np.clip(np.rint(mix*255),0,255)))
def make_cycle(keys,loop=True):
 result=[]
 for i in range(len(keys) if loop else len(keys)-1):
  a=keys[i];b=keys[(i+1)%len(keys)]
  ga=cv2.cvtColor(np.array(a)[:,:,:3],cv2.COLOR_RGB2GRAY);gb=cv2.cvtColor(np.array(b)[:,:,:3],cv2.COLOR_RGB2GRAY)
  args=(None,.5,3,15,3,5,1.2,0)
  fab=cv2.calcOpticalFlowFarneback(ga,gb,*args);fba=cv2.calcOpticalFlowFarneback(gb,ga,*args)
  for j in range(SUB):result.append(a if j==0 else interpolate(a,b,j/SUB,fab,fba))
 if not loop:result.append(keys[-1])
 return result

def gif(frames,path,durations=None):
 # One shared palette for the whole GIF prevents adaptive-palette flicker.
 samples=frames[::max(1,len(frames)//24)];sw,sh=frames[0].size
 montage=Image.new('RGB',(sw*len(samples),sh))
 for i,im in enumerate(samples):montage.paste(im.convert('RGB'),(i*sw,0))
 pal=montage.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 fs=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
 dur=durations or ([30,30,40]*(math.ceil(len(fs)/3)))[:len(fs)]
 fs[0].save(path,save_all=True,append_images=fs[1:],duration=dur,loop=0,optimize=False,disposal=2)

def atlas(frames,path,columns=12):
 w,h=frames[0].size;sheet=blank((w*columns,h*math.ceil(len(frames)/columns)))
 for i,im in enumerate(frames):sheet.paste(im,((i%columns)*w,(i//columns)*h))
 sheet.save(path)

keys={};cycles={}
for name,file in [('energy','01_energy_cycle.png'),('sphere','02_sphere_cycle.png'),('break','03b_shell_break_matched.png'),('emblem','04_emblem_cycle.png')]:
 keys[name]=extract(file,name);cycles[name]=make_cycle(keys[name],name!='break')
 atlas(cycles[name],OUT/'cycles'/f'MEGAGEN_V2_{name}.png',8)
 bg=[]
 for im in cycles[name]:
  c=Image.new('RGBA',(160,160),(18,25,39,255));c.alpha_composite(im);bg.append(c)
 if name=='break':bg += [bg[-1]]*12
 gif(bg,OUT/'gifs'/f'cycle_{name}.gif')
# Semantic masks authored in registered energy-cell coordinates. Preserve exact composite.
# Back columns and top ring arc -> rear; two near columns/impacts -> front; floor arcs -> ground.
yy,xx=np.mgrid[:160,:160]
front=(((xx>=41)&(xx<=69))|((xx>=87)&(xx<=118)))&(yy>=65)
floor=(yy>=109)&~front
rear=~(front|floor)
for name,mask in [('rear',rear),('front',front),('floor',floor)]:Image.fromarray(np.uint8(mask)*255).save(SRC/f'mask_energy_{name}.png')
def split_energy(im):
 arr=np.array(im);result=[]
 for mask in [floor,rear,front]:
  a=arr.copy();a[~mask]=0;result.append(Image.fromarray(a))
 # masks partition pixels exactly; no duplicate highlights.
 assert np.array_equal(sum(np.array(i).astype(np.uint16) for i in result),arr)
 return result

# Characters: native white markers align every direction and phase on the same floor point.
characters=[];character_bounds=[]
for name in ['charizard','mega_charizard_x']:
 p=ROOT/'source/mega_evolution_v1/references'/name
 node=next(n for n in ET.parse(p/'AnimData.xml').findall('.//Anim') if n.findtext('Name')=='Idle')
 w,h=int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'))
 sheet=Image.open(p/'Idle-Anim.png').convert('RGBA');sh=Image.open(p/'Idle-Shadow.png').convert('RGBA');rows=[]
 for d in range(8):
  row=[]
  for f in range(4):
   box=(f*w,d*h,(f+1)*w,(d+1)*h);cell=sheet.crop(box);a=np.array(sh.crop(box));y,x=np.where(np.all(a[:,:,:3]==255,axis=2)&(a[:,:,3]>0));assert len(x)==1
   c=blank();c.alpha_composite(cell,(GROUND[0]-int(x[0]),GROUND[1]-int(y[0])));row.append(c);character_bounds.append(c.getbbox())
  rows.append(row)
 characters.append(rows)

layer_names=['ground','rear_energy','sphere','front_energy','fracture','emblem']
layers_out={n:[] for n in layer_names};previews=[[] for _ in range(8)]
coverage=0;full=[ ]
for f in range(N):
 layers={n:blank() for n in layer_names}
 # Cyclic phases run continuously; authored envelope starts/ends whole transformation.
 e_amp=min(1,f/18)*max(0,min(1,(105-f)/24))
 energy=alpha(cycles['energy'][f%48],e_amp)
 for n,im in zip(['ground','rear_energy','front_energy'],split_energy(energy)):
  layers[n].alpha_composite(im,(GROUND[0]-80,GROUND[1]-112))
 if 30<=f<108:
  orb=cycles['sphere'][(f-30)%48]
  # Growth changes placement envelope, but never stretches an individual opaque hold pose.
  grow=min(1,(f-29)/24);size=max(1,round(160*(.35+.65*grow)))
  orb=orb.resize((size,size),Image.Resampling.NEAREST)
  opacity=min(1,(f-29)/22)
  layers['sphere'].alpha_composite(alpha(orb,opacity),(CENTER[0]-size//2,CENTER[1]-size//2))
 if 96<=f<108:
  # Blend to the generator's first cracking key while both shells hide the actor.
  t=(f-96)/12
  layers['fracture'].alpha_composite(alpha(cycles['break'][0],t),(CENTER[0]-80,CENTER[1]-80))
 if 108<=f<151:
  shard=cycles['break'][min(42,f-108)]
  # World-space radial expansion + generated smaller fragments + progressive alpha loss.
  age=(f-108)/42;size=round(160*(1+.20*max(0,age-.2)));shard=shard.resize((size,size),Image.Resampling.NEAREST)
  fade=min(1,(151-f)/12)
  layers['fracture'].alpha_composite(alpha(shard,fade),(CENTER[0]-size//2,CENTER[1]-size//2))
 if 45<=f<183:
  amp=min(1,(f-45)/18)*min(1,(183-f)/30)
  layers['emblem'].alpha_composite(alpha(cycles['emblem'][(f-45)%48],amp),(CENTER[0]-80,CENTER[1]-80-69))
 # Verify FULL opacity over ALL native sprites during hidden form change, not just one screenshot.
 if 66<=f<=90:
  shell=np.array(layers['sphere'])[:,:,3]
  for form in characters:
   for row in form:
    for im in row:assert np.all(shell[np.array(im)[:,:,3]>0]==255),f'coverage at {f}'
  coverage+=1
 for name in layer_names:layers_out[name].append(layers[name])
 for di in range(8):
  bg=Image.new('RGBA',(W,H),(18,25,39,255));dr=ImageDraw.Draw(bg)
  for x in range(-W,W,24):dr.line((x,152,x+W,232),fill=(27,39,50))
  for x in range(0,W*2,24):dr.line((x,152,x-W,232),fill=(27,39,50))
  for name in ['ground','rear_energy']:bg.alpha_composite(layers[name])
  form=0 if f<78 else 1;bg.alpha_composite(characters[form][di][(f//8)%4])
  for name in ['sphere','front_energy','fracture','emblem']:bg.alpha_composite(layers[name])
  previews[di].append(bg)
for name,fs in layers_out.items():atlas(fs,OUT/'atlases'/f'MEGAGEN_V2_{name}.png')
for di,fs in enumerate(previews):gif(fs,OUT/'gifs'/f'mega_{di}.gif')
# One multidirectional GIF, labels outside native scene, layout 4 columns × 2 rows.
contact_frames=[];dirs=['D','DR','R','UR','U','UL','L','DL']
for f in range(N):
 sheet=Image.new('RGB',(W*4,H*2),(18,25,39))
 for di in range(8):sheet.paste(previews[di][f].convert('RGB'),((di%4)*W,(di//4)*H));ImageDraw.Draw(sheet).text(((di%4)*W+12,(di//4)*H+12),dirs[di],fill='white')
 contact_frames.append(sheet)
gif(contact_frames,OUT/'gifs/mega_8_directions.gif')
story=Image.new('RGB',(W*4,H*2))
for i,f in enumerate([0,24,48,78,102,121,140,176]):story.paste(previews[0][f].convert('RGB'),((i%4)*W,(i//4)*H))
story.save(OUT/'storyboard.png')
# Review layout: rows are the eight gameplay directions, columns are twelve times.
layout=Image.new('RGB',(W*12,H*8))
for di in range(8):
 for col,f in enumerate(range(0,N,16)):
  layout.paste(previews[di][f].convert('RGB'),(col*W,di*H))
layout.save(OUT/'MEGAGEN_V2_directional_layout.png')
(OUT/'directional_layout.json').write_text(json.dumps({'type':'review_only_not_import_atlas','cell':[W,H],'rows':dirs,'columns_frames':list(range(0,N,16))},indent=2)+'\n')

# Loop diagnostics quantify the wrap exactly like other adjacent frame changes (not artistic certification).
seams={}
for name,fs in cycles.items():
 if name=='break':continue
 a=[np.array(im).astype(float) for im in fs];diff=[float(np.mean(np.abs(a[(i+1)%len(a)]-a[i]))) for i in range(len(a))]
 seams[name]={'wrap_mean_rgba_difference':diff[-1],'max_internal_difference':max(diff[:-1]),'mean_internal_difference':float(np.mean(diff[:-1]))}
manifest={'version':2,'source':'image-generator keyframes, RGBA cleanup, registration, bidirectional optical-flow interpolation; NOT native PMDO VFX','frames':N,'ticks_per_frame':2,'duration_ms':6400,'cell':[W,H],'atlas_grid':[12,16],'ground_anchor':GROUND,'sphere_center':CENTER,'directions':dirs,'generated_keys':{k:len(v) for k,v in keys.items()},'cycle_frames':{k:len(v) for k,v in cycles.items()},'layers':layer_names,'form_switch_frame':78,'full_coverage_checks':{'phases':coverage,'forms':2,'directions':8,'native_idle_frames':4,'result':'PASS'},'loop_diagnostics':seams,'multi_direction_note':'same radial VFX camera; 8 native character directions, not 8 independently generated 3D camera angles','limitations':['artistic review still required','optical flow synthesizes inbetweens, not hand-drawn frames','front/rear masks approximate semantic partition of one generated image, not fully separately painted column objects','Ground/Dungeon PMDO playback NOT TESTED','only Charizard/X envelope measured; not universal species-size certification']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
