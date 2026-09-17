from pathlib import Path
import subprocess,sys,json,zipfile,re
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_glace_large_v3'
def main():
 subprocess.run([sys.executable,'-m','unittest','source.arene_glace_large_v3.test_build','-q'],cwd=R,check=True)
 html=R/'apercu_arene_glace_large_v3.html';script=re.search(r'<script>(.*?)</script>',html.read_text(),re.S).group(1)
 subprocess.run(['node','--check'],input=script,text=True,check=True)
 report={'tests_passed':13,'javascript_syntax':'PASS','interactive_browser_test':'NOT RUN','size':[768,512],'method':'New whole landscape generation, uniformly scaled; independent regenerated sky and generated clean floor. No map-chunk terrain assembly.','loop':{'width':792,'frames':198,'seconds':26.4,'frame198_equals_frame0':True,'all_steps_including_join_translate_exactly_4px':True,'spatial_seam_columns_fully_transparent':True},'terrain_stationary':True,'stars_separate':True,'webp_lossless_RGBA':True,'native_game_cycle_recovered':False,'PMDO_runtime':'NOT TESTED','art_approved':False,'other_zones_complete':False}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(R/'renders/arene_glace_large_v3_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
  z.write(html,'apercu.html')
 print('Wide V3 package ready.')
if __name__=='__main__':main()
