"""Montage de zones à plans indépendants, roche Treasure Town et palettes cycliques."""
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import json
from palette_cycle import create

R=Path(__file__).resolve().parents[1]
S=R/'source/zones_treasure_town'
F=R/'source/falaise'
FLOW={'etang':[(0,135,70,14,145),(0,252,89,15,144)],
      'cascades':[(0,178,118,17,230),(0,272,205,16,144),(1,394,161,30,190)]}
RIPPLES={'etang':[(4,171,258,70,18),(3,255,274,55,17)],'cascades':[(4,224,374,129,20),(3,389,365,80,20)]}
PLANTS={
 'littoral':[(0,35,211,18,17),(1,53,310,19,18),(2,215,177,18,16)],
 'plateaux':[(i%4,x,y,19,18) for i,(x,y) in enumerate([(25,170),(65,167),(110,184),(40,217),(91,239),(26,283),(58,315),(24,365),(144,295),(173,365),(288,333),(327,381),(401,206),(449,232),(389,288),(462,333),(445,371)])],
 'etang':[(4,38,248,29,45),(5,108,287,32,48),(4,300,271,26,41),(6,10,341,61,84),(7,401,336,56,89)],
 'cascades':[(4,11,279,61,107),(5,497,280,61,106),(0,111,399,19,17),(1,449,398,19,17)]}


def save(im,path):im.convert('RGBA').save(path,optimize=True)


def sky(mode,size,height):
    im=Image.open(F/f'ciel_{mode}_native.png').convert('RGBA').crop((0,0,480,160)).resize((size[0],height),Image.Resampling.NEAREST)
    a=np.array(im);out=np.empty((size[1],size[0],4),np.uint8);out[:height]=a
    c=np.median(a[-4:,:,:3],axis=(0,1)).astype('uint8');out[height:,:,:3]=c;out[height:,:,3]=255
    return Image.fromarray(out)


def stars(size,height):
    a=np.array(Image.open(F/'astres_nuit_native.png').convert('RGBA'));n,labels,stats,centers=cv2.connectedComponentsWithStats((a[:,:,3]>0).astype('uint8'),8)
    out=Image.new('RGBA',size);scale=min(1,height/105)
    for i in range(1,n):
        x,y,w,h,_=stats[i];part=a[y:y+h,x:x+w].copy();part[labels[y:y+h,x:x+w]!=i]=0
        q=Image.fromarray(part).resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.NEAREST)
        if not q.getbbox():continue
        xx=round(centers[i,0]/480*size[0]-q.width/2);yy=round(centers[i,1]/120*height-q.height/2)
        out.alpha_composite(q,(max(0,min(size[0]-q.width,xx)),max(0,min(height-q.height,yy))))
    return out


