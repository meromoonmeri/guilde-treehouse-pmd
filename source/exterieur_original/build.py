#!/usr/bin/env python3
"""Construit un paysage original à cinq layers générés indépendamment.

Les rasters de generation/ sont uniquement des sorties du générateur d'images,
régénérées sous contrainte stricte de pixel art PMD natif (palette limitée,
clusters nets, contours crénelés, aucun lissage). Le fond magenta #FF00FF est le
chroma-key explicite de tous les overlays.
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
SIZE = (688, 384)
GENERATION_SIZE = (1376, 768)
MAGENTA = np.array((255, 0, 255), dtype=np.uint8)
# Le motif généré de nuages est mis en tuile sur 344 px : 688 px = 2 motifs.
# Une boucle de 172 px est donc strictement continue, sans sacrifier la
# timeline Aseprite/Tiled à un atlas disproportionné.
CLOUD_PERIOD, SEA_PERIOD = 344, 24
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
    return image.resize(SIZE, Image.Resampling.NEAREST)


def normalise_magenta(image: Image.Image) -> Image.Image:
    """Uniformise le chroma-key externe et sa frange fuchsia de générateur.

    Seules les teintes rose/violet connectées au bord du canvas sont une zone
    vide : les violets des ombres, fleurs ou rochers enfermés dans le sujet ne
    sont jamais touchés. Le résultat ne dessine rien, il rend uniquement le
    fond de clé strictement #FF00FF, sans halo fuchsia dans la composition.
    """
    array = np.asarray(image.convert("RGB")).copy()
    red, green, blue = (array[:, :, index] for index in range(3))
    candidate = ((red > 100) & (blue > 100) & (green < np.minimum(red, blue) * .80)).astype(np.uint8)
    _count, labels = cv2.connectedComponents(candidate, connectivity=4)
    border = np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1]))
    exterior = np.isin(labels, np.unique(border[border > 0]))
    array[exterior] = MAGENTA
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
    layers_data = json.dumps([data_uri(image) for image in layer_files], separators=(",", ":"))
    sea_data = json.dumps(data_uri(sea_atlas))
    names = json.dumps([definition[1] for definition in LAYERS], ensure_ascii=False)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Falaise originale — layers générés</title><style>
:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#101522;color:#f8f2df}}*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1180px;margin:auto;padding:22px 16px 34px}}h1{{margin:0;font-size:clamp(1.35rem,4vw,2rem)}}p,small{{color:#c9d3cf;line-height:1.5}}.controls,#layers{{display:flex;flex-wrap:wrap;gap:8px;margin:13px 0}}button,label{{border:1px solid #667993;border-radius:8px;padding:8px 10px;background:#232d41;color:inherit;font:inherit}}button{{cursor:pointer}}button[aria-pressed=true]{{background:#e9d481;color:#172034;font-weight:700}}label{{display:flex;align-items:center;gap:7px;font-size:.92rem}}#stage{{overflow:auto;border:1px solid #52637c;border-radius:12px;padding:14px;background:#070b12}}canvas{{display:block;margin:auto;image-rendering:pixelated;image-rendering:crisp-edges;max-width:none}}code{{color:#f4dc8b}}</style></head><body><main><h1>Falaise originale — layers IA, fond magenta</h1><p>Chaque source est une création indépendante du générateur. <code>#FF00FF</code> est traité comme chroma-key dans cet aperçu. La grille 8 px est active par défaut.</p><div class="controls"><button id="motion" type="button"></button><button id="grid" type="button"></button><span id="time"></span></div><section id="stage"><canvas id="map" width="688" height="384"></canvas></section><div id="layers"></div><small>Nuages : offset horizontal de 1 px/image, retour exact après {CLOUD_PERIOD} images. Mer : 24 états de palette, aucune translation de pixels.</small><script>
'use strict';const SIZE=[688,384],LAYERS={layers_data},SEA_ATLAS={sea_data},NAMES={names},C=document.querySelector('#map'),X=C.getContext('2d'),CACHE={{}},O=document.createElement('canvas'),OX=O.getContext('2d');let visible=NAMES.map(()=>true),frame=0,grid=true,play=true,last=performance.now();function load(u){{if(CACHE[u])return Promise.resolve(CACHE[u]);return new Promise((yes,no)=>{{const i=new Image();i.onload=()=>{{CACHE[u]=i;yes(i)}};i.onerror=no;i.src=u}})}}function keyed(image,sx=0,sy=0){{O.width=SIZE[0];O.height=SIZE[1];OX.clearRect(0,0,...SIZE);OX.drawImage(image,sx,sy,...SIZE,0,0,...SIZE);let d=OX.getImageData(0,0,...SIZE);for(let i=0;i<d.data.length;i+=4)if(d.data[i]>240&&d.data[i+1]<24&&d.data[i+2]>240)d.data[i+3]=0;OX.putImageData(d,0,0);return O}}async function paint(){{await Promise.all(LAYERS.concat([SEA_ATLAS]).map(load));X.clearRect(0,0,...SIZE);for(let i=0;i<LAYERS.length;i++){{if(!visible[i])continue;if(i===1){{let dx=-(frame%{CLOUD_PERIOD});X.drawImage(keyed(CACHE[LAYERS[i]]),dx,0);X.drawImage(keyed(CACHE[LAYERS[i]]),dx+688,0)}}else if(i===2){{let f=frame%24,sx=(f%6)*688,sy=Math.floor(f/6)*384;X.drawImage(keyed(CACHE[SEA_ATLAS],sx,sy),0,0)}}else X.drawImage(keyed(CACHE[LAYERS[i]]),0,0)}}if(grid){{X.save();X.strokeStyle='rgba(255,231,142,.34)';X.lineWidth=1;X.beginPath();for(let x=0;x<=688;x+=8){{X.moveTo(x+.5,0);X.lineTo(x+.5,384)}}for(let y=0;y<=384;y+=8){{X.moveTo(0,y+.5);X.lineTo(688,y+.5)}}X.stroke();X.restore()}}document.querySelector('#time').textContent='Image '+(frame+1)+' / {FRAMES} · mer '+((frame%24)+1)+' / 24';}}function controls(){{let out=document.querySelector('#layers');out.replaceChildren();NAMES.forEach((name,i)=>{{let l=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=visible[i];c.onchange=()=>{{visible[i]=c.checked;paint()}};l.append(c,document.createTextNode(name));out.append(l)}});let g=document.querySelector('#grid');g.textContent=grid?'Grille 8 px : visible':'Grille 8 px : masquée';g.setAttribute('aria-pressed',String(grid));g.onclick=()=>{{grid=!grid;controls();paint()}};let m=document.querySelector('#motion');m.textContent=play?'❚❚ Pause':'▶ Animer';m.setAttribute('aria-pressed',String(play));m.onclick=()=>{{play=!play;last=performance.now();controls();paint()}};}}function resize(){{let max=document.querySelector('#stage').clientWidth-28,scale=Math.min(1,max/688);C.style.width=Math.floor(688*scale)+'px';C.style.height=Math.floor(384*scale)+'px';}}function tick(now){{if(play&&now-last>=250){{frame=(frame+Math.floor((now-last)/250))%{FRAMES};last=now;paint()}}requestAnimationFrame(tick)}}controls();resize();paint();requestAnimationFrame(tick);addEventListener('resize',resize);</script></main></body></html>"""


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
    # Cloud wrap contract: matrix and frame 688 equal exactly; sea preserves
    # all alpha/coordinates and change only its palette values.
    assert np.array_equal(np.asarray(operators[1].at(0)), np.asarray(operators[1].at(CLOUD_PERIOD)))
    assert np.array_equal(np.asarray(operators[2].at(0))[:, :, 3], np.asarray(operators[2].at(12))[:, :, 3])
    manifest = {
        "version": 1, "id": "falaise_originale", "titre": "Falaise océanique originale — layers générés",
        "dimensions": list(SIZE), "grille_px": 8, "fond_chroma_key": "#FF00FF",
        "animation": {"frames": FRAMES, "duree_image_ms": DURATION, "duree_boucle_ms": FRAMES * DURATION,
                       "nuages": f"wrap horizontal parfaitement périodique sur {CLOUD_PERIOD} px", "mer": "cycle de palette 24 phases sans déplacement"},
        "creation": "Cinq layers générés séparément de zéro ; aucune référence externe n'est un layout, template ou pixel source.",
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
