"""Real PMDO 0.8.12 native deserialization in cache, never a user installation.
Restores startup and all installed resources even on failure. No graphics test.
"""
from pathlib import Path
import subprocess, json
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
ENGINE=R/'.cache/pmdo-runtime/engine/PMDO';PACK=R/'exports/cliffnordouesttest1_animation_v1/a_copier'
def main():
 assert (ENGINE/'PMDO').is_file()
 startup=ENGINE/'Data/Script/origin/main.lua';original=startup.read_bytes();assert b'CLIFFNW_NATIVE' not in original
 backups={};dest=ENGINE/'cliffnw_cloud_test.tsv'
 if dest.exists():dest.unlink()
 try:
  for src in PACK.rglob('*'):
   if not src.is_file():continue
   dst=ENGINE/src.relative_to(PACK);backups[dst]=dst.read_bytes() if dst.exists() else None
   dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  startup.write_bytes(original+b'\n'+(HERE/'test_ground_load.lua').read_bytes())
  result=subprocess.run(['./PMDO','-guide'],cwd=ENGINE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
  (R/'.cache/pmdo-runtime/cliffnw-cloud-test.log').write_bytes(result.stdout)
  print(result.stdout.decode(errors='replace')[-2500:])
  if dest.exists():(HERE/'runtime_results.tsv').write_bytes(dest.read_bytes())
  assert result.returncode==0, 'Native load failed; see cache log and runtime_results.tsv'
  rows=dest.read_text().splitlines();assert len(rows)==13 and all(r.endswith('\tPASS') for r in rows)
 finally:
  startup.write_bytes(original)
  for dst,before in backups.items():
   if before is None:dst.unlink(missing_ok=True)
   else:dst.write_bytes(before)
 assert startup.read_bytes()==original
 report={'status':'PASS','pmdo':'0.8.12.0','assertions':rows,'startup_and_resources_restored':True,'method':'Real PMDO DataManager.GetGround and GetMapStatus via temporary Lua hook, -guide','GPU_tested':False,'cloud_playback_tested':False,'missing_custom_tile_banks_loaded':False,'sea_modified':False}
 (HERE/'runtime_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('13 native checks PASS. No rendering, missing-bank, or sea-animation validation.')
if __name__=='__main__':main()
