"""Validate decoded deliverables independently of the renderer's assertions."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageSequence

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/transformations_v1'

def verify():
    m=json.loads((OUT/'manifest.json').read_text())
    v=json.loads((OUT/'verification.json').read_text())
    checks=[]
    for p,sha in m['source_hashes'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,p
    for name,seq in m['sequences'].items():
        for key in ['gifs','hold_gifs']:
            assert len(seq[key])==8
            for p in seq[key]:
                with Image.open(OUT/p) as im:
                    duration=sum(f.info.get('duration',0) for f in ImageSequence.Iterator(im))
                    assert duration==8000,(p,duration)
                    assert im.size==(256,288)
                    checks.append({'file':p,'decoded_frames':im.n_frames,'duration_ms':duration})
        for layer,pages in seq['direction_D_layers'].items():
            occupied=set()
            for page in pages:
                with Image.open(OUT/page['file']) as im:
                    assert im.mode=='RGBA'
                    assert im.size==tuple(page['cell'][i]*page['grid'][i] for i in range(2))
                span=set(range(page['start_frame'],page['start_frame']+page['logical_frames']))
                assert not occupied.intersection(span)
                assert min(span)>=0 and max(span)<240
                occupied.update(span)
        board=Image.new('RGB',(1024,576))
        for d,p in enumerate(seq['gifs']):
            with Image.open(OUT/p) as im:
                im.seek(im.n_frames-1)
                board.paste(im.convert('RGB'),(d%4*256,d//4*288))
        board.save(OUT/'review'/f'{name}_eight_final_views.png')
    for s in v['hold_seams']:
        name=f"{s['kind']}_hold_{m['directions'][s['direction']]}.gif"
        with Image.open(OUT/'gifs'/name) as im:
            fs=[np.array(f.convert('RGB')).astype(np.int16) for f in ImageSequence.Iterator(im)]
        steps=[float(np.abs(a-b).mean()) for a,b in zip(fs,fs[1:])]
        seam=float(np.abs(fs[-1]-fs[0]).mean())
        s['decoded_seam_mean_rgb_delta']=seam
        s['decoded_adjacent_p95']=float(np.percentile(steps,95))
        s['decoded_seam_within_adjacent_p95']=seam<=s['decoded_adjacent_p95']
        # This metric is recorded, not presented as artistic approval.
    v['gif_decode_checks']=checks
    (OUT/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
    print(f'{len(checks)} GIFs decoded: 8,000 ms each; RGBA page geometry and source hashes passed.')

if __name__=='__main__':verify()
