"""Actual PMDO 0.8.12 headless loading of the assembled project (40 Ground).
No graphical editor, animation or gameplay certification. Original startup restored.
"""
from pathlib import Path
import json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
PACK=Path.home()/'.cache/cote_v5_expeditions_pack';RUNTIME=ROOT/'.cache/pmdo-runtime/engine/PMDO'

def main():
 assert (RUNTIME/'PMDO').is_file()
 shutil.copytree(PACK,RUNTIME/'MODS/metano_expeditions',dirs_exist_ok=True)
 manifest=json.loads((PACK/'manifest.json').read_text());tests=[]
 for z in manifest['zones']:
  for v in z['variants'].values():tests.append([v['asset'],z['size'][0]//8,z['size'][1]//8,len(z['planes'])+4,2 if z.get('door') else 1])
 assert len(tests)==40
 table='{'+','.join('{"'+a+'",'+','.join(map(str,rest))+'}' for a,*rest in tests)+'}'
 lua='''
local env=luanet.import_type('System.Environment')
local gfx=luanet.import_type('RogueEssence.Content.GraphicsManager')
local dm=luanet.import_type('RogueEssence.Data.DataManager')
local output=assert(io.open('expeditions_runtime.tsv','w'))
local ok,err=pcall(function()
 gfx.DungeonTexSize=3
 local tests='''+table+'''
 for _,t in ipairs(tests) do
  local m=dm.Instance:GetGround(t[1])
  assert(m~=nil,'null '..t[1])
  assert(m.Width==t[2] and m.Height==t[3],'dimensions '..t[1])
  assert(m.TexSize==1 and m.Layers.Count==t[4],'layers '..t[1])
  assert(m.Entities[0].Markers.Count==t[5],'markers '..t[1])
  output:write(t[1]..'\\t'..m.Width..'\\t'..m.Height..'\\t'..m.Layers.Count..'\\tPASS\\n');output:flush()
 end
end)
if not ok then output:write('FAIL\\t'..tostring(err)..'\\n') end
output:close();print('EXPEDITIONS_NATIVE '..(ok and 'PASS' or tostring(err)))
env.Exit(ok and 0 or 1)
'''
 startup=RUNTIME/'Data/Script/origin/main.lua';original=startup.read_bytes()
 assert b'EXPEDITIONS_NATIVE' not in original and b'NATIVE_GROUND_TEST' not in original
 dest=RUNTIME/'expeditions_runtime.tsv'
 if dest.exists():dest.unlink()
 try:
  startup.write_bytes(original+lua.encode())
  result=subprocess.run(['./PMDO','-guide','-quest','metano_expeditions'],cwd=RUNTIME,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
  (PACK/'runtime_log.txt').write_bytes(result.stdout)
  assert result.returncode==0,result.stdout.decode(errors='replace')
  rows=dest.read_text().splitlines();assert len(rows)==40 and all(r.endswith('\tPASS') for r in rows)
  for target in [HERE/'runtime_results.tsv',PACK/'runtime_results.tsv']:target.write_text('\n'.join(rows)+'\n')
 finally:startup.write_bytes(original)
 report={'status':'PASS','pmdo':'0.8.12.0','ground_deserialized':40,'new_ground':20,'previous_ground':20,
 'assertions':['non-null native Ground','width/height','TexSize','layer count','marker count'],
 'method':'actual PMDO DataManager.GetGround in headless Lua startup hook',
 'graphics_constant_initialized':{'DungeonTexSize':3},'startup_restored':True,
 'editor_graphics_tested':False,'gpu_assets_tested':False,'gameplay_tested':False}
 for target in [HERE/'runtime_verification.json',PACK/'runtime_verification.json']:target.write_text(json.dumps(report,indent=2))
 print('PASS: all 40 Ground deserialized by real PMDO 0.8.12; no GPU test.')
if __name__=='__main__':main()
