"""Complément non destructif : sapins arrière et aurore couvrant les deux côtés.
Les huit plans de l'arène V1, la lune et le terrain restent byte-identiques.
"""
from pathlib import Path
import json,sys,hashlib,io,zipfile,shutil,colorsys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
O=R/'renders/arene_glace_sky_peak_v2';V1=R/'renders/arene_glace_sky_peak_v1'
W,H=960,720;SIZE=(W,H);N=32;MS=125;P='ARENE_SKYPEAK_V2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def blank():return Image.new('RGBA',SIZE)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def key(im,soft=False):
 a=np.array(im);rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1)
 mask=~((r>g*1.35)&(b>g*1.35)&(r>120)&(b>130))
 if soft:
  labs,_=ndimage.label(mask);counts=np.bincount(labs.ravel());ids=np.flatnonzero((counts>=30)&(np.arange(len(counts))>0));mask &= np.isin(labs,ids)
  lum=rgb@np.array([.2126,.7152,.0722]);a[:,:,3]=np.rint(np.clip((lum-34)/180,0,1)**1.2*220).astype('uint8')
 a[~mask]=0;a[a[:,:,3]==0]=0
 return Image.fromarray(a)
def shift(f):
 x=np.arange(W);t=(f%N)/N
 return np.rint(1.5*np.sin(2*np.pi*(x/448-t))+.5*np.sin(2*np.pi*(x/176+t))).astype(int)
def frame(idx,alpha,pal,f):
 a=np.dstack([np.array(pal[f%N],dtype='uint8')[idx],alpha]);a[alpha==0]=0;out=np.zeros_like(a)
 for x,dy in enumerate(shift(f)):
  if dy>0:out[dy:,x]=a[:-dy,x]
  elif dy<0:out[:dy,x]=a[-dy:,x]
  else:out[:,x]=a[:,x]
 out[out[:,:,3]==0]=0
 return Image.fromarray(out)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def webp(ims,p):ims[0].save(p,save_all=True,append_images=ims[1:],duration=MS,loop=0,lossless=True,exact=True,method=4)
def compose(layers):
 im=blank()
 for layer in layers.values():im.alpha_composite(layer)
 return im
def ora(path,layers):
 root=ET.Element('image',w=str(W),h=str(H),name='Arène du Croissant — aurore panoramique',version='0.0.3');stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers.items()):z.writestr(f'data/layer{i}.png',png(im))
  for i,(name,im) in reversed(list(enumerate(layers.items()))):ET.SubElement(stack,'layer',name=name,src=f'data/layer{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  merged=compose(layers);z.writestr('mergedimage.png',png(merged));merged.thumbnail((256,256),Image.Resampling.NEAREST);z.writestr('Thumbnails/thumbnail.png',png(merged));z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'))
