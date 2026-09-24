"""Tests du livrable FDENSE_V1 (lit renders/foret_dense_sn_v1/ ; lancer build.py avant).

pytest source/foret_dense_sn_v1/test_build.py   ou   .venv/bin/python source/foret_dense_sn_v1/test_build.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import labels as LB  # noqa: E402

OUT = HERE.parents[1] / "renders" / "foret_dense_sn_v1"
PREFIX = "FDENSE_V1_"
MAN = json.loads((OUT / "manifest.json").read_text())
NAMES = [c["fichier"] for c in MAN["calques"]]
CANON_ONLY = {"01_sol", "02_ombres", "03_chemin", "04_vegetation_basse", "06_parois_foret"}
GEN_ONLY = {"05_rochers", "07_troncs_racines", "08_entree", "09_canopees"}


def _rgba(name):
    return np.array(Image.open(OUT / name).convert("RGBA")).astype(np.int64)


def _short(f):
    return f[len(PREFIX):-4]


def test_tailles_multiples_de_8():
    for f in NAMES + [MAN["composite"]]:
        a = _rgba(f)
        assert a.shape[0] % 8 == 0 and a.shape[1] % 8 == 0, f


def test_composite_egal_empilement():
    st = Image.new("RGBA", Image.open(OUT / NAMES[0]).size)
    for f in NAMES:
        st.alpha_composite(Image.open(OUT / f).convert("RGBA"))
    assert (np.asarray(st) == np.asarray(Image.open(OUT / MAN["composite"]).convert("RGBA"))).all()


def test_alpha_binaire_et_zero_magenta():
    for f in NAMES:
        a = _rgba(f)
        al = a[..., 3]
        assert set(np.unique(al)) <= {0, 255}, f
        vis = al == 255
        d = np.sqrt(((a[..., :3] - np.array([255, 0, 255])) ** 2).sum(-1))
        assert not (vis & (d < 90)).any(), f


def test_calques_non_vides_et_distincts():
    seen = set()
    for f in NAMES:
        a = _rgba(f)
        assert (a[..., 3] > 0).any(), f
        b = a.copy(); b[b[..., 3] == 0] = 0
        h = hash(b.tobytes())
        assert h not in seen, f
        seen.add(h)


def test_toutes_couleurs_dans_palette_des_references():
    ref = np.concatenate([LB.load_ref(0).reshape(-1, 3), LB.load_ref(1).reshape(-1, 3)]).astype(np.int64)
    refk = set((ref[:, 0] << 16 | ref[:, 1] << 8 | ref[:, 2]).tolist())
    for f in NAMES:
        a = _rgba(f)
        op = a[a[..., 3] == 255][:, :3]
        k = set((op[:, 0] << 16 | op[:, 1] << 8 | op[:, 2]).tolist())
        assert k <= refk, (f, len(k - refk))


def test_provenance_exacte_et_honnete():
    prov = np.load(OUT / f"{PREFIX}provenance.npz")
    refs = {0: LB.load_ref(0), 1: LB.load_ref(1)}
    for f in NAMES:
        n = _short(f)
        a = _rgba(f)
        vis = a[..., 3] == 255
        p = prov[n]
        assert (prov[f"{n}_alpha"] == vis).all(), n
        src = p[..., 0][vis]
        assert (src >= 0).all(), n
        if n in CANON_ONLY:
            assert np.isin(src, [0, 1]).all(), n
        if n in GEN_ONLY:
            assert (src >= 100).all(), n
        for sid, R in refs.items():
            m = vis & (p[..., 0] == sid)
            if m.any():
                assert (R[p[..., 1][m], p[..., 2][m]] == a[..., :3][m]).all(), (n, sid)


def test_chemin_continu_du_sud_a_l_entree():
    prov = np.load(OUT / f"{PREFIX}provenance.npz")
    la = LB.labels_A(LB.load_ref(0))
    p = prov["03_chemin"]
    m = prov["03_chemin_alpha"] & (p[..., 0] == 0)
    path = np.zeros(m.shape, bool)
    path[m] = la[p[..., 1][m], p[..., 2][m]] == LB.CHEMIN
    path = ndi.binary_closing(np.pad(path, 2, mode="edge"), np.ones((3, 3)))[2:-2, 2:-2]
    cc, _ = ndi.label(path)
    bottom = set(np.unique(cc[-1])) - {0}
    ent_y = MAN["placements"]["entree"][1] + 200
    top = set(np.unique(cc[:ent_y])) - {0}
    assert bottom & top, "le chemin ne relie pas le bord sud à l'entrée"


if __name__ == "__main__":
    fails = 0
    for k, v in list(globals().items()):
        if k.startswith("test_") and callable(v):
            try:
                v()
                print("ok  ", k)
            except AssertionError as e:
                fails += 1
                print("FAIL", k, e)
    sys.exit(1 if fails else 0)
