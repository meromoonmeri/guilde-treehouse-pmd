"""Generated Metano-style foreground cutouts + separate V2 backgrounds.
Generated terrain is never resized. Ocean is fixed indexed geometry, palette interpolation only.
"""
from pathlib import Path
import sys,json,hashlib,io,base64
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/caps_terrasses_v3';HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
TITLES=['Cap gauche','Cap droit','Terrasse droite','Terrasse gauche','Corniche gauche','Balcon droit']

def save(im,p):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=False)

def ocean():
 old=json.loads((ROOT/'sprites/cote_v2/manifest.json').read_text());z=old['zones'][0];folder=ROOT/'sprites/cote_v2'/z['id']
 frames=[Image.open(folder/n).copy() for n in z['files']['sea']];base=frames[0];assert base.mode=='P'
 data=np.array(base);assert all(np.array_equal(data,np.array(im)) for im in frames)
 pals=np.array([im.getpalette() for im in frames],dtype=float).reshape(8,256,3)
 alpha=base.info.get('transparency');assert isinstance(alpha,bytes)
 cycle=z['cycle_indices'];static=[i for i in range(256) if i not in cycle]
 def palette(i):
  i%=64;a,t=divmod(i,8);return np.rint((1-t/8)*pals[a]+t/8*pals[(a+1)%8]).astype('uint8')
 colors=[]
 for i in range(64):
  pal=palette(i);assert np.array_equal(pal[static],pals[0,static]);assert np.array_equal(pal,pals[i//8]) if i%8==0 else True
  swatch=np.concatenate([pal,np.full((256,1),255,dtype='uint8')],axis=1).reshape(1,256,4)
  pn=np.array(night(Image.fromarray(swatch)))[0,:,:3]
  for mode,p in [('jour',pal),('nuit',pn)]:
   im=Image.fromarray(data).convert('P');im.putpalette(p.ravel().tolist());im.info['transparency']=alpha
   save(im,OUT/'ocean'/f'{mode}_{i:02d}.png')
  colors.append(pal)
 assert np.array_equal(palette(64),palette(0));assert len({p.tobytes() for p in colors})==64
 old_jump=max(float(np.abs(pals[(i+1)%8]-pals[i]).max()) for i in range(8))
 new_jump=max(float(np.abs(colors[(i+1)%64].astype(float)-colors[i]).max()) for i in range(64))
 assert new_jump<old_jump
 report={'source':str(folder.relative_to(ROOT)),'original_frame_count':8,'original_png_preview_frame_ms':160,'original_png_preview_loop_ms':1280,'original_native_frame_ticks':10,'original_native_loop_ms':80/60*1000,'frame_count':64,'frame_ms':50,'suggested_pmdo_frame_ticks':3,'loop_ms':3200,'method':'linear interpolation of the eight original palette rotations, 8 subphases per original transition','geometry_moves':False,'only_cycle_entries_change_during_day_animation':True,'cycle_indices':cycle,'alpha_unchanged':True,'phase_64_equals_phase_0':True,'unique_day_palettes':64,'max_rgb_channel_jump_old':old_jump,'max_rgb_channel_jump_new':new_jump,'native_mod_updated':False}
 (OUT/'ocean/animation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 return report,folder,z

def main():
 OUT.mkdir(parents=True,exist_ok=True);o,folder,z=ocean();records=[]
 sky=Image.open(folder/z['files']['sky']).convert('RGBA');cloud=Image.open(folder/z['files']['clouds_static']).convert('RGBA')
 save(sky,OUT/'fonds/ciel.png');save(cloud,OUT/'fonds/nuages.png');save(night(sky),OUT/'fonds/ciel_nuit.png');save(night(cloud),OUT/'fonds/nuages_nuit.png')
 board=Image.new('RGB',(1800,640),'#142733');d=ImageDraw.Draw(board)
 files=sorted(OUT.glob('[0-9][0-9]_*_magenta.png'));assert len(files)==6
 for i,(f,title) in enumerate(zip(files,TITLES)):
  slug=f.stem.removesuffix('_magenta');im=Image.open(f).convert('RGBA');a=np.array(im)
  key=(a[:,:,0]>210)&(a[:,:,1]<70)&(a[:,:,2]>210);a[key]=0
  cut=Image.fromarray(a);offset=(-256,0) if slug.startswith('04_') else (0,0)
  if offset!=(0,0):
   shifted=Image.new('RGBA',im.size);shifted.paste(cut,offset);cut=shifted
   assert np.array_equal(np.array(cut)[:,:im.width-256],a[:,256:])
  else:assert np.array_equal(np.array(cut)[~key],np.array(im)[~key])
  save(cut,OUT/(slug+'_terrain.png'));save(night(cut),OUT/(slug+'_terrain_nuit.png'))
  magenta=Image.new('RGBA',cut.size,(255,0,255,255));magenta.alpha_composite(cut);save(magenta,OUT/(slug+'_fond_uniforme.png'))
  # Only illustrative backgrounds are fitted to the foreground canvas, never the terrain itself.
  for mode in ['jour','nuit']:
   bg=Image.new('RGBA',cut.size)
   for layer in [sky if mode=='jour' else night(sky),cloud if mode=='jour' else night(cloud),Image.open(OUT/'ocean'/f'{mode}_00.png').convert('RGBA')]:
    bg.alpha_composite(layer.resize(cut.size,Image.Resampling.NEAREST))
   bg.alpha_composite(cut if mode=='jour' else night(cut));save(bg,OUT/(slug+'_scene'+('_nuit' if mode=='nuit' else '')+'.png'))
   if mode=='jour':
    thumb=bg.copy();thumb.thumbnail((584,250),Image.Resampling.NEAREST);x=i%3*600;y=i//3*320;board.paste(thumb,(x+8,y+44));d.text((x+12,y+10),f'{i+1:02d} - {title}',fill='white');d.text((x+12,y+287),'Terrain seul disponible en PNG transparent',fill='#b5cec6')
  alpha=np.array(cut)[:,:,3];assert (alpha==0).any() and (alpha==255).any();assert im.width%8==im.height%8==0
  records.append({'id':slug,'title':title,'size':list(im.size),'source':f.name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'terrain':slug+'_terrain.png','night':slug+'_terrain_nuit.png','scene':slug+'_scene.png','scene_night':slug+'_scene_nuit.png','offset_px':offset,'terrain_resampled':False,'day_retained_rgb_changed':False,'terrain_plane':'combined grass, rock, crowns; separate from ocean/sky/clouds','terrain_generated_not_canonical':True,'native_pmdo_integrated':False,'transparent_fraction':round(float((alpha==0).mean()),4)})
 save(board,OUT/'PLANCHE_FACE_MER.png')
 manifest={'method':'Cap V2 / Terrasse V2 framing + Metano rock and grass references, generator on magenta, chroma extraction','reference_layouts':['sprites/cote_v2/01_promontoire/COTEV2_01_03_TERRAIN.png','sprites/cote_v2/02_terrasse/COTEV2_02_03_TERRAIN.png'],'reference_texture':'source/falaises_generees/reference_canonique.png','ocean':o,'zones':records}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('6 terrain cutouts, 6 night variants, 12 scenes, 64+64 fixed-index ocean phases, board.')
if __name__=='__main__':main()
