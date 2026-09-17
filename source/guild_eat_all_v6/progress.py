"""Reconstruct explicit remaining-action tracking without declaring draft approval."""
from pathlib import Path
import json,collections
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/guild_eat_all_v6'
def main():
 audit=json.loads((ROOT/'exports/guild_members_audit/audit.json').read_text());contract=json.loads((ROOT/'source/pmd_character_pipeline/contract.json').read_text());report=json.loads((OUT/'verification.json').read_text())
 produced={('0282','Eat'):'gardevoir/Eat',('0282','Nod'):'gardevoir/Nod',('0285','Eat'):'shroomish/Eat'};produced.update({(slot,'Eat'):'Eat' for slot in ['0083','0674','0461','0186']});rows=[];members=[]
 for member in audit['members']:
  slot=member['slot'];pending=[]
  for action in contract['sprite']['completion_levels']['full']:
   item={'slot':slot,'pokemon':member['english_name'],'action':action,'runtime_PMDO':'NOT TESTED'}
   if action in member['xml_actions']:item['state']='native_available'
   elif (slot,action) in produced:
    item.update(state='technical_pass',cycle_complete=True,directions=8,art_approved=False,created_here=True)
   elif slot=='0282' and action=='Pose':item.update(state='native_cutscene_reuse',directions=1,quest_applicability='Not runtime verified')
   else:item.update(state='to_produce',cycle_complete=False);pending.append(action)
   rows.append(item)
  members.append({'slot':slot,'pokemon':member['english_name'],'french_name':member['french_name'],'remaining_without_local_cycle':pending})
 counts=dict(collections.Counter(item['state'] for item in rows));assert counts=={'native_available':156,'to_produce':124,'technical_pass':7,'native_cutscene_reuse':1},counts
 result={'scope':'Nine guild members, project full32 profile. Not the global SpriteCollab inventory. Native availability comes from the pinned audit, not proof of local import.','source_pin':audit['commit'],'counts':counts,'members':members,'actions':rows,'limits':'Seven cycles pass local technical checks; art/runtime acceptance still pending. Eight-direction cycles do not complete all guild assets.','eat_coverage':'9/9 members; six eight-view cycles and three unchanged native single-view cycles.'}
 (OUT/'production_progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 text='# Actions restant à produire — guilde\n\nProfil32 du projet :156actions déjà disponibles dans les bases natives,1Pose Cutscene réutilisée,7cycles8vues produits au stade technique, **124actions encore sans cycle local**. Les états ne valent pas validation artistique ou runtime.\n\n'
 for m in members:text+='## '+m['french_name']+'\n\n'+(', '.join(m['remaining_without_local_cycle']) or 'Profil natif complet : conserver les animations existantes, ne pas les recréer.')+'\n\n'
 (OUT/'PROGRESS.md').write_text(text.rstrip()+'\n');print(counts)
if __name__=='__main__':main()
