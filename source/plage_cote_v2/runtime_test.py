#!/usr/bin/env python3
"""Chargement réel, sans affichage, des deux Grounds livrés par le vrai PMDO 0.8.12.

Prérequis (hors dépôt, voir source/pmdo_runtime/README.md) :
  .cache/pmdo-runtime/engine/PMDO/PMDO  = pmdc-linux-x64.zip v0.8.12 (SHA-256
  c64f72af…) + ressources de base DumpAsset @3e767571.
Le script copie le projet dans MODS/, ajoute temporairement un hook Lua au
script de démarrage, lance `PMDO -guide -quest plage_cote_v2`, puis restaure
le script. Il ne teste ni le rendu GPU, ni l'éditeur, ni le gameplay.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACK = Path.home() / '.cache/plage_cote_v2_pack'
RUNTIME = ROOT / '.cache/pmdo-runtime/engine/PMDO'
TAG = 'PLAGE_CV2_NATIVE'
NAMESPACE = 'plage_cote_v2'


def lua_for(asset: str, W: int, H: int) -> str:
    return f'''
local ok,err=pcall(function()
  local m=dm.Instance:GetGround('{asset}')
  assert(m~=nil,'Ground nul')
  assert(m.Width=={W} and m.Height=={H},'dimensions '..tostring(m.Width)..'x'..tostring(m.Height))
  assert(m.TexSize==3,'TexSize '..tostring(m.TexSize))
  assert(m.Layers.Count==1,'calques '..tostring(m.Layers.Count))
  assert(m.Entities[0].Markers.Count==1,'marqueurs')
  assert(m.Entities[0].GroundObjects.Count==2,'objets')
  local sea=m.Layers[0].Tiles[10][18].Layers[0]
  assert(sea.Frames.Count=={L.FRAMES},'frames mer '..tostring(sea.Frames.Count))
  assert(sea.FrameLength==8,'FrameLength '..tostring(sea.FrameLength))
  assert(sea.Frames[0].Sheet=='PLAGE_CV2_BRINE','feuille '..tostring(sea.Frames[0].Sheet))
  local wall=m.Layers[0].Tiles[0][0].Layers[0]
  assert(wall.Frames.Count=={L.FRAMES},'frames mur '..tostring(wall.Frames.Count))
  local exit=m.Layers[0].Tiles[{W - 1}][12].Layers[0]
  assert(exit.Frames.Count=={L.FRAMES},'frames sortie '..tostring(exit.Frames.Count))
  output:write('{asset}\\t'..m.Width..'\\t'..m.Height..'\\t'..m.TexSize..'\\t'..m.Layers.Count..'\\t'..sea.Frames.Count..'\\tPASS\\n');output:flush()
end)
if not ok then output:write('FAIL\\t{asset}\\t'..tostring(err)..'\\n') end
'''


def main():
    assert (RUNTIME / 'PMDO').is_file(), 'moteur PMDO absent'
    target = RUNTIME / 'MODS' / NAMESPACE
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(PACK, target)
    lua = '''
local env=luanet.import_type('System.Environment')
local gfx=luanet.import_type('RogueEssence.Content.GraphicsManager')
local dm=luanet.import_type('RogueEssence.Data.DataManager')
local output=assert(io.open('plage_cv2_runtime.tsv','w'))
gfx.DungeonTexSize=3
''' + ''.join(lua_for(L.LAYOUTS[name]['asset'], *L.dims(name)) for name in ('crique', 'anse')) + f'''
output:close();print('{TAG} termine')
env.Exit(0)
'''
    startup = RUNTIME / 'Data/Script/origin/main.lua'
    original = startup.read_bytes()
    assert TAG.encode() not in original
    result_file = RUNTIME / 'plage_cv2_runtime.tsv'
    if result_file.exists():
        result_file.unlink()
    try:
        startup.write_bytes(original + lua.encode())
        result = subprocess.run(['./PMDO', '-guide', '-quest', NAMESPACE], cwd=RUNTIME,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = result.stdout.decode(errors='replace')
        (HERE / 'runtime_log.txt').write_text('\n'.join(line for line in log.splitlines()
                                                        if TAG in line or 'rror' in line or 'xception' in line or 'Version' in line)[:20000])
        rows = result_file.read_text().splitlines() if result_file.exists() else []
        passed = (result.returncode == 0 and len(rows) == 2
                  and all(r.split('\t')[-1] == 'PASS' for r in rows)
                  and {r.split('\t')[0] for r in rows} == {'plage_cv2_crique', 'plage_cv2_anse'})
    finally:
        startup.write_bytes(original)
        assert startup.read_bytes() == original
    report = {'status': 'PASS' if passed else 'FAIL', 'pmdo': '0.8.12.0',
              'method': 'DataManager.Instance:GetGround dans un hook Lua de démarrage du vrai binaire PMDO (-guide -quest), sans affichage',
              'assets': {name: L.LAYOUTS[name]['asset'] for name in ('crique', 'anse')},
              'assertions': ['Ground non nul', '35 x 21 (crique) et 43 x 21 (anse) cellules', 'TexSize 3', '1 calque',
                             '1 marqueur', '2 GroundObjects',
                             'cellule de mer (10,18) : 15 frames, FrameLength 8, feuille PLAGE_CV2_BRINE',
                             'cellule de mur (0,0) et de sortie (dernière colonne, rangée 12) : 15 frames'],
              'rows': rows, 'return_code': result.returncode, 'startup_restored': True,
              'graphics_constant_initialized': {'DungeonTexSize': 3}, 'editor_graphics_tested': False,
              'gpu_assets_tested': False, 'gameplay_tested': False,
              'engine': {'zip': 'pmdc-linux-x64.zip v0.8.12', 'sha256': 'c64f72afd27b96d5a870f71e44d05ee1e952909e86b9a53d0479163763c61577',
                         'base_assets': 'audinowho/DumpAsset@3e767571f9dd94270b848b3a73de9bec2553a2eb'}}
    for path in (HERE / 'runtime_verification.json', PACK / 'runtime_verification.json'):
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(report['status'], rows, 'code', result.returncode)
    if not passed:
        print(log[-3000:])
        sys.exit(1)


if __name__ == '__main__':
    main()
