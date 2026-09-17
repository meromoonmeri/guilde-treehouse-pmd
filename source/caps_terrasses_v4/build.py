"""Strict canonical-color correction AFTER reference-driven image generation.
Color membership is guaranteed; this does not claim canonical tile shapes.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/caps_terrasses_v4'
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
TITLES=['Anse gauche','Crochet droit','Paliers décalés droits','Double balcon gauche','Corniche oblique gauche','Paroi haute droite','Avancée basse gauche','Échancrure droite','Trois gradins gauches','Balcon renfoncé droit']

def lab(rgb):
 c=np.asarray(rgb,dtype=float)/255.;lin=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
 xyz=lin@np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]]).T
 xyz/=np.array([.95047,1.,1.08883]);f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
 return np.stack((116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])),axis=-1)

def chroma(im):
 a=np.array(im.convert('RGBA'));r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
 strong=(r>220)&(g<60)&(b>220)
 fringe=(r>145)&(b>145)&(g<125)&(r>g*1.6)&(b>g*1.6)&(b>r*.78)
 labs,_=label(fringe);edge=np.unique(np.r_[labs[0],labs[-1],labs[:,0],labs[:,-1]]);edge=edge[edge!=0]
 key=strong|np.isin(labs,edge);a[key]=0
 return a

def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)

def main():
 cfg=json.loads((HERE/'palette_canonique.json').read_text());pal=np.array(cfg['allowed_rgb'],dtype=np.uint8);tree=cKDTree(lab(pal));allowed={tuple(c) for c in pal.tolist()}
 records=[];palette_reports=[];board=Image.new('RGB',(1800,1500),'#162d38');d=ImageDraw.Draw(board)
 crops=Image.new('RGB',(1280,10*200+180),'#172b34');cd=ImageDraw.Draw(crops)
 ref=Image.open(ROOT/'source/falaises_metano/patches/rebord.png').convert('RGBA');ref=ref.resize((256,96),Image.Resampling.NEAREST);crops.paste(ref,(16,45),ref);cd.text((16,12),'REFERENCE CANONIQUE - bord herbe/roche x4',fill='white');cd.text((390,12),'COUPES NATIVES x1 : original generateur | palette verrouillee',fill='white')
 old=ROOT/'renders/caps_terrasses_v3';bg0=Image.open(old/'fonds/ciel.png').convert('RGBA');bg0.alpha_composite(Image.open(old/'fonds/nuages.png').convert('RGBA'));bg0.alpha_composite(Image.open(old/'ocean/jour_00.png').convert('RGBA'))
 rawfiles=sorted((OUT/'bruts').glob('*.png'));assert len(rawfiles)==10
 for i,(file,title) in enumerate(zip(rawfiles,TITLES)):
  slug=file.stem;raw=Image.open(file).convert('RGBA');a=chroma(raw);h,w=a.shape[:2];opaque=a[:,:,3]>0;assert opaque.any() and (~opaque).any()
  rgb=a[opaque,:3];unique,inverse=np.unique(rgb,axis=0,return_inverse=True);dist,near=tree.query(lab(unique));fixed=pal[near][inverse];before=a.copy();a[opaque,:3]=fixed
  assert {tuple(c) for c in np.unique(fixed,axis=0).tolist()}<=allowed
  diffs=np.sqrt(np.sum((lab(rgb)-lab(fixed))**2,axis=1));changed=np.any(rgb!=fixed,axis=1)
  # Close-camera anchor: if the generated cliff floats above the bottom, translate (no resize).
  ys=np.where(opaque.any(axis=1))[0];dy=0
  if opaque[-1].sum()<w*.08:dy=max(0,h-1-int(ys[-1]))+24
  im=Image.new('RGBA',(w,h));im.paste(Image.fromarray(a),(0,dy));b=Image.new('RGBA',(w,h));b.paste(Image.fromarray(before),(0,dy));correct=np.array(im);visible=correct[:,:,3]>0
  save(im,OUT/(slug+'_terrain.png'));save(night(im),OUT/(slug+'_terrain_nuit.png'))
  magenta=Image.new('RGBA',im.size,(255,0,255,255));magenta.alpha_composite(im);save(magenta,OUT/(slug+'_magenta.png'))
  scene=bg0.resize(im.size,Image.Resampling.NEAREST);scene.alpha_composite(im);save(scene,OUT/(slug+'_scene.png'))
  # Identify grass-family pixels for locating an inspection window, not for collision classification.
  c=correct[:,:,:3].astype(int);grass=(c[:,:,1]>=c[:,:,0]-10)&(c[:,:,1]>c[:,:,2]+35)&visible
  crown=binary_dilation(grass,iterations=3)&visible&~grass
  counts=crown.sum(axis=1);cy=int(np.argmax(counts));xs=np.flatnonzero(crown[max(0,cy-8):min(h,cy+9)].any(axis=0));cx=int(np.median(xs)) if len(xs) else w//2
  x=max(0,min(w-560,cx-280));y=max(0,min(h-160,cy-80));box=(x,y,min(w,x+560),min(h,y+160))
  if slug.startswith('13_'):box=(580,300,1140,460)
  if slug.startswith('11_'):box=(260,260,820,420)
  for j,plane in enumerate([b,im]):
   crop=plane.crop(box);back=Image.new('RGBA',crop.size,(48,62,67,255));back.alpha_composite(crop);crops.paste(back,(j*640+12,180+i*200+28))
   cd.text((j*640+12,180+i*200+6),f'{slug} / '+('GENERATEUR' if j==0 else 'PALETTE METANO'),fill='white')
  save(Image.fromarray((crown*255).astype('uint8')),OUT/'audit'/f'{slug}_bande_reperage.png')
  # Contact sheet uses uniform slots, keeping each terrain aspect ratio.
  thumb=scene.copy();thumb.thumbnail((880,245),Image.Resampling.NEAREST);xx=i%2*900;yy=i//2*300;board.paste(thumb,(xx+8,yy+35));d.text((xx+12,yy+7),f'{i+7:02d} - {title}',fill='white')
  report={'id':slug,'opaque_pixels':int(visible.sum()),'raw_unique_opaque_rgb':len(unique),'corrected_unique_opaque_rgb':len(np.unique(correct[visible,:3],axis=0)),'allowed_canonical_palette_size':len(pal),'out_of_palette_after':0,'changed_opaque_rgb_before_crop':int(changed.sum()),'deltaE76_before_after_median':round(float(np.median(diffs)),3),'deltaE76_before_after_p95':round(float(np.percentile(diffs,95)),3),'deltaE76_before_after_max':round(float(diffs.max()),3),'alpha_binary':bool(np.isin(correct[:,:,3],[0,255]).all()),'transparent_rgb_zero':bool((correct[~visible]==0).all()),'source_texture_tiles_reconstructed':False,'crown_crop_xyxy':box,'edge_contact_pixels':{'left':int(visible[:,0].sum()),'right':int(visible[:,-1].sum()),'bottom':int(visible[-1].sum())}}
  assert report['alpha_binary'] and report['transparent_rgb_zero'];palette_reports.append(report)
  records.append({'id':slug,'title':title,'size':[w,h],'raw':str(file.relative_to(OUT)),'raw_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'terrain':slug+'_terrain.png','night':slug+'_terrain_nuit.png','scene':slug+'_scene.png','offset_px':[0,dy],'resampled':False,'palette_locked':True,'canonical_tile_identity':False,'visual_status':'A_INSPECTER','crown_crop':box})
 save(board,OUT/'PLANCHE_10_FACE_MER.png');save(crops,OUT/'AUDIT_BORDURES_AVANT_APRES.png')
 (OUT/'manifest.json').write_text(json.dumps({'method':'reference-driven generator then nearest canonical RGB color chosen in CIELAB; no geometry redraw','palette_file':'../../source/caps_terrasses_v4/palette_canonique.json','zones':records},ensure_ascii=False,indent=2))
 (HERE/'audit_couleurs.json').write_text(json.dumps({'status':'PASS_COULEURS_ALPHA','canonical_patch_equality':cfg['patch_checks'],'not_proved':'canonical tile pattern identity, automatic crown matching, seamless cross-map joins or engine validity','zones':palette_reports},ensure_ascii=False,indent=2))
 print('10 color-locked foreground layers; 0 out-of-palette pixels; visual inspection still required.')
if __name__=='__main__':main()
