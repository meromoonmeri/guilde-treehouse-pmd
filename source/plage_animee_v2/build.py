"""Plage animee V2 — textures generees par couche + eau en palette cycling.

Entrees :
- 3 textures plein cadre generees (mer, sable, roche), style guide par V1.
- Masques V1 (byte-exacts) pour garder le layout valide et des rives nettes.
- Ecume V1 (geometrie) + vide V1 (byte-identique).

Eau : 1 image indexee (rampe unique de 16, derivee de la texture generee)
+ 16 tables de couleurs en rotation (+1/phase) -> 16 frames, silhouette
inchangee, boucle exacte. Derive vers les rives (x cotes, y bassin nord).
Ecume : 4 niveaux + 16 tables (scintillement), meme horloge. Cycling NOUVEAU
inspire du canon (direction vers les rives), PAS des frames officielles.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import math
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
O = R / "renders/plage_animee_v2"
V1 = R / "renders/plage_arene_generee_v1"
W, H = 456, 480
F, MS = 16, 60  # 16 phases x 60 ms = 0,96 s (rotation +1/phase sur 16)

STATICS = [
    ("02_sable", "Sable de l'arene (texture V2)", "brut_sable.png"),
    ("03_falaises", "Falaises rouges (texture V2)", "brut_roche.png"),
    ("05_rochers", "Rochers (texture V2)", "brut_roche.png"),
    ("06_vide", "Vide hors terrain (V1)", None),
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normaliser(brut: Image.Image) -> np.ndarray:
    s = max(W / brut.width, H / brut.height)
    tmp = brut.resize((round(brut.width * s), round(brut.height * s)), Image.Resampling.LANCZOS)
    x0 = (tmp.width - W) // 2
    y0 = (tmp.height - H) // 2
    return np.array(tmp.crop((x0, y0, x0 + W, y0 + H))).astype(float)


def masque_v1(lid: str) -> np.ndarray:
    with Image.open(V1 / "couches" / f"PlageAreneV1_{lid}.png") as im:
        return np.array(im.convert("RGBA"))[:, :, 3] > 0


def construire():
    (O / "couches").mkdir(parents=True, exist_ok=True)
    (O / "eau" / "mer").mkdir(parents=True, exist_ok=True)
    (O / "eau" / "ecume").mkdir(parents=True, exist_ok=True)
    (O / "scene").mkdir(parents=True, exist_ok=True)
    (O / "review").mkdir(parents=True, exist_ok=True)

    tex_mer = normaliser(Image.open(SRC / "generation/brut_mer.png").convert("RGB"))
    tex_sable = normaliser(Image.open(SRC / "generation/brut_sable.png").convert("RGB"))
    tex_roche = normaliser(Image.open(SRC / "generation/brut_roche.png").convert("RGB"))
    textures = {"brut_sable.png": tex_sable, "brut_roche.png": tex_roche}

    m_mer = masque_v1("01_mer")
    m_sable = masque_v1("02_sable")
    m_fal = masque_v1("03_falaises")
    m_ecu = masque_v1("04_ecume")
    m_roch = masque_v1("05_rochers")
    m_vide = masque_v1("06_vide")

    # --- couches statiques : textures V2 sur masques V1 ---
    couches = {}
    for lid, _label, brut in STATICS:
        if brut is None:  # vide : copie V1 byte-identique
            with Image.open(V1 / "couches" / f"PlageAreneV1_{lid}.png") as im:
                couches[lid] = im.convert("RGBA")
        else:
            m = {"02_sable": m_sable, "03_falaises": m_fal, "05_rochers": m_roch}[lid]
            ref = textures[brut].astype("uint8")
            rgba = np.dstack([ref, np.where(m, 255, 0).astype("uint8")])
            rgba[~m] = 0
            couches[lid] = Image.fromarray(rgba, "RGBA")
        couches[lid].save(O / "couches" / f"PlageAnimeeV2_{lid}.png")

    # --- eau indexee : 2 rampes x 8 niveaux + derive vers les rives ---
    eau = tex_mer[m_mer]
    lum = eau.mean(axis=1)
    yy, xx = np.where(m_mer)
    nord = yy < 150
    coord = np.where(nord, yy, xx).astype(float)
    signe = np.where(nord, 1.0, np.where(xx - W // 2 > 0, -1.0, 1.0))
    # Une seule rampe de 16 : la texture est quasi deux tons plats, deux
    # sous-rampes donneraient une rampe profonde quasi fixe (invisible).
    bords = np.quantile(lum, np.linspace(0, 1, 17))
    lum_q = np.clip(np.searchsorted(bords[1:-1], lum), 0, 15)
    niveau = ((lum_q + signe * (coord // 8)) % 16).astype("uint8")
    index = np.full((H, W), 255, "uint8")
    index[m_mer] = niveau  # 0-15, sombre -> lumineux + derive rives
    # Mode L (pas P sans palette : Pillow reaplatit les valeurs au PNG).
    Image.fromarray(index, "L").save(O / "eau" / "mer_indexee.png")
    # LUT0 en degrade : la texture generee est quasi deux tons plats, donc la
    # mediane par case s'effondrerait (rotation invisible). On echantillonne
    # les extremes de chaque rampe dans l'art et on degrade entre les deux :
    # frame 0 = l'art lisse, frames suivantes = rotation (vagues visibles).
    def grad(pixels, n):
        c0 = np.percentile(pixels, 2, axis=0)
        c1 = np.percentile(pixels, 98, axis=0)
        t = np.linspace(0, 1, n)[:, None]
        return np.round(c0[None, :] + (c1 - c0)[None, :] * t).astype("uint8")
    base = grad(eau, 16)
    luts_mer = []
    for f in range(F):
        luts_mer.append(base[(np.arange(16) + f) % 16])
    frames_mer = []
    for f in range(F):
        rgb = np.zeros((H, W, 3), "uint8")
        rgb[m_mer] = luts_mer[f][index[m_mer]]
        rgba = np.dstack([rgb, np.where(m_mer, 255, 0).astype("uint8")])
        im = Image.fromarray(rgba, "RGBA")
        frames_mer.append(im)
        im.save(O / "eau" / "mer" / f"MerV2_{f:02d}.png")

    # --- ecume : geometrie V1, 4 niveaux, 8 tables (scintillement) ---
    with Image.open(V1 / "couches" / f"PlageAreneV1_04_ecume.png") as im:
        ecu_rgb = np.array(im.convert("RGBA"))[:, :, :3].astype(float)
    fe = ecu_rgb[m_ecu]
    lfe = fe.mean(axis=1)
    bords = np.quantile(lfe, [0, 0.25, 0.5, 0.75, 1])
    niv_e = np.clip(np.searchsorted(bords[1:-1], lfe), 0, 3)
    index_e = np.full((H, W), 255, "uint8")
    index_e[m_ecu] = niv_e
    Image.fromarray(index_e, "L").save(O / "eau" / "ecume_indexee.png")
    base_e = np.zeros((4, 3))
    ce0 = np.percentile(fe, 10, axis=0)  # p10 : ecarte les franges vertes
    ce1 = fe[lfe.argmax()]  # pixel le plus lumineux (blanc franc, pas frange)
    for i in range(4):
        base_e[i] = ce0 + (ce1 - ce0) * i / 3  # degrade sombre -> blanc
    luts_ecu = []
    for f in range(F):
        lut = np.zeros((4, 3), "uint8")
        for i in range(4):
            k = 1 + 0.08 * math.sin(2 * math.pi * (f / F + i / 4))
            lut[i] = np.clip(np.round(base_e[i] * k), 0, 255)
        luts_ecu.append(lut)
    frames_ecu = []
    for f in range(F):
        rgb = np.zeros((H, W, 3), "uint8")
        rgb[m_ecu] = luts_ecu[f][index_e[m_ecu]]
        rgba = np.dstack([rgb, np.where(m_ecu, 255, 0).astype("uint8")])
        im = Image.fromarray(rgba, "RGBA")
        frames_ecu.append(im)
        im.save(O / "eau" / "ecume" / f"EcumeV2_{f:02d}.png")
    (O / "eau" / "palettes_16frames.json").write_text(json.dumps(
        {"mer": [lut.tolist() for lut in luts_mer],
         "ecume": [lut.tolist() for lut in luts_ecu],
         "duree_ms": MS, "boucle": "frame 8 = frame 0 (rotation modulo 8 / sinus exact)"},
        indent=1) + "\n", encoding="utf-8")

    # --- scenes : statiques + eau phase f ---
    scenes = []
    for f in range(F):
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s.alpha_composite(frames_mer[f])
        for lid in ("02_sable", "03_falaises", "05_rochers", "06_vide"):
            s.alpha_composite(couches[lid])
        s.alpha_composite(frames_ecu[f])
        scenes.append(s)
        s.save(O / "scene" / f"scene_{f:02d}.png")
    scenes[0].save(O / "review" / "scene_animee.webp", save_all=True,
                   append_images=scenes[1:], duration=MS, loop=0, lossless=True, method=4)
    pal = scenes[0].convert("RGB").quantize(colors=256)
    gifs = [s.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE) for s in scenes]
    gifs[0].save(O / "review" / "scene_animee.gif", save_all=True,
                 append_images=gifs[1:], duration=MS, loop=0, disposal=1, optimize=False)

    # --- planche : statiques + 8 phases mer + scene f0/f4 ---
    dam = Image.new("RGB", (W, H), (64, 64, 64))
    px = dam.load()
    for y in range(H):
        for x in range(W):
            if (x // 8 + y // 8) % 2:
                px[x, y] = (96, 96, 96)
    vig = []
    for lid in ("02_sable", "03_falaises", "05_rochers", "06_vide"):
        v = dam.copy()
        v.paste(couches[lid], (0, 0), couches[lid])
        vig.append(v)
    tw, th = W // 4, H // 4
    mini = Image.new("RGB", (W, H), (32, 32, 32))
    dam_mini = dam.resize((tw, th))
    for f in range(F):
        v = dam_mini.copy()
        fr = frames_mer[f].resize((tw, th))
        v.paste(fr, (0, 0), fr)
        mini.paste(v, ((f % 4) * tw, (f // 4) * th))
    planche = Image.new("RGB", (W * 4, H * 3), (32, 32, 32))
    for i, v in enumerate(vig):
        planche.paste(v, ((i % 4) * W, 0))
    planche.paste(mini, (0, H))
    planche.paste(scenes[0].convert("RGB"), (W, H))
    planche.paste(scenes[8].convert("RGB"), (2 * W, H))
    planche.paste(scenes[4].convert("RGB"), (0, 2 * H))
    planche.paste(scenes[12].convert("RGB"), (W, 2 * H))
    planche.save(O / "review" / "planche_calques.png")

    # --- ORA : statiques + 8 mer + 8 ecume (f0 visibles) ---
    ora_path = O / "PlageAnimeeV2.ora"
    root = ET.Element("image", {"w": str(W), "h": str(H), "name": ora_path.stem})
    stack = ET.SubElement(root, "stack")
    couches_ora = ([(f"06_vide", couches["06_vide"], True), ("02_sable", couches["02_sable"], True),
                    ("03_falaises", couches["03_falaises"], True),
                    ("05_rochers", couches["05_rochers"], True)]
                   + [(f"01_mer_f{f}", frames_mer[f], f == 0) for f in range(F)]
                   + [(f"04_ecume_f{f}", frames_ecu[f], f == 0) for f in range(F)])
    with zipfile.ZipFile(ora_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        for i, (nom, im, vis) in reversed(list(enumerate(couches_ora))):
            fn = f"data/layer{i}.png"
            ET.SubElement(stack, "layer", {"name": nom, "src": fn, "x": "0", "y": "0",
                                           "opacity": "1.0",
                                           "visibility": "visible" if vis else "hidden",
                                           "composite-op": "svg:src-over"})
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            z.writestr(fn, buf.getvalue())
        z.writestr("stack.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True))
        buf = io.BytesIO()
        scenes[0].save(buf, format="PNG")
        z.writestr("mergedimage.png", buf.getvalue())

    def uri(im: Image.Image) -> str:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    donnees = {"largeur": W, "hauteur": H, "frames": F, "ms": MS,
               "statiques": [{"id": lid, "uri": uri(couches[lid])}
                             for lid in ("06_vide", "02_sable", "03_falaises", "05_rochers")],
               "mer": [uri(im) for im in frames_mer],
               "ecume": [uri(im) for im in frames_ecu]}
    gabarit = (SRC / "viewer.html").read_text(encoding="utf-8")
    (R / "apercu_plage_animee_v2.html").write_text(
        gabarit.replace("__DATA__", json.dumps(donnees)), encoding="utf-8")

    (O / "manifest.json").write_text(json.dumps({
        "id": "plage_animee_v2",
        "methode": "3 textures generees (mer/sable/roche) sur masques V1 + eau "
                   "indexee 2x8 + ecume 4 niveaux, 8 LUTs ; PAS des frames officielles",
        "taille": [W, H], "grille_px": 8, "frames": F, "duree_ms": MS,
        "cycle_ms_total": F * MS,
        "sha256": {p.name: sha256(p) for p in
                   [SRC / "generation/brut_mer.png", SRC / "generation/brut_sable.png",
                    SRC / "generation/brut_roche.png"]},
        "runtime_PMDO": "NON TESTE", "art_approuve": False}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"plage animee V2 : {F} phases x {MS} ms, textures V2, eau indexee 16 couleurs")


if __name__ == "__main__":
    construire()
