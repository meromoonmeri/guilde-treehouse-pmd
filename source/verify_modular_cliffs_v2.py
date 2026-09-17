"""Vérification indépendante des fragments natifs et des placements Tiled du village V2."""
from pathlib import Path
from PIL import Image
import json,hashlib,struct,io
R=Path(__file__).resolve().parents[1];O=R/'sprites/falaises_modulaires_v2';M=json.loads((O/'modules.json').read_text())

def decode(path):
    b=path.read_bytes();s,n=struct.unpack_from('<II',b);assert s==8
    e=[struct.unpack_from('<IIQ',b,8+16*i) for i in range(n)];out=Image.new('RGBA',((max(x for x,y,o in e)+1)*8,(max(y for x,y,o in e)+1)*8))
    for x,y,o in e:
        ln=struct.unpack_from('<q',b,o)[0];assert o>=8+16*n and o+8+ln<=len(b)
        tile=Image.open(io.BytesIO(b[o+8:o+8+ln])).convert('RGBA');assert tile.size==(8,8);out.paste(tile,(x*8,y*8))
    return out

def premul(im):
    out=im.copy();out.putdata([(round(r*a/255),round(g*a/255),round(b*a/255),a) for r,g,b,a in im.getdata()]);return out

atlas=Image.open(O/'Falaises_Metano_Modules.png').convert('RGBA');assert atlas.size==(400,480)
assert decode(O/'Falaises_Metano_Modules.tile').tobytes()==premul(atlas).tobytes()
assert len(M['modules'])==15;cache={};differences=0
for part in M['modules']:
    p=R/part['source']['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==part['source']['sha256']
    if p not in cache:cache[p]=decode(p) if p.suffix=='.tile' else Image.open(p).convert('RGBA')
    expected=cache[p];rect=part['source']['rect_xyxy_px']
    if rect:expected=expected.crop(rect)
    actual=Image.open(O/part['file']).convert('RGBA');assert list(actual.size)==part['size_px']
    assert expected.tobytes()==premul(actual).tobytes()
    x,y,w,h=part['atlas_rect_px'];assert all(v%8==0 for v in [x,y,w,h])
    assert atlas.crop((x,y,x+w,y+h)).tobytes()==actual.tobytes()
ts=json.loads((O/'Falaises_Metano_Modules.tsj').read_text());assert ts['columns']==50 and ts['tilecount']==3000
anims={t['id']:t['animation'] for t in ts['tiles']};assert len(anims)==136
for seq in M['native_animations']:
    assert seq['FrameLength']==10
    ids=[f['TexLoc']['Y']*50+f['TexLoc']['X'] for f in seq['Frames']]
    assert ids==[f['tileid'] for f in anims[seq['id']]] and all(0<=v<3000 for v in ids)
# Match the optional village layer to its second tileset, then to all four PNG composites.
D=O/'decor/04_balcon';tm=json.loads((D/'village.tmj').read_text());assert len(tm['layers'])==3
assert (tm['width'],tm['height'],tm['tilewidth'],tm['tileheight'])==(256,192,8,8)
ref=tm['tilesets'][1];p=(D/ref['source']).resolve();assert p.is_file();hts=json.loads(p.read_text());ha=Image.open(p.parent/hts['image']).convert('RGBA');first=ref['firstgid']
layer=Image.new('RGBA',(2048,1536));data=tm['layers'][2]['data'];assert len(data)==49152
for i,gid in enumerate(data):
    if gid:
        tid=gid-first;assert 0<=tid<hts['tilecount'];x=(tid%hts['columns'])*8;y=(tid//hts['columns'])*8
        layer.paste(ha.crop((x,y,x+8,y+8)),((i%256)*8,(i//256)*8))
assert layer.tobytes()==Image.open(D/'structures.png').convert('RGBA').tobytes()
for f in range(1,5):
    bare=Image.open(D/f'layout_{f}.png').convert('RGBA');render=Image.open(D/f'village_{f}.png').convert('RGBA')
    assert Image.alpha_composite(bare,layer).tobytes()==render.tobytes()
placements=json.loads((O/'placements_maisons.json').read_text());assert len(placements)==10
for p in placements:assert (O/p['image']).is_file() and all(v%8==0 for v in p['position_px'])
old={hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'sprites/maisons_metano').glob('*_jour.png')}
new=[p for p in (R/'sprites/maisons_organiques_v2').glob('[0-9][0-9]_*_jour.png')];assert len(new)==10
assert not any(hashlib.sha256(p.read_bytes()).hexdigest() in old for p in new)
report={'status':'OK','native_modules':15,'source_pixel_differences':0,'native_atlas':'premultiplied roundtrip exact','village_house_layer':'Tiled equals PNG','village_phases_compared':4,'new_houses':10,'not_checked':['Import dans PMDO','Collisions et traversées de cours d’eau','Accès réels aux dix maisons','Fidélité artistique subjective']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
