"""Generated Spinda bunting adapted to existing walls; rugs and a separable Mime Jr stage."""
from pathlib import Path
import sys,json,io,zipfile,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'renders/spinda_decor_v1';sys.path.insert(0,str(S))
from archive import image,entries

def sha(b):return hashlib.sha256(b).hexdigest()
def save(im,path):
 p=O/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True);return path

def key(name):
 raw=image(S/'raws'/f'{name}.webp');a=np.array(raw);g=a[:,:,1].astype(float);a[(a[:,:,0]>g*1.4+30)&(a[:,:,2]>g*1.4+30)]=0
 if name=='rideau_droite':
  # The model added a spurious room to the left. Keep only the requested right wing.
  a[:,:round(raw.width*.767)]=0
 im=Image.fromarray(a);return im.crop(im.getbbox())
def normal(im,canvas,border=2):
 scale=min((canvas[0]-2*border)/im.width,(canvas[1]-2*border)/im.height);size=(round(im.width*scale),round(im.height*scale));small=im.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',canvas);out.paste(small,((canvas[0]-size[0])//2,canvas[1]-size[1]-border));return out

def grade(im):
 a=np.array(im);a[:,:,:3]=np.rint(a[:,:,:3]*[.42,.35,.4]).astype('uint8');return Image.fromarray(a)
def straighten(im):
 a=np.array(im);xs=[];ys=[]
 for x in range(round(im.width*.08),round(im.width*.92)):
  pos=np.flatnonzero(a[:,x,3]);
  if len(pos):xs.append(x);ys.append(int(pos[0]))
 slope=float(np.polyfit(xs,ys,1)[0]);shifts=np.rint(-slope*np.arange(im.width)).astype(int);shifts-=shifts.min();out=Image.new('RGBA',(im.width,im.height+int(shifts.max())))
 for x,y in enumerate(shifts):out.paste(im.crop((x,0,x+1,im.height)),(x,int(y)))
 return out.crop(out.getbbox()),slope

def span(layer,module,start,end,height=24):
 x0,y0=start;x1,y1=end;w=x1-x0;src=module.resize((w,height),Image.Resampling.NEAREST)
 for x in range(w):layer.alpha_composite(src.crop((x,0,x+1,height)),(x0+x,round(y0+(y1-y0)*x/max(1,w-1))))

