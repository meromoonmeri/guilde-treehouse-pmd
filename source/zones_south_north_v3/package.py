from pathlib import Path
import json,sys,subprocess,zipfile
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_south_north_v3'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.zones_south_north_v3.test_build','-q'],cwd=R,check=True)
 audit=json.loads((R/'exports/zones_bg_audit_v1/audit.json').read_text());records=[]
 for e in audit['entries']:
  f=e['file'];state='layout_pending';deliverable=None
  if f in ['forêtglomypmdsky.png','rockroadpmd.png']:state='south_north_candidate';deliverable='exports/zones_south_north_v3/'+('forest_cave' if f.startswith('forêt') else 'blue_rock_cave')
  elif e['kind']=='duplicate':state='duplicate_of_forest';deliverable='exports/zones_south_north_v3/forest_cave'
  elif f=='aurorepmdsky.png':state='layers_only_layout_pending';deliverable='exports/zones_relayout_v2/aurora'
  elif f=='bgnightbackgroundpmdskyda.png':state='BG_layout_candidate';deliverable='exports/zones_relayout_v2/night_sea'
  elif f=='pmdskyicearena.png':state='orientation_review_required';deliverable='exports/zones_relayout_v2/ice_arena'
  elif e['kind']=='UI':state='not_a_map'
  records.append(dict(file=f,kind=e['kind'],state=state,deliverable=deliverable,art_approved=False,runtime='NOT TESTED',planned_layers=e['layers'],orientation_requirement='South access toward northern cave/objective for playable terrain; backgrounds themselves are not traversable.'))
 ledger={'scope':'ALL23references from9ec9a081 plus retained guild programme. Listing a task is not doing it.','latest_user_correction':'Not horizontal widening: south-to-north playable approaches, cave at north, canonical materials, ground/path/trees/walls/entrance in independent layers.','references':records,'superseded_for_this_request':['exports/zones_relayout_v1/forest_clearing','exports/zones_relayout_v1/blue_rock_passage'],'counts':{'south_north_candidates':2,'BG_layout_candidates':1,'references_without_new_layout_meeting_current_direction':18,'duplicates':1,'not_a_map':1},'guild_programme':{'structures':'5 first-lot exterior candidates exist; remaining retained proposals and integration not completed.','vegetation':'First8-plant animated kit exists; scene integration not tested.','Eat':'9members have Eat; other actions remain open.','remaining_full32_actions_without_cycle':124},'all_user_work_finished':False,'runtime_approvals':0}
 (O/'FULL_PROGRAMME_STATUS.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
 report={'batch_tests':12,'checks':['Every visible RGBA matches its native source coordinate','All input source bytes match438b9288','Ordered layer recomposition','Native modules translated only, no mirror or rotation','Continuous path from south edge to northern entrance','8px-radius path-mask clearance','Ground/path/entrance independently exported','Portal not duplicated in frame','8pxTSX dimensions and references'],'runtime':'NOT TESTED','limits':'Path-mask connectivity is not a collision/warp/occlusion test and pixel equality is not artistic approval.','all_work_complete':False}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(R/'exports/zones_south_north_v3_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
 print('Correction pack and full remaining-programme ledger written.')
if __name__=='__main__':main()
