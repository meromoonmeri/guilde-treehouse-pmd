#!/usr/bin/env python3
"""Contrôle indépendant des layouts extérieurs, PNG, Aseprite et Tiled."""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references_exterieures"
PREVIEW = ROOT / "apercu_references_exterieures.html"


def image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        assert opened.mode == "RGBA", f"Calque non RGBA : {path} ({opened.mode})"
        return opened.copy()


def equal(left: Image.Image, right: Image.Image, message: str) -> None:
    assert np.array_equal(np.asarray(left), np.asarray(right)), message


def recompose(layers: list[Image.Image], size: tuple[int, int], start: int = 0) -> Image.Image:
    rendered = Image.new("RGBA", size)
    for layer in layers[start:]:
        rendered.alpha_composite(layer)
    return rendered


def verify_aseprite(path: Path, layers: list[Image.Image], size: tuple[int, int]) -> None:
    raw = path.read_bytes()
    header = struct.unpack_from("<IHHHHHIH", raw)
    assert header == (len(raw), 0xA5E0, 1, *size, 32, 1, 100), f"Entête Aseprite invalide : {path}"
    assert struct.unpack_from("<hhHH", raw, 36) == (0, 0, 8, 8)
    frame_size, magic, chunks, duration = struct.unpack_from("<IHHH", raw, 128)
    assert magic == 0xF1FA and duration == 100 and frame_size + 128 == len(raw)
    pos, decoded, definitions = 144, {}, 0
    for _ in range(chunks):
        length, kind = struct.unpack_from("<IH", raw, pos)
        assert length >= 6 and pos + length <= len(raw)
        data = raw[pos + 6:pos + length]
        if kind == 0x2004:
            definitions += 1
        elif kind == 0x2005:
            index, x, y, opacity, kind_cel, z = struct.unpack_from("<HhhBHh", data)
            assert opacity == 255 and kind_cel == 2 and z == 0 and index not in decoded
            width, height = struct.unpack_from("<HH", data, 16)
            crop = Image.frombytes("RGBA", (width, height), zlib.decompress(data[20:]))
            decoded[index] = (x, y, crop)
        pos += length
    assert pos == len(raw) and definitions == len(layers) and set(decoded) == set(range(len(layers)))
    for index, expected in enumerate(layers):
        x, y, actual = decoded[index]
        box = expected.getbbox()
        expected_crop = expected.crop(box) if box else Image.new("RGBA", (1, 1))
        assert (x, y) == (box[:2] if box else (0, 0))
        equal(actual, expected_crop, f"Cel Aseprite différent : {path}, calque {index}")


def verify_tiled(path: Path, root: Path, mode: str, layer_ids: list[str], size: tuple[int, int]) -> None:
    tiled = json.loads(path.read_text(encoding="utf-8"))
    assert tiled["type"] == "map" and tiled["orientation"] == "orthogonal"
    assert (tiled["tilewidth"], tiled["tileheight"]) == (8, 8)
    assert (tiled["width"] * 8, tiled["height"] * 8) == size
    assert len(tiled["layers"]) == len(layer_ids) and tiled["tilesets"] == []
    for expected_id, layer in zip(layer_ids, tiled["layers"]):
        assert layer["type"] == "imagelayer" and layer["visible"] is True
        expected = (root / "calques" / mode / f"{expected_id}.png").resolve()
        actual = (path.parent / layer["image"]).resolve()
        assert actual == expected and actual.is_file(), f"Lien Tiled incorrect : {path}"


def verify() -> dict:
    manifest_path = OUT / "kit.json"
    assert manifest_path.is_file(), "Kit absent : lancer source/rebuild_references_exterieures.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["animation"] is False and manifest["grille_px"] == 8
    assert len(manifest["scenes"]) == 3
    report = {"scenes": [], "animation": False, "inspection_artistique_automatisee": False}
    for scene in manifest["scenes"]:
        root = OUT / scene["id"]
        size = tuple(scene["dimensions"])
        assert all(value % 8 == 0 for value in size)
        layer_ids = [layer["id"] for layer in scene["calques"]]
        assert len(layer_ids) == 5 and len(set(layer_ids)) == 5
        scene_report = {"id": scene["id"], "dimensions": list(size), "calques": len(layer_ids), "ambiances": []}
        day = None
        for mode in ("jour", "nuit"):
            files = scene["fichiers"][mode]
            native = image((root / files["native"]).resolve())
            assert native.size == size and native.getchannel("A").getextrema() == (255, 255)
            layers = [image(root / files["calques"][layer_id]) for layer_id in layer_ids]
            assert all(layer.size == size for layer in layers)
            coverage = np.add.reduce([(np.asarray(layer)[:, :, 3] > 0).astype(np.uint8) for layer in layers])
            assert coverage.min() == coverage.max() == 1, f"Plans non disjoints ou troués : {scene['id']}/{mode}"
            composition = recompose(layers, size)
            equal(composition, native, f"Composition altérée : {scene['id']}/{mode}")
            equal(composition, image(root / files["composition"]), f"Export PNG différent : {scene['id']}/{mode}")
            base = recompose(layers, size, start=2)
            equal(base, image(root / files["base"]), f"Base différente : {scene['id']}/{mode}")
            magenta = Image.new("RGBA", size, (255, 0, 255, 255))
            magenta.alpha_composite(base)
            equal(magenta, image(root / files["magenta"]), f"Magenta différent : {scene['id']}/{mode}")
            verify_aseprite(root / files["aseprite"], layers, size)
            verify_tiled(root / files["tiled"], root, mode, layer_ids, size)
            if mode == "jour":
                day = np.asarray(composition)
            else:
                assert day is not None and not np.array_equal(day, np.asarray(composition)), "Jour et nuit identiques"
            scene_report["ambiances"].append({
                "id": mode, "recomposition_png": "identique_a_la_native", "aseprite": "1_image_5_calques",
                "tiled": "5_image_layers", "base_magenta": "identique", "plans_disjoints": True,
            })
            print(f"PASS {scene['id']} {mode} — PNG, Aseprite statique et Tiled cohérents")
        report["scenes"].append(scene_report)
    preview = PREVIEW.read_text(encoding="utf-8")
    assert "data:image/webp;base64," in preview
    assert "http://" not in preview and "https://" not in preview
    report["apercu_autonome"] = True
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS : trois layouts, jour/nuit, cinq calques, PNG/Aseprite/Tiled et aperçu autonome.")
    return report


if __name__ == "__main__":
    verify()
