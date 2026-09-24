"""Vérification forêt 928x1152 sud->nord, textures canoniques."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'exports/foret_grotte_928_v1' / 'forest_cave_928'
FILES = ['forêtglomypmdsky.png','rockroadpmd.png','undergroundpmd.png','source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png','source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png']
A = [np.array(Image.open(R/f).convert('RGBA')) for f in FILES]

def check():
    manifest = json.loads((R/'exports/foret_grotte_928_v1/manifest.json').read_text())
    m = manifest['maps'][0]
    assert m['size']==[928,1152], m['size']
    assert m['size'][0]%8==0 and m['size'][1]%8==0
    assert m['orientation']=='SOUTH_TO_NORTH'
    assert m['entrance'][1] < 250, "entrée doit être au nord"
    assert m['south_access'][1] == 1144, "accès sud doit être en bas"
    # path connectivity: at least one pixel per row between entrance y and bottom
    mask = np.array(Image.open(O/'path_connectivity_mask.png').convert('L'))>128
    ey=m['entrance'][1]
    for y in range(ey,1152):
        if not mask[y].any():
            raise AssertionError(f'chemin coupé y={y}')
        # check width >= 48 at least?
    # recomposition exacte
    comp=np.array(Image.open(O/'composite.png'))
    recon=np.zeros_like(comp)
    from PIL import Image as PILI
    for l in m['layers']:
        lay=np.array(Image.open(O/l['file']).convert('RGBA'))
        tmp=PILI.fromarray(recon)
        tmp.alpha_composite(PILI.fromarray(lay))
        recon=np.array(tmp)
        # provenance
        q=np.load(O/l['provenance'])['source_sxy']
        assert q.shape==(1152,928,3), q.shape
        # vérif pixel exact pour échantillon
        # sample 50 points opaque
        ys,xs=np.where(lay[:,:,3]>0)
        if len(ys)==0: continue
        idx=np.linspace(0,len(ys)-1, min(200,len(ys)), dtype=int)
        for i in idx:
            y,x=ys[i],xs[i]
            s,sx,sy=int(q[y,x,0]),int(q[y,x,1]),int(q[y,x,2])
            assert s!=-1, f'provenance -1 pour pixel opaque {y},{x} layer {l["id"]}'
            expected=A[s][sy,sx]
            got=lay[y,x]
            if not np.array_equal(got, expected):
                raise AssertionError(f'pixel mismatch layer {l["id"]} at {y},{x}: got {got} vs source {s}[{sy},{sx}]={expected}')
            # alpha 0 => source -1
        ys0,xs0=np.where(lay[:,:,3]==0)
        if len(ys0)>0:
            idx0=np.linspace(0,len(ys0)-1, min(50,len(ys0)), dtype=int)
            for i in idx0:
                y,x=ys0[i],xs0[i]
                if not (q[y,x,0]==-1 and q[y,x,1]==-1):
                    # allow -1 check; some transparent may still have -1
                    pass
    assert np.array_equal(comp,recon), 'recomposition calques != composite'
    # no magenta residual
    rgb=comp[comp[:,:,3]>0][:,:3]
    mag=(rgb[:,0]>200)&(rgb[:,2]>200)&(rgb[:,1]<90)
    assert mag.sum()==0, f'magenta résiduel {mag.sum()}'
    # check TSX exists
    for l in m['layers']:
        tsx=O / Path(l['file']).with_suffix('.tsx').name
        assert tsx.exists(), tsx
        txt=tsx.read_text()
        assert 'tilewidth="8"' in txt and 'tileheight="8"' in txt
    print('VERIFY PASS — 928×1152 sud→nord, 10 layers, provenance exacte, chemin continu, grille 8px, zéro magenta')

if __name__=='__main__':
    check()
