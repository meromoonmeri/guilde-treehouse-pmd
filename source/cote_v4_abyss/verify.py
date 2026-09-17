"""Independent native-byte reconstruction; NOT an engine or editor runtime test."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WEB=ROOT/'sprites/cote_v4_abyss'
PACK=Path.home()/'.cache/cote_v4_abyss_pack'
sys.path.insert(0,str(ROOT/'source/pmdo_cote'))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


def main():
    V=load('binary_reader',ROOT/'source/pmdo_cote/verify.py')
    C=load('coast_checks',ROOT/'source/cote_dix_zones/verify.py')
    I=load('project_installer',PACK/'INSTALLER.py')
    from night import night
    C.night=night
    m=json.loads((WEB/'manifest.json').read_text());prep=json.loads((WEB/'preparation.json').read_text())
    native={p.stem:V.read_tile(p) for p in (PACK/'Content/Tile').glob('*.tile')}
    idx=I.read_index(PACK/'Content/Tile/index.idx');assert set(idx)==set(native)
    for p in (PACK/'Content/Tile').glob('*.tile'):
        with p.open('rb') as f:assert idx[p.stem]==I.read_node(f)
    header=ET.parse(PACK/'Mod.xml').getroot()
    assert header.findtext('Namespace')=='cotes_metano_abyss_0812' and header.findtext('GameVersion')=='0.8.12.0'
    assert header.findtext('ModType')=='Quest'
    source=ROOT/prep['rock_source']['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==prep['rock_source']['sha256']
    canonical=V.read_tile(source);control=Image.new('RGBA',(64,48))
    for y in range(6):
        for x in range(8):control.paste(canonical[114+x,58+y],(x*8,y*8))
    C.equal(control,Image.open(WEB/'METANO_ROCHE_NATIVE_64x48.png'))
    backgrounds={p.stem:V.read_dir(p) for p in (PACK/'Content/BG').glob('*.dir')}
    for mode in ['jour','nuit']:
        for kind in ['ciel','astres','nuages']:
            assert np.array_equal(np.array(backgrounds[f'V40812_{mode.upper()}_{kind.upper()}']),V.expected(WEB/'fonds'/f'{mode}_{kind}.png'))
    original=Image.open(ROOT/'source/cote_dix_zones/reference_autre_agent/source__falaise__nuages_native.png').convert('RGBA')
    strip=Image.new('RGBA',(1440,208));reconstructed=Image.new('RGBA',original.size)
    for rect,dest in zip(m['clouds']['crops'],m['clouds']['destinations']):
        piece=original.crop(rect);strip.paste(piece,dest);reconstructed.paste(piece,rect[:2])
    C.equal(original,reconstructed);C.equal(strip,Image.open(WEB/'fonds/jour_nuages.png'))
    C.equal(C.night(strip),Image.open(WEB/'fonds/nuit_nuages.png'))
    from audit_materials import audit
    material_report=audit()
    sea_templates={};results=[]
    # Largest terrain is the common sea template; all others are strict crops.
    zones=sorted(m['zones'],key=lambda z:z['size'][0]*z['size'][1],reverse=True)
    for zone in zones:
        size=tuple(zone['size']);w,h=size[0]//8,size[1]//8;base=WEB/zone['id']
        crop=zone['crop'];rock=np.array(Image.open(base/'01_FACES_NATIVE.png'));mask=rock[:,:,3]>0
        yy,xx=np.indices((size[1],size[0]));expected=np.array(control)[yy%48,xx%64]
        assert np.array_equal(rock[mask],expected[mask]),'Native rock material changed'
        terrain=np.array(Image.open(base/'TERRAIN.png'));before=np.array(Image.open(ROOT/'sprites/cote_v3_0812'/zone['id']/'TERRAIN.png'))
        assert np.array_equal(terrain[:,:,3],before[:,:,3])
        assert (terrain[:,0,3]>0).any() and (terrain[:,-1,3]>0).any() and (terrain[-1,:,3]>0).any()
        for day,night in zip(zone['variants']['jour']['layers'],zone['variants']['nuit']['layers']):
            C.equal(C.night(Image.open(base/day)),Image.open(base/night))
        for mode,variant in zone['variants'].items():
            doc=json.loads((PACK/f'Data/Ground/{variant["asset"]}.rsground').read_text());o=doc['Object'];layers=o['Layers']
            assert doc['Version']=='0.8.12.0' and o['TexSize']==1 and not o['Released']
            assert o['$type']=='RogueEssence.Ground.GroundMap, RogueEssence'
            assert o['AssetName']==variant['asset'] and o['ActiveChar'] is None and len(layers)==9
            for layer in layers:
                assert layer['Visible'] and len(layer['Tiles'])==w and all(len(c)==h for c in layer['Tiles'])
            assert [l['Layer'] for l in layers[-3:]]==[0,0,4]
            for layer in layers[-3:]:assert all(not t['Layers'] for col in layer['Tiles'] for t in col)
            assert len(o['obstacles'])==w and all(len(c)==h for c in o['obstacles'])
            for x,col in enumerate(o['obstacles']):
                for y,t in enumerate(col):assert t=={'Bounds':{'X':8*x,'Y':8*y,'Width':8,'Height':8},'Tags':0}
            ent=o['Entities'][0];assert not ent['MapChars'] and not ent['GroundObjects'] and not ent['Spawners']
            marker=ent['Markers'][0];assert marker['EntName']=='entrance'
            assert [marker['Collider']['X'],marker['Collider']['Y']]==zone['entry']
            assert (PACK/f'Data/Script/cotes_metano_abyss_0812/ground/{variant["asset"]}/init.lua').is_file()
            bgs=o['Background']['Layers'];assert o['Background']['$type']=='RogueEssence.Dungeon.LayeredBG, RogueEssence'
            assert [b['BG']['BGAnim']['AnimIndex'] for b in bgs]==[f'V40812_{mode.upper()}_{k}' for k in ['CIEL','ASTRES','NUAGES']]
            assert all(b['BG']['Parallax']=='1, 1' for b in bgs)
            cloud=bgs[-1]['BG'];assert cloud['BGMovement']=={'X':-4,'Y':0} and cloud['RepeatX'] and not cloud['RepeatY']
            if mode not in sea_templates:
                assert size==(1168,912)
                for phase in range(8):
                    assert np.array_equal(np.array(V.render_layer(layers[0],native,phase,size)),V.expected(WEB/'fonds'/f'{mode}_mer_{phase:02d}.png'))
                sea_templates[mode]=layers[0]['Tiles']
            for x,col in enumerate(layers[0]['Tiles']):
                for y,t in enumerate(col):
                    assert t==sea_templates[mode][x][y]
                    for a in t['Layers']:assert len(a['Frames'])==8 and a['FrameLength']==10
            for i,file in enumerate(variant['layers']):
                assert np.array_equal(np.array(V.render_layer(layers[i+1],native,0,size)),V.expected(base/file)),file
            scene=Image.open(WEB/'fonds'/f'{mode}_ciel.png').convert('RGBA').crop((0,0,*size))
            scene=Image.alpha_composite(scene,Image.open(WEB/'fonds'/f'{mode}_astres.png').convert('RGBA').crop((0,0,*size)))
            scene=Image.alpha_composite(scene,C.cloud_image(Image.open(WEB/'fonds'/f'{mode}_nuages.png'),size,0))
            scene=Image.alpha_composite(scene,Image.open(WEB/'fonds'/f'{mode}_mer_00.png').convert('RGBA').crop((0,0,*size)))
            for file in variant['layers']:scene=Image.alpha_composite(scene,Image.open(base/file).convert('RGBA'))
            C.equal(scene,Image.open(base/variant['composition']))
        results.append({'id':zone['id'],'size':size,'rock_pixels_exact':int(mask.sum()),'W_E_S_contacts':True})
        print('PASS',zone['id'],flush=True)
    assert len(list((PACK/'Data/Ground').glob('*.rsground')))==20
    # Real temporary project: preserve an unrelated indexed tileset, install twice,
    # then refuse to overwrite an edited map. The delivered standalone index MUST NOT be copied.
    with tempfile.TemporaryDirectory(prefix='v30812_install_') as tmp:
        target=Path(tmp);(target/'Mod.xml').write_text('<Header><Namespace>test_existing</Namespace></Header>')
        tile=target/'Content/Tile';tile.mkdir(parents=True)
        src=next((PACK/'Content/Tile').glob('*.tile'));shutil.copyfile(src,tile/'EXISTING.tile')
        with src.open('rb') as f:old=I.read_node(f)
        (tile/'index.idx').write_bytes(I.encode_index({'EXISTING':old}))
        I.install(PACK,target,dry_run=True);assert not (target/'Data').exists()
        I.install(PACK,target);I.install(PACK,target)
        assert I.read_index(tile/'index.idx')=={'EXISTING':old,**idx}
        assert len(list((target/'Data/Script/test_existing/ground').glob('*/init.lua')))==20
        edited=next((target/'Data/Ground').glob('*.rsground'));edited.write_text('USER EDIT')
        try:I.install(PACK,target)
        except ValueError:pass
        else:raise AssertionError('Installer overwrote an edited map')
        assert edited.read_text()=='USER EDIT'
    report={'materials':material_report,'status':'PASS','target':'0.8.12','native_runtime_tested':False,'maps':20,
            'native_premultiplied_layers_checked':100,'sea_frames_checked':16,'native_backgrounds':6,
            'standalone_index_complete':True,'installer_merge_and_conflict_tests':True,
            'zones':results,'limits':['No PMDO editor/runtime opening test','GPU alpha rounding not tested',
            'Native modules repeated to extend very tall faces; joins need in-engine review','Night uses the exact Abyss color filter; sky and stars retain existing night artwork',
            'Obstacle grid is deliberately free: draw collisions before gameplay']}
    for path in [HERE/'verification.json',WEB/'verification.json',PACK/'verification.json']:
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('PASS: 20 native Ground files, premultiplied textures, complete index, safe merge installer.')


if __name__=='__main__':main()
