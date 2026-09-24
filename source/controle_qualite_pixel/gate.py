# Copié sans modification depuis la branche arena/01a0d30e-guilde-treehouse-pmd (commit 15d07dd8, source/controle_qualite_pixel/gate.py).
"""Contrôle qualité BLOQUANT pour tout livrable de map en calques (PNG).

Usage :
    .venv/bin/python source/controle_qualite_pixel/gate.py <dossier_zone> [<dossier_zone> ...]
    .venv/bin/python source/controle_qualite_pixel/gate.py --json rapport.json <dossiers...>

Un dossier de zone contient des calques numérotés « NN_nom.png » (ordre d'empilement)
et éventuellement un composite (« composite.png » ou tout PNG non numéroté).

Seuils étalonnés sur des calques canoniques natifs du dépôt (Vast Steppe, Altere Pond,
forêt sud–nord V3) : tous PASS. Ce contrôle détecte les défauts techniques (faux pixel art,
flou, magenta, calques bidons). Il ne remplace PAS la revue artistique ni un test PMDO.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MAX_COLORS_PER_LAYER = 2048      # canon : 5 à 805 couleurs par calque, 1397 pour une map entière
MAX_RARE_COLOR_PCT = 1.0         # % de pixels opaques dont la couleur apparaît < 4 fois (canon <= 0,3)
MAGENTA_KEY_DIST = 90            # distance RGB à (255,0,255) considérée comme fond magenta résiduel
SHADOW_WORDS = ("ombre", "shadow")
MAX_SEMI_ALPHA_PCT = 0.2         # canon Altere Pond Objects : 0,06 % et 0,14 % ; ombres exemptées


def _load(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.int64)


def layer_checks(p: Path, a: np.ndarray) -> list[tuple[str, bool, str]]:
    res = []
    h, w = a.shape[:2]
    al, rgb = a[..., 3], a[..., :3]
    vis = al > 0
    res.append(("grille_8px", w % 8 == 0 and h % 8 == 0, f"{w}x{h}"))
    res.append(("calque_non_vide", bool(vis.any()), f"{int(vis.sum())} px visibles"))
    semi = int(((al > 0) & (al < 255)).sum())
    if any(k in p.name.lower() for k in SHADOW_WORDS):
        res.append(("alpha_binaire", True, f"calque d'ombre : {semi} px semi-alpha tolérés"))
    else:
        pct = 100.0 * semi / max(1, int(vis.sum()))
        res.append(("alpha_binaire", pct <= MAX_SEMI_ALPHA_PCT, f"{semi} px semi-transparents ({pct:.2f} %, max {MAX_SEMI_ALPHA_PCT})"))
    d = np.sqrt(((rgb - np.array([255, 0, 255])) ** 2).sum(-1))
    mag = int((vis & (d < MAGENTA_KEY_DIST)).sum())
    res.append(("zero_magenta_residuel", mag == 0, f"{mag} px proches du magenta de détourage"))
    op = rgb[al == 255]
    if len(op):
        k = op[:, 0] * 65536 + op[:, 1] * 256 + op[:, 2]
        u, c = np.unique(k, return_counts=True)
        rare = 100.0 * c[c < 4].sum() / len(k)
        res.append(("palette_pixel_art", len(u) <= MAX_COLORS_PER_LAYER, f"{len(u)} couleurs (max {MAX_COLORS_PER_LAYER})"))
        res.append(("pas_de_flou_ni_anticrenelage", rare <= MAX_RARE_COLOR_PCT, f"{rare:.2f} % de couleurs rares (max {MAX_RARE_COLOR_PCT})"))
    return res


LAYER_RE = re.compile(r"(?:^|_)(\d{2})_")


def zone_checks(zone: Path) -> dict:
    pngs = sorted(zone.glob("*.png"))
    # calque = « NN_nom.png » ou « Prefixe_NN_nom.png » (préfixe unique exigé par l'import PMDO)
    num = {p: LAYER_RE.search(p.name) for p in pngs}
    layers = sorted((p for p in pngs if num[p]), key=lambda p: (int(num[p].group(1)), p.name))
    # composite = PNG non numéroté dont le nom contient « composite » (masques/revues ignorés)
    others = [p for p in pngs if not num[p] and "composite" in p.name.lower()]
    report = {"zone": str(zone), "layers": {}, "zone_checks": [], "pass": True}
    if not layers:
        report["zone_checks"].append(("calques_numerotes_presents", False, "aucun calque NN_*.png"))
        report["pass"] = False
        return report
    arrays = {p: _load(p) for p in layers}
    for p, a in arrays.items():
        chk = layer_checks(p, a)
        report["layers"][p.name] = chk
        report["pass"] &= all(ok for _, ok, _ in chk)
    shapes = {a.shape for a in arrays.values()}
    zc = report["zone_checks"]
    zc.append(("calques_meme_taille", len(shapes) == 1, str(sorted({s[:2] for s in shapes}))))
    hashes: dict[str, list[str]] = {}
    for p, a in arrays.items():
        b = a.copy(); b[b[..., 3] == 0] = 0
        hashes.setdefault(hashlib.md5(b.tobytes()).hexdigest(), []).append(p.name)
    dups = [v for v in hashes.values() if len(v) > 1]
    zc.append(("aucun_calque_duplique", not dups, str(dups) if dups else "ok"))
    if len(shapes) == 1:
        stack = Image.new("RGBA", Image.open(layers[0]).size)
        for p in layers:
            stack.alpha_composite(Image.open(p).convert("RGBA"))
        st = np.asarray(stack).astype(np.int64)
        for o in others:
            oa = _load(o)
            if oa.shape != st.shape:
                continue
            b = oa.copy(); b[b[..., 3] == 0] = 0
            same_as_layer = [v for k, v in hashes.items() if k == hashlib.md5(b.tobytes()).hexdigest()]
            if len(layers) > 1:
                zc.append((f"composite_{o.name}_distinct_des_calques", not same_as_layer,
                           f"identique à {same_as_layer[0]}" if same_as_layer else "ok"))
            diff = int((np.abs(oa - st).max(-1) > 0).sum())
            zc.append((f"recomposition_{o.name}", diff == 0, f"{diff} px différents de l'empilement"))
            for name, ok, msg in layer_checks(o, oa):
                if name in ("zero_magenta_residuel", "palette_pixel_art", "pas_de_flou_ni_anticrenelage"):
                    zc.append((f"{o.name}:{name}", ok, msg))
    report["pass"] &= all(ok for _, ok, _ in zc)
    return report


def main(argv: list[str]) -> int:
    out_json = None
    if argv[:1] == ["--json"]:
        out_json, argv = Path(argv[1]), argv[2:]
    reports = [zone_checks(Path(z)) for z in argv]
    for r in reports:
        print(("PASS " if r["pass"] else "FAIL ") + r["zone"])
        for lname, chk in r["layers"].items():
            bad = [f"{n}: {m}" for n, ok, m in chk if not ok]
            if bad:
                print(f"   {lname}: " + " | ".join(bad))
        for n, ok, m in r["zone_checks"]:
            if not ok:
                print(f"   [zone] {n}: {m}")
    if out_json:
        out_json.write_text(json.dumps(reports, indent=1, ensure_ascii=False, default=str))
    return 0 if all(r["pass"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
