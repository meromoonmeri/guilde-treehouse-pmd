"""Verify this batch before writing its delivery report, progress and ZIP."""
from pathlib import Path
import sys,json,subprocess,zipfile
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_relayout_v2'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.zones_relayout_v2.test_build','-q'],cwd=R,check=True)
 report={'batch_tests_passed':8,'pixel_source_mismatches':0,'assets':3,'layers':19,'terrain_relayouts':1,'BG_relayouts':1,'BG_layer_preparations':1,'runtime_PMDO':'NOT TESTED','Tiled_import':'NOT TESTED','animation':'NONE','art_approved':False,'checks':['Source bytes match9ec9a081','Every visible RGBA pixel matches recorded source coordinates','Exact layer recomposition, alpha and8px grid','Aurora composite equals native source exactly','Moon, reflection and reef unchanged in size and position','TSX dimensions and image paths'],'limits':['Pixel checks do not validate joins, occlusion or gameplay.','Hidden sky behind moved clouds is reconstructed from native radial halo samples, not authenticated hidden image data.','Ice background planes are visible partitions, not complete hidden relief.']}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 old=json.loads((R/'exports/zones_relayout_v1/production_progress.json').read_text());audit=json.loads((R/'exports/zones_bg_audit_v1/audit.json').read_text());terrain=old['candidates']+['pmdskyicearena.png'];bg=['bgnightbackgroundpmdskyda.png'];preparation=['aurorepmdsky.png']
 progress={'scope':'Current progress after V1 and V2; prior reports remain historical. Candidates are not approvals.','terrain_candidates':terrain,'BG_layout_candidates':bg,'BG_layer_preparation_only':preparation,'pending_layout':[e['file'] for e in audit['entries'] if e['kind'] not in ['UI','duplicate'] and e['file'] not in terrain+bg],'duplicate':old['covered_duplicate'],'not_terrain':'wantedpokemontemplate.png','art_approved':0,'runtime_approved':0}
 (O/'production_progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(R/'exports/zones_relayout_v2_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
 print('V2 pack and current progress written.')
if __name__=='__main__':main()
