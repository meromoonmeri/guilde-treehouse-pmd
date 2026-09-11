#!/usr/bin/env python3
"""Export multicouche animé des trois layouts générés à partir des références.

Méthode reprise du kit principal et du précédent travail extérieur : native
complète validée, plans RGBA, recomposition testée, puis mêmes opérations
animées exportées vers PNG, Aseprite, Tiled et aperçu autonome.
"""
from __future__ import annotations

import base64
import io
import json
import shutil
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw

from exterior_reference_animation import AnimatedLayer, compose, export_variant, stars_spec

ROOT = Path(__file__).resolve().parents[1]
NATIVES = ROOT / "source" / "references_exterieures" / "natives"
OUT = ROOT / "references_exterieures"
PREVIEW = ROOT / "apercu_references_exterieures.html"
FRAMES, DURATION = 24, 250

SCENES = (
    {
        "id": "cascades", "nom": "Sanctuaire des cascades", "dimensions": (408, 648),
        "natives": {"jour": "cascades_jour.png", "nuit": "cascades_nuit.png"},
        "description": "Îlot suspendu, cascades verticales, marais et végétation de rive.",
        "layers": (
            ("00_ciel", "Ciel et montagnes lointaines", False),
            ("01_astres", "Lune fixe et étoiles scintillantes", True),
            ("02_nuages", "Nuages — défilement horizontal", True),
            ("03_eau_cascades", "Eau, cascades et écume", False),
            ("04_ilot_rocheux", "Îlot rocheux suspendu", False),
            ("05_vegetation", "Roseaux, buissons et premier plan", False),
        ),
    },
    {
        "id": "prairie_maritime", "nom": "Prairie maritime", "dimensions": (688, 384),
        "natives": {"jour": "prairie_maritime_jour.png", "nuit": "prairie_maritime_nuit.png"},
        "description": "Prairie fleurie ouverte, rebords rocheux et mer du nord.",
        "layers": (
            ("00_ciel", "Ciel et montagnes lointaines", False),
            ("01_astres", "Lune fixe et étoiles scintillantes", True),
            ("02_nuages", "Nuages — défilement horizontal", True),
            ("03_mer_reflets", "Mer et reflets", False),
            ("04_falaises", "Parois rocheuses et rebords", False),
            ("05_prairie_chemin", "Prairie centrale et chemin", False),
            ("06_fleurs_vegetation", "Fleurs, herbes et buissons", False),
        ),
    },
    {
        "id": "cap_cotier", "nom": "Cap côtier", "dimensions": (688, 384),
        "natives": {"jour": "cap_cotier_jour.png", "nuit": "cap_cotier_nuit.png"},
        "description": "Prairie, chemin, maison-courrier, falaise et océan.",
        "layers": (
            ("00_ciel", "Ciel et horizon marin", False),
            ("01_astres", "Lune fixe et étoiles scintillantes", True),
            ("02_nuages", "Nuages — défilement horizontal", True),
            ("03_mer_reflets", "Mer et reflet lunaire", False),
            ("04_falaise_terrain", "Falaise, chemin et sol", False),
            ("05_maison", "Maison-courrier et abords", False),
            ("06_vegetation", "Arbres, fleurs et liserés d'herbe", False),
        ),
    },
)


