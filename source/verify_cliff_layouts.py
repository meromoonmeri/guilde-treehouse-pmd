"""Recompose indépendamment les cartes Tiled et le .tile, compare chaque phase aux PNG."""
from pathlib import Path
from PIL import Image
import json,io,struct,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path);parser.add_argument("--expected-maps",type=int,default=3);parser.add_argument("--sheet-name",default="Extension_Metano");args=parser.parse_args();SHEET=args.sheet_name
R=Path(__file__).resolve().parents[1];O=args.output if args.output else R/'sprites/falaises_metano';M=json.loads((O/'kit.json').read_text());TS=json.loads((O/(SHEET+'.tsj')).read_text())
assert M['size_px']==[2048,1536] and M['grid_px']==8 and len(M['maps'])==args.expected_maps
atlas=Image.open(O/(SHEET+'.png')).convert('RGBA');cols=TS['columns'];count=TS['tilecount'];assert cols*8==atlas.width and count==atlas.width*atlas.height//64
cache=[atlas.crop(((i%cols)*8,(i//cols)*8,(i%cols)*8+8,(i//cols)*8+8)) for i in range(count)]
animations={t['id']:[f['tileid'] for f in t['animation']] for t in TS['tiles']}
assert TS['tilewidth']==TS['tileheight']==8
for seq in animations.values():assert len(seq)==4 and all(0<=t<count for t in seq)
# Decode native file without using the builder.
b=(O/(SHEET+'.tile')).read_bytes();size,n=struct.unpack_from('<II',b);assert (size,n)==(8,count)
decoded=Image.new('RGBA',atlas.size)
for i in range(n):
    x,y,off=struct.unpack_from('<IIQ',b,8+i*16);assert off>=8+n*16
    length=struct.unpack_from('<q',b,off)[0];assert off+8+length<=len(b)
    tile=Image.open(io.BytesIO(b[off+8:off+8+length])).convert('RGBA');assert tile.size==(8,8)
    decoded.paste(tile,(x*8,y*8))
assert decoded.tobytes()==atlas.tobytes()
checks=[]
for desc in M['maps']:
    d=O/desc['id'];tm=json.loads((d/'layout.tmj').read_text());assert (tm['width'],tm['height'],tm['tilewidth'],tm['tileheight'])==(256,192,8,8)
    assert (d/tm['tilesets'][0]['source']).resolve()==(O/(SHEET+'.tsj')).resolve()
    assert len(tm['layers'])==2
    for layer in tm['layers']:assert len(layer['data'])==49152 and all(0<=gid<=count for gid in layer['data'])
    terrain=Image.open(d/'terrain.png').convert('RGBA');assert terrain.size==(2048,1536) and terrain.getchannel('A').getextrema()==(255,255)
    expected_base=Image.new('RGBA',terrain.size)
    for i,gid in enumerate(tm['layers'][0]['data']):
        if gid:expected_base.paste(cache[gid-1],((i%256)*8,(i//256)*8))
    assert expected_base.tobytes()==terrain.tobytes()
    phase_hashes=set()
    for f in range(4):
        layer=Image.new('RGBA',terrain.size)
        for i,gid in enumerate(tm['layers'][1]['data']):
            if gid:
                idx=gid-1;idx=animations[idx][f] if idx in animations else idx
                layer.paste(cache[idx],((i%256)*8,(i//256)*8))
        water=Image.open(d/f'eau_{f+1}.png').convert('RGBA');assert water.size==terrain.size
        assert sum(water.getchannel('A').histogram()[1:255])==0
        assert water.tobytes()==layer.tobytes()
        composite=Image.open(d/f'layout_{f+1}.png').convert('RGBA');assert Image.alpha_composite(terrain,water).tobytes()==composite.tobytes()
        phase_hashes.add(hashlib.sha256(water.tobytes()).hexdigest())
    assert len(phase_hashes)==4
    for obj in desc['stairs']+desc['cascades']:
        assert obj['x']%8==obj['y']%8==obj['height']%8==0
        assert 0<=obj['x']<2048 and 0<=obj['y']<1536 and obj['y']+obj['height']+8<=1536
    checks.append({'layout':desc['id'],'cells':49152,'phases':4,'pixel_differences':0,'water_layer_separate':True})
assert len(M['native_animations'])==len(animations)
for a in M['native_animations']:
    assert a['FrameLength']==10
    ids=[v['TexLoc']['Y']*cols+v['TexLoc']['X'] for v in a['Frames']]
    assert ids==animations[a['tileid']]
report={'status':'OK','maps':checks,'native_atlas_roundtrip':'pixel exact','animations':len(animations),'not_checked':['Lancement dans PMDO ou interface Tiled','Collisions et chemins praticables','Raccord à une Ground existante','Validation artistique des layouts']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
