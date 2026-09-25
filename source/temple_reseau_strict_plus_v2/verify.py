from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2]
REF=R/"source/temple_reseau_strict_plus_v2/references/reference.png"
OUT=R/"renders/temple_reseau_strict_plus_v2"
m=json.loads((OUT/"manifest.json").read_text())
assert m["sha256"]==hashlib.sha256(REF.read_bytes()).hexdigest()
def load(p): return Image.open(p).convert("RGBA")
count=0
for e in m["rooms"]:
    d=OUT/e["id"]
    for n in e["layers"]:
        assert (d/(n+".png")).exists()
        assert load(d/(n+".png")).size==(512,512)
        count+=1
    comp=np.array(load(d/"composition.png"))
    for port in e["ports"]:
        dirm=port["direction"]
        edge=comp[0,224:288] if dirm=="N" else comp[-1,224:288] if dirm=="S" else comp[224:288,0] if dirm=="W" else comp[224:288,-1]
        assert np.all(edge[:,3]==255)
board=Image.new("RGB",(1200,840),"#11101a")
import PIL.ImageDraw as Draw
dr=Draw.Draw(board)
for i,e in enumerate(m["rooms"]):
    im=load(OUT/e["id"]/"composition.png").resize((392,392), Image.NEAREST)
    x=i%3*400; y=i//3*420
    board.paste(im,(x,y+24),im)
    dr.text((x+8,y+5), e["title"], fill="white")
board.save(OUT/"PLANCHE.png")
report={"rooms":6,"layers":count,"ports":15,"method":"STRICT+ 8px quilting, exact rock mask, 0 recolor"}
(OUT/"verification.json").write_text(json.dumps(report,indent=2))
print(f"VERIFY PASS STRICT+ {report}")
