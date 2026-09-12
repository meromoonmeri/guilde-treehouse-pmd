-- Headless test of real PMDO 0.8.12 deserialization, NOT a graphics/editor test.
-- Loaded ONLY in a disposable runtime copy, then original main.lua restored.
local env=luanet.import_type('System.Environment')
local gfx=luanet.import_type('RogueEssence.Content.GraphicsManager')
local dm=luanet.import_type('RogueEssence.Data.DataManager')
local output=assert(io.open('native_ground_test.tsv','w'))
local ok,err=pcall(function()
  gfx.DungeonTexSize=3 -- normally initialized by graphics startup; collision grid needs 24px
  local tests={
{"v40812_01_cap_large_jour",140,114},
{"v40812_01_cap_large_nuit",140,114},
{"v40812_02_terrasse_croissant_jour",145,113},
{"v40812_02_terrasse_croissant_nuit",145,113},
{"v40812_03_double_belvedere_jour",146,114},
{"v40812_03_double_belvedere_nuit",146,114},
{"v40812_04_pointe_sinueuse_jour",141,114},
{"v40812_04_pointe_sinueuse_nuit",141,114},
{"v40812_05_grande_mesa_jour",143,113},
{"v40812_05_grande_mesa_nuit",143,113},
{"v40812_06_crique_profonde_jour",141,114},
{"v40812_06_crique_profonde_nuit",141,114},
{"v40812_07_balcon_haut_jour",137,114},
{"v40812_07_balcon_haut_nuit",137,114},
{"v40812_08_terrasses_decalees_jour",144,114},
{"v40812_08_terrasses_decalees_nuit",144,114},
{"v40812_09_cap_eventail_jour",139,114},
{"v40812_09_cap_eventail_nuit",139,114},
{"v40812_10_esplanade_arrondie_jour",142,114},
{"v40812_10_esplanade_arrondie_nuit",142,114}}
  for _,test in ipairs(tests) do
    local map=dm.Instance:GetGround(test[1])
    assert(map~=nil,'null ground: '..test[1])
    assert(map.Width==test[2] and map.Height==test[3],'wrong dimensions: '..test[1])
    assert(map.TexSize==1 and map.Layers.Count==9,'wrong layers/grid: '..test[1])
    assert(map.Entities.Count>0,'missing entity layer')
    output:write(test[1]..'\t'..map.Width..'\t'..map.Height..'\t'..map.Layers.Count..'\tPASS\n')
    output:flush()
  end
end)
if not ok then output:write('FAIL\t'..tostring(err)..'\n') end
output:close()
print('NATIVE_GROUND_TEST '..(ok and 'PASS' or tostring(err)))
env.Exit(ok and 0 or 1)
