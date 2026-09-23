"""Bounded per-duo builds and pushes. A failure stops; no fake completion flag."""
from pathlib import Path
import subprocess,sys,shutil,json,time
R=Path(__file__).resolve().parents[2];C=R/'.cache/final_duos_v1';D=R/'renders/final_duos_v1';D.mkdir(parents=True,exist_ok=True)
assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()=='arena/01a0bf18-guilde-treehouse-pmd'
groups=['secrete','discipline','brulees','foret','lisiere','jungle','plaines','ile','volcan','desert','marin'];done=[]
for group in groups:
 print('START',group,flush=True)
 subprocess.run([sys.executable,str(R/'source/final_duos_v1/build.py'),group],cwd=R,check=True,timeout=150)
 for p in (C/'out').glob('D22_'+group+'*'):shutil.copyfile(p,D/p.name)
 done.append(group);status={'completed_duos':done,'day_maps':len(done)*2,'night_maps':len(done)*2,'total_duos':11,'runtime_PMDO':False,'ice_arena_IB2_complete':False}
 (D/'progress.json').write_text(json.dumps(status,indent=2)+'\n')
 subprocess.run(['git','add','source/final_duos_v1/build.py','source/final_duos_v1/run_all.py','source/final_duos_v1/README.md','renders/final_duos_v1'],cwd=R,check=True,timeout=20)
 subprocess.run(['git','commit','-qm','Publish day/night layered PMDO duo '+group],cwd=R,check=True,timeout=30)
 subprocess.run(['git','push','-q','origin','arena/01a0bf18-guilde-treehouse-pmd'],cwd=R,check=True,timeout=40)
 print('PUSHED',group,len(done),'/11',flush=True)
print('ALL11 DUOS PUBLISHED:22 day+22 night Ground editing maps',flush=True)
