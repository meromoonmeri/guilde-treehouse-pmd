#!/usr/bin/env python3
"""Chargement réel, sans affichage, du Ground livré par le vrai PMDO 0.8.12.

Prérequis (hors dépôt, voir source/pmdo_runtime/README.md) :
  .cache/pmdo-runtime/engine/PMDO/PMDO  = pmdc-linux-x64.zip v0.8.12 (SHA-256
  c64f72af…) + ressources de base DumpAsset @3e767571.
Le script copie le projet dans MODS/, ajoute temporairement un hook Lua au
script de démarrage, lance `PMDO -guide -quest plage_beach_cave_v1`, puis
restaure le script. Il ne teste ni le rendu GPU, ni l'éditeur, ni le gameplay.
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
PACK = Path.home() / '.cache/plage_beach_cave_v1_pack'
RUNTIME = ROOT / '.cache/pmdo-runtime/engine/PMDO'
TAG = 'PLAGE_BC1_NATIVE'


def main():
    assert (RUNTIME / 'PMDO').is_file(), 'moteur PMDO absent'
    target = RUNTIME / 'MODS' / L.NAMESPACE
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(PACK, target)
    lua = f'''
local env=luanet.import_type('System.Environment')
local gfx=luanet.import_type('RogueEssence.Content.GraphicsManager')
local dm=luanet.import_type('RogueEssence.Data.DataManager')
local output=assert(io.open('plage_bc1_runtime.tsv','w'))
local ok,err=pcall(function()
  gfx.DungeonTexSize=3
  local m=dm.Instance:GetGround('{L.ASSET}')
  assert(m~=nil,'Ground nul')
  assert(m.Width=={L.NEW_W} and m.Height=={L.NEW_H},'dimensions '..tostring(m.Width)..'x'..tostring(m.Height))
  assert(m.TexSize==3,'TexSize '..tostring(m.TexSize))
  assert(m.Layers.Count==3,'calques '..tostring(m.Layers.Count))
  assert(m.Entities[0].Markers.Count==1,'marqueurs')
  assert(m.Entities[0].GroundObjects.Count==2,'objets')
  local sea=m.Layers[1].Tiles[10][4].Layers[0]
  assert(sea.Frames.Count==17,'frames mer '..tostring(sea.Frames.Count))
  assert(sea.FrameLength==16,'FrameLength '..tostring(sea.FrameLength))
  assert(sea.Frames[0].Sheet=='PLAGE_BC1_ANIM','feuille '..tostring(sea.Frames[0].Sheet))
  local sand=m.Layers[0].Tiles[20][10].Layers[0]
  assert(sand.Frames.Count==1 and sand.Frames[0].Sheet=='PLAGE_BC1_LAYER1','sable')
  assert(m.Layers[2].Tiles[20][10].Layers.Count==0,'front vide attendu')
  output:write('{L.ASSET}\\t'..m.Width..'\\t'..m.Height..'\\t'..m.TexSize..'\\t'..m.Layers.Count..'\\t'..sea.Frames.Count..'\\tPASS\\n');output:flush()
end)
if not ok then output:write('FAIL\\t'..tostring(err)..'\\n') end
output:close();print('{TAG} '..(ok and 'PASS' or tostring(err)))
env.Exit(ok and 0 or 1)
'''
    startup = RUNTIME / 'Data/Script/origin/main.lua'
    original = startup.read_bytes()
    assert TAG.encode() not in original
    result_file = RUNTIME / 'plage_bc1_runtime.tsv'
    if result_file.exists():
        result_file.unlink()
    try:
        startup.write_bytes(original + lua.encode())
        result = subprocess.run(['./PMDO', '-guide', '-quest', L.NAMESPACE], cwd=RUNTIME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = result.stdout.decode(errors='replace')
        (HERE / 'runtime_log.txt').write_text('\n'.join(line for line in log.splitlines() if TAG in line or 'rror' in line or 'xception' in line or 'Version' in line)[:20000])
        rows = result_file.read_text().splitlines() if result_file.exists() else []
        passed = result.returncode == 0 and len(rows) == 1 and rows[0].endswith('\tPASS')
    finally:
        startup.write_bytes(original)
        assert startup.read_bytes() == original
    report = {'status': 'PASS' if passed else 'FAIL', 'pmdo': '0.8.12.0', 'method': 'DataManager.Instance:GetGround dans un hook Lua de démarrage du vrai binaire PMDO (-guide -quest), sans affichage',
              'asset': L.ASSET, 'assertions': ['Ground non nul', f'Width {L.NEW_W} / Height {L.NEW_H} cellules', 'TexSize 3', '3 calques', '1 marqueur', '2 GroundObjects', 'cellule de mer (10,4) : 17 frames, FrameLength 16, feuille PLAGE_BC1_ANIM', 'cellule de sable (20,10) : 1 frame PLAGE_BC1_LAYER1, Front vide'],
              'rows': rows, 'return_code': result.returncode, 'startup_restored': True,
              'graphics_constant_initialized': {'DungeonTexSize': 3}, 'editor_graphics_tested': False, 'gpu_assets_tested': False, 'gameplay_tested': False,
              'engine': {'zip': 'pmdc-linux-x64.zip v0.8.12', 'sha256': 'c64f72afd27b96d5a870f71e44d05ee1e952909e86b9a53d0479163763c61577', 'base_assets': 'audinowho/DumpAsset@3e767571f9dd94270b848b3a73de9bec2553a2eb'}}
    for path in (HERE / 'runtime_verification.json', PACK / 'runtime_verification.json'):
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(report['status'], rows, 'code', result.returncode)
    if not passed:
        print(log[-3000:])
        sys.exit(1)


if __name__ == '__main__':
    main()
