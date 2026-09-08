from pathlib import Path
from io import BytesIO
import json
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "zone_correction"


def read_tile(path):
    data = path.read_bytes()
    size, count = struct.unpack_from("<ii", data, 0)
    assert size == 8
    for i in range(count):
        x, y, off = struct.unpack_from("<iiq", data, 8 + i * 16)
        ln = struct.unpack_from("<q", data, off)[0]
        im = Image.open(BytesIO(data[off + 8:off + 8 + ln])).convert("RGBA")
        assert im.size == (8, 8), (path, i, im.size)
    return count


def main():
    m = json.loads((OUT / "manifest.json").read_text())
    final = Image.open(OUT / "final/zone_corrigee.png").convert("RGBA")
    assert final.size == (528, 384)
    for p in (OUT / "planches").glob("*.png"):
        im = Image.open(p).convert("RGBA")
        assert im.width % 8 == 0 and im.height % 8 == 0, (p, im.size)
        assert set(im.getchannel("A").getdata()) <= {0, 180, 210, 255}, p
    counts = {p.name: read_tile(p) for p in (OUT / "pmd/Content/Tile").glob("*.tile")}
    tm = json.loads((OUT / "tiled/zone_corrigee.tmj").read_text())
    assert (tm["tilewidth"], tm["tileheight"]) == (8, 8)
    assert (tm["width"], tm["height"]) == (66, 48)
    assert [x["name"] for x in tm["layers"]] == ["Sol", "Cliff entrance", "Rochers et bordures", "Fleurs et végétation"]
    ase = (OUT / "aseprite/zone_corrigee.aseprite").read_bytes()
    size, magic, frames, w, h, depth, flags, speed = struct.unpack_from("<IHHHHHIH", ase, 0)
    assert size == len(ase) and magic == 0xA5E0 and (frames, w, h, depth) == (1, 528, 384, 32)
    assert (OUT / "source/generation/zone_corrigee.png").exists()
    assert m["entity_removed"] is True and m["seamless_ground"] is True
    print("PASS")
    print("  final 528x384; grid 8 px;", counts)
    print("  Tiled 66x48; Aseprite valid; separated cliff/ground/rock/flower outputs")


if __name__ == "__main__":
    main()
