#!/usr/bin/env python3
"""Découpe les nouveaux layouts de référence en plans PNG fixes et cohérents.

La séparation est faite *après* avoir fixé la composition de référence : chaque
pixel opaque de la native est affecté à un et un seul plan. Ainsi la
recomposition est strictement identique à la native (aucun collage au runtime,
aucune interpolation, aucun élément ajouté lors de l'export).
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import struct
import zlib
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
NATIVES = ROOT / "source" / "references_exterieures" / "natives"
OUT = ROOT / "references_exterieures"
PREVIEW = ROOT / "apercu_references_exterieures.html"

SCENES = (
    {
        "id": "cascades",
        "nom": "Sanctuaire des cascades",
        "dimensions": (592, 448),
        "natives": {"jour": "cascades_jour.png", "nuit": "cascades_nuit.png"},
        "description": "Layout du panneau de cascades : îlot suspendu, chutes d'eau, eau et végétation de rive.",
        "layers": (
            ("00_ciel_eau", "Ciel, horizon et nappe d'eau"),
            ("01_nuages_astres", "Nuages de jour / étoiles de nuit"),
            ("02_ilot_rocheux", "Îlot rocheux et relief central"),
            ("03_cascades", "Chutes et écume"),
            ("04_vegetation", "Roseaux, buissons et premier plan"),
        ),
    },
    {
        "id": "prairie_maritime",
        "nom": "Prairie maritime",
        "dimensions": (504, 504),
        "natives": {"jour": "prairie_maritime_jour.png", "nuit": "prairie_maritime_nuit.png"},
        "description": "Layout du GIF : prairie fleurie, sentier, reliefs latéraux et mer au nord.",
        "layers": (
            ("00_ciel_mer", "Ciel, horizon et mer"),
            ("01_nuages_astres", "Atmosphère et étoiles nocturnes"),
            ("02_prairie_chemin", "Prairie centrale et chemin"),
            ("03_reliefs", "Falaises, rochers et rebords"),
            ("04_vegetation_fleurs", "Fleurs, buissons et arbres"),
        ),
    },
    {
        "id": "cap_cotier",
        "nom": "Cap côtier",
        "dimensions": (960, 600),
        "natives": {"jour": "cap_cotier_jour.png", "nuit": "cap_cotier_nuit.png"},
        "description": "Layout de la falaise maritime : prairie, chemin, maison-courrier, falaise et océan.",
        "layers": (
            ("00_ciel_mer", "Ciel, horizon et mer"),
            ("01_nuages_astres", "Nuages de jour / lune et étoiles de nuit"),
            ("02_terrain_falaise", "Chemin, sol et paroi rocheuse"),
            ("03_maison", "Maison-courrier et abords immédiats"),
            ("04_vegetation", "Arbres, herbes, fleurs et liserés de prairie"),
        ),
    },
)


def as_rgba(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as opened:
        image = opened.convert("RGBA")
    assert image.size == size, f"Dimensions inattendues pour {path}: {image.size} / {size}"
    assert image.getchannel("A").getextrema() == (255, 255), f"Native non opaque : {path}"
    return image


def alpha_mask(points: list[tuple[int, int]], size: tuple[int, int]) -> np.ndarray:
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return np.asarray(mask, dtype=bool)


def green_pixels(rgb: np.ndarray) -> np.ndarray:
    r, g, b = (rgb[:, :, channel].astype(np.int16) for channel in range(3))
    # Inclut l'herbe sombre nocturne mais pas la mer cyan ni le ciel bleu.
    return (g > r + 7) & (g > b - 8) & (g > 35)


def low_saturation_light(rgb: np.ndarray, limit: int) -> np.ndarray:
    hi = rgb.max(axis=2).astype(np.int16)
    lo = rgb.min(axis=2).astype(np.int16)
    return (hi - lo < limit) & (hi > 130)


def partition(image: Image.Image, proposals: list[np.ndarray]) -> list[Image.Image]:
    """Rend des calques disjoints qui couvrent l'intégralité de la native."""
    source = np.asarray(image.convert("RGBA"))
    h, w = source.shape[:2]
    allocated = np.zeros((h, w), dtype=bool)
    masks: list[np.ndarray] = []
    for proposed in proposals:
        assert proposed.shape == (h, w)
        chosen = proposed & ~allocated
        masks.append(chosen)
        allocated |= chosen
    # Le premier plan est le fond : il reçoit tous les pixels non spécialisés.
    masks[0] |= ~allocated
    assert np.all(np.add.reduce([mask.astype(np.uint8) for mask in masks]) == 1), "Plans chevauchants"
    outputs: list[Image.Image] = []
    for mask in masks:
        pixels = np.zeros_like(source)
        pixels[mask] = source[mask]
        outputs.append(Image.fromarray(pixels, "RGBA"))
    rebuilt = Image.new("RGBA", image.size)
    for output in outputs:
        rebuilt.alpha_composite(output)
    assert np.array_equal(np.asarray(rebuilt), source), "La séparation a modifié la composition"
    return outputs


