#!/usr/bin/env python3
"""Relecture indépendante des packs personnages/dynamax/<numéro>_<slug>/ produits par build_dynamax_sprites.py.

Règles SpriteBot / SkyTemple : index imposés, CopyOf sans chaînage, feuilles Anim / Offsets / Shadow de même
taille, divisibles par la case, 1 ou 8 lignes, colonnes = Durations, Rush / Hit / Return < nb images, alpha 0 ou 255,
un seul pixel blanc par case de Shadow, un pixel de chaque repère par case (tête peut se confondre au centre),
couleurs opaques comptées (avertissement au-delà de 15).

Règles propres à la transformation : toutes les animations de la source sont reprises, avec les mêmes index,
durées, Rush / Hit / Return et CopyOf ; cases multiples de 8 ; le déplacement de l'ancre vaut celui de la source
× échelle ; chaque pixel opaque de la source se retrouve, agrandi, à la bonne place (aucun pixel du Pokémon perdu
ni recoloré, sauf sous un nuage de premier plan, au plus 12 % du corps) ; palette = palette de la source
+ aura ; marge d'un pixel ; silhouettes nuit = jour ; Aseprite, kit.json, credits.txt, README et aperçus présents.
(Les sprites officiels ne sont pas des miroirs exacts gauche/droite : chaque direction est comparée à la sienne.)

Usage : python3 source/personnages/verify_dynamax_sprites.py [slug ...] → controle_qualite.json dans chaque pack.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
from build_dynamax_sprites import AURA, AURA_LIGHT, OUT_ROOT, POKEMON, darkest_colour, load_source, white_pixel  # noqa: E402

MAX_COLOURS = 15


def parse(path: Path) -> tuple[int, list[dict]]:
    root = ET.parse(path).getroot()
    anims = []
    for node in root.find("Anims").iter("Anim"):
        idx = node.find("Index")
        e = {"name": node.find("Name").text, "index": int(idx.text) if idx is not None else None}
        copy = node.find("CopyOf")
        if copy is not None:
            e["copy_of"] = copy.text
        else:
            e["fw"], e["fh"] = int(node.find("FrameWidth").text), int(node.find("FrameHeight").text)
            e["durations"] = [int(d.text) for d in node.find("Durations").iter("Duration")]
            for tag, key in (("RushFrame", "rush"), ("HitFrame", "hit"), ("ReturnFrame", "ret")):
                sub = node.find(tag)
                e[key] = int(sub.text) if sub is not None else None
        anims.append(e)
    return int(root.find("ShadowSize").text), anims


def check_pack(number: str, slug: str, folder: Path) -> tuple[list[str], dict]:
    out = OUT_ROOT / f"{number}_{slug}"
    errors: list[str] = []
    warnings: list[str] = []
    E = errors.append
    if not (out / "AnimData.xml").is_file():
        return [f"{out} : AnimData.xml absent"], {}
    kit = json.loads((out / "kit.json").read_text(encoding="utf-8"))
    scale = int(kit["dynamax"]["echelle"])
    shadow_size, anims = parse(out / "AnimData.xml")
    _, src = load_source(folder)
    src_by = {a.name: a for a in src}
    cloud_colours = {AURA, AURA_LIGHT, darkest_colour(src)}
    if shadow_size != 2:
        E(f"ShadowSize {shadow_size} ≠ 2")
    if [a["name"] for a in anims] != [a.name for a in src]:
        E("liste d'animations différente de la source")
    names = [a["name"] for a in anims]
    colours: set = set()
    src_colours: set = set()
    cells = 0
    lost_total = compared_total = 0
    for e in anims:
        n = e["name"]
        s = src_by.get(n)
        if s is None:
            E(f"{n} : absente de la source")
            continue
        if e["index"] != s.index:
            E(f"{n} : index {e['index']} ≠ {s.index}")
        if "copy_of" in e or s.copy_of:
            if e.get("copy_of") != s.copy_of:
                E(f"{n} : CopyOf {e.get('copy_of')} ≠ {s.copy_of}")
            elif e["copy_of"] not in names or "copy_of" in next(a for a in anims if a["name"] == e["copy_of"]):
                E(f"{n} : CopyOf invalide ou chaîné")
            continue
        if e["durations"] != s.durations or (e["rush"], e["hit"], e["ret"]) != (s.rush, s.hit, s.ret):
            E(f"{n} : durées ou Rush/Hit/Return différents de la source")
        fw, fh, durs = e["fw"], e["fh"], e["durations"]
        if fw % 8 or fh % 8:
            E(f"{n} : case {fw}×{fh} non multiple de 8")
        for key in ("rush", "hit", "ret"):
            if e[key] is not None and not (0 <= e[key] < len(durs)):
                E(f"{n} : {key} hors des images")
        sheets = {}
        for kind in ("Anim", "Offsets", "Shadow"):
            p = out / f"{n}-{kind}.png"
            if not p.is_file():
                E(f"{n}-{kind}.png absent")
                continue
            sheets[kind] = np.array(Image.open(p).convert("RGBA"))
        if len(sheets) < 3:
            continue
        shapes = {v.shape for v in sheets.values()}
        if len(shapes) != 1:
            E(f"{n} : feuilles de tailles différentes")
            continue
        H, W = sheets["Anim"].shape[:2]
        if W != fw * len(durs) or H % fh:
            E(f"{n} : feuille {W}×{H} ≠ {len(durs)} colonnes de {fw} × lignes de {fh}")
            continue
        dirs = H // fh
        if dirs not in (1, 8):
            E(f"{n} : {dirs} lignes")
        if dirs != s.dirs:
            E(f"{n} : {dirs} directions ≠ {s.dirs} dans la source")
        night_path = out / "nuit" / f"{n}-Anim.png"
        night = np.array(Image.open(night_path).convert("RGBA")) if night_path.is_file() else None
        if night is None:
            E(f"{n} : variante nuit absente")
        elif night.shape != sheets["Anim"].shape or not np.array_equal(night[:, :, 3] > 0, sheets["Anim"][:, :, 3] > 0):
            E(f"{n} : silhouette nuit ≠ jour")
        for kind, arr in sheets.items():
            a = arr[:, :, 3]
            if ((a > 0) & (a < 255)).any():
                E(f"{n}-{kind} : alpha intermédiaire")
        anim_sheet = sheets["Anim"]
        opaque = anim_sheet[anim_sheet[:, :, 3] > 0][:, :3]
        colours |= set(map(tuple, opaque.tolist()))
        s_op = s.anim[s.anim[:, :, 3] > 0][:, :3]
        src_colours |= set(map(tuple, s_op.tolist()))
        for d in range(dirs):
            for i in range(len(durs)):
                cells += 1
                box = (slice(d * fh, (d + 1) * fh), slice(i * fw, (i + 1) * fw))
                A, O, S = anim_sheet[box], sheets["Offsets"][box], sheets["Shadow"][box]
                # ancre
                wh = np.argwhere((S[:, :, 3] > 0) & np.all(S[:, :, :3] == 255, axis=2))
                if len(wh) != 1:
                    E(f"{n} d{d} i{i} : {len(wh)} pixel(s) blanc(s) dans Shadow")
                    continue
                ax, ay = int(wh[0][1]), int(wh[0][0])
                sax, say = white_pixel(s.cell(s.shad, d, i))
                exp = (fw // 2 + (sax - s.fw // 2) * scale, fh // 2 + 4 + (say - (s.fh // 2 + 4)) * scale)
                if (ax, ay) != exp:
                    E(f"{n} d{d} i{i} : ancre {(ax, ay)} ≠ {exp} (source × {scale})")
                # repères : un pixel par couleur, positions = source × échelle
                so = s.cell(s.offs, d, i)
                exp_marks = {(int(x) - sax, int(y) - say): tuple(int(v) for v in so[y, x, :3]) for y, x in np.argwhere(so[:, :, 3] > 0)}
                got_marks = {(int(x) - ax, int(y) - ay): tuple(int(v) for v in O[y, x, :3]) for y, x in np.argwhere(O[:, :, 3] > 0)}
                if got_marks != {(x * scale, y * scale): c for (x, y), c in exp_marks.items()}:
                    E(f"{n} d{d} i{i} : repères Offsets ≠ source × {scale}")
                if not any(c[1] == 255 for c in got_marks.values()):
                    E(f"{n} d{d} i{i} : centre (vert) absent")
                # marge et contenu
                m = A[:, :, 3] > 0
                if not m.any():
                    E(f"{n} d{d} i{i} : case vide")
                    continue
                if m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any():
                    E(f"{n} d{d} i{i} : dessin au bord de la case")
                # pixels du Pokémon : chaque pixel source, agrandi, à sa place (sauf sous un nuage de premier plan)
                sc = s.cell(s.anim, d, i)
                sm = sc[:, :, 3] > 0
                ys, xs = np.nonzero(sm)
                x0 = ax + (xs - sax) * scale
                y0 = ay + (ys - say) * scale
                got = A[y0, x0, :3]
                want = sc[ys, xs, :3]
                same = np.all(got == want, axis=1)
                lost = int((~same).sum())
                lost_total += lost
                compared_total += len(same)
                bad = [tuple(int(v) for v in g) for g, ok in zip(got, same) if not ok and tuple(int(v) for v in g) not in cloud_colours]
                if bad:
                    E(f"{n} d{d} i{i} : {len(bad)} pixel(s) du Pokémon recolorés hors nuage, ex. {bad[0]}")
                if lost > len(same) // 8:
                    E(f"{n} d{d} i{i} : {lost} pixels du Pokémon sous les nuages (sur {len(same)}, > 12 %)")
    extra = colours - src_colours
    if not extra <= {AURA, AURA_LIGHT}:
        E(f"couleurs hors palette source + aura : {sorted(extra - {AURA, AURA_LIGHT})[:5]}")
    if len(colours) > MAX_COLOURS:
        warnings.append(f"{len(colours)} couleurs opaques (> {MAX_COLOURS} : import strict SkyTemple refusé)")
    for f in ("kit.json", "credits.txt", "README.md", "apercu.png", "apercu_directions.png", "apercu_comparaison.png",
              "apercu_marche_attente.gif", "apercu_attaques.gif", "apercu.html", f"{slug}.aseprite"):
        if not (out / f).is_file():
            E(f"{f} absent")
    ase = out / f"{slug}.aseprite"
    if ase.is_file():
        head = ase.read_bytes()[:128]
        if int.from_bytes(head[4:6], "little") != 0xA5E0:
            E("Aseprite : en-tête invalide")
        elif int.from_bytes(head[6:8], "little") != sum(len(e["durations"]) for e in anims if "durations" in e):
            E("Aseprite : nombre d'images ≠ feuilles")
    credits = (out / "credits.txt").read_text(encoding="utf-8") if (out / "credits.txt").is_file() else ""
    if number not in credits or "SpriteCollab" not in credits:
        E("credits.txt : source SpriteCollab non citée")
    report = {"pokemon": number, "slug": slug, "animations": len(anims), "cases": cells, "couleurs": len(colours),
              "couleurs_source": len(src_colours), "pixels_compares": compared_total, "pixels_perdus": lost_total,
              "shadow_size": shadow_size, "echelle": scale, "erreurs": errors, "avertissements": warnings[:20],
              "resultat": "OK" if not errors else "ERREURS"}
    (out / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return errors, report


def main(argv: list[str]) -> None:
    failed = False
    for number, slug, name, folder in POKEMON:
        if argv and slug not in argv and number not in argv:
            continue
        if not (OUT_ROOT / f"{number}_{slug}").is_dir():
            print(f"{number} {name} : pack absent")
            continue
        errors, r = check_pack(number, slug, folder)
        if errors:
            failed = True
            print(f"{number} {name} : {len(errors)} erreur(s)")
            for e in errors[:12]:
                print("   ", e)
        else:
            print(f"{number} {name} : OK — {r['animations']} animations, {r['cases']} cases, {r['couleurs']} couleurs "
                  f"(source {r['couleurs_source']}), {r['pixels_perdus']} px sous les nuages / {r['pixels_compares']}"
                  + (f" ; {len(r['avertissements'])} avertissement(s)" if r["avertissements"] else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
