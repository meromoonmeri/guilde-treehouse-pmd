"""Planche de contrôle globale : toutes les lignées, 8 directions."""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P, foulard as F, lignees as L

def charger_reglages():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglages.json")
    return json.load(open(p)) if os.path.isfile(p) else {}

def contexte(pid, reglages):
    d = f"{P.DOS_SPRITE}/{pid}"
    _, anims = P.lire_animdata(d)
    a = next(x for x in anims if x["nom"]=="Idle" and not x["copie_de"])
    im,_ = P.charger_planche(d,"Idle")
    tc = P.taille_corps(im, a["w"], a["h"], im.shape[1]//a["w"], im.shape[0]//a["h"])
    r = dict(reglages.get("_defaut", {})); r.update(reglages.get(pid, {}))
    r.setdefault("largeur_cou", P.largeur_cou(d, anims))
    return d, anims, tc, r

def sheet(anim_nom="Idle", dirs=(0,1,2,4,6), S=6, col=0):
    reglages = charger_reglages(); pals = L.attribuer_palettes()
    lignesimg = []
    for lg in L.LIGNEES:
        pal = F.rampe(F.PALETTES[pals[lg["cle"]]])
        for pid, en, fr in lg["membres"]:
            d, anims, tc, r = contexte(pid, reglages)
            a = next((x for x in anims if x["nom"]==anim_nom and not x["copie_de"]), None)
            if a is None: continue
            im, off = P.charger_planche(d, anim_nom)
            w,h = a["w"], a["h"]; cols=im.shape[1]//w; rows=im.shape[0]//h
            fo = P.rendre_planche(im, off, w, h, cols, rows, anim_nom, pal, r, tc)
            c = min(col, cols-1)
            tiles=[]
            for dd in dirs:
                rr = dd if rows==8 else 0
                b=Image.fromarray(im[rr*h:(rr+1)*h, c*w:(c+1)*w])
                s=Image.fromarray(fo[rr*h:(rr+1)*h, c*w:(c+1)*w])
                tiles.append(Image.alpha_composite(b,s))
            lignesimg.append((pid, fr, pals[lg["cle"]], tiles))
    CW = max(t.size[0] for _,_,_,ts in lignesimg for t in ts)
    CH = max(t.size[1] for _,_,_,ts in lignesimg for t in ts)
    W = 132 + CW*S*len(dirs); H = CH*S*len(lignesimg)
    out = Image.new("RGBA",(W,H),(34,34,44,255)); dr=ImageDraw.Draw(out)
    for i,(pid,fr,pn,ts) in enumerate(lignesimg):
        y=i*CH*S
        if i%3==0: dr.rectangle([0,y,W,y+1],fill=(90,90,110,255))
        dr.text((6,y+CH*S//2-14), f"{pid} {fr}", fill=(235,235,245,255))
        dr.text((6,y+CH*S//2), pn, fill=(150,150,170,255))
        for j,t in enumerate(ts):
            x=132+j*CW*S+(CW-t.size[0])*S//2
            t2=t.resize((t.size[0]*S,t.size[1]*S),Image.NEAREST)
            out.paste(t2,(x,y+(CH-t.size[1])*S//2),t2)
    return out

if __name__=="__main__":
    an = sys.argv[1] if len(sys.argv)>1 else "Idle"
    img = sheet(an); p=f"/home/user/contact_{an}.png"; img.save(p); print(p, img.size)
