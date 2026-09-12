"""Build 20 editable Ground files targeting PMDO 0.8.12, from prepared V2 shapes."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import zipfile

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WEB=ROOT/'sprites/cote_v3_0812'
PACK=Path.home()/'.cache/cote_v3_0812_pack'


def pipeline():
    spec=importlib.util.spec_from_file_location('coastal_native_helpers',ROOT/'source/cote_dix_zones/build.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    b.WEB=WEB;b.OUT=PACK;b.SIZE=(1168,912);b.SHEET_PREFIX='V30812_';b.MAP_PREFIX='v30812_'
    return b


def main():
    prep=json.loads((WEB/'preparation.json').read_text())
    b=pipeline();bg,cloud_info=b.backgrounds()
    with zipfile.ZipFile(ROOT/'cote_metano_v2_pmdo.zip') as z:
        template=json.loads(z.read('Data/Ground/cote_v2_promontoire.rsground'))['Object']
    template.pop('Layers');template.pop('obstacles')
    banks={mode:{'sea':b.N.TileBank('V30812_'+mode.upper()+'_MER'),
                 'terrain':b.N.TileBank('V30812_'+mode.upper()+'_TERRAIN')} for mode in ['jour','nuit']}
    phases=[]
    for i in range(8):
        im=Image.open(ROOT/f'sprites/cote_v2/01_promontoire/COTEV2_01_02_MER_PALETTE_{i:02d}.png').convert('RGBA')
        a=np.array(im);rows=np.arange(912)+216
        rows[rows>=im.height]=im.height-256+(rows[rows>=im.height]-im.height)%256
        moved=a[rows,:1168].copy();moved[:144]=0
        phases.append(Image.fromarray(moved))
    seas={mode:[b.grade(im,mode) for im in phases] for mode in ['jour','nuit']}
    for mode in seas:
        for i,im in enumerate(seas[mode]):b.png(im,WEB/'fonds'/f'{mode}_mer_{i:02d}.png')
    manifest={'pmdo_target':'0.8.12','serialization_version':'0.8.12.0',
              'rogueessence_commit':'4961b2271bb0cace74f40f6a85e799e8e4848ace',
              'reference_agent_commit':'c16efe12d74361df5ba8625abb68260f5f8fc6dd',
              'native_runtime_tested':False,'clouds':cloud_info,'sea_frame_length':10,
              'rock':prep['rock_source'],'zones':[]}
    labels=['Herbe - forme V2','Roche Metano native','Lisiere protegee','Ombres - volumes V2']
    for rec in prep['zones']:
        slug=rec['id'];directory=WEB/slug;size=tuple(rec['size'])
        planes=[(label,Image.open(directory/file).convert('RGBA')) for label,file in zip(labels,rec['layers'])]
        grass=np.array(planes[0][1])[:,:,3]==255
        options=[]
        for y in range(24,size[1]-24,16):
            for x in range(24,size[0]-24,16):
                options.append((grass[y-12:y+12,x-12:x+12].mean(),-abs(x-size[0]//2)-abs(y-size[1]//3),x,y))
        score,_,x,y=max(options);assert score>.9
        entry={'id':slug,'title':rec['title'],'size':size,'new':True,'entry':[x-8,y-8],
               'planes':labels,'crop':rec['crop'],'attached_edges':rec['exits'],
               'variants':{},'terrain_provenance':'approved generated geometry; native Metano rock; separate lighting'}
        for mode in ['jour','nuit']:
            layers=[(label,b.grade(im,mode)) for label,im in planes]
            sea=[im.crop((0,0,*size)) for im in seas[mode]]
            asset='v30812_'+slug+'_'+mode
            doc=b.make_map(asset,rec['title'],mode,layers,sea,banks[mode],template)
            doc['Version']='0.8.12.0'
            o=doc['Object']
            o['Comment']='PMDO 0.8.12. Silhouette V2; roche Metano native; ombres separees. Bords W/E/S sans marge. Collisions a dessiner.'
            o['Entities'][0]['Markers'][0]['Collider'].update(X=x-8,Y=y-8)
            b.N.save(PACK/f'Data/Ground/{asset}.rsground',json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode())
            b.N.save(PACK/f'Data/Script/ground/{asset}/init.lua',b'-- Native Ground animations; empty editing scaffold.\nreturn {}\n')
            names=[]
            for i,(_,im) in enumerate(layers):
                name=f'{mode}_{i:02d}.png';b.png(im,directory/name);names.append(name)
            sky,stars,cloud=bg[mode]
            scene=Image.alpha_composite(sky.crop((0,0,*size)),stars.crop((0,0,*size)))
            scene=Image.alpha_composite(scene,b.clouds_at(cloud,size))
            scene=Image.alpha_composite(scene,sea[0])
            for _,im in layers:scene=Image.alpha_composite(scene,im)
            b.png(scene,directory/f'{mode}_composition.png')
            entry['variants'][mode]={'asset':asset,'layers':names,'composition':f'{mode}_composition.png'}
        manifest['zones'].append(entry)
        print(asset,'contacts W/E/S',rec['edge_contact_pixels'],flush=True)
    for mode in banks:
        for bank in banks[mode].values():bank.write(PACK/f'Content/Tile/{bank.name}.tile')
    for path in [WEB/'manifest.json',PACK/'manifest.json']:
        b.N.save(path,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    (PACK/'provenance').mkdir(exist_ok=True)
    shutil.copyfile(WEB/'preparation.json',PACK/'provenance/preparation.json')
    shutil.copyfile(WEB/'METANO_ROCHE_NATIVE_64x48.png',PACK/'provenance/METANO_ROCHE_NATIVE_64x48.png')
    shutil.copyfile(HERE/'engine_compatibility.json',PACK/'provenance/engine_compatibility.json')
    shutil.copyfile(ROOT/'source/pmdo_cote/INSTALLER.py',PACK/'INSTALLER.py')
    print('20 Ground PMDO 0.8.12 generated. Native/UI runtime not tested.')


if __name__=='__main__':main()
