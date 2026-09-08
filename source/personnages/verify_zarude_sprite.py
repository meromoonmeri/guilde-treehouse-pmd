#!/usr/bin/env python3
"""Relecture indépendante du sprite Zarude (personnages/zarude/).

Règles du SpriteBot de PMDCollab et de l'import SkyTemple : AnimData.xml cohérent (noms, index
imposés, CopyOf), feuilles Anim / Offsets / Shadow de même taille et divisibles par la case, 1 ou
8 lignes, durées = nombre d'images, alpha strictement 0 ou 255, un seul pixel blanc d'ombre et un
seul jeu de repères par case, 15 couleurs au plus.

Contrôles propres à ce sprite :
- squelette = Rillaboom #0812 : mêmes animations, durées, Rush/Hit/Return, cases (ShadowSize 1 : Zarude est plus petit)
  identiques ou agrandies d'un multiple de 8, même déplacement de l'ancre à chaque image ;
- Gauche / Haut-gauche / Bas-gauche = miroir exact de Droite / Haut-droite / Bas-droite (Anim et
  Offsets) pour les animations sans rotation ; Swing et Rotate tournent d'une direction par image ;
- palette ⊂ zarude_pieces.PALETTE, rien au bord des cases, Idle = pose de repos de Walk ;
- variantes nuit (même silhouette), Aseprite, kit.json, credits.txt, aperçus présents.
"""
from __future__ import annotations

import json
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
from zarude_pieces import PALETTE  # noqa: E402

OUT = ROOT / "personnages" / "zarude"
REF = ROOT / "source" / "personnages" / "reference" / "0812"
REQUIRED_INDEX = {"Walk": 0, "Attack": 1, "Strike": 2, "Shoot": 3, "Sing": 4, "Sleep": 5, "Hurt": 6, "Idle": 7,
                  "Swing": 8, "Double": 9, "Hop": 10, "Charge": 11, "Rotate": 12}
COMPLETE_SET = ["Idle", "Walk", "Sleep", "Hurt", "Attack", "Charge", "Shoot", "Strike", "Sing", "Swing", "Double", "Rotate", "Hop"]
SPIN = ("Swing", "Rotate")
MIRROR = {5: 3, 6: 2, 7: 1}
MIN_PIXELS = 250            # une silhouette de Zarude au repos compte ~330 px opaques (22 px de haut)


def rgba(path: Path) -> np.ndarray:
    im = Image.open(path)
    assert im.mode == "RGBA", f"{path.name} : mode {im.mode}"
    return np.array(im)


def marker(cell: np.ndarray, colour: tuple[int, int, int]) -> list[tuple[int, int]]:
    m = (cell[:, :, 3] == 255) & np.all(cell[:, :, :3] == colour, axis=2)
    return [(int(x), int(y)) for y, x in np.argwhere(m)]


def parse(path: Path) -> tuple[int, dict, list[str]]:
    root = ET.parse(path).getroot()
    anims, names = {}, []
    for node in root.find("Anims").iter("Anim"):
        name = node.find("Name").text
        names.append(name)
        copy = node.find("CopyOf")
        if copy is not None:
            anims[name] = {"copy_of": copy.text, "index": int(node.find("Index").text)}
            continue
        durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
        entry = {"fw": int(node.find("FrameWidth").text), "fh": int(node.find("FrameHeight").text),
                 "durations": durations, "index": int(node.find("Index").text)}
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            sub = node.find(tag)
            entry[tag] = int(sub.text) if sub is not None else None
        anims[name] = entry
    return int(root.find("ShadowSize").text), anims, names


def anchor(cell: np.ndarray) -> tuple[int, int]:
    white = marker(cell, (255, 255, 255))
    assert len(white) == 1, f"{len(white)} pixels blancs d'ombre"
    return white[0]


def cells_of(sheet: np.ndarray, fw: int, fh: int):
    dirs, n = sheet.shape[0] // fh, sheet.shape[1] // fw
    return [[sheet[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw] for i in range(n)] for d in range(dirs)]


def crop_about_anchor(cell: np.ndarray, ax: int, ay: int) -> tuple[np.ndarray, tuple[int, int]]:
    ys, xs = np.nonzero(cell[:, :, 3])
    return cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (int(xs.min()) - ax, int(ys.min()) - ay)


