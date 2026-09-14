"""Steady finite-volume sink flow around solid rocks; newly generated water material."""
from pathlib import Path
import io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];OLD=R/'renders/eau_siphons_rapides_v2/eau_siphons_rapides';O=R/'renders/siphons_ecoulement_v3';P=O/'siphons_ecoulement';P.mkdir(parents=True,exist_ok=True)
W,H=456,384;C=2;NX,NY=W//C,H//C;N=128;DT=50;PERIOD=N*DT/1000;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im)
 return c
def rgba(rgb,alpha):
 a=np.zeros((H,W,4),dtype='uint8');a[:,:,:3]=rgb;a[:,:,3]=alpha;a[a[:,:,3]==0]=0;return Image.fromarray(a)
# Retain the dry causeway and rock placement. Only wet outer edges receive a darker blue-gray contact tone.
static=[];rocknames=['04_rochers_arriere','05_rochers_avant','06_galet_decale','07_chaussee_surface','08_chaussee_rebords']
original=[(n,load(OLD/f'siphons_v2_{n}.png')) for n in rocknames];solid=np.maximum.reduce([np.array(im)[:,:,3] for _,im in original])>0
inside=nd.distance_transform_edt(solid);edge=solid&(inside<=2)
for name,im in original:
 a=np.array(im);m=edge&(a[:,:,3]>0);a[m,:3]=np.rint(a[m,:3]*.65+np.array([36,73,93])*.35).astype('uint8');a[a[:,:,3]==0]=0;static.append((name,Image.fromarray(a)));static[-1][1].save(P/f'siphons_v3_{name}.png')
# A conservative 2px grid: any solid pixel makes the corresponding fluid cell impermeable.
wet=~solid.reshape(NY,C,NX,C).any(axis=(1,3))
# Tiny enclosed alpha holes in the source sprites are quiescent pockets, not open circulation domains.
components,_=nd.label(wet);open_components=set(components[0])|set(components[-1])|set(components[:,0])|set(components[:,-1]);open_components.discard(0);wet&=np.isin(components,list(open_components))
ids=np.full((NY,NX),-1,int);ids[wet]=np.arange(wet.sum());ys,xs=np.where(wet);row=[];col=[];data=[];diag=np.zeros(wet.sum())
for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
 ny=ys+dy;nx=xs+dx;valid=(ny>=0)&(ny<NY)&(nx>=0)&(nx<NX);boundary=~valid;diag[boundary]+=2
 a=np.flatnonzero(valid);b=wet[ny[a],nx[a]];a=a[b];diag[a]+=1;row.extend(ids[ys[a],xs[a]]);col.extend(ids[ny[a],nx[a]]);data.extend([-1.]*len(a))
row.extend(np.arange(len(diag)));col.extend(np.arange(len(diag)));data.extend(diag);A=coo_matrix((data,(row,col)),shape=(len(diag),len(diag))).tocsr()
centers=[(272,20,46),(128,68,46),(231,144,77),(292,177,19),(332,163,19),(80,197,46),(400,197,30),(156,184,11),(292,224,11)]
Y,X=np.mgrid[:NY,:NX]+.5;Yu,Xu=np.mgrid[:NY,:NX+1].astype(float);Yu+=.5;Yv,Xv=np.mgrid[:NY+1,:NX].astype(float);Xv+=.5
u=np.zeros((NY,NX+1));v=np.zeros((NY+1,NX));sink=np.zeros((NY,NX))
for cx,cy,r in centers:
 cx/=C;cy/=C;r/=C;strength=(r/10)**1.5
 blob=np.exp(-((X-cx)**2+(Y-cy)**2)/(2*1.7**2))*wet;assert blob.sum()>0;sink+=blob/blob.sum()*strength
 gamma=strength/(2*np.pi)*2.0
 for field,fx,fy,is_u in [(u,Xu,Yu,True),(v,Xv,Yv,False)]:
  dx=fx-cx;dy=fy-cy;rr=dx*dx+dy*dy;field+=gamma*(-dy if is_u else dx)/(rr+2.5**2)*np.exp(-rr/(2*r*r))
