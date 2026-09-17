from pathlib import Path
import json,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_glace_generee_v2'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.arene_glace_generee_v2.test_build','-q'],cwd=R,check=True)
 report={'tests_passed':11,'method':'Whole generated terrain and separately generated full floor, then layer separation. No cropped-map terrain assembly.','checks':['Two saved generated inputs with hashes','Exact recomposition of normalized keyed terrain','Disjoint visible masks cover the whole terrain','Clean generated hidden floor, no repeated source-map patches','Binary alpha and removal of magenta','Retained background animation bytes unchanged','Complete6.4second GIF loop and exact decoded delta frames','Static generated terrain invariant across phases','ORA layer recomposition matches scene phase0'],'canonical_terrain_pixels':False,'native_animation_cycle_recovered':False,'PMDO_runtime':'NOT TESTED','art_approved':False,'other_zones_complete':False}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(R/'renders/arene_glace_generee_v2_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
 print('Generated-render pack ready.')
if __name__=='__main__':main()
