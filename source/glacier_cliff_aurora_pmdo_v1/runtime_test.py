"""Run the real PMDO 0.8.12 Ground deserializer when the disposable cache exists.

No GPU/editor window is initialized deliberately.  This is a native loader test,
not a claim that movement or rendering was tested.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACK = ROOT / "exports/glacier_cliff_aurora_pmdo_v1"
RUNTIME = Path.home() / ".cache/pmdo-runtime/engine/PMDO/PMDO"

HOOK = r'''-- NATIVE_GLACIER_GROUND_TEST
local env = luanet.import_type('System.Environment')
local gfx = luanet.import_type('RogueEssence.Content.GraphicsManager')
local dm = luanet.import_type('RogueEssence.Data.DataManager')
local output = assert(io.open('native_glacier_ground_test.tsv', 'w'))
local ok, err = pcall(function()
  gfx.DungeonTexSize = 3
  local map = dm.Instance:GetGround('glacier_cliff_aurora_v1')
  assert(map ~= nil, 'null GroundMap')
  assert(map.Width == 72 and map.Height == 54, 'wrong dimensions')
  assert(map.TexSize == 3, 'wrong TexSize')
  assert(map.Layers.Count == 5, 'wrong layer count')
  assert(map.Entities.Count > 0, 'missing entity layer')
  output:write('glacier_cliff_aurora_v1\t' .. map.Width .. '\t' .. map.Height .. '\t' .. map.TexSize .. '\t' .. map.Layers.Count .. '\tPASS\n')
  output:flush()
end)
if not ok then output:write('glacier_cliff_aurora_v1\tFAIL\t' .. tostring(err) .. '\n') end
output:close()
print('NATIVE_GLACIER_GROUND_TEST ' .. (ok and 'PASS' or tostring(err)))
env.Exit(ok and 0 or 1)
'''


def main():
    binary = RUNTIME / "PMDO"
    base = RUNTIME / "Base/PathParams.xml"
    if not binary.is_file() or not base.is_file():
        print("SKIP: disposable PMDO 0.8.12 runtime or base assets are not installed")
        return 2
    mods = RUNTIME / "MODS"
    destination = mods / "glacier_cliff_aurora_v1"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(PACK, destination, ignore=shutil.ignore_patterns("tests"))
    startup = RUNTIME / "Data/Script/origin/main.lua"
    original = startup.read_bytes()
    result = RUNTIME / "native_glacier_ground_test.tsv"
    if result.exists():
        result.unlink()
    try:
        startup.write_bytes(original + b"\n" + HOOK.encode("utf-8"))
        proc = subprocess.run(
            ["./PMDO", "-guide", "-quest", "glacier_cliff_aurora_v1"],
            cwd=RUNTIME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=180,
        )
        (ROOT / "source/glacier_cliff_aurora_pmdo_v1/runtime_log.txt").write_bytes(proc.stdout)
        if proc.returncode != 0:
            print(proc.stdout.decode(errors="replace"))
            raise SystemExit(f"native PMDO exited with {proc.returncode}")
        rows = result.read_text(encoding="utf-8").splitlines()
        assert rows == ["glacier_cliff_aurora_v1\t72\t54\t3\t5\tPASS"], rows
        (ROOT / "source/glacier_cliff_aurora_pmdo_v1/runtime_results.tsv").write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )
        print("PASS: real PMDO 0.8.12 deserialized glacier_cliff_aurora_v1")
    finally:
        startup.write_bytes(original)
        assert startup.read_bytes() == original
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
