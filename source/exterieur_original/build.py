#!/usr/bin/env python3
"""Construit un paysage original à cinq layers générés indépendamment.

Les rasters de generation/ sont uniquement des sorties du générateur d'images.
Ils ne consomment ni découpe, ni layout, ni pixel des références précédentes.
Le fond magenta #FF00FF est le chroma-key explicite de tous les overlays.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from animation import AnimatedLayer, compose, export_variant, save_png

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
GENERATION = SOURCE / "generation"
OUT = ROOT / "exterieur_original"
PREVIEW = ROOT / "apercu_exterieur_original.html"
# Carte de 28×16 tuiles PMDO (24 px), soit 84×48 cellules d'édition de 8 px.
# Elle excède la fenêtre logique 320×240 de WaterfallVillageCapital.
SIZE = (672, 384)
GENERATION_SIZE = (1376, 768)
CELL_PX, PMDO_TILE_PX, VIEWPORT_SIZE = 8, 24, (320, 240)
VIEWPORT_ORIGIN = (176, 72)  # 22×9 cellules de 8 px — parfaitement aligné.
MAGENTA = np.array((255, 0, 255), dtype=np.uint8)
# Deux motifs de nuages de 336 px couvrent la carte de 672 px. Les deux
# dimensions sont des multiples de la grille de 8 px, donc le wrap reste net.
CLOUD_PERIOD, SEA_PERIOD = 336, 24
FRAMES, DURATION = math.lcm(CLOUD_PERIOD, SEA_PERIOD), 250
MODE = "original"

LAYERS = (
    ("00_ciel", "Ciel ouvert — sans nuage", False, "00_ciel_genere.png"),
    ("01_nuages_wrap", "Nuages — overlay horizontal, wrap parfait", True, "02_nuages_genere.png"),
    ("02_mer_palette", "Mer — cycle de palette sans déplacement", True, "01_mer_generee.png"),
    ("03_plateaux_reliefs", "Plateaux et reliefs naturels", False, "03_plateaux_reliefs_generes.png"),
    ("04_falaise", "Falaise naturelle de premier plan", False, "04_falaise_generee.png"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated(path: Path) -> Image.Image:
    """Normalise un raster créé par le générateur, jamais une référence externe."""
    assert path.is_file(), f"Layer généré manquant : {path}"
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    assert image.size == GENERATION_SIZE, f"Taille générée inattendue : {path} = {image.size}"
    # 1 344×768 est un multiple exact de 2 de 672×384 : le cadrage central
    # évite toute interpolation et conserve les pixels générés intacts.
    return image.crop((16, 0, 1360, 768)).resize(SIZE, Image.Resampling.NEAREST)


def normalise_magenta(image: Image.Image) -> Image.Image:
    """Uniformise le chroma-key externe et la frange fuchsia du générateur.

    Seules les teintes rose/violet connectées au bord sont supprimées : les
    violets de roche ou de végétation enfermés dans un sujet restent intacts.
    """
    array = np.asarray(image.convert("RGB")).copy()
    red, green, blue = (array[:, :, index] for index in range(3))
    candidate = ((red > 100) & (blue > 100) & (green < np.minimum(red, blue) * .80)).astype(np.uint8)
    _count, labels = cv2.connectedComponents(candidate, connectivity=4)
    border = np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1]))
    exterior = np.isin(labels, np.unique(border[border > 0]))
    # Les îlots rose vif restants au sein d'un nuage sont des trous produits
    # par le modèle, non des couleurs utilisables du décor.
    strict_key = (red > 220) & (blue > 220) & (green < 100)
    array[exterior | strict_key] = MAGENTA
    return Image.fromarray(array, "RGB")


def rgba_from_magenta(image: Image.Image) -> Image.Image:
    array = np.asarray(image.convert("RGB")).copy()
    alpha = np.full(array.shape[:2], 255, dtype=np.uint8)
    keyed = np.all(array == MAGENTA, axis=2)
    array[keyed] = 0
    alpha[keyed] = 0
    return Image.fromarray(np.dstack((array, alpha)), "RGBA")


def magenta_from_rgba(image: Image.Image) -> Image.Image:
    array = np.asarray(image.convert("RGBA"))
    output = array[:, :, :3].copy()
    output[array[:, :, 3] == 0] = MAGENTA
    return Image.fromarray(output, "RGB")


def cloud_wrap(image: Image.Image) -> Image.Image:
    """Construit un ruban de nuages réellement périodique sur 344 px.

    Une tranche issue du layer IA est répétée deux fois sur les 688 px du
    cadre. Ses bords sont du chroma-key pur : le bord droit d'un motif rejoint
    exactement le bord gauche du suivant, et `offset(..., -172, 0)` est
    bit-identique à l'état 0. Ce n'est pas une copie de layout externe : le
    motif et ses groupes de nuages proviennent du layer généré original.
    """
    array = np.asarray(image.convert("RGB")).copy()
    start = (SIZE[0] - CLOUD_PERIOD) // 2
    tile = array[:, start:start + CLOUD_PERIOD].copy()
    tile[:, :12] = MAGENTA
    tile[:, -12:] = MAGENTA
    repeated = np.concatenate([tile] * (SIZE[0] // CLOUD_PERIOD), axis=1)
    return Image.fromarray(repeated, "RGB")


def palette_cycle(sea: Image.Image) -> tuple[list[Image.Image], dict]:
    """Fabrique un cycle chromatique sans translation ni déformation de la mer."""
    base = np.asarray(sea.convert("RGBA"))
    active = base[:, :, 3] > 0
    frames: list[Image.Image] = []
    phases: list[dict] = []
    for frame in range(SEA_PERIOD):
        # 0 -> maximum doux -> 0. La frame 24 (phase 0) raccorde exactement
        # avec la frame 0 ; les coordonnées et l'alpha ne changent jamais.
        strength = math.sin(math.pi * frame / SEA_PERIOD)
        current = base.copy()
        rgb = current[:, :, :3].astype(np.int16)
        rgb[:, :, 0][active] += round(5 * strength)
        rgb[:, :, 1][active] += round(15 * strength)
        rgb[:, :, 2][active] += round(8 * strength)
        current[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        frames.append(Image.fromarray(current, "RGBA"))
        phases.append({"phase": frame, "force": round(strength, 8), "deplacement_px": [0, 0]})
    assert np.array_equal(np.asarray(frames[0])[:, :, 3], np.asarray(frames[12])[:, :, 3])
    assert not np.array_equal(np.asarray(frames[0]), np.asarray(frames[12]))
    return frames, {"palette_phases": phases,
                    "geometrie_inchangee": True, "raccord_frame_24_vers_0": True}


def atlas(frames: list[Image.Image], columns: int = 6) -> Image.Image:
    rows = math.ceil(len(frames) / columns)
    image = Image.new("RGBA", (SIZE[0] * columns, SIZE[1] * rows))
    for index, frame in enumerate(frames):
        image.alpha_composite(frame, ((index % columns) * SIZE[0], (index // columns) * SIZE[1]))
    return image


def write_source_layers(keyed: list[Image.Image], sea_frames: list[Image.Image]) -> None:
    """Conserve les cinq PNG finals sur fond magenta et les 24 états de mer."""
    folder = OUT / "calques_magentas" / MODE
    for definition, image in zip(LAYERS, keyed):
        path = folder / f"{definition[0]}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(path, optimize=True)
    cycle_dir = OUT / "cycles_magentas" / "mer_palette"
    for index, frame in enumerate(sea_frames):
        path = cycle_dir / f"mer_palette_{index:02d}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        magenta_from_rgba(frame).save(path, optimize=True)


def data_uri(image: Image.Image) -> str:
    data = io.BytesIO()
    image.save(data, format="WEBP", lossless=True, method=4)
    return "data:image/webp;base64," + base64.b64encode(data.getvalue()).decode("ascii")


def preview_html(layer_files: list[Image.Image], sea_atlas: Image.Image) -> str:
    """Aperçu autonome : carte complète, grille 8 px et fenêtre PMDO 320×240."""
    layers_data = json.dumps([data_uri(image) for image in layer_files], separators=(",", ":"))
    sea_data = json.dumps(data_uri(sea_atlas))
    names = json.dumps([definition[1] for definition in LAYERS], ensure_ascii=False)
    html = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Falaise originale — carte WaterfallVillageCapital</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#101522;color:#f8f2df}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:22px 16px 34px}h1{margin:0;font-size:clamp(1.35rem,4vw,2rem)}p,small{color:#c9d3cf;line-height:1.5}.controls,#layers{display:flex;flex-wrap:wrap;gap:8px;margin:13px 0}button,label{border:1px solid #667993;border-radius:8px;padding:8px 10px;background:#232d41;color:inherit;font:inherit}button{cursor:pointer}button[aria-pressed=true]{background:#e9d481;color:#172034;font-weight:700}label{display:flex;align-items:center;gap:7px;font-size:.92rem}#stage{overflow:auto;border:1px solid #52637c;border-radius:12px;padding:14px;background:#070b12}canvas{display:block;margin:auto;image-rendering:pixelated;image-rendering:crisp-edges;max-width:none}code{color:#f4dc8b}</style></head><body><main><h1>Falaise originale — carte WaterfallVillageCapital</h1><p>Carte <code>[[MAP_W]] × [[MAP_H]] px</code>, cellules 8 px. Le cadre jaune est la viewport logique <code>320 × 240 px</code> de WaterfallVillageCapital, alignée à la cellule 8 px. <code>#FF00FF</code> est traité comme transparence.</p><div class="controls"><button id="motion" type="button"></button><button id="grid" type="button"></button><button id="viewport" type="button"></button><span id="time"></span></div><section id="stage"><canvas id="map" width="[[MAP_W]]" height="[[MAP_H]]"></canvas></section><div id="layers"></div><small>Nuages : wrap horizontal de [[CLOUD_PERIOD]] px. Mer : 24 états de palette, aucun déplacement de pixels. La carte complète fait [[MAP_TILES_W]] × [[MAP_TILES_H]] tuiles PMDO de 24 px.</small><script>
'use strict';
const SIZE=[[[MAP_W]],[[MAP_H]],],LAYERS=[[LAYERS]],SEA_ATLAS=[[SEA]],NAMES=[[NAMES]],VIEW={x:[[VIEW_X]],y:[[VIEW_Y]],w:[[VIEW_W]],h:[[VIEW_H]]};
const C=document.querySelector('#map'),X=C.getContext('2d'),CACHE={},O=document.createElement('canvas'),OX=O.getContext('2d'),MOTION=document.querySelector('#motion'),GRID=document.querySelector('#grid'),VIEWPORT=document.querySelector('#viewport');
let visible=NAMES.map(()=>true),frame=0,grid=true,showViewport=true,play=true,last=performance.now();
function load(url){if(CACHE[url])return Promise.resolve(CACHE[url]);return new Promise((yes,no)=>{const image=new Image();image.onload=()=>{CACHE[url]=image;yes(image)};image.onerror=no;image.src=url})}
function keyed(image,sx=0,sy=0){O.width=SIZE[0];O.height=SIZE[1];OX.clearRect(0,0,SIZE[0],SIZE[1]);OX.drawImage(image,sx,sy,SIZE[0],SIZE[1],0,0,SIZE[0],SIZE[1]);const data=OX.getImageData(0,0,SIZE[0],SIZE[1]);for(let p=0;p<data.data.length;p+=4)if(data.data[p]>240&&data.data[p+1]<24&&data.data[p+2]>240)data.data[p+3]=0;OX.putImageData(data,0,0);return O}
async function paint(){await Promise.all(LAYERS.concat([SEA_ATLAS]).map(load));X.clearRect(0,0,SIZE[0],SIZE[1]);for(let i=0;i<LAYERS.length;i++){if(!visible[i])continue;if(i===1){const dx=-(frame%[[CLOUD_PERIOD]]);X.drawImage(keyed(CACHE[LAYERS[i]]),dx,0);X.drawImage(keyed(CACHE[LAYERS[i]]),dx+SIZE[0],0)}else if(i===2){const phase=frame%24;X.drawImage(keyed(CACHE[SEA_ATLAS],(phase%6)*SIZE[0],Math.floor(phase/6)*SIZE[1]),0,0)}else X.drawImage(keyed(CACHE[LAYERS[i]]),0,0)}if(grid){X.save();X.strokeStyle='rgba(255,231,142,.34)';X.lineWidth=1;X.beginPath();for(let x=0;x<=SIZE[0];x+=8){X.moveTo(x+.5,0);X.lineTo(x+.5,SIZE[1])}for(let y=0;y<=SIZE[1];y+=8){X.moveTo(0,y+.5);X.lineTo(SIZE[0],y+.5)}X.stroke();X.restore()}if(showViewport){X.save();X.strokeStyle='#ffe260';X.lineWidth=2;X.setLineDash([6,3]);X.strokeRect(VIEW.x+1,VIEW.y+1,VIEW.w-2,VIEW.h-2);X.setLineDash([]);X.fillStyle='rgba(16,21,34,.75)';X.fillRect(VIEW.x+4,VIEW.y+4,208,19);X.fillStyle='#ffe260';X.font='12px system-ui';X.fillText('Viewport WaterfallVillageCapital · 320 × 240',VIEW.x+8,VIEW.y+18);X.restore()}document.querySelector('#time').textContent='Image '+(frame+1)+' / [[FRAMES]] · mer '+((frame%24)+1)+' / 24'}
function controls(){const out=document.querySelector('#layers');out.replaceChildren();NAMES.forEach((name,index)=>{const label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=visible[index];box.onchange=()=>{visible[index]=box.checked;paint()};label.append(box,document.createTextNode(name));out.append(label)});GRID.textContent=grid?'Grille 8 px : visible':'Grille 8 px : masquée';GRID.setAttribute('aria-pressed',String(grid));VIEWPORT.textContent=showViewport?'Viewport 320×240 : visible':'Viewport 320×240 : masquée';VIEWPORT.setAttribute('aria-pressed',String(showViewport));MOTION.textContent=play?'❚❚ Pause':'▶ Animer';MOTION.setAttribute('aria-pressed',String(play))}
GRID.onclick=()=>{grid=!grid;controls();paint()};VIEWPORT.onclick=()=>{showViewport=!showViewport;controls();paint()};MOTION.onclick=()=>{play=!play;last=performance.now();controls();paint()};
function resize(){const max=document.querySelector('#stage').clientWidth-28,scale=Math.min(1,max/SIZE[0]);C.style.width=Math.floor(SIZE[0]*scale)+'px';C.style.height=Math.floor(SIZE[1]*scale)+'px'}
function tick(now){if(play&&now-last>=250){frame=(frame+Math.floor((now-last)/250))%[[FRAMES]];last=now;paint()}requestAnimationFrame(tick)}
controls();resize();paint();requestAnimationFrame(tick);addEventListener('resize',resize);
</script></main></body></html>"""
    tokens = {
        "[[MAP_W]]": str(SIZE[0]), "[[MAP_H]]": str(SIZE[1]),
        "[[MAP_TILES_W]]": str(SIZE[0] // PMDO_TILE_PX), "[[MAP_TILES_H]]": str(SIZE[1] // PMDO_TILE_PX),
        "[[LAYERS]]": layers_data, "[[SEA]]": sea_data, "[[NAMES]]": names,
        "[[CLOUD_PERIOD]]": str(CLOUD_PERIOD), "[[FRAMES]]": str(FRAMES),
        "[[VIEW_X]]": str(VIEWPORT_ORIGIN[0]), "[[VIEW_Y]]": str(VIEWPORT_ORIGIN[1]),
        "[[VIEW_W]]": str(VIEWPORT_SIZE[0]), "[[VIEW_H]]": str(VIEWPORT_SIZE[1]),
    }
    for token, value in tokens.items():
        html = html.replace(token, value)
    return html

def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    keyed: list[Image.Image] = []
    for key, _label, _animated, filename in LAYERS:
        source = generated(GENERATION / filename)
        layer = source if key == "00_ciel" else normalise_magenta(source)
        if key == "01_nuages_wrap":
            layer = cloud_wrap(layer)
        keyed.append(layer)
    rgba = [rgba_from_magenta(image) if key != "00_ciel" else image.convert("RGBA") for (key, *_), image in zip(LAYERS, keyed)]
    assert rgba[0].getchannel("A").getextrema() == (255, 255)
    assert all(np.any(np.all(np.asarray(image.convert("RGB")) == MAGENTA, axis=2)) for image in keyed[1:])
    sea_frames, cycle_meta = palette_cycle(rgba[2])
    source_atlas = atlas(sea_frames)
    source_atlas_path = OUT / "animations" / "source_mer_palette.png"
    save_png(source_atlas, source_atlas_path)
    write_source_layers(keyed, sea_frames)
    definitions = [{"id": key, "nom": label, "anime": animated} for key, label, animated, _filename in LAYERS]
    cloud_spec = {"kind": "scroll", "period": CLOUD_PERIOD, "prefix": "nuages_wrap",
                  "vitesse_px_par_image": -1, "wrap_horizontal_parfait": True,
                  "couture_bords_px": 12}
    sea_spec = {"kind": "frames", "period": SEA_PERIOD, "prefix": "mer_palette",
                "source_atlas": "animations/source_mer_palette.png", "source_frame_size": list(SIZE),
                "source_columns": 6, "palette_only": True, **cycle_meta}
    specs = {"01_nuages_wrap": cloud_spec, "02_mer_palette": sea_spec}
    files = export_variant(OUT, MODE, definitions, rgba, specs, SIZE, FRAMES, 3, [], "falaise_originale")
    operators = [AnimatedLayer(image, specs.get(definition["id"]), OUT) for definition, image in zip(definitions, rgba)]
    initial = compose(operators, SIZE, 0)
    with Image.open(OUT / files["composition"]) as opened:
        assert np.array_equal(np.asarray(opened.convert("RGBA")), np.asarray(initial))
    # Cloud wrap contract: matrix and period frame equal exactly; sea preserves
    # all alpha/coordinates and changes only its palette values.
    assert np.array_equal(np.asarray(operators[1].at(0)), np.asarray(operators[1].at(CLOUD_PERIOD)))
    assert np.array_equal(np.asarray(operators[2].at(0))[:, :, 3], np.asarray(operators[2].at(12))[:, :, 3])

    # Contrat de carte/viewport : mêmes unités que WaterfallVillageCapital.
    # Le canvas reste une petite carte autonome, mais son pas est 8 px et son
    # cadre caméra est la fenêtre PMDO réelle 320×240, tous deux sans fraction.
    viewport_box = (*VIEWPORT_ORIGIN, VIEWPORT_ORIGIN[0] + VIEWPORT_SIZE[0], VIEWPORT_ORIGIN[1] + VIEWPORT_SIZE[1])
    viewport_path = "compositions/viewport_waterfallvillagecapital.png"
    save_png(initial.crop(viewport_box), OUT / viewport_path)
    map_contract = {
        "reference": "WaterfallVillageCapital / Metano Town — guide de grille, de viewport et de texture; aucun pixel source livré",
        "map_px": list(SIZE), "cellule_px": CELL_PX, "cellules": [SIZE[0] // CELL_PX, SIZE[1] // CELL_PX],
        "tuile_pmdo_px": PMDO_TILE_PX, "tuiles_pmdo": [SIZE[0] // PMDO_TILE_PX, SIZE[1] // PMDO_TILE_PX],
        "viewport_px": list(VIEWPORT_SIZE), "viewport_cellules": [VIEWPORT_SIZE[0] // CELL_PX, VIEWPORT_SIZE[1] // CELL_PX],
        "origine_px": list(VIEWPORT_ORIGIN), "origine_cellules": [VIEWPORT_ORIGIN[0] // CELL_PX, VIEWPORT_ORIGIN[1] // CELL_PX],
        "composition_vue": viewport_path,
    }
    map_contract_path = OUT / "map_waterfallvillagecapital.json"
    map_contract_path.write_text(json.dumps(map_contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tiled_path = OUT / files["tiled"]
    tiled = json.loads(tiled_path.read_text(encoding="utf-8"))
    tiled["properties"] = [
        {"name": "cellule_edition_px", "type": "int", "value": CELL_PX},
        {"name": "tuile_pmdo_px", "type": "int", "value": PMDO_TILE_PX},
        {"name": "viewport_waterfallvillagecapital_px", "type": "string", "value": "320x240"},
        {"name": "viewport_origine_px", "type": "string", "value": f"{VIEWPORT_ORIGIN[0]},{VIEWPORT_ORIGIN[1]}"},
    ]
    tiled_path.write_text(json.dumps(tiled, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    files["viewport"] = viewport_path
    files["contrat_map_viewport"] = str(map_contract_path.relative_to(OUT))
    manifest = {
        "version": 1, "id": "falaise_originale", "titre": "Falaise océanique originale — layers générés",
        "dimensions": list(SIZE), "grille_px": 8, "fond_chroma_key": "#FF00FF",
        "animation": {"frames": FRAMES, "duree_image_ms": DURATION, "duree_boucle_ms": FRAMES * DURATION,
                       "nuages": f"wrap horizontal parfaitement périodique sur {CLOUD_PERIOD} px", "mer": "cycle de palette 24 phases sans déplacement"},
        "creation": "Cinq layers générés séparément. Les falaises/plateaux suivent la DA des tuiles Metano Town et le ciel la DA Sharpedo ; aucun pixel de référence n'est copié, découpé, recoloré ou composé.",
        "map_viewport": map_contract,
        "calques": definitions, "fichiers": {MODE: {**files,
            "calques_magentas": {definition["id"]: f"calques_magentas/{MODE}/{definition['id']}.png" for definition in definitions},
            "cycle_mer_magentas": [f"cycles_magentas/mer_palette/mer_palette_{frame:02d}.png" for frame in range(SEA_PERIOD)]}},
        "sources_generation": {filename: {"sha256": sha256(GENERATION / filename), "dimensions": list(GENERATION_SIZE)} for *_x, filename in LAYERS},
    }
    (OUT / "kit.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(SOURCE / "README.md", OUT / "README.md")
    PREVIEW.write_text(preview_html(keyed, source_atlas), encoding="utf-8")
    print(f"Falaise originale exportée : {len(LAYERS)} layers générés, {FRAMES} images, fond magenta et grille 8 px.")
    return manifest


if __name__ == "__main__":
    build()
