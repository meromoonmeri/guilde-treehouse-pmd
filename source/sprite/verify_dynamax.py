#!/usr/bin/env python3
"""Relecture indépendante de sprite/<dex>_<slug>/ (build_dynamax.py) et de sprite/vfx/ (build_vfx.py).

Règles SpriteBot / SkyTemple : feuilles Anim / Offsets / Shadow de même taille, divisibles par la case, 1 ou 8
lignes, colonnes = Durations, Rush / Hit / Return < nb images, CopyOf vers une animation présente non chaînée,
alpha 0 ou 255, un seul pixel blanc par case de Shadow, un pixel de chaque repère par case.

Règles de la transformation Dynamax : mêmes animations, index, durées, Rush / Hit / Return et CopyOf que la source
SpriteCollab ; cases multiples de 8 ; ancre = source × échelle autour de (fw/2, fh/2 + 4) ; chaque pixel opaque de
la source se retrouve agrandi à sa place (les seuls pixels différents sont sous un nuage de premier plan : couleurs
des nuages uniquement, au plus 12 % du corps) ; palette = source + aura (2 couleurs) ; marge d'un pixel ;
credits.txt cite SpriteCollab.

VFX : feuilles à une ligne, palette = les 5 couleurs des effets et rien d'autre (aucun personnage, aucun fond),
aperçus transparents, aucun fichier étranger.

Usage : python3 source/sprite/verify_dynamax.py [dex ...] [--vfx] [--tous] [--pas N] [--procs N] [--source DIR]
        --tous : toutes les espèces de sprite/index.json ; --pas N : une espèce sur N (échantillon) ; --procs N : en parallèle
        → sprite/controle_qualite.json (résumé) ; code de sortie 1 s'il y a des erreurs.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dynamax_fx as FX  # noqa: E402
from build_dynamax import AURA, AURA_LIGHT, DEFAULT_SOURCE, OUT_ROOT, darkest_colour, load_source, slug_of, source_folder, white_pixel  # noqa: E402

VFX_DIR = OUT_ROOT / "vfx"
VFX_PALETTE = {FX.FX_DARK, FX.FX_CRIMSON, FX.FX_RED, FX.FX_LIGHT, FX.FX_WHITE}
VFX_FILES = {"AnimData.xml", "kit.json", "README.md", "apercu.png", "apercu.gif"}


def colours_of(A: np.ndarray) -> set:
    """Couleurs opaques d'une feuille RGBA (np.unique sur des entiers : 100 × plus rapide que set(map(tuple, ...)) sur 2 M de pixels)."""
    px = A[A[:, :, 3] > 0][:, :3].astype(np.uint32)
    if len(px) == 0:
        return set()
    packed = np.unique((px[:, 0] << 16) | (px[:, 1] << 8) | px[:, 2])
    return {(int(v >> 16), int((v >> 8) & 255), int(v & 255)) for v in packed}


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


