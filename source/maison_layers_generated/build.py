from pathlib import Path
import numpy as np,json,hashlib,shutil
from PIL import Image
R=Path('/home/user/guilde-treehouse-pmd');S=R/'source/maison_layers_generated';O=R/'renders/generator_multicalque_final/maison_interieure';O.mkdir(parents=True,exist_ok=True)
files=[('00_murs_parois','wall_layer_magenta.png'),('01_sol','floor_layer_magenta.png'),('02_salle_vide','empty_room_layer_magenta.png'),('03_objets_decoration','decor_layer_magenta.png'),('04_entree','entrance_layer_magenta.png')]
def key(path):
 im=Image.open(path).convert('RGBA');a=np.array(im).astype(np.int32);k=a[0,0,:3];d=np.sqrt(((a[:,:,:3]-k)**2).sum(2));a[:,:,3]=np.clip((d-75)*8,0,255).astype(np.uint8);return Image.fromarray(a.astype(np.uint8))
ims=[]
for n,f in files:
 im=key(S/f);im.save(O/f'{n}.png');ims.append(im)
# explicit empty-room base is the generated floor layer; decoration/architecture remain independent.
full=Image.new('RGBA',ims[0].size,(38,25,20,255))
# compositing order follows the generated layer semantics: floor, walls, architecture, objects, entrance
for index in [1,0,3,4]: full.alpha_composite(ims[index])
full.save(O/'Maison_Interieure_Ovale_Multicalque.png')
manifest={'method':'each layer generated independently with image generator, then chroma-keyed and packed','canvas_px':list(full.size),'layers':[n+'.png' for n,_ in files],'water_layer':None,'objects_own_layer':'03_objets_decoration.png','source_reference':'d5c79863 IMG_5001.png'}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False));h={}
for p in O.glob('*'):
 if p.is_file():h[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(O/'hashes.json').write_text(json.dumps(h,indent=2));print('packed independently generated layers',full.size)
