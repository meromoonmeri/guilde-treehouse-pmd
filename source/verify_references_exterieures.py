#!/usr/bin/env python3
"""Contrôle des layouts extérieurs générés, multicouches et animés.

Les contrôles portent sur l'identité stricte de l'image 0 avec la native, la
périodicité des deux opérations visuelles et les vraies cels/atlases animées.
Ils ne prétendent pas automatiser un jugement artistique.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

from exterior_reference_animation import AnimatedLayer, compose

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references_exterieures"
PREVIEW = ROOT / "apercu_references_exterieures.html"
FRAMES, DURATION = 24, 250


def image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        assert opened.mode == "RGBA", f"Image non RGBA : {path} ({opened.mode})"
        return opened.copy()


def equal(left: Image.Image, right: Image.Image, message: str) -> None:
    assert np.array_equal(np.asarray(left), np.asarray(right)), message


def crop_for_cel(frame: Image.Image) -> tuple[tuple[int, int], Image.Image]:
    box = frame.getbbox()
    return (box[:2] if box else (0, 0), frame.crop(box) if box else Image.new("RGBA", (1, 1)))


def parse_aseprite(path: Path, expected_size: tuple[int, int], layer_count: int, periods: list[int], operators: list[AnimatedLayer]) -> None:
    """Contrôle la structure Aseprite et les cels propres/chaînées de la boucle."""
    raw = path.read_bytes()
    total, magic, frames, width, height, depth, colors, duration = struct.unpack_from("<IHHHHHIH", raw)
    assert (total, magic, frames, width, height, depth, colors, duration) == (len(raw), 0xA5E0, FRAMES, *expected_size, 32, 1, DURATION), f"Entête Aseprite invalide : {path}"
    assert struct.unpack_from("<hhHH", raw, 36) == (0, 0, 8, 8)
    pos, layer_defs, tag_count = 128, 0, 0
    frame_cels: list[dict[int, tuple]] = []
    for frame in range(FRAMES):
        frame_bytes, frame_magic, chunk_count, frame_duration = struct.unpack_from("<IHHH", raw, pos)
        assert frame_magic == 0xF1FA and frame_duration == DURATION and frame_bytes >= 16
        end = pos + frame_bytes
        pos += 16
        cels: dict[int, tuple] = {}
        seen_chunks = 0
        while pos < end:
            length, kind = struct.unpack_from("<IH", raw, pos)
            assert length >= 6 and pos + length <= end
            data = raw[pos + 6:pos + length]
            if kind == 0x2004:
                layer_defs += 1
            elif kind == 0x2018:
                tag_count += 1
            elif kind == 0x2005:
                index, x, y, opacity, cel_kind, z = struct.unpack_from("<HhhBHh", data)
                assert 0 <= index < layer_count and opacity == 255 and z == 0 and index not in cels
                if cel_kind == 2:
                    w, h = struct.unpack_from("<HH", data, 16)
                    pixels = zlib.decompress(data[20:])
                    assert len(pixels) == w * h * 4
                    cels[index] = ("raw", x, y, Image.frombytes("RGBA", (w, h), pixels))
                elif cel_kind == 1:
                    assert len(data) >= 18
                    cels[index] = ("linked", x, y, struct.unpack_from("<H", data, 16)[0])
                else:
                    raise AssertionError(f"Type de cel Aseprite inattendu {cel_kind}")
            pos += length
            seen_chunks += 1
        assert pos == end and seen_chunks == chunk_count
        assert set(cels) == set(range(layer_count)), f"Cels manquantes à l'image {frame}: {path}"
        frame_cels.append(cels)
    assert pos == len(raw) and layer_defs == layer_count and tag_count == 1, f"Structure Aseprite incomplète : {path}"
    # Toute phase dynamique est écrite réellement et toutes les images fixes
    # suivantes sont des cels liées, comme dans le workflow extérieur audité.
    for frame, cels in enumerate(frame_cels):
        for index, op in enumerate(operators):
            kind, x, y, value = cels[index]
            if frame < periods[index]:
                assert kind == "raw", f"Cel dynamique absente: {path}, image {frame}, calque {index}"
                expected_xy, expected_crop = crop_for_cel(op.at(frame))
                assert (x, y) == expected_xy
                equal(value, expected_crop, f"Pixels de cel différents: {path}, image {frame}, calque {index}")
            else:
                assert kind == "linked" and value == frame % periods[index], f"Cel non liée: {path}, image {frame}, calque {index}"
    # Les opérations sont cycliques et ont un mouvement perceptible.
    for index, op in enumerate(operators):
        for phase in (0, 1, 7, 23):
            equal(op.at(phase), op.at(phase + periods[index]), f"Période invalide pour le calque {index}: {path}")
        if periods[index] > 1:
            assert not np.array_equal(np.asarray(op.at(0)), np.asarray(op.at(periods[index] // 2))), f"Animation immobile: {path}, calque {index}"


def verify_tiled(path: Path, root: Path, mode: str, definitions: list[dict], specs: dict, size: tuple[int, int]) -> None:
    tiled = json.loads(path.read_text(encoding="utf-8"))
    assert tiled["type"] == "map" and tiled["orientation"] == "orthogonal"
    assert (tiled["tilewidth"], tiled["tileheight"]) == (8, 8)
    assert (tiled["width"] * 8, tiled["height"] * 8) == size
    assert len(tiled["layers"]) == len(definitions) + 1  # dernier groupe de repères
    animated = [definition for definition in definitions if definition["id"] in specs]
    assert len(tiled["tilesets"]) == len(animated)
    by_gid = {tileset["firstgid"]: tileset for tileset in tiled["tilesets"]}
    for index, definition in enumerate(definitions):
        layer = tiled["layers"][index]
        assert layer["name"] == definition["nom"] and layer["visible"] is True
        spec = specs.get(definition["id"])
        if not spec:
            assert layer["type"] == "imagelayer"
            expected = (root / "calques" / mode / f"{definition['id']}.png").resolve()
            assert (path.parent / layer["image"]).resolve() == expected and expected.is_file()
            continue
        assert layer["type"] == "objectgroup" and len(layer["objects"]) == 1
        obj = layer["objects"][0]
        tileset = by_gid[obj["gid"]]
        assert tileset["tilecount"] == spec["period"] == FRAMES
        assert tileset["tiles"][0]["id"] == 0
        sequence = tileset["tiles"][0]["animation"]
        assert [(entry["tileid"], entry["duration"]) for entry in sequence] == [(i, DURATION) for i in range(FRAMES)]
        atlas = (path.parent / tileset["image"]).resolve()
        assert atlas.is_file() and atlas == (root / "animations" / f"{spec['prefix']}_{mode}.png").resolve()
        with Image.open(atlas) as atlas_image:
            assert atlas_image.mode == "RGBA" and atlas_image.width == size[0] * tileset["columns"]
            assert atlas_image.height == tileset["tileheight"] * ((FRAMES + tileset["columns"] - 1) // tileset["columns"])
    marker_layer = tiled["layers"][-1]
    assert marker_layer["type"] == "objectgroup" and marker_layer["visible"] is False


def verify() -> dict:
    manifest_path = OUT / "kit.json"
    assert manifest_path.is_file(), "Kit absent : lancer source/rebuild_references_exterieures.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    animation = manifest["animation"]
    assert (animation["frames"], animation["duree_image_ms"], animation["duree_boucle_ms"]) == (FRAMES, DURATION, FRAMES * DURATION)
    assert manifest["grille_px"] == 8 and len(manifest["scenes"]) == 3
    report = {"scenes": [], "animation": True, "inspection_artistique_automatisee": False,
              "contrat": "image_0=native ; nuages et étoiles périodiques ; Aseprite et Tiled animés"}
    for scene in manifest["scenes"]:
        root, size = OUT / scene["id"], tuple(scene["dimensions"])
        assert all(value % 8 == 0 for value in size)
        definitions = scene["calques"]
        assert len(definitions) >= 6 and len({layer["id"] for layer in definitions}) == len(definitions)
        assert [layer["id"] for layer in definitions[:3]] == ["00_ciel", "01_astres", "02_nuages"]
        scene_report = {"id": scene["id"], "dimensions": list(size), "calques": len(definitions), "ambiances": []}
        day = None
        for mode in ("jour", "nuit"):
            files = scene["fichiers"][mode]
            native = image((root / files["native"]).resolve())
            assert native.size == size and native.getchannel("A").getextrema() == (255, 255)
            layers = [image(root / files["calques"][definition["id"]]) for definition in definitions]
            assert all(layer.size == size for layer in layers)
            specs = files["operations"]
            if layers[2].getbbox():
                assert specs["02_nuages"]["kind"] == "scroll" and specs["02_nuages"]["period"] == FRAMES
            else:
                assert "02_nuages" not in specs, "Un plan nuages transparent ne doit pas créer un atlas vide"
            if mode == "nuit":
                assert specs["01_astres"]["kind"] == "stars" and specs["01_astres"]["moon_steady"] is True
                assert (root / specs["01_astres"]["groups"]).is_file()
            else:
                assert "01_astres" not in specs
            operators = [AnimatedLayer(layer, specs.get(definition["id"]), root) for definition, layer in zip(definitions, layers)]
            initial = compose(operators, size, 0)
            equal(initial, native, f"Image 0 différente de la native : {scene['id']}/{mode}")
            equal(initial, image(root / files["composition"]), f"Composition PNG différente : {scene['id']}/{mode}")
            base = compose(operators, size, 0, scene["base_start"])
            equal(base, image(root / files["base"]), f"Base différente : {scene['id']}/{mode}")
            magenta = Image.new("RGBA", size, (255, 0, 255, 255)); magenta.alpha_composite(base)
            equal(magenta, image(root / files["magenta"]), f"Base magenta différente : {scene['id']}/{mode}")
            periods = [operator.period for operator in operators]
            parse_aseprite(root / files["aseprite"], size, len(layers), periods, operators)
            verify_tiled(root / files["tiled"], root, mode, definitions, specs, size)
            if mode == "jour":
                day = np.asarray(initial)
            else:
                assert day is not None and not np.array_equal(day, np.asarray(initial)), "Jour et nuit identiques"
            scene_report["ambiances"].append({"id": mode, "image_0": "identique_a_la_native",
                "aseprite": f"{FRAMES}_images_et_cels_animees", "tiled": f"{len([x for x in specs if x])}_atlas_animes",
                "base_magenta": "identique", "animation": "nuages" + ("_et_etoiles" if mode == "nuit" else "")})
            print(f"PASS {scene['id']} {mode} — image 0, animation PNG/Aseprite/Tiled cohérentes")
        report["scenes"].append(scene_report)
    preview = PREVIEW.read_text(encoding="utf-8")
    assert "data:image/webp;base64," in preview and "24 phases de 250 ms" in preview
    # L'aperçu applique la même LUT de groupes que les cels, avec la valeur 255
    # du groupe 0 qui maintient la lune immobile ; pas un fondu global.
    assert "starGroups" in preview and "levels[groups[g]]" in preview and "globalAlpha" not in preview
    assert "http://" not in preview and "https://" not in preview
    report["apercu_autonome"] = True
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS : 3 layouts générés, jour/nuit, calques sémantiques et exports animés.")
    return report


if __name__ == "__main__":
    verify()
