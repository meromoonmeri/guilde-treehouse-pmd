"""Validation des PNG, raccords, formats .tile et références d'animation (sans moteur)."""
from pathlib import Path
from PIL import Image
import struct, io, json
P=Path(__file__).resolve().parents[1]/'sprites/ponts_pmdo'
for mode in ('jour','nuit'):
    atlas=Image.open(P/f'tilesheet_{mode}.png').convert('RGBA')
    assert atlas.size==(480,320)
    assert set(atlas.getchannel('A').getdata())=={0,255}
    assert len(atlas.getcolors(100000))<=48
    for f in range(4):
        path=P/f'Ponts_Dores_{mode}_{f+1}.tile'; data=path.read_bytes()
        size,n=struct.unpack_from('<II',data); assert (size,n)==(8,600)
        decoded=Image.new('RGBA',(480,80))
        for i in range(n):
            x,y,off=struct.unpack_from('<IIQ',data,8+i*16)
            assert x<60 and y<10 and off>=8+16*n
            length=struct.unpack_from('<q',data,off)[0]
            assert off+8+length<=len(data)
            tile=Image.open(io.BytesIO(data[off+8:off+8+length])).convert('RGBA');assert tile.size==(8,8)
            assert all(a==255 or (r,g,b,a)==(0,0,0,0) for r,g,b,a in tile.getdata())
            decoded.paste(tile,(x*8,y*8))
        row=atlas.crop((0,f*80,480,(f+1)*80))
        assert decoded.tobytes()==row.tobytes()
        for left,right in [(0,1),(1,1),(1,2)]:
            assert row.crop((left*80+79,0,left*80+80,80)).tobytes()==row.crop((right*80,0,right*80+1,80)).tobytes()
        for top,bottom in [(3,4),(4,4),(4,5)]:
            assert row.crop((top*80,79,top*80+80,80)).tobytes()==row.crop((bottom*80,0,bottom*80+80,1)).tobytes()
    stamps=json.loads((P/f'stamps_{mode}.json').read_text())
    assert len(stamps['modules'])==6
    for module in stamps['modules']:
        for cell in module['cells']:
            anim=cell['tile']['Layers'][0]; assert anim['FrameLength']==11 and len(anim['Frames'])==4
            for frame in anim['Frames']:
                assert (P/(frame['Sheet']+'.tile')).exists()
                assert 0<=frame['TexLoc']['X']<60 and 0<=frame['TexLoc']['Y']<10
    ts=json.loads((P/f'tilesheet_{mode}.tsj').read_text())
    for t in ts['tiles']:
        assert len(t['animation'])==4
        assert all(0<=a['tileid']<2400 and a['duration']==180 for a in t['animation'])
report={'status':'OK','checks':['PNG RGBA, dimensions et palette 48 couleurs','Alpha binaire et RGB transparent nul','8 fichiers .tile relus, reconstitution exacte des PNG','Raccords horizontaux et verticaux exacts aux quatre phases','Références et coordonnées des animations Tiled et PMDO'], 'not_checked':['Ouverture dans le moteur PMDO','TexSize et placement dans WaterfallVillageCapital.rsground (téléchargement LFS inaccessible)']}
(P/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
