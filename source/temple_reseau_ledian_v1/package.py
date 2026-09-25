from pathlib import Path
import zipfile, json
R=Path(__file__).resolve().parents[2]
O=R/'renders/temple_reseau_ledian_v1'
zip_path=O/'temple_reseau_ledian_v1_pack.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    # bruts
    for p in (O/'bruts').glob("*.png"):
        z.write(p, f"bruts/{p.name}")
    # materiaux
    for p in (O/'materiaux').glob("*.png"):
        z.write(p, f"materiaux/{p.name}")
    # rooms
    for room in json.loads((O/'manifest.json').read_text())['rooms']:
        d=O/room['id']
        for f in d.glob("*.png"):
            z.write(f, f"{room['id']}/{f.name}")
    for f in [O/'manifest.json', O/'verification.json', O/'PLANCHE.png']:
        if f.exists(): z.write(f, f.name)
    # apercu
    apercu=R/'apercu_temple_reseau_ledian_v1.html'
    if apercu.exists(): z.write(apercu, apercu.name)
    # reference
    z.write(R/'source/temple_reseau_ledian_v1/references/reference_temple.png', 'references/reference_temple.png')
print(f"pack -> {zip_path} {zip_path.stat().st_size/1024:.1f} KB")
