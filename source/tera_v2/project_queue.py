"""Refresh only the project missing-resource queue selected by the user."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/tera_v2'

def main():
    audit=json.loads((ROOT/'source/sprite_audit_v2/audit.json').read_text())
    required=json.loads((ROOT/'source/pmd_character_pipeline/contract.json').read_text())['portrait']['required_full']
    allslots={r['path']:r for r in audit['all_slots']}
    def entry(path):
        r=allslots[path]
        return {'slot':path,'name':r['name'],'existing_sprite_actions':list(r['sprite_files']),'existing_portraits':list(r['portrait_files']),'missing_required_portraits':[n for n in required if n not in r['portrait_files']],'policy':'Preserve every existing native portrait; values in tracker dictionaries are lock flags, not presence flags','status':'Not produced in this generation-limited turn'}
    priority=[entry(p) for p in ['0893','1024/0002','0026/0002','0026/0003']]
    base=[entry(r['path']) for r in audit['base_missing_sprites']]
    approval=json.loads((ROOT/'source/pokemon_custom/tirtouga_portraits_v3/approval.json').read_text())
    for name,sha in approval['sha256'].items():
        p=ROOT/'exports/pokemon_custom/tirtouga_portraits_v4/portraits_individual'/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
    report={'scope':'User selected existing project queue, not production of every missing SpriteCollab asset','pin':audit['commit'],'carapagos':{'local_actions':32,'local_portraits':16,'approved_original_hashes_preserved':approval['sha256'],'status':'Previously exported; consolidated review added, not new artwork or final art/PMDO approval'},'priority':priority,'base_missing_sprite_species':base,'base_count':len(base),'base_missing_normal_portrait_count':len(audit['base_missing_normal_portrait']),'priority_missing_portrait_count':sum(len(x['missing_required_portraits']) for x in priority),'blocked_generation_attempts':['zarude_west_v2.png','terapagos_stellar_front_v2.png'],'generation_limit':'10 successful crown generations; later Zarude and Stellar calls blocked; no files produced for them'}
    (OUT/'project_queue.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Project audit:',len(base),'base species missing sprites; priority missing emotions:',report['priority_missing_portrait_count'])

if __name__=='__main__':main()
