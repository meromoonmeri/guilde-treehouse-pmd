"""Validation hors moteur des 10 huttes et du format PMDO natif."""
from pathlib import Path
from PIL import Image
import json,struct,io,hashlib
P=Path(__file__).resolve().parents[1]/'sprites/maisons_metano'
m=json.loads((P/'maisons.json').read_text());assert len(m['houses'])==10
hashes=set()
for mode in ['jour','nuit']:
    atlas=Image.open(P/f'Maisons_Metano_{mode}.png').convert('RGBA');assert atlas.size==(560,256)
    rebuilt=Image.new('RGBA',atlas.size)
    for h in m['houses']:
        im=Image.open(P/h['files'][mode]).convert('RGBA');assert im.size==(112,128)
        assert set(im.getchannel('A').getdata())=={0,255}
        assert all(a==255 or (r,g,b,a)==(0,0,0,0) for r,g,b,a in im.getdata())
        assert im.getbbox() and im.getbbox()[3]<=120
        assert len(im.getcolors(100000))<=48
        assert not any(r>180 and b>180 and g<70 for r,g,b,a in im.getdata() if a)
        if mode=='jour':hashes.add(hashlib.sha256(im.tobytes()).hexdigest())
        x,y,w,hh=h['atlas_rect_px'];assert all(v%8==0 for v in [x,y,w,hh])
        rebuilt.paste(im,(x,y))
    assert rebuilt.tobytes()==atlas.tobytes()
    data=(P/f'Maisons_Metano_{mode}.tile').read_bytes();size,n=struct.unpack_from('<II',data);assert (size,n)==(8,2240)
    decoded=Image.new('RGBA',atlas.size)
    for i in range(n):
        x,y,off=struct.unpack_from('<IIQ',data,8+16*i);assert x<70 and y<32 and off>=8+n*16
        length=struct.unpack_from('<q',data,off)[0];assert off+8+length<=len(data)
        tile=Image.open(io.BytesIO(data[off+8:off+8+length])).convert('RGBA');assert tile.size==(8,8)
        decoded.paste(tile,(x*8,y*8))
    assert decoded.tobytes()==atlas.tobytes()
    ts=json.loads((P/f'Maisons_Metano_{mode}.tsj').read_text());assert ts['tilewidth']==ts['tileheight']==8 and ts['tilecount']==2240
assert len(hashes)==10
report={'status':'OK','houses':10,'individual_png':20,'native_tile_files':2,'checks':['Dimensions, alignement grille 8 px et ligne de base','10 images distinctes','Transparence binaire et absence de magenta vif','Palette limitée par maison','Recomposition exacte des atlas depuis les PNG','Décodage indépendant des .tile égal aux atlas PNG','Dimensions et références des TSJ'],'not_checked':['Ouverture et placement dans PMDO','Collisions, zones d’entrée et occlusion','Fidélité artistique subjective au style Métano']}
(P/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
