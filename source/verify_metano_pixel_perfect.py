"""Contrôle source -> atlas -> cartes -> PNG, sans importer le script de construction."""
from pathlib import Path
from PIL import Image
import json,hashlib,struct,io
R=Path(__file__).resolve().parents[1];O=R/'sprites/metano_pixel_perfect';M=json.loads((O/'provenance.json').read_text())

def read_native(p):
    b=p.read_bytes();s,n=struct.unpack_from('<II',b);assert s==8
    cache={};tiles={}
    for i in range(n):
        x,y,off=struct.unpack_from('<IIQ',b,8+i*16);assert off>=8+n*16
        if off not in cache:
            length=struct.unpack_from('<q',b,off)[0];assert off+8+length<=len(b)
            im=Image.open(io.BytesIO(b[off+8:off+8+length])).convert('RGBA');assert im.size==(8,8);cache[off]=im
        tiles[x,y]=cache[off]
    return tiles

def premul(im):
    out=im.copy();out.putdata([(round(r*a/255),round(g*a/255),round(b*a/255),a) for r,g,b,a in im.getdata()]);return out

pins={k:v['git_blob_sha1'] for k,v in json.loads((R/'source/eau_metano/sources_github.json').read_text())['sources'].items()}
pins.update({'Metano_Town_Base':'19b295495e49819b356c02d13a574616dd67d36c','Metano_Town_Cliffs':'6d342b97ebfcad3e9aa6022b49e0f3b5b9d75640'})
source={}
for name,info in M['sources'].items():
    p=R/info['path'];b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==info['sha256']
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==info['git_blob_sha1']==pins[name]
    source[name]=read_native(p);assert len(source[name])==info['tiles']

sheet=M['atlas']['name'];cols=M['atlas']['columns'];count=M['atlas']['tilecount'];used=M['atlas']['used_entries'];origins=M['atlas']['entries']
assert len(origins)==used
raw_atlas=read_native(O/(sheet+'.tile'));png=Image.open(O/(sheet+'.png')).convert('RGBA');assert png.width==cols*8 and len(raw_atlas)==count
cache=[]
for i in range(count):
    xy=(i%cols,i//cols);tile=png.crop((xy[0]*8,xy[1]*8,xy[0]*8+8,xy[1]*8+8));cache.append(tile)
    assert premul(tile).tobytes()==raw_atlas[xy].tobytes()
    if i<used:
        ref=origins[i];assert ref['tileid']==i
        assert raw_atlas[xy].tobytes()==source[ref['sheet']][tuple(ref['texloc'])].tobytes()
    else:assert tile.getbbox() is None
TS=json.loads((O/(sheet+'.tsj')).read_text());assert TS['tilewidth']==TS['tileheight']==8 and TS['tilecount']==count
animations={t['id']:[f['tileid'] for f in t['animation']] for t in TS['tiles']}
for seq in M['native_animations']:
    ids=[f['TexLoc']['Y']*cols+f['TexLoc']['X'] for f in seq['Frames']]
    assert seq['FrameLength']==10 and ids==animations[seq['tileid']]
    assert len(ids)==4 and all(0<=v<used for v in ids)
    assert origins[seq['tileid']]['role']=='animation_first_frame'

def render(data,f=0):
    out=Image.new('RGBA',(2048,1536))
    for i,gid in enumerate(data):
        if gid:
            tid=gid-1
            if tid in animations:tid=animations[tid][f]
            out.paste(cache[tid],((i%256)*8,(i//256)*8))
    return out

reports=[]
for record in M['maps']:
    d=O/record['id'];dry=json.loads((d/'sec.tmj').read_text());wet=json.loads((d/'anime.tmj').read_text())
    assert len(dry['layers'])==2 and len(wet['layers'])==4
    for tm in [dry,wet]:
        assert (tm['width'],tm['height'],tm['tilewidth'],tm['tileheight'])==(256,192,8,8)
        assert (d/tm['tilesets'][0]['source']).resolve()==(O/(sheet+'.tsj')).resolve()
        for l in tm['layers']:assert len(l['data'])==49152 and all(0<=v<=used for v in l['data'])
    assert dry['layers']==wet['layers'][:2]
    for i,gid in enumerate(dry['layers'][0]['data']):
        assert gid>0;ref=origins[gid-1]
        assert ref['sheet']=='Metano_Town_Base' and ref['texloc']==[(i%256)%16,80+(i//256)%16]
    cliff_columns=set(range(57,93))|set(range(114,122))|set(range(162,189))
    for gid in dry['layers'][1]['data']:
        if gid:
            ref=origins[gid-1];assert ref['sheet']=='Metano_Town_Cliffs' and ref['texloc'][0] in cliff_columns and ref['role']=='native'
    grass=render(dry['layers'][0]['data']);cliffs=render(dry['layers'][1]['data']);combined=Image.alpha_composite(grass,cliffs)
    assert grass.tobytes()==Image.open(d/'herbe.png').convert('RGBA').tobytes()
    assert cliffs.tobytes()==Image.open(d/'falaises_bordures.png').convert('RGBA').tobytes()
    assert combined.tobytes()==Image.open(d/'sans_eau_sans_chemins.png').convert('RGBA').tobytes()
    assert combined.getchannel('A').getextrema()==(255,255)
    banks=render(wet['layers'][2]['data']);assert banks.tobytes()==Image.open(d/'berges_eau.png').convert('RGBA').tobytes()
    hashes=set()
    for f in range(4):
        water=render(wet['layers'][3]['data'],f);assert water.tobytes()==Image.open(d/f'eau_frame_{f+1}.png').convert('RGBA').tobytes()
        img=Image.alpha_composite(Image.alpha_composite(combined,banks),water)
        assert img.tobytes()==Image.open(d/f'avec_eau_frame_{f+1}.png').convert('RGBA').tobytes()
        hashes.add(hashlib.sha256(water.tobytes()).hexdigest())
    assert len(hashes)==4
    reports.append({'layout':record['id'],'native_px':[2048,1536],'grid_cells':[256,192],'dry_source_whitelist':'grass + cliffs only; no roads, stairs, cave or water columns','png_recomposition_differences':0,'distinct_water_frames':4})
report={'status':'OK','source_blobs_verified':len(source),'canonical_atlas_entries_checked':used,'source_tile_pixel_differences':0,'atlas_premultiplied_roundtrip_differences':0,'layouts':reports,'not_verified':['PMDO runtime import','Collisions and transitions','Artistic/topological continuity at all new joins','Standalone original cascade timing (10 ticks chosen; river timing verified in original map)']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