def cascade_layers(image: Image.Image, mode: str) -> list[Image.Image]:
    a = np.asarray(image)
    rgb = a[:, :, :3]
    h, w = a.shape[:2]
    yy, xx = np.indices((h, w))
    island_zone = alpha_mask([(round(w*.22), 48), (round(w*.68), 40), (round(w*.76), 150),
                              (round(w*.73), 286), (round(w*.56), 326), (round(w*.26), 285),
                              (round(w*.18), 150)], (w, h))
    # Colonnes et éclats d'eau, volontairement isolés du relief et de la nappe.
    blue_water = (rgb[:, :, 2].astype(np.int16) > rgb[:, :, 0].astype(np.int16) + 20) & (rgb[:, :, 1] > rgb[:, :, 0])
    waterfall_bands = (((xx > w*.27) & (xx < w*.40)) | ((xx > w*.45) & (xx < w*.57)) |
                       ((xx > w*.62) & (xx < w*.72))) & (yy > 46) & (yy < 405)
    waterfalls = waterfall_bands & blue_water
    foreground_area = (yy > 235) | (xx < w*.19) | (xx > w*.80)
    vegetation = green_pixels(rgb) & foreground_area & ~waterfalls
    pale = low_saturation_light(rgb, 62)
    # Les nuages et astres restent uniquement dans l'atmosphère, jamais sur l'îlot.
    atmosphere = (yy < 220) & ~island_zone & pale
    if mode == "nuit":
        atmosphere |= (yy < 145) & (rgb.max(axis=2) > 185) & ~island_zone
    island = island_zone & ~waterfalls & ~atmosphere & ~vegetation
    return partition(image, [np.zeros((h, w), dtype=bool), atmosphere, island, waterfalls, vegetation])


def prairie_maritime_layers(image: Image.Image, mode: str) -> list[Image.Image]:
    a = np.asarray(image)
    rgb = a[:, :, :3]
    h, w = a.shape[:2]
    yy, xx = np.indices((h, w))
    land = yy > 84
    # Les reliefs suivent les deux retours pierreux du layout fourni.
    relief_zone = (((xx < w*.29) | (xx > w*.70)) & (yy > 105) & (yy < h*.78)) | ((yy > h*.75) & ((xx < w*.20) | (xx > w*.79)))
    flowers = (rgb[:, :, 0].astype(np.int16) > rgb[:, :, 1].astype(np.int16) + 25) & (rgb[:, :, 0] > rgb[:, :, 2].astype(np.int16) + 15)
    vegetation = (green_pixels(rgb) | flowers) & land & ~relief_zone
    relief = relief_zone & ~green_pixels(rgb)
    terrain = land & ~vegetation & ~relief
    pale = low_saturation_light(rgb, 58)
    atmosphere = (yy < 125) & pale
    if mode == "nuit":
        atmosphere |= (yy < 105) & (rgb.max(axis=2) > 175)
    return partition(image, [np.zeros((h, w), dtype=bool), atmosphere, terrain, relief, vegetation])


def cap_layers(image: Image.Image, mode: str) -> list[Image.Image]:
    a = np.asarray(image)
    rgb = a[:, :, :3]
    h, w = a.shape[:2]
    yy, xx = np.indices((h, w))
    # Boîte serrée sur la maison-courrier : le contexte immédiatement joint est
    # volontairement conservé avec la structure pour ne pas l'entailler.
    house = alpha_mask([(338, 110), (535, 110), (576, 165), (580, 340), (500, 365), (353, 345), (322, 230)], (w, h))
    land = alpha_mask([(0, 165), (560, 165), (620, 245), (588, 600), (0, 600)], (w, h))
    vegetation = green_pixels(rgb) & (land | (xx < 250)) & ~house
    terrain = land & ~vegetation & ~house
    pale = low_saturation_light(rgb, 58)
    atmosphere = (yy < 245) & ~house & pale
    if mode == "nuit":
        atmosphere |= (yy < 180) & (rgb.max(axis=2) > 175) & ~house
    return partition(image, [np.zeros((h, w), dtype=bool), atmosphere, terrain, house, vegetation])


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, optimize=True)


def _string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<H", len(raw)) + raw


def _chunk(kind: int, data: bytes) -> bytes:
    return struct.pack("<IH", len(data) + 6, kind) + data