def main() -> None:
    report = {"animations": {}, "fichiers": {}}
    shadow_size, anims, names = parse(OUT / "AnimData.xml")
    ref_shadow_size, ref_anims, _ = parse(REF / "AnimData.xml")
    assert 0 <= shadow_size <= 2, "ShadowSize hors de [0, 2]"
    assert shadow_size == 1, "ShadowSize attendu : 1 (Zarude fait 22 px de haut, Rillaboom 35 px → 2)"
    assert len(names) == len(set(names)) <= 44, "noms d'animation en double ou trop nombreux"
    for name, m in anims.items():
        assert REQUIRED_INDEX.get(name, m["index"]) == m["index"], f"{name} : index {m['index']} ≠ {REQUIRED_INDEX.get(name)}"
        if "copy_of" in m:
            assert m["copy_of"] in anims and "copy_of" not in anims[m["copy_of"]], f"{name} : CopyOf invalide"
        else:
            for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
                if m[tag] is not None:
                    assert m[tag] < len(m["durations"]), f"{name} : {tag} au-delà du nombre d'images"
    missing = [n for n in COMPLETE_SET if n not in anims]
    assert not missing, f"set donjon complet incomplet : {missing}"
    assert set(anims) == set(ref_anims), f"animations ≠ référence : {set(anims) ^ set(ref_anims)}"
    sheets = {p.name.split("-")[0] for p in OUT.glob("*-Anim.png")}
    assert sheets == {n for n, m in anims.items() if "copy_of" not in m}, "feuilles ≠ XML"

    # squelette
    for name, m in anims.items():
        r = ref_anims[name]
        if "copy_of" in m:
            assert r.get("copy_of") == m["copy_of"], f"{name} : CopyOf ≠ référence"
            continue
        assert m["durations"] == r["durations"], f"{name} : durées ≠ référence"
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            assert m[tag] == r[tag], f"{name} : {tag} ≠ référence"
        assert m["fw"] >= r["fw"] and m["fh"] >= r["fh"], f"{name} : case plus petite que la référence"
        assert (m["fw"] - r["fw"]) % 8 == 0 and (m["fh"] - r["fh"]) % 8 == 0, f"{name} : agrandissement non multiple de 8"

    palette_ref = set(PALETTE.values())
    palette, total_cells = set(), 0
    rest_pose = {}
    for name, m in anims.items():
        if "copy_of" in m:
            continue
        fw, fh, durations = m["fw"], m["fh"], m["durations"]
        assert fw % 2 == 0 and fh % 2 == 0, f"{name} : case impaire"
        anim = rgba(OUT / f"{name}-Anim.png")
        offs = rgba(OUT / f"{name}-Offsets.png")
        shad = rgba(OUT / f"{name}-Shadow.png")
        night = rgba(OUT / "nuit" / f"{name}-Anim.png")
        assert anim.shape == offs.shape == shad.shape == night.shape, f"{name} : tailles différentes"
        assert anim.shape[1] % fw == 0 and anim.shape[0] % fh == 0, f"{name} : feuille non divisible par la case"
        n, dirs = anim.shape[1] // fw, anim.shape[0] // fh
        assert dirs in (1, 8), f"{name} : {dirs} lignes"
        assert n == len(durations), f"{name} : {n} images pour {len(durations)} durées"
        for sheet_name, sheet in (("Anim", anim), ("Offsets", offs), ("Shadow", shad), ("nuit", night)):
            assert set(np.unique(sheet[:, :, 3])) <= {0, 255}, f"{name}-{sheet_name} : pixels semi-transparents"
        assert np.array_equal(anim[:, :, 3], night[:, :, 3]), f"{name} : silhouette nuit ≠ jour"
        assert not np.array_equal(anim, night), f"{name} : variante nuit identique au jour"
        palette |= set(map(tuple, anim[anim[:, :, 3] > 0][:, :3].tolist()))
        r = ref_anims[name]
        ref_shadow = rgba(REF / f"{name}-Shadow.png")
        ref_cells = cells_of(ref_shadow, r["fw"], r["fh"])
        assert len(ref_cells) == dirs and len(ref_cells[0]) == n, f"{name} : grille ≠ référence"
        A, O, S = cells_of(anim, fw, fh), cells_of(offs, fw, fh), cells_of(shad, fw, fh)
        stats = {"case": [fw, fh], "images": n, "directions": dirs, "pixels_min": None, "pixels_max": None,
                 "case_reference": [r["fw"], r["fh"]], "ancre_repos": None}
        for d in range(dirs):
            for i in range(n):
                cell, o, s = A[d][i], O[d][i], S[d][i]
                ax, ay = anchor(s)
                rx, ry = anchor(ref_cells[d][i])
                disp = (ax - fw // 2, ay - (fh // 2 + 4))
                ref_disp = (rx - r["fw"] // 2, ry - (r["fh"] // 2 + 4))
                assert disp == ref_disp, f"{name} dir {d} image {i} : déplacement d'ancre {disp} ≠ référence {ref_disp}"
                # gabarit d'ombre 24 × 8 identique à la référence
                assert np.array_equal(s[ay - 4:ay + 4, ax - 12:ax + 12], ref_shadow[ry - 4 + d * r["fh"]:ry + 4 + d * r["fh"], rx - 12 + i * r["fw"]:rx + 12 + i * r["fw"]]), \
                    f"{name} dir {d} image {i} : gabarit d'ombre ≠ référence"
                centre = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 1] == 255))]
                reds = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 0] == 255))]
                blues = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 2] == 255))]
                assert len(centre) == 1 and len(reds) == 1 and len(blues) == 1, f"{name} dir {d} image {i} : repères centre/mains ≠ 1"
                assert len(marker(o, (255, 255, 255))) == 0, f"{name} dir {d} image {i} : pixel blanc dans Offsets"
                assert len(marker(o, (0, 0, 0))) == 1, f"{name} dir {d} image {i} : repère tête absent ou multiple"
                ys, xs = np.nonzero(cell[:, :, 3])
                px = int(len(xs))
                assert px >= MIN_PIXELS, f"{name} dir {d} image {i} : trop peu de pixels ({px})"
                assert xs.min() >= 1 and ys.min() >= 1 and xs.max() <= fw - 2 and ys.max() <= fh - 2, f"{name} dir {d} image {i} : dessin au bord de la case"
                # les repères tombent dans la silhouette ou à un pixel d'elle
                for (mx, my) in centre + reds + blues + marker(o, (0, 0, 0)):
                    near = cell[max(0, my - 1):my + 2, max(0, mx - 1):mx + 2, 3]
                    assert near.any(), f"{name} dir {d} image {i} : repère ({mx}, {my}) hors du dessin"
                stats["pixels_min"] = px if stats["pixels_min"] is None else min(stats["pixels_min"], px)
                stats["pixels_max"] = px if stats["pixels_max"] is None else max(stats["pixels_max"], px)
                total_cells += 1
                if i == 0 and d == 0:
                    stats["ancre_repos"] = [ax, ay]
                    if name in ("Walk", "Idle", "Charge", "Rotate", "Swing"):
                        rest_pose[name] = crop_about_anchor(cell, ax, ay)
            # miroirs
            if dirs == 8 and d in MIRROR and name not in SPIN:
                md = MIRROR[d]
                for i in range(n):
                    for kind, X in (("Anim", A), ("Offsets", O)):
                        ax, ay = anchor(S[d][i])
                        bx, by = anchor(S[md][i])
                        a_img, (aox, aoy) = crop_about_anchor(X[d][i], ax, ay)
                        b_img, (box, boy) = crop_about_anchor(X[md][i], bx, by)
                        assert np.array_equal(a_img, b_img[:, ::-1]) and aoy == boy and aox == -(box + b_img.shape[1] - 1), \
                            f"{name} dir {d} image {i} : {kind} n'est pas le miroir de la direction {md}"
        if name in SPIN:
            # l'image i de la direction d regarde (d − i) mod 8 : même dessin que Walk image 1 de cette direction
            walk = rgba(OUT / "Walk-Anim.png")
            wfw, wfh = anims["Walk"]["fw"], anims["Walk"]["fh"]
            W = cells_of(walk, wfw, wfh)
            WS = cells_of(rgba(OUT / "Walk-Shadow.png"), wfw, wfh)
            for d in range(8):
                for i in range(n):
                    facing = (d - i) % 8
                    a_img, a_org = crop_about_anchor(A[d][i], *anchor(S[d][i]))
                    w_img, w_org = crop_about_anchor(W[facing][0], *anchor(WS[facing][0]))
                    assert a_img.shape == w_img.shape and np.array_equal(a_img, w_img) and a_org == w_org, \
                        f"{name} dir {d} image {i} : ne regarde pas la direction {facing}"
        report["animations"][name] = stats
    assert palette <= palette_ref, f"couleurs hors palette : {palette - palette_ref}"
    assert len(palette) <= 15, f"{len(palette)} couleurs (15 max)"
    for key in ("Idle", "Charge"):
        assert rest_pose[key][0].shape == rest_pose["Walk"][0].shape and np.array_equal(rest_pose[key][0], rest_pose["Walk"][0]) \
            and rest_pose[key][1] == rest_pose["Walk"][1], f"{key} image 1 ≠ pose de repos de Walk"

    # Aseprite
    data = (OUT / "zarude.aseprite").read_bytes()
    size, magic, frames, w, h, depth = struct.unpack_from("<IHHHHH", data, 0)
    assert magic == 0xA5E0 and size == len(data), "Aseprite : en-tête invalide"
    expected_frames = sum(len(m["durations"]) for m in anims.values() if "copy_of" not in m)
    assert frames == expected_frames, f"Aseprite : {frames} images ≠ {expected_frames}"
    assert depth == 32, "Aseprite : profondeur ≠ RGBA"
    pos = 128
    frame_size, fmagic, old_chunks, duration, _, chunks = struct.unpack_from("<IHHH2sI", data, pos)
    assert fmagic == 0xF1FA, "Aseprite : image invalide"
    p, layers, tags, first_cel = pos + 16, 0, 0, None
    for _ in range(chunks):
        clen, ckind = struct.unpack_from("<IH", data, p)
        if ckind == 0x2004:
            layers += 1
        elif ckind == 0x2018:
            tags = struct.unpack_from("<H", data, p + 6)[0]
        elif ckind == 0x2005 and first_cel is None:
            layer, x, y, opacity, ctype, _ = struct.unpack_from("<HhhBHh", data, p + 6)
            cw, ch = struct.unpack_from("<HH", data, p + 6 + 16)
            raw = zlib.decompress(data[p + 6 + 20:p + clen])
            first_cel = (layer, x, y, np.frombuffer(raw, np.uint8).reshape(ch, cw, 4))
        p += clen
    assert layers == 8, f"Aseprite : {layers} calques"
    assert tags == len([n for n, m in anims.items() if "copy_of" not in m]), f"Aseprite : {tags} étiquettes"
    walk = rgba(OUT / "Walk-Anim.png")
    fw, fh = anims["Walk"]["fw"], anims["Walk"]["fh"]
    layer, x, y, pix = first_cel
    ox, oy = (w - fw) // 2, (h - fh) // 2
    cell = walk[0:fh, 0:fw]
    ys, xs = np.nonzero(cell[:, :, 3])
    crop = cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    assert layer == 0 and (x, y) == (xs.min() + ox, ys.min() + oy) and np.array_equal(crop, pix), "Aseprite : premier cel ≠ Walk Bas image 1"
    report["fichiers"]["aseprite"] = {"images": frames, "calques": layers, "etiquettes": tags, "toile": [w, h]}

    kit = json.loads((OUT / "kit.json").read_text())
    assert kit["couleurs"] == len(palette), "kit.json : nombre de couleurs"
    assert set(kit["palette"]) == {"#%02x%02x%02x" % c for c in palette}, "kit.json : palette"
    for name, m in anims.items():
        if "copy_of" in m:
            continue
        assert kit["animations"][name]["case"] == [m["fw"], m["fh"]], f"kit.json : case de {name}"
        assert kit["animations"][name]["durees"] == m["durations"], f"kit.json : durées de {name}"
    credits = (OUT / "credits.txt").read_text()
    assert "544245909639397378" in credits and "0812" in credits and "CC_BY-NC_4" in credits, "credits.txt : référence Rillaboom / licence absentes"
    assert "Game Character Hub" in credits or "planche" in credits, "credits.txt : origine de la planche de marche absente"
    for f in ("apercu.png", "apercu_directions.png", "apercu_reference.png", "apercu.html", "apercu_marche_attente.gif",
              "apercu_attaque_hurlement.gif", "README.md"):
        assert (OUT / f).is_file(), f"fichier manquant : {f}"

    report["resume"] = {"animations": len(anims), "feuilles": len(sheets), "cases": total_cells, "couleurs": len(palette),
                        "shadow_size": shadow_size, "squelette": "0812 Rillaboom", "miroirs_exacts": True, "statut": "conforme"}
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK — {len(anims)} animations, {total_cells} cases contrôlées, {len(palette)} couleurs, ShadowSize {shadow_size}, squelette Rillaboom respecté")


if __name__ == "__main__":
    main()
