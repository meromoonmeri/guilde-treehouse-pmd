"""Independent native rectangle / layout / PNG-to-8px-tiles roundtrip checks.
The import test simulates the source importer partitioning, not PMDO GPU execution.
"""
from pathlib import Path
from PIL import Image
import json,struct,io,hashlib
R=Path(__file__).resolve().parents[1];O=R/'sprites/metano_import_png';M=json.loads((O/'manifest.json').read_text());sources={}
PIN={'Metano_Town_Base':'19b295495e49819b356c02d13a574616dd67d36c','Metano_Town_Cliffs':'6d342b97ebfcad3e9aa6022b49e0f3b5b9d75640'}
for name,sha in PIN.items():
    raw=(R/M['sources'][name]['path']).read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==sha
    size,count=struct.unpack_from('<II',raw);assert size==8;tiles={};cache={}
    for i in range(count):
        x,y,offset=struct.unpack_from('<IIQ',raw,8+i*16)
        if offset not in cache:
            length=struct.unpack_from('<q',raw,offset)[0];im=Image.open(io.BytesIO(raw[offset+8:offset+8+length])).convert('RGBA')
            pixels=[(round(r*255/a),round(g*255/a),round(b*255/a),a) if 0<a<255 else (r,g,b,a) for r,g,b,a in im.getdata()];im.putdata(pixels);cache[offset]=im
        tiles[x,y]=cache[offset]
    sources[name]=tiles
modules={}
for name,info in M['modules'].items():
    x0,y0,x1,y1=info['source_rect_px'];expected=Image.new('RGBA',(x1-x0,y1-y0))
    for y in range(y0//8,y1//8):
        for x in range(x0//8,x1//8):
            im=sources[info['sheet']].get((x,y))
            if im:expected.paste(im,(x*8-x0,y*8-y0))
    actual=Image.open(O/info['file']).convert('RGBA');assert actual.size==expected.size and actual.tobytes()==expected.tobytes();modules[name]=actual
assert Image.open(O/'METANO_V3_TEMOIN_64x96.png').convert('RGBA').tobytes()==modules['retour_arrondi'].tobytes()
records=[]
for z in M['zones']:
    d=O/z['id'];w,h=z['size'];floor=Image.new('RGBA',(w,h));cliffs=Image.new('RGBA',(w,h));occupied=set()
    for y in range(h//8):
        for x in range(w//8):floor.paste(sources['Metano_Town_Base'][x%16,80+y%16],(x*8,y*8))
    for p in z['placements']:
        x,y=p['dest_px'];im=modules[p['module']];assert x%8==y%8==0 and x>=0 and y>=0 and x+im.width<=w and y+im.height<=h
        # Whole module rectangles must not overlap; no accidental erasure of another face.
        cells={(tx,ty) for tx in range(x//8,(x+im.width)//8) for ty in range(y//8,(y+im.height)//8)}
        assert not (cells&occupied);occupied|=cells;cliffs.paste(im,(x,y))
    prefix='METANO_V3_'+z['id'][3:].upper()
    for suffix,expected in [('SOL',floor),('FALAISES',cliffs),('SCENE',Image.alpha_composite(floor,cliffs))]:
        path=d/(prefix+'_'+suffix+'.png');actual=Image.open(path);assert actual.mode=='RGBA' and actual.size==(w,h)
        assert actual.tobytes()==expected.tobytes();assert hashlib.sha256(path.read_bytes()).hexdigest()==z['files'][path.name]['sha256']
    records.append({'zone':z['id'],'native_module_placements':len(z['placements']),'source_module_resizes':0,'overlapping_module_rectangles':0,'layer_composition_different_pixels':0})
roundtrips=[];names=set()
for path in sorted(O.rglob('*.png')):
    assert path.stem not in names,'PMDO names sheets by basename: collision';names.add(path.stem)
    im=Image.open(path).convert('RGBA');w,h=im.size;assert w%8==h%8==0
    rebuilt=Image.new('RGBA',im.size);nonempty=0
    for y in range(0,h,8):
        for x in range(0,w,8):
            tile=im.crop((x,y,x+8,y+8))
            if tile.getchannel('A').getbbox():rebuilt.paste(tile,(x,y));nonempty+=1
    assert rebuilt.tobytes()==im.tobytes(),('PNG tile roundtrip',path.name)
    roundtrips.append({'png':str(path.relative_to(O)),'size_px':[w,h],'tile_size':8,'nonempty_cells':nonempty,'different_pixels':0})
report={'status':'PASS','pinned_sources':PIN,'modules_source_identical':len(modules),'unique_pmdo_sheet_names':True,'zones':records,'png_import_partition_tests':roundtrips,'runtime_pmdo_tested':False,'artistic_quality_scope':'Whole original modules preserved; visual inspection performed separately. Not an automatic certification of every new join.'}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS:',len(modules),'native modules;',len(records),'scenes;',len(roundtrips),'PNG split/recompose tests; unique sheet names; no native rescaling.')
