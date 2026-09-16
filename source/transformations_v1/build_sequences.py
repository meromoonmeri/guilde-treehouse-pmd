"""Reproducible Charizard transformation film pilots, not PMDO runtime integration.
Generated component art is combined with authored choreography and native actors.
240 frames at two engine ticks, plus independent 240-frame periodic hold loops.
"""
from pathlib import Path
import sys, json, math, hashlib, base64
import xml.etree.ElementTree as ET
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(Path(__file__).parent))
from assets import OUT, ROOT, load_assets, transparent, opacity, gif, atlas
from crown_attachment.attach import load_profiles, inspect_profile, place, DIRECTIONS

SIZE = (256, 288)
GROUND = (128, 250)
N, HOLD, SWAP = 240, 240, 132
LAYERS = ['ground', 'rear', 'actor', 'body_surface', 'front', 'accessory', 'veil']
COLORS = [(79,223,255), (156,131,255), (255,135,228), (255,236,142), (184,255,247)]
YY, XX = np.mgrid[:SIZE[1], :SIZE[0]]

def smooth(a,b,t):
    p=max(0,min(1,(t-a)/(b-a)))
    return p*p*(3-2*p)

def compose(layers):
    im=transparent(SIZE)
    for name in LAYERS: im.alpha_composite(layers[name])
    return im

def stamp(dest, im, center, size=None, alpha=1):
    if size: im=im.resize(tuple(max(1,round(v)) for v in size), Image.Resampling.NEAREST)
    if alpha != 1: im=opacity(im,alpha)
    dest.alpha_composite(im,(round(center[0]-im.width/2),round(center[1]-im.height/2)))

class Actor:
    def __init__(self, name):
        self.profile=load_profiles()[name]
        self.path=ROOT/self.profile['sprite_dir']
        self.records=[r for r in inspect_profile(name,self.profile)['records'] if r['action']=='Idle']
        self.sheet=Image.open(self.path/'Idle-Anim.png').convert('RGBA')
        self.count=max(r['frame'] for r in self.records)+1
        self.durations=[next(r['ticks'] for r in self.records if r['frame']==i) for i in range(self.count)]
    def render(self,d,t,scale=1):
        tick=(t*2)%sum(self.durations);f=0
        while tick>=self.durations[f]:tick-=self.durations[f];f+=1
        r=next(r for r in self.records if r['row']==d and r['frame']==f)
        w,h=r['frame_size'];im=self.sheet.crop((f*w,d*h,(f+1)*w,(d+1)*h))
        im=im.resize((round(w*scale),round(h*scale)),Image.Resampling.NEAREST)
        pos=(round(GROUND[0]-r['shadow'][0]*scale),round(GROUND[1]-r['shadow'][1]*scale))
        full=transparent(SIZE);full.alpha_composite(im,pos)
        head=[GROUND[i]+(r['head'][i]-r['shadow'][i])*scale for i in range(2)]
        return full,r,head

def background():
    im=Image.new('RGBA',SIZE,(14,21,35,255));d=ImageDraw.Draw(im)
    d.rectangle((0,244,255,287),fill=(26,34,46))
    d.ellipse((12,223,244,279), fill=(34,43,55),outline=(54,64,73),width=2)
    for j in range(11):
        x=(j*67+19)%248;y=246+(j*13)%34
        d.line((x,y,x+11,y),fill=(43,54,65),width=1)
    return im

BG=background()

def preview(im,kind=None):
    bg=BG.copy();bg.alpha_composite(im)
    if kind=='tera_fire':bg=bg.crop((64,136,192,280)).resize(SIZE,Image.Resampling.NEAREST)
    return bg.convert('RGB')

def envelope(actor,target,d):
    mask=np.zeros(SIZE[::-1],np.uint8)
    for t in range(16):
        for obj,sc in [(actor,1),target]:
            a=np.array(obj.render(d,t,sc)[0])[:,:,3]
            mask=np.maximum(mask,a)
    mask=cv2.dilate(mask,np.ones((13,13),np.uint8))
    points=cv2.findNonZero(mask)
    hull=cv2.convexHull(points)
    out=np.zeros_like(mask);cv2.fillConvexPoly(out,hull,255)
    return out,Image.fromarray(out).getbbox()

