from pathlib import Path
import zipfile, json
R=Path(__file__).resolve().parents[2]
OUT=R/"renders/temple_reseau_strict_plus_v2"
zp=OUT/"temple_reseau_strict_plus_v2_pack.zip"
with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
    for room in json.loads((OUT/"manifest.json").read_text())["rooms"]:
        d=OUT/room["id"]
        for f in d.glob("*.png"): z.write(f, f"{room['id']}/{f.name}")
    for f in [OUT/"manifest.json",OUT/"verification.json",OUT/"PLANCHE.png"]:
        if f.exists(): z.write(f,f.name)
    apercu=R/"apercu_temple_reseau_strict_plus_v2.html"
    if apercu.exists(): z.write(apercu,aperçu.name if False else apercu.name)
    z.write(R/"source/temple_reseau_strict_plus_v2/references/reference.png","references/reference.png")
print(zp.stat().st_size/1024)
