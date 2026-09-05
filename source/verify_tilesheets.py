"""Vérifie les pixels, grilles, raccords et formats du kit modulaire."""
from pathlib import Path
from PIL import Image
from scipy.ndimage import label
import hashlib
import json
import struct
import zlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "tilesheets"


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


def tiled(path):
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
    assert len(tm["layers"]) == 6
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
                assert 0 <= x <= composite.width - im.width and 0 <= y <= composite.height - im.height
                composite.alpha_composite(im, (x, y))
    assert not ids or tm["nextobjectid"] > max(ids)
    return composite


def verify():
    m = json.loads((KIT / "kit.json").read_text())
    source = json.loads((ROOT / "source/tilesheets/provenance.json").read_text())
    for path, expected in source["salles_preservees_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, f"Salle antérieure modifiée : {path}"
    assert m["grille_px"] == 32 and len(m["objets"]) == 20 and len(m["modules"]) == 9
    assert len({o["id"] for o in m["objets"]}) == 20
    assert m["spirales"]["motifs"] == 16
    report = {"grille": 32, "objets": 20, "motifs_spirales": 16, "salles_existantes_intactes": True, "modules": []}
    for mode in m["palettes"]:
        sheet = np.array(image(KIT / "parquet" / f"parquet_{mode}.png"))
        assert sheet.shape == (128, 256, 4) and (sheet[:, :, 3] == 255).all()
        horizontal = [sheet[i // 8 * 32:i // 8 * 32 + 32, i % 8 * 32:i % 8 * 32 + 32] for i in range(16)]
        vertical = [sheet[i // 8 * 32:i // 8 * 32 + 32, i % 8 * 32:i % 8 * 32 + 32] for i in range(16, 32)]
        for a in horizontal:
            for b in horizontal:
                assert np.array_equal(a[:, -1], b[:, 0]), "Raccord latéral de parquet"
                assert np.array_equal(a[0], b[0]) and np.array_equal(a[-1], b[-1]), "Phase des joints"
        for a in vertical:
            for b in vertical:
                assert np.array_equal(a[-1], b[0]), "Raccord longitudinal du parquet vertical"
        spirals = image(KIT / "spirales" / f"spirales_{mode}.png")
        a = np.array(spirals)
        assert spirals.size == (256, 256) and 0 < a[:, :, 3].max() < 255
        assert np.count_nonzero(a[:, :, 3]) < 256 * 256 * .2
        for i in range(16):
            individual = image(KIT / "spirales/individuelles" / f"spirale_{i + 1:02d}_{mode}.png")
            sx, sy = i % 4 * 64, i // 4 * 64
            same(individual, spirals.crop((sx, sy, sx + 64, sy + 64)), "Motif mal rangé")
        obj_atlas = image(KIT / "objets" / f"objets_{mode}.png")
        obj_shadow = image(KIT / "objets" / f"ombres_{mode}.png")
        assert obj_atlas.size == obj_shadow.size == (384, 480)
        for obj in m["objets"]:
            im = image(KIT / obj["fichiers"][mode]["png"])
            shadow = image(KIT / obj["fichiers"][mode]["ombre"])
            assert list(im.size) == obj["taille"] and im.size == shadow.size
            assert im.width % 8 == im.height % 8 == 0
            pixels = np.array(im)
            assert set(np.unique(pixels[:, :, 3])) <= {0, 255} and (pixels[:, :, 3] == 255).any()
            r, g, b = [pixels[:, :, k].astype(int) for k in range(3)]
            assert not ((r > 220) & (b > 220) & (g < 50) & (pixels[:, :, 3] > 0)).any(), "Fond magenta résiduel"
            x, y, w, h = obj["rect_atlas"]
            tile = obj_atlas.crop((x, y, x + w, y + h))
            target = Image.new("RGBA", (96, 96))
            target.alpha_composite(im, (48 - obj["pivot"][0], 88 - obj["pivot"][1]))
            same(tile, target, "Objet coupé ou décalé dans la planche")
        composed = obj_shadow.copy()
        composed.alpha_composite(obj_atlas)
        aseprite(KIT / "objets" / f"objets_{mode}.aseprite", 2, composed)
        aseprite(KIT / "parquet" / f"parquet_et_spirales_{mode}.aseprite", 2)
    for module in m["modules"]:
        w, h = module["dimensions"]
        path = KIT / "modules" / module["id"]
        floor = np.array(Image.open(path / "sol_praticable.png")) > 0
        assert floor.shape == (h, w) and floor.any()
        components, count = label(floor)
        assert count == 1, f"Sol déconnecté : {module['id']}"
        for p in module["acces"]:
            direction = p["direction"]
            strip = {"N": floor[0], "S": floor[-1], "E": floor[:, -1], "O": floor[:, 0]}[direction]
            pixels = np.flatnonzero(strip)
            assert len(pixels) == p["largeur_px"] == 96 and (np.diff(pixels) == 1).all()
            expected = (pixels[0] + pixels[-1] + 1) / 2
            assert p["ancrage_px"][0 if direction in ["N", "S"] else 1] == expected
        alphas = []
        for mode, files in module["fichiers"].items():
            target = image(KIT / files["png"])
            assert target.size == (w, h)
            composite = Image.new("RGBA", (w, h))
            for file in files["calques"]:
                layer = image(KIT / file)
                assert layer.size == (w, h)
                composite.alpha_composite(layer)
            same(composite, target, "Recomposition PNG des calques")
            same(tiled(KIT / files["tiled"]), target, "Recomposition Tiled")
            aseprite(KIT / files["aseprite"], 6, target)
            wall = np.array(image(KIT / files["calques"][1]))[:, :, 3] > 0
            assert not wall[floor].any(), "Un mur empiète sur le plancher"
            for layer_index in [2, 3]:
                a = np.array(image(KIT / files["calques"][layer_index]))[:, :, 3] > 0
                assert not a[~floor].any(), "Ombre/spirale hors du plancher"
            if module["famille"] == "couloir":
                for i in [3, 4, 5]:
                    assert image(KIT / files["calques"][i]).getbbox() is None
            alphas.append(np.array(target)[:, :, 3] > 0)
        assert np.array_equal(*alphas)
        report["modules"].append({"id": module["id"], "sol_connecte": True, "acces_px": 96,
                                   "PNG_Aseprite_Tiled": "identiques", "calques": 6, "jour_nuit": True})
    # Exemple réel de raccord à même échelle, sans redimensionnement :
    # couloir H (axe y=80) -> palier est-ouest (axe y=144), décalage de 64 px.
    for mode in m["palettes"]:
        a = np.array(image(KIT / "modules/couloir_horizontal" / f"{mode}.png"))
        b = np.array(image(KIT / "modules/palier_baies" / f"{mode}.png"))
        assert np.array_equal(a[:, -1], b[64:224, 0]), "Joint couloir / palier"
    report["raccord_couloir_palier_pixel_exact"] = True
    report["parquet_bords_communs"] = True
    report["spirales_sans_parquet"] = True
    report["limite"] = "Formats relus par code, sans ouverture dans l'interface Aseprite/Tiled. Les modules ne sont pas intégrés à un moteur."
    (KIT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS : 20 objets, 32 parquets, 16 spirales transparentes ; 18 modules PNG/Aseprite/Tiled identiques ; raccords et salles initiales préservés.")


if __name__ == "__main__":
    verify()
