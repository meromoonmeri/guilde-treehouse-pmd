"""Eight generated wall attachments; native fire poses; true indexed-palette light cycle."""
from pathlib import Path
import sys,json,hashlib,zipfile,io,math
import numpy as np
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;R=S.parents[1];O=R/'renders/spinda_torches_v1';sys.path.insert(0,str(S))
from archive import image,entries
DIRS=['N','NE','E','SE','S','SW','W','NW'];LABELS=['Nord · face','Nord-est · trois-quarts','Est · profil','Sud-est · retour','Sud · dos','Sud-ouest · retour','Ouest · profil','Nord-ouest · trois-quarts']
CUPS={'N':(.50,.13),'NE':(.225,.35),'E':(.28,.15),'SE':(.28,.14),'S':(.5,.145),'SW':(.69,.13),'W':(.66,.14),'NW':(.66,.16)}
NORMALS={'N':(0,1),'NE':(-.707,.707),'E':(-1,0),'SE':(-.707,-.707),'S':(0,-1),'SW':(.707,-.707),'W':(1,0),'NW':(.707,.707)}
COUNT=16;MS=100

def sha(b):return hashlib.sha256(b).hexdigest()
def save(im,file):
 p=O/file;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True,**({'lossless':True,'exact':True} if p.suffix=='.webp' else {}));return file

def light_indices(direction):
 yy,xx=np.indices((96,96));dx,dy=NORMALS[direction];x=xx-48;y=yy-48
 # Fixed spatial index texture. Only palette entries change with time.
 field=.76*np.exp(-2*((x/32)**2+(y/29)**2))+.24*np.exp(-2*(((x-dx*10)/32)**2+((y-dy*10)/26)**2))
 levels=np.rint(field*15).astype(int);phase=np.floor(np.hypot(x,y)*.3+(x*dx+y*dy)*.22).astype(int)%16
 return np.where(levels>0,1+(levels-1)*16+phase,0).astype('uint8')

def palette(frame):
 colours=[[0,0,0] for _ in range(256)];alpha=[0]*256
 ring=[]
 for k in range(16):
  t=2*math.pi*k/16;v=(math.sin(t)+.25*math.sin(3*t+.7))/1.25
  ring.append([round(228+25*v),round(169+34*v),round(88+24*v)])
 for level in range(1,16):
  for phase in range(16):
   i=1+(level-1)*16+phase;colours[i]=ring[(phase+frame)%16];alpha[i]=level*2
 return colours,alpha

def cycle_image(indices,frame):
 im=Image.fromarray(indices).convert('P');colours,alpha=palette(frame);im.putpalette([c for rgb in colours for c in rgb]);im.info['transparency']=bytes(alpha);return im

