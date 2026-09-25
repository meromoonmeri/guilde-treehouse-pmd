"""
Temple Réseau STRICT — même DA / matière / perspective que IMG_5004.png 408x408
Échantillonnage PUR : aucune génération, aucune recoloration, aucune rotation.
On réutilise les pixels natifs de la référence pour toutes les matières.
Quilting 8px avec seam (comme zones_south_north), partitions Ledian conservées.
6 pièces 512x512, 15 ports 64px, calques alignés.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[2]
REF=R/"source/temple_reseau_strict_v1/references/reference.png"
OUT=R/"renders/temple_reseau_strict_v1"
SIZE=(512,512)
# specs identiques Ledian (polygones 512)
SPECS=[
 ('couloir_ns','Couloir nord–sud élargi',['N','S'],[(221,0),(288,0),(288,106),(407,121),(406,425),(325,452),(325,512),(191,512),(191,449),(93,425),(93,124),(221,106)]),
 ('couloir_ew','Couloir est–ouest',['E','W'],[(0,216),(73,192),(439,192),(512,216),(512,332),(433,370),(80,370),(0,332)]),
 ('couloir_t','Jonction en T',['N','E','W'],[(221,0),(288,0),(288,122),(359,170),(413,239),(512,239),(512,332),(389,332),(321,436),(219,436),(120,332),(0,332),(0,239),(135,239),(171,170),(221,122)]),
 ('salle_traversee','Salle traversante',['N','S'],[(224,0),(288,0),(288,149),(381,174),(435,262),(428,355),(324,445),(324,512),(192,512),(192,445),(90,355),(81,262),(129,174),(224,149)]),
 ('salle_laterale','Salle latérale',['W','S'],[(103,184),(381,184),(454,263),(446,351),(324,449),(324,512),(192,512),(192,445),(75,355),(0,312),(0,236),(75,236)]),
 ('salle_carrefour','Salle carrefour',['N','S','E','W'],[(224,0),(288,0),(288,135),(381,168),(423,230),(512,230),(512,298),(423,298),(388,361),(322,444),(322,512),(190,512),(190,444),(121,361),(82,298),(0,298),(0,230),(82,230),(130,168),(224,135)]),
]
def poly(points, size=SIZE):
    im=Image.new('L', size); ImageDraw.Draw(im).polygon(points, fill=255); return np.array(im)>0

def seam(cost):
    # minimal seam for quilting (copied from zones_south_north)
    h,w=cost.shape
    dp=np.zeros((h,w), float); bp=np.zeros((h,w), int)
    dp[0]=cost[0]
    for y in range(1,h):
        for x in range(w):
            best=dp[y-1,x]
            bi=x
            if x>0 and dp[y-1,x-1]<best: best=dp[y-1,x-1]; bi=x-1
            if x<w-1 and dp[y-1,x+1]<best: best=dp[y-1,x+1]; bi=x+1
            dp[y,x]=cost[y,x]+best; bp[y,x]=bi
    # backtrack from min at bottom
    path=np.zeros(h, int); path[-1]=int(np.argmin(dp[-1]))
    for y in range(h-2,-1,-1): path[y]=bp[y+1, path[y+1]]
    return path

# Load reference atlas
REF_IM=np.array(Image.open(REF).convert('RGBA'))
Rh,Rw=REF_IM.shape[:2]

# Define source boxes per material by sampling directly from reference
# Floor : dalles claires centrales (stone)
FLOOR_BOXES=[(x,y,x+24,y+24) for x in [140,164,188,212] for y in [200,224,248,272]]
# Wall : murs violets ornés nord (violet)
WALL_BOXES=[(x,y,x+24,y+24) for x in [80,120,160,200,240,280] for y in [24,48,72,96]]
# Rock : bordure rocheuse brune (outer)
ROCK_BOXES=[(x,y,x+24,y+24) for x in [12,36,60] for y in [40,80,120,160,200,240,280,320]] + [(x,y,x+24,y+24) for x in [336,360,384] for y in [40,80,120,160,200,240,280,320]] + [(x,y,x+24,y+24) for x in [12,60,108,156,204,252,300,336] for y in [12,360]]
# Dirt : chemin terre ocre sud
DIRT_BOXES=[(x,y,x+24,y+16) for x in [152,176,200,224] for y in [340,356,372,388]]
# Columns / autel : direct copy (not quilted)
# For pillars we will copy pillar sprite directly when needed, but for walls we quilt

def quilt_fill(target_shape, mask, boxes, seed=11):
    """Fill mask area by quilting 24x24/24x16 patches sampled from REF, without blending."""
    H,W=target_shape
    out=np.zeros((H,W,4), dtype=np.uint8)
    # overlap
    hh,ww=24,24
    # if dirt, hh=16
    # Determine hh/ww from first box
    hh0=boxes[0][3]-boxes[0][1]; ww0=boxes[0][2]-boxes[0][0]
    hh,ww=hh0,ww0
    ov=min(8, hh//2, ww//2)
    rng=np.random.default_rng(seed)
    # pre-extract patches as arrays for speed
    # We will on-the-fly pick best seam
    for y in range(0,H, hh - ov):
        for x in range(0,W, ww - ov):
            h=min(hh, H-y); w=min(ww, W-x)
            want=mask[y:y+h, x:x+w]
            if not want.any(): continue
            old=out[y:y+h, x:x+w]
            occupied=(old[:,:,3]>0)&want
            best=None
            # try random subset of boxes
            perm=rng.permutation(len(boxes))
            for idx in perm[:24]:
                x0,y0,x1,y1=boxes[idx]
                # crop patch region of size h x w from reference (handle smaller at edges)
                patch=REF_IM[y0:y0+h, x0:x0+w]
                if patch.shape[0]!=h or patch.shape[1]!=w:
                    # pad if near edge (should not happen)
                    tmp=np.zeros((h,w,4), dtype=np.uint8)
                    tmp[:patch.shape[0], :patch.shape[1]]=patch
                    patch=tmp
                cost=((old[:,:,:3].astype(float)-patch[:,:,:3])**2).sum(2)
                score=cost[occupied].mean() if occupied.any() else rng.random()
                if best is None or score<best[0]:
                    best=(score, x0,y0,patch,cost)
            _,x0,y0,patch,cost=best
            take=want.copy()
            if x and w>=ov:
                # vertical seam
                s=seam(cost[:,:ov])
                take[:,:ov] &= (np.arange(ov)[None,:] >= s[:,None])
            if y and h>=ov:
                s=seam(cost[:ov,:].T)
                take[:ov,:] &= (np.arange(ov)[:,None] >= s[None,:])
            # keep transparent where old empty
            take |= want & (old[:,:,3]==0)
            old[take]=patch[take]
    return out

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"materiaux").mkdir(exist_ok=True)
    # save material patches for provenance
    Image.fromarray(REF_IM[200:232,140:180]).save(OUT/"materiaux"/"patch_sol_reference.png")
    Image.fromarray(REF_IM[24:48,80:104]).save(OUT/"materiaux"/"patch_mur_reference.png")
    Image.fromarray(REF_IM[40:64,12:36]).save(OUT/"materiaux"/"patch_roche_reference.png")
    manifest={"reference":"IMG_5004.png 408x408","sha256":hashlib.sha256(REF.read_bytes()).hexdigest(),"size":list(SIZE),"port_width":64,"method":"sampling strict - quilting 8px, no recolor/rotate, DA/perspective preserved","rooms":[]}
    yy,xx=np.mgrid[:SIZE[1],:SIZE[0]]
    for slug,title,dirs,polygon in SPECS:
        print(f"Building {slug} strict")
        # masks: polygon interior = walkable/ interior, outer is rock border
        interior=poly(polygon)
        # Determine masks: sol = interior central, murs = north strip of interior, roche = outer + sides
        # For strict, we follow Ledian partitions but fill with strict materials:
        # 01_sol_chemin = interior (floor + dirt)
        # 02_murs_fond = interior north band (yy<140) within interior
        # 03/04/05 = roche left/right/premier plan = remaining (interior sides + outer)
        # But outer rock is everything not interior, but inside 512 with rock texture
        # So define rock mask = ~interior plus side strips of interior near border
        H,W=SIZE[1],SIZE[0]
        sol_mask=interior.copy()
        # for corridors, sol is same as interior; for rooms, interior includes walls; we keep sol as interior for now and carve walls later
        # Walls: top band of interior
        mur_mask=interior & (yy<165)
        # Dirt/chemin sud: bottom strip of interior where path exits
        # For strict, we will split sol into stone + dirt at bottom
        # Keep sol_mask as interior excluding mur
        sol_mask=interior & ~mur_mask
        # Now split sol_mask into stone floor vs dirt path at south
        dirt_mask=sol_mask & (yy>360) & (xx>190) & (xx<322)
        stone_mask=sol_mask & ~dirt_mask
        # Rocks: all outer area plus side roche (we treat outer as rock, plus interior side margins)
        rock_mask=~interior
        # For side rocks, also include interior edge 20px near border for thickness perception?
        # Keep rock_mask as outer only, but also add left/right/premier plan partitions like Ledian:
        left_mask=rock_mask | (interior & (xx<140) & (yy>165) & (yy<380))
        # Actually we want 5 layers like Ledian: sol, murs, roche_gauche, roche_droite, roche_premier_plan
        # So we define:
        masks={}
        masks["01_sol_chemin"] = stone_mask
        masks["01b_dirt_chemin"] = dirt_mask
        masks["02_murs_fond"] = mur_mask
        # roche partitions from outer + side
        # Use same logic as Ledian but with strict rock source
        other=rock_mask
        # Also side interior rock strips should be part of roche, not sol
        # Redefine: sol should be central only, side strips are rock
        # So carve side strips from stone_mask
        side_left=interior & (xx<140) & (yy>165) & (yy<380)
        side_right=interior & (xx>372) & (yy>165) & (yy<380)
        # Adjust stone to exclude sides
        masks["01_sol_chemin"] = stone_mask & ~side_left & ~side_right
        masks["03_roche_gauche"] = (rock_mask | side_left) & (xx<256) & (yy>=165)
        masks["03_roche_gauche"] |= (rock_mask & (xx<256))
        masks["04_roche_droite"] = (rock_mask | side_right) & (xx>=256) & (yy>=165)
        masks["04_roche_droite"] |= (rock_mask & (xx>=256))
        masks["05_roche_premier_plan"] = rock_mask & (yy>=380)
        # Clean overlaps: ensure exclusive
        # Make them exclusive by priority
        occupied=np.zeros((H,W), bool)
        ordered=["01_sol_chemin","01b_dirt_chemin","02_murs_fond","03_roche_gauche","04_roche_droite","05_roche_premier_plan"]
        final_masks={}
        for k in ordered:
            m=masks.get(k, np.zeros((H,W), bool))
            m=m & ~occupied
            final_masks[k]=m
            occupied|=m
        # Any remaining uncovered (should be none) add to rock
        remaining= ~occupied & (np.ones((H,W),bool))
        # But we only want to cover where reference would be opaque? For strict, we cover full 512 with either rock or interior, so full coverage is expected
        # Rock should fill remaining
        final_masks["03_roche_gauche"] |= remaining & (xx<256)
        final_masks["04_roche_droite"] |= remaining & (xx>=256)

        # Now quilt each mask with its material
        layers={}
        # stone floor
        if final_masks["01_sol_chemin"].any():
            arr=quilt_fill(SIZE, final_masks["01_sol_chemin"], FLOOR_BOXES, seed=hash(slug)%1000)
            # convert to Image
            im=Image.fromarray(arr)
            # mask to keep only where mask true (already)
            a=np.array(im); a[~final_masks["01_sol_chemin"]]=0; layers["01_sol_chemin"]=Image.fromarray(a)
        if final_masks["01b_dirt_chemin"].any():
            arr=quilt_fill(SIZE, final_masks["01b_dirt_chemin"], DIRT_BOXES, seed=hash(slug)%1000+1)
            a=np.array(arr); a[~final_masks["01b_dirt_chemin"]]=0; layers["01b_dirt_chemin"]=Image.fromarray(a)
        if final_masks["02_murs_fond"].any():
            arr=quilt_fill(SIZE, final_masks["02_murs_fond"], WALL_BOXES, seed=hash(slug)%1000+2)
            a=np.array(arr); a[~final_masks["02_murs_fond"]]=0; layers["02_murs_fond"]=Image.fromarray(a)
        for rk in ["03_roche_gauche","04_roche_droite","05_roche_premier_plan"]:
            if final_masks[rk].any():
                arr=quilt_fill(SIZE, final_masks[rk], ROCK_BOXES, seed=hash(slug)%1000+3)
                a=np.array(arr); a[~final_masks[rk]]=0; layers[rk]=Image.fromarray(a)
        # Pillars / autel : copy directly from reference at correct perspective positions
        # Pillar positions: replicate reference's pillar layout scaled to 512
        # Reference pillars at approx (left pillar 60,80) and (right 320,80) and top columns (100,20) etc.
        # For strict, we will copy 3 pillars and autel from reference and paste at same relative north positions
        # Use direct copy without quilting
        # Extract pillar 40x60 from reference (pillar shaft)
        pillar=Image.open(REF).convert("RGBA").crop((68,72,108,172)) # left pillar + base
        # But we have rock and wall already quilted, we need to overlay pillars on top
        # For each room, we place pillars at north wall positions if room has north wall
        # Simplified: place 2 side pillars and top columns if interior includes north
        # We add as extra layer 06_piliers
        pil_layer=Image.new("RGBA", SIZE, (0,0,0,0))
        # top columns (small)
        col_top=Image.open(REF).convert("RGBA").crop((108,16,148,96))
        col_top2=Image.open(REF).convert("RGBA").crop((260,16,300,96))
        # autel at north center
        autel=Image.open(REF).convert("RGBA").crop((140,80,268,200))
        # Place autel centered north for rooms with north wall
        has_north="N" in dirs or mur_mask.any()
        if has_north:
            # center autel at 256, 80 (top)
            pil_layer.alpha_composite(autel, (256-64, 40))
            pil_layer.alpha_composite(col_top, (120, 16))
            pil_layer.alpha_composite(col_top2, (360, 16))
            # side pillars (from reference's lower pillars)
            pil_left=Image.open(REF).convert("RGBA").crop((48,120,88,220))
            pil_right=Image.open(REF).convert("RGBA").crop((320,120,360,220))
            # place side pillars along wall edges
            pil_layer.alpha_composite(pil_left, (60, 120))
            pil_layer.alpha_composite(pil_right, (420, 120))
            # keep only where interior or rock? Keep all, but will overlay
            layers["06_piliers_autel"]=pil_layer
        # Ports : use floor patch common stripe (like Ledian) but sample from reference floor
        patch=Image.open(REF).convert("RGBA").crop((140,200,180,232))
        p=np.array(patch.resize((64,64), Image.NEAREST))
        stripe=p[:32].copy(); stripe[:,:,3]=np.minimum(stripe[:,:,3], np.array([255]*16+[round(255*(31-y)/16) for y in range(16,32)], dtype=np.uint8)[:,None])
        portspec={'N':((224,0),(256,8)),'S':((224,480),(256,504)),'W':((0,224),(8,256)),'E':((480,224),(504,256))}
        entries=[]
        for d in dirs:
            port=Image.new("RGBA", SIZE)
            arr=stripe if d=='N' else stripe[::-1] if d=='S' else np.transpose(stripe,(1,0,2)) if d=='W' else np.transpose(stripe,(1,0,2))[:,::-1]
            pos,point=portspec[d]; port.alpha_composite(Image.fromarray(arr.copy()), pos)
            layers[f"07_acces_{d}"]=port
            entries.append({"direction":d,"xy":list(point),"width":64,"layer":f"07_acces_{d}.png"})
        # Save
        out=OUT/slug; out.mkdir(parents=True, exist_ok=True)
        for n,im in layers.items():
            im.save(out/(n+".png"))
        # recomposed without ports (for verification)
        recomposed=Image.new("RGBA", SIZE)
        for k in ["01_sol_chemin","01b_dirt_chemin","02_murs_fond","03_roche_gauche","04_roche_droite","05_roche_premier_plan"]:
            if k in layers: recomposed.alpha_composite(layers[k])
        recomposed.save(out/"terrain_sans_ports.png")
        # full composition with pillars and ports
        comp=recomposed.copy()
        if "06_piliers_autel" in layers: comp.alpha_composite(layers["06_piliers_autel"])
        for k in layers:
            if k.startswith("07_acces"): comp.alpha_composite(layers[k])
        comp.save(out/"composition.png")
        # schema
        schema=Image.new("RGB", SIZE, "#11101a"); sd=ImageDraw.Draw(schema); sd.polygon(polygon, fill="#c9b8e8")
        for e in entries:
            x,y=e["xy"]; sd.ellipse((x-13,y-13,x+13,y+13), fill="#8a6ab8"); sd.text((max(5,x-4),max(20,min(482,y-5))), e["direction"], fill="white")
        sd.text((12,12), title, fill="white"); schema.save(out/"schema.png")
        # verification: check ports opaque
        arr=np.array(comp)
        for d in dirs:
            edge=arr[0,224:288] if d=='N' else arr[-1,224:288] if d=='S' else arr[224:288,0] if d=='W' else arr[224:288,-1]
            assert np.all(edge[:,3]==255), (slug,d)
        manifest["rooms"].append({"id":slug,"title":title,"ports":entries,"layers":list(layers.keys()),"polygon":polygon})
        print(f"  -> {slug} {len(layers)} layers")
    (OUT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Built {len(manifest['rooms'])} strict rooms")

if __name__=="__main__":
    build()
