"""Image générée -> natif indexé -> masques -> calques -> exports, comme le kit initial.

Ce fichier ne dessine aucun décor. Les polygones ne servent qu'à sélectionner
les pixels d'une génération existante. --preparer fige les masques une fois ;
les reconstructions suivantes consomment ces masques, sans segmenter à nouveau.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import sys
import struct
import zlib
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_fill_holes, binary_dilation, distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "source"))
from rebuild_kit import ase, png, night, cut

HERE = Path(__file__).parent
RAW = HERE / "galerie_est_ouest_retenue.png"
NATIVE = HERE / "natifs/galerie_est_ouest.png"
MASK = HERE / "masques/galerie_est_ouest.png"
OUT = ROOT / "tilesheets/generes/galerie_est_ouest"
SIZE = (648, 432)
LAYERS = [
    ("00_exterieur", "Extérieur — pas de fenêtre ici"),
    ("01_sol", "Sol et continuité des passages"),
    ("02_structure", "Murs et charpente générés"),
    ("03_cadres_fenetres", "Cadres de fenêtres — vide"),
    ("04_tableaux", "Tableaux — vide"),
    ("05_porte_maitre", "Porte — vide"),
    ("06_decorations", "Végétation haute extraite"),
    ("07_objets", "Objets — vide"),
    ("08_ombres_acces", "Ombres d’accès extraites"),
    ("09_eclairage_fixe", "Éclairage ajouté — vide"),
    ("10_bordure_avant", "Bordure, racines et feuillage avant"),
]


def save_json(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def load_base():
    a = np.array(Image.open(NATIVE).convert("RGBA"))
    key = (a[:, :, 0] == 255) & (a[:, :, 1] == 0) & (a[:, :, 2] == 255)
    a[key] = 0
    return Image.fromarray(a)


def polygon(points):
    # Un masque de sélection, jamais de la peinture dans l'image du décor.
    out = Image.new("L", SIZE)
    ImageDraw.Draw(out).polygon(points, fill=255)
    return np.array(out) > 0


def prepare():
    raw = Image.open(RAW).convert("RGB").resize(SIZE, Image.Resampling.NEAREST)
    a = np.array(raw)
    r, g, b = [a[:, :, k].astype(int) for k in range(3)]
    key = (r > g + 45) & (b > g + 35) & (b > 75)
    # 255 couleurs pour le dessin et une entrée #FF00FF réservée au détourage.
    work = a.copy()
    work[key] = (151, 87, 36)
    q = Image.fromarray(work).quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indices = np.array(q)
    indices[key] = 255
    nat = Image.fromarray(indices).convert("P")
    nat.putpalette(q.getpalette()[:765] + [255, 0, 255])
    NATIVE.parent.mkdir(parents=True, exist_ok=True)
    nat.save(NATIVE, optimize=True)
    im = load_base()
    a = np.array(im)
    alpha = a[:, :, 3] > 0
    yy, xx = np.indices(alpha.shape)
    # Zone admissible relevée sur le natif. La coupe basse suit l'intérieur du chant.
    roi = polygon([(0, 240), (40, 240), (159, 175), (493, 175), (610, 242), (647, 241),
                   (647, 312), (586, 312), (582, 302), (567, 315), (543, 329),
                   (514, 340), (472, 349), (430, 355), (385, 357), (326, 358),
                   (266, 357), (217, 355), (175, 349), (135, 340), (106, 329),
                   (80, 314), (63, 299), (61, 312), (0, 312)])
    ellipse = ((xx - 324) / 292) ** 2 + ((yy - 270) / 88) ** 2 < 1
    gc = np.full(alpha.shape, cv2.GC_BGD, np.uint8)
    gc[alpha & roi] = cv2.GC_PR_BGD
    gc[alpha & roi & ellipse] = cv2.GC_PR_FGD
    core = (abs(xx - 324) < 170) & (abs(yy - 267) < 41) & roi & alpha
    gc[core] = cv2.GC_FGD
    # Les lames visibles aux deux extrémités font partie du même plan de sol.
    exits = alpha & (yy >= 244) & (yy <= 309) & ((xx < 44) | (xx > 609))
    gc[exits] = cv2.GC_FGD
    cv2.setRNGSeed(2718)
    cv2.grabCut(a[:, :, :3].copy(), gc, None, np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_MASK)
    floor = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)) & roi & alpha
    regions, _ = label(floor)
    floor = regions == regions[267, 324]
    floor = binary_fill_holes(floor) & roi & alpha
    # Préserver les traits sombres à l'intérieur de la surface sélectionnée.
    for x in range(SIZE[0]):
        ys = np.flatnonzero(floor[:, x])
        if len(ys):
            floor[ys.min():ys.max() + 1, x] |= roi[ys.min():ys.max() + 1, x] & alpha[ys.min():ys.max() + 1, x]
    # Inclure les fines lames supérieures des sorties, pas une bande de sol
    # abandonnée sur le calque de structure par le seuil de GrabCut.
    floor |= alpha & ((xx < 36) | (xx > 615)) & (yy >= 238) & (yy <= 309)
    front = alpha & ~floor & (yy >= 290)
    r, g, b = [a[:, :, k].astype(float) for k in range(3)]
    green = alpha & (g > r * 1.035) & (g > b * 1.3) & (g > 27) & (yy < 170)
    decor = binary_dilation(green, iterations=1) & alpha & (yy < 170)
    walls = alpha & ~floor & ~front & ~decor
    semantic = np.zeros(alpha.shape, np.uint8)
    for value, mask in [(1, floor), (2, walls), (6, decor), (10, front)]:
        semantic[mask] = value
    assert np.array_equal(semantic > 0, alpha)
    MASK.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(semantic).save(MASK, optimize=True)
    save_json({"source_generee": str(RAW.relative_to(ROOT)), "native": str(NATIVE.relative_to(ROOT)),
               "dimensions": list(SIZE), "palette_native": "255 couleurs + magenta réservé", "grille": 8,
               "masque": str(MASK.relative_to(ROOT)), "etiquettes": {"0": "transparence", "1": "sol", "2": "murs", "6": "végétation haute", "10": "bordure avant"},
               "methode": "Normalisation du natif, détourage, GrabCut guidé et sélection de zones ; aucun décor peint par script.",
               "masques_figes": True}, HERE / "methode_galerie.json")


def layer_images():
    im = load_base()
    a = np.array(im)
    s = np.array(Image.open(MASK))
    h, w = s.shape
    assert (w, h) == SIZE and np.array_equal(s > 0, a[:, :, 3] > 0)
    yy, xx = np.indices(s.shape)
    # Même principe algébrique que l'ancien agent : isoler une part des pixels
    # foncés des accès, avec compensation sous-jacente. Aucune ombre nouvelle.
    region = ((xx < w * .25) | (xx > w * .75)) & (yy > h * .40) & (yy < h * .79)
    # Masque adapté à cette image : ne pas extraire toute une boîte rectangulaire
    # de grain sombre. Seule la bande au contact des retours est décomposée.
    region &= distance_transform_edt(s != 2) <= 8
    lum = .2126 * a[:, :, 0] + .7152 * a[:, :, 1] + .0722 * a[:, :, 2]
    sh = np.rint(np.clip((153 - lum) / 190, 0, .32) * 255).astype("uint8")
    sh[~(region & (s == 1))] = 0
    sh = np.minimum(sh, 255 - a[:, :, :3].max(axis=2))
    sh[sh < 6] = 0
    unsh = a.copy()
    unsh[:, :, :3] = np.rint(a[:, :, :3].astype(float) * 255 / (255 - sh.astype(float))[:, :, None]).clip(0, 255).astype("uint8")
    unsh[s == 0] = 0
    base = Image.fromarray(unsh)
    layers = [Image.new("RGBA", SIZE) for _ in LAYERS]
    for i in [1, 2, 6, 10]:
        layers[i] = cut(base, s == i)
    shadow = np.zeros_like(a)
    shadow[:, :, 3] = sh
    layers[8] = Image.fromarray(shadow)
    reconstructed = Image.new("RGBA", SIZE)
    for layer in layers:
        reconstructed.alpha_composite(layer)
    error = int(np.abs(np.array(reconstructed).astype(int) - a.astype(int)).max())
    assert error <= 1, error
    return layers, error


def export_tiled(path, images, mode):
    w, h = SIZE
    cols, rows = w // 8, h // 8
    count = cols * rows
    sets, layers = [], []
    for i, ((name, title), im) in enumerate(zip(LAYERS, images)):
        a = np.array(im)
        occupied = a[:, :, 3].reshape(rows, 8, cols, 8).max((1, 3)) > 0
        first = i * count + 1
        data = np.arange(first, first + count, dtype=np.uint32).reshape(rows, cols)
        data[~occupied] = 0
        sets.append({"firstgid": first, "name": name, "tilewidth": 8, "tileheight": 8, "tilecount": count,
                     "columns": cols, "image": f"calques/{mode}/{name}.png", "imagewidth": w, "imageheight": h, "spacing": 0, "margin": 0})
        layers.append({"id": i + 1, "name": title, "type": "tilelayer", "width": cols, "height": rows,
                       "x": 0, "y": 0, "opacity": 1, "visible": True, "data": data.ravel().tolist()})
    obj = {"type": "map", "version": "1.10", "orientation": "orthogonal", "renderorder": "right-down", "width": cols,
           "height": rows, "tilewidth": 8, "tileheight": 8, "infinite": False, "nextlayerid": 12, "nextobjectid": 1, "tilesets": sets, "layers": layers}
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def export():
    OUT.mkdir(parents=True, exist_ok=True)
    day, error = layer_images()
    (OUT / "natif_magenta.png").write_bytes(NATIVE.read_bytes())
    outputs = {}
    for mode in ["jour", "nuit"]:
        body = day if mode == "jour" else [im.copy() if i == 8 else night(im) for i, im in enumerate(day)]
        folder = OUT / "calques" / mode
        folder.mkdir(parents=True, exist_ok=True)
        composite = Image.new("RGBA", SIZE)
        for (name, _), im in zip(LAYERS, body):
            png(im, folder / (name + ".png"))
            composite.alpha_composite(im)
        png(composite, OUT / f"base_{mode}_transparente.png")
        magenta = Image.new("RGBA", SIZE, (255, 0, 255, 255))
        magenta.alpha_composite(composite)
        png(magenta, OUT / f"base_{mode}_magenta.png")
        dark = Image.new("RGBA", SIZE, (23, 16, 29, 255))
        dark.alpha_composite(composite)
        png(dark, OUT / f"apercu_{mode}.png")
        ase(OUT / f"galerie_{mode}.aseprite", [(title, im) for (_, title), im in zip(LAYERS, body)], SIZE)
        export_tiled(OUT / f"galerie_{mode}.tmj", body, mode)
        outputs[mode] = {"base": f"base_{mode}_transparente.png", "magenta": f"base_{mode}_magenta.png", "apercu": f"apercu_{mode}.png",
                         "aseprite": f"galerie_{mode}.aseprite", "tiled": f"galerie_{mode}.tmj",
                         "calques": [f"calques/{mode}/{name}.png" for name, _ in LAYERS]}
    manifest = {"id": "galerie_est_ouest", "methode": "image générée aplatie puis calques reconstruits",
                "reference_workflow": "source/rebuild_kit.py à la révision 6c4ac5a", "dimensions": list(SIZE), "grille": 8,
                "source_brute": str(RAW.relative_to(ROOT)), "sha256_source": hashlib.sha256(RAW.read_bytes()).hexdigest(),
                "natif": str(NATIVE.relative_to(ROOT)), "calques": [{"id": name, "nom": title, "non_vide": bool(im.getbbox())} for (name, title), im in zip(LAYERS, day)],
                "fichiers": outputs, "ecart_max_recomposition_natif": error,
                "statut": "Premier module généré traité ; les huit autres ne sont pas remplacés",
                "limites": ["Les calques sont extraits après génération, pas nativement créés par le générateur.",
                            "La végétation masquée peut laisser voir de la transparence : les surfaces cachées ne sont pas inventées.",
                            "Une partie des ombres reste intégrée aux textures ; ce n’est pas un matériau entièrement rééclairable.",
                            "Les cellules Tiled recomposent le dessin ; ce n’est pas un tileset de construction universel."]}
    save_json(manifest, OUT / "kit.json")
    build_preview(manifest)
    print("Méthode d’origine : natif généré 648×432, 11 calques dont", sum(bool(im.getbbox()) for im in day), "non vides, jour/nuit, Aseprite et Tiled 8 px ; écart", error)


def build_preview(manifest):
    def data(file):
        return "data:image/png;base64," + base64.b64encode((OUT / file).read_bytes()).decode()
    images = {mode: {"base": data(f["base"]), "layers": [data(p) for p in f["calques"]]} for mode, f in manifest["fichiers"].items()}
    payload = json.dumps({"images": images, "layers": manifest["calques"]}, ensure_ascii=False, separators=(",", ":"))
    html = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Galerie générée — méthode du kit d’origine</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f0e5;color:#304335;font:14px/1.6 system-ui,sans-serif}main{max-width:1210px;margin:auto;padding:26px 20px}h1{font:500 34px/1.15 Georgia,serif;margin:8px 0 15px}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:10px;color:#967230}p{color:#667360}button,select{font:inherit;border:1px solid #cad2bd;border-radius:5px;background:#fffdf2;color:#304335;padding:7px 10px;cursor:pointer}button.active{background:#304b38;color:#fffbe4}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}.work{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:18px}.scene,aside{border:1px solid #d8decc;border-radius:8px;background:#fafaf2;overflow:hidden}.stage{min-height:460px;overflow:auto;display:flex;padding:18px;background:#17101d}canvas{margin:auto;display:block;image-rendering:pixelated;flex:none}.checker{background-color:#e3e8da;background-image:conic-gradient(#f1f2e8 25%,transparent 0 50%,#f1f2e8 0 75%,transparent 0);background-size:24px 24px}.white{background:#ff00ff}aside{padding:18px}h2{font-size:12px;text-transform:uppercase;letter-spacing:.1em;margin:0 0 16px}.layer{display:flex;gap:7px;align-items:center;margin:10px 0;font-size:12px}.empty{opacity:.45}input{accent-color:#486b41}.footer{padding:12px 16px;font-size:11px;display:flex;gap:13px;align-items:center;flex-wrap:wrap}.note{background:#e6ebdb;padding:14px 17px;border-radius:6px;margin-top:20px;color:#57664e;font-size:12px}a{color:#456840;text-underline-offset:3px}.links{display:flex;gap:16px;flex-wrap:wrap;margin:15px 0;font-size:12px}.mini{font-size:11px}.status{font-size:11px;color:#967230}@media(max-width:760px){main{padding:20px 12px}.work{grid-template-columns:minmax(0,1fr)}h1{font-size:28px}.stage{min-height:280px;padding:10px}.toolbar{gap:5px}button{font-size:12px}.layer{margin:10px 0}}</style></head><body><main><div class="eyebrow">Guilde Treehouse / génération → post-traitement → exports</div><h1>La méthode du kit d’origine</h1><p>Une image maîtresse générée, puis un natif indexé et des calques extraits — aucun mur ni parquet dessiné par script.</p><div class="status">Premier module traité : galerie est-ouest · 648 × 432 px · grille 8 px</div><div class="toolbar"><button data-mode="jour" class="active">Jour</button><button data-mode="nuit">Nuit</button><button data-preset="all">Composition</button><button data-preset="1">Sol</button><button data-preset="2">Murs</button><button data-preset="10">Bordure avant</button><button data-preset="6">Végétation haute</button></div><div class="work"><section class="scene"><div id="stage" class="stage"><canvas id="canvas" width="648" height="432" aria-label="Galerie générée et ses calques"></canvas></div><div class="footer"><select id="background" aria-label="Fond"><option value="dark">Fond sombre</option><option value="checker">Transparence</option><option value="white">Contrôle magenta</option></select><label><input id="grid" type="checkbox"> Grille 8 px</label><a id="download" download="galerie.png">PNG affiché</a></div></section><aside><h2>11 emplacements de calques</h2><div id="layers"></div><p class="mini">5 calques contiennent des pixels. Les autres restent réservés et vides, comme dans la structure du kit d’origine.</p><div class="links"><a id="ase">Aseprite</a><a id="tmj">Tiled</a></div></aside></div><div class="note">Les ombres ont été dessinées par le générateur. Une partie est isolée après coup ; l’ambiance et les ombres restantes restent dans les textures. Masquer un élément ne recrée pas ce qui était caché derrière lui.</div><div class="links"><a href="README.md">Méthode et limites</a><a href="natif_magenta.png">Natif magenta</a><a href="kit.json">Métadonnées</a></div><p class="mini">Cette page présente le premier module généré traité. Elle ne prétend pas avoir remplacé les huit autres couloirs/paliers.</p></main><script>
const D=__DATA__,imgs={},$=s=>document.querySelector(s),C=$('#canvas'),ctx=C.getContext('2d');let mode='jour',ready=false;const active=D.layers.map(()=>true);function fit(){const scale=Math.min(1.5,($('#stage').clientWidth-36)/648);C.style.width=648*scale+'px';C.style.height=432*scale+'px'}function draw(){if(!ready)return;C.width=648;C.height=432;ctx.imageSmoothingEnabled=false;if(active.every(Boolean))ctx.drawImage(imgs[mode].base,0,0);else imgs[mode].layers.forEach((im,i)=>{if(active[i])ctx.drawImage(im,0,0)});$('#download').href=C.toDataURL();$('#download').download='galerie_'+mode+'.png';if($('#grid').checked){ctx.strokeStyle='rgba(255,243,175,.22)';ctx.beginPath();for(let x=0;x<648;x+=8){ctx.moveTo(x+.5,0);ctx.lineTo(x+.5,432)}for(let y=0;y<432;y+=8){ctx.moveTo(0,y+.5);ctx.lineTo(648,y+.5)}ctx.stroke()}$('#ase').href='galerie_'+mode+'.aseprite';$('#tmj').href='galerie_'+mode+'.tmj';fit()}function controls(){$('#layers').innerHTML='';D.layers.forEach((r,i)=>{const l=document.createElement('label');l.className='layer'+(r.non_vide?'':' empty');const input=document.createElement('input');input.type='checkbox';input.checked=active[i];input.disabled=!r.non_vide;input.dataset.layer=i;input.onchange=()=>{active[i]=input.checked;draw()};l.append(input,document.createTextNode(r.nom));$('#layers').append(l)})}function load(url){return new Promise((ok,no)=>{let im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=url})}Promise.all(Object.entries(D.images).map(async([m,v])=>{imgs[m]={base:await load(v.base),layers:await Promise.all(v.layers.map(load))}})).then(()=>{ready=true;controls();draw();document.body.dataset.ready='true'});document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(q=>q.classList.toggle('active',q===b));draw()});document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>{active.fill(b.dataset.preset==='all');if(b.dataset.preset!=='all')active[+b.dataset.preset]=true;controls();draw()});$('#background').onchange=e=>{$('#stage').className='stage '+e.target.value};$('#grid').onchange=draw;window.onresize=fit;
</script></body></html>'''
    (OUT / "apercu.html").write_text(html.replace("__DATA__", payload))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparer", action="store_true", help="Normaliser le natif et figer ses masques de sélection")
    args = parser.parse_args()
    if args.preparer:
        prepare()
    export()
