import json, zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
OUT=R/'renders'/'entrees_magenta_duo_v1'
MAN=json.loads((OUT/'manifest.json').read_text())
zip_path=OUT/'entrees_magenta_duo_v1_pack.zip'
with zipfile.ZipFile(zip_path,'w', zipfile.ZIP_DEFLATED) as z:
    for scene in MAN['scenes']:
        zdir=OUT/'zones'/scene['id']
        for lf in scene['layers']:
            z.write(zdir/lf['file'], f"zones/{scene['id']}/{lf['file']}")
            tsx=zdir/Path(lf['file']).with_suffix('.tsx')
            if tsx.exists(): z.write(tsx, f"zones/{scene['id']}/{tsx.name}")
        if (zdir/'COMPOSITION.png').exists(): z.write(zdir/'COMPOSITION.png', f"zones/{scene['id']}/COMPOSITION.png")
        if (zdir/'ANIMATION_COMPLETE.webp').exists(): z.write(zdir/'ANIMATION_COMPLETE.webp', f"zones/{scene['id']}/ANIMATION_COMPLETE.webp")
        if (zdir/'ANIMATION_COMPLETE.gif').exists(): z.write(zdir/'ANIMATION_COMPLETE.gif', f"zones/{scene['id']}/ANIMATION_COMPLETE.gif")
        if (zdir/f"{scene['id']}.ora").exists(): z.write(zdir/f"{scene['id']}.ora", f"zones/{scene['id']}/{scene['id']}.ora")
        if (zdir/f"{scene['id']}.tmj").exists(): z.write(zdir/f"{scene['id']}.tmj", f"zones/{scene['id']}/{scene['id']}.tmj")
        if scene['animation']:
            for f in scene['animation']['files']:
                z.write(zdir/f, f"zones/{scene['id']}/{f}")
    z.write(OUT/'manifest.json', 'manifest.json')
    if (OUT/'verification.json').exists(): z.write(OUT/'verification.json', 'verification.json')
    # apercu
    apercu=R/'apercu_entrees_magenta_duo_v1.html'
    if apercu.exists(): z.write(apercu, 'apercu_entrees_magenta_duo_v1.html')
print(f"pack -> {zip_path} {zip_path.stat().st_size/1024:.1f} KB")
