from pathlib import Path
import json, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "map_zones_debloquees_v1"
expected_layers = [
    "00_fond_hub_cafe.png", "01_carte_parchemin.png", "02_chemins_zones.png",
    "03_emblemes_lieux.png", "04_etat_zones_debloquees.png",
]
for name in expected_layers:
    p = OUT / "layers" / name
    assert p.exists(), p
    assert Image.open(p).size == (1600, 1000), (name, Image.open(p).size)
for i in range(8):
    p = OUT / "animations" / f"MapZones_unlock_{i:02d}.png"
    assert p.exists() and Image.open(p).size == (1600, 1000)
assert (OUT / "animations/MapZones_unlock.webp").exists()
assert (OUT / "ZoneEmblemes_AssetSprite.png").exists()
assert Image.open(OUT / "ZoneEmblemes_AssetSprite.png").size == (864, 144)
data = json.loads((OUT / "assetsprite.json").read_text())
assert data["format"] == "AssetSprite" and len(data["entries"]) == 6
manifest = json.loads((OUT / "manifest.json").read_text())
for rel, info in manifest["files"].items():
    p = OUT / rel
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == info["sha256"], rel
print("PASS map zones: 5 calques, 8 frames PNG + WebP, 6 emblemes AssetSprite, manifest SHA valide")