def build():
 O.mkdir(exist_ok=True);audit={};flat={};assets=[]
 for side in ['gauche','droite']:
  raw=key('banderole_'+side);flat[side],slope=straighten(raw);audit[side]={'slope_removed':slope,'method':'Column shear on generated art to follow wall attachment lines; never applied to native reference.'}
 specs=[('tapis_rectangle',(144,56)),('tapis_ovale',(128,88)),('tapis_couloir',(56,136)),('estrade',(192,80)),('rideau_gauche',(184,128)),('rideau_droite',(88,128))]
 sprites={}
 for name,size in specs:sprites[name]=normal(key(name),size)
 # Both curtain poles share a 120-pixel height; preserve generated proportions.
 for side,size in [('gauche',(184,128)),('droite',(88,128))]:
  im=key('rideau_'+side);im=im.resize((round(im.width*120/im.height),120),Image.Resampling.NEAREST);out=Image.new('RGBA',size);out.paste(im,(2,4));sprites['rideau_'+side]=out
 sprites['banderole_nord']=flat['gauche'].resize((128,32),Image.Resampling.NEAREST)
 for side in ['gauche','droite']:
  out=Image.new('RGBA',(104,88));span(out,flat[side],(4,58) if side=='gauche' else (4,2),(100,2) if side=='gauche' else (100,58),24);sprites['banderole_'+side]=out
 for name,im in sprites.items():
  files={mode:save(img,f'objets/SpindaDecor_{name}_{mode}.png') for mode,img in [('jour',im),('nuit',grade(im))]};assets.append({'id':name,'files':files,'size':list(im.size),'native':False,'generated':True,'bbox':list(im.getbbox())})
 # Original canonical reference kept byte-for-byte, not relabelled generated/native-adapted.
 native=R/'renders/cafe_spinda_revisite_v7/assets/SpindaV7_ruban_spinda.png';(O/'references').mkdir(exist_ok=True);(O/'references/ruban_spinda_natif.png').write_bytes(native.read_bytes())
 stage_positions={'estrade':[8,104],'rideau_gauche':[8,0],'rideau_droite':[112,0]};stage=Image.new('RGBA',(208,184));stage_layers=[]
 for name in ['estrade','rideau_gauche','rideau_droite']:
  im=Image.new('RGBA',stage.size);im.alpha_composite(sprites[name],tuple(stage_positions[name]));files={mode:save(pic,f'estrade/SpindaDecor_{name}_aligne_{mode}.png') for mode,pic in [('jour',im),('nuit',grade(im))]};stage.alpha_composite(im);stage_layers.append({'id':name,'files':files,'position':stage_positions[name]})
 save(stage,'apercus/SpindaDecor_estrade_assemblee.png')
 rooms=[];room_previews=[];basez=zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip');m7=json.loads(basez.read('manifest.json'))
 for r in m7['rooms']:
  day=Image.new('RGBA',(600,448));window=np.zeros((448,600),bool)
  for l in r['layers']:
   im=Image.open(io.BytesIO(basez.read(l['file']))).convert('RGBA');day.alpha_composite(im)
   if l['id']=='fenetres':window=np.array(im)[:,:,3]>0
  b=Image.new('RGBA',(600,448));paths=[('gauche',(80,158),(168,104)),('droite',(432,104),(520,158))]
  if r['id'] in ['accueil','casino']:paths += [('gauche',(168,104),(232,104)),('droite',(368,104),(432,104))]
  else:paths += [('gauche',(168,104),(300,104)),('droite',(300,104),(432,104))]
  for side,p0,p1 in paths:span(b,flat[side],p0,p1,24)
  a=np.array(b);assert not ((a[:,:,3]>0)&window).any();assert not ((a[:,:,3]>0)&(np.array(day)[:,:,3]==0)).any()
  if r['id'] in ['accueil','casino']:assert not a[:192,232:368,3].any()
  for port in r['ports'].values():
   x,y=port['point'];assert not a[max(0,y-16):y+17,max(0,x-16):x+17,3].any()
  files={mode:save(pic,f'banderoles/SpindaDecor_{r["id"]}_banderoles_{mode}.png') for mode,pic in [('jour',b),('nuit',grade(b))]};composite=day.copy();composite.alpha_composite(b);room_previews.append((r['id'],composite));rooms.append({'id':r['id'],'files':files,'paths':[{'source':s,'start':p0,'end':p1} for s,p0,p1 in paths],'windows_untouched':True,'ports_clear':True})
  if r['id']=='cafe':
   scene=composite.copy();scene.alpha_composite(sprites['tapis_rectangle'],(232,280));scene.alpha_composite(stage,(200,104));assert np.array_equal(np.array(scene)[:,:,3],np.array(day)[:,:,3]);save(scene,'apercus/SpindaDecor_cafe_demonstration.png')
 # Unplaced library sheet; no accidental baked furniture in maps.
 sheet=Image.new('RGBA',(512,400));coords=[];x=y=8;rh=0
 for name,im in sprites.items():
  if x+im.width+8>512:x=8;y+=rh+8;rh=0
  sheet.alpha_composite(im,(x,y));coords.append({'id':name,'rect':[x,y,*im.size]});x+=im.width+8;rh=max(rh,im.height)
 assert y+rh<=400;save(sheet,'tilesheets/SpindaDecor_objets_tilesheet.png')
 preview=Image.new('RGB',(1024,800),'#28212a');d=ImageDraw.Draw(preview);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
 for rec in coords:
  x,y,w,h=rec['rect'];obj=sprites[rec['id']].resize((w*2,h*2),Image.Resampling.NEAREST);preview.paste(obj,(x*2,y*2),obj)
 d.text((20,776),'Banderoles adaptées • tapis rouges • estrade + deux rideaux — calques séparés',font=font,fill='#eed7b0');save(preview,'apercus/SpindaDecor_collection.png')
 board=Image.new('RGB',(1200,960),'#28212a');d=ImageDraw.Draw(board)
 for i,(name,im) in enumerate(room_previews):
  x=i%2*600;y=i//2*320;thumb=im.resize((420,314),Image.Resampling.NEAREST);board.paste(thumb,(x+90,y),thumb);d.text((x+12,y+12),name,font=font,fill='#eed7b0')
 # A compact audit sheet; room layers themselves stay at 600x448.
 board.save(O/'apercus/SpindaDecor_banderoles_5salles.webp',lossless=True,method=6)
 audit7=json.loads((R/'renders/cafe_spinda_revisite_v7/audit/native_sizes.json').read_text());reference={'file':'references/ruban_spinda_natif.png','sha256':sha(native.read_bytes()),'source':audit7['sources']['SpindaCafe2'],'crop':[240,56,304,96],'native_reference_unchanged':True,'adapted_outputs_are_native':False}
 manifest={'version':'Spinda décors V1','assets':assets,'room_layers':rooms,'stage':{'canvas':[208,184],'layers':stage_layers,'independent_left_and_right':True},'tilesheet':{'file':'tilesheets/SpindaDecor_objets_tilesheet.png','grid':8,'rects':coords},'reference':reference,'adaptation':audit,'generation_attempts':10,'rejected':['banderole_nord','banderole_nord_v2'],'accepted_generated_images':8,'cleanup':{'rideau_droite':'Crop unwanted room fragment at x < 76.7% of raw width. No room pixels retained.','front_garland':'Derived from retained generated diagonal, rectified, then conformed to wall paths. Both clipped front attempts excluded.'},'demo_only':['stage and red rug placement in café preview'],'native_layouts_modified':False,'runtime_PMDO':'NOT TESTED','previous_pending':'Other V8 furniture and regenerated windows remain pending.'}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (O/'README.md').write_text((S/'README.md').read_text())
 with zipfile.ZipFile(O/'Spinda_banderoles_tapis_estrade.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(O.rglob('*')):
   if not p.is_file() or p.suffix=='.zip' or 'apercus' in p.parts or p.name.startswith('verification'):continue
   info=zipfile.ZipInfo(str(p.relative_to(O)),(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
 print('Built:',len(assets),'independent objects,5 fitted wall layers in day/night,3 aligned stage layers,3 red rugs')
 return manifest
if __name__=='__main__':build()
