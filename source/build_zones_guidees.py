"""Générateur -> guide de composition -> sélection de VRAIES tuiles 8px.
Le générateur n'est pas modifié. Ses pixels ne sont jamais copiés dans les textures finales.
Dépendances : Pillow, numpy, scipy. Reconstruction reproductible depuis les guides conservés.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
import json,hashlib
from zones_guidees.native_tools import Bank,ROOT,BASE,CLIFF,ANIM,RIVERS

O=ROOT/'sprites/zones_guidees';O.mkdir(exist_ok=True)
W,H=2048,1536;GW,GH=256,192;NAME='Zones_Guidees_Canon_8px'
bank=Bank()

def rock(a):
    r,g,b=a[...,0],a[...,1],a[...,2]
    return (r>g+9)&(r>90)&(g>45)&(b<g*1.15)

def feature(a):
    # Features describe the generated geometry ONLY; all candidates remain unmodified native sprites.
    rgb=a.reshape(-1,4,2,4,2,3).mean(axis=(2,4)).reshape(-1,48)/255
    mask=rock(a).reshape(-1,64).astype(np.float32)
    return np.concatenate([rgb*.45,mask*1.2],axis=1).astype(np.float32)

# Reference vocabulary excludes stairs, cave and water columns from the dry reconstruction.
allowed=set(range(57,93))|set(range(114,122))|set(range(162,189))
candidates=[];refs=[];by_coord={};by_pixels={};grass0=bank.image(bank.get(BASE,0,80))
for (x,y),raw in sorted(bank.sources[CLIFF].items()):
    if x not in allowed or y<(26 if x<93 else 38 if x>=162 else 54):continue
    if raw.getbbox() is None:continue
    gid=bank.get(CLIFF,x,y);img=Image.alpha_composite(grass0,bank.image(gid));rgb=np.asarray(img)[:,:,:3].astype(np.float32)
    if not rock(rgb).any():continue
    sig=raw.tobytes()
    if sig not in by_pixels:
        by_pixels[sig]=len(refs);candidates.append(rgb);refs.append((x,y,gid))
    by_coord[x,y]=by_pixels[sig]
C=np.stack(candidates);MASK=rock(C);TREE=cKDTree(feature(C));print('Canonical cliff vocabulary:',len(C),'distinct tiles')

records=[];MAPDATA=[]
for z in range(1,3):
    id=f'0{z}_'+('cirque' if z==1 else 'terrasses');out=O/id;out.mkdir(exist_ok=True)
    p=ROOT/f'source/zones_guidees/generateur_{z:02}.png';guide=Image.open(p).convert('RGB')
    # The guide can be resized for measuring forms. Canonical sprites are never resized.
    resized=np.asarray(guide.resize((W,H),Image.Resampling.NEAREST)).astype(np.float32)
    patches=resized.reshape(GH,8,GW,8,3).transpose(0,2,1,3,4).reshape(-1,8,8,3)
    fractions=rock(patches).mean(axis=(1,2));active=np.flatnonzero(fractions>=2/64)
    mask_for_tone=rock(patches)
    blue=(patches[:,:,:,2]*mask_for_tone).mean(axis=(1,2)).reshape(GH,GW)
    green=(patches[:,:,:,1]*mask_for_tone).mean(axis=(1,2)).reshape(GH,GW)
    tone=uniform_filter(blue,size=(5,3))/(uniform_filter(green,size=(5,3))+1e-6)
    _,nearest=TREE.query(feature(patches[active]),k=min(20,len(C)),workers=1)
    floor=[bank.get(BASE,x%16,80+y%16) for y in range(GH) for x in range(GW)]
    cliffs=[0]*(GW*GH);chosen=np.full(GW*GH,-1,dtype=np.int32)
    # Rerank nearest native tiles with boundary continuity; never rotate or recolor a tile.
    for at,i in enumerate(active):
        if fractions[i]>=.95:
            # A coherent 64x48 native rock pattern avoids a per-tile mosaic in full rock interiors.
            ratio=tone[i//GW,i%GW]
            sx=85 if ratio>.80 else 86 if ratio>.70 else 92 if ratio>.64 else 114+(i%GW)%8
            coord=(sx,59+(i//GW)%6)
            ci=by_coord[coord];chosen[i]=ci;cliffs[i]=refs[ci][2];continue
        options=list(nearest[at]);neighbors=[]
        for prev in ([i-1] if i%GW else [])+([i-GW] if i>=GW else []):
            ci=chosen[prev]
            if ci>=0:
                sx,sy,_=refs[ci];suggest=by_coord.get((sx+1,sy) if prev==i-1 else (sx,sy+1))
                if suggest is not None:options.append(suggest)
                neighbors.append((prev,ci))
        options=np.array(sorted(set(options)));a=C[options];target=patches[i]
        scores=((a-target)**2).mean(axis=(1,2,3))/(255**2)*.5
        scores+=((MASK[options]!=rock(target)).mean(axis=(1,2)))*1.4
        for prev,ci in neighbors:
            edge=(a[:,:,0,:]-C[ci][:,-1,:]) if prev==i-1 else (a[:,0,:,:]-C[ci][-1,:,:])
            scores+=(edge**2).mean(axis=(1,2))/(255**2)*.10
        ci=int(options[np.argmin(scores)]);chosen[i]=ci;cliffs[i]=refs[ci][2]
    grass=bank.render(floor);structure=bank.render(cliffs);dry=Image.alpha_composite(grass,structure)
    grass.save(out/'herbe.png');structure.save(out/'falaises.png');dry.save(out/'canonique_sec.png')
    # Choose a vertical river crossing from the guide's cliff bands, not by painting a new water texture.
    grid=fractions.reshape(GH,GW)
    def bands_for(cx):
        yes=grid[:,cx-4:cx+4].mean(axis=1)>.56
        for y in range(1,GH-2):
            if yes[y-1] and yes[y+1]:yes[y]=True
            if yes[y-1] and yes[y+2]:yes[y:y+2]=True
        edges=np.diff(np.r_[False,yes,False].astype(int));starts=np.where(edges==1)[0];ends=np.where(edges==-1)[0]
        return [(int(a),int(b)) for a,b in zip(starts,ends) if b-a>=10 and a>=8 and b<GH-3]
    choices=[]
    for cx in range(80,177,4):
        bands=bands_for(cx)
        if len(bands)<2:continue
        score=25*len(bands)+sum(min(b-a,28) for a,b in bands)-abs(cx-128)*.12
        # Prefer space for the native reservoir above the first fall.
        first=bands[0][0];score-=grid[max(0,first-40):first,max(0,cx-25):cx+16].mean()*40
        choices.append((score,cx,bands))
    assert choices,'No reliable two-cliff river crossing found in the generated guide'
    _,cx,bands=max(choices);banks=[0]*(GW*GH);water=[0]*(GW*GH);dx=cx-128
    def put(layer,x,y,gid):
        if gid and 0<=x<GW and 0<=y<GH:layer[y*GW+x]=gid
    def river_row(dy,sy,lake=False):
        lo,hi=(103,144) if lake else (123,133)
        for sx in range(lo,hi):
            # Include only actual water cells and their native shore neighbors, not the whole grass rectangle.
            nearby=any((sx+xx,sy+yy) in bank.sources[RIVERS[0]] for xx,yy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)])
            if nearby:put(banks,sx+dx,dy,bank.get(BASE,sx,sy))
            refs4=[(s,sx,sy) for s in RIVERS]
            ids=[bank.get(*r) for r in refs4]
            if any(ids):
                assert all(ids);put(water,sx+dx,dy,bank.animated(refs4))
    shift=bands[0][0]-57
    for y in range(max(0,shift)):river_row(y,0,True)
    for sy in range(57):river_row(sy+shift,sy,True)
    for j,(top,end) in enumerate(bands):
        stop=bands[j+1][0] if j+1<len(bands) else GH
        for y in range(end-1,stop):river_row(y,50+(y-end+1)%2)
        length=end-top
        for y in range(length):
            sy=y if y<6 else 13+y-(length-4) if y>=length-4 else 8+(y-6)%4
            for x in range(8):put(water,cx-4+x,top+y,bank.animated([(ANIM,1+9*f+x,62+sy) for f in range(4)]))
    bank_png=bank.render(banks);bank_png.save(out/'berges.png');wetbase=Image.alpha_composite(dry,bank_png);thumbs=[]
    for f in range(4):
        w=bank.render(water,f);w.save(out/f'eau_{f+1}.png');full=Image.alpha_composite(wetbase,w);full.save(out/f'canonique_eau_{f+1}.png')
        thumbs.append(full.convert('RGB').resize((512,384),Image.Resampling.NEAREST))
    thumbs[0].save(out/'apercu_eau.gif',save_all=True,append_images=thumbs[1:],duration=[170,160,170,170],loop=0)
    rec={'id':id,'name':'Le cirque des sources' if z==1 else 'Les trois gradins','guide':str(p.relative_to(ROOT)),'guide_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'guide_px':list(guide.size),'final_px':[W,H],'cellules':[GW,GH],'river_center_px':int(cx*8),'cliff_bands_px':[[a*8,b*8] for a,b in bands],'method':'Generator proposal -> coherent native interior pattern + nearest canonical boundary tiles with seam reranking. Only the guide is resampled; no guide pixels enter final assets.','active_cliff_cells':len(active)}
    (out/'zone.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2));records.append(rec);MAPDATA.append([floor,cliffs,banks,water]);print(id,'reconstructed;',len(active),'cliff cells; falls:',rec['cliff_bands_px'])

atlas=bank.save(O,NAME);cols=atlas['columns'];count=atlas['tilecount']
ts={'type':'tileset','version':'1.10','name':NAME,'tilewidth':8,'tileheight':8,**atlas,'margin':0,'spacing':0,'image':NAME+'.png','tiles':[{'id':g-1,'animation':[{'tileid':v-1,'duration':167} for v in seq]} for g,seq in bank.animations.items()]}
(O/(NAME+'.tsj')).write_text(json.dumps(ts,indent=2))
for rec,data in zip(records,MAPDATA):
    for wet in [False,True]:
        labels=['Herbe canonique','Falaises canoniques','Berges canoniques','Eau animée'][:4 if wet else 2]
        layers=[{'id':i+1,'name':name,'type':'tilelayer','x':0,'y':0,'width':GW,'height':GH,'opacity':1,'visible':True,'data':data[i]} for i,name in enumerate(labels)]
        tm={'type':'map','version':'1.10','orientation':'orthogonal','renderorder':'right-down','width':GW,'height':GH,'tilewidth':8,'tileheight':8,'infinite':False,'layers':layers,'nextlayerid':len(layers)+1,'nextobjectid':1,'tilesets':[{'firstgid':1,'source':'../'+NAME+'.tsj'}]}
        (O/rec['id']/('eau.tmj' if wet else 'sec.tmj')).write_text(json.dumps(tm,separators=(',',':')))
manifest={'reference':'Palikadude/Halcyon','commit':'da6c2130d641507447e6386a5e47a296e8cb4c71','sources':bank.source_info,'atlas':{'name':NAME,**atlas,'used':len(bank.images),'entries':bank.origins},'zones':records,'native_animations':[{'tileid':g-1,'Frames':[{'Sheet':NAME,'TexLoc':{'X':(v-1)%cols,'Y':(v-1)//cols}} for v in seq],'FrameLength':10} for g,seq in bank.animations.items()],'limits':['Generator internals are not altered; prompts and source references were adjusted','Pixel-perfect refers to copied native tiles, not a pixel-identical reproduction of the generated guide','Automated selection can produce imperfect joins; topology and runtime gameplay not certified','Waterfall row counts adapted to cliff height using unchanged source tile rows','The generator image is not itself a game-ready canonical tileset']}
(O/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Main before/after PNG comparison; imports use only the native files in each zone directory.
fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fp,26);small=ImageFont.truetype(fp,15)
board=Image.new('RGB',(1600,1480),'#1b2e27');d=ImageDraw.Draw(board)
d.text((26,22),'GÉNÉRATEUR → TUILES CANONIQUES DE MÉTANO',font=font,fill='#ecd99e')
d.text((26,66),'À gauche : proposition générée. À droite : reconstruction en vraies tuiles de 8 × 8 px.',font=small,fill='#b4c8b0')
for i,rec in enumerate(records):
    y=112+i*644
    for j,p in enumerate([ROOT/rec['guide'],O/rec['id']/'canonique_sec.png']):
        im=Image.open(p).convert('RGB').resize((768,576),Image.Resampling.NEAREST);board.paste(im,(24+j*792,y))
    d.text((26,y+588),rec['name']+' · prototype du générateur',font=small,fill='#ecd99e');d.text((816,y+588),'Version canonique · PNG natif 2048 × 1536 px',font=small,fill='#ecd99e')
d.text((26,1430),'Versions sèches et quatre phases d’eau fournies séparément. Aucun pixel du prototype n’est collé dans les textures finales.',font=small,fill='#b4c8b0')
board.save(O/'comparaison_generateur_canonique.png')
print('Finished: 2 guided zones, canonical atlas, dry/wet Tiled maps and native PNGs.')
