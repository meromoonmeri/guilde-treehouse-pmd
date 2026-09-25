"""Temple STRICT+ — sévérité maximale : 8px quilting, masque roche exact, DA perspective intacte."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[2]
REF=R/"source/temple_reseau_strict_plus_v2/references/reference.png"
OUT=R/"renders/temple_reseau_strict_plus_v2"
SIZE=(512,512)
SPECS=[
 ('couloir_ns','Couloir N-S strict+',['N','S'],[(221,0),(288,0),(288,106),(407,121),(406,425),(325,452),(325,512),(191,512),(191,449),(93,425),(93,124),(221,106)]),
 ('couloir_ew','Couloir E-W strict+',['E','W'],[(0,216),(73,192),(439,192),(512,216),(512,332),(433,370),(80,370),(0,332)]),
 ('couloir_t','Jonction T strict+',['N','E','W'],[(221,0),(288,0),(288,122),(359,170),(413,239),(512,239),(512,332),(389,332),(321,436),(219,436),(120,332),(0,332),(0,239),(135,239),(171,170),(221,122)]),
 ('salle_traversee','Salle traversante strict+',['N','S'],[(224,0),(288,0),(288,149),(381,174),(435,262),(428,355),(324,445),(324,512),(192,512),(192,445),(90,355),(81,262),(129,174),(224,149)]),
 ('salle_laterale','Salle latérale strict+',['W','S'],[(103,184),(381,184),(454,263),(446,351),(324,449),(324,512),(192,512),(192,445),(75,355),(0,312),(0,236),(75,236)]),
 ('salle_carrefour','Salle carrefour strict+',['N','S','E','W'],[(224,0),(288,0),(288,135),(381,168),(423,230),(512,230),(512,298),(423,298),(388,361),(322,444),(322,512),(190,512),(190,444),(121,361),(82,298),(0,298),(0,230),(82,230),(130,168),(224,135)]),
]
def poly(pts): 
    im=Image.new('L', SIZE); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im)>0
def seam(cost):
    h,w=cost.shape
    dp=np.zeros((h,w), float); bp=np.zeros((h,w), int)
    dp[0]=cost[0]
    for y in range(1,h):
        for x in range(w):
            best=dp[y-1,x]; bi=x
            if x>0 and dp[y-1,x-1]<best: best=dp[y-1,x-1]; bi=x-1
            if x<w-1 and dp[y-1,x+1]<best: best=dp[y-1,x+1]; bi=x+1
            dp[y,x]=cost[y,x]+best; bp[y,x]=bi
    path=np.zeros(h,int); path[-1]=int(np.argmin(dp[-1]))
    for y in range(h-2,-1,-1): path[y]=bp[y+1,path[y+1]]
    return path
REF_IM=np.array(Image.open(REF).convert('RGBA'))
# 8px strict boxes
FLOOR_BOXES=[(x,y,x+8,y+8) for x in range(140,180,8) for y in range(200,232,8)]
WALL_BOXES=[(x,y,x+8,y+8) for x in range(80,300,8) for y in range(24,112,8)]
ROCK_BOXES=[(x,y,x+8,y+8) for x in range(12,36,8) for y in range(40,200,8)]+[(x,y,x+8,y+8) for x in range(336,400,8) for y in range(40,200,8)]+[(x,y,x+8,y+8) for x in range(12,400,8) for y in range(12,36,8)]+[(x,y,x+8,y+8) for x in range(12,400,8) for y in range(360,380,8)]
DIRT_BOXES=[(x,y,x+8,y+8) for x in range(152,224,8) for y in range(340,388,8)]
def quilt_fill(H,W,mask,boxes,seed=11):
    out=np.zeros((H,W,4),np.uint8)
    hh,ww=8,8
    ov=4
    rng=np.random.default_rng(seed)
    for y in range(0,H,hh-ov):
        for x in range(0,W,ww-ov):
            h=min(hh,H-y); w=min(ww,W-x)
            want=mask[y:y+h,x:x+w]
            if not want.any(): continue
            old=out[y:y+h,x:x+w]
            occupied=(old[:,:,3]>0)&want
            best=None
            perm=rng.permutation(len(boxes))
            for idx in perm[:32]:
                x0,y0,x1,y1=boxes[idx]
                patch=REF_IM[y0:y0+h,x0:x0+w]
                if patch.shape[0]!=h or patch.shape[1]!=w:
                    tmp=np.zeros((h,w,4),np.uint8); tmp[:patch.shape[0],:patch.shape[1]]=patch; patch=tmp
                cost=((old[:,:,:3].astype(float)-patch[:,:,:3])**2).sum(2)
                score=cost[occupied].mean() if occupied.any() else rng.random()
                if best is None or score<best[0]: best=(score,patch,cost)
            _,patch,cost=best
            take=want.copy()
            if x and w>=ov:
                s=seam(cost[:,:ov]); take[:,:ov]&= (np.arange(ov)[None,:] >= s[:,None])
            if y and h>=ov:
                s=seam(cost[:ov,:].T); take[:ov,:]&= (np.arange(ov)[:,None] >= s[None,:])
            take|= want & (old[:,:,3]==0)
            old[take]=patch[take]
    return out
def build():
    OUT.mkdir(parents=True, exist_ok=True); (OUT/"materiaux").mkdir(exist_ok=True)
    Image.fromarray(REF_IM[200:232,140:180]).save(OUT/"materiaux/patch_sol_8.png")
    Image.fromarray(REF_IM[40:64,12:36]).save(OUT/"materiaux/patch_roche_8.png")
    manifest={"reference":"IMG_5004 408x408 STRICT+","sha256":hashlib.sha256(REF.read_bytes()).hexdigest(),"size":list(SIZE),"method":"STRICT+ 8px quilting, masque roche exact, 0 recolor/rotate/scale, DA/perspective intacte","rooms":[]}
    yy,xx=np.mgrid[:SIZE[1],:SIZE[0]]
    for slug,title,dirs,polygon in SPECS:
        print(f"Building {slug} STRICT+ 8px")
        interior=poly(polygon)
        mur_mask=interior & (yy<165)
        dirt_mask=interior & (yy>360) & (xx>190) & (xx<322) & ~mur_mask
        stone_mask=interior & ~mur_mask & ~dirt_mask
        # rock = exact outer + side strips
        side_left=interior & (xx<140) & (yy>165) & (yy<380)
        side_right=interior & (xx>372) & (yy>165) & (yy<380)
        stone_mask= stone_mask & ~side_left & ~side_right
        rock_mask= ~interior
        masks={
            "01_sol_chemin": stone_mask,
            "01b_dirt": dirt_mask,
            "02_murs_fond": mur_mask,
            "03_roche_gauche": (rock_mask | side_left) & (xx<256),
            "04_roche_droite": (rock_mask | side_right) & (xx>=256),
            "05_roche_premier_plan": rock_mask & (yy>=380)
        }
        # exclusive
        occupied=np.zeros(SIZE[::-1], bool)
        order=["01_sol_chemin","01b_dirt","02_murs_fond","03_roche_gauche","04_roche_droite","05_roche_premier_plan"]
        final={}
        for k in order:
            m=masks[k] & ~occupied
            final[k]=m; occupied|=m
        remaining= ~occupied
        final["03_roche_gauche"]|= remaining & (xx<256)
        final["04_roche_droite"]|= remaining & (xx>=256)
        H,W=SIZE[1],SIZE[0]
        layers={}
        if final["01_sol_chemin"].any():
            arr=quilt_fill(H,W,final["01_sol_chemin"],FLOOR_BOXES, seed=hash(slug)%1000)
            a=np.array(Image.fromarray(arr)); a[~final["01_sol_chemin"]]=0; layers["01_sol_chemin"]=Image.fromarray(a)
        if final["01b_dirt"].any():
            arr=quilt_fill(H,W,final["01b_dirt"],DIRT_BOXES, seed=hash(slug)%1000+1)
            a=np.array(Image.fromarray(arr)); a[~final["01b_dirt"]]=0; layers["01b_dirt"]=Image.fromarray(a)
        if final["02_murs_fond"].any():
            arr=quilt_fill(H,W,final["02_murs_fond"],WALL_BOXES, seed=hash(slug)%1000+2)
            a=np.array(Image.fromarray(arr)); a[~final["02_murs_fond"]]=0; layers["02_murs_fond"]=Image.fromarray(a)
        for rk in ["03_roche_gauche","04_roche_droite","05_roche_premier_plan"]:
            if final[rk].any():
                arr=quilt_fill(H,W,final[rk],ROCK_BOXES, seed=hash(slug)%1000+3)
                a=np.array(Image.fromarray(arr)); a[~final[rk]]=0; layers[rk]=Image.fromarray(a)
        # piliers / autel direct
        pil=Image.new("RGBA", SIZE, (0,0,0,0))
        autel=Image.open(REF).convert("RGBA").crop((140,80,268,200))
        col1=Image.open(REF).convert("RGBA").crop((108,16,148,96))
        col2=Image.open(REF).convert("RGBA").crop((260,16,300,96))
        pil_left=Image.open(REF).convert("RGBA").crop((48,120,88,220))
        pil_right=Image.open(REF).convert("RGBA").crop((320,120,360,220))
        if "N" in dirs or True:
            pil.alpha_composite(autel, (256-64,40))
            pil.alpha_composite(col1, (120,16))
            pil.alpha_composite(col2, (360,16))
            pil.alpha_composite(pil_left, (60,120))
            pil.alpha_composite(pil_right, (420,120))
            layers["06_piliers_autel"]=pil
        patch=Image.open(REF).convert("RGBA").crop((140,200,180,232))
        p=np.array(patch.resize((64,64), Image.NEAREST))
        stripe=p[:32].copy(); stripe[:,:,3]=np.minimum(stripe[:,:,3], np.array([255]*16+[round(255*(31-y)/16) for y in range(16,32)],dtype=np.uint8)[:,None])
        portspec={'N':((224,0),(256,8)),'S':((224,480),(256,504)),'W':((0,224),(8,256)),'E':((480,224),(504,256))}
        entries=[]
        for d in dirs:
            port=Image.new("RGBA",SIZE)
            arr=stripe if d=='N' else stripe[::-1] if d=='S' else np.transpose(stripe,(1,0,2)) if d=='W' else np.transpose(stripe,(1,0,2))[:,::-1]
            pos,pt=portspec[d]; port.alpha_composite(Image.fromarray(arr.copy()),pos)
            layers[f"07_acces_{d}"]=port; entries.append({"direction":d,"xy":list(pt),"width":64,"layer":f"07_acces_{d}.png"})
        out=OUT/slug; out.mkdir(parents=True, exist_ok=True)
        for n,im in layers.items(): im.save(out/(n+".png"))
        recomposed=Image.new("RGBA",SIZE)
        for k in ["01_sol_chemin","01b_dirt","02_murs_fond","03_roche_gauche","04_roche_droite","05_roche_premier_plan"]:
            if k in layers: recomposed.alpha_composite(layers[k])
        recomposed.save(out/"terrain_sans_ports.png")
        comp=recomposed.copy()
        if "06_piliers_autel" in layers: comp.alpha_composite(layers["06_piliers_autel"])
        for k in layers:
            if k.startswith("07_acces"): comp.alpha_composite(layers[k])
        comp.save(out/"composition.png")
        schema=Image.new("RGB",SIZE,"#11101a"); sd=ImageDraw.Draw(schema); sd.polygon(polygon, fill="#c9b8e8")
        for e in entries:
            x,y=e["xy"]; sd.ellipse((x-13,y-13,x+13,y+13), fill="#8a6ab8"); sd.text((max(5,x-4),max(20,min(482,y-5))), e["direction"], fill="white")
        sd.text((12,12), title, fill="white"); schema.save(out/"schema.png")
        arr=np.array(comp)
        for d in dirs:
            edge=arr[0,224:288] if d=='N' else arr[-1,224:288] if d=='S' else arr[224:288,0] if d=='W' else arr[224:288,-1]
            assert np.all(edge[:,3]==255), (slug,d)
        manifest["rooms"].append({"id":slug,"title":title,"ports":entries,"layers":list(layers.keys())})
        print(f" -> {slug} {len(layers)} layers")
    (OUT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Built {len(manifest['rooms'])} STRICT+")
if __name__=="__main__": build()
