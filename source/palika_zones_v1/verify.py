"""Independent checks for the generated Palika-style two-zone export."""
from __future__ import annotations

import io
import json
import struct
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "palika_zones_v1"
SIZE = (2048, 1536)
TILE = 8


def compose(images):
    out = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    for image in images:
        out.alpha_composite(image)
    return out


def verify_zone(zone_id: str):
    zone = OUT / zone_id
    manifest = json.loads((zone / "manifest.json").read_text())
    assert tuple(manifest["delivery_dimensions"]) == SIZE
    assert manifest["grid"]["tile_px"] == TILE
    composition = Image.open(zone / "COMPOSITION.png").convert("RGBA")
    assert composition.size == SIZE

    images = []
    alpha_sum = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
    for entry in manifest["layer_order_bottom_to_top"]:
        image = Image.open(zone / entry["file"]).convert("RGBA")
        assert image.size == SIZE, entry["id"]
        alpha = np.asarray(image)[:, :, 3] > 0
        alpha_sum += alpha.astype(np.uint8)
        images.append(image)
    assert int(alpha_sum.max()) == 1, f"overlapping alpha masks in {zone_id}"
    assert compose(images).tobytes() == composition.tobytes(), f"rebuild mismatch in {zone_id}"

    with zipfile.ZipFile(zone / "zone_seche.ora") as archive:
        assert archive.read("mimetype") == b"image/openraster"
        merged = Image.open(io.BytesIO(archive.read("mergedimage.png"))).convert("RGBA")
        assert merged.size == SIZE
        assert merged.tobytes() == composition.tobytes(), f"ORA merged mismatch in {zone_id}"

    ase = (zone / "zone_seche.aseprite").read_bytes()
    size, magic, frames, width, height, depth = struct.unpack_from("<IHHHHH", ase, 0)
    assert magic == 0xA5E0 and frames == 1 and (width, height, depth) == (2048, 1536, 32)

    tmj = json.loads((zone / "zone_seche.tmj").read_text())
    assert (tmj["width"], tmj["height"]) == (256, 192)
    assert (tmj["tilewidth"], tmj["tileheight"]) == (8, 8)
    assert len(tmj["layers"]) == len(images)
    return {"zone": zone_id, "layers": len(images), "size": list(SIZE), "reconstruction": "exact"}


def main():
    results = [verify_zone(zone["id"]) for zone in json.loads((OUT / "manifest.json").read_text())["zones"]]
    print(json.dumps({"status": "ok", "zones": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
