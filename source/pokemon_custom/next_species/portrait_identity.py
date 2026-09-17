"""Single-expression studies with the native Normal face as immutable anatomical base.
Generated files supply expression suggestions ONLY within hand-defined eye/mouth ROIs.
Not final portrait-sheet exports: the reference Normal background is retained for comparison.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SRC = Path(__file__).parent
OUT = ROOT / 'exports/pokemon_custom/portrait_identity_v1'
PROFILES = {
    'mega_raichu_x': {
        'editable': [(13,18,20,25), (27,18,33,25), (16,27,30,31)],
        'protected': [(3,22,13,32), (33,23,36,32), (21,25,26,27)],
    },
    'mega_raichu_y': {
        'editable': [(10,15,18,21), (24,15,31,21), (15,22,29,27)],
        'protected': [(4,20,14,29), (29,20,35,29), (18,20,24,22)],
    },
}


def constrained_expression(base, proposal, profile):
    a = np.array(base.convert('RGBA'))
    proposal = proposal.resize(base.size, Image.Resampling.NEAREST).convert('RGB')
    rgb = np.array(proposal).astype(np.int32)
    palette = np.unique(a[:,:,:3].reshape(-1,3), axis=0).astype(np.int32)
    distance = ((rgb[:,:,None,:] - palette[None,None,:,:])**2).sum(axis=3)
    quantized = palette[distance.argmin(axis=2)]
    mask = np.zeros(a.shape[:2], bool)
    for x1,y1,x2,y2 in profile['editable']:
        mask[y1:y2,x1:x2] = True
    for x1,y1,x2,y2 in profile['protected']:
        mask[y1:y2,x1:x2] = False
    out = a.copy()
    out[mask,:3] = quantized[mask]
    assert np.array_equal(out[~mask],a[~mask])
    assert np.array_equal(out[:,:,3],a[:,:,3])
    assert len(np.unique(out.reshape(-1,4),axis=0)) <= 15
    return Image.fromarray(out), mask


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    board = Image.new('RGB',(850,960),(21,30,44))
    draw = ImageDraw.Draw(board)
    report = {'status':'anatomy-constrained Happy studies, not user-approved emotion exports',
              'method':'Generated expression guide, restricted to explicit eye/mouth regions; native palette and every other pixel preserved.',
              'background':'Native Normal background retained for this comparison only; final Happy canonical background mapping still pending.',
              'subjects':{}}
    for i,(name,profile) in enumerate(PROFILES.items()):
        path = SRC/'references'/name/'Normal.png'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        normal = Image.open(path).convert('RGBA')
        generated = SRC/'generation'/f'{name}_happy_locked_v1.png'
        candidate,mask = constrained_expression(normal, Image.open(generated),profile)
        diff = np.any(np.array(normal)!=np.array(candidate),axis=2)
        assert diff.any(), 'Identical Normal must not be counted as a new expression'
        candidate.save(OUT/f'{name}_Happy_study.png')
        Image.fromarray(np.uint8(mask)*255).save(OUT/f'{name}_editable_mask.png')
        row_y = i*480
        draw.text((20,row_y+14),name+' / NORMAL natif',fill='white')
        draw.text((440,row_y+14),'HAPPY / proposition contrainte',fill='white')
        board.paste(normal.resize((400,400),Image.Resampling.NEAREST),(20,row_y+40))
        board.paste(candidate.resize((400,400),Image.Resampling.NEAREST),(440,row_y+40))
        changed = int(diff.sum())
        draw.text((20,row_y+452),f'{changed} pixels modifies, uniquement yeux/bouche. Anatomie exterieure et nez conserves.',fill=(172,211,222))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        report['subjects'][name] = {'normal_path':str(path.relative_to(ROOT)), 'normal_sha256':digest,
            'generator_source':str(generated.relative_to(ROOT)), 'changed_pixels':changed,
            'changed_pixels_outside_editable_regions':int((diff & ~mask).sum()),
            'normal_original_unchanged':True, 'profile':profile,
            'art_approval':False, 'technical_scope':'40x40, opaque, native <=15-color palette; this does not certify facial acting'}
    board.save(OUT/'comparison.png')
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
