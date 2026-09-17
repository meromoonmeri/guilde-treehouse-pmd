"""Animate the aurora itself, independently of horizontal background scrolling."""
from pathlib import Path
import json,math,io,base64,zipfile
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];OLD=R/'renders/arene_glace_large_v3';O=R/'renders/arene_boreales_v4';N=88;DT=100

def motion(frame):
 a=np.array(Image.open(OLD/'animation/AreneLargeV3_Aurore_Wrap792.png').convert('RGBA'));h,w=a.shape[:2];y,x=np.mgrid[:h,:w];p=2*math.pi*(frame%N)/N
 # Periodic travelling folds, different horizontal/vertical phases and depth-dependent sway.
 dx=9*np.sin(2*math.pi*x/w*6+p)+5*np.sin(y/31-2*p+2*math.pi*x/w*3)
 dy=13*np.sin(2*math.pi*x/w*3-2*p)+6*np.sin(2*math.pi*x/w*9+p)
 # Breathing height plus travelling folds: definitely not a rigid translation.
 stretch=1+.09*np.sin(2*math.pi*x/w*3+p)
 sx=np.rint(x+dx).astype(int)%w;sy=np.rint((y-85)/stretch+85+dy).astype(int)
 valid=(sy>=0)&(sy<h);out=a[np.clip(sy,0,h-1),sx].copy()
 shimmer=.74+.16*np.sin(p*2+2*math.pi*x/w*18-y/26)+.10*np.sin(p*3-2*math.pi*x/w*39)
 out[:,:,3]=np.rint(out[:,:,3]*np.clip(shimmer,.42,1)*valid).astype('uint8');out[out[:,:,3]==0]=0
 return Image.fromarray(out)
def viewport(im,f,wrap=True):
 a=np.array(im);return Image.fromarray(a[:,(np.arange(768)+(3*(f%264) if wrap else 0))%792])
def uri(im):
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
def build():
 for folder in ['animation/frames','calques','review']:(O/folder).mkdir(parents=True,exist_ok=True)
 import shutil
 for path in (OLD/'calques').glob('*.png'):shutil.copy2(path,O/'calques'/path.name)
 frames=[motion(f) for f in range(N)]
 for f,im in enumerate(frames):im.save(O/'animation/frames'/f'AuroreV4_{f:03}.png')
 frames[0].save(O/'animation/aurore_sans_defilement.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True,method=4)
 terrain=Image.open(OLD/'review/terrain_detoure.png').convert('RGBA');sky=Image.open(OLD/'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA');sky.alpha_composite(Image.open(OLD/'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'))
 def scene(f,wrap=True):
  im=sky.copy();im.alpha_composite(viewport(frames[f%N],f,wrap));im.alpha_composite(terrain);return im
 for f in [0,22,44,66]:scene(f,False).save(O/'review'/f'scene_sans_scroll_{f:03}.png')
 # A visible contact sheet proving changing poses at fixed horizontal placement.
 sheet=Image.new('RGBA',(792*2,240*2),(12,18,36,255))
 for i,f in enumerate([0,22,44,66]):sheet.alpha_composite(frames[f],((i%2)*792,(i//2)*240))
 sheet.save(O/'review/poses_sans_defilement.png')
 def gif(path,count,render,size=None):
  def rgb(f):
   im=render(f).convert('RGB');return im.resize(size,Image.Resampling.NEAREST) if size else im
  board=Image.new('RGB',(rgb(0).width,rgb(0).height*4))
  for i,f in enumerate([0,22,44,66]):board.paste(rgb(f),(0,i*rgb(0).height))
  palette=board.quantize(colors=256)
  def pal(f):return rgb(f).quantize(palette=palette,dither=Image.Dither.NONE)
  pal(0).save(path,save_all=True,append_images=(pal(f) for f in range(1,count)),duration=DT,loop=0,disposal=1,optimize=False)
 def on_dark(f):
  im=Image.new('RGBA',(792,240),(12,18,36,255));im.alpha_composite(frames[f%N]);return im
 gif(O/'review/aurore_ANIMEE_sans_scroll.gif',N,on_dark)
 gif(O/'review/scene_animee_wrap.gif',264,scene,(384,256))
 data={'sky':uri(sky),'terrain':uri(terrain),'frames':[uri(im) for im in frames]}
 template=(R/'source/arene_boreales_v4/viewer.html').read_text();(R/'apercu_boreales_animees_v4.html').write_text(template.replace('__DATA__',json.dumps(data)))
 manifest={'size':[768,512],'intrinsic_frames':88,'frame_ms':100,'intrinsic_loop_seconds':8.8,'wrap_frames':264,'wrap_loop_seconds':26.4,'scroll_px_per_frame':3,'tile_size':[792,240],'motion':'Nonrigid travelling folds, horizontal sway, variable height, vertical undulation and travelling opacity scintillation. RGB from canonical drawing retained. Animated even with scroll disabled.','native_game_cycle':False,'runtime_tested':False,'terrain_and_sky':'V3 unchanged; separate PNG layers copied byte-identically','viewer_default':'intrinsic animation ON, scroll OFF to demonstrate real changing poses','preview_gif':'Scene GIF half size; PNG and transparent WebP full size','reference':'../arene_glace_large_v3/manifest.json','credits':'Canonical PMD reference drawing from user-provided aurorepmdsky.png via V1/V3. Pokemon/Nintendo/Creatures/GAME FREAK/Chunsoft; no additional redistribution permission inferred. New authored motion, not recovered official animation.'}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print('88 intrinsic poses,8.8s; optional wrap26.4s. Terrain/sky preserved.')
if __name__=='__main__':build()
