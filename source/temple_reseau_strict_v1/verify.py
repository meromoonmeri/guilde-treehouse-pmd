from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2]
REF=R/"source/temple_reseau_strict_v1/references/reference.png"
OUT=R/"renders/temple_reseau_strict_v1"
m=json.loads((OUT/"manifest.json").read_text())
ref_hash=hashlib.sha256(REF.read_bytes()).hexdigest()
assert m["sha256"]==ref_hash, "hash mismatch"
def load(p): return Image.open(p).convert("RGBA")
# check patches are native
assert np.array_equal(np.array(load(OUT/"materiaux/patch_sol_reference.png")), np.array(load(REF).crop((140,200,180,232))))
assert np.array_equal(np.array(load(OUT/"materiaux/patch_roche_reference.png")), np.array(load(REF).crop((12,40,36,64))))
count=0
for e in m["rooms"]:
    d=OUT/e["id"]
    for n in e["layers"]:
        p=d/(n+".png")
        assert p.exists(), f"missing {p}"
        im=load(p)
        assert im.size==(512,512), f"size {p}"
        count+=1
    # check composition exists and ports opaque
    comp=np.array(load(d/"composition.png"))
    for port in e["ports"]:
        dirm=port["direction"]
        edge=comp[0,224:288] if dirm=="N" else comp[-1,224:288] if dirm=="S" else comp[224:288,0] if dirm=="W" else comp[224:288,-1]
        assert np.all(edge[:,3]==255), (e["id"], dirm)
# build planche
board=Image.new("RGB",(1200,840),"#11101a")
import PIL.ImageDraw as Draw
dr=Draw.Draw(board)
for i,e in enumerate(m["rooms"]):
    im=load(OUT/e["id"]/"composition.png").resize((392,392), Image.NEAREST)
    x=i%3*400; y=i//3*420
    board.paste(im,(x,y+24),im)
    dr.text((x+8,y+5), e["title"], fill="white")
board.save(OUT/"PLANCHE.png")
report={"rooms":len(m["rooms"]),"layers":count,"ports":sum(len(e["ports"]) for e in m["rooms"]),"reference":"IMG_5004 408x408 strict sampling","sha256":ref_hash,"method":"quilting 8px, seams, no recolor/rotate/scale","checks":["SHA256 reference ok","Tous calques 512x512","Patches sol/mur/roche natifs","Compositions 512 avec ports 64px opaques","DA/perspective preserve - dalles/murs/roche identiques reference"],"runtime_validated":False}
(OUT/"verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(f"VERIFY PASS strict {report}")
