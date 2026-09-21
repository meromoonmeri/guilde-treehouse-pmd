from pathlib import Path
import json
from lupa import LuaRuntime
C=Path('.cache/ice_boss_v1');text=(C/'native/Data/Script/halcyon/event_single.lua').read_text();src=text[text.index('function SINGLE_CHAR_SCRIPT.DrawLavaPool'):text.index('--For use in the Terrakion Fight')]
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''SINGLE_CHAR_SCRIPT={}; SV={SearingTunnel={}}; clock=0; writes={}; tiles={}
local function noop(...) end
print=noop
local function obj(...) return {} end
luanet={import_type=obj}; LUA_ENGINE={LuaCast=function(self,n,t)return n end}
SOUND={PlayBattleSE=noop}; DUNGEON={MoveScreen=noop}; GAME={WaitFrames=function(self,n)clock=clock+n end};TASK={WaitTask=noop}
RogueElements={Loc=function(x,y)return{X=x,Y=y}end}
RogueEssence={Content={ObjAnimData=obj,ScreenMover=obj},Ground={GroundAnim=obj},Dungeon={EffectTile=function(id,reveal,loc)table.insert(writes,{id=id,x=loc.X,y=loc.Y,tick=clock});return {ID=id}end}}
local anims={Add=noop,RemoveAt=noop};local map={Decorations={[0]={Anims=anims}},Rand={Next=function()return 0 end}}
function map:GetTile(loc)local k=loc.X..','..loc.Y;if not tiles[k]then tiles[k]={} end;return tiles[k]end
function map:GetCharAtLoc(loc)return nil end
_ZONE={CurrentMap=map}
''')
lua.execute(src);out={}
for name,left,right in [('TopStraight',False,False),('BottomStraight',True,True),('DiagonalDown',False,True),('DiagonalUp',True,False)]:
 lua.execute('clock=0;writes={};tiles={}');g=lua.globals();g.SINGLE_CHAR_SCRIPT.DrawLavaPool(left,right,False);getattr(g.SINGLE_CHAR_SCRIPT,'DrawStraightFlow' if left==right else 'DrawDiagonalFlow')(left,right,False)
 writes=[{'x':r['x'],'y':r['y'],'tick':r['tick'],'effect':r['id']} for r in g.writes.values()];out[name]={'writes':writes,'end_tick':g.clock,'unique_cells':sorted(set((r['x'],r['y']) for r in writes))};print(name,len(writes),len(out[name]['unique_cells']),g.clock,sorted(set(r['tick'] for r in writes)))
(C/'native_traces.json').write_text(json.dumps(out,indent=2)+'\n');(C/'native_flow_excerpt.lua').write_text(src)
