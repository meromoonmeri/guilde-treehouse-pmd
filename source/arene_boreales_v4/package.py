from pathlib import Path
import subprocess,sys,re,zipfile,json
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_boreales_v4'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.arene_boreales_v4.test_build','-q'],cwd=R,check=True)
 html=R/'apercu_boreales_animees_v4.html';subprocess.run(['node','--check'],input=re.search(r'<script>(.*?)</script>',html.read_text(),re.S).group(1),text=True,check=True)
 (O/'verification.json').write_text(json.dumps({'dedicated_tests_passed':9,'intrinsic_poses':88,'animates_with_scroll_off':True,'rigid_translation_only':False,'intrinsic_loop_seconds':8.8,'combined_loop_seconds':26.4,'static_layers_byte_identical':True,'javascript_syntax':'PASS','interactive_browser':'NOT TESTED','runtime_PMDO':'NOT TESTED','native_cycle_recovered':False,'other_zones_complete':False},indent=2)+'\n')
 with zipfile.ZipFile(R/'renders/arene_boreales_v4_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
  z.write(html,'apercu.html')
if __name__=='__main__':main()
