"""Decode the reference Searing Crucible rsmap: static tile layer + 4 animated Object decorations."""
from pathlib import Path
import sys,json,struct,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references/nev5';OUT=R/'renders/searing_crucible_ice_v1/reference'
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
def load_dir(p):
    d=Path(p).read_bytes();n=struct.unpack('<q',d[:8])[0];im=Image.open(io.BytesIO(d[8:8+n])).convert('RGBA');w,h,rot,frames=struct.unpack('<4i',d[8+n:8+n+16])
    cols=im.width//w;out=[]
    for i in range(frames):
        fr=straight(im.crop(((i%cols)*w,(i//cols)*h,(i%cols)*w+w,(i//cols)*h+h)));out.append(fr)
    return out,w,h
def rsmap():
    return json.loads((REF/'Data/Map/searing_crucible.rsmap').read_bytes().decode('utf-8-sig'))['Object']
def render_static(o,bank):
    tl=o['Layers'][0]['Tiles'];W=len(tl);H=len(tl[0]);im=Image.new('RGBA',(W*24,H*24))
    # ground texture stored in Tiles[x][y].Data.TileTex; Layers[0] is empty here
    grid=o['Tiles'];terrain=np.zeros((H,W),dtype='U12')
    for x in range(W):
        for y in range(H):
            t=grid[x][y];terrain[y,x]=t['Data']['ID']
            for l in t['Data']['TileTex']['Layers']:
                f=l['Frames'][0];im.alpha_composite(bank[f['Sheet']][f['TexLoc']['X'],f['TexLoc']['Y']],(x*24,y*24))
            for l in tl[x][y]['Layers']:
                f=l['Frames'][0];im.alpha_composite(bank[f['Sheet']][f['TexLoc']['X'],f['TexLoc']['Y']],(x*24,y*24))
    return im,terrain
if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True);o=rsmap()
    size,b,_=tiles(REF/'Content/Tile/Spring_Cave_Pit.tile');bank={'Spring_Cave_Pit':{k:straight(v) for k,v in b.items()}}
    static,terrain=render_static(o,bank);static.save(OUT/'crucible_static.png')
    anims={};decos=[]
    for dl in o['Decorations']:
        for a in dl['Anims']:
            oa=a['ObjectAnim'];name=oa['AnimIndex']
            if name not in anims:anims[name]=load_dir(REF/f'Content/Object/{name}.dir')
            decos.append(dict(name=name,x=a['MapLoc']['X'],y=a['MapLoc']['Y'],frame_time=oa['FrameTime'],flip=oa['AnimFlip'],alpha=oa['Alpha']))
    frames=[]
    for t in range(0,252,4):  # 63 frames * FrameTime4 = 252 game frames per loop
        f=static.copy()
        for d in decos:
            fr,w,h=anims[d['name']];i=(t//d['frame_time'])%len(fr);img=fr[i]
            if d['flip']:img=img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            f.alpha_composite(img,(d['x'],d['y']))
        frames.append(f)
    frames[0].save(OUT/'crucible_animated_reference.webp',save_all=True,append_images=frames[1:],duration=round(4*1000/60),loop=0,lossless=True)
    frames[0].save(OUT/'crucible_frame0.png')
    (OUT/'reference_decode.json').write_text(json.dumps(dict(map_size_tiles=[len(o['Tiles']),len(o['Tiles'][0])],terrain_counts={k:int(v) for k,v in zip(*np.unique(terrain,return_counts=True))},decorations=decos,anims={k:dict(frames=len(v[0]),w=v[1],h=v[2]) for k,v in anims.items()},status=list(o['Status'].keys()),music=o['Music'],entry=o['EntryPoints']),indent=2))
    print('decoded',static.size,len(decos),'decorations',{k:len(v[0]) for k,v in anims.items()})
