#!/usr/bin/env python3
"""Vérifie le contrat du paysage original généré, fond magenta et boucles."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

from build import (CELL_PX, CLOUD_PERIOD, FRAMES, LAYERS, MAGENTA, MODE, OUT,
                   PMDO_TILE_PX, SEA_PERIOD, SIZE, VIEWPORT_ORIGIN, VIEWPORT_SIZE,
                   rgba_from_magenta)

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / "apercu_exterieur_original.html"


def read(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        return opened.copy()


def same(left: Image.Image, right: Image.Image, message: str) -> None:
    assert np.array_equal(np.asarray(left), np.asarray(right)), message


def verify_aseprite(path: Path) -> None:
    raw = path.read_bytes()
    total, magic, frames, width, height, depth, colors, duration = struct.unpack_from("<IHHHHHIH", raw)
    assert (total, magic, frames, width, height, depth, colors, duration) == (len(raw), 0xA5E0, FRAMES, *SIZE, 32, 1, 250)
    periods = [1, CLOUD_PERIOD, SEA_PERIOD, 1, 1]
    pos, definitions, tags = 128, 0, 0
    for frame in range(FRAMES):
        frame_bytes, frame_magic, chunk_count, frame_duration = struct.unpack_from("<IHHH", raw, pos)
        assert frame_magic == 0xF1FA and frame_duration == 250 and frame_bytes >= 16
        end, cels, chunks = pos + frame_bytes, {}, 0
        pos += 16
        while pos < end:
            length, kind = struct.unpack_from("<IH", raw, pos)
            assert length >= 6 and pos + length <= end
            data = raw[pos + 6:pos + length]
            if kind == 0x2004:
                definitions += 1
            elif kind == 0x2018:
                tags += 1
            elif kind == 0x2005:
                index, _x, _y, opacity, cel_kind, _z = struct.unpack_from("<HhhBHh", data)
                assert opacity == 255 and 0 <= index < len(LAYERS)
                assert index not in cels
                if frame < periods[index]:
                    assert cel_kind == 2, f"Cel source absente à frame {frame}, layer {index}"
                else:
                    assert cel_kind == 1 and struct.unpack_from("<H", data, 16)[0] == frame % periods[index]
                cels[index] = cel_kind
            pos += length
            chunks += 1
        assert pos == end and chunks == chunk_count and set(cels) == set(range(len(LAYERS)))
    assert pos == len(raw) and definitions == len(LAYERS) and tags == 1


def verify() -> None:
    manifest = json.loads((OUT / "kit.json").read_text(encoding="utf-8"))
    assert manifest["dimensions"] == list(SIZE) and manifest["grille_px"] == 8
    assert manifest["fond_chroma_key"] == "#FF00FF"
    assert manifest["animation"]["frames"] == FRAMES
    assert len(manifest["calques"]) == len(LAYERS) == 5
    files = manifest["fichiers"][MODE]
    keyed, rgba = [], []
    for definition in manifest["calques"]:
        layer_id = definition["id"]
        magenta = read(OUT / files["calques_magentas"][layer_id])
        assert magenta.mode == "RGB" and magenta.size == SIZE
        array = np.asarray(magenta)
        if layer_id != "00_ciel":
            assert np.any(np.all(array == MAGENTA, axis=2)), f"Fond magenta absent : {layer_id}"
        # Le fichier final est explicitement magenta ; l'alpha n'existe que
        # pour les exports d'édition/animation, par chroma-key déterministe.
        keyed.append(magenta)
        transparent = rgba_from_magenta(magenta) if layer_id != "00_ciel" else magenta.convert("RGBA")
        rgba_file = read(OUT / files["calques_rgba"][layer_id]).convert("RGBA")
        same(transparent, rgba_file, f"Chroma-key différent : {layer_id}")
        rgba.append(rgba_file)
    composition = Image.new("RGBA", SIZE)
    for layer in rgba:
        composition.alpha_composite(layer)
    same(composition, read(OUT / files["composition"]).convert("RGBA"), "Composition image 0 différente")

    specs = files["operations"]
    cloud_spec, sea_spec = specs["01_nuages_wrap"], specs["02_mer_palette"]
    assert cloud_spec["kind"] == "scroll" and cloud_spec["period"] == CLOUD_PERIOD and cloud_spec["wrap_horizontal_parfait"]
    assert sea_spec["kind"] == "frames" and sea_spec["period"] == SEA_PERIOD and sea_spec["palette_only"]
    from animation import AnimatedLayer
    cloud, sea = AnimatedLayer(rgba[1], cloud_spec, OUT), AnimatedLayer(rgba[2], sea_spec, OUT)
    same(cloud.at(0), cloud.at(CLOUD_PERIOD), "Le wrap nuages ne revient pas exactement à la frame 0")
    assert not np.array_equal(np.asarray(cloud.at(0)), np.asarray(cloud.at(1))), "Nuages immobiles"
    same(sea.at(0).getchannel("A"), sea.at(12).getchannel("A"), "Le cycle de mer a déplacé sa géométrie")
    assert not np.array_equal(np.asarray(sea.at(0)), np.asarray(sea.at(12))), "Palette de mer immobile"

    tiled = json.loads((OUT / files["tiled"]).read_text(encoding="utf-8"))
    assert (tiled["width"] * CELL_PX, tiled["height"] * CELL_PX) == SIZE
    assert len(tiled["layers"]) == 6 and len(tiled["tilesets"]) == 2
    properties = {item["name"]: item["value"] for item in tiled["properties"]}
    assert properties == {"cellule_edition_px": CELL_PX, "tuile_pmdo_px": PMDO_TILE_PX,
                          "viewport_waterfallvillagecapital_px": "320x240",
                          "viewport_origine_px": f"{VIEWPORT_ORIGIN[0]},{VIEWPORT_ORIGIN[1]}"}
    periods = sorted(tileset["tilecount"] for tileset in tiled["tilesets"])
    assert periods == [SEA_PERIOD, CLOUD_PERIOD]
    for tileset in tiled["tilesets"]:
        sequence = tileset["tiles"][0]["animation"]
        assert len(sequence) == tileset["tilecount"] and all(entry["duration"] == 250 for entry in sequence)
    view = json.loads((OUT / files["contrat_map_viewport"]).read_text(encoding="utf-8"))
    assert view["map_px"] == list(SIZE) and view["cellule_px"] == CELL_PX
    assert view["viewport_px"] == list(VIEWPORT_SIZE) and view["origine_px"] == list(VIEWPORT_ORIGIN)
    assert all(value % CELL_PX == 0 for value in (*SIZE, *VIEWPORT_SIZE, *VIEWPORT_ORIGIN))
    assert read(OUT / files["viewport"]).size == VIEWPORT_SIZE
    verify_aseprite(OUT / files["aseprite"])

    html = PREVIEW.read_text(encoding="utf-8")
    for token in ("#FF00FF", "Grille 8 px : visible", "x+=8", "y+=8", f"frame%{CLOUD_PERIOD}", "frame%24", "Viewport WaterfallVillageCapital"):
        assert token in html, f"Contrat aperçu absent : {token}"
    assert "http://" not in html and "https://" not in html
    (OUT / "controle_qualite.json").write_text(json.dumps({
        "resultat": "PASS", "layers": 5, "fond": "#FF00FF", "grille_px": 8,
        "nuages": {"period_px": CLOUD_PERIOD, "wrap": "bit_identique"},
        "mer": {"frames_palette": SEA_PERIOD, "geometrie": "inchangee"},
        "map_waterfallvillagecapital": {"cellule_px": CELL_PX, "tuile_pmdo_px": PMDO_TILE_PX,
                                         "viewport_px": list(VIEWPORT_SIZE), "origine_px": list(VIEWPORT_ORIGIN)},
        "aseprite_frames": FRAMES,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS paysage original — 5 layers IA, fond magenta, mer {SEA_PERIOD} palettes, nuages wrap {CLOUD_PERIOD} px.")


if __name__ == "__main__":
    verify()
