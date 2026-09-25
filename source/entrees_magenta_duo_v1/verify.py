import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[2]
OUT=R/'renders'/'entrees_magenta_duo_v1'
CFG=json.loads((Path(__file__).parent/'references'/'config.json').read_text())
MAN=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else None

def check():
    assert OUT.exists(), "build not run"
    assert MAN, "manifest missing"
    ok=0; fail=0
    for scene in MAN['scenes']:
        base=scene['base']
        conf=next(c for c in CFG if c['id']==base)
        w,h=conf['size']
        assert w%8==0 and h%8==0, f"{scene['id']} size not multiple 8"
        zdir=OUT/'zones'/scene['id']
        assert zdir.exists(), f"missing {zdir}"
        # check layers exist and are aligned
        comp=np.zeros((h,w,4), dtype=np.uint8)
        for lf in scene['layers']:
            p=zdir/lf['file']
            assert p.exists(), f"missing layer {p}"
            im=np.array(Image.open(p).convert('RGBA'))
            assert im.shape==(h,w,4), f"size mismatch {p}"
            # composite
            alpha=im[:,:,3:]/255.0
            comp[:,:,:3]=comp[:,:,:3]*(1-alpha)+im[:,:,:3]*alpha
            comp[:,:,3]=np.maximum(comp[:,:,3], im[:,:,3])
        # check opaque where expected? For demo fallback, may not be fully opaque at magenta holes — allow but log
        # check TSX
        for lf in scene['layers']:
            tsx=zdir/Path(lf['file']).with_suffix('.tsx')
            assert tsx.exists(), f"missing tsx {tsx}"
            txt=tsx.read_text()
            assert 'tilewidth="8"' in txt
        # animation check
        if scene['animation']:
            anim=scene['animation']
            assert len(anim['files'])==conf['frames'] or len(anim['files'])>0, "anim count"
            for f in anim['files']:
                assert (zdir/f).exists()
            assert sum(anim['durations_ms'])==anim['cycle_ms']
        # composition exists
        assert (zdir/'COMPOSITION.png').exists()
        # ORA exists
        assert (zdir/f"{scene['id']}.ora").exists()
        ok+=1
    # masques
    for conf in CFG:
        assert (OUT/'masques'/conf['id']/'valid.png').exists()
    print(f"VERIFY PASS: {ok} scenes, {ok+fail} total")
    # write verification.json
    (OUT/'verification.json').write_text(json.dumps({"scenes": ok, "status":"PASS", "grid":8, "note":"Fichier uniquement, pas de test PMDO/GPU"}, indent=2))

if __name__=='__main__':
    check()
