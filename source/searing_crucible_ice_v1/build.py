"""Searing Crucible -> ice re-adaptation (lot searing_crucible_ice_v1).

* Geometry: the exact 21x21 floor/unbreakable grid of the reference rsmap (New-Era V5 @cb6e902f).
* Ground: canonical VastIceMountainPeak DTEF autotile (PMDCollab/RawAsset @03c80dad), wall/floor
  resolved with the AutoTileAdjacent 47-case mapping already audited in renders/dungeon_autotiles_v1.
  Native cells are copied without recoloring, rotation or scaling.
* Animations: the four native 63-frame lava Object animations (FrameTime 4, mirrored pairs, same MapLoc)
  are re-palettised to a glacial palette (lava -> glowing ice, rock -> VastIceMountainPeak wall blues).
  This palette transfer is a DERIVED animation, disclosed as such (not certified canonical pixels).
* Overlay: the native Steam BG (128x128) recoloured at runtime by the engine colour -> here a cold
  mist (170,200,230,90) moving y -20 like the reference status emitter.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references';OUT=R/'renders/searing_crucible_ice_v1'
sys.path.insert(0,str(S));from decode import load_dir,rsmap
MAP=json.loads((R/'renders/dungeon_autotiles_v1/reference_manifest.json').read_text())['mapping'];SLOT={m:i for i,m in enumerate(MAP) if m>=0}
T=24
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# ---------- geometry ----------
o=rsmap();g=o['Tiles'];W=len(g);H=len(g[0])
floor=np.array([[g[x][y]['Data']['ID']=='floor' for x in range(W)] for y in range(H)])
# ---------- canonical autotile ----------
sheets=[Image.open(REF/f'rawasset/VastIceMountainPeak/tileset_{i}.png').convert('RGBA') for i in range(3)]
def code(x,y,is_wall):
    def q(dx,dy):
        nx,ny=x+dx,y+dy
        return True if not(0<=nx<W and 0<=ny<H) else (not floor[ny,nx])==is_wall
    dirs=[(0,1),(-1,0),(0,-1),(1,0)];bits=[q(*d) for d in dirs];v=sum(1<<i for i,b in enumerate(bits) if b)
    for i,diag in enumerate([(-1,1),(-1,-1),(1,-1),(1,1)]):
        if bits[i] and bits[(i+1)%4] and q(*diag):v|=1<<(i+4)
    return v
def cell(typ,slot,x,y):
    sx=(typ*6+slot%6)*T;sy=slot//6*T;box=(sx,sy,sx+T,sy+T)
    choices=[i for i in range(3) if sheets[i].crop(box).getbbox()];i=choices[(x*13+y*7)%len(choices)] if choices else 0
    return sheets[i].crop(box),i,box
ground=Image.new('RGBA',(W*T,H*T));cells=[]
for y in range(H):
    for x in range(W):
        wall=not floor[y,x];typ=0 if wall else 2;slot=SLOT[code(x,y,wall)];im,var,box=cell(typ,slot,x,y);ground.alpha_composite(im,(x*T,y*T))
        cells.append(dict(x=x,y=y,type='wall' if wall else 'floor',slot=slot,variant=var,box=box))
# ---------- animations: palette transfer ----------
# Explicit palette map of the native lava sprites (13 opaque colours, audited in the manifest).
# (127,79,71) is the Spring_Cave_Pit floor colour baked as sprite backing -> transparent, the canonical ice floor shows through.
PAL={(127,79,71):(0,0,0,0),
 # lava ramp (dark -> hot) -> glowing ice ramp
 (159,47,39):(88,150,214,255),(207,23,0):(120,184,236,255),(223,47,0):(160,214,248,255),(239,79,0):(204,238,255,255),(247,127,0):(244,252,255,255),
 (199,23,0):(112,176,232,255),(215,47,0):(150,206,246,255),(231,79,0):(194,232,254,255),(239,127,0):(236,250,255,255),
 # crust / rock ramp -> VastIceMountainPeak wall blues (63,79,119)..(119,135,159)
 (55,31,31):(47,63,103,255),(63,31,31):(55,71,111,255),(63,39,39):(59,75,115,255),(71,31,31):(59,73,113,255),(79,47,47):(63,79,119,255),(95,55,55):(71,87,127,255),(111,63,63):(79,95,135,255),
 (119,71,71):(87,119,143,255),(135,87,87):(103,127,151,255),(159,103,103):(119,135,159,255)}
def frost(im):
    a=np.array(im);out=np.zeros_like(a);key=a[...,0].astype(int)*65536+a[...,1].astype(int)*256+a[...,2].astype(int);vis=a[...,3]>0
    for (r,g,b),v in PAL.items():out[(key==r*65536+g*256+b)&vis]=v
    # lava pixels pulse in brightness over the 63 frames (r 191..247, g 23..127): map by brightness onto the ice ramp
    lava=vis&(out[...,3]==0)&(key!=127*65536+79*256+71)&(a[...,0].astype(int)>a[...,1].astype(int)+60)
    if lava.any():
        t=np.clip((a[...,0].astype(float)+a[...,1]-200)/(374-200),0,1)[lava][:,None];out[...,:3][lava]=np.rint(ICE_LO+(ICE_HI-ICE_LO)*t);out[...,3][lava]=255
    unk=vis&(out[...,3]==0)&(key!=127*65536+79*256+71);assert not unk.any(),np.unique(a[unk],axis=0)
    return Image.fromarray(out)
ICE_LO=np.array([132,196,244]);ICE_HI=np.array([244,252,255]);ROCK_LO=np.array([47,63,103]);ROCK_HI=np.array([119,135,159])
NAMES={'Spring_Cave_Pit_Big_Lava_Stream':'Ice_Peak_Big_Frost_Stream','Spring_Cave_Pit_Small_Lava_Stream':'Ice_Peak_Small_Frost_Stream','Spring_Cave_Pit_Lava_Pool_Connected':'Ice_Peak_Frost_Pool_Connected','Spring_Cave_Pit_Lava_Pool_Disconnected':'Ice_Peak_Frost_Pool_Disconnected'}
anims={};decos=[]
(OUT/'objets_animes').mkdir(parents=True,exist_ok=True);(OUT/'calques').mkdir(exist_ok=True)
for dl in o['Decorations']:
    for a in dl['Anims']:
        oa=a['ObjectAnim'];src=oa['AnimIndex'];name=NAMES[src]
        if name not in anims:
            fr,w,h=load_dir(REF/f'nev5/Content/Object/{src}.dir');ice=[frost(f) for f in fr];anims[name]=(ice,w,h)
            strip=Image.new('RGBA',(w*len(ice),h))
            for i,f in enumerate(ice):strip.paste(f,(i*w,0))
            strip.save(OUT/'objets_animes'/f'{name}_{w}x{h}_{len(ice)}f.png')
            cmp=Image.new('RGBA',(w*8,h*2))
            for k,i in enumerate(range(0,63,8)):cmp.paste(fr[i],(k*w,0));cmp.paste(ice[i],(k*w,h))
            cmp.save(OUT/'objets_animes'/f'comparatif_{src}_vs_{name}.png')
        decos.append(dict(name=name,source=src,x=a['MapLoc']['X'],y=a['MapLoc']['Y'],frame_time=oa['FrameTime'],flip=oa['AnimFlip']))
# ---------- overlay: native Steam BG as cold mist ----------
steam,_,_=load_dir(REF/'nev5/Content/BG/Steam.dir');steam=steam[0]
MIST=(170,200,230,90)
def mist_layer(t):
    lay=Image.new('RGBA',ground.size);m=np.array(steam).astype(float);col=np.zeros_like(m);col[...,:3]=MIST[:3];col[...,3]=m[...,3]*MIST[3]/255*200/255
    tile=Image.fromarray(col.astype('uint8'));oy=int(-20*t/60)%128
    for yy in range(-128,ground.height+128,128):
        for xx in range(0,ground.width,128):lay.alpha_composite(tile,(xx,yy+oy))
    return lay
# ---------- layers + frames ----------
ground.save(OUT/'calques/01_sol_vast_ice_mountain_peak_natif.png')
decor0=Image.new('RGBA',ground.size)
for d in decos:
    fr,w,h=anims[d['name']];img=fr[0]
    if d['flip']:img=img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    decor0.alpha_composite(img,(d['x'],d['y']))
decor0.save(OUT/'calques/02_flux_glace_frame0.png');mist_layer(0).save(OUT/'calques/03_brume_froide_frame0.png')
frames=[];frames_nomist=[]
for t in range(0,252,4):
    f=ground.copy()
    for d in decos:
        fr,w,h=anims[d['name']];img=fr[(t//d['frame_time'])%len(fr)]
        if d['flip']:img=img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        f.alpha_composite(img,(d['x'],d['y']))
    frames_nomist.append(f.copy());f.alpha_composite(mist_layer(t));frames.append(f)
dur=round(4*1000/60)
frames[0].save(OUT/'creuset_glace_anime.webp',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True)
frames_nomist[0].save(OUT/'creuset_glace_anime_sans_brume.webp',save_all=True,append_images=frames_nomist[1:],duration=dur,loop=0,lossless=True)
frames[0].save(OUT/'creuset_glace_frame0.png')
# planche: reference vs ice
ref=Image.open(OUT/'reference/crucible_frame0.png').convert('RGBA');pl=Image.new('RGBA',(ref.width*2+12,ref.height),(20,20,30,255));pl.paste(ref,(0,0));pl.paste(frames[0],(ref.width+12,0));pl.save(OUT/'planche_reference_vs_glace.png')
manifest=dict(lot='searing_crucible_ice_v1',map_size_tiles=[W,H],pixels=list(ground.size),floor_cells=int(floor.sum()),wall_cells=int((~floor).sum()),
 autotile=dict(sheet='VastIceMountainPeak',source='PMDCollab/RawAsset@03c80dad937911572f8fb19903771a47956fc696 TileDtef/VastIceMountainPeak/tileset_{0,1,2}.png',mapping='renders/dungeon_autotiles_v1/reference_manifest.json',recolor=False,rotation=False,scale=False),
 animations={k:dict(frames=len(v[0]),w=v[1],h=v[2],frame_time=4,loop_game_frames=252,kind='palette transfer of native lava animation (derived, not canonical)') for k,v in anims.items()},
 decorations=decos,overlay=dict(source='nev5 Content/BG/Steam.dir',color=MIST,speed_y=-20,kind='native BG, engine-style colour'),
 palette=dict(map={str(k):v for k,v in PAL.items()},ice=[ICE_LO.tolist(),ICE_HI.tolist()],rock=[ROCK_LO.tolist(),ROCK_HI.tolist()]),
 references={str(p.relative_to(S)):sha(p) for p in sorted(REF.rglob('*')) if p.is_file()},cells=cells,runtime_validated=False)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=1))
print('ok',ground.size,len(frames),'frames',{k:len(v[0]) for k,v in anims.items()})
