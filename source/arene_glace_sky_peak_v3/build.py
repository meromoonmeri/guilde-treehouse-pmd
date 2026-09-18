"""V3: new referenced terrain + distant ridge + forest valley; V2 sky effects retained.
Generated art is NOT a native tile extraction. Visible terrain is partitioned losslessly.
"""
from pathlib import Path
import sys, json, hashlib, io, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[2]; O=R/'renders/arene_glace_sky_peak_v3'; V2=R/'renders/arene_glace_sky_peak_v2'
P='ARENE_SKYPEAK_V3'; SIZE=(960,896)
FLOOR=[(493,254),(553,248),(720,251),(698,279),(739,296),(895,329),(926,409),(918,483),(1000,533),(890,547),(808,583),(731,622),(705,738),(711,848),(494,848),(501,788),(542,747),(550,694),(534,619),(494,579),(386,561),(310,537),(248,541),(228,498),(268,491),(268,443),(264,414),(320,400),(308,376),(340,356),(412,356),(415,319),(485,305)]
def load(p): return Image.open(p).convert('RGBA')
def blank(): return Image.new('RGBA',SIZE)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(im,p): p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
 a[(r>40)&(b>40)&(r>g*1.30)&(b>g*1.30)&(r>b*.65)]=0
 return Image.fromarray(a)
def place(im,width,xy):
 wh=(width,round(im.height*width/im.width)); result=blank();result.alpha_composite(im.resize(wh,Image.Resampling.NEAREST),xy)
 return result,{'input_size':im.size,'output_size':wh,'xy':xy,'resampling':'nearest, uniform'}
def compose(layers):
 im=blank()
 for layer in layers.values(): im.alpha_composite(layer)
 return im
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(path,layers):
 root=ET.Element('image',w=str(SIZE[0]),h=str(SIZE[1]),name='Arène / vallée enneigée',version='0.0.3');stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers.items()): z.writestr(f'data/{i}.png',png(im))
  for i,(name,im) in reversed(list(enumerate(layers.items()))): ET.SubElement(stack,'layer',name=name,src=f'data/{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  scene=compose(layers);z.writestr('mergedimage.png',png(scene));scene.thumbnail((256,256),Image.Resampling.NEAREST);z.writestr('Thumbnails/thumbnail.png',png(scene));z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'))
def main(preview=False):
 old=json.loads((V2/'manifest.json').read_text()); layers={}; retained=[]
 for name in ['01_ciel_bleu_noir','02_etoiles_natives','02b_aurore_panoramique','03_lune_canonique']:
  original=load(V2/old['layers'][name]);im=blank()
  if name=='01_ciel_bleu_noir':im=Image.new('RGBA',SIZE,original.getpixel((0,719)))
  im.paste(original,(0,0));layers[name]=im;retained.append({'layer':name,'source':str((V2/old['layers'][name]).relative_to(R)),'sha256':sha(V2/old['layers'][name]),'method':'Original 960×720 pixels retained, canvas extended downward without resampling.'})
 mountains=key(load(O/'bruts/montagnes_tres_lointaines_magenta.png'));mb=mountains.getbbox();mountains=mountains.crop(mb)
 layers['04_montagnes_horizon'],mountain_meta=place(mountains,960,(0,160))
 forest=key(load(O/'bruts/mer_de_sapins_profonde_magenta.png'));fb=forest.getbbox();forest=forest.crop(fb)
 # Receding trees fill the interval, not a narrow row beside the arena.
 layers['05_vallee_mer_de_sapins'],forest_meta=place(forest,960,(0,213))
 raw=key(load(O/'bruts/arene_matiere_canonique_magenta.png'));a=np.array(raw);valid=a[:,:,3]>0
 polygon=Image.new('L',raw.size);ImageDraw.Draw(polygon).polygon(FLOOR,fill=255);floor=(np.array(polygon)>0)&valid
 yy,xx=np.indices(valid.shape);rest=valid&~floor
 masks={'06_sol_visible_acces_sud':floor,'07_roches_glaces_arriere':rest&(yy<490),'08_immersion_gauche':rest&(yy>=490)&(xx<raw.width/2),'09_immersion_droite':rest&(yy>=490)&(xx>=raw.width/2)}
 for name,mask in masks.items():
  part=a.copy();part[~mask]=0;layers[name],terrain_meta=place(Image.fromarray(part),960,(0,270))
 terrain=compose({k:v for k,v in layers.items() if k in masks});expected,_=place(raw,960,(0,270));assert terrain.tobytes()==expected.tobytes()
 # Explicit visible-pixel masks: no claim of reconstructed hidden ground/rock surfaces.
 mask_layer,_=place(Image.fromarray((floor*255).astype('uint8')).convert('RGBA'),960,(0,270))
 save(mask_layer.getchannel('R'),O/'controle'/f'{P}_masque_sol_visible.png')
 files={}
 for name,im in layers.items():
  path=O/'calques'/f'{P}_{name}.png';save(im,path);files[name]=str(path.relative_to(O))
 save(terrain,O/f'{P}_terrain_seul.png');save(compose(layers),O/f'{P}_composition_nuit.png')
 if preview: return
 ora(O/f'{P}_editable.ora',layers)
 scenes=[];scene_files={};effect_files=[]
 for f,rel in enumerate(old['aurora']['frames']):
  effect=blank();effect.paste(load(V2/rel),(0,0))
  effect_files.append('../arene_glace_sky_peak_v2/'+rel)
  current={k:effect if k=='02b_aurore_panoramique' else im for k,im in layers.items()};scene=compose(current);scenes.append(scene)
  if f in [0,8,16,24]:
   p=O/'frames_composition'/f'{P}_scene_{f:02d}.png';save(scene,p);scene_files[f]=str(p.relative_to(O))
 scenes[0].save(O/f'{P}_composition_animee.webp',save_all=True,append_images=scenes[1:],duration=125,loop=0,lossless=True,method=4)
 refs=[R/'pmdskyicearena.png',R/'iceroadpmdsky.png',R/'source/references_54d3731/snow.png',R/'source/sky_peak_v1/232233_reference.png']
 manifest={'title':'Arène — roche/glace référencées, horizon très lointain et vallée boisée','canvas':SIZE,'layers':files,'composition':f'{P}_composition_nuit.png','webp':f'{P}_composition_animee.webp','ora':f'{P}_editable.ora','scene_frames':scene_files,'effect_frames':effect_files,'retained':retained,'references':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in refs],'raws':[{'path':str(p.relative_to(O)),'sha256':sha(p)} for p in sorted((O/'bruts').glob('*.png'))],'normalization':{'mountains':mountain_meta|{'crop':mb},'forest':forest_meta|{'crop':fb},'terrain':terrain_meta},'terrain_floor_polygon':FLOOR,'aurora':{'source':str(V2.relative_to(R)),'frames':32,'frame_ms':125,'horizontal_scroll':False,'vertical_amplitude_px':2},'limits':['Roche/glace, montagnes et forêt sont des générations guidées par les références canoniques, pas des copies de tuiles originales. Aucune certification de texture ou échelle native.','Terrain régénéré selon la demande ; aucun filtre de recoloration ajouté après génération.','Sol et reliefs : partition exacte des pixels visibles, sans reconstruction des surfaces cachées.','Ciel, étoiles, lune native et aurore V2 conservés dans leur emprise originale. Seul le canevas est prolongé vers le bas.','Pas de Ground, collision, warp ou validation GPU pour cette illustration.']}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print('V3 built: 960×896, 10 layers, 32 scene frames; native moon and V2 aurora retained.')
if __name__=='__main__':main('--preview' in sys.argv)