uf=np.zeros_like(u,dtype=bool);vf=np.zeros_like(v,dtype=bool);uf[:,1:-1]=wet[:,:-1]&wet[:,1:];uf[:,0]=wet[:,0];uf[:,-1]=wet[:,-1];vf[1:-1]=wet[:-1]&wet[1:];vf[0]=wet[0];vf[-1]=wet[-1]
u[~uf]=0;v[~vf]=0
# Pressure projection: divergence equals removal at sinks, zero elsewhere, with no flow through solid faces.
div=u[:,1:]-u[:,:-1]+v[1:]-v[:-1];phi=np.zeros((NY,NX));phi[wet]=spsolve(A,(div+sink)[wet])
u[:,1:-1]+=(phi[:,1:]-phi[:,:-1])*uf[:,1:-1];u[:,0]+=2*phi[:,0];u[:,-1]-=2*phi[:,-1]
v[1:-1]+=(phi[1:]-phi[:-1])*vf[1:-1];v[0]+=2*phi[0];v[-1]-=2*phi[-1]
speed=np.hypot((u[:,:-1]+u[:,1:])*.5,(v[:-1]+v[1:])*.5)*C;scale=140/np.percentile(speed[wet],95);u*=scale;v*=scale;sink*=scale
residual=(u[:,1:]-u[:,:-1]+v[1:]-v[:-1]+sink)[wet];relative=float(np.max(np.abs(residual))/np.max(sink));assert relative<1e-8
boundary_inflow=float(u[:,0].sum()-u[:,-1].sum()+v[0].sum()-v[-1].sum());assert np.isclose(boundary_inflow,sink.sum(),rtol=1e-8)
np.savez_compressed(O/'CHAMP_ECOULEMENT.npz',u=u,v=v,wet=wet,sink=sink,solid=solid,cell_size=C)
_,nearest=nd.distance_transform_edt(~wet,return_indices=True)
def velocity(x,y):
 return nd.map_coordinates(u,[y-.5,x],order=1,mode='nearest'),nd.map_coordinates(v,[y,x-.5],order=1,mode='nearest')
def valid(x,y):return wet[np.clip(y.astype(int),0,NY-1),np.clip(x.astype(int),0,NX-1)]
def safe_step(x,y,dt):
 ux,vy=velocity(x,y);mx=x+ux*dt*.5;my=y+vy*dt*.5;ux,vy=velocity(mx,my);a=np.clip(x+ux*dt,.01,NX-.01);b=np.clip(y+vy*dt,.01,NY-.01)
 good=valid(a,b)&valid((x+a)/2,(y+b)/2)
 return np.where(good,a,x),np.where(good,b,y)
# Flow-map texture animation: two staggered backward traces crossfade only when each warp resets.
# The velocity field remains steady. This visual looping method is not a free-surface fluid simulation.
bx=X[wet].copy();by=Y[wet].copy();uv=[]
for k in range(32):
 uv.append((bx.copy(),by.copy()))
 for _ in range(5):bx,by=safe_step(bx,by,-.005)
raw=load(O/'bruts/eau_matiere.png').resize((W,H),NN);ra=np.array(raw);lum=ra[:,:,:3]@np.array([.2126,.7152,.0722]);lo,hi=np.percentile(lum,[2,98]);material=np.clip((lum-lo)/max(hi-lo,1),0,1)
textures=[]
for bx,by in uv:
 val=nd.map_coordinates(material,[by*C,bx*C],order=1,mode='wrap');small=np.zeros((NY,NX));small[wet]=val
 # Values beneath the solid cells never render; nearest fluid completion avoids a dark interpolation seam.
 small[~wet]=small[nearest[0,~wet],nearest[1,~wet]];textures.append(np.array(Image.fromarray(small.astype('float32')).resize((W,H),Image.Resampling.BILINEAR)))
