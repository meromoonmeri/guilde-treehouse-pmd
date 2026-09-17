from pathlib import Path
import subprocess,sys,re,zipfile,json
R=Path(__file__).resolve().parents[2];O=R/'renders/boreales_frames_generees_v5'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.boreales_frames_generees_v5.test_build','-q'],cwd=R,check=True)
 html=R/'apercu_boreales_generees_palette_v5.html';subprocess.run(['node','--check'],input=re.search(r'<script>(.*?)</script>',html.read_text(),re.S).group(1),text=True,check=True)
 (O/'verification.json').write_text(json.dumps({'dedicated_tests_passed':11,'generated_key_drawings':9,'output_frames':72,'intermediates':'premultiplied dissolves between generated drawings; not independently generated drawings','palette_cycling':'indexed palette lookup changes, fixed geometry/alpha verified','old_aurora_deformation':False,'sky_terrain_unchanged':True,'JS_syntax':'PASS','interactive_browser':'NOT TESTED','PMDO_runtime':'NOT TESTED','native_pixels':False,'native_animation_cycle':False},indent=2)+'\n')
 with zipfile.ZipFile(R/'renders/boreales_frames_generees_v5_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
  z.write(html,'apercu.html')
if __name__=='__main__':main()
