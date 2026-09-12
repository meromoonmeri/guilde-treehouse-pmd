"""V2: corrected generated rock, separate generated sky/clouds, real indexed palette cycling.
Never overwrites V1. Cloud wrapping and palette rotation are independent animations.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,base64,math
R=Path(__file__).resolve().parents[1];S=R/'source/cote_v2';O=R/'sprites/cote_v2';O.mkdir(exist_ok=True)
OLD=R/'sprites/falaises_cotieres_nues'
def key_image(path):
    im=Image.open(path).convert('RGBA');a=np.asarray(im).copy();r,g,b=[a[:,:,i].astype(float) for i in range(3)]
    key=((r>160)&(b>145)&(r>g*1.35)&(b>g*1.35))|((r>100)&(b>100)&(r>g*1.8)&(b>g*1.8)&(b>r*.8)&(g<100));a[key]=0
    return Image.fromarray(a)
def digest(data):return hashlib.sha256(data).hexdigest()
cloud_source=key_image(S/'nuages_generes.png');a=np.asarray(cloud_source);occupied=a[:,:,3].any(axis=0);edges=np.diff(np.r_[False,occupied,False].astype(int));runs=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]));runs=[(int(x),int(y)) for x,y in runs if y-x>16];assert len(runs)==4,runs
clouds=[];source_boxes=[]
for i,(x0,x1) in enumerate(runs):
    ys=np.where(a[:,x0:x1,3].any(axis=1))[0];box=[x0,int(ys[0]),x1,int(ys[-1])+1];crop=cloud_source.crop(box);im=Image.new('RGBA',(math.ceil(crop.width/8)*8,math.ceil(crop.height/8)*8));im.paste(crop,(0,0));im.save(O/f'COTEV2_NUAGE_{i+1:02}.png',optimize=True);clouds.append(im);source_boxes.append(box)
P=math.ceil((sum(im.width for im in clouds)+128*len(clouds))/8)*8
CH=math.ceil((max(im.height for im in clouds)+32)/8)*8;horizon=CH+16
cloudtile=Image.new('RGBA',(P,CH));placements=[];x=64
for i,im in enumerate(clouds):
    y=CH-16-im.height;cloudtile.paste(im,(x,y));placements.append({'cloud':i+1,'dest_px':[x,y]});x+=im.width+128
assert x-64<=P
cloudtile.save(O/'COTEV2_NUAGES_WRAP.png',optimize=True)
assert not np.asarray(cloudtile)[:,:32,3].any() and not np.asarray(cloudtile)[:,-32:,3].any()
manifest={'version':2,'terrain_is_generated_not_canonical':True,'terrain_resampling':False,'cloud_resampling':False,'sky_fitting':'Generated sky resized with nearest-neighbor only; rock and cloud sprites never resized','clouds':{'source_sha256':digest((S/'nuages_generes.png').read_bytes()),'source_boxes':source_boxes,'transparent_padding_to_grid_px':8,'placements':placements,'tile':'COTEV2_NUAGES_WRAP.png','size_px':[P,CH],'period_px':P,'speed_px_per_second':12,'direction':'left','mode':'translation modulo period, NOT ping-pong','y':8,'sky_horizon_px':horizon,'horizontal_transparent_margin_min_px':32},'sea':{'mode':'fixed indexed PNG data, cyclic permutation of palette entries only','frame_count':8,'frame_ms':160,'moving_geometry':False,'quantization':False,'source':'V1 sea frame 1, derived from user Pelipper Post Office sheet; this is not Metano river animation'},'zones':[],'limits':['Generated terrain texture, not source-identical Metano tile assembly','Sky/clouds generated; source cloud colors preserved after chroma key','Sea indices remain fixed but the new palette sequence is original, not game metadata','No PMDO runtime test; PNG import alone does not enable wrapping or runtime palette rotation']}
view=[];previews=[]
def cloud_layer(w,h,offset=0):
    layer=Image.new('RGBA',(w,h));offset=offset%P
    for x in range(-offset,w,P):layer.paste(cloudtile,(x,8))
    return layer
for zi,name in enumerate(['01_promontoire','02_terrasse']):
    d=O/name;d.mkdir(exist_ok=True);prefix='COTEV2_'+str(zi+1).zfill(2)
    if zi==0:terrain=Image.open(OLD/name/'COTE01_02_TERRAIN_GENERE.png').convert('RGBA')
    else:terrain=key_image(S/'terrasse_roche_corrigee.png')
    w,h=terrain.size;assert w%8==h%8==0 and horizon<h
    terrain_file=prefix+'_03_TERRAIN.png';terrain.save(d/terrain_file,optimize=True)
    sky=Image.new('RGBA',(w,h));sky.paste(Image.open(S/'ciel_sans_nuages.png').convert('RGBA').resize((w,horizon),Image.Resampling.NEAREST),(0,0));sky_file=prefix+'_00_CIEL_SANS_NUAGES.png';sky.save(d/sky_file,optimize=True)
    overlay=cloud_layer(w,h);cloud_file=prefix+'_01_NUAGES_POSITION_0.png';overlay.save(d/cloud_file,optimize=True)
    # Reposition the previous phase-1 sea; no resampling or moving waves between phases.
    oldsea=Image.open(OLD/name/f'COTE{zi+1:02}_01_MER_01.png').convert('RGBA');sea=Image.new('RGBA',(w,h));sea.paste(oldsea,(0,horizon-208));raw=np.asarray(sea)
    colors,indices=np.unique(raw.reshape(-1,4),axis=0,return_inverse=True);assert len(colors)<=256 and list(colors[0])==[0,0,0,0]
    data=indices.reshape(h,w).astype('uint8');counts=np.bincount(data.ravel(),minlength=len(colors));dominant=int(np.argmax(counts[1:]))+1
    luminance=colors[:,:3].astype(float)@np.array([.2126,.7152,.0722]);eligible=[i for i in range(1,len(colors)) if i!=dominant]
    selected=sorted(eligible,key=lambda i:luminance[i])[-8:];assert len(selected)==8
    # Closed luminance traversal reduces the jump at the end of the palette ring.
    cycle=[selected[i] for i in [0,2,4,6,7,5,3,1]]
    basepal=np.zeros((256,3),np.uint8);basepal[:len(colors)]=colors[:,:3];alpha=np.zeros(256,np.uint8);alpha[:len(colors)]=colors[:,3]
    filenames=[];palettes=[]
    for f in range(8):
        pal=basepal.copy()
        for j,k in enumerate(cycle):pal[k]=basepal[cycle[(j+f)%8]]
        im=Image.fromarray(data,'P');im.putpalette(pal.ravel().tolist());im.info['transparency']=alpha.tobytes()
        fn=f'{prefix}_02_MER_PALETTE_{f:02}.png';im.save(d/fn,optimize=False);filenames.append(fn);palettes.append(pal[:len(colors)].tolist())
        assert im.tobytes()==data.tobytes()
        if f==0:assert im.convert('RGBA').tobytes()==sea.tobytes()
    record={'id':name,'dimensions_px':[w,h],'files':{'sky':sky_file,'clouds_static':cloud_file,'terrain':terrain_file,'sea':filenames},'cloud_tile':'../COTEV2_NUAGES_WRAP.png','sea_indices_sha256':digest(data.tobytes()),'sea_active_colors':len(colors),'sea_palette_base_rgb':basepal[:len(colors)].tolist(),'sea_palette_frames_rgb':palettes,'sea_alpha':alpha[:len(colors)].tolist(),'cycle_indices':cycle,'static_background_index':dominant,'terrain_pixels_sha256':digest(terrain.tobytes())}
    (d/'animation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));manifest['zones'].append(record)
    rgba0=Image.open(d/filenames[0]).convert('RGBA');full=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(sky,overlay),rgba0),terrain);full.save(d/(prefix+'_COMPOSITION_00.png'),optimize=True)
    assert cloud_layer(w,h,0).tobytes()==cloud_layer(w,h,P).tobytes()
    im=full.convert('RGB');im.thumbnail((640,480),Image.Resampling.NEAREST);previews.append(im)
    def uri(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
    view.append({'id':name,'w':w,'h':h,'sky':uri(d/sky_file),'terrain':uri(d/terrain_file),'sea':[uri(d/f) for f in filenames],'palettes':palettes,'cycle':cycle})
manifest['source_hashes']={n:digest((S/n).read_bytes()) for n in ['terrasse_roche_corrigee.png','ciel_sans_nuages.png','nuages_generes.png','reference_metano_modules.png']}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
board=Image.new('RGB',(1312,568),'#20372a');dr=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for i,im in enumerate(previews):board.paste(im,(16+i*656,48));dr.text((16+i*656,15),['Promontoire · nouveau ciel et mer','Terrasse · roche corrigée'][i],font=font,fill='#ebd99b')
dr.text((16,540),'4 calques : ciel fixe / nuages wrap / mer à palette cyclique / terrain. Aperçu réduit.',font=font,fill='#ebd99b');board.save(O/'APERCU_NE_PAS_IMPORTER.png',optimize=True)
html=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(view)).replace('__CLOUD__',json.dumps('data:image/png;base64,'+base64.b64encode((O/'COTEV2_NUAGES_WRAP.png').read_bytes()).decode())).replace('__PERIOD__',str(P)).replace('__CLOUDY__','8')
(R/'apercu_cote_v2.html').write_text(html)
print('Built corrected terrace, generated sky, four cloud sprites with wrap strip, 8 indexed sea palettes per scene. Cloud period:',P,'sky height:',horizon)
