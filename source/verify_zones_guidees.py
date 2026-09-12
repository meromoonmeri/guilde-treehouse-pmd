"""Independent source/atlas/render verification; does not import the builder."""
from pathlib import Path
from PIL import Image
import numpy as np
import json,struct,io,hashlib
R=Path(__file__).resolve().parents[1];O=R/'sprites/zones_guidees';m=json.loads((O/'provenance.json').read_text())
PINNED={'Metano_Town_Base':'19b295495e49819b356c02d13a574616dd67d36c','Metano_Town_Cliffs':'6d342b97ebfcad3e9aa6022b49e0f3b5b9d75640','Metano_Town_Animation_Tileset':'8b01d1730ef537ecc5578101fc8c1ea9630a3569','Metano_Town_River_Animation_1':'97d615195ef9488de15d28060a77e88b03c989a1','Metano_Town_River_Animation_2':'6956ccd5d7053faaa217edb7382939155f282f6c','Metano_Town_River_Animation_3':'21243860eef0e229957478d86f5a155b631aacbb','Metano_Town_River_Animation_4':'5e5528a0d2a5a8ca380db320186c4868ba1277f3'}
def decode(data):
    size,count=struct.unpack_from('<II',data);assert size==8
    cache={};result={}
    for i in range(count):
        x,y,off=struct.unpack_from('<IIQ',data,8+i*16)
        if off not in cache:
            length=struct.unpack_from('<q',data,off)[0];cache[off]=Image.open(io.BytesIO(data[off+8:off+8+length])).convert('RGBA')
        result[x,y]=cache[off]
    return result
sources={}
for n,meta in m['sources'].items():
    data=(R/meta['path']).read_bytes();sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert sha==PINNED[n]==meta['git_blob_sha1'];assert hashlib.sha256(data).hexdigest()==meta['sha256'];sources[n]=decode(data)
a=m['atlas'];native=decode((O/(a['name']+'.tile')).read_bytes());png=Image.open(O/(a['name']+'.png')).convert('RGBA');sprites=[]
for i,ref in enumerate(a['entries']):
    orig=sources[ref['sheet']][tuple(ref['texloc'])];actual=native[i%a['columns'],i//a['columns']];assert orig.tobytes()==actual.tobytes()
    sprite=png.crop(((i%a['columns'])*8,(i//a['columns'])*8,(i%a['columns']+1)*8,(i//a['columns']+1)*8));arr=np.asarray(sprite).astype(np.uint32);premul=arr.copy();premul[:,:,:3]=(arr[:,:,:3]*arr[:,:,3:4]+127)//255
    assert np.array_equal(premul,np.asarray(orig)),('PNG alpha roundtrip',i)
    sprites.append(sprite)
ts=json.loads((O/(a['name']+'.tsj')).read_text());assert ts['columns']==a['columns'] and ts['tilecount']==a['tilecount']
animations={t['id']+1:[f['tileid']+1 for f in t['animation']] for t in ts['tiles']}
for item in m['native_animations']:
    seq=animations[item['tileid']+1];assert len(seq)==4 and item['FrameLength']==10
    assert all(1<=g<=len(sprites) for g in seq)
    for g,frame in zip(seq,item['Frames']):assert frame=={'Sheet':a['name'],'TexLoc':{'X':(g-1)%a['columns'],'Y':(g-1)//a['columns']}}
    refs=[a['entries'][g-1] for g in seq];names=[r['sheet'] for r in refs]
    if names[0]=='Metano_Town_Animation_Tileset':
        x,y=refs[0]['texloc'];assert all(r['texloc']==[x+9*f,y] for f,r in enumerate(refs)) and len(set(names))==1
    else:assert names==[f'Metano_Town_River_Animation_{f}' for f in range(1,5)] and all(r['texloc']==refs[0]['texloc'] for r in refs)
def render(layer,frame):
    result=Image.new('RGBA',(2048,1536));assert len(layer['data'])==256*192
    for i,g in enumerate(layer['data']):
        if not g:continue
        assert 1<=g<=len(sprites);g=animations.get(g,[g]*4)[frame];result.paste(sprites[g-1],((i%256)*8,(i//256)*8))
    return result
def same(actual,path):
    assert np.array_equal(np.asarray(actual),np.asarray(Image.open(path).convert('RGBA'))),str(path)
checks=[]
for zone in m['zones']:
    out=O/zone['id'];assert hashlib.sha256((R/zone['guide']).read_bytes()).hexdigest()==zone['guide_sha256']
    dry=json.loads((out/'sec.tmj').read_text());wet=json.loads((out/'eau.tmj').read_text());assert dry['layers']==wet['layers'][:2];assert len(dry['layers'])==2 and len(wet['layers'])==4
    assert dry['tilewidth']==dry['tileheight']==8 and dry['width']==256 and dry['height']==192
    for l,layer in enumerate(dry['layers']):
        for g in set(layer['data'])-{0}:
            assert g not in animations;r=a['entries'][g-1];x,y=r['texloc']
            if l==0:assert r['sheet']=='Metano_Town_Base' and 0<=x<16 and 80<=y<96
            else:assert r['sheet']=='Metano_Town_Cliffs' and x in set(range(57,93))|set(range(114,122))|set(range(162,189)) and y>=(26 if x<93 else 38 if x>=162 else 54)
    grass=render(dry['layers'][0],0);cliff=render(dry['layers'][1],0);sec=Image.alpha_composite(grass,cliff);same(grass,out/'herbe.png');same(cliff,out/'falaises.png');same(sec,out/'canonique_sec.png')
    banks=render(wet['layers'][2],0);same(banks,out/'berges.png');base=Image.alpha_composite(sec,banks);hashes=[]
    for f in range(4):
        water=render(wet['layers'][3],f);same(water,out/f'eau_{f+1}.png');full=Image.alpha_composite(base,water);same(full,out/f'canonique_eau_{f+1}.png');hashes.append(hashlib.sha256(full.tobytes()).hexdigest())
    assert len(set(hashes))==4
    checks.append({'zone':zone['id'],'dry_source_whitelist':'PASS','all_layer_and_composite_pngs_different_pixels':0,'distinct_water_phases':4})
report={'status':'PASS','pinned_source_blobs':len(sources),'atlas_entries_source_identical':len(sprites),'tile_pixel_differences':0,'png_alpha_roundtrip_differences':0,'native_animations':len(animations),'zones':checks,'not_certified':['Aesthetic continuity of every joint','PMDO runtime import, collisions, navigation and transitions','Generated proposal pixels: not canonical','Reduced comparison PNG and GIF previews: not import assets']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
