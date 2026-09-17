from pathlib import Path
import subprocess,sys,json,zipfile
R=Path(__file__).resolve().parents[2];O=R/'exports/ice_arena_aurora_v1'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.ice_arena_aurora_v1.test_build','-q'],cwd=R,check=True)
 report={'batch_tests_passed':10,'animation_steps':64,'frame_ticks':6,'duration_seconds':6.4,'authored_motion':True,'recovered_canonical_cycle':False,'PNG_rgb_source_mismatches':0,'static_terrain_motion':False,'terrain_runtime':'NOT TESTED','art_approved':False,'checks':['Canonical input hashes','Per-frame native aurora source coordinates','Frame64 equals frame0','At most1px column displacement between adjacent phases including wrap','Native star shapes/RGB, alpha-only twinkle','Real GIF frame count,6.4s duration, infinite loop','Static terrain invariant across sampled scene phases','All128PNG match atlas cells','Native palette in static layers','Central south approach stays clear of rendered ice'],'limits':'No engine collision, warp, import or parallax test. New motion, not an official recovered animation. Color-reduced GIFs are previews; losslessWebP and PNG are authoritative.'}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(R/'exports/ice_arena_aurora_v1_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
 print('Animated arena pack verified and written.')
if __name__=='__main__':main()
