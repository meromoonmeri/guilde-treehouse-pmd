"""Decode persisted outputs and check declared coverage, without claiming PMDO tests."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/tera_v2'

def main():
    manifest=json.loads((OUT/'surface_manifest.json').read_text());local=json.loads((OUT/'surface_verification.json').read_text());count=0
    for path,sha in local['source_hashes_preserved'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    for profile in manifest['profiles'].values():
        assert (OUT/profile['xml']).read_bytes()==(ROOT/profile['source_dir']/'AnimData.xml').read_bytes()
        for action in profile['actions']:
            with Image.open(ROOT/action['source']) as source:native=np.array(source.convert('RGBA'))
            assert len(action['phase_files'])==24
            for path in action['phase_files']:
                with Image.open(OUT/path) as image:a=np.array(image)
                assert a.shape==native.shape and np.array_equal(a[:,:,3],native[:,:,3])
                assert np.array_equal(a[native[:,:,3]==0],native[native[:,:,3]==0]);count+=1
    crowns=json.loads((OUT/'crown_manifest.json').read_text())
    assert crowns['type_count']==19
    for r in crowns['records']:
        with Image.open(OUT/r['file']) as im:assert im.size==(64,80) and im.mode=='RGBA'
        if r['type']=='stellar':assert r['status'].startswith('rejected') and r['file'].startswith('review/rejected_models/')
    catalogue=json.loads((OUT/'catalogue_report.json').read_text())
    with (OUT/'spritecollab_catalogue.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==catalogue['animation_sheet_count']==55953
    assert sum(r['processing_state'].startswith('24_phases') for r in rows)==catalogue['rendered_remote_sheets']==12
    gifs=[]
    for p in (OUT/'review').glob('*.gif'):
        with Image.open(p) as im:
            duration=sum(frame.info.get('duration',0) for frame in ImageSequence.Iterator(im))
            assert duration>0 and duration%1600==0
            gifs.append({'file':str(p.relative_to(OUT)),'decoded_frames':im.n_frames,'duration_ms':duration})
    result={'decoded_local_phase_sheets':count,'source_hashes_and_xml_preserved':True,'local_alpha_and_transparent_rgb_exact':True,'crown_models_decoded':len(crowns['records']),'crown_types_drawn_not_approved':19,'catalogue_complete':catalogue['complete_tree_inventory'],'remote_rendered_count':12,'gifs':gifs,'runtime_PMDO':'NOT INTEGRATED OR TESTED'}
    (OUT/'delivery_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