# New funnel depth shading uses the old destination coordinates, not the six adapted sand animation poses.
depth=np.zeros((H,W))
for cx,cy,r in centers:depth=np.maximum(depth,np.exp(-.5*(((xx-cx)/(r*.53))**2+((yy-cy)/(r*.40))**2)))
palette=np.array([[7,30,47],[8,39,58],[10,48,69],[12,58,81],[15,69,94],[18,80,106],[21,92,118],[25,103,128],[30,114,139],[38,126,149],[49,139,160],[63,152,171],[81,166,182],[105,183,196],[134,203,209],[169,221,223]],dtype='uint8')
# Tracers obey the projected field with small swept steps and disappear at sinks; no path is drawn through rock.
rng=np.random.default_rng(173);choices=rng.choice(len(xs),size=900,replace=False);tx=xs[choices].astype(float)+.5;ty=ys[choices].astype(float)+.5;times=np.zeros(len(tx));active=np.ones(len(tx),bool);records=[[[0.,x,y]] for x,y in zip(tx,ty)];absorbed=np.zeros(len(tx),bool)
for iteration in range(2400):
 ux,vy=velocity(tx,ty);dt=np.minimum(.025,.35/np.maximum(np.hypot(ux,vy),.01));dt[~active]=0;nx,ny=safe_step(tx,ty,dt);times+=dt
 for k in np.flatnonzero(active):records[k].append([float(times[k]),float(nx[k]),float(ny[k])])
 tx,ty=nx,ny;near=np.zeros(len(tx),bool)
 for cx,cy,r in centers:near|=(tx-cx/C)**2+(ty-cy/C)**2<3.5**2
 absorbed|=active&near;active&=~near&(times<PERIOD-.2)
 if not active.any():break
tracks=[np.array(rec) for rec,ok in zip(records,absorbed) if ok and rec[-1][0]>.25];assert len(tracks)>=80,len(tracks);offsets=rng.uniform(0,PERIOD,len(tracks))
heads=np.zeros((N,len(tracks),2),dtype='float32');tails=heads.copy();visibility=np.zeros((N,len(tracks)),dtype='uint8')
shore=nd.distance_transform_edt(~solid);shade=rgba([8,39,56],np.rint((~solid)*np.clip((5-shore)/5,0,1)*48).astype('uint8'));static=[('03_ombres_contact',shade)]+static;shade.save(P/'siphons_v3_03_ombres_contact.png')
# Shore glints travel according to local tangential velocity and remain restrained, not an opaque white halo.
cy,cx=np.mgrid[:NY,:NX]+.5;uc,vc=velocity(cx,cy);fullu=np.array(Image.fromarray(uc.astype('float32')).resize((W,H),Image.Resampling.BILINEAR))*C;fullv=np.array(Image.fromarray(vc.astype('float32')).resize((W,H),Image.Resampling.BILINEAR))*C
phase_field=xx*.27+yy*.31;rate=np.clip((fullu*.27+fullv*.31)/(2*np.pi),-3,3);# integer cycles guarantee an exact loop
rate=np.rint(rate*PERIOD)/PERIOD
names=['01_eau_advectee','02_filets_courant','09_reflets_rives'];groups={n:[] for n in names};frames=[]
for i in range(N):
 t=i*DT/1000;a=(i*2)%32;b=(a+16)%32;weight=1-abs(a-16)/16;tex=textures[a]*weight+textures[b]*(1-weight)
 idx=np.clip(np.rint(7+tex*2.8-depth*4.5),0,15).astype('uint8');water=Image.fromarray(palette[idx]).convert('RGBA')
 streaks=Image.new('RGBA',(W,H));d=ImageDraw.Draw(streaks)
 for k,track in enumerate(tracks):
  age=(t+offsets[k])%PERIOD;end=track[-1,0]
  if age<.05 or age>end-.03:continue
  x=np.interp(age,track[:,0],track[:,1])*C;y=np.interp(age,track[:,0],track[:,2])*C;old=max(0,age-.16);px=np.interp(old,track[:,0],track[:,1])*C;py=np.interp(old,track[:,0],track[:,2])*C
  strength=max(0,min(1,(age-.05)/.12,(end-age-.03)/.12));alpha=round(175*strength);ages=np.linspace(old,age,6);points=list(zip(np.rint(np.interp(ages,track[:,0],track[:,1])*C).astype(int),np.rint(np.interp(ages,track[:,0],track[:,2])*C).astype(int)));d.line(points,fill=(112,193,207,alpha),width=1);heads[i,k]=[x,y];tails[i,k]=[px,py];visibility[i,k]=alpha
 ar=np.array(streaks);ar[solid]=0;streaks=Image.fromarray(ar)
 pulse=(np.sin(phase_field-2*np.pi*rate*t)+1)/2;outside=(~solid)&(shore<=2);inneredge=solid&(inside<=2)
 alpha=np.rint((outside*28+inneredge*18)*np.clip((pulse-.55)/.45,0,1)).astype('uint8');rim=rgba([114,182,198],alpha)
 ims=[water,streaks,rim]
 for n,im in zip(names,ims):groups[n].append(im);im.save(P/f'siphons_v3_{n}_{i:03}.png')
 ls=list(zip(names[:2],ims[:2]))+static+[(names[2],rim)];c=compose(ls);assert np.all(np.array(c)[:,:,3]==255);frames.append(c);c.save(P/f'siphons_v3_scene_{i:03}.png')
 if i==0:first=ls;c.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True)
