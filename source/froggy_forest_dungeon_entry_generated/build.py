from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image
S=Path(__file__).parent
O=Path('renders/froggy_forest_dungeon_entry_multicalque'); O.mkdir(parents=True,exist_ok=True)
files=[('01_sol_foret','01_forest_ground_magenta.png'),('02_falaises_rochers','02_cliffs_rocks_magenta.png'),('03_cascades_eau','04_water_cascades_magenta.png'),('04_chemin_entree','03_path_entrance_floor_magenta.png'),('05_vegetation','05_vegetation_magenta.png'),('06_entree_donjon','06_dungeon_entrance_magenta.png')]
def key(p):
    im=Image.open(S/p).convert('RGBA'); a=np.array(im).astype(np.int32); c=a[0,0,:3]
    d=np.sqrt(((a[:,:,:3]-c)**2).sum(axis=2)); a[:,:,3]=np.clip((d-55)*6,0,255).astype(np.uint8)
    return Image.fromarray(a.astype(np.uint8))
ims=[]
for n,f in files:
    im=key(f'{S.name}/{f}') if False else key(S/f)
    im.save(O/f'{n}.png'); ims.append(im)
full=Image.new('RGBA',ims[0].size,(22,44,35,255))
for im in ims: full.alpha_composite(im)
full.save(O/'Froggy_Forest_Entree_Donjon_Cascades_Multicalque.png')
manifest={'canvas_px':list(full.size),'method':'six independently generated image-generator layers, chroma-keyed then recomposed','references':['Foggy_Forest_Base_Camp_TDS.png','entrancecascade.png','Mystifying_Forest_entrance_TDS.png','Waterfall_Cave_ledge_TDS.png'],'layers':[n+'.png' for n,_ in files],'water_only_where_generated':'03_cascades_eau.png','no_house_v2':True}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
h={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*.png')}; (O/'hashes.json').write_text(json.dumps(h,indent=2))
