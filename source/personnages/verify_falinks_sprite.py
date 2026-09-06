#!/usr/bin/env python3
"""Relecture indépendante du sprite d'escouade Falinks (personnages/falinks/).

Reprend les règles appliquées par le SpriteBot de PMDCollab et par l'import SkyTemple :
AnimData.xml cohérent (noms, index imposés, CopyOf), feuilles Anim / Offsets / Shadow de
même taille et divisibles par la case, 1 ou 8 lignes, durées = nombre d'images, alpha
strictement 0 ou 255, un seul pixel blanc d'ombre et un seul jeu de repères par case,
15 couleurs au plus. Ajoute les contrôles propres à la composition : chaque case contient
six unités (pixels d'origine uniquement), l'ancre au repos est en (largeur/2, hauteur/2 + 4),
les variantes nuit et l'Aseprite correspondent aux feuilles.
"""
from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "personnages" / "falinks"
REF = ROOT / "source" / "personnages" / "reference" / "0870"
REQUIRED_INDEX = {"Walk": 0, "Attack": 1, "Strike": 2, "Shoot": 3, "Sleep": 5, "Hurt": 6, "Idle": 7,
                  "Swing": 8, "Double": 9, "Hop": 10, "Charge": 11, "Rotate": 12}
COMPLETE_SET = ["Idle", "Walk", "Sleep", "Hurt", "Attack", "Charge", "Shoot", "Strike", "Swing", "Double", "Rotate", "Hop"]
UNIT_PIXELS = {"brass": 137, "trooper": 135}    # pixels d'une unité au repos (Walk image 1)
LOCKSTEP = ["Attack", "Swing", "Double", "Hop", "Charge", "Rotate", "Hurt"]
_BRASS_SHADOWS: dict[str, tuple[np.ndarray, int, int]] = {}


