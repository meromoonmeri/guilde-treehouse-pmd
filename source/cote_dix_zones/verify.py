"""Independent checks for the 24 native Ground variants and their source pixels.
No PMDO or .NET runtime is invoked. Full scene PNGs are verified separately from
native premultiplied textures (GPU rounding on translucent stars is not claimed).
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import struct
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PACK=Path.home()/'.cache/cote_dix_pack'
WEB=ROOT/'sprites/cote_dix_zones'
sys.path.insert(0,str(ROOT/'source/pmdo_cote'))
spec=importlib.util.spec_from_file_location('native_checks',ROOT/'source/pmdo_cote/verify.py')
V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
from INSTALLER import install, read_index, encode_index


def night(image):
    rgba=np.array(image.convert('RGBA'))
    rgb=rgba[:,:,:3].astype(float)
    luminance=(rgb@np.array([.2126,.7152,.0722]))[:,:,None]
    rgba[:,:,:3]=np.rint((luminance*.2+rgb*.8)*np.array([.4,.42,.58])+np.array([4,8,15])).clip(0,255).astype('uint8')
    rgba[rgba[:,:,3]==0]=0
    return Image.fromarray(rgba)


def cloud_image(strip,size,offset):
    out=Image.new('RGBA',size)
    for x in range(-(offset%strip.width),size[0],strip.width):out.paste(strip,(x,0))
    return out


def equal(a,b):
    assert a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()


def main():
    m=json.loads((WEB/'manifest.json').read_text())
    refs=json.loads((HERE/'reference_autre_agent/provenance.json').read_text())
    for f in refs['files']:
        raw=(HERE/'reference_autre_agent'/f['local']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==f['blob']
    assert len(m['zones'])==12 and sum(z['new'] for z in m['zones'])==10
    assert len(list((PACK/'Data/Ground').glob('*.rsground')))==24
    for src in m['sources'].values():
        assert hashlib.sha256((ROOT/src['path']).read_bytes()).hexdigest()==src['sha256']
    sources={name:V.read_tile(ROOT/m['sources'][name]['path']) for name in ['Metano_Town_Base','Metano_Town_Cliffs']}
    native={p.stem:V.read_tile(p) for p in (PACK/'Content/Tile').glob('*.tile')}
    background={p.stem:V.read_dir(p) for p in (PACK/'Content/BG').glob('*.dir')}
    for mode in ['jour','nuit']:
        for kind in ['ciel','astres','nuages']:
            assert np.array_equal(np.array(background[f'C10_{mode.upper()}_{kind.upper()}']),V.expected(WEB/'fonds'/f'{mode}_{kind}.png'))
    original=Image.open(HERE/'reference_autre_agent/source__falaise__nuages_native.png').convert('RGBA')
    reconstructed=Image.new('RGBA',original.size)
    strip=Image.new('RGBA',tuple(m['clouds']['strip_size']))
    for rect,dest in zip(m['clouds']['crops'],m['clouds']['destinations']):
        piece=original.crop(rect);reconstructed.paste(piece,rect[:2]);strip.paste(piece,dest)
    equal(original,reconstructed)
    equal(strip,Image.open(WEB/'fonds/jour_nuages.png'))
    equal(night(strip),Image.open(WEB/'fonds/nuit_nuages.png'))
    assert strip.size==(1440,208) and m['clouds']['speed_px_s']==-4
    a=cloud_image(strip,(1312,1024),0)
    equal(a,cloud_image(strip,a.size,1440))
    equal(cloud_image(strip,a.size,1439).crop((1,0,1312,1024)),a.crop((0,0,1311,1024)))
    report={'status':'PASS','maps':24,'new_layouts':10,'day_night_variants':20,'styled_previous_variants':4,
            'pmdo_runtime_tested':False,'source_agent_blobs_exact':True,
            'cloud_pixels_preserved':True,'night_formula_exact':True,
            'sea_native_frame_length':10,'cloud_speed_px_s':-4,'zones':[],
            'limits':['GPU rounding on translucent stars not tested',
                      'native-module adaptation of the concept guide, not identical silhouettes',
                      'north/side shoreline tiles have river-blue pixels removed through alpha',
                      'new module junctions, collision and gameplay need in-engine review']}
    unique=set();sea_templates={}
    for zone in m['zones']:
        size=tuple(zone['size']);w,h=size[0]//8,size[1]//8
        base=WEB/zone['id']
        dayfiles=zone['variants']['jour']['layers']
        if zone['new']:
            provenance=json.loads((PACK/f'provenance/{zone["id"]}.json').read_text())
            assert len(dayfiles)==len(provenance)*2
            for p,record in enumerate(provenance):
                for k,field in enumerate(['ground','cliffs']):
                    result=Image.new('RGBA',size)
                    for pos,(sheet,x,y,cutout) in record[field].items():
                        dx,dy=map(int,pos.split(','));tile=sources[sheet][x,y].copy()
                        # Selected native regions have binary alpha: no unpremultiplication loss.
                        assert set(np.unique(np.array(tile)[:,:,3]))<={0,255}
                        if cutout:
                            assert field=='ground'
                            arr=np.array(tile);arr[arr[:,:,2].astype(int)>arr[:,:,0].astype(int)+8]=0
                            tile=Image.fromarray(arr)
                        result.paste(tile,(dx*8,dy*8))
                    equal(result,Image.open(base/dayfiles[p*2+k]))
        else:
            n=1 if 'promontoire' in zone['id'] else 2
            slug=zone['id'][3:]
            equal(Image.open(base/dayfiles[0]),Image.open(ROOT/f'sprites/cote_v2/{n:02d}_{slug}/COTEV2_{n:02d}_03_TERRAIN.png'))
        for day_file,night_file in zip(dayfiles,zone['variants']['nuit']['layers']):
            equal(night(Image.open(base/day_file)),Image.open(base/night_file))
        for mode,variant in zone['variants'].items():
            doc=json.loads((PACK/f'Data/Ground/{variant["asset"]}.rsground').read_text())
            o=doc['Object'];layers=o['Layers']
            assert doc['Version']=='0.7.15.1' and o['TexSize']==1 and not o['Released']
            assert o['$type']=='RogueEssence.Ground.GroundMap, RogueEssence'
            assert o['AssetName']==variant['asset'] and o['ActiveChar'] is None
            assert len(layers)==len(variant['layers'])+4
            for layer in layers:
                assert layer['Visible'] and len(layer['Tiles'])==w and all(len(c)==h for c in layer['Tiles'])
            for layer in layers[-3:]:
                assert all(not cell['Layers'] for col in layer['Tiles'] for cell in col)
            assert [l['Layer'] for l in layers[-3:]]==[0,0,4]
            assert len(o['obstacles'])==w and all(len(c)==h for c in o['obstacles'])
            for x,col in enumerate(o['obstacles']):
                for y,wall in enumerate(col):
                    assert wall=={'Bounds':{'X':8*x,'Y':8*y,'Width':8,'Height':8},'Tags':0}
            entities=o['Entities'][0]
            assert not entities['MapChars'] and not entities['GroundObjects'] and not entities['Spawners']
            marker=entities['Markers'][0]
            assert marker['EntName']=='entrance' and [marker['Collider']['X'],marker['Collider']['Y']]==zone['entry']
            bgs=o['Background']['Layers']
            assert o['Background']['$type']=='RogueEssence.Dungeon.LayeredBG, RogueEssence'
            assert [b['BG']['BGAnim']['AnimIndex'] for b in bgs]==[f'C10_{mode.upper()}_{k}' for k in ['CIEL','ASTRES','NUAGES']]
            assert all(b['BG']['Parallax']=='1, 1' for b in bgs)
            cloud=bgs[-1]['BG'];assert cloud['BGMovement']=={'X':-4,'Y':0} and cloud['RepeatX'] and not cloud['RepeatY']
            if mode not in sea_templates:
                for phase in range(8):
                    rendered=V.render_layer(layers[0],native,phase,size)
                    equal(rendered,Image.open(WEB/'fonds'/f'{mode}_mer_{phase:02d}.png'))
                sea_templates[mode]=layers[0]['Tiles']
            for x,col in enumerate(layers[0]['Tiles']):
                for y,cell in enumerate(col):
                    assert cell==sea_templates[mode][x][y]
                    for anim in cell['Layers']:
                        assert len(anim['Frames'])==8 and anim['FrameLength']==10
            for i,file in enumerate(variant['layers']):
                equal(V.render_layer(layers[i+1],native,0,size),Image.open(base/file))
            # PNG preview compositing (straight alpha), independently of native GPU blending.
            scene=Image.open(WEB/'fonds'/f'{mode}_ciel.png').convert('RGBA').crop((0,0,*size))
            scene=Image.alpha_composite(scene,Image.open(WEB/'fonds'/f'{mode}_astres.png').convert('RGBA').crop((0,0,*size)))
            scene=Image.alpha_composite(scene,cloud_image(Image.open(WEB/'fonds'/f'{mode}_nuages.png'),size,0))
            scene=Image.alpha_composite(scene,Image.open(WEB/'fonds'/f'{mode}_mer_00.png').convert('RGBA').crop((0,0,*size)))
            for file in variant['layers']:scene=Image.alpha_composite(scene,Image.open(base/file).convert('RGBA'))
            equal(scene,Image.open(base/variant['composition']))
            if mode=='jour' and zone['new']:
                digest=hashlib.sha256(scene.tobytes()).hexdigest();assert digest not in unique;unique.add(digest)
        report['zones'].append({'id':zone['id'],'variants':2,'tile_pixel_differences':0,'png_composition_differences':0})
        print('PASS',zone['id'],flush=True)
    # Same installer, now tested with the complete 24-map pack and an existing index.
    with tempfile.TemporaryDirectory() as tmp:
        mod=Path(tmp)/'mod';td=mod/'Content/Tile';td.mkdir(parents=True)
        (mod/'Mod.xml').write_text('<Header><Namespace>test_mod</Namespace></Header>')
        tile=next((PACK/'Content/Tile').glob('*.tile'));raw=tile.read_bytes();_,count=struct.unpack_from('<ii',raw)
        shutil.copyfile(tile,td/'AlreadyThere.tile')
        old=encode_index({'AlreadyThere':raw[:8+count*16]});(td/'index.idx').write_bytes(old)
        install(PACK,mod,True);assert not (mod/'Data').exists()
        install(PACK,mod)
        nodes=read_index(td/'index.idx');assert len(nodes)==5 and nodes['AlreadyThere']==raw[:8+count*16]
        assert next(td.glob('*.bak')).read_bytes()==old
        assert len(list((mod/'Data/Ground').glob('*.rsground')))==24
        assert len(list((mod/'Data/Script/test_mod/ground').glob('*/init.lua')))==24
        edited=next((mod/'Data/Ground').glob('*.rsground'));edited.write_text('user edited structures')
        try:
            install(PACK,mod);raise AssertionError('An edited map was overwritten')
        except ValueError as exc:assert 'Conflits' in str(exc)
        assert edited.read_text()=='user edited structures'
    report['installer_index_merge_and_protection']='PASS'
    for path in [HERE/'verification.json',PACK/'verification.json',WEB/'verification.json']:
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('PASS: 24 maps; 10 unique new layouts; no PMDO runtime test.')


if __name__=='__main__':main()
