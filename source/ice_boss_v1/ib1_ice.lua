-- IB1: glacial adaptation of Halcyon Searing Crucible. Original data untouched.
-- Requires Halcyon working-copy event registration and a registered ib1_ice_spikes Tile.
local patterns = require 'halcyon.ib1_patterns'
local EFFECT = 'ib1_ice_spikes'
local function state()
  SV.IB1IceBoss = SV.IB1IceBoss or {Direction='TopStraight', Countdown=-1}
  return SV.IB1IceBoss
end
local function layer(name)
  local layers = _ZONE.CurrentMap.Decorations
  for i=0,layers.Count-1 do if layers[i].Name == name then return layers[i].Anims end end
  error('IB1 decoration layer missing: '..name)
end
local function key(c) return c[1]..','..c[2] end
local function add_sprite(list, id, x, y)
  list:Add(RogueEssence.Ground.GroundAnim(RogueEssence.Content.ObjAnimData(id,4),RogueElements.Loc(x,y)))
end
local function ports(direction)
  local list=layer('IB1 active vents');list:Clear()
  if direction == 'None' then return end
  local p=patterns[direction]
  add_sprite(list,'IB1_vent',120,p.leftBottom and 312 or 192)
  add_sprite(list,'IB1_vent',360,p.rightBottom and 312 or 192)
end
local function active_cells()
  local cells={}
  for x=0,20 do for y=0,20 do
    if _ZONE.CurrentMap:GetTile(RogueElements.Loc(x,y)).Effect.ID == EFFECT then table.insert(cells,{x,y}) end
  end end
  return cells
end
local function display(rising,retracting)
  local list=layer('IB1 ice spikes');list:Clear();local moving={}
  for _,c in ipairs(rising or {}) do moving[key(c)]=true end
  for _,c in ipairs(active_cells()) do
    add_sprite(list,moving[key(c)] and 'IB1_spike_rise' or 'IB1_spike_idle',24*c[1],24*c[2]-8)
  end
  for _,c in ipairs(retracting or {}) do add_sprite(list,'IB1_spike_retract',24*c[1],24*c[2]-8) end
end
local function apply(c,remove)
  local loc=RogueElements.Loc(c[1],c[2]);local tile=_ZONE.CurrentMap:GetTile(loc)
  if remove then
    if tile.Effect.ID==EFFECT then tile.Effect=RogueEssence.Dungeon.EffectTile('',true,loc) end
  else
    tile.Effect=RogueEssence.Dungeon.EffectTile(EFFECT,true,loc)
    local chara=_ZONE.CurrentMap:GetCharAtLoc(loc)
    if chara~=nil then TASK:WaitTask(tile.Effect:InteractWithTile(RogueEssence.Dungeon.SingleCharContext(chara))) end
  end
end
local function run_pattern(direction,remove)
  local p=patterns[direction];ports(remove and 'None' or direction)
  GAME:WaitFrames(40) -- native pool preparation interval
  for _,wave in ipairs(p.waves) do
    for _,c in ipairs(wave.cells) do apply(c,remove) end
    display(remove and nil or wave.cells,remove and wave.cells or nil)
    GAME:WaitFrames(16) -- four new ice emergence/retraction poses,4frames each
    display();GAME:WaitFrames(24) -- total40frames between native waves
  end
end
function SINGLE_CHAR_SCRIPT.IB1_IceBegin(owner,ownerChar,context,args)
  if context.User~=nil then return end
  SV.IB1IceBoss={Direction='TopStraight',Countdown=-1}
  -- The serialized map already contains TopStraight, just like the original.
  ports('TopStraight');display()
end
function SINGLE_CHAR_SCRIPT.IB1_RemoveIce()
  local s=state()
  if s.Direction~='None' then run_pattern(s.Direction,true) end
  s.Direction='None'
end
function SINGLE_CHAR_SCRIPT.IB1_QueueIce()
  local map=_ZONE.CurrentMap;local l=map.Rand:Next(0,2);local r=map.Rand:Next(0,2)
  local name=l==0 and (r==0 and 'TopStraight' or 'DiagonalDown') or (r==1 and 'BottomStraight' or 'DiagonalUp')
  state().Direction=name;run_pattern(name,false)
end
function SINGLE_CHAR_SCRIPT.IB1_IceFlowHandler(owner,ownerChar,context,args)
  if context.User~=nil then return end
  local active=args.IceDuration or 2;local pause=args.NothingDuration or 1
  assert(active>=1 and pause>=1,'IB1 durations must be >=1')
  local s=state()
  if s.Countdown<0 then s.Countdown=active+pause-1 end
  if s.Countdown==pause then GAME:WaitFrames(20);SINGLE_CHAR_SCRIPT.IB1_RemoveIce() end
  if s.Countdown==0 then GAME:WaitFrames(20);SINGLE_CHAR_SCRIPT.IB1_QueueIce() end
  s.Countdown=s.Countdown-1
end
function SINGLE_CHAR_SCRIPT.IB1_IceChipDamage(owner,ownerChar,context,args)
  local chara=context.User;if chara==nil then return end
  if chara.Element1=='ice' or chara.Element2=='ice' or chara.Intrinsic=='ice_body' then return end
  local eff=PMDC.Dungeon.PreTypeEvent.CalculateTypeMatchup('ice',chara.Element1)+PMDC.Dungeon.PreTypeEvent.CalculateTypeMatchup('ice',chara.Element2)
  eff=PMDC.Dungeon.PreTypeEvent.GetEffectivenessMult(eff)
  if chara.Intrinsic=='thick_fat' then eff=eff/2 end
  if eff<=0 then return end
  local damage=math.max(1,math.floor(chara.MaxHP/16*eff/4))
  TASK:WaitTask(chara:InflictDamage(damage))
end
-- Clear hook delegates the original Halcyon victory checks/sequence, only the
-- cleanup is changed. No changes to SV.SearingTunnel or story flags here.
function SINGLE_CHAR_SCRIPT.IB1_IceBossClear(owner,ownerChar,context,args)
  local teams=_ZONE.CurrentMap.MapTeams
  for i=0,teams.Count-1 do
    local players=teams[i].Players
    for j=0,players.Count-1 do if not players[j].Dead then return end end
  end
  SINGLE_CHAR_SCRIPT.IB1_RemoveIce()
  SINGLE_CHAR_SCRIPT.LuaCheckBossClearEvent(owner,ownerChar,context,args)
end
return patterns
