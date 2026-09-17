"""Complete the sixteen Carapagos front portraits; preserve every approved original."""
import hashlib
import json
import sys
import shutil
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
import build_canonical_expressions as base


def main():
    base.OUT=base.ROOT/'exports/pokemon_custom/canonical_expressions_v2'
    base.GALLERY=base.ROOT/'apercu_expressions_canoniques_v2.html'
    base.CONFIG['tirtouga']['emotions']=['Pain','Worried','Crying','Teary-Eyed','Determined','Joyous','Inspired','Dizzy','Sigh','Stunned']
    base.CONFIG['tirtouga']['show_preserved']=True
    base.build()
    out=base.OUT/'tirtouga'
    sys.path.insert(0,str(base.ROOT/'source/pmd_character_pipeline'))
    from validate import run
    shutil.copyfile(out/'portraits_partial.png',out/'portraits.png')
    result=run('portrait',out/'portraits.png','full')
    assert result['technical_precheck']=='PASS',result
    report=json.loads((base.OUT/'verification.json').read_text())
    report['carapagos_full_front_precheck']=result
    hashes={}
    for p in (out/'portraits_individual').glob('*.png'):
        hashes[p.stem]=hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest()
    report['carapagos_duplicate_raster_pairs']=[(a,b) for a in hashes for b in hashes if a<b and hashes[a]==hashes[b]]
    assert not report['carapagos_duplicate_raster_pairs']
    # Check expression subjects separately: differing emotion backgrounds cannot hide a copied face.
    raw={p.stem:hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest() for p in (out/'editable').glob('*_subject.png')}
    report['carapagos_duplicate_new_subject_pairs']=[(a,b) for a in raw for b in raw if a<b and raw[a]==raw[b]]
    assert not report['carapagos_duplicate_new_subject_pairs']
    (base.OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    html=base.GALLERY.read_text().replace('Ce lot est partiel.', 'Carapagos : les 16 expressions de face sont présentes (6 originaux conservés et 10 propositions). Méga-Raichu X/Y restent partiels.')
    html=html.replace('exports/pokemon_custom/canonical_expressions_v1/verification.json','exports/pokemon_custom/canonical_expressions_v2/verification.json')
    base.GALLERY.write_text(html)
    print('Carapagos: 16 front emotions, full technical PASS, no duplicated new subject rasters; art/runtime approval pending.')


if __name__=='__main__':main()
