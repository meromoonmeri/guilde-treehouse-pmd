"""Relecture indépendante des exports Aseprite/Tiled de tilesheets, grille 32 px."""
from PIL import Image
import json
import struct
import zlib
import numpy as np

def image(path):
    return Image.open(path).convert("RGBA")


def same(a, b, message):
    assert a.size == b.size and np.array_equal(np.array(a), np.array(b)), message


def aseprite(path, expected_layers, target=None):
    data = path.read_bytes()
    length, magic, frames, w, h, depth = struct.unpack_from("<IHHHHH", data)
    assert (length, magic, frames, depth) == (len(data), 0xA5E0, 1, 32)
    assert struct.unpack_from("<HH", data, 40) == (32, 32)
    frame_size, frame_magic, chunks = struct.unpack_from("<IHH", data, 128)
    assert frame_magic == 0xF1FA and frame_size + 128 == len(data)
    pos, layer_count = 144, 0
    cells = {}
    for _ in range(chunks):
        size, kind = struct.unpack_from("<IH", data, pos)
        chunk = data[pos + 6:pos + size]
        if kind == 0x2004:
            layer_count += 1
        elif kind == 0x2005:
            i, x, y, opacity, typ = struct.unpack_from("<HhhBH", chunk)
            assert typ == 2 and opacity == 255
            cw, ch = struct.unpack_from("<HH", chunk, 16)
            cells[i] = (x, y, Image.frombytes("RGBA", (cw, ch), zlib.decompress(chunk[20:])))
        pos += size
    assert pos == len(data) and layer_count == len(cells) == expected_layers
    composite = Image.new("RGBA", (w, h))
    for _, (x, y, im) in sorted(cells.items()):
        composite.alpha_composite(im, (x, y))
    if target is not None:
        same(composite, target, f"Aseprite différent : {path}")
    return composite


def tiled(path, expected_layers=13):
    tm = json.loads(path.read_text())
    assert tm["tilewidth"] == tm["tileheight"] == 32
    sets = []
    for ref in tm["tilesets"]:
        ts_path = (path.parent / ref["source"]).resolve()
        assert ts_path.is_file()
        ts = json.loads(ts_path.read_text())
        if "image" in ts:
            im = image((ts_path.parent / ts["image"]).resolve())
            assert im.size == (ts["imagewidth"], ts["imageheight"])
            assert ts["tilecount"] == im.width // 32 * (im.height // 32)
            tiles = [im.crop((i % ts["columns"] * 32, i // ts["columns"] * 32,
                              i % ts["columns"] * 32 + 32, i // ts["columns"] * 32 + 32)) for i in range(ts["tilecount"])]
        else:
            tiles = [image((ts_path.parent / t["image"]).resolve()) for t in ts["tiles"]]
            assert len(tiles) == ts["tilecount"]
        sets.append((ref["firstgid"], tiles))
    assert all(sets[i][0] + len(sets[i][1]) <= sets[i + 1][0] for i in range(len(sets) - 1))

    def tile(gid):
        first, tiles = max((s for s in sets if s[0] <= gid), key=lambda s: s[0])
        index = gid - first
        assert 0 <= index < len(tiles)
        return tiles[index]

    composite = Image.new("RGBA", (tm["width"] * 32, tm["height"] * 32))
    assert len(tm["layers"]) == expected_layers
    ids = set()
    for layer in tm["layers"]:
        assert layer.get("opacity", 1) == 1 and layer.get("visible", True)
        if layer["type"] == "tilelayer":
            assert len(layer["data"]) == tm["width"] * tm["height"]
            for i, gid in enumerate(layer["data"]):
                if gid:
                    composite.alpha_composite(tile(gid), (i % tm["width"] * 32, i // tm["width"] * 32))
        else:
            assert layer["type"] == "objectgroup"
            for obj in layer["objects"]:
                assert obj["id"] not in ids
                ids.add(obj["id"])
                im = tile(obj["gid"])
                assert im.size == (obj["width"], obj["height"]) and obj["rotation"] == 0
                x, y = int(obj["x"]), int(obj["y"] - obj["height"])
                assert -im.width < x < composite.width and -im.height < y < composite.height
                composite.alpha_composite(im, (x, y))
    assert not ids or tm["nextobjectid"] > max(ids)
    return composite
