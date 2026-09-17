"""Generated drawings + indexed palette cycling. No deformation of V1/V3/V4 aurora."""
from pathlib import Path
import numpy as np
from PIL import Image
import colorsys,json,io,base64,hashlib,shutil
R=Path(__file__).resolve().parents[2];O=R/'renders/boreales_frames_generees_v5';OLD=R/'renders/arene_glace_large_v3';N=72

def palette(f):
 # 16 cycling hue slots, each with 16 fixed luminosity levels. Closed cool-color wheel.
 return np.array([[round(c*255*(.10+.90*l/15)) for c in colorsys.hsv_to_rgb(.65+.18*np.sin(2*np.pi*(h/16+(f%N)/N)),.90,1)] for h in range(16) for l in range(16)],dtype='uint8')
def extract():
 raw=Image.open(O/'bruts/aurores_8_poses.png').convert('RGB');keys=[];p=Image.new('P',(1,1));p.putpalette(palette(0).ravel().tolist())
 # Generator returned 3x3 (nine actual drawings), NOT the requested 2x4; extract actual grid.
 for i in range(9):
  col,row=i%3,i//3;box=(round(col*raw.width/3)+3,round(row*raw.height/3)+3,round((col+1)*raw.width/3)-3,round((row+1)*raw.height/3)-3)
  im=raw.crop(box);size=(312,round(im.height*312/im.width));im=im.resize(size,Image.Resampling.NEAREST);a=np.array(im);r,g,b=a.astype(float).transpose(2,0,1)
  red=(r>g*1.3)&(r>b*1.3)&(r>75);a[:,:,0]=np.minimum(a[:,:,0],np.maximum(a[:,:,1],a[:,:,2]));alpha=np.rint(np.clip(np.maximum(g,b)/120,0,1)*255).astype('uint8');alpha[red]=0
  # Transparent margins/feather protect repeated edges; no spatial warp or old aurora pixels.
  x=np.arange(im.width);fade=np.minimum(np.clip(x/12,0,1),np.clip((im.width-1-x)/12,0,1));alpha=np.rint(alpha*fade).astype('uint8')
  idx=Image.fromarray(a).quantize(palette=p,dither=Image.Dither.NONE);padded=Image.new('P',(312,208));padded.putpalette(palette(0).ravel().tolist());padded.paste(idx,(0,0));idx=padded;alpha=np.pad(alpha,((0,208-alpha.shape[0]),(0,0)));idx.save(O/'keyframes'/f'pose_{i:02}_indexed.png');Image.fromarray(alpha).save(O/'keyframes'/f'pose_{i:02}_alpha.png')
  keys.append((np.array(idx),alpha));out=palette(0)[np.array(idx)];rgba=np.dstack([out,alpha]);rgba[alpha==0]=0;Image.fromarray(rgba).save(O/'keyframes'/f'pose_{i:02}.png')
 return keys

def tile(keys,f,cycling=True,animate=True):
 pal=palette(f if cycling else 0);canvas=Image.new('RGBA',(936,240));phase=(f%72)/8 if animate else 0;k=int(phase);t=phase-k
 for i in range(3):
  a,aa=keys[(k+i*3)%9];b,ba=keys[(k+1+i*3)%9];alpha=(1-t)*aa.astype(float)+t*ba.astype(float)
  # Premultiplied crossfade between GENERATED drawings, not geometric deformation.
  rgb=((1-t)*pal[a].astype(float)*aa[:,:,None]+t*pal[b].astype(float)*ba[:,:,None])/np.maximum(alpha[:,:,None],1)
  out=np.dstack([np.rint(rgb).astype('uint8'),np.rint(alpha).astype('uint8')]);out[out[:,:,3]==0]=0;canvas.alpha_composite(Image.fromarray(out),(i*312,8))
 return canvas

def uri(im):
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
def build():
 for folder in ['keyframes','animation/frames','review','calques']:(O/folder).mkdir(parents=True,exist_ok=True)
 keys=extract();frames=[tile(keys,f) for f in range(72)]
 for f,im in enumerate(frames):im.save(O/'animation/frames'/f'BorealeGenV5_{f:03}.png')
 (O/'animation/palettes_72.json').write_text(json.dumps([palette(f).tolist() for f in range(72)]))
 def webp(name,ims):ims[0].save(O/'animation'/name,save_all=True,append_images=ims[1:],duration=100,loop=0,lossless=True,method=4)
 webp('dessins_et_palette_cycling.webp',frames);webp('palette_cycling_seule_pose_fixe.webp',[tile(keys,f,animate=False) for f in range(72)])
 for p in (OLD/'calques').glob('*.png'):shutil.copy2(p,O/'calques'/p.name)
 sky=Image.open(OLD/'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA');sky.alpha_composite(Image.open(OLD/'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'));ground=Image.open(OLD/'review/terrain_detoure.png').convert('RGBA')
 def scene(f):
  im=sky.copy();a=np.array(frames[f%72]);im.alpha_composite(Image.fromarray(a[:,:768]));im.alpha_composite(ground);return im
 for f in [0,18,36,54]:scene(f).save(O/'review'/f'scene_{f:02}.png')
 board=Image.new('RGBA',(936,240*3),(10,16,30,255))
 for i,f in enumerate([0,24,48]):board.alpha_composite(frames[f],(0,i*240))
 board.save(O/'review/poses_et_couleurs.png')
 def gif(name,render):
  palette_image=Image.new('RGB',(768,512*4))
  for i,f in enumerate([0,18,36,54]):palette_image.paste(render(f).convert('RGB'),(0,512*i))
  p=palette_image.quantize(colors=256)
  def q(f):return render(f).convert('RGB').quantize(palette=p,dither=Image.Dither.NONE)
  q(0).save(O/'review'/name,save_all=True,append_images=(q(f) for f in range(1,72)),duration=100,loop=0,disposal=1,optimize=False)
 gif('scene_dessins_generes_palette.gif',scene)
 data={'sky':uri(sky),'ground':uri(ground),'frames':[uri(im) for im in frames],'paletteOnly':[uri(tile(keys,f,animate=False)) for f in range(72)]}
 (R/'apercu_boreales_generees_palette_v5.html').write_text((R/'source/boreales_frames_generees_v5/viewer.html').read_text().replace('__DATA__',json.dumps(data)))
 (O/'manifest.json').write_text(json.dumps({'generated_key_drawings':9,'requested_sheet_grid':[2,4],'actual_sheet_grid':[3,3],'intrinsic_frames':72,'frame_ms':100,'cycle_seconds':7.2,'wrap_seconds':28.8,'method':'Nine genuinely image-generated drawings; eight premultiplied dissolve steps between each adjacent pair. No geometric deformation of an old aurora image.','palette_cycling':'256-entry indexed palette:16 cool hue slots x16 fixed brightness levels,72 cyclic palettes. Index/alpha PNGs exported; no geometric changes in palette-only demo.','raw_source_sha256':hashlib.sha256((O/'bruts/aurores_8_poses.png').read_bytes()).hexdigest(),'raw_filename_note':'Filename reflects requested eight poses; actual generated output has nine.','reference':'aurorepmdsky.png; generated adaptation, NOT native pixel-exact art or extracted game animation','terrain_sky':'V3 byte-identical','runtime_PMDO':'NOT TESTED','other_zones_complete':False},indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':build()
