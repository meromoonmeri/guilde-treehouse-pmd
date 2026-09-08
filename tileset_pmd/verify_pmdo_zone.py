from pathlib import Path
from io import BytesIO
import json
import struct
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tileset_pmd"
TILE_DIR = OUT / "pmd" / "Content" / "Tile"
PLANCHES = OUT / "planches"


def tile_entries(path):
    data = path.read_bytes()
    size, count = struct.unpack_from("<ii", data, 0)
    assert size == 8, (path, size)
    entries = []
    for i in range(count):
        x, y, offset = struct.unpack_from("<iiq", data, 8 + i * 16)
        ln = struct.unpack_from("<q", data, offset)[0]
        png = data[offset + 8:offset + 8 + ln]
        im = Image.open(BytesIO(png)).convert("RGBA")
        assert im.size == (8, 8), (path, i, im.size)
        entries.append((x, y, im))
    return entries


def assert_hard_pixels(path):
    im = Image.open(path).convert("RGBA")
    alpha = set(im.getchannel("A").getdata())
    # The only partial alpha deliberately retained is contact shadow metadata.
    assert alpha <= {0, 180, 210, 255}, (path, sorted(alpha))
    return im


def main():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["grid"]["pmd_ground_tile_px"] == 8
    assert manifest["grid"]["interpolation"] == "none"
    names = [
        "01_Luminous_Spring_Base", "02_Luminous_Spring_River", "03_Luminous_Spring_Cliffs",
        "04_Luminous_Spring_Fringe", "05_Luminous_Spring_Objects", "06_Luminous_Spring_Objects_Over",
        "07_Luminous_Spring_Objects_Under", "08_Luminous_Spring_Shadows", "09_Luminous_Spring_River_Animations",
    ]
    counts = {}
    for name in names:
        p = TILE_DIR / f"{name}.tile"
        e = tile_entries(p)
        counts[name] = len(e)
        assert len({(x, y) for x, y, _ in e}) == len(e), p
        for _, _, im in e:
            alpha = set(im.getchannel("A").getdata())
            assert alpha <= {0, 180, 210, 255}, (p, alpha)
    # All artist boards are native 8 px sheets, not interpolated previews.
    for p in sorted(PLANCHES.glob("*.png")):
        im = assert_hard_pixels(p)
        assert im.width % 8 == 0 and im.height % 8 == 0, (p, im.size)
    # Eight distinct frames with one canvas and a constant bottom-center anchor.
    strip = Image.open(PLANCHES / "05_lumiere_frames.png").convert("RGBA")
    assert strip.size == (256, 32)
    frames = [strip.crop((i * 32, 0, i * 32 + 32, 32)) for i in range(8)]
    assert len({f.tobytes() for f in frames}) == 8, "light frames were duplicated"
    anchor = [f.getpixel((16, 31)) for f in frames]
    assert all(a[3] == 255 for a in anchor), anchor
    # Confirm Aseprite is an 8-frame 32-bit file with the expected grid.
    ase = (OUT / "aseprite/05_lumiere_spring.aseprite").read_bytes()
    size, magic, frame_count, width, height, depth, flags, speed = struct.unpack_from("<IHHHHHIH", ase, 0)
    assert size == len(ase) and magic == 0xA5E0
    assert (frame_count, width, height, depth) == (8, 32, 32, 32)
    assert struct.unpack_from("<hhHH", ase, 36) == (0, 0, 8, 8)
    # Tiled uses the same ground cell and exposes the Halcyon-style layer order.
    tm = json.loads((OUT / "tiled/luminous_spring_pmdo.tmj").read_text(encoding="utf-8"))
    assert (tm["tilewidth"], tm["tileheight"]) == (8, 8)
    assert [l["name"] for l in tm["layers"][:8]] == manifest["reference_observed"]["layer_order"]
    assert tm["width"] == tm["height"] == 64
    assert len(tm["tilesets"]) == 11
    # Every file the manifest advertises exists.
    for value in manifest["files"].values():
        assert (OUT / value).exists(), value
    print("PASS")
    print("  8 px PMDO grid;", len(names), "Halcyon-style tile sheets:", counts)
    print("  8 distinct light frames; Aseprite 8 frames; Tiled 64x64; .rsground present")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL:", exc)
        sys.exit(1)