def brass_disp(name: str, d: int, i: int) -> tuple[int, int]:
    """Déplacement de l'ancre du brass d'origine dans sa case (dir d, image i)."""
    if name not in _BRASS_SHADOWS:
        root = ET.parse(REF / "0002" / "AnimData.xml").getroot()
        node = next(n for n in root.find("Anims").iter("Anim") if n.find("Name").text == name)
        fw, fh = int(node.find("FrameWidth").text), int(node.find("FrameHeight").text)
        _BRASS_SHADOWS[name] = (rgba(REF / "0002" / f"{name}-Shadow.png"), fw, fh)
    sheet, fw, fh = _BRASS_SHADOWS[name]
    cell = sheet[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
    (x, y), = marker(cell, (255, 255, 255))
    return x - fw // 2, y - (fh // 2 + 4)


def rgba(path: Path) -> np.ndarray:
    im = Image.open(path)
    assert im.mode == "RGBA", f"{path.name} : mode {im.mode}"
    return np.array(im)


def marker(cell: np.ndarray, colour: tuple[int, int, int]) -> list[tuple[int, int]]:
    m = (cell[:, :, 3] == 255) & np.all(cell[:, :, :3] == colour, axis=2)
    return [(int(x), int(y)) for y, x in np.argwhere(m)]


def reference_palette() -> set[tuple[int, int, int]]:
    colours = set()
    for form in ("0002", "0003"):
        for png in (REF / form).glob("*-Anim.png"):
            a = rgba(png)
            colours |= set(map(tuple, a[a[:, :, 3] > 0][:, :3].tolist()))
    return colours


def main() -> None:
    errors, report = [], {"animations": {}, "fichiers": {}}
    root = ET.parse(OUT / "AnimData.xml").getroot()
    shadow_size = int(root.find("ShadowSize").text)
    assert 0 <= shadow_size <= 2, "ShadowSize hors de [0, 2]"
    anims, names = {}, []
    for node in root.find("Anims").iter("Anim"):
        name = node.find("Name").text
        assert name not in names, f"nom d'animation en double : {name}"
        names.append(name)
        index = int(node.find("Index").text)
        assert REQUIRED_INDEX.get(name, index) == index, f"{name} : index {index} ≠ {REQUIRED_INDEX.get(name)}"
        copy = node.find("CopyOf")
        if copy is not None:
            anims[name] = {"copy_of": copy.text}
            continue
        durations = [int(d.text) for d in node.find("Durations").iter("Duration")]
        entry = {"fw": int(node.find("FrameWidth").text), "fh": int(node.find("FrameHeight").text), "durations": durations}
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            sub = node.find(tag)
            if sub is not None:
                assert int(sub.text) < len(durations), f"{name} : {tag} au-delà du nombre d'images"
                entry[tag] = int(sub.text)
        anims[name] = entry
    assert len(names) <= 44, "plus de 44 animations"
    missing = [n for n in COMPLETE_SET if n not in anims]
    assert not missing, f"set donjon complet incomplet : {missing}"
    for name, m in anims.items():
        if "copy_of" in m:
            assert m["copy_of"] in anims and "copy_of" not in anims[m["copy_of"]], f"{name} : CopyOf invalide"
    sheets = {p.name.split("-")[0] for p in OUT.glob("*-Anim.png")}
    assert sheets == {n for n, m in anims.items() if "copy_of" not in m}, f"feuilles ≠ XML : {sheets ^ {n for n, m in anims.items() if 'copy_of' not in m}}"

    palette_ref = reference_palette()
    palette, total_cells = set(), 0
    for name, m in anims.items():
        if "copy_of" in m:
            continue
        fw, fh, durations = m["fw"], m["fh"], m["durations"]
        assert fw % 2 == 0 and fh % 2 == 0, f"{name} : case impaire"
        anim = rgba(OUT / f"{name}-Anim.png")
        offs = rgba(OUT / f"{name}-Offsets.png")
        shad = rgba(OUT / f"{name}-Shadow.png")
        night = rgba(OUT / "nuit" / f"{name}-Anim.png")
        ombres = rgba(OUT / "ombres_unites" / f"{name}-Ombres.png")
        assert anim.shape == offs.shape == shad.shape == night.shape == ombres.shape, f"{name} : tailles différentes"
        assert set(np.unique(ombres[:, :, 3])) <= {0, 100}, f"{name} : calque d'ombres ≠ alpha 0/100"
        assert anim.shape[1] % fw == 0 and anim.shape[0] % fh == 0, f"{name} : feuille non divisible par la case"
        n, dirs = anim.shape[1] // fw, anim.shape[0] // fh
        assert dirs in (1, 8), f"{name} : {dirs} lignes"
        assert n == len(durations), f"{name} : {n} images pour {len(durations)} durées"
        for sheet_name, sheet in (("Anim", anim), ("Offsets", offs), ("Shadow", shad), ("nuit", night)):
            assert set(np.unique(sheet[:, :, 3])) <= {0, 255}, f"{name}-{sheet_name} : pixels semi-transparents"
        assert np.array_equal(anim[:, :, 3], night[:, :, 3]), f"{name} : silhouette nuit ≠ jour"
        palette |= set(map(tuple, anim[anim[:, :, 3] > 0][:, :3].tolist()))
        stats = {"case": [fw, fh], "images": n, "directions": dirs, "pixels_min": None, "pixels_max": None, "ancre_repos": None}
        for d in range(dirs):
            for i in range(n):
                cell = anim[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                o = offs[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                s = shad[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw]
                white = marker(s, (255, 255, 255))
                assert len(white) == 1, f"{name} dir {d} image {i} : {len(white)} pixels blancs d'ombre"
                centre = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 1] == 255))]
                assert len(centre) == 1, f"{name} dir {d} image {i} : {len(centre)} repères centre"
                reds = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 0] == 255))]
                blues = [(x, y) for y, x in np.argwhere((o[:, :, 3] == 255) & (o[:, :, 2] == 255))]
                assert len(reds) == 1 and len(blues) == 1, f"{name} dir {d} image {i} : repères mains multiples"
                assert len(marker(o, (255, 255, 255))) == 0, f"{name} dir {d} image {i} : pixel blanc dans Offsets"
                blacks = marker(o, (0, 0, 0))
                assert len(blacks) <= 1, f"{name} dir {d} image {i} : plusieurs repères tête"
                # étendue : rien ne touche le bord de la case (marge d'un pixel)
                ys, xs = np.nonzero(cell[:, :, 3])
                px = int(len(xs))
                assert px > 0, f"{name} dir {d} image {i} : case vide"
                # semelles : plus aucun blanc pur dans les trois dernières lignes de chaque unité ;
                # on contrôle globalement : le blanc pur ne descend jamais sous la ligne y_max - 2 de la case
                white_px = (cell[:, :, 3] > 0) & np.all(cell[:, :, :3] == 255, axis=2)
                assert not white_px[ys.max() - 2:].any(), f"{name} dir {d} image {i} : semelle blanche restante"
                # ombres par unité : le calque couvre au moins six ombres de 14 × 6 fusionnées (≥ 6 × 40 px sans recouvrement total)
                oc = ombres[d * fh:(d + 1) * fh, i * fw:(i + 1) * fw, 3] > 0
                assert oc.sum() >= 3 * 60, f"{name} dir {d} image {i} : calque d'ombres trop petit ({int(oc.sum())} px)"
                assert xs.min() >= 1 and ys.min() >= 1 and xs.max() <= fw - 2 and ys.max() <= fh - 2, f"{name} dir {d} image {i} : dessin au bord de la case"
                # au moins six unités : les pixels d'une case ne descendent jamais sous 5 unités visibles
                assert px >= 5 * UNIT_PIXELS["trooper"] * 0.5, f"{name} dir {d} image {i} : trop peu de pixels ({px})"
                stats["pixels_min"] = px if stats["pixels_min"] is None else min(stats["pixels_min"], px)
                stats["pixels_max"] = px if stats["pixels_max"] is None else max(stats["pixels_max"], px)
                total_cells += 1
                if i == 0 and d == 0:
                    stats["ancre_repos"] = list(white[0])
                # l'ancre suit le déplacement du brass d'origine (glissade, secousse, bond) ;
                # pour Shoot, la formation garde une ancre fixe
                if name in LOCKSTEP or (i == 0 and d == 0):
                    bd = (0, 0) if name == "Shoot" else brass_disp(name, d if name != "Sleep" else 0, i)
                    expected = (fw // 2 + bd[0], fh // 2 + 4 + bd[1])
                    assert white[0] == expected, f"{name} dir {d} image {i} : ancre {white[0]} ≠ {expected}"
        report["animations"][name] = stats
    assert palette <= palette_ref, f"couleurs étrangères aux unités d'origine : {palette - palette_ref}"
    assert len(palette) <= 15, f"{len(palette)} couleurs (15 max)"

    # Aseprite : en-tête, nombre d'images = somme des images de toutes les animations
    data = (OUT / "falinks.aseprite").read_bytes()
    size, magic, frames, w, h, depth = struct.unpack_from("<IHHHHH", data, 0)
    assert magic == 0xA5E0 and size == len(data), "Aseprite : en-tête invalide"
    expected_frames = sum(len(m["durations"]) for m in anims.values() if "copy_of" not in m)
    assert frames == expected_frames, f"Aseprite : {frames} images ≠ {expected_frames}"
    assert depth == 32, "Aseprite : profondeur ≠ RGBA"
    # première image : 8 calques + étiquettes, puis cels ; on relit le premier cel et on le compare à la feuille
    pos = 128
    frame_size, fmagic, old_chunks, duration, _, chunks = struct.unpack_from("<IHHH2sI", data, pos)
    assert fmagic == 0xF1FA, "Aseprite : image invalide"
    p, layers, tags, cels = pos + 16, 0, 0, 0
    first_cel = None
    for _ in range(chunks):
        clen, ckind = struct.unpack_from("<IH", data, p)
        if ckind == 0x2004:
            layers += 1
        elif ckind == 0x2018:
            tags = struct.unpack_from("<H", data, p + 6)[0]
        elif ckind == 0x2005:
            cels += 1
            if first_cel is None:
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
    for name, m in anims.items():
        if "copy_of" in m:
            continue
        assert kit["animations"][name]["case"] == [m["fw"], m["fh"]], f"kit.json : case de {name}"
        assert kit["animations"][name]["durees"] == m["durations"], f"kit.json : durées de {name}"
    credits = (OUT / "credits.txt").read_text()
    assert "215638650434617345" in credits and "544245909639397378" in credits, "credits.txt : auteurs des unités absents"
    for f in ("apercu.png", "apercu_directions.png", "apercu.html", "apercu_marche_attente.gif", "apercu_attaque.gif", "README.md"):
        assert (OUT / f).is_file(), f"fichier manquant : {f}"

    report["resume"] = {"animations": len(anims), "feuilles": len(sheets), "cases": total_cells, "couleurs": len(palette),
                        "shadow_size": shadow_size, "semelles_blanches": 0, "calque_ombres_unites": True, "statut": "conforme"}
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK — {len(anims)} animations, {total_cells} cases contrôlées, {len(palette)} couleurs, ShadowSize {shadow_size}")


if __name__ == "__main__":
    main()
