"""Comparaison pixel par pixel indépendante des exports aux PNG contenus dans les .tile."""
from pathlib import Path
from PIL import Image
import json,struct,io,hashlib
R=Path(__file__).resolve().parents[1];O=R/'sprites/eau_metano';S=R/'source/eau_metano';m=json.loads((O/'eau_metano.json').read_text())

def read_native(p):
    b=p.read_bytes();size,n=struct.unpack_from('<II',b);assert size==8
    entries=[struct.unpack_from('<IIQ',b,8+16*i) for i in range(n)];w=(max(x for x,y,o in entries)+1)*8;h=(max(y for x,y,o in entries)+1)*8
    out=Image.new('RGBA',(w,h));tiles={}
    for x,y,o in entries:
        assert o>=8+16*n;length=struct.unpack_from('<q',b,o)[0];assert length>0 and o+8+length<=len(b)
        t=Image.open(io.BytesIO(b[o+8:o+8+length])).convert('RGBA');assert t.size==(8,8);out.paste(t,(x*8,y*8));tiles[x,y]=t
    return out,tiles
source={}
pinned=json.loads((S/'sources_github.json').read_text())['sources']
for name,meta in m['sources'].items():
    p=S/'natifs'/(name+'.tile');raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pinned[name]['git_blob_sha1']
    native,tiles=read_native(p);source[name]=(native,tiles);png=Image.open(O/(name+'.png')).convert('RGBA');assert png.size==native.size
    # Native textures use premultiplied alpha; PNG uses straight alpha. Validate the inverse.
    for a,b in zip(native.getdata(),png.getdata()):
        assert a[3]==b[3]
        recovered=tuple(round(v*b[3]/255) for v in b[:3])+(b[3],)
        assert a==recovered,(name,a,b,recovered)
    assert len(tiles)==meta['tile_count']
base=source['Metano_Town_Animation_Tileset'][0];sheet=Image.open(O/'Cascades_Metano_Exact.png').convert('RGBA');assert sheet.size==(256,136)
hashes=set()
for i,rect in enumerate(m['cascades']['source_rects_xyxy_px']):
    native=base.crop(rect);png=Image.open(O/f'cascade_frame_{i+1}.png').convert('RGBA')
    assert native.tobytes()==png.tobytes()==sheet.crop((64*i,0,64*(i+1),136)).tobytes()
    hashes.add(hashlib.sha256(png.tobytes()).hexdigest())
assert len(hashes)==4
compact=Image.open(O/'Riviere_Metano_Compacte.png').convert('RGBA');w,h=m['river']['compact_frame_size_px'];seen=set();comparisons=0
for e in m['river']['entries']:
    x,y=e['compact_xy_cells']
    for xy in e['source_texlocs']:
        seen.add(tuple(xy))
        for f,name in enumerate(m['river']['source_sheets']):
            a=source[name][1][tuple(xy)];b=compact.crop((x*8,y*8+f*h,x*8+8,y*8+f*h+8))
            assert a.tobytes()==b.tobytes();comparisons+=1
assert len(seen)==m['river']['original_cells']==3204
for name in ['Cascades_Metano_Exact','Riviere_Metano_Compacte']:
    im=Image.open(O/(name+'.png')).convert('RGBA');decoded,_=read_native(O/(name+'.tile'));assert decoded.tobytes()==im.tobytes()
    ts=json.loads((O/(name+'.tsj')).read_text());assert ts['tilewidth']==ts['tileheight']==8
    assert ts['columns']==im.width//8 and ts['tilecount']==(im.width//8)*(im.height//8)
    for tile in ts['tiles']:
        assert len(tile['animation'])==4
        assert all(0<=fr['tileid']<ts['tilecount'] for fr in tile['animation'])
proof=json.loads((S/'animations_carte.json').read_text());assert proof['TexSize']==1
river_records=[g for g in proof['animations'] if g['animation']['Frames'][0]['Sheet']=='Metano_Town_River_Animation_1']
assert sum(g['count'] for g in river_records)==3200
assert all(g['animation']['FrameLength']==10 and [f['Sheet'] for f in g['animation']['Frames']]==m['river']['source_sheets'] for g in river_records)
report={'status':'OK','cascade_frames':4,'cascade_pixel_differences':0,'river_source_tile_frame_comparisons':comparisons,'river_pixel_differences':0,'whole_atlas_premultiplied_roundtrip_differences':0,'native_tile_roundtrips':2,'original_map_TexSize':1,'verified_river_FrameLength':10,'not_verified':['Cadence originale des quatre rectangles autonomes de cascade : 10 ticks proposés pour aperçu','Lancement dans le moteur PMDO','Autorisations de redistribution des ressources tierces']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
