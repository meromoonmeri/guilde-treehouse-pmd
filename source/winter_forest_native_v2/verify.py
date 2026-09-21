"""Independent checks: every placed cell equals its unchanged native source rectangle."""
from pathlib import Path
import json, hashlib, zipfile, io, sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).resolve().parent;OUT=ROOT/'renders/winter_forest_native_v2';REF=SRC/'references';P='WinterNativeV2'
report={};checks=0
def ok(name,cond):
    global checks
    assert cond,name
    report[name]='PASS';checks+=1
prov=json.loads((SRC/'provenance.json').read_text())
for s in prov['sources']:
    ok('source hash '+s['file'],hashlib.sha256((REF/s['file']).read_bytes()).hexdigest()==s['sha256'])
sheets=[np.array(Image.open(REF/f'FrostyForest_tileset_{i}.png').convert('RGBA')) for i in range(3)]
for i,a in enumerate(sheets): ok(f'sheet {i} is 432x192',a.shape==(192,432,4))
net=json.loads((OUT/'network.json').read_text());world=np.array(json.loads((OUT/'world_grid.json').read_text()),bool)
placements=json.loads((OUT/'native_placements.json').read_text())
atlas=np.array(Image.open(OUT/f'{P}_NetworkTerrain.png').convert('RGBA'))
ok('atlas size 1008x1656',atlas.shape==(1656,1008,4))
covered=np.zeros(world.shape,int);forest_cells=0;exact=0
for p in placements:
    x,y=p['xy'];sx,sy,w,h=p['rect'];src=sheets[p['variant']][sy:sy+h,sx:sx+w]
    assert (src[:,:,3]==255).all(),'transparent rectangle used'
    if p['layer']=='forest':
        forest_cells+=1;assert not world[y,x]
        assert np.array_equal(atlas[y*24:y*24+24,x*24:x*24+24],src);exact+=1
    else:
        covered[y,x]+=1
        if world[y,x]: assert np.array_equal(atlas[y*24:y*24+24,x*24:x*24+24],src);exact+=1
ok('every cell has exactly one snow module',(covered==1).all())
ok('every forest cell placed once',forest_cells==int((~world).sum()))
ok('all visible atlas cells identical to native rectangles',exact==world.size)
report['exact_native_cells']=exact
colors=set(map(tuple,np.unique(np.concatenate([s.reshape(-1,4) for s in sheets]),axis=0)))
ok('atlas palette subset of source palette',set(map(tuple,np.unique(atlas.reshape(-1,4),axis=0)))<=colors)
for s in net['scenes']:
    base=OUT/s['id']/s['stem'];gx,gy=s['grid'];box=(slice(gy*552,gy*552+552),slice(gx*504,gx*504+504))
    terrain=np.array(Image.open(str(base)+'_Terrain.png').convert('RGBA'));ok(s['id']+' terrain equals atlas crop',np.array_equal(terrain,atlas[box]))
    snow=Image.open(str(base)+'_Snow.png').convert('RGBA');forest=Image.open(str(base)+'_Forest.png').convert('RGBA')
    ok(s['id']+' layers recompose terrain',np.array_equal(np.array(Image.alpha_composite(snow,forest)),terrain))
    with zipfile.ZipFile(str(base)+'_Layers.ora') as z:
        ok(s['id']+' ORA merged equals terrain',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),terrain))
    walk=np.array(Image.open(str(base)+'_WalkIntent.png'))>0;local=world[gy*23:gy*23+23,gx*21:gx*21+21]
    ok(s['id']+' walk intent matches grid',np.array_equal(walk[::24,::24],local))
    for d in 'NSEW':
        open_=dict(N=local[0,9:12],S=local[-1,9:12],W=local[10:13,0],E=local[10:13,-1])[d]
        ok(f'{s["id"]} border {d} {"open" if d in s["ports"] else "sealed"}',open_.all() if d in s['ports'] else not open_.any())
    # Passage: all walkable cells in a scene are 4-connected.
    from scipy import ndimage
    labels,n=ndimage.label(local);ok(s['id']+' single connected walkable region',n==1)
    for mode in ['boreal','cloudy']:
        pv=np.array(Image.open(str(base)+f'_{mode}_Preview.png').convert('RGBA'));ok(f'{s["id"]} {mode} preview holds terrain unchanged',np.array_equal(pv[336:888,0:504],terrain))
    anim=Image.open(str(base)+'_AnimatedPreview.webp');data=Path(str(base)+'_AnimatedPreview.webp').read_bytes();pos=12;total=0;n=0
    while pos+8<=len(data):
        tag=data[pos:pos+4];size=int.from_bytes(data[pos+4:pos+8],'little')
        if tag==b'ANMF': total+=int.from_bytes(data[pos+20:pos+23],'little');n+=1
        pos+=8+size+(size&1)
    ok(s['id']+' animated preview loops 6.4 s (identical frames merged by encoder)',total==6400 and n in (96,192))
for a,ap,b,bp in net['links']:
    if b=='arena_v5': continue
    ok(f'link {a}.{ap}-{b}.{bp} both declared',ap in next(s['ports'] for s in net['scenes'] if s['id']==a) and bp in next(s['ports'] for s in net['scenes'] if s['id']==b))
for label,count in [('powder',96),('flakes',96)]:
    ok(label+' frame count',len(list((OUT/'atmosphere'/label).glob('*.png')))==count)
report['checks']=checks;report['status']='PASS';report['runtime_validated']=False;report['note']='Pixel provenance and logical connectivity only; no PMDO collision, camera or gameplay validation.'
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS',checks,'checks;',exact,'native cells verified')
