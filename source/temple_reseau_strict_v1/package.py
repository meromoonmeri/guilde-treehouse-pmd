from pathlib import Path
import zipfile, json
R=Path(__file__).resolve().parents[2]
OUT=R/"renders/temple_reseau_strict_v1"
zip_path=OUT/"temple_reseau_strict_v1_pack.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (OUT/"materiaux").glob("*.png"): z.write(p, f"materiaux/{p.name}")
    for room in json.loads((OUT/"manifest.json").read_text())["rooms"]:
        d=OUT/room["id"]
        for f in d.glob("*.png"): z.write(f, f"{room['id']}/{f.name}")
    for f in [OUT/"manifest.json", OUT/"verification.json", OUT/"PLANCHE.png"]:
        if f.exists(): z.write(f, f.name)
    apercu=R/"apercu_temple_reseau_strict_v1.html"
    if apercu.exists(): z.write(apercu, apercu.name)
    z.write(R/"source/temple_reseau_strict_v1/references/reference.png", "references/reference.png")
print(f"pack {zip_path.stat().st_size/1024:.1f} KB")