def ground_fx(im,t,intensity,radius,tera=False):
    if intensity<=0:return
    d=ImageDraw.Draw(im);color=(110,213,255) if tera else (251,64,132)
    for j in range(3):
        phase=(t/48+j/3)%1;r=radius*(.65+.45*phase)
        a=round(160*intensity*(1-phase))
        d.ellipse((128-r,250-r*.24,128+r,250+r*.24),outline=(*color,a),width=1+j%2)
    for j in range(24 if tera else 38):
        p=(t/48+j*.618)%1;theta=j*2.399
        x=128+math.cos(theta)*radius*(1-.58*p)
        y=250+math.sin(theta)*radius*.22-p*(40 if tera else 90)
        a=round(225*intensity*math.sin(math.pi*p));s=1+(j%5==0)
        d.rectangle((round(x),round(y),round(x+s),round(y+s)),fill=(*(COLORS[j%5] if tera else color),a))

def cloud_orbit(rear,front,assets,head,bbox,t,amount,giga=False):
    if amount<=0:return
    # Three depth-separated rings; integral revolutions and asset cycles close at 240.
    width=bbox[2]-bbox[0];cy=max(22,min(head[1]-21,bbox[1]+5))
    for ring in range(3):
        for j in range(3):
            theta=2*math.pi*(t/HOLD*(ring+1)+j/3+ring*.13)
            depth=round(math.sin(theta),10);rx=min(79,width*.36+ring*5)
            x=head[0]+math.cos(theta)*rx;y=cy+depth*(7+ring*2)-ring*9
            size=(round((29+ring*5+(8 if giga else 0))*(.9+.12*depth)),13+ring*2)
            img=assets['cloud'][(t*(ring+1)+j*16)%48]
            stamp(front if depth>=0 else rear,img,(x,y),size,amount*(.8+.2*(depth+1)/2))

def bolts(im,t,bbox,amount,giga=False):
    if amount<=0:return
    d=ImageDraw.Draw(im);left,top,right,bottom=bbox
    count=12 if giga else 7
    for j in range(count):
        age=(t+j*7)%19
        if age>13:continue
        seed=j*111+t//3*97;rng=np.random.default_rng(seed)
        x=128+(j/(count-1)-.5)*(right-left+22)
        tip=min(250,top-35+age*28)
        points=[(round(x),max(0,top-70))]
        for y in range(max(4,top-58),max(5,round(tip)),11):
            points.append((round(x+rng.integers(-14,15)+math.sin(y*.09+t*.25+j)*9),y))
        if len(points)<2:continue
        brightness=math.sin(math.pi*age/14)**2;a=round(amount*255)
        d.line(points,fill=(87,8,35,a),width=5 if giga else 3)
        d.line(points,fill=(round(139+116*brightness),round(12+110*brightness),round(48+112*brightness),a),width=2)
        if brightness>.65:d.line(points,fill=(255,219,226,a),width=1)
        for k in range(2,len(points),4):
            x,y=points[k];sgn=1 if j%2 else -1
            d.line([(x,y),(x+sgn*9,y-8),(x+sgn*19,y-11)],fill=(250,62,115,a),width=1)