def prepare():
    cfg=json.loads((S/'layouts.json').read_text());bank=Image.open(S/'eau_sprites.png').convert('RGBA');plants=Image.open(S/'plantes_sprites.png').convert('RGBA')
    water_parts=[]
    for i in range(6):
        q=bank.crop(((i%3)*256,(i//3)*192,(i%3+1)*256,(i//3+1)*192));water_parts.append(q.crop(q.getbbox()))
    for name,c in cfg.items():
        d=S/name;size=tuple(c['size']);w,h=size
        for mode in ['jour','nuit']:save(sky(mode,size,max(90,c['sky']+10)),d/f'ciel_{mode}.png')
        save(stars(size,c['sky']),d/'astres_nuit.png')
        cl=Image.open(F/'nuages_native.png').convert('RGBA').crop((0,0,480,128));scale=min(w/480,c['sky']/115)
        cl=cl.resize((round(480*scale),round(128*scale)),Image.Resampling.NEAREST);plane=Image.new('RGBA',size);plane.alpha_composite(cl,((w-cl.width)//2,0));save(plane,d/'nuages.png')
        if (d/'reliefs_genere.png').exists():
            q=Image.open(d/'reliefs_genere.png').convert('RGBA')
            if name=='plateaux':
                a=np.array(q);color=np.median(a[236:248,:,:3],axis=(0,1)).astype('uint8')
                for yy in range(248,h):
                    t=min(1,(yy-248)/12);a[yy,:,:3]=np.rint(a[247,:,:3]*(1-t)+color*t).astype('uint8');a[yy,:,3]=255
                q=Image.fromarray(a)
            save(q,d/'reliefs.png')
        else:save(Image.new('RGBA',size),d/'reliefs.png')
        terrain=np.array(Image.open(d/'terrain_genere.png').convert('RGBA'));rr,gg,bb=[terrain[:,:,i].astype(int) for i in range(3)]
        grass=(gg>rr+8)&(gg>bb+20)&(terrain[:,:,3]>0)
        veg=Image.new('RGBA',size);placed=[]
        offsets=sorted([(x,y) for x in range(-28,29,4) for y in range(-28,29,4)],key=lambda q:q[0]*q[0]+q[1]*q[1])
        for i,x,y,bw,bh in PLANTS[name]:
            q=plants.crop(((i%4)*192,(i//4)*192,(i%4+1)*192,(i//4+1)*192));q=q.crop(q.getbbox()).resize((bw,bh),Image.Resampling.NEAREST);foot=np.array(q)[:,:,3]>0
            if i>=4:foot[:-5]=False
            for dx,dy in offsets:
                xx,yy=x+dx,y+dy
                if xx<0 or yy<0 or xx+bw>w or yy+bh>h:continue
                if grass[yy:yy+bh,xx:xx+bw][foot].mean()<.85:continue
                veg.alpha_composite(q,(xx,yy));placed.append([i,xx,yy,bw,bh]);break
        save(veg,d/'vegetation.png')
        water=Image.new('RGBA',size)
        if c['water_y']:
            y=c['water_y'];texture=Image.open(S/'eau_texture.png').convert('RGBA').resize((w,h-y),Image.Resampling.NEAREST)
            if name=='littoral':
                # Teinte de mer compatible avec le cap approuvé, motif généré indépendant.
                ref=np.array(Image.open(R/'source/sharpedo/mer_native.png').convert('RGBA'))[y:,:,:3].astype(float)
                a=np.array(texture);v=a[:,:,:3].astype(float);row=np.median(v,axis=1)[:,None,:]
                a[:,:,:3]=np.rint(ref+(v-row)*.55).clip(0,255).astype('uint8');texture=Image.fromarray(a)
            water.alpha_composite(texture,(0,y));create(water,'surface',d,'eau')
        else:save(water,d/'eau_native.png')
        effects=Image.new('RGBA',size)
        for sid,x,y,bw,bh in FLOW.get(name,[]):
            sprite=water_parts[sid];aa=np.array(sprite);cut=int(sprite.height*.72);active=aa[:cut,:,3]>0;xx=np.where(active.any(0))[0]
            body=sprite.crop((int(xx.min()),0,int(xx.max()+1),cut)).resize((bw,bh),Image.Resampling.NEAREST)
            effects.alpha_composite(body,(x,y))
            foot=sprite.crop((0,cut,sprite.width,sprite.height));foot=foot.crop(foot.getbbox()).resize((bw*3,max(12,bw)),Image.Resampling.NEAREST)
            effects.alpha_composite(foot,(x-bw,y+bh-5))
        for sid,x,y,bw,bh in RIPPLES.get(name,[]):effects.alpha_composite(water_parts[sid].resize((bw,bh),Image.Resampling.NEAREST),(x,y))
        if effects.getbbox():create(effects,'cascade',d,'cascades')
        else:save(effects,d/'cascades_native.png')
        (d/'placements.json').write_text(json.dumps({'vegetation':placed,'cascades':FLOW.get(name,[]),'reflets':RIPPLES.get(name,[])},ensure_ascii=False,indent=2)+'\n')
        print(name,'— texture TT, plans indépendants, cartes d’indices de cycling',flush=True)


if __name__=='__main__':prepare()