def main():
 O.mkdir(parents=True,exist_ok=True);(O/'aurore').mkdir(exist_ok=True)
 old=json.loads((V1/'manifest.json').read_text());preserved=[];fixed={};paths={}
 for name,rel in old['layers'].items():
  src=V1/rel;dst=O/'calques'/f'{P}_{name}.png';dst.parent.mkdir(exist_ok=True);shutil.copy2(src,dst);fixed[name]=load(dst);paths[name]=str(dst.relative_to(O));preserved.append({'source':str(src.relative_to(R)),'output':str(dst.relative_to(O)),'sha256':sha(src)})
 # All eight V1 layers preserved. New mid-distance forest has its own layer.
 pine=key(load(O/'bruts/sapins_enneiges_magenta.png'));pine_box=pine.getbbox();pine=pine.crop(pine_box)
 pine_size=(640,round(pine.height*640/pine.width));pine=pine.resize(pine_size,Image.Resampling.NEAREST)
 forest=blank();pine_xy=(160,345-pine.height);forest.alpha_composite(pine,pine_xy)
 forest_name='04b_sapins_enneiges';fixed[forest_name]=forest
 save(forest,O/'calques'/f'{P}_{forest_name}.png');paths[forest_name]=f'calques/{P}_{forest_name}.png'
 # Overscan only, never squeeze the ribbon into a small floating center crop.
 raw=load(O/'bruts/aurore_panoramique_magenta.png');clean=key(raw,soft=True)
 scaled=(1056,round(clean.height*1056/clean.width));clean=clean.resize(scaled,Image.Resampling.NEAREST)
 master=blank();master.alpha_composite(clean,(-48,-8));save(master,O/'aurore'/f'{P}_dessin_detoure.png')
 a=np.array(master);alpha=a[:,:,3];opaque=alpha>0
 sample=Image.fromarray(a[:,:,:3][opaque][None,:,:]).quantize(colors=32,method=Image.Quantize.MEDIANCUT)
 base_palette=np.array(sample.getpalette(),dtype='uint8').reshape(-1,3)[:32]
 base_idx=np.array(Image.fromarray(a[:,:,:3]).quantize(palette=sample,dither=Image.Dither.NONE))
 idx=(base_idx.astype(int)+(np.arange(W)*8//W)[None,:]*32).astype('uint8');idx[~opaque]=0
 palettes=[]
 for f in range(N):
  lut=[]
  for band in range(8):
   delta=.10*np.sin(2*np.pi*(f/N-band/8))
   for rgb in base_palette:
    h,s,v=colorsys.rgb_to_hsv(*(rgb.astype(float)/255));lut.append([round(255*q) for q in colorsys.hsv_to_rgb((h+delta)%1,s,v)])
  palettes.append(lut)
 pim=Image.fromarray(idx).convert('P');pim.putpalette(np.array(palettes[0]).ravel().tolist());save(pim,O/'aurore'/f'{P}_indices.png');save(Image.fromarray(alpha),O/'aurore'/f'{P}_alpha.png')
 (O/'aurore'/f'{P}_palettes.json').write_text(json.dumps({'frames':palettes,'frame_ms':MS,'hue_delta_turns':.10,'displacement_px':[shift(f).tolist() for f in range(N)]})+'\n')
 frames=[frame(idx,alpha,palettes,f) for f in range(N)];effect_paths=[];scene_paths=[];scenes=[];coverage=[]
 order=['01_ciel_bleu_noir','02_etoiles_natives','02b_aurore_panoramique','03_lune_canonique','04_montagnes_lointaines',forest_name,'05_sol_complet_et_acces_sud','06_reliefs_arriere','07_immersion_gauche','08_immersion_droite']
 # Geography occlusion determines the actual visible sky at the lateral edges.
 hide=blank()
 for name in order[4:]:hide.alpha_composite(fixed[name])
 clear=np.array(hide)[:,:,3]==0
 for f,im in enumerate(frames):
  p=O/'aurore'/f'{P}_onde_{f:02d}.png';save(im,p);effect_paths.append(str(p.relative_to(O)))
  layers={name:(im if name=='02b_aurore_panoramique' else fixed[name]) for name in order}
  s=compose(layers);scenes.append(s);p=O/'frames_composition'/f'{P}_scene_{f:02d}.png';save(s,p);scene_paths.append(str(p.relative_to(O)))
  vis=(np.array(im)[:,:,3]>=24)&clear
  coverage.append({'frame':f,'left_visible_sky_pixels':int(vis[:300,:120].sum()),'right_visible_sky_pixels':int(vis[:300,-120:].sum()),'left_edge_alpha_pixels':int((np.array(im)[:,0,3]>0).sum()),'right_edge_alpha_pixels':int((np.array(im)[:,-1,3]>0).sum())})
 name='02b_aurore_panoramique';p=O/'calques'/f'{P}_{name}.png';save(frames[0],p);paths[name]=str(p.relative_to(O))
 save(scenes[0],O/f'{P}_composition_nuit.png');webp(scenes,O/f'{P}_composition_animee.webp');webp(frames,O/'aurore'/f'{P}_onde_transparente.webp')
 ordered={name:frames[0] if name=='02b_aurore_panoramique' else fixed[name] for name in order};ora(O/f'{P}_editable.ora',ordered)
 skyframes=[]
 for im in frames:
  skyframes.append(compose({'sky':fixed['01_ciel_bleu_noir'],'stars':fixed['02_etoiles_natives'],'aurora':im,'moon':fixed['03_lune_canonique']}))
 webp(skyframes,O/f'{P}_ciel_aurore_lune.webp')
 refs=[R/'aurorepmdsky.png',R/'renders/onde_boreale_glace_v2/bruts/onde_pmd_magenta.png',V1/old['composition'],R/'source/references_54d3731/snow.png']
 manifest={'title':'Arène du Croissant — aurore sur les deux côtés','date':'2026-09-18','canvas':[W,H],'layers':{name:paths[name] for name in order},'preserved':preserved,'new_raws':[{'path':str(p.relative_to(O)),'sha256':sha(p)} for p in sorted((O/'bruts').glob('*.png'))],'references':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in refs],'forest':{'crop':pine_box,'resized_size':pine_size,'position':pine_xy,'resampling':'nearest uniforme, bois en plan intermédiaire derrière le relief'},'aurora':{'raw_size':list(raw.size),'normalized_size':list(scaled),'position':[-48,-8],'scale_uniform':1056/raw.width,'horizontal_translation':0,'amplitude_max_px':2,'frame_ms':MS,'frames':effect_paths,'period_ms':N*MS,'indexed':'aurore/'+P+'_indices.png','alpha':'aurore/'+P+'_alpha.png','palette':'aurore/'+P+'_palettes.json','description':'Nouvelle composition panoramique générée couvrant les deux bords, sans miroir/tuilage du petit ruban central, puis animation de palette et ondulation verticale ±2px. Aucun wrap de l’aurore.'},'coverage_per_frame':coverage,'composition':P+'_composition_nuit.png','webp':P+'_composition_animee.webp','sky_webp':P+'_ciel_aurore_lune.webp','overlay_webp':'aurore/'+P+'_onde_transparente.webp','ora':P+'_editable.ora','scene_frames':scene_paths,'limits':['Terrain, montagnes, ciel, étoiles et lune de V1 conservés byte-identiques. Ciel V1 bleu-noir dérivé des65lignes sombres validées, pas le fichier entier de climat.','Sapins et aurore : nouvelles générations référencées, pas textures/cycle natifs extraits.','Un dessin d’aurore,32étapes animées ; pas32dessins générés.','Pas de nouveaux nuages, pas de Ground/collisions/warp ni test moteur.']}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 board=Image.new('RGB',(1440,1200),'#101c29');d=ImageDraw.Draw(board);font=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
 d.text((24,17),'ARÈNE DU CROISSANT / AURORE PANORAMIQUE',font=font(29),fill='#e0eee9')
 d.text((24,61),'Aurore jusqu’aux deux bords · sapins arrière · lune native inchangée',font=font(18),fill='#acc6d4')
 for i,(im,title) in enumerate([(load(V1/old['composition']),'Avant — ciel dégagé'),(scenes[0],'Après — deux côtés du ciel habités')]):
  im=im.resize((696,522),Image.Resampling.NEAREST);x=16+i*716;board.paste(im,(x,132));d.text((x+8,101),title,font=font(18),fill='white')
 for i,f in enumerate([0,8,16,24]):
  im=skyframes[f].crop((0,0,W,320)).resize((344,115),Image.Resampling.NEAREST);board.paste(im,(16+i*358,710));d.text((20+i*358,684),f'Phase {f:02d} /32',font=font(15),fill='white')
 for i,(name,title) in enumerate([('02b_aurore_panoramique','Onde seule / transparence'),(forest_name,'Sapins — calque indépendant')]):
  tile=Image.new('RGBA',(696,270),'#253644');im=ordered[name].crop((0,0,W,380)).resize((682,270),Image.Resampling.NEAREST);tile.alpha_composite(im,(7,0));board.paste(tile,(16+i*716,879));d.text((24+i*716,850),title,font=font(18),fill='white')
 d.text((24,1170),'32frames ×125ms · 4s · ±2px · sans scroll de l’aurore · aucun rendu moteur revendiqué',font=font(16),fill='#acc6d4');save(board,O/'PLANCHE_AVANT_APRES.png')
 print('Arène V2 : dix plans, panoramique sur les deux bords,32frames ; huit plans V1 inchangés.')
if __name__=='__main__':main()
