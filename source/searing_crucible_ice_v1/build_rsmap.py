"""Produce a complete PMDO ground map: Data/Map/frozen_crucible.rsmap.
Copy of the reference searing_crucible.rsmap where ONLY these change:
  * every cell's TileTex -> VastIceMountainPeak sheet, TexLoc taken from the canonical DumpAsset autotile
    (vast_ice_mountain_peak_wall/floor.json) for the cell's neighbour code and the same variant used by build.py;
  * the 8 decorations' AnimIndex -> Ice_Peak_* (.dir produced by pack_sprites.py);
  * steam emitter colour -> cold mist; Name/AssetName -> Frozen Crucible / frozen_crucible.
Everything else (geometry, entry, teams, music, script events, status list) is left untouched.
Also renders the rsmap from the DumpAsset VastIceMountainPeak.tile bank and checks it equals calques/01 (pixel-exact)."""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references';O=R/'renders/searing_crucible_ice_v1'
sys.path.insert(0,str(S));from decode import rsmap
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
m=json.loads((O/'manifest.json').read_text());cells={(c['x'],c['y']):c for c in m['cells']}
MAP=json.loads((R/'renders/dungeon_autotiles_v1/reference_manifest.json').read_text())['mapping']
auto={t:json.loads((REF/f'dumpasset/Data/AutoTile/vast_ice_mountain_peak_{t}.json').read_text(encoding='utf-8-sig'))['Object']['Tiles'] for t in ['wall','floor']}
NAMES={'Spring_Cave_Pit_Big_Lava_Stream':'Ice_Peak_Big_Frost_Stream','Spring_Cave_Pit_Small_Lava_Stream':'Ice_Peak_Small_Frost_Stream','Spring_Cave_Pit_Lava_Pool_Connected':'Ice_Peak_Frost_Pool_Connected','Spring_Cave_Pit_Lava_Pool_Disconnected':'Ice_Peak_Frost_Pool_Disconnected'}
raw=json.loads((REF/'nev5/Data/Map/searing_crucible.rsmap').read_bytes().decode('utf-8-sig'));o=raw['Object']
o['Name']['DefaultText']='Frozen Crucible';o['AssetName']='frozen_crucible';o['Comment']='Ice re-adaptation of Searing Crucible (lot searing_crucible_ice_v1). Ground: VastIceMountainPeak (DumpAsset). Objects: Ice_Peak_* (derived).'
g=o['Tiles'];W=len(g);H=len(g[0])
for x in range(W):
    for y in range(H):
        c=cells[(x,y)];code=MAP[c['slot']];variants=auto[c['type']][f'Tilex{code:02X}']
        var=variants[c['variant']] if c['variant']<len(variants) else variants[0]
        layers=[{'Frames':[{'Sheet':f['Sheet'],'TexLoc':dict(f['TexLoc'])} for f in l['Frames']],'FrameLength':l['FrameLength']} for l in var]
        g[x][y]['Data']['TileTex']={'AutoTileset':'','Associates':[],'Layers':layers,'NeighborCode':-1}
for dl in o['Decorations']:
    for a in dl['Anims']:a['ObjectAnim']['AnimIndex']=NAMES[a['ObjectAnim']['AnimIndex']]
o['Status']['steam']['Emitter']['Color']='170, 200, 230, 90'
out=O/'Data/Map';out.mkdir(parents=True,exist_ok=True);p=out/'frozen_crucible.rsmap'
p.write_bytes(('\ufeff'+json.dumps(raw,indent=2)).encode('utf-8'))
# render from the DumpAsset bank and compare with our layer
size,bank,_=tiles(REF/'dumpasset/Content/Tile/VastIceMountainPeak.tile');im=Image.new('RGBA',(W*24,H*24))
for x in range(W):
    for y in range(H):
        for l in g[x][y]['Data']['TileTex']['Layers']:
            f=l['Frames'][0];im.alpha_composite(straight(bank[(f['TexLoc']['X'],f['TexLoc']['Y'])]),(x*24,y*24))
im.save(O/'calques/01b_sol_rendu_depuis_rsmap.png');ours=Image.open(O/'calques/01_sol_vast_ice_mountain_peak_natif.png').convert('RGBA')
d=np.abs(np.array(im).astype(int)-np.array(ours).astype(int));ident=bool(d.max()==0)
print('rsmap',p,'rendered==layer',ident,'maxdiff',int(d.max()),'cells differing',int((d.max(axis=2)>0).reshape(H,24,W,24).max(axis=(1,3)).sum()))
json.dump(dict(rsmap=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),render_identical_to_layer=ident,tile_bank='audinowho/DumpAsset@d74394dc Content/Tile/VastIceMountainPeak.tile',runtime_validated=False),open(O/'rsmap_manifest.json','w'),indent=1)