def shell_facets(mask,t):
    a=np.zeros((*mask.shape,4),np.uint8)
    # Opaque interlocking faceted enclosure; alpha is explicitly tested at the swap.
    sector=((XX//12)+(YY//17)+(XX+YY)//23)%len(COLORS)
    for i,c in enumerate(COLORS):
        m=(sector==i)&(mask>0);a[m,:3]=c;a[m,3]=255
    edges=((XX+2*YY)%37<2)|((2*XX-YY)%43<2)
    a[edges&(mask>0),:3]=(224,252,255)
    band=((XX+YY-t*3)%63<5)&(mask>0);a[band,:3]=(255,255,250)
    return Image.fromarray(a)

def body_crystal(actor,t,amount):
    a=np.array(actor);m=a[:,:,3]>0
    out=np.zeros_like(a);ids=((XX+YY)//8+(t%HOLD)*5//HOLD)%5
    for i,c in enumerate(COLORS):out[ids==i,:3]=c
    streak=((XX*2+YY-t*2)%48<4);facet=((XX+YY*2)%19==0)
    out[:,:,3]=np.where(m,np.where(streak,225,np.where(facet,170,42))*amount,0).astype(np.uint8)
    return Image.fromarray(out)

def shards(im,t,bbox,amount,opening=False):
    if amount<=0:return
    d=ImageDraw.Draw(im);l,top,r,b=bbox;cx=(l+r)/2;cy=(top+b)/2
    for j in range(24):
        theta=j*2.399;tau=t/34 if opening else (t/56+j*.13)%1
        radius=(r-l)*(.35+tau*.8) if opening else (r-l)*(.8-.42*tau)
        x=cx+math.cos(theta)*radius;y=cy+math.sin(theta)*radius*.8-(0 if opening else tau*20)
        s=2+j%4;col=COLORS[(j+t//9)%5];a=round(255*amount)
        d.polygon([(x,y-s*2),(x+s,y),(x,y+s*2),(x-s,y)],fill=(*col,a))
        d.line((x,y-s*2,x,y+s),fill=(255,255,255,a),width=1)

def render(kind,d,t,assets,normal,gmax,hold=False):
    layers={name:transparent(SIZE) for name in LAYERS}
    after=hold or t>=SWAP
    target=gmax if kind=='gigantamax' else normal
    scale=3 if kind=='dynamax' and after else 1
    actor,r,head=(target if after else normal).render(d,t,scale)
    layers['actor']=actor
    mask,bbox=ENVELOPES[kind,d];l,top,right,bottom=bbox;w=right-l;h=bottom-top
    if kind!='tera_fire':
        charge=0 if hold else smooth(0,35,t)*(1-smooth(158,208,t))
        ground_fx(layers['ground'],t,.4 if hold else max(charge,.15 if after else 0),w*.57)
        if not hold:
            # Moving leading edge descends from the sky, reaches the anchored ground.
            descent=smooth(22,86,t);tip=round(250*descent)
            fade=1-smooth(148,199,t)
            if tip>0 and fade>0:
                component=assets['giga' if kind=='gigantamax' else 'column'][t%48]
                beam=transparent(SIZE)
                width=w*(.55+.45*smooth(64,115,t))*1.4
                stamp(beam,component,(128,125),(width,250),fade*.85)
                arr=np.array(beam);arr[tip:]=0;layers['rear'].alpha_composite(Image.fromarray(arr))
                # Distinct, independently cycling inner column.
                inner=transparent(SIZE);stamp(inner,assets['column'][(t*2+13)%48],(128,125),(width*.63,250),fade*.65)
                a=np.array(inner);a[tip:]=0;layers['front'].alpha_composite(Image.fromarray(a))
                ImageDraw.Draw(layers['front']).ellipse((128-width*.23,max(0,tip-3),128+width*.23,tip+2),fill=(255,151,192,round(220*fade)))
            bolts(layers['front'],t,bbox,smooth(44,83,t)*fade,kind=='gigantamax')
            # Generated branch layer supplements the independently drawn forks.
            stamp(layers['rear'],assets['lightning'][(t*3)%48],(128,142),(w+15,215),charge*.6)
            seal=smooth(105,124,t)*(1-smooth(143,164,t))
            if seal:
                veil=np.zeros((*mask.shape,4),np.uint8)
                veil[:,:,:3]=(255,222,240)
                veil[:,:,3]=np.uint8(mask*seal)
                stripes=((XX+5*np.sin(YY*.08+t*.18)+t*2)%19<3)&(mask>0);veil[stripes,:3]=(255,130,181)
                layers['veil']=Image.fromarray(veil)
                # Pixel-stepped pulse skirt and outward rings give the opaque core volume.
                glow=transparent(SIZE)
                pulse=smooth(116,130,t)*(1-smooth(137,156,t))
                gd=ImageDraw.Draw(glow)
                cx=(l+right)/2;cy=(top+bottom)/2
                for j in range(4,0,-1):
                    gd.ellipse((l-j*3,top-j*3,right+j*3,bottom+j*3),fill=(255,111+20*j,176+13*j,round(pulse*(90-j*14))))
                for j in range(3):
                    radius=max(0,(t-119+j*4)*3)
                    if 0<radius<110:
                        gd.ellipse((cx-radius,cy-radius*.6,cx+radius,cy+radius*.6),outline=(255,197,221,round(pulse*190)),width=2)
                glow.alpha_composite(layers['veil']);layers['veil']=glow
        final_actor=target.render(d,t,3 if kind=='dynamax' else 1)[0]
        final_bbox=final_actor.getbbox()
        final_head=target.render(d,t,3 if kind=='dynamax' else 1)[2]
        cloud_orbit(layers['rear'],layers['front'],assets,final_head,final_bbox,t,1 if hold else smooth(100,187,t),kind=='gigantamax')
    else:
        strength=1 if hold else smooth(12,90,t)
        ground_fx(layers['ground'],t,.3 if hold else .85*(1-smooth(177,235,t)),max(28,w*.65),True)
        layers['body_surface']=body_crystal(actor,t,.8 if hold else strength*(.35+.65*smooth(140,190,t)))
        if not hold:
            grow=smooth(30,103,t);fade=1-smooth(145,183,t)
            if grow>0 and fade>0:
                crystal=assets['growth'][min(42,round(grow*42))]
                rising=transparent(SIZE);stamp(rising,crystal,((l+right)/2,(top+bottom)/2),(w+16,h+18),fade)
                ar=np.array(rising);ar[:round(bottom-(h+22)*grow)]=0
                layers['front'].alpha_composite(Image.fromarray(ar))
                # Refraction moves within the forming enclosure, not a single colored aura.
                pr=transparent(SIZE);stamp(pr,assets['prism'][t%48],((l+right)/2,(top+bottom)/2),(w+12,h+10),.55*grow*fade)
                layers['rear'].alpha_composite(pr)
            seal=smooth(87,119,t)*(1-smooth(145,163,t))
            if seal>0:
                layers['veil']=opacity(shell_facets(mask,t),seal)
                if t>=143:
                    dr=ImageDraw.Draw(layers['veil']);cx=(l+right)//2;cy=(top+bottom)//2
                    for j in range(7):
                        theta=j*2*math.pi/7
                        dr.line([(cx,cy),(cx+math.cos(theta)*w*.25,cy+math.sin(theta)*h*.24),(cx+math.cos(theta+.2)*w,cy+math.sin(theta+.2)*h)],fill=(20,32,76,255),width=1)
            if 148<=t<190:shards(layers['front'],t-148,bbox,1-smooth(163,190,t),True)
            if t<112:shards(layers['rear'],t,bbox,smooth(0,30,t)*(1-smooth(86,112,t)))
        material=1 if hold else smooth(166,212,t)
        if material>0:
            crown,pos,detail=place(assets['crowns']['fire'][d],'fire',r,GROUND)
            c=np.array(crown);height=crown.height
            # Ordered crystal facets assemble from bottom to top; no head is in the accessory.
            yy,xx=np.mgrid[:height,:crown.width]
            reveal=((height-yy)/height*.8+((xx//3)%3)*.07)<=material
            c[~reveal]=0
            facets=(xx+yy-t)%24<2
            c[facets&(c[:,:,3]>0),:3]=(255,245,209)
            layers['accessory'].alpha_composite(Image.fromarray(c),pos)
            draw=ImageDraw.Draw(layers['accessory'])
            # Sparse periodic sparkle points around the crown and along body facets.
            for j in range(5):
                p=(t+j*17)%48
                if p>8:continue
                x=pos[0]+3+(j*7)%(max(1,crown.width-6));y=pos[1]+3+(j*11)%(max(1,crown.height-5))
                draw.line((x-2,y,x+2,y),fill=(255,248,217,255));draw.line((x,y-2,x,y+2),fill=(255,248,217,255))
            if material<1:shards(layers['rear'],t,(pos[0],pos[1],pos[0]+crown.width,pos[1]+crown.height),1-material)
    return layers

ENVELOPES={}

def export_pages(frames,folder,stem):
    folder.mkdir(parents=True,exist_ok=True);pages=[]
    for start in range(0,len(frames),40):
        page=frames[start:start+40]
        if not any(f.getbbox() for f in page):continue
        rows=math.ceil(len(page)/8)
        path=folder/f'{stem}_{start:03d}.8x{rows}.png'
        desc=atlas(page,path);desc['start_frame']=start;pages.append(desc)
    return pages

def main():
    assets=load_assets();normal=Actor('charizard');gmax=Actor('gigantamax_charizard')
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for actor in [normal,gmax] for p in actor.path.glob('*') if p.is_file()}
    for kind in ['dynamax','gigantamax','tera_fire']:
        for d in range(8):
            ENVELOPES[kind,d]=envelope(normal,(gmax,1) if kind=='gigantamax' else (normal,3 if kind=='dynamax' else 1),d)
    manifest={'canvas':SIZE,'ground_anchor':GROUND,'frame_ticks':2,'tick_rate':60,'sequence_frames':N,'sequence_ms':8000,'hold_frames':HOLD,'hold_ms':8000,'swap_frame':SWAP,'layer_order':LAYERS,'source_hashes':sources,'directions':DIRECTIONS,'sequences':{},'runtime_PMDO':'NOT TESTED','review_camera':{'tera_fire':'2x nearest-neighbor crop (64,136,192,280), preview only; transparent layers retain original canvas'},'layer_export_scope':'All seven layers for direction D; other seven views reproducible from script and existing native direction rows. Page PNGs are import sources, not compiled runtime assets.'}
    verification={'opaque_swap_checks':[],'body_surface_checks':[],'hold_seams':[],'source_hashes_preserved':False,'runtime_PMDO':'NOT TESTED'}
    for kind in ['dynamax','gigantamax','tera_fire']:
        print('Building',kind,flush=True);views=[];layer_manifest={}
        for d in range(8):
            films=[];layers_all={name:[] for name in LAYERS} if d==0 else None
            for t in range(N):
                layers=render(kind,d,t,assets,normal,gmax)
                films.append(preview(compose(layers),kind))
                if d==0:
                    for name in LAYERS:layers_all[name].append(layers[name])
                if SWAP-3<=t<=SWAP+3:
                    # Both source and target are completely hidden by an independently opaque layer.
                    m=ENVELOPES[kind,d][0]>0;alpha=np.array(layers['veil'])[:,:,3]
                    assert np.all(alpha[m]==255),(kind,d,t,int(alpha[m].min()))
                    verification['opaque_swap_checks'].append({'kind':kind,'direction':d,'frame':t,'coverage':1.0})
                if kind=='tera_fire':
                    a=np.array(layers['actor'])[:,:,3];surface=np.array(layers['body_surface'])[:,:,3]
                    assert not np.any(surface[a==0]),(d,t,'surface outside actor')
            path=OUT/'gifs'/f'{kind}_{DIRECTIONS[d]}.gif';gif(films,path)
            views.append(str(path.relative_to(OUT)))
            if d==0:
                for name,fs in layers_all.items():layer_manifest[name]=export_pages(fs,OUT/'layers'/kind,f'TR_{kind}_{name}_D')
                board=Image.new('RGB',(SIZE[0]*4,SIZE[1]*2),(14,21,35))
                for i,t in enumerate([0,42,84,120,132,158,194,239]):
                    board.paste(films[t],((i%4)*SIZE[0],(i//4)*SIZE[1]))
                    ImageDraw.Draw(board).text(((i%4)*SIZE[0]+8,(i//4)*SIZE[1]+8),f'{t*2/60:.2f}s',fill='white')
                board.save(OUT/'review'/f'{kind}_storyboard.png')
            del films,layers_all
            if kind=='tera_fire':verification['body_surface_checks'].append({'direction':d,'frames':N,'outside_actor_pixels':0})
        loops=[]
        for d in range(8):
            hold_frames=[preview(compose(render(kind,d,t,assets,normal,gmax,True)),kind) for t in range(HOLD)]
            # Complete periodic closure, not a frozen duplicate endpoint.
            first=np.array(hold_frames[0]);endpoint=np.array(preview(compose(render(kind,d,HOLD,assets,normal,gmax,True)),kind))
            assert np.array_equal(first,endpoint),(kind,d,'loop does not close')
            seam=float(np.abs(np.array(hold_frames[-1]).astype(float)-first).mean())
            verification['hold_seams'].append({'kind':kind,'direction':d,'frame0_equals_frame240':True,'last_to_first_mean_rgb_delta':seam})
            path=OUT/'gifs'/f'{kind}_hold_{DIRECTIONS[d]}.gif';gif(hold_frames,path);loops.append(str(path.relative_to(OUT)))
        manifest['sequences'][kind]={'gifs':views,'hold_gifs':loops,'direction_D_layers':layer_manifest}
    for p,sha in sources.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha
    verification['source_hashes_preserved']=True
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    make_gallery(manifest)
    print('Built 24 films + 24 hold loops; all swap, clipping and periodicity assertions passed.',flush=True)

def make_gallery(manifest):
    # Lightweight portable gallery; media stay in exports instead of duplicating 80 MB in HTML.
    data={}
    for kind,v in manifest['sequences'].items():
        data[kind]={}
        for key in ['gifs','hold_gifs']:
            data[kind][key]=['exports/transformations_v1/'+p for p in v[key]]
    html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Transformations • Dracaufeu</title><style>
    *{box-sizing:border-box}body{margin:0;background:#0e1523;color:#edf4ff;font:16px system-ui}main{max-width:1250px;margin:auto;padding:36px 24px}small,.eyebrow{color:#97b8c9}h1{font-size:clamp(28px,4vw,48px);margin:12px 0}p{line-height:1.6;color:#b7c8d9}.tag{display:inline-block;padding:6px 12px;border:1px solid #384757;border-radius:20px;font-size:12px;color:#a7e3dc}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}button{border:1px solid #44536b;background:#182438;color:#dceeff;border-radius:8px;padding:10px 14px;cursor:pointer}button.active{background:#a7e3dc;color:#122135}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}article{border:1px solid #344156;border-radius:14px;overflow:hidden;background:#141f31}article img{width:100%;image-rendering:pixelated;display:block}article h2,article p{margin:16px}article h2{font-size:20px}article p{font-size:14px}.note{margin-top:24px;padding:20px;border-left:3px solid #ecbe79;background:#1b2432}a{color:#a7e3dc}footer{margin-top:30px;color:#97b8c9;font-size:13px}@media(max-width:800px){.grid{grid-template-columns:1fr}article img{max-height:600px;object-fit:contain}}</style><main><div class="eyebrow">ATELIER VFX / LIVRABLE PILOTE 01</div><h1>Trois transformations.<br>Huit directions.</h1><span class="tag">Dracaufeu · 240 phases / 8 secondes</span> <span class="tag">Boucles d’état · 240 phases / 8 secondes</span><p>Colonne descendante, éclairs ramifiés et nuages en orbite. Révélation de la véritable forme Gigamax. Enveloppe cristalline, fracture puis matérialisation d’une couronne Feu indépendante et sans visage.</p><nav id="directions"></nav><nav><button id="film" class="active" onclick="setMode('gifs')">Transformation complète</button><button id="hold" onclick="setMode('hold_gifs')">État persistant · boucle</button><button onclick="update()">Rejouer ensemble</button></nav><div class="grid"><article><img id="dynamax" alt="Transformation Dynamax"><h2>01 / Dynamax</h2><p>Dracaufeu agrandi ×3. Descente énergétique, particules aspirées, occultation opaque et trois orbites de nuages.</p></article><article><img id="gigantamax" alt="Transformation Gigamax"><h2>02 / Gigamax</h2><p>Véritable sprite Gigamax de SpriteCollab. Enveloppe plus large, davantage d’éclairs et de nuages. Le corps natif final comporte une pose par direction.</p></article><article><img id="tera_fire" alt="Téracristallisation Feu"><h2>03 / Téracristal · Feu · vue ×2</h2><p>Cristaux croissants, coque facettée opaque, fissures et fragments. Reflets limités à la silhouette et assemblage progressif du candélabre.</p></article></div><div class="note"><strong>Livrable visuel, pas certification en jeu.</strong><p>Ces trois films concernent Dracaufeu, pas toutes les espèces. Couronne Feu : angles et occultations anatomiques encore à valider ; variante volontairement sans visage. Les 18 autres types ne sont pas animés dans cette galerie. Les huit vues sont produites ; les sept calques séparés sont exportés pour la vue D, les autres sont reproductibles par le script. Aucun import ni rendu Ground/Dungeon PMDO n’a été testé.</p><p>Les composants utilisent des images générées, interpolées par flux optique, complétées par une chorégraphie calculée : il ne s’agit pas de 240 dessins manuels distincts. Le redémarrage du film revient à l’état initial ; seules les boucles d’état sont périodiques.</p></div><footer>Sources des personnages : SpriteCollab, crédits conservés dans les dossiers de références. Vérifications : masque opaque au changement, reflets sans débordement, boucle périodique et intégrité des originaux. Consulter le <a href="exports/transformations_v1/README.md">guide du livrable</a> et le <a href="exports/transformations_v1/verification.json">rapport de vérification</a>.</footer></main><script>'''
    html+='const DATA='+json.dumps(data)+';const DIRS='+json.dumps(DIRECTIONS)+';'
    html+='''let direction=0,mode='gifs';function update(){for(const kind of Object.keys(DATA)){const img=document.getElementById(kind);img.removeAttribute('src');img.src=DATA[kind][mode][direction]}document.querySelectorAll('#directions button').forEach((b,i)=>b.classList.toggle('active',i===direction));document.getElementById('film').classList.toggle('active',mode==='gifs');document.getElementById('hold').classList.toggle('active',mode==='hold_gifs')}function setMode(m){mode=m;update()}DIRS.forEach((name,i)=>{let b=document.createElement('button');b.textContent=name;b.onclick=()=>{direction=i;update()};document.getElementById('directions').appendChild(b)});update();</script></html>'''
    (ROOT/'apercu_transformations_v1.html').write_text(html)

if __name__=='__main__':main()
