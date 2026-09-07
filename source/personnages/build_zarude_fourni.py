#!/usr/bin/env python3
"""Zarude — intégration du sprite fourni par l'utilisateur (`IMG_4840.png`) au format SpriteCollab.

La planche fournie est une feuille 256 × 256 : **4 orientations × 4 images**, cases de 64 × 64,
17 couleurs, alpha 0/255. Elle est plus fine que le Zarude dessiné pièce par pièce dans
`personnages/zarude/` — on la garde donc comme **dessin de référence**, et le travail consiste à
la mettre au format du jeu sans en repeindre le style.

Ce qui est fait, dans l'ordre :

1. **Lecture de la planche.** Les quatre lignes sont : de face, de profil (tournée vers la gauche),
   son miroir exact (vers la droite) et de dos. Les quatre colonnes sont un cycle de marche : image
   0 et 2 sont deux appuis distincts, 1 et 3 sont ces mêmes appuis abaissés de 2 px. Chaque case est
   recadrée sur son contenu et son **ancre au sol** est calculée (milieu de la silhouette, dernière
   ligne opaque), ce qui remplace le pixel blanc absent de la planche d'origine.
2. **Palette ramenée à 15 couleurs.** Le SpriteBot en refuse davantage. Les deux teintes les plus
   rares (16 et 32 pixels sur 24 000) sont rabattues sur leur plus proche voisine ; la différence
   n'est pas visible et rien d'autre n'est modifié. Le détail est écrit dans `kit.json`.
3. **Huit directions.** Le dessin n'en donne que quatre. Les diagonales reprennent le profil du bon
   côté, comme le font les sprites officiels à quatre vues : Bas-droite / Haut-droite = profil droit,
   Bas-gauche / Haut-gauche = profil gauche. C'est une limite du dessin fourni, pas un choix ; elle
   est signalée dans le README.
4. **Squelette d'animation.** Les cadences, les cases, les déplacements d'ancre et les créneaux
   `<Index>` sont relus tels quels sur **Rillaboom #0812** (même carrure, déjà utilisé pour le Zarude
   dessiné, § 6 de METHODE_SPRITES_PMD.md). Chaque image d'animation choisit une des quatre poses
   fournies selon un plan explicite, et c'est l'ancre du squelette qui porte l'élan, le bond, la
   secousse et le cercle de Swing.

Sortie : `personnages/zarude_fourni/`, dossier SpriteCollab complet et importable dans SkyTemple.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                     # noqa: E402
from rebuild_kit import night              # noqa: E402

SOURCE = ROOT / "source" / "personnages" / "reference" / "zarude_fourni.png"
SKELETON = ROOT / "source" / "personnages" / "reference" / "0812"     # Rillaboom
OUT = ROOT / "personnages" / "zarude_fourni"
TILE = 64
MAX_COLOURS = 15

# Lignes de la planche fournie.
FRONT, PROFILE_L, PROFILE_R, BACK = 0, 1, 2, 3
# Direction SpriteCollab -> (ligne de la planche, miroir horizontal)
DIR_SOURCE = {
    0: (FRONT, False),        # Bas
    1: (PROFILE_R, False),    # Bas-droite  — profil droit, faute de vue diagonale
    2: (PROFILE_R, False),    # Droite
    3: (PROFILE_R, False),    # Haut-droite
    4: (BACK, False),         # Haut
    5: (PROFILE_L, False),    # Haut-gauche
    6: (PROFILE_L, False),    # Gauche
    7: (PROFILE_L, False),    # Bas-gauche
}
# Les quatre poses fournies : 0 et 2 = appuis, 1 et 3 = les mêmes abaissés de 2 px.
POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_DOWN_B = 0, 1, 2, 3

# Plan d'animation : pour chaque animation du squelette, la pose de chaque image.
# Il n'invente aucune cadence : seul le choix de pose est ici, le temps vient de Rillaboom.
FRAME_PLAN = {
    "Idle":   [POSE_UP_A],
    "Walk":   [POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_DOWN_B],
    "Sleep":  [POSE_DOWN_A, POSE_DOWN_B],
    "Hurt":   [POSE_DOWN_A, POSE_DOWN_B],
    "Attack": [POSE_UP_A, POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_UP_B, POSE_UP_B,
               POSE_DOWN_B, POSE_UP_B, POSE_DOWN_B, POSE_UP_B, POSE_DOWN_B, POSE_UP_A, POSE_UP_A],
    "Shoot":  [POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_UP_B, POSE_DOWN_B, POSE_UP_B,
               POSE_DOWN_B, POSE_UP_B, POSE_DOWN_B, POSE_UP_A, POSE_UP_A],
    "Sing":   [POSE_UP_A, POSE_UP_A, POSE_DOWN_A, POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_DOWN_B,
               POSE_UP_B, POSE_DOWN_B, POSE_UP_B, POSE_DOWN_B, POSE_UP_B, POSE_DOWN_B,
               POSE_UP_A, POSE_UP_A, POSE_UP_A],
    "Swing":  [POSE_UP_A] * 9,
    "Double": [POSE_UP_A, POSE_DOWN_A, POSE_UP_B, POSE_DOWN_B] * 4,
    "Hop":    [POSE_DOWN_A, POSE_UP_A, POSE_UP_A, POSE_UP_B, POSE_UP_B,
               POSE_UP_B, POSE_UP_B, POSE_UP_A, POSE_DOWN_A, POSE_DOWN_B],
    "Charge": [POSE_UP_A, POSE_DOWN_A] * 5,
    "Rotate": [POSE_UP_A] * 9,
}
# Swing et Rotate tournent d'une direction par image, comme sur la référence.
SPINNING = {"Swing", "Rotate"}


# ---------------------------------------------------------------------------
# Lecture de la planche fournie
# ---------------------------------------------------------------------------
def reduce_palette(sheet: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    """Ramène la planche à 15 couleurs en rabattant les plus rares sur leur voisine la plus proche."""
    out = sheet.copy()
    changes: list[dict] = []
    while True:
        px = out[out[:, :, 3] > 0][:, :3]
        uniq, counts = np.unique(px, axis=0, return_counts=True)
        if len(uniq) <= MAX_COLOURS:
            return out, changes
        order = np.argsort(counts)
        rare = tuple(int(v) for v in uniq[order[0]])
        others = [tuple(int(v) for v in uniq[i]) for i in order[1:]]
        near = min(others, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, rare)))
        mask = (out[:, :, 3] > 0) & np.all(out[:, :, :3] == rare, axis=2)
        out[mask, :3] = near
        changes.append({"de": "#%02x%02x%02x" % rare, "vers": "#%02x%02x%02x" % near,
                        "pixels": int(mask.sum())})


def read_poses() -> dict[tuple[int, int], tuple[np.ndarray, tuple[int, int]]]:
    """(ligne, pose) -> (dessin recadré, ancre au sol relative au coin haut-gauche du recadrage)."""
    sheet = np.array(Image.open(SOURCE).convert("RGBA"))
    assert sheet.shape == (256, 256, 4), sheet.shape
    sheet, changes = reduce_palette(sheet)
    read_poses.changes = changes                                     # type: ignore[attr-defined]
    poses = {}
    for row in range(4):
        for col in range(4):
            cell = sheet[row * TILE:(row + 1) * TILE, col * TILE:(col + 1) * TILE]
            ys, xs = np.nonzero(cell[:, :, 3])
            y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
            crop = cell[y0:y1 + 1, x0:x1 + 1].copy()
            # ancre au sol : milieu des pixels de la dernière ligne opaque du dessin
            last = np.nonzero(crop[-1, :, 3])[0]
            ax = int(round(float(last.mean()))) if len(last) else crop.shape[1] // 2
            poses[(row, col)] = (crop, (ax, crop.shape[0] - 1))
    return poses


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
def build(poses: dict, name: str, skel: P.Anim) -> P.Built:
    plan = FRAME_PLAN[name]
    n = len(skel.durations)
    assert len(plan) == n, f"{name} : {len(plan)} poses pour {n} images"
    rows = skel.dirs
    disp = [skel.frames[0][i].disp for i in range(n)]

    ext_x = ext_y = 0
    for d in range(rows):
        for i, pose in enumerate(plan):
            row, mirror = DIR_SOURCE[(d - i) % 8 if name in SPINNING and rows > 1 else d]
            crop, (ax, ay) = poses[(row, pose)]
            h, w = crop.shape[:2]
            x0, x1 = -ax + disp[i][0], (w - 1 - ax) + disp[i][0]
            y0, y1 = -ay + disp[i][1], disp[i][1]
            ext_x = max(ext_x, abs(x0), abs(x1))
            ext_y = max(ext_y, abs(y0 + 4), abs(y1 - 4))
    # jamais plus petite que la case du squelette : on agrandit par pas de 8 si le dessin déborde
    # (§ 6.6 de METHODE_SPRITES_PMD.md), on ne tasse jamais le dessin.
    fw = max(skel.fw, ((2 * (ext_x + 1) + 7) // 8) * 8)
    fh = max(skel.fh, ((2 * (ext_y + 5) + 7) // 8) * 8)

    built = P.Built(name, skel.index, fw, fh, list(skel.durations), rush=skel.rush,
                    hit=skel.hit, ret=skel.ret,
                    notes="poses du dessin fourni, squelette Rillaboom #0812")
    shadow_template = skel.frames[0][0]
    for d in range(rows):
        cells, anchors = [], []
        for i, pose in enumerate(plan):
            src_dir = (d - i) % 8 if name in SPINNING and rows > 1 else d
            row, mirror = DIR_SOURCE[src_dir]
            crop, (ax, ay) = poses[(row, pose)]
            if mirror:
                crop = crop[:, ::-1].copy()
                ax = crop.shape[1] - 1 - ax
            h, w = crop.shape[:2]
            cx, cy = fw // 2 + disp[i][0], fh // 2 + 4 + disp[i][1]
            cell = np.zeros((fh, fw, 4), np.uint8)
            offs = np.zeros((fh, fw, 4), np.uint8)
            shad = np.zeros((fh, fw, 4), np.uint8)
            px, py = cx - ax, cy - ay
            px, py = max(0, min(px, fw - w)), max(0, min(py, fh - h))
            block = cell[py:py + h, px:px + w]
            mask = crop[:, :, 3] > 0
            block[mask] = crop[mask]

            # repères : centre au tiers supérieur du corps, tête au sommet, mains aux extrémités
            marks = {"center": (0, -h // 3), "head": (0, -h + 4),
                     "lhand": (-w // 3, -h // 3), "rhand": (w // 3, -h // 3)}
            for key, (mx, my) in marks.items():
                x, y = cx + mx, cy + my
                if 0 <= x < fw and 0 <= y < fh:
                    offs[y, x, :3] = np.maximum(offs[y, x, :3], P.MARK_COLOURS[key])
                    offs[y, x, 3] = 255

            gx0, gy0, _, _ = shadow_template.shadow_box
            g = shadow_template.shadow
            if g.size:
                sx, sy = cx + gx0, cy + gy0
                gh, gw = g.shape[:2]
                if 0 <= sx and sx + gw <= fw and 0 <= sy and sy + gh <= fh:
                    sblock = shad[sy:sy + gh, sx:sx + gw]
                    smask = g[:, :, 3] > 0
                    sblock[smask] = g[smask]
            shad[cy, cx] = (255, 255, 255, 255)
            cells.append((cell, offs, shad))
            anchors.append((cx, cy))
        built.cells.append(cells)
        built.anchors.append(anchors)
    return built


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(builts: list[P.Built], path: Path) -> None:
    zoom, blocks = 2, []
    for b in builts:
        n = len(b.durations)
        img = Image.new("RGBA", (n * (b.fw * zoom + 2) + 8, b.fh * zoom + 28), (26, 26, 46, 255))
        d = ImageDraw.Draw(img)
        d.text((4, 4), f"{b.name} — créneau {b.index}, case {b.fw} × {b.fh}, {n} images, "
                       f"{b.dirs} direction(s), durées {b.durations}", fill=(230, 230, 230, 255), font=font(12))
        for i in range(n):
            cell = Image.fromarray(b.cells[0][i][0], "RGBA").resize((b.fw * zoom, b.fh * zoom), Image.NEAREST)
            tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
            tile.alpha_composite(cell)
            img.alpha_composite(tile, (4 + i * (b.fw * zoom + 2), 26))
        blocks.append(img)
    W = max(b.width for b in blocks) + 16
    out = Image.new("RGBA", (W, sum(b.height + 6 for b in blocks) + 56), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), "ZARUDE — SPRITE FOURNI MIS AU FORMAT SPRITECOLLAB (× 2)", fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 34), "Dessin de l'utilisateur (IMG_4840.png), squelette d'animation Rillaboom #0812.",
           fill=(170, 170, 200, 255), font=font(12))
    y = 56
    for b in blocks:
        out.alpha_composite(b, (8, y))
        y += b.height + 6
    out.save(path, optimize=True)


def directions_sheet(walk: P.Built, path: Path) -> None:
    zoom = 4
    cw, ch = walk.fw * zoom + 6, walk.fh * zoom + 22
    out = Image.new("RGBA", (8 * cw + 6, ch + 44), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 8), "Walk image 1 — les huit directions (× 4)", fill=(240, 240, 240, 255), font=font(14))
    d.text((8, 26), "le dessin fourni n'a que quatre vues : les diagonales reprennent le profil du bon côté",
           fill=(170, 170, 200, 255), font=font(11))
    for dd in range(8):
        cell = Image.fromarray(walk.cells[dd][0][0], "RGBA").resize((walk.fw * zoom, walk.fh * zoom), Image.NEAREST)
        tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
        tile.alpha_composite(cell)
        out.alpha_composite(tile, (6 + dd * cw, 44))
        d.text((6 + dd * cw + 4, 44 + walk.fh * zoom + 4), P.DIRECTIONS[dd], fill=(200, 200, 220, 255), font=font(12))
    out.save(path, optimize=True)


def parquet(size: tuple[int, int], zoom: int) -> Image.Image:
    src = ROOT / "salles" / "01_accueil" / "salle_jour.png"
    bg = Image.new("RGBA", size, (150, 104, 52, 255))
    if src.is_file():
        tile = Image.open(src).convert("RGBA").crop((264, 252, 392, 316))
        a = np.array(tile).astype(np.int16)
        a[:, :, :3] = (a[:, :, :3] * 0.72).clip(0, 255)
        tile = Image.fromarray(a.astype(np.uint8), "RGBA")
        tile = tile.resize((tile.width * zoom, tile.height * zoom), Image.NEAREST)
        for y in range(0, size[1], tile.height):
            for x in range(0, size[0], tile.width):
                bg.alpha_composite(tile, (x, y))
    return bg


def gif(builts: dict[str, P.Built], names: list[str], directions: list[int], path: Path, zoom: int = 3) -> None:
    sel = [builts[n] for n in names]
    cw = max(b.fw for b in sel) * zoom + 8
    ch = max(b.fh for b in sel) * zoom + 8
    bg = parquet((len(directions) * cw, len(sel) * ch), zoom)
    total = max(sum(b.durations) for b in sel)
    frames, durs, tick = [], [], 0
    while tick < total:
        img = bg.copy()
        step = total - tick
        for r, b in enumerate(sel):
            t = tick % sum(b.durations)
            acc, idx = 0, 0
            for i, dv in enumerate(b.durations):
                if acc + dv > t:
                    idx, step = i, min(step, acc + dv - t)
                    break
                acc += dv
            for c, dd in enumerate(directions):
                d = dd if b.dirs > 1 else 0
                cell = Image.fromarray(b.cells[d][idx][0], "RGBA").resize((b.fw * zoom, b.fh * zoom), Image.NEAREST)
                ax, ay = b.anchors[d][idx]
                img.alpha_composite(cell, (c * cw + cw // 2 - ax * zoom, r * ch + ch * 3 // 4 - ay * zoom))
        frames.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durs.append(int(round(step * 1000 / 60)))
        tick += step
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


def player_html(builts: list[P.Built], path: Path) -> None:
    manifest = {b.name: {"fw": b.fw, "fh": b.fh, "durations": b.durations, "dirs": b.dirs} for b in builts}
    path.write_text(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Zarude — sprite fourni au format PMD</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#1a1a2e;color:#eee}}
header{{padding:12px 16px;border-bottom:1px solid #333}} h1{{font-size:18px;margin:0 0 4px}}
p{{margin:2px 0;color:#aab;font-size:13px}}
.bar{{display:flex;gap:16px;padding:10px 16px;align-items:center;font-size:14px;flex-wrap:wrap}}
canvas{{image-rendering:pixelated;background:#241c14;display:block;margin:12px 16px;border:1px solid #333}}
select,input{{background:#222;color:#eee;border:1px solid #444;padding:3px}}
</style></head><body>
<header><h1>Zarude — dessin fourni, mis au format SpriteCollab</h1>
<p>Quatre vues dessinées, squelette d'animation de Rillaboom #0812. Les diagonales reprennent le profil.</p></header>
<div class="bar">
<label>Animation <select id="anim"></select></label>
<label>Direction <select id="dir"></select></label>
<label>Zoom <input id="zoom" type="range" min="1" max="8" value="4"></label>
<label><input id="play" type="checkbox" checked> lecture</label><span id="info"></span></div>
<canvas id="c"></canvas>
<script>
const M = {json.dumps(manifest)}, imgs = {{}};
const anim = document.getElementById('anim'), dsel = document.getElementById('dir');
for (const k of Object.keys(M)) {{ const o = document.createElement('option'); o.textContent = k; anim.append(o); }}
const names = {json.dumps(P.DIRECTIONS)};
function loadDirs() {{ dsel.innerHTML = '';
  for (let i = 0; i < M[anim.value].dirs; i++) {{ const o = document.createElement('option'); o.value = i; o.textContent = names[i]; dsel.append(o); }} }}
anim.onchange = loadDirs; loadDirs();
function img(n) {{ if (!imgs[n]) {{ const i = new Image(); i.src = n + '-Anim.png'; imgs[n] = i; }} return imgs[n]; }}
const c = document.getElementById('c'), g = c.getContext('2d');
let t = 0;
setInterval(() => {{
  const m = M[anim.value], z = +document.getElementById('zoom').value, d = +dsel.value || 0;
  const total = m.durations.reduce((a, b) => a + b, 0);
  if (document.getElementById('play').checked) t = (t + 1) % total;
  let acc = 0, f = 0;
  for (let i = 0; i < m.durations.length; i++) {{ if (acc + m.durations[i] > t) {{ f = i; break; }} acc += m.durations[i]; }}
  c.width = m.fw * z + 40; c.height = m.fh * z + 40; g.imageSmoothingEnabled = false;
  g.clearRect(0, 0, c.width, c.height);
  const im = img(anim.value);
  if (im.complete) g.drawImage(im, f * m.fw, d * m.fh, m.fw, m.fh, 20, 20, m.fw * z, m.fh * z);
  document.getElementById('info').textContent = anim.value + ' — image ' + (f + 1) + '/' + m.durations.length;
}}, 1000 / 60);
</script></body></html>
""", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nuit").mkdir(exist_ok=True)
    poses = read_poses()
    shadow_size, skel = P.load_sprite(SKELETON)
    builts = [build(poses, name, skel[name]) for name in FRAME_PLAN]
    by_name = {b.name: b for b in builts}

    for b in builts:
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            P.sheet(b, which).save(OUT / f"{b.name}-{kind}.png", optimize=True)
        night(P.sheet(b, 0)).save(OUT / "nuit" / f"{b.name}-Anim.png", optimize=True)
    entries: list = list(builts) + [("Strike", skel["Strike"].index, "Attack")]
    P.write_animdata(shadow_size, entries, OUT / "AnimData.xml")
    ase = P.write_aseprite(builts, OUT / "zarude_fourni.aseprite")
    contact_sheet(builts, OUT / "apercu.png")
    directions_sheet(by_name["Walk"], OUT / "apercu_directions.png")
    gif(by_name, ["Walk", "Idle"], [0, 2, 4, 6], OUT / "apercu_marche_attente.gif")
    gif(by_name, ["Attack", "Hop"], [0, 2, 4, 6], OUT / "apercu_attaque.gif")
    player_html(builts, OUT / "apercu.html")

    (OUT / "credits.txt").write_text("\n".join([
        "# Zarude — dessin fourni par l'utilisateur, mis au format SpriteCollab",
        "2026-09-07 00:00:00.000000\tDessin : utilisateur (IMG_4840.png) — mise au format : Guilde Treehouse\tCUR\tCC_BY-NC_4\t"
        + ",".join(FRAME_PLAN),
        "",
        "Squelette d'animation (durées, déplacements d'ancre, cases, créneaux) : Rillaboom #0812,",
        "baronessfaron (<@!544245909639397378>), CC BY-NC 4.0 — https://sprites.pmdcollab.org/#/0812",
        "Zarude #0893 n'existe pas sur SpriteCollab ; ce sprite n'y a été ni soumis ni approuvé.",
    ]) + "\n", encoding="utf-8")

    used: set[tuple[int, int, int]] = set()
    for b in builts:
        for row in b.cells:
            for cell in row:
                px = cell[0][cell[0][:, :, 3] > 0]
                used |= set(map(tuple, px[:, :3].tolist()))
    kit = {
        "pokemon": {"nom": "Zarude", "numero": "0893", "forme": "0000",
                    "note": "absent de SpriteCollab ; dessin fourni par l'utilisateur"},
        "source_dessin": {"fichier": "source/personnages/reference/zarude_fourni.png",
                          "planche": [256, 256], "grille": "4 orientations × 4 images de 64 × 64",
                          "orientations": ["de face", "profil gauche", "profil droit (miroir)", "de dos"],
                          "palette_rabattue": read_poses.changes},   # type: ignore[attr-defined]
        "squelette": {"sprite": "Rillaboom #0812", "apporte": "durées, déplacements d'ancre, cases, créneaux <Index>, Rush/Hit/Return"},
        "directions": {P.DIRECTIONS[d]: {"vue": ["de face", "profil gauche", "profil droit", "de dos"][r],
                                         "miroir": m} for d, (r, m) in DIR_SOURCE.items()},
        "limite_connue": "le dessin fourni n'a pas de vue diagonale : les quatre diagonales reprennent le profil du bon côté",
        "shadow_size": shadow_size,
        "animations": {b.name: {"creneau": b.index, "case": [b.fw, b.fh], "images": len(b.durations),
                                "directions": b.dirs, "durees": b.durations, "ticks": sum(b.durations),
                                "poses": FRAME_PLAN[b.name]} for b in builts},
        "copies": {"Strike": "Attack"},
        "aseprite": ase,
        "palette": sorted("#%02x%02x%02x" % c for c in used),
        "couleurs": len(used),
    }
    (OUT / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Zarude fourni : {len(builts)} animations (+ Strike), {len(used)} couleurs → {OUT.relative_to(ROOT)}")
    for b in builts:
        print(f"  {b.name:8s} {b.fw:3d} × {b.fh:3d}  {len(b.durations):2d} images  {b.dirs} dir  {sum(b.durations):3d} ticks")


if __name__ == "__main__":
    main()