def check_species(dex: str, source: Path, scale: int) -> tuple[list[str], dict]:
    out = OUT_ROOT / f"{dex}_{slug_of(dex)}"
    errors: list[str] = []
    E = errors.append
    if not (out / "AnimData.xml").is_file():
        return [f"{out.name} : AnimData.xml absent"], {"dex": dex}
    shadow_size, anims = parse(out / "AnimData.xml")
    _, src = load_source(source_folder(dex, source))
    src_by = {a.name: a for a in src}
    cloud_colours = {AURA, AURA_LIGHT, darkest_colour(src)}
    if shadow_size != 2:
        E(f"ShadowSize {shadow_size} ≠ 2")
    if [a["name"] for a in anims] != [a.name for a in src]:
        E("liste d'animations différente de la source")
    names = [a["name"] for a in anims]
    colours: set = set()
    src_colours: set = set()
    cells = lost_total = compared_total = 0
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
        if len({v.shape for v in sheets.values()}) != 1:
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
        for kind, arr in sheets.items():
            a = arr[:, :, 3]
            if ((a > 0) & (a < 255)).any():
                E(f"{n}-{kind} : alpha intermédiaire")
        A = sheets["Anim"]
        colours |= colours_of(A)
        src_colours |= colours_of(s.anim)
        for d in range(dirs):
            for i in range(len(durs)):
                cells += 1
                box = (slice(d * fh, (d + 1) * fh), slice(i * fw, (i + 1) * fw))
                a, o, sh = A[box], sheets["Offsets"][box], sheets["Shadow"][box]
                wh = np.argwhere((sh[:, :, 3] > 0) & np.all(sh[:, :, :3] == 255, axis=2))
                if len(wh) != 1:
                    E(f"{n} d{d} i{i} : {len(wh)} pixel(s) blanc(s) dans Shadow")
                    continue
                ax, ay = int(wh[0][1]), int(wh[0][0])
                sax, say = white_pixel(s.cell(s.shad, d, i), s.fw, s.fh)
                exp = (fw // 2 + (sax - s.fw // 2) * scale, fh // 2 + 4 + (say - (s.fh // 2 + 4)) * scale)
                if (ax, ay) != exp:
                    E(f"{n} d{d} i{i} : ancre {(ax, ay)} ≠ {exp}")
                so = s.cell(s.offs, d, i)
                exp_marks = {((int(x) - sax) * scale, (int(y) - say) * scale): tuple(int(v) for v in so[y, x, :3]) for y, x in np.argwhere(so[:, :, 3] > 0)}
                got_marks = {(int(x) - ax, int(y) - ay): tuple(int(v) for v in o[y, x, :3]) for y, x in np.argwhere(o[:, :, 3] > 0)}
                if got_marks != exp_marks:
                    E(f"{n} d{d} i{i} : repères Offsets ≠ source × {scale}")
                m = a[:, :, 3] > 0
                if m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any():
                    E(f"{n} d{d} i{i} : dessin au bord de la case")
                sc = s.cell(s.anim, d, i)
                ys, xs = np.nonzero(sc[:, :, 3] > 0)
                if len(xs) == 0:
                    continue
                got = a[ay + (ys - say) * scale, ax + (xs - sax) * scale, :3]
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
    credits = (out / "credits.txt").read_text(encoding="utf-8") if (out / "credits.txt").is_file() else ""
    if dex not in credits or "SpriteCollab" not in credits:
        E("credits.txt : source SpriteCollab non citée")
    report = {"dex": dex, "animations": len(anims), "cases": cells, "couleurs": len(colours), "couleurs_source": len(src_colours),
              "pixels_compares": compared_total, "pixels_sous_nuages": lost_total, "erreurs": errors[:20]}
    return errors, report


def check_vfx() -> tuple[list[str], dict]:
    errors: list[str] = []
    E = errors.append
    if not (VFX_DIR / "AnimData.xml").is_file():
        return [f"{VFX_DIR} : AnimData.xml absent"], {}
    kit = json.loads((VFX_DIR / "kit.json").read_text(encoding="utf-8"))
    _, anims = parse(VFX_DIR / "AnimData.xml")
    names = [a["name"] for a in anims]
    for size in ("M", "L"):
        if f"Transformation-{size}" not in names:
            E(f"Transformation-{size} absente de AnimData.xml")
    colours: set = set()
    cells = 0
    for e in anims:
        n = e["name"]
        if e["index"] is None or e["index"] < 13:
            E(f"{n} : index {e['index']} (attendu ≥ 13)")
        fw, fh, durs = e["fw"], e["fh"], e["durations"]
        if fw % 8 or fh % 8:
            E(f"{n} : case {fw}×{fh} non multiple de 8")
        if e["hit"] is None or e["ret"] is None or not (0 <= e["hit"] < e["ret"] < len(durs)):
            E(f"{n} : HitFrame / ReturnFrame manquants ou hors des images")
        if len(durs) != len(kit.get("images", [])):
            E(f"{n} : {len(durs)} durées ≠ {len(kit.get('images', []))} images dans kit.json")
        sheets = {}
        for kind in ("Anim", "Offsets", "Shadow"):
            p = VFX_DIR / f"{n}-{kind}.png"
            if not p.is_file():
                E(f"{n}-{kind}.png absent")
                continue
            sheets[kind] = np.array(Image.open(p).convert("RGBA"))
        if len(sheets) < 3 or len({v.shape for v in sheets.values()}) != 1:
            E(f"{n} : feuilles absentes ou de tailles différentes")
            continue
        H, W = sheets["Anim"].shape[:2]
        if W != fw * len(durs) or H != fh:
            E(f"{n} : feuille {W}×{H} ≠ {len(durs)} colonnes de {fw} × 1 ligne de {fh}")
            continue
        for kind, arr in sheets.items():
            a = arr[:, :, 3]
            if ((a > 0) & (a < 255)).any():
                E(f"{n}-{kind} : alpha intermédiaire")
        A = sheets["Anim"]
        colours |= colours_of(A)
        for i in range(len(durs)):
            cells += 1
            box = (slice(0, fh), slice(i * fw, (i + 1) * fw))
            a, o, sh = A[box], sheets["Offsets"][box], sheets["Shadow"][box]
            wh = np.argwhere((sh[:, :, 3] > 0) & np.all(sh[:, :, :3] == 255, axis=2))
            if len(wh) != 1 or (int(wh[0][1]), int(wh[0][0])) != (fw // 2, fh // 2 + 4):
                E(f"{n} i{i} : ancre Shadow absente ou ≠ (fw/2, fh/2 + 4)")
            greens = np.argwhere((o[:, :, 3] > 0) & (o[:, :, 1] == 255) & (o[:, :, 0] == 0))
            if len(greens) != 1 or (int(greens[0][1]), int(greens[0][0])) != (fw // 2, fh // 2 + 4):
                E(f"{n} i{i} : centre vert des Offsets absent ou ≠ ancre")
            m = a[:, :, 3] > 0
            if not m.any():
                E(f"{n} i{i} : case vide")
            elif m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any():
                E(f"{n} i{i} : dessin au bord de la case")
    if not colours <= VFX_PALETTE:
        E(f"couleurs hors palette des effets (personnage ou fond ?) : {sorted(colours - VFX_PALETTE)[:5]}")
    for f in sorted(VFX_FILES):
        if not (VFX_DIR / f).is_file():
            E(f"{f} absent")
    allowed = VFX_FILES | {f"{n}-{k}.png" for n in names for k in ("Anim", "Offsets", "Shadow")}
    for f in sorted(VFX_DIR.iterdir()):
        if f.name not in allowed:
            E(f"fichier étranger dans vfx/ : {f.name}")
    if (VFX_DIR / "apercu.png").is_file():
        a = np.array(Image.open(VFX_DIR / "apercu.png").convert("RGBA"))
        if a[0, 0, 3] != 0 or (a[:, :, 3] > 0).mean() > 0.5:
            E("apercu.png : fond non transparent")
        extra = colours_of(a) - VFX_PALETTE
        if extra:
            E(f"apercu.png : couleurs hors palette des effets {sorted(extra)[:3]}")
    if (VFX_DIR / "apercu.gif").is_file():
        g = Image.open(VFX_DIR / "apercu.gif")
        if g.info.get("transparency") is None or np.array(g.convert("RGBA"))[0, 0, 3] != 0:
            E("apercu.gif : fond non transparent")
    return errors, {"effets": len(anims), "cases": cells, "couleurs": len(colours), "erreurs": errors[:20]}


def _check(args: tuple) -> tuple[str, list[str], dict]:
    dex, source, scale = args
    try:
        errors, r = check_species(dex, Path(source), scale)
    except Exception as exc:  # noqa: BLE001
        errors, r = [f"{type(exc).__name__}: {exc}"], {"dex": dex}
    return dex, errors, r


def main(argv: list[str]) -> None:
    source = DEFAULT_SOURCE
    want_vfx = "--vfx" in argv or not [a for a in argv if not a.startswith("--")] and "--tous" not in argv
    all_species = "--tous" in argv
    step, procs = 1, 1
    dexes = []
    it = iter(argv)
    for arg in it:
        if arg == "--source":
            source = Path(next(it))
        elif arg == "--pas":
            step = int(next(it))
        elif arg == "--procs":
            procs = int(next(it))
        elif arg.startswith("--"):
            continue
        else:
            dexes.append(arg.zfill(4))
    index_path = OUT_ROOT / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {"source": {"echelle": 3}, "especes": {}}
    scale = int(index["source"].get("echelle", 3))
    if all_species:
        dexes = [d for d, r in sorted(index["especes"].items()) if "erreur" not in r][::step]
    failed = False
    summary = {"vfx": None, "especes": {}, "ok": 0, "erreurs": 0}
    if want_vfx or all_species:
        errors, r = check_vfx()
        summary["vfx"] = {"resultat": "OK" if not errors else "ERREURS", **r}
        print("vfx :", "OK" if not errors else f"{len(errors)} erreur(s)", "—", f"{r.get('effets')} feuilles, {r.get('cases')} cases, {r.get('couleurs')} couleurs")
        for e in errors[:10]:
            print("   ", e)
        failed |= bool(errors)
    jobs = [(d, str(source), scale) for d in dexes]
    pool = Pool(procs) if procs > 1 and len(jobs) > 1 else None
    results = pool.imap(_check, jobs, chunksize=1) if pool else map(_check, jobs)
    for k, (dex, errors, r) in enumerate(results, 1):
        r["resultat"] = "OK" if not errors else "ERREURS"
        summary["especes"][dex] = r
        if errors:
            failed = True
            summary["erreurs"] += 1
            print(f"[{k}/{len(dexes)}] {dex} : {len(errors)} erreur(s)", flush=True)
            for e in errors[:6]:
                print("   ", e)
        else:
            summary["ok"] += 1
            if len(dexes) <= 20 or k % 25 == 0:
                print(f"[{k}/{len(dexes)}] {dex} OK — {r['animations']} anim, {r['cases']} cases, {r['couleurs']} couleurs, "
                      f"{r['pixels_sous_nuages']} px sous les nuages / {r['pixels_compares']}", flush=True)
    if pool:
        pool.close()
    if dexes:
        print(f"{summary['ok']} espèces OK, {summary['erreurs']} en erreur" + (f" (échantillon : une sur {step})" if step > 1 else ""))
    (OUT_ROOT / "controle_qualite.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