np.savez_compressed(O/'TRACEURS_CONTROLE.npz',heads=heads,tails=tails,alpha=visibility)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'siphons_ecoulement.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(n,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'siphons_ecoulement.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');re=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(re),np.array(frames[0]))
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'static_layers':[n for n,_ in static],'animation_groups':names,'render_order':names[:2]+[n for n,_ in static]+names[2:],'sink_centers':centers,'flow':{'model':'steady 2D finite-volume pressure projection with swirl, sink removal and open external boundaries','cell_px':C,'solid_normal_face_flux':0,'relative_mass_residual':relative,'total_sink_flux':float(sink.sum()),'net_boundary_inflow':boundary_inflow,'retained_sink_reaching_tracks':len(tracks),'velocity_95th_percentile_px_s':140},'rendering':'new generated material, dual-phase backward advection looping; regenerated funnel shading, no old six sand poses or old blue rings; bounded numerical tracer stepping','tests':{'opaque_compositions':True,'ora_exact':True,'finite_volume_balance':True,'zero_flow_through_solid_faces':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for n,seq in groups.items():
 b=io.BytesIO();seq[0].save(b,format='WEBP',save_all=True,append_images=seq[1:],duration=DT,loop=0,lossless=True);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
for n,im in static:items.append({'name':n,'src':uri(png(im))})
stills=[]
for im in frames[::4]:
 b=io.BytesIO();im.save(b,format='WEBP',lossless=True);stills.append(uri(b.getvalue(),'image/webp'))
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Siphons · écoulement autour des rochers</title><style>body{background:#12222d;color:#d5e8ea;font:16px system-ui;max-width:1050px;margin:28px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;width:684px;background:repeating-conic-gradient(#23414b 0 25%,#365962 0 50%) 0/16px 16px}button,select{padding:10px;margin:8px;background:#244855;color:#e2f2f0;border:1px solid #6a98a1}input{width:200px}</style><h1>Siphons · écoulement autour des rochers</h1><p>Eau régénérée et entraînée par un champ2D vers neuf siphons. Rochers et chaussée imperméables dans le calcul ; le passage reste sec. Palette bleu–turquoise, reflets de rive discrets. 128 phases à50ms ; curseur sur32 échantillons. Approximation stationnaire2D et rendu bouclé, pas une simulation3D de surface libre ni un test PMDO.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="31" value="0"><span id="label">Boucle 6,4 s</span><br><img id="view" alt="Courant d’eau vers les siphons"><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value*4+1)+' / 128 (échantillons 1/4)'};</script>'''
(R/'apercu_siphons_ecoulement_v3.html').write_text(html);print(json.dumps(manifest['flow'],indent=2))