def write_aseprite(path: Path, layers: list[tuple[str, Image.Image]], size: tuple[int, int]) -> None:
    """Écrit un Aseprite à une image, dont chaque plan est un vrai layer."""
    chunks: list[bytes] = []
    for label, _ in layers:
        chunks.append(_chunk(0x2004, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + _string(label)))
    for index, (_, image) in enumerate(layers):
        box = image.getbbox()
        x, y = box[:2] if box else (0, 0)
        crop = image.crop(box) if box else Image.new("RGBA", (1, 1))
        cel = struct.pack("<HhhBHh", index, x, y, 255, 2, 0) + b"\0" * 5
        cel += struct.pack("<HH", crop.width, crop.height) + zlib.compress(crop.tobytes(), 9)
        chunks.append(_chunk(0x2005, cel))
    payload = b"".join(chunks)
    frame = struct.pack("<IHHH2sI", len(payload) + 16, 0xF1FA, len(chunks), 100, b"\0\0", len(chunks)) + payload
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(frame) + 128, 0xA5E0, 1, *size, 32, 1, 100)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + frame)


def write_tiled(path: Path, directory: str, mode: str, layers: tuple[tuple[str, str], ...], size: tuple[int, int]) -> None:
    width, height = size
    data = {
        "type": "map", "version": "1.10", "tiledversion": "1.11.0", "orientation": "orthogonal",
        "renderorder": "right-down", "tilewidth": 8, "tileheight": 8, "width": width // 8, "height": height // 8,
        "infinite": False, "nextlayerid": len(layers) + 1, "nextobjectid": 1,
        "layers": [
            {"id": index + 1, "name": label, "type": "imagelayer", "image": f"../calques/{mode}/{layer_id}.png",
             "visible": True, "opacity": 1, "x": 0, "y": 0}
            for index, (layer_id, label) in enumerate(layers)
        ],
        "tilesets": [],
        "properties": [{"name": "reference_layout", "type": "string", "value": directory}],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def webp_data(image: Image.Image) -> str:
    raw = io.BytesIO()
    image.convert("RGBA").save(raw, format="WEBP", lossless=True, method=4)
    return "data:image/webp;base64," + base64.b64encode(raw.getvalue()).decode("ascii")


def preview_html(scenes: list[dict]) -> str:
    data = json.dumps(scenes, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Layouts extérieurs PMD — jour et nuit</title><style>
:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#121725;color:#f8f0d7}}*{{box-sizing:border-box}}body{{margin:0;min-width:300px}}main{{max-width:1180px;margin:auto;padding:22px 16px 34px}}h1{{margin:0;font-size:clamp(1.35rem,4vw,2rem)}}p{{line-height:1.5;color:#c6d0ca}}.controls{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}button,label{{border:1px solid #5c6b82;border-radius:8px;padding:8px 10px;background:#222b3e;color:inherit;font:inherit}}button{{cursor:pointer}}button[aria-pressed=true]{{background:#dac574;color:#171b2b;font-weight:700}}#stage{{background:#090d17;border:1px solid #48546b;border-radius:12px;padding:14px;overflow:auto}}canvas{{display:block;margin:auto;max-width:none;image-rendering:pixelated;image-rendering:crisp-edges}}#layers{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}label{{display:flex;gap:7px;align-items:center;font-size:.92rem}}small{{display:block;color:#aab8b0;margin-top:12px}}code{{color:#f2da8d}}</style></head>
<body><main><h1>Layouts extérieurs PMD — jour / nuit</h1><p>Composition par plans fixes : masquez un plan pour contrôler le découpage, puis réactivez-le pour retrouver la référence.</p>
<div id="scene-buttons" class="controls" aria-label="Scène"></div><div id="mode-buttons" class="controls" aria-label="Ambiance"></div>
<section id="stage"><canvas id="map"></canvas></section><div id="layers" aria-label="Plans de composition"></div><small id="note"></small></main>
<script>'use strict';const DATA={data},canvas=document.querySelector('#map'),ctx=canvas.getContext('2d'),images={{}};let scene=0,mode='jour',visible=[];
function load(url){{if(images[url])return Promise.resolve(images[url]);return new Promise((ok,no)=>{{const im=new Image();im.onload=()=>{{images[url]=im;ok(im)}};im.onerror=no;im.src=url}})}}
function controls(){{const s=DATA[scene],a=document.querySelector('#scene-buttons'),b=document.querySelector('#mode-buttons'),l=document.querySelector('#layers');a.replaceChildren();b.replaceChildren();l.replaceChildren();DATA.forEach((x,i)=>{{const q=document.createElement('button');q.textContent=x.nom;q.setAttribute('aria-pressed',String(i===scene));q.onclick=()=>{{scene=i;visible=DATA[scene].layers.map(()=>true);draw()}};a.append(q)}});for(const value of ['jour','nuit']){{const q=document.createElement('button');q.textContent=value==='jour'?'☀ Jour':'☾ Nuit';q.setAttribute('aria-pressed',String(value===mode));q.onclick=()=>{{mode=value;draw()}};b.append(q)}}s.layers.forEach((x,i)=>{{const q=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=visible[i];c.onchange=()=>{{visible[i]=c.checked;paint()}};q.append(c,document.createTextNode(x.nom));l.append(q)}});document.querySelector('#note').textContent=s.description+' · '+s.dimensions.join(' × ')+' px · '+s.layers.length+' plans fixes';}}
async function paint(){{const s=DATA[scene];ctx.clearRect(0,0,canvas.width,canvas.height);await Promise.all(s.images[mode].map(load));s.images[mode].forEach((u,i)=>{{if(visible[i])ctx.drawImage(images[u],0,0)}})}}
function draw(){{const s=DATA[scene];canvas.width=s.dimensions[0];canvas.height=s.dimensions[1];canvas.style.width=Math.min(s.dimensions[0],document.querySelector('#stage').clientWidth-28)+'px';canvas.style.height='auto';controls();paint()}}visible=DATA[0].layers.map(()=>true);draw();</script></body></html>"""


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    previews: list[dict] = []
    manifest_scenes: list[dict] = []
    classifier: dict[str, Callable[[Image.Image, str], list[Image.Image]]] = {
        "cascades": cascade_layers, "prairie_maritime": prairie_maritime_layers, "cap_cotier": cap_layers,
    }
    for scene in SCENES:
        destination = OUT / scene["id"]
        if destination.exists():
            shutil.rmtree(destination)
        files: dict[str, dict] = {}
        preview_modes: dict[str, list[str]] = {}
        for mode, native_name in scene["natives"].items():
            native = as_rgba(NATIVES / native_name, scene["dimensions"])
            images = classifier[scene["id"]](native, mode)
            assert len(images) == len(scene["layers"])
            layer_files: dict[str, str] = {}
            composition = Image.new("RGBA", scene["dimensions"])
            base = Image.new("RGBA", scene["dimensions"])
            labels: list[tuple[str, Image.Image]] = []
            for index, ((layer_id, label), image) in enumerate(zip(scene["layers"], images)):
                relative = f"calques/{mode}/{layer_id}.png"
                save_png(image, destination / relative)
                layer_files[layer_id] = relative
                composition.alpha_composite(image)
                if index >= 2:
                    base.alpha_composite(image)
                labels.append((label, image))
            assert np.array_equal(np.asarray(composition), np.asarray(native))
            comp_path = f"compositions/{mode}.png"
            base_path = f"bases/{mode}_transparente.png"
            magenta_path = f"bases/{mode}_magenta.png"
            save_png(composition, destination / comp_path)
            save_png(base, destination / base_path)
            magenta = Image.new("RGBA", scene["dimensions"], (255, 0, 255, 255))
            magenta.alpha_composite(base)
            save_png(magenta, destination / magenta_path)
            ase_path = f"aseprite/{scene['id']}_{mode}.aseprite"
            tiled_path = f"tiled/{scene['id']}_{mode}.tmj"
            write_aseprite(destination / ase_path, labels, scene["dimensions"])
            write_tiled(destination / tiled_path, scene["id"], mode, scene["layers"], scene["dimensions"])
            files[mode] = {"native": f"../../source/references_exterieures/natives/{native_name}", "calques": layer_files,
                           "composition": comp_path, "base": base_path, "magenta": magenta_path,
                           "aseprite": ase_path, "tiled": tiled_path}
            preview_modes[mode] = [webp_data(image) for image in images]
        manifest_scenes.append({"id": scene["id"], "nom": scene["nom"], "dimensions": list(scene["dimensions"]),
                                "grille_px": 8, "animation": False,
                                "calques": [{"id": layer_id, "nom": label} for layer_id, label in scene["layers"]],
                                "fichiers": files})
        previews.append({"id": scene["id"], "nom": scene["nom"], "description": scene["description"],
                         "dimensions": list(scene["dimensions"]),
                         "layers": [{"nom": label} for _, label in scene["layers"]], "images": preview_modes})
    manifest = {"version": 1, "titre": "Layouts extérieurs PMD — références jour/nuit", "grille_px": 8,
                "animation": False, "methode": "Composition PNG par calques disjoints, sans interpolation ni animation.",
                "provenance": "source/references_exterieures/provenance.json", "scenes": manifest_scenes}
    (OUT / "kit.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PREVIEW.write_text(preview_html(previews), encoding="utf-8")
    print("Exports terminés : 3 layouts × jour/nuit, 5 calques par variante, PNG/Aseprite/Tiled et aperçu autonome.")
    return manifest


if __name__ == "__main__":
    build()