def build():
 O.mkdir(exist_ok=True);objects=[];source_audit=[]
 for direction,label in zip(DIRS,LABELS):
  name='N_front' if direction=='N' else direction;raw=image(S/'raws'/f'{name}.webp');a=np.array(raw);g=a[:,:,1].astype(float);mask=(a[:,:,0]>g*1.4+30)&(a[:,:,2]>g*1.4+30);a[mask]=0;keyed=Image.fromarray(a);box=keyed.getbbox();crop=keyed.crop(box);scale=min(40/crop.width,32/crop.height);size=(round(crop.width*scale),round(crop.height*scale));small=crop.resize(size,Image.Resampling.NEAREST)
  cup=[round(CUPS[direction][i]*size[i]) for i in range(2)];offset=[32-cup[0],44-cup[1]];support=Image.new('RGBA',(64,88));support.paste(small,offset);assert support.getbbox()[2]<64 and support.getbbox()[3]<88
  day=save(support,f'supports/Torche_{direction}_jour.png');b=np.array(support);b[:,:,:3]=np.rint(b[:,:,:3]*[.58,.48,.44]).astype('uint8');night=save(Image.fromarray(b),f'supports/Torche_{direction}_nuit.png')
  indices=light_indices(direction);frames=[];sheet=Image.new('RGBA',(96*16,96))
  for n in range(16):
   im=cycle_image(indices,n);file=save(im,f'lumiere/{direction}/Torche_{direction}_cycle_{n:02}.png');frames.append(file);sheet.paste(im.convert('RGBA'),(96*n,0))
  strip=save(sheet,f'tilesheets/Torche_{direction}_lumiere_16frames.png');idxfile=save(Image.fromarray(indices),f'indices/Torche_{direction}_indices.png')
  objects.append({'id':direction,'label':label,'wall_direction':direction,'inward_normal':list(NORMALS[direction]),'support':{'jour':day,'nuit':night},'support_size':[64,88],'support_anchor':[32,44],'light_anchor':[48,48],'light_size':[96,96],'light_frames':frames,'light_strip':strip,'indices':idxfile,'native':False})
  source_audit.append({'direction':direction,'raw':f'raws/{name}.webp','keyed_bbox':box,'visible_size':size,'placement':offset,'cup_anchor_fraction':CUPS[direction],'resample':'nearest; generated support only','mirrored_or_rotated':False})
 fire=[]
 for n in range(4):
  src=R/f'renders/cafe_spinda_reseau_v4/assets/SpindaV4_flamme_{n:02}.png';file=f'flamme/Torche_flamme_native_{n:02}.png';(O/file).parent.mkdir(exist_ok=True);(O/file).write_bytes(src.read_bytes());im=Image.open(src).convert('RGBA');assert im.size==(32,40);fire.append({'file':file,'sha256':sha(src.read_bytes()),'rgba_sha256':sha(im.tobytes()),'source':str(src.relative_to(R))})
 strip=Image.new('RGBA',(128,40))
 for i,r in enumerate(fire):strip.paste(Image.open(O/r['file']).convert('RGBA'),(32*i,0))
 firestrip=save(strip,'tilesheets/Torche_flamme_native_4poses.png')
 supportstrip=Image.new('RGBA',(64*8,88))
 for i,o in enumerate(objects):supportstrip.paste(Image.open(O/o['support']['jour']),(64*i,0))
 save(supportstrip,'tilesheets/Torches_supports_8angles.png')
 # Night reference only: no modification of the original rooms. Remove V8's static ambient overlay.
 with zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v8/SpindaV8_atelier_lot1.zip') as z:
  v8=json.loads(z.read('manifest.json'));cafe=next(r for r in v8['rooms'] if r['id']=='cafe');background=Image.new('RGBA',(600,448))
  for layer in cafe['modes']['nuit']['layers']:
   if layer['id']!='lumiere_tamisee':background.alpha_composite(Image.open(io.BytesIO(z.read(layer['file']))).convert('RGBA'))
 save(background,'demo/Cafe_nuit_sans_halo_statique.webp')
 placements=[{'direction':'N','x':168,'y':112,'phase':0},{'direction':'N','x':432,'y':112,'phase':5},{'direction':'NW','x':98,'y':148,'phase':10},{'direction':'NE','x':504,'y':148,'phase':15}]
 m={'title':'Torches murales · huit orientations','objects':objects,'light_frames_in_zip_only':True,'frame_count':16,'frame_ms':100,'period_ms':1600,'flame':{'size':[32,40],'anchor':[16,40],'frames':fire,'strip':firestrip,'pose_count':4,'period_ms':400,'native_untransformed':True},'palette':{'file':'palette_cycles.json','index_fixed_across_frames':True,'cycle_rings':15,'ring_length':16,'max_alpha':30,'rgba_strips_available':True},'background':'demo/Cafe_nuit_sans_halo_statique.webp','demo_placements':placements,'demo_only':True,'layer_order':['lumiere','support','flamme'],'source_audit':source_audit,'runtime_PMDO':'NOT TESTED','old_V8_collection':'unchanged; pending furniture/windows/ribbons not completed by this torch set'}
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');(O/'palette_cycles.json').write_text(json.dumps({'transparent_index':0,'index_formula':'1 + (level-1)*16 + phase, level 1..15','animation':'Each 16-entry colour ring is cyclically rotated by one entry per frame. Alpha for each ring stays fixed. No bitmap scrolling or movement.','frame_ms':MS,'frame_count':16,'base_rgba_palette':[[*rgb,al] for rgb,al in zip(*palette(0))],'rings':[{'start':1+(level-1)*16,'length':16,'step_per_frame':1} for level in range(1,16)]},separators=(',',':'))+'\n')
 provenance=json.loads((R/'renders/cafe_spinda_reseau_v4/flammes_provenance.json').read_text());(O/'flammes_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 (O/'index.html').write_text((S/'viewer.html').read_text().replace('__DATA__',json.dumps(m,ensure_ascii=False)))
 # Readable sheet preview, actual normalised sprites; not additional generator output.
 preview=Image.new('RGB',(960,420),'#211b23');d=ImageDraw.Draw(preview)
 for j,o in enumerate(objects):
  x=(j%4)*240;y=(j//4)*190;tile=Image.new('RGBA',(96,96));tile.alpha_composite(cycle_image(light_indices(o['id']),0).convert('RGBA'));tile.alpha_composite(Image.open(O/o['support']['jour']).convert('RGBA'),(16,4));tile.alpha_composite(Image.open(O/fire[0]['file']).convert('RGBA'),(32,8));tile=tile.resize((168,168),Image.Resampling.NEAREST);preview.paste(tile,(x+36,y+20),tile);d.text((x+15,y+5),o['label'],fill='#eac795')
 d.text((18,396),'8 supports generes | flamme native 4 poses | lumiere : 16 frames de palette cycling separees',fill='#cbbb9f');preview.save(O/'Torches_8_orientations.jpg',quality=82)
 (R/'apercu_spinda_torches.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/spinda_torches_v1/index.html"><a href="renders/spinda_torches_v1/index.html">Torches murales animées</a></html>\n')
 # Standalone animated preview; composited illustration, not an import layer.
 animated=[];obj=objects[0];light=Image.open(O/obj['light_strip']).convert('RGBA');body=Image.open(O/obj['support']['nuit']).convert('RGBA')
 for n in range(16):
  frame=Image.new('RGBA',(96,96),'#211b23');frame.alpha_composite(light.crop((n*96,0,(n+1)*96,96)));frame.alpha_composite(body,(16,4));frame.alpha_composite(Image.open(O/fire[n%4]['file']).convert('RGBA'),(32,8));animated.append(frame.resize((192,192),Image.Resampling.NEAREST))
 animated[0].save(O/'Torche_N_animation.webp',save_all=True,append_images=animated[1:],lossless=True,duration=100,loop=0,minimize_size=True)
 files=[p for p in O.rglob('*') if p.is_file() and p.suffix not in ['.zip','.jpg'] and not p.name.startswith('verification')]
 with zipfile.ZipFile(O/'Spinda_torches_8angles_animees.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(files):
   info=zipfile.ZipInfo(str(p.relative_to(O)),(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;raw=p.read_bytes()
   if p.name=='index.html':raw=raw.replace(b'class="button primary" href="Spinda_torches_8angles_animees.zip"',b'hidden class="button primary" href="Spinda_torches_8angles_animees.zip"')
   z.writestr(info,raw,compresslevel=9)
 for p in (O/'lumiere').rglob('*.png'):p.unlink()
 print('Built 8 supports, 4 native poses, 128 indexed light frames, 10 RGBA strips; ZIP bytes:',(O/'Spinda_torches_8angles_animees.zip').stat().st_size)
 return m
if __name__=='__main__':build()
