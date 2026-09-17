"""Clean generated terrain + separate animated sky/sea from the user's reference sheet.
Generated terrain is explicitly NOT certified as canonical Metano tile art.
No source art is resized in the exports. Only previews are reduced.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,base64
R=Path(__file__).resolve().parents[1];S=R/'source/falaises_cotieres_nues';O=R/'sprites/falaises_cotieres_nues';O.mkdir(exist_ok=True)
sheet=Image.open(S/'reference_ciel_mer.png').convert('RGBA')
sky=sheet.crop((544,8,1264,216))
sea=[sheet.crop((544+56*f,224,592+56*f,352)) for f in range(5)]
near_sea=[sheet.crop((824+56*f,224,872+56*f,392)) for f in range(5)]
# Background animation timing is proposed, not recovered from the original game's metadata.
shifts=[0,2,4,6,8,6,4,2]
manifest={'status':'generated_terrain_with_reference_backdrops','terrain_is_canonical_metano':False,'terrain_resized':False,'source_sea_sky':'User upload IMG_4890.png, commit 3bc185b; Pelipper Post Office sheet, ripped by Jaxster; original game art Nintendo/Game Freak/Chunsoft','reference_sha256':hashlib.sha256((S/'reference_ciel_mer.png').read_bytes()).hexdigest(),'sky_rect':[544,8,1264,216],'sea_rects':[[544+56*f,224,592+56*f,352] for f in range(5)],'near_sea_rects':[[824+56*f,224,872+56*f,392] for f in range(5)],'sky_motion':'8-phase slow horizontal oscillation of the source strip, 600 ms per phase','water_motion':'5 source strips in left-to-right order, 150 ms per phase; timing/order proposed','zones':[],'limits':['Generated rock and grass, not an exact assembly of Metano native tiles','No PMDO runtime import test','Only terrain is generated; sky and sea are extracted/repeated from the user reference, not Metano river assets','Source strips repeat in the background; new layouts and timing are not official game assets']}
viewer_data=[];thumbs=[]
for i,name in enumerate(['01_promontoire','02_terrasse']):
    d=O/name;d.mkdir(exist_ok=True);prefix='COTE'+str(i+1).zfill(2)
    src=Image.open(S/(name+'.png')).convert('RGBA');a=np.asarray(src).copy();r,g,b=[a[:,:,j].astype(float) for j in range(3)]
    key=((r>160)&(b>145)&(r>g*1.35)&(b>g*1.35))|((r>100)&(b>100)&(r>g*1.8)&(b>g*1.8)&(b>r*.8)&(g<100))
    a[key]=0;terrain=Image.fromarray(a);w,h=terrain.size;assert w%8==h%8==0
    translate_y=256 if i==0 else 0
    if translate_y:
        placed=Image.new('RGBA',(w,h));placed.paste(terrain,(0,translate_y));terrain=placed
    assert np.array_equal(np.asarray(src)[~key],a[~key]),'Non-keyed generated pixels changed'
    terrain_name=prefix+'_02_TERRAIN_GENERE.png';terrain.save(d/terrain_name,optimize=True)
    horizon=208;sky_names=[];sea_names=[]
    for f,shift in enumerate(shifts):
        layer=Image.new('RGBA',(w,h))
        # Repeat first source row above the 208px cloud strip, without creating new colors.
        for yy in range(max(0,horizon-208)):
            for xx in range(-720,w,720):layer.paste(sky.crop((0,0,720,1)),(xx+shift,yy))
        for xx in range(-720,w,720):layer.paste(sky,(xx+shift,horizon-208))
        fn=f'{prefix}_00_CIEL_{f+1:02}.png';layer.save(d/fn,optimize=True);sky_names.append(fn)
    for f,strip in enumerate(sea):
        layer=Image.new('RGBA',(w,h))
        for xx in range(0,w,48):layer.paste(strip,(xx,horizon))
        for yy in range(horizon+128,h,168):
            for xx in range(0,w,48):layer.paste(near_sea[f],(xx,yy))
        fn=f'{prefix}_01_MER_{f+1:02}.png';layer.save(d/fn,optimize=True);sea_names.append(fn)
    sky0=Image.open(d/sky_names[0]).convert('RGBA');sea0=Image.open(d/sea_names[0]).convert('RGBA');full=Image.alpha_composite(Image.alpha_composite(sky0,sea0),terrain)
    full.save(d/(prefix+'_COMPOSITION_FIXE.png'),optimize=True)
    # Inspectable manifest: independent PNG layers with a common origin and native dimensions.
    record={'id':name,'size_px':[w,h],'origin_px':[0,0],'generated_terrain_translation_y':translate_y,'import_cell_px':8,'horizon_px':horizon,'terrain':terrain_name,'sky':sky_names,'sea':sea_names,'source_generated_sha256':hashlib.sha256((S/(name+'.png')).read_bytes()).hexdigest(),'keyed_pixels':int(key.sum()),'nonkey_generated_pixels_modified':0}
    for names in [sky_names,sea_names]:assert len({hashlib.sha256((d/f).read_bytes()).hexdigest() for f in names})==len(set(shifts)) if names==sky_names else len({hashlib.sha256((d/f).read_bytes()).hexdigest() for f in names})==5
    manifest['zones'].append(record)
    def url(fn):return 'data:image/png;base64,'+base64.b64encode((d/fn).read_bytes()).decode()
    viewer_data.append({'id':name,'w':w,'h':h,'terrain':url(terrain_name),'sky':[url(fn) for fn in sky_names],'sea':[url(fn) for fn in sea_names]})
    im=full.convert('RGB');im.thumbnail((640,480),Image.Resampling.NEAREST);thumbs.append(im)
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
board=Image.new('RGB',(1312,560),'#20372a');draw=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for i,im in enumerate(thumbs):board.paste(im,(16+656*i,48));draw.text((16+656*i,15),['Promontoire nu','Terrasse nue'][i],font=font,fill='#e6d89c')
draw.text((16,532),'Aperçu réduit — terrains générés, sans bâtiments, arbres ni objets. Ciel et mer séparés.',font=font,fill='#e6d89c');board.save(O/'APERCU_NE_PAS_IMPORTER.png',optimize=True)
template=(S/'viewer.html').read_text();(R/'apercu_falaises_cotieres_nues.html').write_text(template.replace('__DATA__',json.dumps(viewer_data)))
print('Built 2 bare terrain PNGs, 16 sky frames, 10 sea frames, 2 still composites and offline animated viewer.')