def load(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as opened:
        image = opened.convert("RGBA")
    assert image.size == size, f"Dimensions inattendues pour {path}: {image.size}, attendu {size}"
    assert image.getchannel("A").getextrema() == (255, 255), f"Native non opaque : {path}"
    return image


def mask_polygon(points: list[tuple[int, int]], size: tuple[int, int]) -> np.ndarray:
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return np.asarray(mask, dtype=bool)


def green(rgb: np.ndarray) -> np.ndarray:
    red, grn, blue = (rgb[:, :, i].astype(np.int16) for i in range(3))
    return (grn > red + 6) & (grn >= blue - 12) & (grn > 30)


def red_or_pink(rgb: np.ndarray) -> np.ndarray:
    red, grn, blue = (rgb[:, :, i].astype(np.int16) for i in range(3))
    return (red > grn + 23) & (red > blue + 10) & (red > 85)


def components(mask: np.ndarray, min_area: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype("uint8"), 8)
    keep = np.zeros(mask.shape, dtype=bool)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= min_area:
            keep |= labels == label
    return keep


def atmosphere_masks(image: Image.Image, mode: str, expect_clouds: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Sépare nuages et astres, en gardant le fond à reconstituer sous eux."""
    a = np.asarray(image.convert("RGBA"))
    rgb, (h, w) = a[:, :, :3], a.shape[:2]
    yy, _ = np.indices((h, w))
    high, low = rgb.max(axis=2).astype(np.int16), rgb.min(axis=2).astype(np.int16)
    r, g, b = (rgb[:, :, i].astype(np.int16) for i in range(3))
    ceiling = yy < int(h * .48)
    if mode == "jour":
        candidate_cloud = ceiling & (high > 145) & ((high - low) < 115) & (b >= r - 18)
        raw_astres = np.zeros((h, w), dtype=bool)
    else:
        # Les nuages bleu-violet gardent davantage de rouge que le fond indigo.
        candidate_cloud = ceiling & (high > 56) & (r > b * .38) & (g > b * .38)
        # Coeurs presque blancs/cyan des étoiles et de la lune. Les lavis
        # mauves des nuages sont volontairement exclus, même s'ils sont très
        # lumineux sur leurs contours.
        raw_astres = ceiling & (high > 210) & (r > 145) & (g > 155) & ((high - low) < 105)
    cloud = components(candidate_cloud, 35)
    if mode == "nuit":
        # Ne retenir comme astres que les composantes petites/moyennes : les
        # vastes composantes lumineuses restent des nuages animés.
        count, labels, stats, _ = cv2.connectedComponentsWithStats(raw_astres.astype("uint8"), 8)
        stars = np.zeros((h, w), dtype=bool)
        for label in range(1, count):
            _, _, box_w, box_h, area = stats[label]
            # Une lune peut atteindre environ 50 px dans le rendu large ; une
            # traînée de nuage, même fragmentée, s'étend nettement davantage.
            if 1 <= area <= 2200 and box_w <= 55 and box_h <= 55:
                stars |= labels == label
        # Certains ciels exportent la lune et des étoiles bleues très fines,
        # dont seuls les coeurs ont une luminance plus basse. Ce filet de
        # secours ne prend que des ponctuels (8×8 px maximum), jamais une
        # masse de nuage. Il évite une timeline "étoiles" figée autour de la
        # lune dans cette variante.
        if count - 1 <= 6:
            faint = ceiling & (high > 165) & (r > 60) & (g > 90) & ((high - low) < 145)
            f_count, f_labels, f_stats, _ = cv2.connectedComponentsWithStats(faint.astype("uint8"), 8)
            for label in range(1, f_count):
                _, _, box_w, box_h, area = f_stats[label]
                if box_w <= 8 and box_h <= 8 and area <= 28:
                    stars |= f_labels == label
        # Les astres sont prioritaires sur les nuages : la lune reste donc
        # fixe dans son plan plutôt que de défiler avec une nappe blanche.
        cloud &= ~stars
    else:
        stars = raw_astres
    # Les scènes qui montrent effectivement des nuages gardent cette opération
    # séparée ; la prairie est volontairement dégagée dans ses deux ambiances.
    if expect_clouds:
        assert cloud.any(), f"Nuages introuvables pour {mode}"
    if mode == "nuit":
        assert stars.any(), "Astres nocturnes introuvables"
    return cloud, stars


def exclusive(*proposals: np.ndarray) -> list[np.ndarray]:
    """Rend les plans de terrain disjoints ; le ciel conserve le reliquat."""
    used = np.zeros(proposals[0].shape, dtype=bool)
    outputs: list[np.ndarray] = []
    for proposal in proposals:
        current = proposal & ~used
        outputs.append(current)
        used |= current
    return outputs


def terrain_masks(scene: str, image: Image.Image) -> list[np.ndarray]:
    a = np.asarray(image.convert("RGBA"))
    rgb, (h, w) = a[:, :, :3], a.shape[:2]
    yy, xx = np.indices((h, w))
    greens, flowers = green(rgb), red_or_pink(rgb)
    blue_water = (rgb[:, :, 2].astype(np.int16) > rgb[:, :, 0].astype(np.int16) + 18) & (rgb[:, :, 1] > rgb[:, :, 0] - 5)
    if scene == "cascades":
        water = blue_water & (yy > h * .22)
        island_zone = mask_polygon([
            (round(w*.19), round(h*.07)), (round(w*.81), round(h*.07)), (round(w*.88), round(h*.33)),
            (round(w*.73), round(h*.62)), (round(w*.50), round(h*.68)), (round(w*.25), round(h*.62)),
            (round(w*.12), round(h*.34)),
        ], (w, h))
        island = island_zone & ~water
        vegetation = greens & ((yy > h*.53) | (xx < w*.20) | (xx > w*.80)) & ~water
        return exclusive(water, island, vegetation)
    if scene == "prairie_maritime":
        # La mer occupe une bande étroite sous les montagnes ; le ciel bleu
        # et la voûte nocturne doivent rester dans 00_ciel / 01_astres.
        water = blue_water & (yy >= h * .13) & (yy < h * .31)
        rock_zone = (((xx < w*.30) | (xx > w*.70)) & (yy > h*.10) & (yy < h*.90)) | ((yy > h*.76) & ((xx < w*.22) | (xx > w*.78)))
        rocks = rock_zone & ~greens
        land = yy > h*.22
        plants = (greens | flowers) & land & ~rocks & ~water
        terrain = land & ~plants & ~rocks & ~water
        return exclusive(water, rocks, terrain, plants)
    if scene == "cap_cotier":
        # L'océan débute sous la ligne d'horizon ; ne pas voler la lune et les
        # nuages situés à droite dans le plan marin.
        water = blue_water & (yy >= h*.26) & (xx > w*.55)
        house = mask_polygon([
            (round(w*.34), round(h*.23)), (round(w*.57), round(h*.23)), (round(w*.62), round(h*.36)),
            (round(w*.61), round(h*.65)), (round(w*.51), round(h*.70)), (round(w*.34), round(h*.66)),
            (round(w*.29), round(h*.42)),
        ], (w, h))
        land = mask_polygon([(0, round(h*.33)), (round(w*.63), round(h*.33)), (round(w*.68), round(h*.51)),
                             (round(w*.61), h), (0, h)], (w, h))
        plants = greens & (land | (xx < w*.26)) & ~house & ~water
        terrain = land & ~plants & ~house & ~water
        return exclusive(water, terrain, house, plants)
    raise ValueError(scene)


def cut(source: np.ndarray, mask: np.ndarray) -> Image.Image:
    pixels = np.zeros_like(source)
    pixels[mask] = source[mask]
    return Image.fromarray(pixels, "RGBA")


def make_layers(scene: str, image: Image.Image, mode: str) -> list[Image.Image]:
    """Reconstitue exactement l'image 0, puis laisse les deux plans atmosphériques évoluer."""
    source = np.asarray(image.convert("RGBA"))
    static = terrain_masks(scene, image)
    occupied = np.logical_or.reduce(static)
    clouds, stars = atmosphere_masks(image, mode, expect_clouds=scene != "prairie_maritime")
    if scene == "prairie_maritime":
        # Les deux layouts de prairie, jour comme nuit, ont un ciel dégagé :
        # le plan reste disponible et transparent, sans faux nuage à animer.
        clouds.fill(False)
    # La détection chromatique de nuages peut aussi accrocher une écume, une
    # cascade ou un rocher clair dans la moitié haute. Les plans de relief,
    # d'eau et de végétation sont prioritaires : un nuage ne porte jamais un
    # élément de décor terrestre.
    clouds &= ~occupied
    stars &= ~occupied
    if scene != "prairie_maritime":
        assert clouds.any(), f"Nuages supprimés par la séparation sémantique : {scene}/{mode}"
    if mode == "nuit":
        assert stars.any(), f"Astres supprimés par la séparation sémantique : {scene}/{mode}"
    animated = clouds | stars
    # Le ciel sous les éléments mobiles est inpainté. À l'image 0, les PNG
    # originaux se superposent exactement sur ce fond ; après déplacement les
    # nuages découvrent un ciel continu, au lieu d'un trou transparent.
    background = source.copy()
    fill = cv2.inpaint(source[:, :, :3], (animated.astype("uint8") * 255), 3, cv2.INPAINT_TELEA)
    background[animated, :3] = fill[animated]
    background[occupied & ~animated] = 0
    background = Image.fromarray(background, "RGBA")
    layers = [background, cut(source, stars), cut(source, clouds)] + [cut(source, mask) for mask in static]
    initial = Image.new("RGBA", image.size)
    for layer in layers:
        initial.alpha_composite(layer)
    assert np.array_equal(np.asarray(initial), source), f"Recomposition initiale altérée : {scene}/{mode}"
    return layers


def data_uri(image: Image.Image) -> str:
    data = io.BytesIO()
    image.convert("RGBA").save(data, format="WEBP", lossless=True, method=4)
    return "data:image/webp;base64," + base64.b64encode(data.getvalue()).decode("ascii")


def data_uri_path(path: Path) -> str:
    with Image.open(path) as opened:
        return data_uri(opened)


def preview_html(scenes: list[dict]) -> str:
    payload = json.dumps(scenes, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Extérieurs PMD — layouts animés</title><style>
:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#101522;color:#f7efd7}}*{{box-sizing:border-box}}body{{margin:0;min-width:300px}}main{{max-width:1180px;margin:auto;padding:22px 16px 34px}}h1{{margin:0;font-size:clamp(1.35rem,4vw,2rem)}}p,small{{line-height:1.5;color:#c9d3cf}}.controls,#layers{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}button,label{{border:1px solid #60718a;border-radius:8px;padding:8px 10px;background:#232d41;color:inherit;font:inherit}}button{{cursor:pointer}}button[aria-pressed=true]{{background:#dbc779;color:#172034;font-weight:700}}label{{display:flex;gap:7px;align-items:center;font-size:.92rem}}#stage{{background:#080c15;border:1px solid #485670;border-radius:12px;padding:14px;overflow:auto}}canvas{{display:block;margin:auto;image-rendering:pixelated;image-rendering:crisp-edges;max-width:none}}</style></head><body><main><h1>Layouts extérieurs PMD — calques animés</h1><p>Les nuages défilent ; les étoiles scintillent la nuit. Masquez un plan pour vérifier son indépendance.</p><div class="controls" id="scenes"></div><div class="controls" id="modes"></div><div class="controls"><button id="motion" type="button"></button><span id="time"></span></div><section id="stage"><canvas id="map"></canvas></section><div id="layers"></div><small id="note"></small></main><script>
'use strict';const DATA={payload},C=document.querySelector('#map'),X=C.getContext('2d'),I={{}},A=document.createElement('canvas'),AX=A.getContext('2d'),G=document.createElement('canvas'),GX=G.getContext('2d');let si=0,mode='jour',frame=0,play=!matchMedia('(prefers-reduced-motion:reduce)').matches,last=performance.now(),visible=[];function load(u){{if(I[u])return Promise.resolve(I[u]);return new Promise((ok,no)=>{{let q=new Image;q.onload=()=>{{I[u]=q;ok(q)}};q.onerror=no;q.src=u}})}}async function paint(){{let s=DATA[si],v=s.variants[mode],sources=v.layers.concat(v.starGroups?[v.starGroups]:[]);await Promise.all(sources.map(load));X.clearRect(0,0,C.width,C.height);for(let n=0;n<v.layers.length;n++){{if(!visible[n])continue;let op=v.operations[n],q=I[v.layers[n]];if(op==='cloud'){{let dx=-(frame%24);X.drawImage(q,dx,0);X.drawImage(q,dx+C.width,0)}}else if(op==='stars'){{A.width=G.width=C.width;A.height=G.height=C.height;AX.clearRect(0,0,C.width,C.height);GX.clearRect(0,0,C.width,C.height);AX.drawImage(q,0,0);GX.drawImage(I[v.starGroups],0,0);let px=AX.getImageData(0,0,C.width,C.height),groups=GX.getImageData(0,0,C.width,C.height).data,levels=v.starLevels[frame%24];for(let a=3,g=0;a<px.data.length;a+=4,g+=4)px.data[a]=Math.floor((px.data[a]*levels[groups[g]]+127)/255);AX.putImageData(px,0,0);X.drawImage(A,0,0)}}else X.drawImage(q,0,0)}}document.querySelector('#time').textContent='Image '+(frame+1)+' / 24';}}function controls(){{let s=DATA[si],a=document.querySelector('#scenes'),b=document.querySelector('#modes'),l=document.querySelector('#layers');a.replaceChildren();b.replaceChildren();l.replaceChildren();DATA.forEach((q,i)=>{{let z=document.createElement('button');z.textContent=q.nom;z.setAttribute('aria-pressed',String(i===si));z.onclick=()=>{{si=i;frame=0;visible=DATA[si].layers.map(()=>true);draw()}};a.append(z)}});for(let k of ['jour','nuit']){{let z=document.createElement('button');z.textContent=k==='jour'?'☀ Jour':'☾ Nuit';z.setAttribute('aria-pressed',String(k===mode));z.onclick=()=>{{mode=k;frame=0;draw()}};b.append(z)}}s.layers.forEach((q,i)=>{{let z=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=visible[i];c.onchange=()=>{{visible[i]=c.checked;paint()}};z.append(c,document.createTextNode(q));l.append(z)}});let m=document.querySelector('#motion');m.textContent=play?'❚❚ Pause':'▶ Animer';m.setAttribute('aria-pressed',String(play));m.onclick=()=>{{play=!play;last=performance.now();controls();paint()}};document.querySelector('#note').textContent=s.description+' · '+s.size.join(' × ')+' px · 24 phases de 250 ms';}}function draw(){{let s=DATA[si];C.width=s.size[0];C.height=s.size[1];let max=document.querySelector('#stage').clientWidth-28,scale=Math.min(1,max/C.width);C.style.width=Math.floor(C.width*scale)+'px';C.style.height=Math.floor(C.height*scale)+'px';controls();paint()}}function tick(now){{if(play&&now-last>250){{frame=(frame+Math.floor((now-last)/250))%24;last=now;paint()}}requestAnimationFrame(tick)}}visible=DATA[0].layers.map(()=>true);draw();requestAnimationFrame(tick);</script></body></html>"""


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    selectors: dict[str, Callable[[str, Image.Image, str], list[Image.Image]]] = {scene["id"]: make_layers for scene in SCENES}
    manifest_scenes, preview_scenes = [], []
    for scene in SCENES:
        root = OUT / scene["id"]
        if root.exists():
            shutil.rmtree(root)
        definitions = [{"id": layer_id, "nom": label, "anime": animated} for layer_id, label, animated in scene["layers"]]
        manifest = {"id": scene["id"], "nom": scene["nom"], "dimensions": list(scene["dimensions"]), "grille_px": 8,
                    "animation": {"frames": FRAMES, "duree_image_ms": DURATION, "duree_boucle_ms": FRAMES * DURATION},
                    "base_start": 3, "calques": definitions, "fichiers": {}}
        variants = {}
        for mode, native_name in scene["natives"].items():
            native = load(NATIVES / native_name, scene["dimensions"])
            layers = selectors[scene["id"]](scene["id"], native, mode)
            assert len(layers) == len(definitions)
            specs = {}
            if layers[2].getbbox():
                specs["02_nuages"] = {"kind": "scroll", "period": FRAMES, "prefix": "nuages"}
            if mode == "nuit":
                specs["01_astres"] = stars_spec(layers[1], root)
            files = export_variant(root, mode, definitions, layers, specs, scene["dimensions"], FRAMES, 3, [], scene["id"])
            actual = compose([AnimatedLayer(layer, specs.get(defn["id"]), root) for defn, layer in zip(definitions, layers)], scene["dimensions"], 0)
            assert np.array_equal(np.asarray(actual), np.asarray(native)), f"PNG initial différent : {scene['id']}/{mode}"
            manifest["fichiers"][mode] = {"native": f"../../source/references_exterieures/natives/{native_name}", **files}
            variants[mode] = {"layers": [data_uri(layer) for layer in layers],
                              "operations": ["stars" if definitions[index]["id"] in specs and specs[definitions[index]["id"]]["kind"] == "stars" else "cloud" if definitions[index]["id"] in specs and specs[definitions[index]["id"]]["kind"] == "scroll" else "fixed" for index in range(len(layers))],
                              "starGroups": data_uri_path(root / specs["01_astres"]["groups"]) if "01_astres" in specs else None,
                              "starLevels": specs["01_astres"]["levels"] if "01_astres" in specs else None}
            moving = "nuages animés" if "02_nuages" in specs else "ciel dégagé (plan nuages transparent)"
            print(f"{scene['id']} {mode} : {len(layers)} plans, {moving}" + (", étoiles scintillantes" if mode == "nuit" else ""))
        (root / "kit.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest_scenes.append(manifest)
        preview_scenes.append({"nom": scene["nom"], "description": scene["description"], "size": list(scene["dimensions"]),
                               "layers": [layer["nom"] for layer in definitions], "variants": variants})
    kit = {"version": 2, "titre": "Layouts extérieurs PMD — générés, multicouches et animés", "grille_px": 8,
           "animation": {"frames": FRAMES, "duree_image_ms": DURATION, "duree_boucle_ms": FRAMES * DURATION},
           "methode": "Rendus générés, séparation en calques, nuages en défilement et étoiles nocturnes scintillantes.",
           "provenance": "../source/references_exterieures/provenance.json", "scenes": manifest_scenes}
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PREVIEW.write_text(preview_html(preview_scenes), encoding="utf-8")
    print("Export complet : 3 scènes, jour/nuit, calques PNG, Aseprite/Tiled animés et aperçu autonome.")
    return kit


if __name__ == "__main__":
    build()
